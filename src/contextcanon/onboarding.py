from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable

from .parser import ContextCanonError


EVIDENCE_SCHEMA = "contextcanon/onboarding-evidence/v0"
SELECTION_POLICY = "contextcanon/onboarding-default/v0"
MAX_EVIDENCE_FILE_BYTES = 1024 * 1024
_TEXT_SUFFIXES = {".md", ".mdx", ".rst", ".txt", ".adoc", ".asciidoc"}
_ROOT_DOCUMENT_PREFIXES = {
    "ARCHITECTURE",
    "CHANGELOG",
    "CONTRIBUTING",
    "DESIGN",
    "DEVELOPING",
    "DEVELOPMENT",
    "README",
    "SECURITY",
    "SUPPORT",
}
_AGENT_FILENAMES = {"agents.md", "claude.md", "gemini.md", ".goosehints"}
_ROOT_MANIFESTS = {
    ".editorconfig",
    ".pre-commit-config.yaml",
    ".pre-commit-config.yml",
    "build.gradle",
    "build.gradle.kts",
    "cargo.toml",
    "cmakelists.txt",
    "compose.yaml",
    "compose.yml",
    "docker-compose.yaml",
    "docker-compose.yml",
    "dockerfile",
    "go.mod",
    "go.work",
    "makefile",
    "mypy.ini",
    "package.json",
    "pom.xml",
    "pyproject.toml",
    "pytest.ini",
    "ruff.toml",
    "setup.cfg",
    "settings.gradle",
    "settings.gradle.kts",
    "tox.ini",
}
_BLOCKED_COMPONENTS = {".git", ".context", ".venv", "__pycache__", "node_modules", "venv"}
_SENSITIVE_FILENAMES = {
    ".netrc",
    ".npmrc",
    ".pypirc",
    "credentials",
    "credentials.json",
    "id_ed25519",
    "id_rsa",
    "secrets",
    "secrets.json",
}
_SENSITIVE_STEMS = {"credentials", "secrets"}
_SENSITIVE_SUFFIXES = {".jks", ".kdbx", ".key", ".keystore", ".p12", ".pem", ".pfx"}


@dataclass(frozen=True)
class EvidenceEntry:
    path: str
    sha256: str
    size: int
    reason: str

    @property
    def snapshot_path(self) -> str:
        return f"evidence/{self.path}"

    def to_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "reason": self.reason,
            "sha256": self.sha256,
            "size": self.size,
            "snapshot": self.snapshot_path,
        }


@dataclass(frozen=True)
class ExcludedEvidence:
    path: str
    reason: str

    def to_dict(self) -> dict[str, str]:
        return {"path": self.path, "reason": self.reason}


@dataclass(frozen=True)
class PreparedEvidence:
    project_root: Path
    snapshot_root: Path
    evidence_digest: str
    included: tuple[EvidenceEntry, ...]
    excluded: tuple[ExcludedEvidence, ...]

    @property
    def manifest_path(self) -> Path:
        return self.snapshot_root / "manifest.json"


