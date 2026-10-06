from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from .compiler import Compiler
from .model import CompiledPackage, RelationshipKind
from .onboarding_storage import RUN_MARKER, binding_from_row, enclosing_parent, freeze_package, provenance_path
from .version_store import package_key, version_path
from .onboarding import find_enclosing_context_root, project_root_from_snapshot, resolve_onboarding_scope
from .onboarding_structure import HumanStructurePlan
from .package import PACKAGE_MANIFEST_PATH, load_package, load_package_files
from .path_budget import preflight_paths
from .parser import ContextCanonError
from .onboarding_workspace import write_utf8


LEGACY_REUSABLE_CONTEXTS_SCHEMA = "contextcanon/onboarding-reusable-contexts/v0"
REUSABLE_CONTEXTS_SCHEMA = "contextcanon/onboarding-reusable-contexts/v1"
LEGACY_REUSABLE_CONTEXTS_STATE_SCHEMA = "contextcanon/onboarding-reusable-contexts-state/v0"
REUSABLE_CONTEXTS_STATE_SCHEMA = "contextcanon/onboarding-reusable-contexts-state/v1"
REUSABLE_CONTEXTS_STATE_NAME = "reusable-contexts.json"
FROZEN_CATALOG_DIR_NAME = "reusable-context-packages"
FROZEN_PROVENANCE_REL = ".context/onboarding-provenance.json"
FROZEN_PROVENANCE_SCHEMA = "contextcanon/onboarding-reusable-package-provenance/v0"
CATALOG_START = "<!-- contextcanon-reusable-catalog:start -->"
CATALOG_END = "<!-- contextcanon-reusable-catalog:end -->"
ASSIGNMENTS_START = "<!-- contextcanon-reusable-assignments:start -->"
ASSIGNMENTS_END = "<!-- contextcanon-reusable-assignments:end -->"
GENERATED_PROJECT_START = "<!-- contextcanon-reusable-project-nodes:start -->"
GENERATED_PROJECT_END = "<!-- contextcanon-reusable-project-nodes:end -->"
GENERATED_CATALOG_START = "<!-- contextcanon-reusable-found-nodes:start -->"
GENERATED_CATALOG_END = "<!-- contextcanon-reusable-found-nodes:end -->"

_HEADER_RE = re.compile(
    r'<!-- contextcanon-reusable-contexts schema="(?P<schema>[^"]+)" '
    r'evidence="(?P<evidence>[0-9a-f]{64})" structure="(?P<structure>[0-9a-f]{64})" -->'
)
_ASSIGN_RE = re.compile(
    r'^- \*\*(?P<target>.+?)\*\* \(`(?P<path>[^`]+)`\) ← '
    r'\*\*(?P<source>.+?)\*\* \(`(?P<version>[^`]+)`\)'
    r'(?: \[(?P<relationship>Parent|Reference)\])?$'
)
_PLAIN_ASSIGN_RE = re.compile(
    r'^(?:- )?(?P<target>.+) \((?P<path>.+)\) ← '
    r'(?P<source>.+) \((?P<version>.+)\)'
    r'(?: \[(?P<relationship>Parent|Reference)\])?$'
)
@dataclass(frozen=True)
class ReusableContextAssignment:
    target_node_key: str
    target_name: str
    target_path: str
    source_node_id: str
    source_name: str
    source_version: str
    source_normalized_digest: str
    source_package_digest: str
    relationship: RelationshipKind
    why: str

    @property
    def owner_spec(self) -> str:
        return f"{self.target_node_key}={self.source_node_id}"

    def to_dict(self) -> dict[str, str]:
        return {
            "target_node_key": self.target_node_key,
            "target_name": self.target_name,
            "target_path": self.target_path,
            "source_node_id": self.source_node_id,
            "source_name": self.source_name,
            "source_version": self.source_version,
            "source_normalized_digest": self.source_normalized_digest,
            "source_package_digest": self.source_package_digest,
            "relationship": self.relationship,
            "why": self.why,
        }


@dataclass(frozen=True)
class ReusableContextsPlan:
    evidence_digest: str
    structure_digest: str
    decision: str
    catalog_locations: tuple[str, ...]
    catalog_roots: tuple[Path, ...]
    catalog_packages: tuple[CompiledPackage, ...]
    assignments: tuple[ReusableContextAssignment, ...]
    review_digest: str

    @property
    def is_complete(self) -> bool:
        return self.decision == "accept"

    @property
    def catalog_package_inputs(self) -> tuple[str, ...]:
        return tuple(str(path) for path in self.catalog_roots)

    @property
    def owner_source_specs(self) -> tuple[str, ...]:
        return tuple(assignment.owner_spec for assignment in self.assignments)

    @property
    def owner_source_whys(self) -> dict[str, str]:
        return {assignment.owner_spec: assignment.why for assignment in self.assignments}

    @property
    def owner_source_relationships(self) -> dict[str, RelationshipKind]:
        return {assignment.owner_spec: assignment.relationship for assignment in self.assignments}


def _error(message: str) -> ContextCanonError:
    return ContextCanonError(f"Reusable Context setup: {message}")


