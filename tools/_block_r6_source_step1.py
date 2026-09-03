from __future__ import annotations

import sys
from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one match, found {count}: {old[:120]!r}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


def patch_git_transport() -> None:
    replace_once(
        "src/contextcanon/git_transport.py",
        "import os\nimport shutil\nimport subprocess\nimport tempfile\n",
        "import json\nimport os\nimport re\nimport shutil\nimport subprocess\nimport tempfile\n",
    )
    replace_once(
        "src/contextcanon/git_transport.py",
        "from .parser import ContextCanonError, find_repo_root, parse_node\n\n\n",
        "from .parser import ContextCanonError, find_repo_root, parse_node\n\n\nCANDIDATE_PROVENANCE_SCHEMA = \"contextcanon/git-candidate-provenance/v0\"\n_GIT_SHA_RE = re.compile(r\"^[0-9a-f]{40}$\")\n\n\n",
    )
    replace_once(
        "src/contextcanon/git_transport.py",
        '''        _clone(source, checkout)\n        candidate_root = _candidate_node_root(checkout, source)\n        candidate = load_package(candidate_root)\n''',
        '''        candidate_ref = _clone(source, checkout)\n        candidate_root = _candidate_node_root(checkout, source)\n        candidate = load_package(candidate_root)\n''',
    )
    replace_once(
        "src/contextcanon/git_transport.py",
        '''        persisted = _persist_candidate(node_root, candidate_root, candidate)\n        return candidate, persisted\n''',
        '''        persisted = _persist_candidate(node_root, candidate_root, candidate)\n        _persist_candidate_provenance(node_root, source, candidate, candidate_ref)\n        return candidate, persisted\n''',
    )

    p = Path("src/contextcanon/git_transport.py")
    text = p.read_text(encoding="utf-8")
    start = text.find("def _clone(source: SourceRef, destination: Path) -> None:\n")
    end = text.find("\n\ndef _candidate_node_root", start)
    if start < 0 or end < 0:
        raise SystemExit("git transport _clone boundary missing")
    replacement = r'''def _clone(source: SourceRef, destination: Path) -> str:
    """Clone the update-discovery snapshot and return its exact Git commit.

    New onboarding records an exact accepted commit SHA in ``ref``. Reusing
    that SHA for discovery would fetch the already accepted package forever,
    so an exact SHA means: discover from the remote default branch. Historical
    symbolic refs remain supported as explicit discovery branches/tags.
    """

    command = ["git", "clone", "--quiet", "--depth", "1", "--single-branch"]
    if source.transport_ref and not _GIT_SHA_RE.fullmatch(source.transport_ref):
        command.extend(["--branch", source.transport_ref])
    command.extend([source.locator, str(destination)])
    try:
        completed = subprocess.run(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise ContextCanonError("Git Source transport requires the 'git' executable on PATH") from exc
    except OSError as exc:
        raise ContextCanonError(f"Could not start Git Source transport: {exc}") from exc

    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or f"exit code {completed.returncode}"
        discovery = source.transport_ref if source.transport_ref and not _GIT_SHA_RE.fullmatch(source.transport_ref) else "remote default branch"
        raise ContextCanonError(
            f"Git Source fetch failed for {source.name} discovery ref {discovery}: {detail}"
        )

    exact = subprocess.run(
        ["git", "-C", str(destination), "rev-parse", "HEAD"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    candidate_ref = exact.stdout.strip()
    if exact.returncode != 0 or not _GIT_SHA_RE.fullmatch(candidate_ref):
        detail = exact.stderr.strip() or exact.stdout.strip() or f"exit code {exact.returncode}"
        raise ContextCanonError(f"Could not resolve exact Git Source candidate commit: {detail}")
    return candidate_ref
'''
    p.write_text(text[:start] + replacement + text[end:], encoding="utf-8")

    append = r'''


def candidate_provenance_path(node_root: Path, package_digest: str) -> Path:
    return node_root.resolve() / ".context" / "candidates" / f"{package_digest}.git.json"


def load_candidate_provenance(node_root: Path, package_digest: str) -> dict[str, str] | None:
    path = candidate_provenance_path(node_root, package_digest)
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContextCanonError(f"Invalid Git Source candidate provenance {path}: {exc}") from exc
    required = {"schema", "source_id", "locator", "accepted_ref", "candidate_ref", "node_path", "package_digest"}
    if not isinstance(raw, dict) or set(raw) != required or raw.get("schema") != CANDIDATE_PROVENANCE_SCHEMA:
        raise ContextCanonError(f"Invalid Git Source candidate provenance schema in {path}")
    values = {key: str(value) for key, value in raw.items()}
    if not _GIT_SHA_RE.fullmatch(values["candidate_ref"]):
        raise ContextCanonError(f"Invalid exact Git Source candidate commit in {path}")
    if values["package_digest"] != package_digest:
        raise ContextCanonError(f"Git Source candidate provenance digest mismatch in {path}")
    return values


def _persist_candidate_provenance(
    node_root: Path,
    source: SourceRef,
    candidate: CompiledPackage,
    candidate_ref: str,
) -> Path:
    path = candidate_provenance_path(node_root, candidate.package_digest)
    payload = {
        "schema": CANDIDATE_PROVENANCE_SCHEMA,
        "source_id": source.id,
        "locator": source.locator,
        "accepted_ref": source.transport_ref or "",
        "candidate_ref": candidate_ref,
        "node_path": source.node_path or ".",
        "package_digest": candidate.package_digest,
    }
    encoded = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(encoded, encoding="utf-8")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
    return path
'''
    p = Path("src/contextcanon/git_transport.py")
    p.write_text(p.read_text(encoding="utf-8").rstrip() + append, encoding="utf-8")