def _run_git(project_root: Path, *args: str) -> bytes:
    try:
        result = subprocess.run(
            ["git", "-C", str(project_root), *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except FileNotFoundError as exc:
        raise ContextCanonError("Git is required for onboarding inventory but was not found") from exc
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        suffix = f": {detail}" if detail else ""
        raise ContextCanonError(f"Git onboarding inventory failed{suffix}")
    return result.stdout


def _same_path(left: Path, right: Path) -> bool:
    return os.path.normcase(str(left.resolve())) == os.path.normcase(str(right.resolve()))


def _require_git_repository_root(path: Path) -> Path:
    project_root = path.resolve()
    if not project_root.is_dir():
        raise ContextCanonError(f"Onboarding project is not a directory: {project_root}")
    raw = _run_git(project_root, "rev-parse", "--show-toplevel")
    try:
        git_root = Path(raw.decode("utf-8").strip()).resolve()
    except UnicodeDecodeError as exc:
        raise ContextCanonError("Git repository root is not valid UTF-8") from exc
    if not _same_path(project_root, git_root):
        raise ContextCanonError(
            f"onboard prepare must target the Git repository root; repository root is {git_root}"
        )
    return project_root


def _repository_paths(project_root: Path) -> list[str]:
    raw = _run_git(project_root, "ls-files", "--cached", "--others", "--exclude-standard", "-z")
    result: list[str] = []
    for item in raw.split(b"\0"):
        if not item:
            continue
        try:
            path = item.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ContextCanonError("Git repository contains a path that is not valid UTF-8") from exc
        pure = PurePosixPath(path)
        if pure.is_absolute() or ".." in pure.parts:
            raise ContextCanonError(f"Git returned unsafe repository path: {path}")
        result.append(pure.as_posix())
    return sorted(set(result))


def _default_reason(path: str) -> str | None:
    pure = PurePosixPath(path)
    parts = pure.parts
    name = pure.name
    lower_name = name.lower()

    if lower_name in _AGENT_FILENAMES:
        return "agent-instruction"
    if path.lower() == ".github/copilot-instructions.md":
        return "agent-instruction"
    if len(parts) >= 3 and tuple(part.lower() for part in parts[:2]) == (".github", "instructions"):
        if pure.suffix.lower() in _TEXT_SUFFIXES:
            return "agent-instruction"

    if any(part.lower() in {"docs", "doc", "documentation"} for part in parts[:-1]):
        if pure.suffix.lower() in _TEXT_SUFFIXES:
            return "documentation"

    if len(parts) == 1:
        upper_name = name.upper()
        prefix = upper_name.split(".", 1)[0]
        if prefix in _ROOT_DOCUMENT_PREFIXES:
            return "root-document"
        if lower_name in _ROOT_MANIFESTS or (
            lower_name.startswith("requirements") and lower_name.endswith(".txt")
        ):
            return "project-manifest"

    if len(parts) >= 3 and tuple(part.lower() for part in parts[:2]) == (".github", "workflows"):
        if pure.suffix.lower() in {".yml", ".yaml"}:
            return "ci-workflow"

    return None


def _blocked_reason(path: str) -> str | None:
    pure = PurePosixPath(path)
    lower_parts = tuple(part.lower() for part in pure.parts)
    if any(part in _BLOCKED_COMPONENTS for part in lower_parts[:-1]):
        return "framework-or-derived-path"

    lower_name = pure.name.lower()
    if lower_name == ".env" or lower_name.startswith(".env."):
        return "sensitive-path"
    if (
        lower_name in _SENSITIVE_FILENAMES
        or PurePosixPath(lower_name).stem in _SENSITIVE_STEMS
        or pure.suffix.lower() in _SENSITIVE_SUFFIXES
    ):
        return "sensitive-path"
    if any(part in {"credentials", "secrets"} for part in lower_parts[:-1]):
        return "sensitive-path"
    return None


def _safe_project_file(project_root: Path, relative: str) -> Path:
    pure = PurePosixPath(relative)
    if pure.is_absolute() or ".." in pure.parts:
        raise ContextCanonError(f"Unsafe onboarding evidence path: {relative}")
    candidate = project_root.joinpath(*pure.parts)
    try:
        candidate.resolve().relative_to(project_root)
    except ValueError as exc:
        raise ContextCanonError(f"Onboarding evidence escapes project root: {relative}") from exc
    return candidate


def _explicit_path(project_root: Path, value: str) -> str:
    raw = Path(value)
    if raw.is_absolute():
        raise ContextCanonError(f"Explicit onboarding include must be repository-relative: {value}")
    raw_candidate = project_root / raw
    if raw_candidate.is_symlink():
        raise ContextCanonError(f"Explicit onboarding include must not be a symlink: {value}")
    candidate = raw_candidate.resolve()
    try:
        relative = candidate.relative_to(project_root)
    except ValueError as exc:
        raise ContextCanonError(f"Explicit onboarding include escapes repository: {value}") from exc
    if not candidate.exists():
        raise ContextCanonError(f"Explicit onboarding include does not exist: {relative.as_posix()}")
    if not candidate.is_file():
        raise ContextCanonError(f"Explicit onboarding include must be a regular file: {relative.as_posix()}")
    path = relative.as_posix()
    blocked = _blocked_reason(path)
    if blocked:
        raise ContextCanonError(f"Explicit onboarding include is blocked ({blocked}): {path}")
    return path


def _collect_entry(project_root: Path, path: str, reason: str, explicit: bool) -> tuple[EvidenceEntry | None, ExcludedEvidence | None, bytes | None]:
    blocked = _blocked_reason(path)
    if blocked:
        if explicit:
            raise ContextCanonError(f"Explicit onboarding include is blocked ({blocked}): {path}")
        return None, ExcludedEvidence(path, blocked), None

    pure = PurePosixPath(path)
    raw_source = project_root.joinpath(*pure.parts)
    if raw_source.is_symlink():
        if explicit:
            raise ContextCanonError(f"Explicit onboarding include must not be a symlink: {path}")
        return None, ExcludedEvidence(path, "symlink"), None

    source = _safe_project_file(project_root, path)
    if not source.is_file():
        raise ContextCanonError(f"Onboarding evidence changed during preparation or is not a file: {path}")

    size = source.stat().st_size
    if size > MAX_EVIDENCE_FILE_BYTES:
        if explicit:
            raise ContextCanonError(
                f"Explicit onboarding include exceeds {MAX_EVIDENCE_FILE_BYTES} bytes: {path}"
            )
        return None, ExcludedEvidence(path, "too-large"), None

    data = source.read_bytes()
    if len(data) != size:
        raise ContextCanonError(f"Onboarding evidence changed while being read: {path}")
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        if explicit:
            raise ContextCanonError(f"Explicit onboarding include is not UTF-8 text: {path}")
        return None, ExcludedEvidence(path, "non-utf8"), None

    digest = hashlib.sha256(data).hexdigest()
    return EvidenceEntry(path=path, sha256=digest, size=size, reason=reason), None, data


def _manifest_payload(
    included: tuple[EvidenceEntry, ...], excluded: tuple[ExcludedEvidence, ...]
) -> dict[str, object]:
    return {
        "schema": EVIDENCE_SCHEMA,
        "selection": {
            "accepted_encoding": "utf-8",
            "max_file_bytes": MAX_EVIDENCE_FILE_BYTES,
            "policy": SELECTION_POLICY,
            "repository_listing": "git ls-files --cached --others --exclude-standard",
        },
        "included": [entry.to_dict() for entry in included],
        "excluded": [entry.to_dict() for entry in excluded],
    }


def _evidence_digest(payload: dict[str, object]) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _manifest_bytes(payload: dict[str, object], digest: str) -> bytes:
    manifest = dict(payload)
    manifest["evidence_digest"] = digest
    return (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _verify_existing_snapshot(
    snapshot_root: Path,
    manifest_bytes: bytes,
    included: tuple[EvidenceEntry, ...],
) -> None:
    manifest_path = snapshot_root / "manifest.json"
    if not manifest_path.is_file() or manifest_path.read_bytes() != manifest_bytes:
        raise ContextCanonError(f"Existing onboarding evidence snapshot is corrupt: {snapshot_root}")

    evidence_root = snapshot_root / "evidence"
    actual: set[str] = set()
    if evidence_root.exists():
        for path in evidence_root.rglob("*"):
            if path.is_symlink():
                raise ContextCanonError(f"Existing onboarding evidence snapshot contains symlink: {path}")
            if path.is_file():
                actual.add(path.relative_to(evidence_root).as_posix())
    expected = {entry.path for entry in included}
    if actual != expected:
        raise ContextCanonError(f"Existing onboarding evidence snapshot has wrong file set: {snapshot_root}")

    for entry in included:
        path = evidence_root.joinpath(*PurePosixPath(entry.path).parts)
        data = path.read_bytes()
        if len(data) != entry.size or hashlib.sha256(data).hexdigest() != entry.sha256:
            raise ContextCanonError(f"Existing onboarding evidence snapshot has modified file: {entry.path}")


def prepare_onboarding_evidence(
    project: Path,
    *,
    explicit_paths: Iterable[str] = (),
) -> PreparedEvidence:
    project_root = _require_git_repository_root(project)

    selected: dict[str, tuple[str, bool]] = {}
    for path in _repository_paths(project_root):
        # ContextCanon/derived trees are outside the project-evidence domain. In
        # particular, an earlier onboarding snapshot must never become a new
        # candidate merely because it contains copied docs/ paths.
        if _blocked_reason(path) == "framework-or-derived-path":
            continue
        reason = _default_reason(path)
        if reason:
            selected[path] = (reason, False)

    for value in explicit_paths:
        path = _explicit_path(project_root, value)
        selected[path] = ("explicit", True)

    included_items: list[EvidenceEntry] = []
    excluded_items: list[ExcludedEvidence] = []
    content: dict[str, bytes] = {}
    for path in sorted(selected):
        reason, explicit = selected[path]
        entry, excluded, data = _collect_entry(project_root, path, reason, explicit)
        if entry is not None and data is not None:
            included_items.append(entry)
            content[path] = data
        elif excluded is not None:
            excluded_items.append(excluded)

    included = tuple(included_items)
    excluded = tuple(excluded_items)
    payload = _manifest_payload(included, excluded)
    digest = _evidence_digest(payload)
    manifest = _manifest_bytes(payload, digest)

    base = project_root / ".context" / "onboarding"
    snapshot_root = base / digest
    if snapshot_root.exists():
        _verify_existing_snapshot(snapshot_root, manifest, included)
        return PreparedEvidence(project_root, snapshot_root, digest, included, excluded)

    base.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".prepare-", dir=base))
    try:
        evidence_root = staging / "evidence"
        for entry in included:
            destination = evidence_root.joinpath(*PurePosixPath(entry.path).parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content[entry.path])
        (staging / "manifest.json").write_bytes(manifest)
        try:
            os.rename(staging, snapshot_root)
        except OSError:
            if not snapshot_root.exists():
                raise
            _verify_existing_snapshot(snapshot_root, manifest, included)
    finally:
        if staging.exists():
            shutil.rmtree(staging)

    return PreparedEvidence(project_root, snapshot_root, digest, included, excluded)