def _between(text: str, start: str, end: str, label: str) -> str:
    if text.count(start) != 1 or text.count(end) != 1:
        raise _error(f"malformed {label} markers")
    a = text.index(start) + len(start)
    b = text.index(end, a)
    return text[a:b]


def _catalog_locations(text: str) -> tuple[str, ...]:
    body = _between(text, CATALOG_START, CATALOG_END, "Catalog locations")
    values: list[str] = []
    for raw in body.splitlines():
        line = raw.strip()
        if not line:
            continue

        # Human input is intentionally forgiving. A pasted path is the semantic
        # value; Markdown bullet/code/quote wrappers are only presentation.
        if line.startswith("- "):
            line = line[2:].strip()
        if len(line) >= 2 and (line[0], line[-1]) in {
            ("`", "`"),
            ('"', '"'),
            ("'", "'"),
        }:
            line = line[1:-1].strip()

        if not line:
            raise _error("Catalog location cannot be empty")
        if line.startswith("<!--"):
            raise _error("Catalog locations must contain paths, not machine markers")
        if line not in values:
            values.append(line)
    return tuple(values)

def _decision(text: str) -> str:
    matches = re.findall(r"(?m)^Decision: `([^`]+)`$", text)
    if len(matches) != 1 or matches[0] not in {"pending", "accept"}:
        raise _error("Decision must appear exactly once and be `pending` or `accept`")
    return matches[0]


def _enclosing_parent_package(snapshot_root: Path):
    root = snapshot_root.resolve()
    if not _shared_snapshot(root):
        return None
    frozen = enclosing_parent(root)
    return frozen[0] if frozen is not None else None


def _shared_snapshot(root: Path) -> bool:
    return (root / RUN_MARKER).is_file() or (
        root.parent.name == "onboarding" and root.parent.parent.name == ".context"
    )


def _candidate_manifest_paths(location: Path) -> list[Path]:
    if (location / ".context" / "package.json").is_file():
        return [location / ".context" / "package.json"]
    if not location.is_dir():
        raise _error(f"Catalog location does not exist or is not a directory: {location}")
    result: list[Path] = []
    for manifest in location.rglob("package.json"):
        if manifest.parent.name != ".context":
            continue
        rel_parts = manifest.relative_to(location).parts
        # Ignore accepted/candidate package caches inside another Node.
        if any(name in rel_parts for name in ("sources", "versions", "onboarding", "parent-candidates", "source-reviews", "parent-reviews")) and ".context" in rel_parts:
            continue
        if "candidates" in rel_parts and ".context" in rel_parts:
            continue
        result.append(manifest)
    return sorted(result)


def discover_catalog(locations: tuple[str, ...]) -> tuple[tuple[Path, ...], tuple[CompiledPackage, ...]]:
    by_id: dict[str, tuple[Path, CompiledPackage]] = {}
    for raw in locations:
        location = Path(raw).expanduser().resolve()
        manifests = _candidate_manifest_paths(location)
        if not manifests:
            raise _error(
                f"Catalog location contains no compiled Context package: {location}. "
                "Build/publish the reusable Node first or choose a directory containing compiled Nodes."
            )
        for manifest in manifests:
            root = manifest.parent.parent
            package = load_package(root)
            previous = by_id.get(package.metadata.id)
            if previous is not None:
                if package_key(previous[1]) != package_key(package):
                    raise _error(
                        f"Catalog contains more than one package version for {package.metadata.name} "
                        f"({package.metadata.id}); narrow the Catalog location before accepting the run"
                    )
                continue
            by_id[package.metadata.id] = (root, package)
    ordered = sorted(
        by_id.values(),
        key=lambda item: (item[1].metadata.name.casefold(), item[1].metadata.version, item[1].metadata.id),
    )
    return tuple(item[0] for item in ordered), tuple(item[1] for item in ordered)


def _git_text(root: Path, *args: str) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), *args],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except OSError:
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout.strip()


def _git_bytes(root: Path, *args: str) -> bytes | None:
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), *args],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError:
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout


def _package_artifact_git_paths(
    repository: Path,
    package_root: Path,
    package: CompiledPackage,
) -> tuple[str, ...]:
    try:
        node_rel = package_root.resolve().relative_to(repository.resolve())
    except ValueError as exc:
        raise _error(f"Catalog package root is not inside its Git repository: {package_root}") from exc

    prefix = PurePosixPath(node_rel.as_posix())
    paths: list[str] = []
    for relative in [PACKAGE_MANIFEST_PATH, *(file.path for file in package.files)]:
        pure = PurePosixPath(relative)
        if pure.is_absolute() or ".." in pure.parts or not pure.parts:
            raise _error(f"Catalog package contains unsafe artifact path: {relative}")
        combined = pure if prefix.as_posix() == "." else prefix / pure
        paths.append(combined.as_posix())
    return tuple(dict.fromkeys(paths))


