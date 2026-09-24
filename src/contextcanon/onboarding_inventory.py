from __future__ import annotations

import csv
import fnmatch
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable, Mapping

from .onboarding import (
    PreparedEvidence,
    REVIEWED_INVENTORY_SELECTION_POLICY,
    _blocked_reason,
    _default_reason,
    _repository_paths,
    _require_git_repository_root,
    _safe_project_file,
    prepare_onboarding_evidence,
)
from .parser import ContextCanonError


INVENTORY_SCHEMA = "contextcanon/onboarding-inventory/v0"
INVENTORY_STATE_SCHEMA = "contextcanon/onboarding-inventory-state/v0"
INVENTORY_ACCEPTANCE_SCHEMA = "contextcanon/onboarding-inventory-acceptance/v0"
INVENTORY_SELECTION_POLICY = REVIEWED_INVENTORY_SELECTION_POLICY

INVENTORY_COLUMNS = (
    "path",
    "status",
    "kind",
    "handling",
    "description",
    "note",
    "hint",
    "size",
    "sha256",
    "accepted_sha256",
    "rule",
)
INVENTORY_KINDS = {
    "document",
    "transcription",
    "structured-data",
    "configuration",
    "source-code",
    "raw-record",
    "generated",
    "binary",
    "other",
    "unknown",
}
INVENTORY_HANDLINGS = {"source", "interpret", "lookup", "ignore", "undecided"}
INVENTORY_STATUSES = {"new", "unchanged", "changed", "missing"}