def patch_cli() -> None:
    replace_once(
        "src/contextcanon/cli.py",
        "from .git_transport import fetch_git_candidate\n",
        "from .git_transport import fetch_git_candidate, load_candidate_provenance\n",
    )
    replace_once(
        "src/contextcanon/cli.py",
        '''                print(f"fetched candidate {candidate.metadata.name} {candidate.metadata.version} ({candidate.package_digest})")\n                print(f"Candidate package: {label}")\n                return 0\n''',
        '''                print(f"fetched candidate {candidate.metadata.name} {candidate.metadata.version} ({candidate.package_digest})")\n                provenance = load_candidate_provenance(node_root, candidate.package_digest)\n                if provenance is not None:\n                    print(f"Candidate Git commit: {provenance['candidate_ref']}")\n                print(f"Candidate package: {label}")\n                print("Accepted Source pin is unchanged until explicit review and accept.")\n                return 0\n''',
    )


def patch_tests() -> None:
    # Add a regression that mirrors real onboarding: the accepted ref is an
    # exact old commit SHA, while fetch must discover the newer default-branch
    # package and freeze its exact commit beside the candidate artifact.
    p = Path("tests/test_git_transport.py")
    text = p.read_text(encoding="utf-8")
    text = text.replace(
        "from contextcanon.git_transport import fetch_git_candidate\n",
        "from contextcanon.git_transport import fetch_git_candidate, load_candidate_provenance\n",
        1,
    )
    marker = "    def test_git_fetch_rejects_missing_node_path(self):\n"
    test = r'''    def test_exact_accepted_commit_discovers_newer_default_branch_and_freezes_candidate_commit(self):
        provider, v1, v2 = self.make_provider()
        commits = self.git(provider, "log", "--format=%H", "--reverse").stdout.splitlines()
        self.assertEqual(len(commits), 2)
        accepted_ref, candidate_ref = commits
        consumer = self.make_consumer(provider, v1)
        source_path = consumer / "CONTEXT.src.md"
        source_path.write_text(
            source_path.read_text(encoding="utf-8").replace('ref="main"', f'ref="{accepted_ref}"'),
            encoding="utf-8",
        )

        candidate, candidate_root = fetch_git_candidate(consumer, "node-python")
        self.assertEqual(candidate.metadata.version, "2.0.0")
        self.assertEqual(candidate.package_digest, v2.package_digest)
        provenance = load_candidate_provenance(consumer, candidate.package_digest)
        self.assertIsNotNone(provenance)
        self.assertEqual(provenance["accepted_ref"], accepted_ref)
        self.assertEqual(provenance["candidate_ref"], candidate_ref)
        self.assertEqual(provenance["source_id"], "node-python")
        self.assertEqual(provenance["node_path"], "nodes/library/python-development")
        self.assertEqual(candidate_root, consumer / ".context/candidates" / v2.package_digest)

        # Discovery is candidate-only; even a newer remote snapshot does not
        # move the accepted consumer package.
        compiled = Compiler(consumer).compile(consumer)
        self.assertEqual(compiled.source_packages[0].package_digest, v1.package_digest)
        self.assertEqual(compiled.inherited_rules[0].statement, "Prefer explicit Python v1.")

'''
    if marker not in text:
        raise SystemExit("git transport test insertion marker missing")
    p.write_text(text.replace(marker, test + marker, 1), encoding="utf-8")