def git_package_artifact_status(
    repository: Path,
    package_root: Path,
    package: CompiledPackage,
) -> bytes | None:
    """Return Git porcelain output only for bytes that make up the frozen package.

    A Context Node may physically contain other active project subtrees. Their
    dirty working files do not make this package ambiguous; only changes to the
    exact artifact files copied into the immutable package do.
    """

    paths = _package_artifact_git_paths(repository, package_root, package)
    chunks: list[bytes] = []
    for start in range(0, len(paths), 64):
        status = _git_bytes(
            repository,
            "--literal-pathspecs",
            "status",
            "--porcelain=v1",
            "-z",
            "--untracked-files=all",
            "--",
            *paths[start : start + 64],
        )
        if status is None:
            return None
        if status:
            chunks.append(status)
    return b"".join(chunks)


def _catalog_provenance(package_root: Path, package: CompiledPackage) -> dict[str, str]:
    repository_text = _git_text(package_root, "rev-parse", "--show-toplevel")
    if repository_text is None:
        return {
            "schema": FROZEN_PROVENANCE_SCHEMA,
            "package_digest": package.package_digest,
            "kind": "local",
            "locator": str(package_root.resolve()),
            "ref": "",
            "node_path": ".",
            "discovery_ref": "",
        }

    repository = Path(repository_text).resolve()
    try:
        node_path = package_root.resolve().relative_to(repository).as_posix() or "."
    except ValueError as exc:
        raise _error(f"Catalog package root is not inside its Git repository: {package_root}") from exc

    status = git_package_artifact_status(repository, package_root, package)
    if status:
        raise _error(
            f"Catalog package {package.metadata.name} has uncommitted package artifact changes; "
            "accept reusable Context only from exact committed package bytes"
        )

    exact = _git_text(repository, "rev-parse", "HEAD") or ""
    origin = _git_text(repository, "remote", "get-url", "origin") or ""
    branch = _git_text(repository, "branch", "--show-current") or ""
    if origin and re.fullmatch(r"[0-9a-f]{40}", exact):
        return {
            "schema": FROZEN_PROVENANCE_SCHEMA,
            "package_digest": package.package_digest,
            "kind": "git",
            "locator": origin,
            "ref": exact,
            "node_path": node_path,
            "discovery_ref": branch,
        }

    return {
        "schema": FROZEN_PROVENANCE_SCHEMA,
        "package_digest": package.package_digest,
        "kind": "local",
        "locator": str(repository),
        "ref": exact,
        "node_path": node_path,
        "discovery_ref": "",
    }


def _frozen_package_root(snapshot_root: Path, package_digest: str) -> Path:
    return snapshot_root.resolve() / FROZEN_CATALOG_DIR_NAME / package_digest