_TEXT_SUFFIXES = {".md", ".mdx", ".rst", ".txt", ".adoc", ".asciidoc"}
_STRUCTURED_SUFFIXES = {".csv", ".tsv"}
_CONFIGURATION_SUFFIXES = {".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".xml"}
_SOURCE_SUFFIXES = {
    ".py", ".java", ".kt", ".kts", ".js", ".jsx", ".ts", ".tsx", ".go", ".rs",
    ".c", ".cc", ".cpp", ".h", ".hpp", ".cs", ".rb", ".php", ".sh", ".bash",
    ".zsh", ".ps1", ".sql", ".swift", ".scala",
}
_OPAQUE_DOCUMENT_SUFFIXES = {".doc", ".docx", ".odt", ".pdf", ".ppt", ".pptx", ".odp", ".xls", ".xlsx", ".ods"}
_BINARY_SUFFIXES = {
    ".7z", ".avi", ".bin", ".bmp", ".doc", ".docx", ".exe", ".gif", ".gz", ".ico",
    ".jar", ".jpeg", ".jpg", ".mov", ".mp3", ".mp4", ".odt", ".ods", ".odp", ".pdf", ".png", ".ppt", ".pptx",
    ".tar", ".tif", ".tiff", ".wav", ".webp", ".xls", ".xlsx", ".zip",
}
_GENERATED_COMPONENTS = {"build", "dist", "generated", "out", "target", ".cache", "coverage"}
_RAW_RECORD_TOKENS = {"chat", "meeting", "minutes", "notes", "prestudy", "transcript", "workshop"}


@dataclass(frozen=True)
class InventoryRule:
    pattern: str
    kind: str
    handling: str

    def to_dict(self) -> dict[str, str]:
        return {"pattern": self.pattern, "kind": self.kind, "handling": self.handling}


@dataclass(frozen=True)
class InventoryRow:
    path: str
    status: str
    kind: str
    handling: str
    description: str
    note: str
    hint: str
    size: int | None
    sha256: str
    accepted_sha256: str
    rule: str

    def to_csv_dict(self) -> dict[str, str]:
        return {
            "path": self.path,
            "status": self.status,
            "kind": self.kind,
            "handling": self.handling,
            "description": self.description,
            "note": self.note,
            "hint": self.hint,
            "size": "" if self.size is None else str(self.size),
            "sha256": self.sha256,
            "accepted_sha256": self.accepted_sha256,
            "rule": self.rule,
        }


@dataclass(frozen=True)
class InventoryRefresh:
    project_root: Path
    csv_path: Path
    directories: tuple[str, ...]
    rules: tuple[InventoryRule, ...]
    rows: tuple[InventoryRow, ...]
    omitted_source_code: int = 0

    @property
    def counts(self) -> dict[str, int]:
        result = {status: 0 for status in sorted(INVENTORY_STATUSES)}
        for row in self.rows:
            result[row.status] = result.get(row.status, 0) + 1
        return result


@dataclass(frozen=True)
class InventorySelection:
    project_root: Path
    csv_path: Path
    directories: tuple[str, ...]
    rows: tuple[InventoryRow, ...]
    evidence_reasons: Mapping[str, str]


def _state_path(project_root: Path) -> Path:
    return project_root / ".context" / "onboarding" / "inventory-state.json"


def _acceptance_path(project_root: Path) -> Path:
    return project_root / ".context" / "onboarding" / "inventory-acceptance.json"


def _sha256(path: Path, *, inventory_path: str | None = None) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
    except OSError as exc:
        label = inventory_path or str(path)
        raise ContextCanonError(
            f"Inventory could not read file while hashing {label!r}: {exc}"
        ) from exc
    return digest.hexdigest()


def _normalize_directory(project_root: Path, value: str) -> str:
    raw = Path(value)
    if raw.is_absolute():
        raise ContextCanonError(f"Inventory directory must be repository-relative: {value}")
    candidate = (project_root / raw).resolve()
    try:
        relative = candidate.relative_to(project_root)
    except ValueError as exc:
        raise ContextCanonError(f"Inventory directory escapes repository: {value}") from exc
    if not candidate.is_dir():
        raise ContextCanonError(f"Inventory directory does not exist or is not a directory: {value}")
    normalized = relative.as_posix()
    return normalized if normalized != "." else "."


def normalize_directories(project_root: Path, directories: Iterable[str]) -> tuple[str, ...]:
    values = tuple(directories)
    if not values:
        return (".",)
    result: list[str] = []
    for value in values:
        normalized = _normalize_directory(project_root, value)
        if normalized not in result:
            result.append(normalized)
    if "." in result:
        return (".",)
    return tuple(result)


def _in_scope(path: str, directories: tuple[str, ...]) -> bool:
    if directories == (".",):
        return True
    return any(path == directory or path.startswith(directory + "/") for directory in directories)


def parse_inventory_rule(value: str) -> InventoryRule:
    if "=" not in value or ":" not in value.rsplit("=", 1)[1]:
        raise ContextCanonError(
            "Inventory rule must look like 'glob=kind:handling', for example '*.csv=structured-data:source'"
        )
    pattern, classification = value.rsplit("=", 1)
    kind, handling = classification.split(":", 1)
    pattern = pattern.strip()
    kind = kind.strip()
    handling = handling.strip()
    if not pattern:
        raise ContextCanonError("Inventory rule glob must not be empty")
    if kind not in INVENTORY_KINDS:
        raise ContextCanonError(f"Unsupported inventory kind {kind!r}")
    if handling not in INVENTORY_HANDLINGS:
        raise ContextCanonError(f"Unsupported inventory handling {handling!r}")
    return InventoryRule(pattern, kind, handling)


def _default_classification(path: str, custom_rules: tuple[InventoryRule, ...]) -> tuple[str, str, str, str]:
    blocked = _blocked_reason(path)
    if blocked:
        return "other", "ignore", f"blocked:{blocked}", ""

    pure = PurePosixPath(path)
    lower_parts = tuple(part.lower() for part in pure.parts)
    lower_name = pure.name.lower()
    suffix = pure.suffix.lower()

    for rule in custom_rules:
        if fnmatch.fnmatchcase(path, rule.pattern):
            return rule.kind, rule.handling, f"custom:{rule.pattern}", ""

    if any(part in _GENERATED_COMPONENTS for part in lower_parts[:-1]):
        return "generated", "ignore", "generated-directory", ""

    stem_tokens = {
        token
        for fragment in lower_name.replace("_", "-").replace(".", "-").split("-")
        for token in [fragment.strip()]
        if token
    }
    if suffix in _TEXT_SUFFIXES and stem_tokens.intersection(_RAW_RECORD_TOKENS):
        return "raw-record", "interpret", "raw-record-name", ""

    if lower_name == ".gitignore":
        return "configuration", "ignore", "gitignore", ""

    reason = _default_reason(path)
    if reason in {"root-document", "documentation", "agent-instruction"}:
        descriptions = {
            "root-document": "Familiar project-level documentation.",
            "documentation": "Project documentation.",
            "agent-instruction": "Agent/harness instruction surface.",
        }
        return "document", "source", reason, descriptions[reason]
    if reason in {"project-manifest", "ci-workflow"}:
        descriptions = {
            "project-manifest": "Project configuration or manifest.",
            "ci-workflow": "Continuous-integration workflow configuration.",
        }
        return "configuration", "source", reason, descriptions[reason]

    if suffix in _TEXT_SUFFIXES:
        return "document", "source", "text-document", ""
    if suffix in _STRUCTURED_SUFFIXES:
        description = ""
        if "glossar" in lower_name or "glossary" in lower_name:
            description = "Structured glossary or terminology data."
        elif "parameter" in lower_name:
            description = "Structured parameter data."
        return "structured-data", "source", "structured-data", description
    if suffix in _CONFIGURATION_SUFFIXES:
        return "configuration", "source", "configuration", ""
    if suffix in _SOURCE_SUFFIXES:
        return "source-code", "ignore", "source-code", ""
    if suffix in _BINARY_SUFFIXES:
        return "binary", "ignore", "binary", ""
    return "unknown", "undecided", "unclassified", ""


def _matches_custom_rule(path: str, rules: tuple[InventoryRule, ...]) -> bool:
    return any(fnmatch.fnmatchcase(path, rule.pattern) for rule in rules)


def _default_source_code_omitted(
    path: str,
    rules: tuple[InventoryRule, ...],
    previous: Mapping[str, str] | None = None,
    accepted: Mapping[str, str] | None = None,
) -> bool:
    """Keep ordinary fast-changing source files out of the default human inventory."""

    if PurePosixPath(path).suffix.lower() not in _SOURCE_SUFFIXES or _matches_custom_rule(path, rules):
        return False
    for known in (previous, accepted):
        if not known:
            continue
        kind = known.get("kind", "")
        handling = known.get("handling", "")
        description = known.get("description", "")
        note = known.get("note", "")
        # Preserve a deliberate human source-code row, but migrate the old default
        # source-code/lookup rows out of the first-adoption CSV.
        if kind and (kind != "source-code" or handling not in {"lookup", "ignore"} or description or note):
            return False
    return True


def _opaque_companions(path: str, live_paths: frozenset[str]) -> tuple[str, ...]:
    pure = PurePosixPath(path)
    suffix = pure.suffix.lower()
    if suffix == ".md":
        return tuple(
            candidate
            for extension in sorted(_OPAQUE_DOCUMENT_SUFFIXES)
            for candidate in [str(pure.with_suffix(extension))]
            if candidate in live_paths
        )
    if suffix in _OPAQUE_DOCUMENT_SUFFIXES:
        markdown = str(pure.with_suffix(".md"))
        return (markdown,) if markdown in live_paths else ()
    return ()


def _load_existing_csv(path: Path) -> dict[str, dict[str, str]]:
    if not path.is_file():
        return {}
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            if reader.fieldnames is None or "path" not in reader.fieldnames:
                raise ContextCanonError(f"Inventory CSV is missing required 'path' column: {path}")
            result: dict[str, dict[str, str]] = {}
            for index, raw in enumerate(reader, start=2):
                item = {key: (value or "").strip() for key, value in raw.items() if key is not None}
                item_path = item.get("path", "")
                if not item_path:
                    raise ContextCanonError(f"Inventory CSV row {index} has no path")
                if item_path in result:
                    raise ContextCanonError(f"Inventory CSV contains duplicate path: {item_path}")
                result[item_path] = item
            return result
    except UnicodeDecodeError as exc:
        raise ContextCanonError(f"Inventory CSV is not valid UTF-8: {path}") from exc


def _load_json(path: Path, expected_schema: str) -> dict[str, object] | None:
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContextCanonError(f"Invalid ContextCanon inventory state: {path}") from exc
    if not isinstance(payload, dict) or payload.get("schema") != expected_schema:
        raise ContextCanonError(f"Unsupported ContextCanon inventory state in {path}")
    return payload


def _load_acceptance(project_root: Path) -> dict[str, dict[str, str]]:
    payload = _load_json(_acceptance_path(project_root), INVENTORY_ACCEPTANCE_SCHEMA)
    if payload is None:
        return {}
    raw_files = payload.get("files", {})
    if not isinstance(raw_files, dict):
        raise ContextCanonError("Inventory acceptance files must be an object")
    result: dict[str, dict[str, str]] = {}
    for path, raw in raw_files.items():
        if isinstance(path, str) and isinstance(raw, dict):
            result[path] = {str(key): str(value) for key, value in raw.items()}
    return result


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _row_from_live(
    project_root: Path,
    path: str,
    *,
    previous: dict[str, str] | None,
    accepted: dict[str, str] | None,
    rules: tuple[InventoryRule, ...],
    live_paths: frozenset[str],
) -> InventoryRow:
    source = _safe_project_file(project_root, path)
    hint = ""
    if source.is_symlink():
        size = None
        digest = ""
        default_kind, default_handling, default_rule, default_description = (
            "other", "ignore", "symlink", ""
        )
        hint = "Symlinks are not onboarding Evidence."
    elif source.is_dir():
        size = None
        digest = ""
        default_kind, default_handling, default_rule, default_description = (
            "other", "ignore", "git-directory-entry", ""
        )
        hint = (
            "Git exposes this directory as one repository entry (for example an embedded repository, submodule, or gitlink). "
            "The parent inventory does not scan its contents; onboard that repository separately if it matters."
        )
    elif not source.is_file():
        size = None
        digest = ""
        default_kind, default_handling, default_rule, default_description = (
            "other", "ignore", "non-regular-path", ""
        )
        hint = "This Git-visible path is not a regular file and cannot become onboarding Evidence."
    else:
        try:
            size = source.stat().st_size
        except OSError as exc:
            raise ContextCanonError(
                f"Inventory could not inspect file metadata for {path!r}: {exc}"
            ) from exc
        digest = _sha256(source, inventory_path=path)
        default_kind, default_handling, default_rule, default_description = _default_classification(path, rules)

    if not default_rule.startswith("custom:"):
        companions = _opaque_companions(path, live_paths)
        suffix = PurePosixPath(path).suffix.lower()
        if suffix == ".md" and companions:
            default_kind = "transcription"
            default_handling = "source"
            default_rule = "markdown-transcription"
            default_description = "Markdown transcription of " + ", ".join(companions) + "."
            hint = "Keep this transcription faithful to the original; semantic interpretation belongs in later review."
        elif suffix in _OPAQUE_DOCUMENT_SUFFIXES:
            default_kind = "binary"
            default_handling = "ignore"
            if companions:
                default_rule = "opaque-document-with-transcription"
                hint = f"Onboarding uses the same-name Markdown transcription: {companions[0]}"
            else:
                default_rule = "opaque-document-needs-transcription"
                markdown = str(PurePosixPath(path).with_suffix(".md"))
                hint = f"If this document matters for onboarding, create a careful Markdown transcription as {markdown} and rerun STEP 02."

    baseline = (accepted or {}).get("sha256") or (previous or {}).get("sha256", "")
    if accepted:
        status = "unchanged" if baseline == digest else "changed"
    elif previous and baseline:
        status = "unchanged" if baseline == digest else "changed"
    else:
        status = "new"

    kind = (previous or {}).get("kind") or (accepted or {}).get("kind") or default_kind
    handling = (previous or {}).get("handling") or (accepted or {}).get("handling") or default_handling
    description = (previous or {}).get("description") or (accepted or {}).get("description") or default_description
    note = (previous or {}).get("note") or (accepted or {}).get("note") or ""
    accepted_sha = (accepted or {}).get("sha256", "")
    rule = default_rule
    return InventoryRow(path, status, kind, handling, description, note, hint, size, digest, accepted_sha, rule)


def _row_missing(path: str, previous: dict[str, str] | None, accepted: dict[str, str]) -> InventoryRow:
    kind = (previous or {}).get("kind") or accepted.get("kind") or "unknown"
    handling = (previous or {}).get("handling") or accepted.get("handling") or "undecided"
    description = (previous or {}).get("description") or accepted.get("description") or ""
    note = (previous or {}).get("note") or accepted.get("note") or ""
    return InventoryRow(
        path=path,
        status="missing",
        kind=kind,
        handling=handling,
        description=description,
        note=note,
        hint="Previously known path is no longer present in the repository scope.",
        size=None,
        sha256="",
        accepted_sha256=accepted.get("sha256", ""),
        rule="missing",
    )


def _write_csv(path: Path, rows: tuple[InventoryRow, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=INVENTORY_COLUMNS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row.to_csv_dict())


def _is_inventory_control_path(project_root: Path, csv_path: Path, path: str) -> bool:
    """Keep the inventory/workspace itself out of the project material it inventories."""

    try:
        csv_relative = csv_path.resolve().relative_to(project_root).as_posix()
    except ValueError:
        return False
    if path == csv_relative:
        return True
    parent = csv_path.resolve().parent
    if parent == project_root:
        return False
    try:
        parent_relative = parent.relative_to(project_root).as_posix()
    except ValueError:
        return False
    marker = '<!-- contextcanon:onboarding-workspace schema="contextcanon/onboarding-workspace/v0" -->'
    readme = parent / "README.md"
    if not readme.is_file():
        return False
    try:
        owned_workspace = marker in readme.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        owned_workspace = False
    return owned_workspace and path.startswith(parent_relative + "/")


def refresh_inventory(
    project: Path,
    csv_path: Path,
    *,
    directories: Iterable[str] = (),
    rule_specs: Iterable[str] = (),
) -> InventoryRefresh:
    project_root = _require_git_repository_root(project)
    normalized_directories = normalize_directories(project_root, directories)
    rules = tuple(parse_inventory_rule(value) for value in rule_specs)
    existing = _load_existing_csv(csv_path)
    accepted = _load_acceptance(project_root)

    all_live_paths = [
        path for path in _repository_paths(project_root)
        if _in_scope(path, normalized_directories)
        and not _is_inventory_control_path(project_root, csv_path, path)
        and _blocked_reason(path) != "framework-or-derived-path"
    ]
    all_live_set = frozenset(all_live_paths)
    live_paths = [
        path for path in all_live_paths
        if not _default_source_code_omitted(path, rules, existing.get(path), accepted.get(path))
    ]
    rows: list[InventoryRow] = []
    live_set = set(live_paths)
    for path in live_paths:
        rows.append(
            _row_from_live(
                project_root,
                path,
                previous=existing.get(path),
                accepted=accepted.get(path),
                rules=rules,
                live_paths=all_live_set,
            )
        )
    for path in sorted(set(accepted).union(existing) - live_set):
        if not _in_scope(path, normalized_directories):
            continue
        if _default_source_code_omitted(path, rules, existing.get(path), accepted.get(path)):
            continue
        baseline = accepted.get(path)
        if baseline is None:
            previous = existing[path]
            baseline = {
                "sha256": previous.get("sha256", ""),
                "kind": previous.get("kind", "unknown"),
                "handling": previous.get("handling", "undecided"),
                "description": previous.get("description", ""),
                "note": previous.get("note", ""),
            }
        rows.append(_row_missing(path, existing.get(path), baseline))

    result = InventoryRefresh(
        project_root=project_root,
        csv_path=csv_path.resolve(),
        directories=normalized_directories,
        rules=rules,
        rows=tuple(sorted(rows, key=lambda item: item.path)),
        omitted_source_code=len(all_live_paths) - len(live_paths),
    )
    _write_csv(result.csv_path, result.rows)
    _write_json(
        _state_path(project_root),
        {
            "schema": INVENTORY_STATE_SCHEMA,
            "csv_path": result.csv_path.relative_to(project_root).as_posix()
            if result.csv_path.is_relative_to(project_root)
            else str(result.csv_path),
            "directories": list(result.directories),
            "rules": [rule.to_dict() for rule in result.rules],
        },
    )
    return result


def _directories_from_state(project_root: Path, csv_path: Path) -> tuple[str, ...] | None:
    payload = _load_json(_state_path(project_root), INVENTORY_STATE_SCHEMA)
    if payload is None:
        return None
    raw_csv = payload.get("csv_path")
    if isinstance(raw_csv, str):
        expected = Path(raw_csv)
        if not expected.is_absolute():
            expected = project_root / expected
        if expected.resolve() != csv_path.resolve():
            return None
    raw_directories = payload.get("directories")
    if not isinstance(raw_directories, list) or not all(isinstance(item, str) for item in raw_directories):
        return None
    return normalize_directories(project_root, raw_directories)


def _row_from_csv(path: str, raw: dict[str, str]) -> InventoryRow:
    kind = raw.get("kind", "").strip() or "unknown"
    handling = raw.get("handling", "").strip() or "undecided"
    status = raw.get("status", "").strip() or "new"
    if status == "present":
        status = "unchanged"
    if kind not in INVENTORY_KINDS:
        raise ContextCanonError(f"Inventory path {path!r} has unsupported kind {kind!r}")
    if handling not in INVENTORY_HANDLINGS:
        raise ContextCanonError(f"Inventory path {path!r} has unsupported handling {handling!r}")
    if status not in INVENTORY_STATUSES:
        raise ContextCanonError(f"Inventory path {path!r} has unsupported status {status!r}")
    size_raw = raw.get("size", "").strip()
    try:
        size = int(size_raw) if size_raw else None
    except ValueError as exc:
        raise ContextCanonError(f"Inventory path {path!r} has invalid size {size_raw!r}") from exc
    return InventoryRow(
        path=path,
        status=status,
        kind=kind,
        handling=handling,
        description=raw.get("description", "").strip(),
        note=raw.get("note", "").strip(),
        hint=raw.get("hint", "").strip(),
        size=size,
        sha256=raw.get("sha256", "").strip(),
        accepted_sha256=raw.get("accepted_sha256", "").strip(),
        rule=raw.get("rule", "").strip(),
    )


def load_inventory_rows(csv_path: Path) -> tuple[InventoryRow, ...]:
    raw = _load_existing_csv(csv_path)
    return tuple(_row_from_csv(path, item) for path, item in sorted(raw.items()))


def validate_inventory_for_prepare(
    project: Path,
    csv_path: Path,
    *,
    directories: Iterable[str] = (),
) -> InventorySelection:
    project_root = _require_git_repository_root(project)
    explicit_directories = tuple(directories)
    if explicit_directories:
        normalized_directories = normalize_directories(project_root, explicit_directories)
    else:
        normalized_directories = _directories_from_state(project_root, csv_path) or (".",)

    rows = load_inventory_rows(csv_path)
    row_by_path = {row.path: row for row in rows}
    live_paths = [
        path for path in _repository_paths(project_root)
        if _in_scope(path, normalized_directories)
        and not _is_inventory_control_path(project_root, csv_path, path)
        and _blocked_reason(path) != "framework-or-derived-path"
    ]
    missing_rows = sorted(
        path for path in set(live_paths) - set(row_by_path)
        if PurePosixPath(path).suffix.lower() not in _SOURCE_SUFFIXES
    )
    if missing_rows:
        preview = ", ".join(missing_rows[:5])
        suffix = "" if len(missing_rows) <= 5 else f" (+{len(missing_rows) - 5} more)"
        raise ContextCanonError(
            "Inventory is stale: repository files are not listed in the CSV: "
            f"{preview}{suffix}. Rerun 'contextcanon onboard inventory' before freezing Evidence."
        )

    errors: list[str] = []
    evidence_reasons: dict[str, str] = {}
    for row in rows:
        if not _in_scope(row.path, normalized_directories):
            continue
        live = _safe_project_file(project_root, row.path)
        if live.is_symlink():
            if row.handling != "ignore":
                errors.append(f"{row.path}: path is a symlink and must use handling=ignore")
            continue
        if not live.exists():
            if row.handling != "ignore":
                errors.append(f"{row.path}: file is missing; set handling=ignore or restore it")
            continue
        if not live.is_file():
            if row.handling != "ignore":
                errors.append(
                    f"{row.path}: path is not a regular file (for example an embedded Git repository/submodule/gitlink directory) "
                    "and must use handling=ignore"
                )
            continue
        blocked = _blocked_reason(row.path)
        if blocked and row.handling != "ignore":
            errors.append(f"{row.path}: blocked ({blocked}) and must use handling=ignore")
            continue
        if row.handling == "undecided":
            errors.append(f"{row.path}: handling is undecided")
            continue
        current_sha = _sha256(live, inventory_path=row.path)
        if row.sha256 and row.sha256 != current_sha:
            errors.append(f"{row.path}: content changed since inventory was generated; rerun inventory")
            continue
        if row.handling in {"source", "interpret"} and not row.description:
            errors.append(f"{row.path}: {row.handling} rows require a short description")
        if row.handling in {"source", "interpret"}:
            evidence_reasons[row.path] = f"inventory-{row.handling}"

    if errors:
        detail = "\n".join(f"- {item}" for item in errors[:20])
        if len(errors) > 20:
            detail += f"\n- ... and {len(errors) - 20} more"
        raise ContextCanonError(f"Inventory review is not ready for Evidence freeze:\n{detail}")

    return InventorySelection(
        project_root=project_root,
        csv_path=csv_path.resolve(),
        directories=normalized_directories,
        rows=rows,
        evidence_reasons=evidence_reasons,
    )


def prepare_from_inventory(
    project: Path,
    csv_path: Path,
    *,
    directories: Iterable[str] = (),
) -> tuple[PreparedEvidence, InventorySelection]:
    selection = validate_inventory_for_prepare(project, csv_path, directories=directories)
    metadata = {
        row.path: {
            "kind": row.kind,
            "handling": row.handling,
            "description": row.description,
            "note": row.note,
        }
        for row in selection.rows
        if row.path in selection.evidence_reasons
    }
    prepared = prepare_onboarding_evidence(
        selection.project_root,
        selected_reasons=selection.evidence_reasons,
        selected_metadata=metadata,
        selection_policy=INVENTORY_SELECTION_POLICY,
    )

    files: dict[str, dict[str, str]] = {}
    for row in selection.rows:
        if not _in_scope(row.path, selection.directories):
            continue
        live = _safe_project_file(selection.project_root, row.path)
        digest = _sha256(live, inventory_path=row.path) if live.is_file() and not live.is_symlink() else ""
        files[row.path] = {
            "sha256": digest,
            "kind": row.kind,
            "handling": row.handling,
            "description": row.description,
            "note": row.note,
        }
    inventory_bytes = selection.csv_path.read_bytes()
    _write_json(
        _acceptance_path(selection.project_root),
        {
            "schema": INVENTORY_ACCEPTANCE_SCHEMA,
            "inventory_sha256": hashlib.sha256(inventory_bytes).hexdigest(),
            "inventory_path": (
                selection.csv_path.relative_to(selection.project_root).as_posix()
                if selection.csv_path.is_relative_to(selection.project_root)
                else str(selection.csv_path)
            ),
            "evidence_digest": prepared.evidence_digest,
            "directories": list(selection.directories),
            "files": files,
        },
    )
    return prepared, selection
