from __future__ import annotations

import base64
import hashlib
import json
import re
from pathlib import Path
from typing import Callable, Iterable

from .compiler import Compiler, discover_nodes
from .onboarding_workspace import (
    CHECKLIST_END,
    CHECKLIST_START,
    CHECKPOINT_END,
    CHECKPOINT_START,
    DEFAULT_WORKSPACE_NAME,
    LEGACY_ARTIFACT_NAMES,
    PLACEMENT_FOLLOWUP_NAME,
    PLACEMENT_INSTRUCTION_NAME,
    PLACEMENT_PREVIEW_NAME,
    PLACEMENT_PROPOSAL_NAME,
    PLACEMENT_REVIEW_NAME,
    PLAN_MARKER,
    STRUCTURE_INSTRUCTION_NAME,
    STRUCTURE_PREVIEW_NAME,
    STRUCTURE_PROPOSAL_NAME,
    STRUCTURE_REVIEW_NAME,
    WORKSPACE_MARKER,
    write_utf8,
)
from .outputs import expected_outputs
from .parser import ContextCanonError, find_repo_root


RESET_JOURNAL_NAME = "onboarding-reset-journal.json"
RESET_JOURNAL_SCHEMA = "contextcanon/onboarding-reset-journal/v1"

_ARTIFACT_STEPS = {
    STRUCTURE_INSTRUCTION_NAME: 2,
    STRUCTURE_PROPOSAL_NAME: 2,
    STRUCTURE_REVIEW_NAME: 3,
    STRUCTURE_PREVIEW_NAME: 4,
    PLACEMENT_INSTRUCTION_NAME: 5,
    PLACEMENT_PROPOSAL_NAME: 5,
    PLACEMENT_REVIEW_NAME: 7,
    PLACEMENT_PREVIEW_NAME: 8,
    PLACEMENT_FOLLOWUP_NAME: 9,
}
_LEGACY_STEPS = {legacy: _ARTIFACT_STEPS[numbered] for legacy, numbered in LEGACY_ARTIFACT_NAMES.items()}

_SKELETON_RE = re.compile(
    r'^# .+ — Local Context Source\n'
    r'<!-- ctx:node id="[^"]+" version="0\.1\.0-draft" -->\n\n'
    r'## Overview\n\n'
    r'(?:This Node skeleton reserves the accepted onboarding landing point before detailed project knowledge is distributed\.|'
    r'This area is intentionally reserved by the project owner; implementation details are not yet decided\.)\n\n'
    r'The later placement pass will add only the Rules, Topics, Sources, or mappings reviewed for this area\.\n?$'
)


def _error(message: str) -> ContextCanonError:
    return ContextCanonError(f"Onboarding reset: {message}")


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _b64(content: bytes | None) -> str | None:
    return None if content is None else base64.b64encode(content).decode("ascii")


def _unb64(content: str | None) -> bytes | None:
    return None if content is None else base64.b64decode(content.encode("ascii"))


def _journal_path(snapshot_root: Path) -> Path:
    return snapshot_root.resolve() / RESET_JOURNAL_NAME


def _load_journal(snapshot_root: Path) -> list[dict[str, object]]:
    path = _journal_path(snapshot_root)
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise _error(f"reset journal is unreadable: {path}") from exc
    if not isinstance(raw, dict) or raw.get("schema") != RESET_JOURNAL_SCHEMA or not isinstance(raw.get("records"), list):
        raise _error(f"unsupported reset journal: {path}")
    return list(raw["records"])


