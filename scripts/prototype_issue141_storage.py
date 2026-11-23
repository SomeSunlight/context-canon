#!/usr/bin/env python3
"""#141 isolation: compare actual #137 Git trees as v4, CAS, tar, tar.gz.

Read-only on the user repository. Only temporary copies are transformed.
Prototype only: no runtime loader/migration, no onboarding or acceptance edits.
Requires a full Git clone containing both baseline commits.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tarfile
import tempfile

BEFORE = "5a1f2bff24a9f6c6af49d96044eaf15b80d0d0b6"
AFTER = "359f7efe6b02d59b75d3c7e5ffedfa7ed9c9c99c"
PKG = ".context/package.json"
VERSIONS = Path(".context/versions")


def git(root: Path, *args: str, binary: bool = False) -> bytes | str:
    out = subprocess.run(["git", "-C", str(root), *args], check=True,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout
    return out if binary else out.decode("utf-8")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe(path: str) -> Path:
    p = PurePosixPath(path)
    if not path or p.is_absolute() or ".." in p.parts or "\\" in path or path != p.as_posix():
        raise ValueError(f"unsafe path: {path!r}")
    return Path(*p.parts)


def v4_digest(files: dict[str, bytes]) -> str:
    d = hashlib.sha256()
    for name, value in sorted(files.items()):
        d.update(name.encode("utf-8") + b"\0" + hashlib.sha256(value).digest() + b"\0")
    return d.hexdigest()


def package(folder: Path) -> dict[str, bytes]:
    rawbytes = (folder / PKG).read_bytes()
    manifest = json.loads(rawbytes)
    if manifest.get("schema") != "contextcanon/package/v4":
        raise ValueError("unsupported legacy package")
    result = {PKG: rawbytes}
    for entry in manifest["files"]:
        name = entry["path"]
        safe(name)
        if name in result:
            raise ValueError("duplicate path")
        path = folder / safe(name)
        if path.is_symlink() or not path.is_file():
            raise ValueError("missing/symlink member")
        data = path.read_bytes()
        if digest(data) != entry["sha256"] or len(data) != entry["size"]:
            # Some retained packages bind original CRLF bytes while Git
            # historically stored the LF form. Recover only when exact
            # SHA-256 AND byte length authenticate the result (#112).
            candidate = data.replace(b"\n", b"\r\n")
            if len(candidate) == entry["size"] and digest(candidate) == entry["sha256"]:
                data = candidate
            else:
                raise ValueError(f"v4 member corrupted: {folder / name}; stored_size={len(data)}, expected_size={entry['size']}")
        result[name] = data
    if v4_digest({k: v for k, v in result.items() if k != PKG}) != manifest["digests"]["package"]:
        raise ValueError("v4 package digest changed")
    seen = {p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file()}
    if set(result) != seen:
        raise ValueError("extra/missing package files")
    return result


def all_packages(root: Path) -> dict[str, dict[str, bytes]]:
    # Legacy v0-v3 remain byte-for-byte intact; this bounded prototype
    # transforms only verified v4, never silently migrates a legacy package.
    return {folder.name: package(folder)
            for folder in sorted((root / VERSIONS).iterdir())
            if folder.is_dir() and (folder / PKG).is_file()
            and json.loads((folder / PKG).read_bytes()).get("schema") == "contextcanon/package/v4"}


def stage(root: Path, mode: str) -> None:
    if mode == "v4":
        return
    for token, contents in all_packages(root).items():
        if mode == "cas":
            refs = []
            for name, data in sorted(contents.items()):
                h = digest(data)
                dest = root / ".context/objects/sha256" / h[:2] / h[2:]
                dest.parent.mkdir(parents=True, exist_ok=True)
                if dest.exists() and dest.read_bytes() != data:
                    raise ValueError("collision or corrupt object")
                dest.write_bytes(data)
                refs.append({"path": name, "sha256": h, "size": len(data)})
            target = root / ".context/revisions" / (token + ".json")
            target.parent.mkdir(parents=True, exist_ok=True)
            metadata = json.loads(contents[PKG])
            target.write_text(json.dumps({
                "schema": "contextcanon/history-ref/research-1", "token": token,
                "node": metadata.get("node"), "digests": metadata["digests"],
                "members": refs,
            }, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        else:
            name = token + (".tar.gz" if mode == "tgz" else ".tar")
            target = root / ".context/archives" / name
            target.parent.mkdir(parents=True, exist_ok=True)
            buffer = io.BytesIO()
            with tarfile.open(fileobj=buffer, mode="w", format=tarfile.PAX_FORMAT) as tar:
                for rel, data in sorted(contents.items()):
                    entry = tarfile.TarInfo(rel)
                    entry.size, entry.mode = len(data), 0o444
                    entry.uid = entry.gid = entry.mtime = 0
                    entry.uname = entry.gname = ""
                    tar.addfile(entry, io.BytesIO(data))
            if mode == "tar":
                target.write_bytes(buffer.getvalue())
            else:
                with target.open("wb") as output:
                    with gzip.GzipFile(filename="", mode="wb", fileobj=output,
                                       mtime=0, compresslevel=9) as compressor:
                        compressor.write(buffer.getvalue())
        shutil.rmtree(root / VERSIONS / token)
    if mode == "cas":
        attrs = root / ".gitattributes"
        with attrs.open("a", encoding="utf-8", newline="\n") as output:
            output.write("\n.context/objects/sha256/** -text\n")
    # Existing browsing README contains links to old v4 folders (known gap).
    # A production format needs new on-demand read-only export links.


def restored(root: Path, mode: str, token: str) -> dict[str, bytes]:
    if mode == "v4":
        return package(root / VERSIONS / token)
    if mode == "cas":
        ref = json.loads((root / ".context/revisions" / (token + ".json")).read_bytes())
        if ref["schema"] != "contextcanon/history-ref/research-1" or ref["token"] != token:
            raise ValueError("reference identity changed")
        found = {}
        for entry in ref["members"]:
            rel = entry["path"]
            safe(rel)
            if rel in found:
                raise ValueError("duplicate member")
            h = entry["sha256"]
            if len(h) != 64 or any(c not in "0123456789abcdef" for c in h):
                raise ValueError("bad content address")
            obj = root / ".context/objects/sha256" / h[:2] / h[2:]
            if not obj.is_file() or obj.is_symlink():
                raise ValueError("missing/unsafe object")
            data = obj.read_bytes()
            if len(data) != entry["size"] or digest(data) != h:
                raise ValueError("corrupt byte object")
            found[rel] = data
        if json.loads(found[PKG])["digests"] != ref["digests"]:
            raise ValueError("wrong identity reference")
    else:
        extension = ".tar.gz" if mode == "tgz" else ".tar"
        target = root / ".context/archives" / (token + extension)
        found = {}
        with tarfile.open(target, "r:gz" if mode == "tgz" else "r:") as tar:
            for item in tar:
                safe(item.name)
                if not item.isfile() or item.name in found:
                    raise ValueError("unsafe/duplicate archive entry")
                found[item.name] = tar.extractfile(item).read()
    raw = json.loads(found[PKG])
    expected = {item["path"] for item in raw["files"]} | {PKG}
    if set(found) != expected:
        raise ValueError("manifest member mismatch")
    for item in raw["files"]:
        value = found[item["path"]]
        if digest(value) != item["sha256"] or len(value) != item["size"]:
            raise ValueError("v4 member identity mismatch")
    if v4_digest({k: v for k, v in found.items() if k != PKG}) != raw["digests"]["package"]:
        raise ValueError("v4 package digest mismatch")
    return found


def unpack(repo: Path, ref: str, dest: Path) -> None:
    """Extract exact committed *blob* bytes, not Git-archive export conversions.

    Git for Windows can apply CRLF filters during git archive despite no
    explicit worktree checkout. The benchmark's input must instead be the
    actual Git objects; otherwise cross-platform comparisons are invalid.
    """
    entries = []
    for row in git(repo, "ls-tree", "-r", "-z", ref, binary=True).split(b"\0"):
        if not row:
            continue
        header, name = row.split(b"\t", 1)
        mode, kind, obj = header.decode("ascii").split()
        if kind != "blob" or mode == "120000":
            raise ValueError("unsupported Git tree member (symlinks forbidden)")
        entries.append((name.decode("utf-8"), obj))
    unique = list(dict.fromkeys(sha for _, sha in entries))
    output = subprocess.run(
        ["git", "-C", str(repo), "cat-file", "--batch"],
        input=("\n".join(unique) + "\n").encode("ascii"), check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout
    pos = 0
    objects: dict[str, bytes] = {}
    for sha in unique:
        end = output.index(b"\n", pos)
        head = output[pos:end].split(b" ")
        if len(head) != 3 or head[0] != sha.encode("ascii") or head[1] != b"blob":
            raise ValueError("invalid Git batch object header")
        size = int(head[2])
        offset = end + 1
        if output[offset + size:offset + size + 1] != b"\n":
            raise ValueError("invalid Git batch object framing")
        objects[sha] = output[offset:offset + size]
        pos = offset + size + 1
    if pos != len(output):
        raise ValueError("unexpected Git batch bytes")
    for name, sha in entries:
        path = dest / safe(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(objects[sha])


def replace(root: Path, src: Path) -> None:
    for child in root.iterdir():
        if child.name == ".git":
            continue
        shutil.rmtree(child) if child.is_dir() else child.unlink()
    for child in src.iterdir():
        shutil.copytree(child, root / child.name) if child.is_dir() else shutil.copy2(child, root / child.name)


def experiment(before: Path, after: Path, mode: str, scratch: Path) -> dict:
    a, b, gitroot = (scratch / (mode + suffix) for suffix in ("-a", "-b", "-git"))
    shutil.copytree(before, a)
    shutil.copytree(after, b)
    originals = all_packages(b)
    stage(a, mode)
    stage(b, mode)
    for token, content in originals.items():
        if restored(b, mode, token) != content:
            raise AssertionError("materialization not byte identical")
    if mode == "cas":
        # Fail closed for damaged or missing Git-tracked byte objects.
        token = next(iter(originals))
        ref = json.loads((b / ".context/revisions" / (token + ".json")).read_bytes())
        entry = ref["members"][0]
        h = entry["sha256"]
        obj = b / ".context/objects/sha256" / h[:2] / h[2:]
        intact = obj.read_bytes()
        try:
            obj.write_bytes((bytes([intact[0] ^ 1]) + intact[1:]) if intact else b"x")
            try:
                restored(b, mode, token)
                raise AssertionError("corrupt object was accepted")
            except ValueError:
                pass
            obj.unlink()
            try:
                restored(b, mode, token)
                raise AssertionError("missing object was accepted")
            except ValueError:
                pass
        finally:
            obj.write_bytes(intact)
        if restored(b, mode, token) != originals[token]:
            raise AssertionError("failed to recover original after corruption test")
    gitroot.mkdir()
    git(gitroot, "init", "-q", "--initial-branch=main")
    git(gitroot, "config", "user.name", "Issue 141 research")
    git(gitroot, "config", "user.email", "research@example.invalid")
    git(gitroot, "config", "core.autocrlf", "false")
    replace(gitroot, a)
    git(gitroot, "add", "-A", "-f")
    git(gitroot, "commit", "-qm", "before")
    git(gitroot, "gc", "--prune=now")
    packdir = gitroot / ".git/objects/pack"
    first = sum(p.stat().st_size for p in packdir.glob("*.pack"))
    replace(gitroot, b)
    git(gitroot, "add", "-A", "-f")
    stat = git(gitroot, "diff", "--cached", "--numstat").splitlines()
    status = git(gitroot, "diff", "--cached", "--name-status").splitlines()
    tracked = git(gitroot, "ls-files", "-s").splitlines()
    metrics = {
        "paths_changed": len(status),
        "paths_added": sum(s.startswith("A\t") for s in status),
        "paths_modified": sum(s.startswith("M\t") for s in status),
        "text_additions": sum(int(s.split("\t")[0]) for s in stat if s.split("\t")[0].isdigit()),
        "text_deletions": sum(int(s.split("\t")[1]) for s in stat if s.split("\t")[1].isdigit()),
        "binary_diff_paths": sum(s.startswith("-\t-") for s in stat),
        "checkout_bytes": sum(p.stat().st_size for p in gitroot.rglob("*") if p.is_file() and ".git" not in p.relative_to(gitroot).parts),
        "tracked_paths": len(tracked),
        "new_versions": len(originals) - len(all_packages(before)),
        "retained_versions": len(originals),
    }
    git(gitroot, "commit", "-qm", "after")
    # The repository must be reconstructible with NO provider, server or
    # special filters. Exercise an offline local clone for all v4 packages.
    clone = scratch / (mode + "-offline-clone")
    subprocess.run(
        ["git", "-c", "core.autocrlf=true" if mode == "cas" else "core.autocrlf=false",
         "clone", "-q", "--no-hardlinks", str(gitroot), str(clone)],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    for token, expected in originals.items():
        if restored(clone, mode, token) != expected:
            raise AssertionError("offline clone changed accepted package bytes")
    metrics["offline_cloned_packages_verified"] = len(originals)
    git(gitroot, "gc", "--prune=now")
    metrics["git_gc_pack_delta"] = sum(p.stat().st_size for p in packdir.glob("*.pack")) - first
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--before", default=BEFORE)
    parser.add_argument("--after", default=AFTER)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="cc141-experiment-") as tmp:
        scratch = Path(tmp)
        first, second = scratch / "source-before", scratch / "source-after"
        first.mkdir()
        second.mkdir()
        unpack(args.repo.resolve(), args.before, first)
        unpack(args.repo.resolve(), args.after, second)
        results = {mode: experiment(first, second, mode, scratch)
                   for mode in ("v4", "cas", "tar", "tgz")}
        print(json.dumps({"source": {"before": args.before, "after": args.after},
                          "results": results}, indent=2))


if __name__ == "__main__":
    main()
