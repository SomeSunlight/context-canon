from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path, PurePosixPath

from .config import configured_source
from .model import CompiledPackage, SourceRef
from .package import PACKAGE_MANIFEST_PATH, load_package
from .parser import ContextCanonError, find_repo_root, parse_node


CANDIDATE_PROVENANCE_SCHEMA = "contextcanon/git-candidate-provenance/v0"
CONFIGURED_CANDIDATE_PROVENANCE_SCHEMA = "contextcanon/source-candidate-provenance/v1"
_GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def resolve_git_package_provenance(package_root: Path) -> dict[str, str]:
    """Resolve clean, exact Git provenance for one already-published package Node.

    This is a read-only first-adoption helper. It never fetches and never
    guesses a branch: the package bytes must already exist in a clean Git
    checkout, and the returned ``ref`` is the checkout's exact HEAD commit.
    """

    package_root = package_root.resolve()

    def read(root: Path, *args: str) -> str:
        try:
            completed = subprocess.run(
                ["git", "-C", str(root), *args],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
        except FileNotFoundError as exc:
            raise ContextCanonError("Git Source provenance requires the 'git' executable on PATH") from exc
        except OSError as exc:
            raise ContextCanonError(f"Could not start Git Source provenance lookup: {exc}") from exc
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip() or f"exit code {completed.returncode}"
            raise ContextCanonError(f"Could not resolve Git Source provenance: {detail}")
        return completed.stdout.strip()

    repository = Path(read(package_root, "rev-parse", "--show-toplevel")).resolve()
    try:
        node_path = package_root.relative_to(repository).as_posix() or "."
    except ValueError as exc:
        raise ContextCanonError(f"Source package root is not inside its Git repository: {package_root}") from exc

    status = read(
        repository,
        "status",
        "--porcelain",
        "--untracked-files=all",
        "--",
        node_path,
    )
    if status:
        raise ContextCanonError(
            "Source package path has uncommitted changes; exact first-adoption provenance would be ambiguous"
        )

    ref = read(repository, "rev-parse", "HEAD")
    if not _GIT_SHA_RE.fullmatch(ref):
        raise ContextCanonError(f"Source Git HEAD is not an exact commit SHA: {ref!r}")
    locator = read(repository, "remote", "get-url", "origin")
    if not locator:
        raise ContextCanonError("Source Git repository has no usable origin locator")
    if any(char in locator for char in '"\n\r])'):
        raise ContextCanonError("Source Git origin cannot be represented safely in Context authoring")
    if any(char in node_path for char in '"\n\r'):
        raise ContextCanonError("Source Git node path cannot be represented safely in Context authoring")
    return {"locator": locator, "ref": ref, "node_path": node_path}


def fetch_git_candidate(
    node_root: Path,
    source_id: str,
    discovery_ref: str | None = None,
) -> tuple[CompiledPackage, Path]:
    """Fetch one immutable Source candidate through central or legacy transport metadata."""

    node_root = node_root.resolve()
    parsed = parse_node(node_root, find_repo_root(node_root))
    source = _find_source(parsed.sources, source_id, parsed.metadata.name)
    configured = configured_source(parsed.repo_root, source_id)

    if configured is not None:
        source_config, repository = configured
        if repository.kind == "local":
            if discovery_ref is not None:
                raise ContextCanonError("--ref cannot be used with a local ContextCanon repository")
            repository_root = repository.resolve_local(parsed.repo_root)
            candidate_root = _configured_candidate_node_root(repository_root, source_config.node_path, source.name)
            candidate = load_package(candidate_root)
            if candidate.metadata.id != source.id:
                raise ContextCanonError(
                    f"Configured Source {source.name} expects Node ID {source.id}, got {candidate.metadata.id}"
                )
            persisted = _persist_candidate(node_root, candidate_root, candidate)
            _persist_configured_candidate_provenance(
                node_root,
                source,
                candidate,
                kind="local",
                location=repository.location,
                discovery_ref="",
                candidate_ref="",
                node_path=source_config.node_path,
            )
            return candidate, persisted

        ref = discovery_ref if discovery_ref is not None else repository.ref
        checkout_parent = Path(tempfile.mkdtemp(prefix="contextcanon-git-"))
        checkout = checkout_parent / "repository"
        try:
            candidate_ref = _clone_location(repository.location, checkout, ref)
            candidate_root = _configured_candidate_node_root(checkout, source_config.node_path, source.name)
            candidate = load_package(candidate_root)
            if candidate.metadata.id != source.id:
                raise ContextCanonError(
                    f"Configured Source {source.name} expects Node ID {source.id}, got {candidate.metadata.id}"
                )
            persisted = _persist_candidate(node_root, candidate_root, candidate)
            _persist_configured_candidate_provenance(
                node_root,
                source,
                candidate,
                kind="git",
                location=repository.location,
                discovery_ref=ref or "",
                candidate_ref=candidate_ref,
                node_path=source_config.node_path,
            )
            return candidate, persisted
        finally:
            shutil.rmtree(checkout_parent, ignore_errors=True)

    _validate_git_source(source, node_root)
    checkout_parent = Path(tempfile.mkdtemp(prefix="contextcanon-git-"))
    checkout = checkout_parent / "repository"
    try:
        if discovery_ref is None:
            candidate_ref = _clone(source, checkout)
        else:
            candidate_ref = _clone_location(source.locator, checkout, discovery_ref)
        candidate_root = _candidate_node_root(checkout, source)
        candidate = load_package(candidate_root)
        if candidate.metadata.id != source.id:
            raise ContextCanonError(
                f"Git Source {source.name} expects Node ID {source.id}, got {candidate.metadata.id} "
                f"at node-path {source.node_path}"
            )
        persisted = _persist_candidate(node_root, candidate_root, candidate)
        if discovery_ref is None:
            _persist_candidate_provenance(node_root, source, candidate, candidate_ref)
        else:
            _persist_configured_candidate_provenance(
                node_root,
                source,
                candidate,
                kind="git",
                location=source.locator,
                discovery_ref=discovery_ref,
                candidate_ref=candidate_ref,
                node_path=source.node_path or ".",
            )
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
    """Clone legacy discovery semantics while keeping exact accepted SHAs non-live."""
    ref = source.transport_ref
    if ref and _GIT_SHA_RE.fullmatch(ref):
        ref = None
    return _clone_location(source.locator, destination, ref)


def _clone_location(locator: str, destination: Path, ref: str | None) -> str:
    if ref and _GIT_SHA_RE.fullmatch(ref):
        command = ["git", "clone", "--quiet", "--no-checkout", locator, str(destination)]
    else:
        command = ["git", "clone", "--quiet", "--depth", "1", "--single-branch"]
        if ref:
            command.extend(["--branch", ref])
        command.extend([locator, str(destination)])
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
        raise ContextCanonError(f"Git Source fetch failed for discovery ref {ref or 'remote default branch'}: {detail}")

    if ref and _GIT_SHA_RE.fullmatch(ref):
        fetch = subprocess.run(
            ["git", "-C", str(destination), "fetch", "--quiet", "--depth", "1", "origin", ref],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        if fetch.returncode != 0:
            detail = fetch.stderr.strip() or fetch.stdout.strip() or f"exit code {fetch.returncode}"
            raise ContextCanonError(f"Git Source fetch failed for exact ref {ref}: {detail}")
        checkout = subprocess.run(
            ["git", "-C", str(destination), "checkout", "--quiet", "FETCH_HEAD"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        if checkout.returncode != 0:
            detail = checkout.stderr.strip() or checkout.stdout.strip() or f"exit code {checkout.returncode}"
            raise ContextCanonError(f"Could not checkout exact Git Source ref {ref}: {detail}")

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


def _configured_candidate_node_root(repository: Path, node_path: str, source_name: str) -> Path:
    root = repository.resolve()
    path = PurePosixPath(node_path)
    candidate = root.joinpath(*path.parts).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ContextCanonError(f"Configured Source {source_name} path escapes repository: {node_path}") from exc
    if not candidate.is_dir():
        raise ContextCanonError(f"Configured Source {source_name} path does not exist: {candidate}")
    return candidate

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
        raise ContextCanonError(f"Invalid Source candidate provenance {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ContextCanonError(f"Invalid Source candidate provenance schema in {path}")
    schema = raw.get("schema")
    if schema == CANDIDATE_PROVENANCE_SCHEMA:
        required = {"schema", "source_id", "locator", "accepted_ref", "candidate_ref", "node_path", "package_digest"}
        if set(raw) != required:
            raise ContextCanonError(f"Invalid Git Source candidate provenance schema in {path}")
        values = {key: str(value) for key, value in raw.items()}
        if not _GIT_SHA_RE.fullmatch(values["candidate_ref"]):
            raise ContextCanonError(f"Invalid exact Git Source candidate commit in {path}")
    elif schema == CONFIGURED_CANDIDATE_PROVENANCE_SCHEMA:
        required = {"schema", "source_id", "kind", "location", "discovery_ref", "candidate_ref", "node_path", "package_digest"}
        if set(raw) != required or raw.get("kind") not in {"git", "local"}:
            raise ContextCanonError(f"Invalid configured Source candidate provenance schema in {path}")
        values = {key: str(value) for key, value in raw.items()}
        if values["kind"] == "git" and not _GIT_SHA_RE.fullmatch(values["candidate_ref"]):
            raise ContextCanonError(f"Invalid exact configured Git Source candidate commit in {path}")
        if values["kind"] == "local" and values["candidate_ref"]:
            raise ContextCanonError(f"Local Source candidate provenance must not invent a Git commit in {path}")
    else:
        raise ContextCanonError(f"Invalid Source candidate provenance schema in {path}")
    if values["package_digest"] != package_digest:
        raise ContextCanonError(f"Source candidate provenance digest mismatch in {path}")
    return values


def _persist_configured_candidate_provenance(
    node_root: Path,
    source: SourceRef,
    candidate: CompiledPackage,
    *,
    kind: str,
    location: str,
    discovery_ref: str,
    candidate_ref: str,
    node_path: str,
) -> Path:
    path = candidate_provenance_path(node_root, candidate.package_digest)
    payload = {
        "schema": CONFIGURED_CANDIDATE_PROVENANCE_SCHEMA,
        "source_id": source.id,
        "kind": kind,
        "location": location,
        "discovery_ref": discovery_ref,
        "candidate_ref": candidate_ref,
        "node_path": node_path,
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