def _write_journal(snapshot_root: Path, records: list[dict[str, object]]) -> None:
    path = _journal_path(snapshot_root)
    if not records:
        path.unlink(missing_ok=True)
        return
    payload = {"schema": RESET_JOURNAL_SCHEMA, "records": records}
    write_utf8(path, json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def _managed_state(project_root: Path) -> dict[str, bytes | None]:
    project = project_root.resolve()
    result: dict[str, bytes | None] = {}
    compiler = Compiler(project)
    for node_root in discover_nodes(project):
        source = node_root / "CONTEXT.src.md"
        result[source.relative_to(project).as_posix()] = source.read_bytes() if source.is_file() else None
        compiled = compiler.compile(node_root)
        for rel in expected_outputs(compiled):
            path = node_root / rel
            project_rel = path.relative_to(project).as_posix()
            result[project_rel] = path.read_bytes() if path.is_file() else None
        source_store = node_root / ".context" / "sources"
        if source_store.is_dir():
            for path in source_store.rglob("*"):
                if path.is_file():
                    result[path.relative_to(project).as_posix()] = path.read_bytes()
    return result


def _changed_record(before: dict[str, bytes | None], after: dict[str, bytes | None]) -> list[dict[str, object]]:
    changes: list[dict[str, object]] = []
    for rel in sorted(set(before) | set(after)):
        old = before.get(rel)
        new = after.get(rel)
        if old == new:
            continue
        changes.append({
            "path": rel,
            "before": _b64(old),
            "after_exists": new is not None,
            "after_sha256": None if new is None else _sha(new),
        })
    return changes


def record_transition(
    snapshot_root: Path,
    project_root: Path,
    *,
    step: int,
    command: list[str],
    before: dict[str, bytes | None],
    after: dict[str, bytes | None],
) -> None:
    changes = _changed_record(before, after)
    if not changes:
        return
    records = _load_journal(snapshot_root)
    records.append({"step": step, "command": command, "changes": changes})
    _write_journal(snapshot_root, records)


def run_journaled(argv: list[str], delegate: Callable[[list[str]], int]) -> int:
    if len(argv) < 3 or argv[0] != "onboard" or argv[1] not in {"structure-materialize", "placement-publish"}:
        return delegate(argv)
    snapshot = Path(argv[2]).resolve()
    project_arg = None
    if "--project" in argv:
        index = argv.index("--project")
        if index + 1 >= len(argv):
            return delegate(argv)
        project_arg = Path(argv[index + 1])
    project = (project_arg or find_repo_root(snapshot)).resolve()
    before = _managed_state(project)
    result = delegate(argv)
    if result != 0:
        return result
    after = _managed_state(project)
    step = 4 if argv[1] == "structure-materialize" else 9
    record_transition(snapshot, project, step=step, command=list(argv), before=before, after=after)
    return result


def _verify_after(project: Path, change: dict[str, object]) -> None:
    path = project / str(change["path"])
    expected_exists = bool(change["after_exists"])
    if not expected_exists:
        if path.exists() or path.is_symlink():
            raise _error(f"refusing reset because a recorded absent path now exists: {change['path']}")
        return
    if not path.is_file():
        raise _error(f"refusing reset because recorded managed file is missing: {change['path']}")
    expected = str(change["after_sha256"])
    if _sha(path.read_bytes()) != expected:
        raise _error(f"refusing reset because managed file changed after ContextCanon recorded it: {change['path']}")


def _restore_change(project: Path, change: dict[str, object]) -> None:
    path = project / str(change["path"])
    before = _unb64(change.get("before"))
    if before is None:
        path.unlink(missing_ok=True)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(before)


def _prune_empty(project: Path, paths: Iterable[Path]) -> None:
    candidates: set[Path] = set()
    for path in paths:
        parent = path.parent
        while parent != project and project in parent.parents:
            candidates.add(parent)
            parent = parent.parent
    for directory in sorted(candidates, key=lambda value: len(value.parts), reverse=True):
        try:
            directory.rmdir()
        except OSError:
            pass


def _restore_journal(snapshot_root: Path, project: Path, from_step: int) -> tuple[list[int], list[str]]:
    records = _load_journal(snapshot_root)
    selected = [record for record in records if int(record.get("step", 999)) >= from_step]
    if not selected:
        return [], []
    restored: list[str] = []
    for record in reversed(selected):
        changes = list(record.get("changes", []))
        for change in changes:
            _verify_after(project, change)
        for change in reversed(changes):
            _restore_change(project, change)
            restored.append(str(change["path"]))
        _prune_empty(project, [project / str(change["path"]) for change in changes])
    remaining = [record for record in records if int(record.get("step", 999)) < from_step]
    _write_journal(snapshot_root, remaining)
    return [int(record["step"]) for record in selected], restored


def _remove_legacy_skeletons(project: Path) -> list[str]:
    removed: list[str] = []
    compiler = Compiler(project)
    candidates = sorted(
        (path for path in project.rglob("CONTEXT.src.md") if path.parent != project),
        key=lambda value: len(value.parts), reverse=True,
    )
    for source in candidates:
        try:
            text = source.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if _SKELETON_RE.fullmatch(text) is None:
            continue
        node_root = source.parent
        try:
            compiled = compiler.compile(node_root)
        except ContextCanonError:
            continue
        outputs = expected_outputs(compiled)
        output_paths: list[Path] = []
        safe = True
        for rel, expected in outputs.items():
            path = node_root / rel
            output_paths.append(path)
            if not path.is_file() or path.read_bytes() != expected:
                safe = False
                break
        if not safe:
            continue
        source.unlink()
        removed.append(source.relative_to(project).as_posix())
        for path in output_paths:
            if path.is_file():
                path.unlink()
                removed.append(path.relative_to(project).as_posix())
        _prune_empty(project, [source, *output_paths])
    return removed


def _workspace_root(snapshot_root: Path, workspace: Path | None) -> Path:
    return workspace.resolve() if workspace is not None else find_repo_root(snapshot_root) / DEFAULT_WORKSPACE_NAME


def _reset_workspace(workspace_root: Path, from_step: int) -> list[str]:
    if not workspace_root.exists():
        return []
    readme = workspace_root / "README.md"
    try:
        owned = WORKSPACE_MARKER in readme.read_text(encoding="utf-8")
    except (FileNotFoundError, UnicodeDecodeError):
        owned = False
    if not owned:
        raise _error(f"refusing to reset unowned workspace: {workspace_root}")
    removed: list[str] = []
    for name, step in {**_ARTIFACT_STEPS, **_LEGACY_STEPS}.items():
        if step < from_step:
            continue
        path = workspace_root / name
        if path.is_file() or path.is_symlink():
            path.unlink()
            removed.append(path.name)
    return sorted(set(removed))


def _rewrite_plan_after_reset(workspace_root: Path, snapshot_root: Path, from_step: int) -> None:
    path = workspace_root / "PLAN.md"
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    if PLAN_MARKER not in text:
        return
    if CHECKLIST_START in text and CHECKLIST_END in text:
        start = text.index(CHECKLIST_START)
        end = text.index(CHECKLIST_END, start) + len(CHECKLIST_END)
        block = text[start:end]
        block = re.sub(
            r"- \[[ x]\] (?P<n>\d+)\.",
            lambda match: f"- [{'x' if int(match.group('n')) < from_step else ' '}] {match.group('n')}.",
            block,
        )
        text = text[:start] + block + text[end:]
    if CHECKPOINT_START in text and CHECKPOINT_END in text:
        start = text.index(CHECKPOINT_START)
        end = text.index(CHECKPOINT_END, start) + len(CHECKPOINT_END)
        snapshot = snapshot_root.resolve()
        try:
            label = snapshot.relative_to(find_repo_root(snapshot)).as_posix()
        except ValueError:
            label = str(snapshot)
        block = (
            CHECKPOINT_START + "\n"
            + f"- Evidence: `{snapshot.name}`\n"
            + f"- Snapshot: `{label}`\n"
            + f"- Stage: **reset before step {from_step}**\n\n"
            + f"**Next:** restart at numbered step {from_step} using the exact command in this PLAN.\n"
            + CHECKPOINT_END
        )
        text = text[:start] + block + text[end:]
    write_utf8(path, text)


def reset_onboarding(
    snapshot_root: Path,
    *,
    from_step: int,
    workspace_root: Path | None = None,
    project_root: Path | None = None,
) -> dict[str, object]:
    if from_step < 2 or from_step > 9:
        raise _error("--from must be a numbered onboarding step from 2 through 9; frozen Evidence is intentionally preserved")
    snapshot = snapshot_root.resolve()
    project = (project_root or find_repo_root(snapshot)).resolve()
    workspace = _workspace_root(snapshot, workspace_root)

    selected_steps, project_files = _restore_journal(snapshot, project, from_step)
    legacy_files: list[str] = []
    if from_step <= 4 and 4 not in selected_steps:
        legacy_files = _remove_legacy_skeletons(project)
    workspace_files = _reset_workspace(workspace, from_step)

    if 9 in selected_steps:
        (snapshot / "placement-acceptance.json").unlink(missing_ok=True)

    _rewrite_plan_after_reset(workspace, snapshot, from_step)
    return {
        "from_step": from_step,
        "journal_records_reversed": len(selected_steps),
        "project_files_restored_or_removed": sorted(set(project_files + legacy_files)),
        "workspace_files_removed": workspace_files,
        "evidence_preserved": True,
    }


def add_reset_parser(onboard_sub) -> None:
    command = onboard_sub.add_parser(
        "reset",
        help="reset ContextCanon onboarding artifacts/project mutations from one numbered step onward",
    )
    command.add_argument("snapshot", help="root of the prepared content-addressed evidence snapshot")
    command.add_argument("--from", dest="from_step", type=int, required=True, metavar="STEP")
    command.add_argument("--workspace", metavar="PATH")
    command.add_argument("--project", metavar="PATH")


def handle_reset_args(args) -> dict[str, object]:
    return reset_onboarding(
        Path(args.snapshot),
        from_step=args.from_step,
        workspace_root=Path(args.workspace) if args.workspace else None,
        project_root=Path(args.project) if args.project else None,
    )
