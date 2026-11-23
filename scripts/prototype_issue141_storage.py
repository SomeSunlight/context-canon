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
            raise ValueError("v4 member corrupted")
        result[name] = data
    if v4_digest({k: v for k, v in result.items() if k != PKG}) != manifest["digests"]["package"]:
        raise ValueError("v4 package digest changed")
    seen = {p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file()}
    if set(result) != seen:
        raise ValueError("extra/missing package files")
    return result


def all_packages(root: Path) -> dict[str, dict[str, bytes]]:
    return {folder.name: package(folder)
            for folder in sorted((root / VERSIONS).iterdir())
            if folder.is_dir() and (folder / PKG).is_file()}


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
    raw = git(repo, "archive", "--format=tar", ref, binary=True)
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:") as stream:
        for member in stream:
            path = dest / safe(member.name.rstrip("/"))
            if member.isdir():
                path.mkdir(parents=True, exist_ok=True)
            elif member.isfile():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(stream.extractfile(member).read())
            else:
                raise ValueError("symlinks not supported in this isolated experiment")


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
    gitroot.mkdir()
    git(gitroot, "init", "-q", "--initial-branch=main")
    git(gitroot, "config", "user.name", "Issue 141 research")
    git(gitroot, "config", "user.email", "research@example.invalid")
    git(gitroot, "config", "core.autocrlf", "false")
    replace(gitroot, a)
    git(gitroot, "add", "-A")
    git(gitroot, "commit", "-qm", "before")
    git(gitroot, "gc", "--prune=now")
    packdir = gitroot / ".git/objects/pack"
    first = sum(p.stat().st_size for p in packdir.glob("*.pack"))
    replace(gitroot, b)
    git(gitroot, "add", "-A")
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
