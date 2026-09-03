from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path, PurePosixPath

from .model import CompiledPackage, SourceRef
from .package import PACKAGE_MANIFEST_PATH, load_package
from .parser import ContextCanonError, find_repo_root, parse_node


CANDIDATE_PROVENANCE_SCHEMA = "contextcanon/git-candidate-provenance/v0"
_GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def fetch_git_candidate(node_root: Path, source_id: str) -> tuple[CompiledPackage, Path]:
    """Fetch one immutable Source candidate through generic Git transport.

    This function discovers candidate bytes only. It never changes the accepted
    Source store or CONTEXT.src.md and it has no composition semantics.
    """

    node_root = node_root.resolve()
    parsed = parse_node(node_root, find_repo_root(node_root))
    source = _find_source(parsed.sources, source_id, parsed.metadata.name)
    _validate_git_source(source, node_root)

    checkout_parent = Path(tempfile.mkdtemp(prefix="contextcanon-git-"))
    checkout = checkout_parent / "repository"
    try:
        candidate_ref = _clone(source, checkout)
        candidate_root = _candidate_node_root(checkout, source)
        candidate = load_package(candidate_root)
        if candidate.metadata.id != source.id:
            raise ContextCanonError(
                f"Git Source {source.name} expects Node ID {source.id}, got {candidate.metadata.id} "
                f"at node-path {source.node_path}"
            )
        persisted = _persist_candidate(node_root, candidate_root, candidate)
        _persist_candidate_provenance(node_root, source, candidate, candidate_ref)
        return candidate, persisted
    finally:
        shutil.rmtree(checkout_parent, ignore_errors=True)


def _find_source(sources: tuple[SourceRef, ...], source_id: str, node_name: str) -> SourceRef:
    matches = [source for source in sources if source.id == source_id]
    if not matches:
        raise ContextCanonError(f"{node_name}: no Source with Node ID {source_id}")
    if len(matches) != 1:
        raise ContextCanonError(f"{node_name}: Source Node ID {source_id} is not unique")
    return matches[0]


def _validate_git_source(source: SourceRef, node_root: Path) -> None:
    if source.transport != "git":
        raise ContextCanonError(
            f"{node_root}: Source {source.name} does not declare transport=\"git\""
        )
    if not source.is_pinned:
        raise ContextCanonError(f"{node_root}: Git Source {source.name} must be exactly pinned before update discovery")
    if not source.transport_ref or source.node_path is None:
        raise ContextCanonError(f"{node_root}: Git Source {source.name} has incomplete transport metadata")


def _clone(source: SourceRef, destination: Path) -> str:
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


def _candidate_node_root(checkout: Path, source: SourceRef) -> Path:
    node_path = PurePosixPath(source.node_path or ".")
    candidate = checkout.joinpath(*node_path.parts).resolve()
    try:
        candidate.relative_to(checkout.resolve())
    except ValueError as exc:
        raise ContextCanonError(f"Git Source node-path escapes checkout: {source.node_path}") from exc
    if not candidate.is_dir():
        raise ContextCanonError(
            f"Git Source {source.name} node-path does not exist in ref {source.transport_ref}: {source.node_path}"
        )
    return candidate


def _persist_candidate(
    node_root: Path,
    candidate_root: Path,
    candidate: CompiledPackage,
) -> Path:
    store = node_root / ".context" / "candidates"
    store.mkdir(parents=True, exist_ok=True)
    destination = store / candidate.package_digest

    if destination.exists():
        existing = load_package(destination)
        if (
            existing.metadata.id == candidate.metadata.id
            and existing.normalized_digest == candidate.normalized_digest
            and existing.package_digest == candidate.package_digest
        ):
            return destination
        raise ContextCanonError(f"Candidate store path exists with different content: {destination}")

    staging = Path(tempfile.mkdtemp(prefix=f".{candidate.package_digest[:12]}-", dir=store))
    try:
        manifest_target = staging / PACKAGE_MANIFEST_PATH
        manifest_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(candidate_root / PACKAGE_MANIFEST_PATH, manifest_target)
        for file in candidate.files:
            target = staging / file.path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(candidate_root / file.path, target)

        staged = load_package(staging)
        if (
            staged.metadata.id != candidate.metadata.id
            or staged.normalized_digest != candidate.normalized_digest
            or staged.package_digest != candidate.package_digest
        ):
            raise ContextCanonError("Git Source candidate identity changed while staging")
        os.replace(staging, destination)
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
    return destination


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