def patch_docs() -> None:
    replace_once(
        "nodes/internal/framework-development/docs/external-sources.md",
        "Compiler 0.4 provides a generic Git candidate transport. It is not GitHub-specific and uses the system `git` executable.",
        "Compiler 0.5 provides a generic Git candidate transport. It is not GitHub-specific and uses the system `git` executable.",
    )
    replace_once(
        "nodes/internal/framework-development/docs/external-sources.md",
        "- `ref=\"main\"` — branch/tag/ref used for candidate discovery;",
        "- `ref=\"...\"` — accepted Git provenance. Current onboarding records the exact accepted commit SHA. Historical symbolic branch/tag refs remain supported as an explicit discovery ref;",
    )
    replace_once(
        "nodes/internal/framework-development/docs/external-sources.md",
        "`source fetch` clones the declared Git ref into a temporary checkout, enters `node-path`, loads and fully verifies the immutable package already published there, then copies only that immutable artifact to `.context/candidates/<package-digest>/`.\n\nIt does **not** modify `CONTEXT.src.md` or `.context/sources/`.",
        "`source fetch` explicitly performs update discovery. When `ref` is an exact accepted commit SHA (the normal current-onboarding form), discovery reads the repository's current default branch rather than cloning that old accepted commit forever. Historical symbolic refs are followed directly. ContextCanon enters `node-path`, loads and fully verifies the immutable package already published there, copies only that immutable artifact to `.context/candidates/<package-digest>/`, and records the exact discovered Git commit in a sibling `<package-digest>.git.json` provenance record.\n\nIt does **not** modify `CONTEXT.src.md` or `.context/sources/`. The moving remote branch is used only long enough to discover one candidate; the persisted candidate immediately becomes content-addressed package bytes plus an exact Git commit.",
    )
    replace_once(
        "nodes/internal/framework-development/docs/external-sources.md",
        "Compiler 0.4 implements immutable manifests, full package verification, offline accepted-package composition, exact Source pins, deterministic package diff, review receipts, explicit acceptance, multi-Node Git addressing, generic Git candidate retrieval, staged package publication, and atomic canonical-pin replacement.",
        "Compiler 0.5 implements immutable manifests, full package verification, offline accepted-package composition, exact Source pins, deterministic package diff, review receipts, explicit acceptance, multi-Node Git addressing, generic Git candidate retrieval, staged package publication, atomic canonical-pin replacement, and exact-commit capture for update candidates discovered from a moving remote branch.",
    )


def complete() -> None:
    replace_once(
        "PLAN.md",
        "**Status: ACTIVE — R6 reusable Source update discovery UX, step 1 of 3. Fast-run remains ACTIVE.**",
        "**Status: ACTIVE — R6 reusable Source update discovery UX, step 2 of 3. Fast-run remains ACTIVE.**",
    )
    replace_once(
        "PLAN.md",
        "- [ ] 1. Let projects discover/fetch a newer reusable Source package without manually tracking package identities.",
        "- [x] 1. Let projects discover/fetch a newer reusable Source package without manually tracking package identities.",
    )
    state = Path("STATE.md")
    state.write_text(
        state.read_text(encoding="utf-8").rstrip()
        + "\n\n## Latest Block R6 step 1 Source-discovery checkpoint\n\nGit-backed reusable Source discovery now distinguishes the accepted Git provenance from the moving update-discovery surface. A Source pinned by current onboarding to an exact old commit can explicitly `source fetch` the repository's newer default-branch package; ContextCanon immediately freezes the candidate under its package digest and records the exact discovered Git commit beside it. Normal build and accepted Source pins remain untouched. R6 proceeds to binding review/accept to that exact candidate without live pulls.\n",
        encoding="utf-8",
    )


def apply() -> None:
    patch_git_transport()
    patch_cli()
    patch_tests()
    patch_docs()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--complete":
        complete()
    else:
        apply()