def _write_frozen_package(
    destination: Path,
    package_root: Path,
    package: CompiledPackage,
    provenance: dict[str, str],
) -> Path:
    if destination.exists():
        existing = load_package(destination)
        if existing.package_digest != package.package_digest:
            raise _error(f"Frozen reusable package path contains the wrong package: {destination}")
        provenance_path = destination / FROZEN_PROVENANCE_REL
        if not provenance_path.is_file():
            write_utf8(provenance_path, json.dumps(provenance, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
        return destination

    paths = (PACKAGE_MANIFEST_PATH, FROZEN_PROVENANCE_REL, *(file.path for file in package.files))
    preflight_paths(destination, paths, action="onboarding frozen reusable Context")
    temporary = destination.with_name(destination.name + ".tmp")
    preflight_paths(temporary, paths, action="onboarding frozen reusable Context staging")
    if temporary.exists():
        shutil.rmtree(temporary)
    try:
        for rel in [PACKAGE_MANIFEST_PATH, *(file.path for file in package.files)]:
            source = package_root / Path(*PurePosixPath(rel).parts)
            if not source.is_file():
                raise _error(f"Catalog package file disappeared while freezing: {source}")
            target = temporary / Path(*PurePosixPath(rel).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read_bytes())
        provenance_path = temporary / FROZEN_PROVENANCE_REL
        write_utf8(provenance_path, json.dumps(provenance, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
        verified = load_package(temporary)
        if verified.package_digest != package.package_digest:
            raise _error(
                f"Frozen reusable package digest mismatch for {package.metadata.name}: "
                f"expected {package.package_digest}, got {verified.package_digest}"
            )
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary.replace(destination)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary, ignore_errors=True)
    return destination


def _freeze_catalog(
    snapshot_root: Path,
    roots: tuple[Path, ...],
    packages: tuple[CompiledPackage, ...],
) -> tuple[Path, ...]:
    result: list[Path] = []
    for root, package in zip(roots, packages):
        destination = _frozen_package_root(snapshot_root, package.package_digest)
        provenance = _catalog_provenance(root, package)
        result.append(freeze_package(snapshot_root, root, package, provenance)
                      if _shared_snapshot(snapshot_root.resolve()) else
                      _write_frozen_package(destination, root, package, provenance))
    return tuple(result)


def _manifest_digest(raw: bytes) -> str | None:
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    digests = value.get("digests") if isinstance(value, dict) else None
    if not isinstance(digests, dict):
        return None
    digest = digests.get("package")
    return digest if isinstance(digest, str) else None


def _read_historical_package(original_root: Path, expected_digest: str, expected_binding=None):
    """Read/verify exact committed artifacts without modifying either repository."""
    original_root = original_root.resolve()
    anchor = original_root
    while not anchor.exists() and anchor != anchor.parent:
        anchor = anchor.parent
    repository_text = _git_text(anchor, "rev-parse", "--show-toplevel")
    if repository_text is None:
        return None
    repository = Path(repository_text).resolve()
    try:
        node_path = original_root.relative_to(repository).as_posix() or "."
    except ValueError:
        return None
    manifest_rel = PACKAGE_MANIFEST_PATH if node_path == "." else f"{node_path}/{PACKAGE_MANIFEST_PATH}"
    history = _git_text(repository, "log", "--all", "--format=%H", "--", manifest_rel)
    if not history:
        return None
    for commit in history.splitlines():
        manifest_bytes = _git_bytes(repository, "show", f"{commit}:{manifest_rel}")
        if manifest_bytes is None or _manifest_digest(manifest_bytes) != expected_digest:
            continue
        try:
            manifest = json.loads(manifest_bytes)
            rows = manifest.get("files", [])
            if not isinstance(rows, list) or any(not isinstance(row, dict) or not isinstance(row.get("path"), str) for row in rows):
                continue
        except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
            continue
        contents = {PACKAGE_MANIFEST_PATH: manifest_bytes}
        for row in rows:
            rel = row["path"]
            git_path = rel if node_path == "." else f"{node_path}/{rel}"
            data = _git_bytes(repository, "show", f"{commit}:{git_path}")
            if data is None:
                break
            # Git may have stored LF for a CRLF artifact whose original bytes
            # were bound by a legacy Windows manifest. Restore that one known
            # transport conversion only when its size AND full SHA prove the
            # exact original bytes. This is not package/EOL normalization.
            if len(data) != row.get("size") or hashlib.sha256(data).hexdigest() != row.get("sha256"):
                crlf = data.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
                if len(crlf) == row.get("size") and hashlib.sha256(crlf).hexdigest() == row.get("sha256"):
                    data = crlf
            contents[rel] = data
        else:
            try:
                package = load_package_files(contents)
            except ContextCanonError:
                continue
            if package.package_digest != expected_digest or (expected_binding is not None and package_key(package) != package_key(expected_binding)):
                continue
            origin = _git_text(repository, "remote", "get-url", "origin") or ""
            provenance = {
                "schema": FROZEN_PROVENANCE_SCHEMA,
                "package_digest": expected_digest,
                "kind": "git" if origin else "local",
                "locator": origin or str(repository),
                "ref": commit,
                "node_path": node_path,
                # Legacy review state did not bind a symbolic discovery branch.
                "discovery_ref": "",
            }
            return package, contents, provenance
    return None


def _recover_historical_package(
    snapshot_root: Path,
    original_root: Path,
    expected_digest: str,
    expected_binding=None,
) -> Path | None:
    recovered = _read_historical_package(original_root, expected_digest, expected_binding)
    if recovered is None:
        return None
    package, contents, provenance = recovered
    # Ordinary legacy runtime recovery still publishes an owned freeze. The
    # migration preview calls only the read-only reader above.
    with tempfile.TemporaryDirectory(prefix=".recover-") as directory:
        temporary = Path(directory)
        preflight_paths(temporary, contents, action="onboarding historical package recovery")
        for rel, data in contents.items():
            path = temporary / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        if _shared_snapshot(snapshot_root):
            return freeze_package(snapshot_root, temporary, package, provenance)
        return _write_frozen_package(_frozen_package_root(snapshot_root, expected_digest),
                                     temporary, package, provenance)


def _accepted_catalog_from_state(
    snapshot_root: Path,
    state: dict[str, object],
) -> tuple[tuple[Path, ...], tuple[CompiledPackage, ...]]:
    rows = state.get("catalog_packages")
    if not isinstance(rows, list):
        raise _error("reusable Context machine state has no valid Catalog package list")

    frozen_roots: list[Path] = []
    packages: list[CompiledPackage] = []
    for row in rows:
        if not isinstance(row, dict):
            raise _error("reusable Context machine state has an invalid Catalog package entry")
        original_path = row.get("path")
        expected_digest = row.get("package_digest")
        if not isinstance(original_path, str) or not isinstance(expected_digest, str):
            raise _error("reusable Context machine state has an incomplete Catalog package entry")

        binding = binding_from_row(row)
        shared = _shared_snapshot(snapshot_root.resolve())
        central = version_path(project_root_from_snapshot(snapshot_root), binding) if shared else None
        destination = central if central is not None and central.exists() else _frozen_package_root(snapshot_root, expected_digest)
        if not destination.is_dir():
            original_root = Path(original_path).expanduser().resolve()

            # Legacy STEP-07 state recorded exact identity but not package bytes.
            # Prefer recovery from Git history because it yields exact provenance
            # even when the current checkout has moved on or was temporarily restored.
            recovered = _recover_historical_package(snapshot_root, original_root, expected_digest, binding)
            if recovered is not None:
                destination = recovered
            else:
                current: CompiledPackage | None = None
                try:
                    current = load_package(original_root)
                except ContextCanonError:
                    current = None
                if current is not None and current.package_digest == expected_digest:
                    provenance = _catalog_provenance(original_root, current)
                    destination = (freeze_package(snapshot_root, original_root, current, provenance) if shared else
                                   _write_frozen_package(destination, original_root, current, provenance))
                else:
                    raise _error(
                        "Accepted reusable Context package bytes are not frozen and the exact historical package "
                        f"cannot be recovered: {row.get('name', row.get('id', expected_digest))} "
                        f"{row.get('version', '')} ({expected_digest}). "
                        "Provide the exact historical package checkout or restart reusable-Context review; "
                        "do not substitute the newer live Catalog package."
                    )

        package = load_package(destination)
        if package_key(package) != package_key(binding) or package.metadata.version != binding.version:
            raise _error(f"Frozen reusable package binding mismatch at {destination}")
        if shared and destination != central:
            provenance_file = destination / FROZEN_PROVENANCE_REL
            if not provenance_file.is_file():
                raise _error(f"Frozen reusable package has no exact provenance: {destination}")
            provenance = json.loads(provenance_file.read_text(encoding="utf-8"))
            destination = freeze_package(snapshot_root, destination, package, provenance)
        frozen_roots.append(destination)
        packages.append(package)

    return tuple(frozen_roots), tuple(packages)


def _parse_assignments(
    text: str,
    structure: HumanStructurePlan,
    packages: tuple[CompiledPackage, ...],
    *,
    enclosing_parent_node_id: str | None = None,
    reject_existing_parent_duplicate: bool = True,
    require_relationship: bool = True,
) -> tuple[ReusableContextAssignment, ...]:
    body = _between(text, ASSIGNMENTS_START, ASSIGNMENTS_END, "Assignments")
    target_by_label = {(node.name, node.path): node for node in structure.nodes}
    package_by_label: dict[tuple[str, str], list[CompiledPackage]] = {}
    for package in packages:
        package_by_label.setdefault((package.metadata.name, package.metadata.version), []).append(package)

    lines = body.splitlines()
    result: list[ReusableContextAssignment] = []
    seen: set[tuple[str, str]] = set()
    index = 0
    while index < len(lines):
        line = lines[index].strip()
        if not line or line in {"```", "```text"}:
            index += 1
            continue
        match = _ASSIGN_RE.fullmatch(line) or _PLAIN_ASSIGN_RE.fullmatch(line)
        if match is None:
            raise _error(
                f"Cannot parse Assignment line {line!r}. Expected raw text like "
                "'<project name> (<path>) ← <reusable Context name> (<version>) [Parent|Reference]'. "
                "Do not add Markdown bold markers or backticks; a leading list dash is optional."
            )
        if require_relationship and match.group("relationship") is None:
            raise _error(f"Assignment {line!r} needs an explicit [Parent] or [Reference] choice")
        target = target_by_label.get((match.group("target"), match.group("path")))
        if target is None:
            raise _error(
                f"Assignment target is not an accepted project Context Node: "
                f"{match.group('target')} ({match.group('path')})"
            )
        candidates = package_by_label.get((match.group("source"), match.group("version")), [])
        if not candidates:
            raise _error(
                f"Assignment Source is not present in the current Catalog: "
                f"{match.group('source')} {match.group('version')}"
            )
        if len(candidates) != 1:
            raise _error(
                f"Catalog label is ambiguous for {match.group('source')} {match.group('version')}; "
                "narrow the Catalog location"
            )
        index += 1
        if index >= len(lines):
            raise _error(f"Assignment {line!r} is missing its next-line 'Why: ...' rationale")
        why_line = lines[index].strip()
        if not why_line.startswith("Why:"):
            raise _error(f"Expected 'Why: ...' on the line after Assignment {line!r}; indentation is optional")
        why = why_line[4:].strip()
        if not why or why == "-":
            raise _error("Every reusable Context assignment needs a real Why rationale")
        package = candidates[0]
        relationship = (match.groupdict().get("relationship") or "Parent").lower()
        if relationship not in {"parent", "reference"}:
            raise _error(f"Unsupported reusable Context relationship {relationship!r}")
        if (
            reject_existing_parent_duplicate
            and enclosing_parent_node_id is not None
            and target.path == "."
            and package.metadata.id == enclosing_parent_node_id
        ):
            raise _error(
                f"{package.metadata.name} is already the enclosing Parent of the onboarding root; "
                "do not add it again as an Assignment"
            )
        identity = (target.key, package.metadata.id)
        if identity in seen:
            raise _error(f"Duplicate reusable Context assignment for {target.name} and {package.metadata.name}")
        seen.add(identity)
        result.append(
            ReusableContextAssignment(
                target_node_key=target.key,
                target_name=target.name,
                target_path=target.path,
                source_node_id=package.metadata.id,
                source_name=package.metadata.name,
                source_version=package.metadata.version,
                source_normalized_digest=package.normalized_digest,
                source_package_digest=package.package_digest,
                relationship=relationship,  # type: ignore[arg-type]
                why=why,
            )
        )
        index += 1
    return tuple(result)


def _normalized_payload(
    evidence_digest: str,
    structure_digest: str,
    decision: str,
    locations: tuple[str, ...],
    roots: tuple[Path, ...],
    packages: tuple[CompiledPackage, ...],
    assignments: tuple[ReusableContextAssignment, ...],
) -> dict[str, object]:
    return {
        "schema": REUSABLE_CONTEXTS_STATE_SCHEMA,
        "evidence_digest": evidence_digest,
        "structure_digest": structure_digest,
        "decision": decision,
        "catalog_locations": list(locations),
        "catalog_packages": [
            {
                "path": str(root),
                "id": package.metadata.id,
                "name": package.metadata.name,
                "version": package.metadata.version,
                "normalized_digest": package.normalized_digest,
                "package_digest": package.package_digest,
            }
            for root, package in zip(roots, packages)
        ],
        "assignments": [assignment.to_dict() for assignment in assignments],
    }


def _legacy_normalized_payload(
    evidence_digest: str,
    structure_digest: str,
    decision: str,
    locations: tuple[str, ...],
    roots: tuple[Path, ...],
    packages: tuple[CompiledPackage, ...],
    assignments: tuple[ReusableContextAssignment, ...],
) -> dict[str, object]:
    payload = _normalized_payload(
        evidence_digest,
        structure_digest,
        decision,
        locations,
        roots,
        packages,
        assignments,
    )
    payload["schema"] = LEGACY_REUSABLE_CONTEXTS_STATE_SCHEMA
    payload["assignments"] = [
        {key: value for key, value in assignment.to_dict().items() if key != "relationship"}
        for assignment in assignments
    ]
    return payload


def _digest(payload: dict[str, object]) -> str:
    data = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def render_reusable_contexts(
    evidence_digest: str,
    structure: HumanStructurePlan,
    decision: str,
    locations: tuple[str, ...],
    packages: tuple[CompiledPackage, ...],
    assignments: tuple[ReusableContextAssignment, ...],
    enclosing_parent=None,
) -> str:
    lines = [
        "# STEP 07 — Reusable Contexts",
        f'<!-- contextcanon-reusable-contexts schema="{REUSABLE_CONTEXTS_SCHEMA}" evidence="{evidence_digest}" structure="{structure.structure_digest}" -->',
        "",
        "Your project now has its own Context shelves. This step asks one simple question: **should any already-curated reusable Context also apply here?** For example, a shared Development Workflow or GitHub Local Context can be attached where it belongs instead of copying those rules into this project by hand.",
        "",
        "You choose the relationship explicitly. **Parent** is normative: its Rules apply here and its effective Context propagates to semantic Children. **Reference** is informational: its Rules do not apply and the relationship is not inherited by Children. ContextCanon keeps that exact choice through preview and publication.",
        "",
        "> **Important:** every editing/copy instruction in this file refers to the **raw Markdown text**, not to the rendered preview.",
        "",
        "> **Edit only** the two areas marked ✏️ below and the `Decision` line. Everything else is instruction or generated help and will be rewritten when you rerun this step.",
        "",
        "## Catalog locations",
        "",
        "First tell ContextCanon where it may look for reusable Context Nodes. Add one directory per line. A location may itself be one compiled Context Node or a directory containing several Nodes.",
        "",
        "Paste a path normally. Markdown bullets, backticks, or quotes are optional input conveniences; ContextCanon rewrites accepted input into one canonical Markdown form on the next run.",
        "",
        r"Example path: `C:\Users\you\PycharmProjects\context-canon\nodes\library`",
        "",
        "> ✏️ **EDIT HERE — Catalog locations start below.**",
        "",
        CATALOG_START,
    ]
    lines.extend(f"- `{value}`" for value in locations)
    lines.extend(
        [
            CATALOG_END,
            "",
            "> **END EDITABLE Catalog locations.**",
            "",
            "## Existing Parents — generated",
            "",
        ]
    )
    if enclosing_parent is None:
        lines.append("No enclosing Parent exists for this onboarding scope.")
    else:
        root_node = next((node for node in structure.nodes if node.path == "."), None)
        root_label = root_node.name if root_node is not None else "Onboarding root"
        lines.extend(
            [
                f"{root_label} (.) ← {enclosing_parent.metadata.name} ({enclosing_parent.metadata.version}) [Parent]",
                "Why: This is the already accepted nearest enclosing Context; its Rules govern this subtree.",
                "",
                "This relationship already exists. **Do not copy it into Assignments below.** ContextCanon publishes it once as the root's canonical Parent import.",
            ]
        )
    lines.extend(
        [
            "",
            "## Assignments",
            "",
            "An Assignment means: **this project Context Node imports this reusable Context as either Parent or Reference**. Keep the list sparse: add only relationships that should really exist. The arrow reads from the project Node on the left to the reusable Context it imports on the right.",
            "",
            "Use the generated raw-text lists at the bottom. For a project Node, copy everything after `Copy:` to the end of that raw Markdown line. For a reusable Context, copy everything after `Copy:` up to but not including ` — exact package`. Join those two fragments with ` ← `, append exactly ` [Parent]` or ` [Reference]`, then put `Why: ...` on the next line. Indentation is optional.",
            "",
            "There is deliberately **no Markdown formatting syntax to preserve** in an Assignment: no list dash, no bold markers and no backticks.",
            "",
            "Assignment syntax: **read-only help — do not edit here.**",
            "",
            "```text",
            "<project name> (<project path>) ← <reusable Context name> (<version>) [Parent]",
            "Why: <why this reusable Context governs this Node>",
            "",
            "<project name> (<project path>) ← <reusable Context name> (<version>) [Reference]",
            "Why: <why this reusable Context is useful information here>",
            "```",
            "",
            "> ✏️ **EDIT HERE — reusable-Context Assignments and Decision start below.**",
            "",
            f"Decision: `{decision}`",
            "",
            ASSIGNMENTS_START,
            "```text",
        ]
    )
    for assignment in assignments:
        lines.extend(
            [
                f"{assignment.target_name} ({assignment.target_path}) ← {assignment.source_name} ({assignment.source_version}) [{assignment.relationship.title()}]",
                f"Why: {assignment.why}",
            ]
        )
    lines.extend(
        [
            "```",
            ASSIGNMENTS_END,
            "",
            "> **END EDITABLE reusable-Context Assignments.**",
            "",
            "Set `Decision` to `accept` when every Assignment has the intended Parent/Reference meaning. An empty assignment list is valid when no additional reusable Context applies.",
            "",
            "## Available project Context Nodes — generated",
            "",
            "Raw Markdown: copy everything after `Copy:` to the end of the line.",
            "",
            GENERATED_PROJECT_START,
        ]
    )
    for node in structure.nodes:
        lines.append(f"- Copy: {node.name} ({node.path})")
    lines.extend(
        [
            GENERATED_PROJECT_END,
            "",
            "## Available reusable Context Nodes — generated",
            "",
            "Raw Markdown: copy everything after `Copy:` up to but not including ` — exact package`. The digest remains visible for review only.",
            "",
            GENERATED_CATALOG_START,
        ]
    )
    if packages:
        for package in packages:
            lines.append(
                f"- Copy: {package.metadata.name} ({package.metadata.version}) — exact package {package.package_digest}"
            )
    elif locations:
        lines.append("No verified reusable Context Nodes found.")
    else:
        lines.append("No Catalog locations yet. Add one or more above and run this step again.")
    lines.extend(
        [
            GENERATED_CATALOG_END,
            "",
            "Package identities are review information. ContextCanon resolves and remembers them automatically; never paste IDs or digests into Assignments.",
            "",
        ]
    )
    return "\n".join(lines)

def _initial_text(evidence_digest: str, structure: HumanStructurePlan, enclosing_parent=None) -> str:
    return render_reusable_contexts(
        evidence_digest, structure, "pending", (), (), (), enclosing_parent=enclosing_parent
    )


def _parse_bound_text(
    path: Path, evidence_digest: str, structure: HumanStructurePlan
) -> tuple[str, tuple[str, ...], str]:
    text = path.read_text(encoding="utf-8")
    header = _HEADER_RE.search(text)
    if header is None:
        raise _error(f"{path} is missing its ContextCanon binding header")
    schema = header.group("schema")
    if schema not in {REUSABLE_CONTEXTS_SCHEMA, LEGACY_REUSABLE_CONTEXTS_SCHEMA}:
        raise _error(f"unsupported schema {schema!r}")
    if header.group("evidence") != evidence_digest:
        raise _error("Evidence digest differs from this onboarding snapshot")
    if header.group("structure") != structure.structure_digest:
        raise _error(
            "Accepted project Context structure changed; recreate/review STEP-07-reusable-contexts.md against the new structure"
        )
    return text, _catalog_locations(text), schema


def refresh_reusable_contexts(
    path: Path,
    snapshot_root: Path,
    evidence_digest: str,
    structure: HumanStructurePlan,
) -> tuple[ReusableContextsPlan, bool]:
    path = path.resolve()
    enclosing_parent = _enclosing_parent_package(snapshot_root)
    created = False
    if not path.exists():
        write_utf8(path, _initial_text(evidence_digest, structure, enclosing_parent))
        created = True
    text, locations, human_schema = _parse_bound_text(path, evidence_digest, structure)
    decision = _decision(text)

    # Once STEP 07 is accepted and unchanged, rerunning the command is idempotent:
    # use the already frozen exact package set rather than reopening the moving Catalog.
    state_path = snapshot_root.resolve() / REUSABLE_CONTEXTS_STATE_NAME
    if decision == "accept" and state_path.is_file():
        try:
            prior = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            prior = None
        if (
            isinstance(prior, dict)
            and prior.get("decision") == "accept"
            and prior.get("human_file_sha256") == hashlib.sha256(path.read_bytes()).hexdigest()
        ):
            return load_accepted_reusable_contexts(
                path,
                snapshot_root,
                evidence_digest,
                structure,
            ), created

    roots, packages = discover_catalog(locations) if locations else ((), ())
    assignments = _parse_assignments(
        text,
        structure,
        packages,
        require_relationship=human_schema != LEGACY_REUSABLE_CONTEXTS_SCHEMA,
        enclosing_parent_node_id=(
            enclosing_parent.metadata.id if enclosing_parent is not None else None
        ),
    )
    canonical = render_reusable_contexts(
        evidence_digest,
        structure,
        decision,
        locations,
        packages,
        assignments,
        enclosing_parent=enclosing_parent,
    )
    write_utf8(path, canonical)
    payload = _normalized_payload(
        evidence_digest,
        structure.structure_digest,
        decision,
        locations,
        roots,
        packages,
        assignments,
    )
    review_digest = _digest(payload)
    effective_roots = _freeze_catalog(snapshot_root, roots, packages) if decision == "accept" else roots
    payload["review_digest"] = review_digest
    payload["human_file_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    if decision == "accept":
        payload["frozen_catalog_packages"] = [
            {
                "package_digest": package.package_digest,
                "id": package.metadata.id,
                "normalized_digest": package.normalized_digest,
                "path": str(root),
            }
            for root, package in zip(effective_roots, packages)
        ]
    write_utf8(
        snapshot_root.resolve() / REUSABLE_CONTEXTS_STATE_NAME,
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    return ReusableContextsPlan(
        evidence_digest,
        structure.structure_digest,
        decision,
        locations,
        effective_roots,
        packages,
        assignments,
        review_digest,
    ), created


def load_accepted_reusable_contexts(
    path: Path,
    snapshot_root: Path,
    evidence_digest: str,
    structure: HumanStructurePlan,
) -> ReusableContextsPlan:
    state_path = snapshot_root.resolve() / REUSABLE_CONTEXTS_STATE_NAME
    if not state_path.is_file():
        raise _error("STEP 07 has not been validated yet; run `contextcanon onboard reusable-contexts` first")
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise _error(f"machine state is unreadable: {state_path}") from exc
    state_schema = state.get("schema")
    if state_schema not in {
        REUSABLE_CONTEXTS_STATE_SCHEMA,
        LEGACY_REUSABLE_CONTEXTS_STATE_SCHEMA,
    }:
        raise _error("unsupported reusable Context machine state")
    if state.get("evidence_digest") != evidence_digest or state.get("structure_digest") != structure.structure_digest:
        raise _error("reusable Context machine state does not match this Evidence/Structure")
    if state.get("decision") != "accept":
        raise _error("STEP 07 is still pending; set Decision to `accept` and rerun the step")
    if not path.is_file():
        raise _error(f"missing human reusable Context review: {path}")
    current_sha = hashlib.sha256(path.read_bytes()).hexdigest()
    if current_sha != state.get("human_file_sha256"):
        raise _error("STEP-07-reusable-contexts.md changed after validation; rerun `contextcanon onboard reusable-contexts`")

    text, locations, human_schema = _parse_bound_text(path, evidence_digest, structure)
    if state_schema == REUSABLE_CONTEXTS_STATE_SCHEMA and human_schema != REUSABLE_CONTEXTS_SCHEMA:
        raise _error("canonical reusable Context state is bound to a legacy human review schema")
    roots, packages = _accepted_catalog_from_state(snapshot_root, state) if locations else ((), ())
    enclosing_parent = _enclosing_parent_package(snapshot_root)
    assignments = _parse_assignments(
        text,
        structure,
        packages,
        require_relationship=human_schema != LEGACY_REUSABLE_CONTEXTS_SCHEMA,
        enclosing_parent_node_id=(
            enclosing_parent.metadata.id if enclosing_parent is not None else None
        ),
        reject_existing_parent_duplicate=state_schema != LEGACY_REUSABLE_CONTEXTS_STATE_SCHEMA,
    )

    state_rows = state.get("catalog_packages", [])
    if not isinstance(state_rows, list):
        raise _error("reusable Context machine state has no valid Catalog package list")
    original_roots = tuple(
        Path(row["path"])
        for row in state_rows
        if isinstance(row, dict) and isinstance(row.get("path"), str)
    )
    if len(original_roots) != len(packages):
        raise _error("reusable Context machine state Catalog package count is inconsistent")

    payload_factory = (
        _legacy_normalized_payload
        if state_schema == LEGACY_REUSABLE_CONTEXTS_STATE_SCHEMA
        else _normalized_payload
    )
    payload = payload_factory(
        evidence_digest,
        structure.structure_digest,
        "accept",
        locations,
        original_roots,
        packages,
        assignments,
    )
    review_digest = _digest(payload)
    if review_digest != state.get("review_digest"):
        raise _error(
            "Frozen reusable Context package identity no longer matches the accepted STEP 07 review"
        )
    return ReusableContextsPlan(
        evidence_digest,
        structure.structure_digest,
        "accept",
        locations,
        roots,
        packages,
        assignments,
        review_digest,
    )
