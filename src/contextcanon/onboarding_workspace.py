from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .parser import ContextCanonError, find_repo_root


WORKSPACE_SCHEMA = "contextcanon/onboarding-workspace/v0"
DEFAULT_WORKSPACE_NAME = "contextcanon-onboarding"
WORKSPACE_MARKER = f'<!-- contextcanon:onboarding-workspace schema="{WORKSPACE_SCHEMA}" -->'
PLAN_MARKER = f'<!-- contextcanon:onboarding-plan schema="{WORKSPACE_SCHEMA}" -->'
CHECKPOINT_START = "<!-- contextcanon-onboarding-checkpoint:start -->"
CHECKPOINT_END = "<!-- contextcanon-onboarding-checkpoint:end -->"
CHECKLIST_START = "<!-- contextcanon-onboarding-checklist:start -->"
CHECKLIST_END = "<!-- contextcanon-onboarding-checklist:end -->"

README_NAME = "README.md"
PLAN_NAME = "PLAN.md"
STRUCTURE_INSTRUCTION_NAME = "structure-instruction.md"
STRUCTURE_PROPOSAL_NAME = "structure-proposal.json"
STRUCTURE_REVIEW_NAME = "structure.md"
STRUCTURE_PREVIEW_NAME = "structure-preview.md"
PLACEMENT_INSTRUCTION_NAME = "placement-instruction.md"
PLACEMENT_PROPOSAL_NAME = "placement-proposal.json"
PLACEMENT_REVIEW_NAME = "placement.md"
PLACEMENT_PREVIEW_NAME = "placement-preview.md"
PLACEMENT_FOLLOWUP_NAME = "placement-followup.md"


@dataclass(frozen=True)
class OnboardingWorkspace:
    root: Path

    @property
    def readme_path(self) -> Path:
        return self.root / README_NAME

    @property
    def plan_path(self) -> Path:
        return self.root / PLAN_NAME

    @property
    def structure_instruction_path(self) -> Path:
        return self.root / STRUCTURE_INSTRUCTION_NAME

    @property
    def structure_proposal_path(self) -> Path:
        return self.root / STRUCTURE_PROPOSAL_NAME

    @property
    def structure_path(self) -> Path:
        return self.root / STRUCTURE_REVIEW_NAME

    @property
    def structure_preview_path(self) -> Path:
        return self.root / STRUCTURE_PREVIEW_NAME

    @property
    def placement_instruction_path(self) -> Path:
        return self.root / PLACEMENT_INSTRUCTION_NAME

    @property
    def placement_proposal_path(self) -> Path:
        return self.root / PLACEMENT_PROPOSAL_NAME

    @property
    def placement_path(self) -> Path:
        return self.root / PLACEMENT_REVIEW_NAME

    @property
    def placement_preview_path(self) -> Path:
        return self.root / PLACEMENT_PREVIEW_NAME

    @property
    def placement_followup_path(self) -> Path:
        return self.root / PLACEMENT_FOLLOWUP_NAME


def _workspace_readme() -> str:
    return f"""# ContextCanon onboarding workspace
{WORKSPACE_MARKER}

This directory is the **visible human working area** for one structure-first ContextCanon onboarding.

Start with [`{PLAN_NAME}`]({PLAN_NAME}) when continuing the onboarding. It is the operational checklist: it shows what ContextCanon has already validated, what comes next, and the exact invocation details that must survive a pause. This README is deliberately only the stable orientation page.

## Mental model

ContextCanon separates three jobs:

- `.context/onboarding/<evidence-digest>/` keeps immutable machine-owned frozen Evidence and acceptance/provenance state;
- this directory keeps the human/LLM review artifacts;
- the actual Context Nodes remain in their accepted repository locations and may use directories that did not exist before onboarding.

The repository's old directory tree is evidence about the project, not a taxonomy ContextCanon must preserve. Structure review designs the shelves first; placement review then decides where the existing meaning belongs.

## Human-facing artifacts

- `{PLAN_NAME}` — generated operational checklist and current validated checkpoint.
- `{STRUCTURE_INSTRUCTION_NAME}` — generated instruction for the coarse-structure reasoning pass.
- `{STRUCTURE_PROPOSAL_NAME}` — LLM JSON for coarse structure discovery.
- `{STRUCTURE_REVIEW_NAME}` — human-editable accepted shelf map and fixed-Markdown decision.
- `{STRUCTURE_PREVIEW_NAME}` — deterministic preview before missing Node skeletons/directories are created.
- `{PLACEMENT_INSTRUCTION_NAME}` — generated instruction for the placement reasoning pass.
- `{PLACEMENT_PROPOSAL_NAME}` — LLM JSON describing where existing meaning belongs.
- `{PLACEMENT_REVIEW_NAME}` — human-owned placement decisions.
- `{PLACEMENT_PREVIEW_NAME}` — exact deterministic publication preview.
- `{PLACEMENT_FOLLOWUP_NAME}` — durable follow-up after placement publication.

None of these working files become canonical Context merely because they exist. Explicit publication changes reviewed Context Node authoring.

## Why frozen Evidence exists

Freezing does not lock the live Git repository. ContextCanon copies selected review material into a content-addressed snapshot so the LLM, human review, preview and publication can all refer to the **same exact project bytes**. Prepare a new snapshot only when you intentionally want a new evidence basis.

## Ownership

ContextCanon recognizes this workspace by the marker directly below the H1. Files such as this README and `{PLAN_NAME}` are framework-owned operating surfaces; `structure.md` and `placement.md` are the human-editable review gates.

If a directory with the same name already exists without the marker, ContextCanon refuses to take it over. Use `--workspace <path>` to choose another directory instead.
"""


def _workspace_plan() -> str:
    return f"""# ContextCanon onboarding plan
{PLAN_MARKER}

This is the **operational checklist** for the current onboarding. ContextCanon updates the framework-owned checklist/checkpoint after it validates a stage. Human review still happens in `{STRUCTURE_REVIEW_NAME}` and `{PLACEMENT_REVIEW_NAME}`.

## Checklist

{CHECKLIST_START}
- [ ] 1. Freeze Evidence — `contextcanon onboard prepare .`
- [ ] 2. Structure proposal — generate `{STRUCTURE_INSTRUCTION_NAME}`, run LLM handoff 1, validate `{STRUCTURE_PROPOSAL_NAME}`.
- [ ] 3. Structure review — edit and validate `{STRUCTURE_REVIEW_NAME}`.
- [ ] 4. Materialize shelves — review `{STRUCTURE_PREVIEW_NAME}` and create any missing accepted Node directories/skeletons.
- [ ] 5. Placement proposal — generate `{PLACEMENT_INSTRUCTION_NAME}`, run LLM handoff 2, validate `{PLACEMENT_PROPOSAL_NAME}`.
- [ ] 6. Placement review — edit `{PLACEMENT_REVIEW_NAME}` until every decision is resolved.
- [ ] 7. Publication preview — review exact `{PLACEMENT_PREVIEW_NAME}` changes.
- [ ] 8. Publish placement — publish reviewed canonical Context and inspect `{PLACEMENT_FOLLOWUP_NAME}`.
{CHECKLIST_END}

## Current checkpoint

{CHECKPOINT_START}
No ContextCanon structure-first command has recorded a checkpoint in this workspace yet.
{CHECKPOINT_END}

The checkpoint is the **last state ContextCanon validated**, not a file watcher. If you edit `{STRUCTURE_REVIEW_NAME}` or `{PLACEMENT_REVIEW_NAME}`, the edit becomes validated human input only after the next ContextCanon command loads it successfully.

## Review gates

- **LLM handoff 1:** `{STRUCTURE_INSTRUCTION_NAME}` + only the frozen `evidence/` tree → `{STRUCTURE_PROPOSAL_NAME}`.
- **Human gate 1:** review/edit `{STRUCTURE_REVIEW_NAME}`.
- **LLM handoff 2:** `{PLACEMENT_INSTRUCTION_NAME}` + only the same frozen `evidence/` tree → `{PLACEMENT_PROPOSAL_NAME}`.
- **Human gate 2:** review/edit `{PLACEMENT_REVIEW_NAME}`.

`--owner-source` is a one-time choice when a new `{PLACEMENT_REVIEW_NAME}` is created. Once recorded there, it is not repeated on preview/publish. Exact `--catalog-package` inputs that must be reused are retained in the checkpoint below.
"""


def write_utf8(path: Path, text: str) -> None:
    """Atomically write UTF-8 without depending on shell redirection/codepages."""

    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def _snapshot_label(snapshot_root: Path) -> str:
    snapshot = snapshot_root.resolve()
    project = find_repo_root(snapshot)
    try:
        return snapshot.relative_to(project).as_posix()
    except ValueError:
        return str(snapshot)


def _completed_steps(stage: str, placement_review_complete: bool | None) -> set[int]:
    completed = {1}
    if stage in {
        "structure proposal validated",
        "human structure validated",
        "structure previewed",
        "structure materialized",
        "placement instruction ready",
        "placement proposal validated",
        "human placement review",
        "placement publication previewed",
        "placement published",
    }:
        completed.add(2)
    if stage in {
        "human structure validated",
        "structure previewed",
        "structure materialized",
        "placement instruction ready",
        "placement proposal validated",
        "human placement review",
        "placement publication previewed",
        "placement published",
    }:
        completed.add(3)
    if stage in {
        "structure materialized",
        "placement instruction ready",
        "placement proposal validated",
        "human placement review",
        "placement publication previewed",
        "placement published",
    }:
        completed.add(4)
    if stage in {
        "placement proposal validated",
        "human placement review",
        "placement publication previewed",
        "placement published",
    }:
        completed.add(5)
    if stage in {"placement publication previewed", "placement published"} or (
        stage == "human placement review" and placement_review_complete is True
    ):
        completed.add(6)
    if stage == "placement published":
        completed.update({7, 8})
    elif stage == "placement publication previewed":
        completed.add(7)
    return completed


def _rewrite_checklist(text: str, completed: set[int], path: Path) -> str:
    if text.count(CHECKLIST_START) != 1 or text.count(CHECKLIST_END) != 1:
        raise ContextCanonError(f"Malformed onboarding checklist markers in {path}")
    start = text.index(CHECKLIST_START)
    end = text.index(CHECKLIST_END, start) + len(CHECKLIST_END)
    template = _workspace_plan()
    template_start = template.index(CHECKLIST_START)
    template_end = template.index(CHECKLIST_END, template_start) + len(CHECKLIST_END)
    block = template[template_start:template_end]
    for step in completed:
        block = block.replace(f"- [ ] {step}.", f"- [x] {step}.")
    return text[:start] + block + text[end:]


def update_workspace_checkpoint(
    workspace: OnboardingWorkspace,
    snapshot_root: Path,
    *,
    stage: str,
    next_action: str,
    structure_digest: str | None = None,
    placement_proposal_digest: str | None = None,
    placement_review_digest: str | None = None,
    placement_review_complete: bool | None = None,
    acceptance_digest: str | None = None,
    source_catalog: tuple[str, ...] = (),
    source_catalog_inputs: tuple[str, ...] = (),
    owner_source_specs: tuple[str, ...] = (),
) -> None:
    """Rewrite only the framework-owned checklist/checkpoint inside PLAN.md."""

    try:
        text = workspace.plan_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        write_utf8(workspace.plan_path, _workspace_plan())
        text = workspace.plan_path.read_text(encoding="utf-8")
    if PLAN_MARKER not in text:
        raise ContextCanonError(f"Refusing to update unowned onboarding plan: {workspace.plan_path}")

    text = _rewrite_checklist(text, _completed_steps(stage, placement_review_complete), workspace.plan_path)
    lines = [
        f"- Evidence: `{snapshot_root.resolve().name}`",
        f"- Snapshot: `{_snapshot_label(snapshot_root)}`",
        f"- Stage: **{stage}**",
    ]
    if structure_digest is not None:
        lines.append(f"- Accepted structure: `{structure_digest}`")
    if placement_proposal_digest is not None:
        lines.append(f"- Placement proposal: `{placement_proposal_digest}`")
    if placement_review_digest is not None:
        state = "complete" if placement_review_complete else "still has pending decisions"
        lines.append(f"- Placement review: `{placement_review_digest}` — {state}")
    if source_catalog:
        lines.append("- Exact reusable Source catalog:")
        lines.extend(f"  - `{item}`" for item in source_catalog)
    if source_catalog_inputs:
        lines.append("- Reuse these exact `--catalog-package` inputs on the next placement command:")
        lines.extend(f"  - `{item}`" for item in source_catalog_inputs)
    if owner_source_specs:
        lines.append("- Owner-selected Source choices already recorded in `placement.md` (do not repeat on preview/publish):")
        lines.extend(f"  - `{item}`" for item in owner_source_specs)
    if acceptance_digest is not None:
        lines.append(f"- Placement acceptance: `{acceptance_digest}`")
    lines.extend(["", "**Next:**", "", next_action])
    block = CHECKPOINT_START + "\n" + "\n".join(lines) + "\n" + CHECKPOINT_END

    if text.count(CHECKPOINT_START) != 1 or text.count(CHECKPOINT_END) != 1:
        raise ContextCanonError(f"Malformed onboarding checkpoint markers in {workspace.plan_path}")
    start = text.index(CHECKPOINT_START)
    end = text.index(CHECKPOINT_END, start) + len(CHECKPOINT_END)
    text = text[:start] + block + text[end:]
    write_utf8(workspace.plan_path, text)


def _default_workspace_root(snapshot_root: Path) -> Path:
    project_root = find_repo_root(snapshot_root)
    if not (project_root / ".git").exists():
        raise ContextCanonError(
            "Cannot infer the onboarding project root from the Evidence snapshot; "
            "run from/use a snapshot inside its Git repository or pass --workspace explicitly"
        )
    return project_root / DEFAULT_WORKSPACE_NAME


def _refresh_framework_owned_surfaces(workspace: OnboardingWorkspace) -> None:
    write_utf8(workspace.readme_path, _workspace_readme())
    if not workspace.plan_path.exists():
        write_utf8(workspace.plan_path, _workspace_plan())
        return
    try:
        plan = workspace.plan_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ContextCanonError(f"Onboarding workspace PLAN is not valid UTF-8: {workspace.plan_path}") from exc
    if PLAN_MARKER not in plan:
        raise ContextCanonError(f"Refusing to take over existing unowned onboarding plan: {workspace.plan_path}")


def open_onboarding_workspace(
    snapshot_root: Path,
    workspace_root: Path | None = None,
    *,
    create: bool,
) -> OnboardingWorkspace:
    root = workspace_root.resolve() if workspace_root is not None else _default_workspace_root(snapshot_root)
    workspace = OnboardingWorkspace(root)

    if root.exists() or root.is_symlink():
        if root.is_symlink() or not root.is_dir():
            raise ContextCanonError(f"Onboarding workspace path is not a normal directory: {root}")
        try:
            readme = workspace.readme_path.read_text(encoding="utf-8")
        except FileNotFoundError as exc:
            raise ContextCanonError(
                f"Refusing to take over existing directory without ContextCanon onboarding marker: {root}"
            ) from exc
        except UnicodeDecodeError as exc:
            raise ContextCanonError(f"Onboarding workspace README is not valid UTF-8: {workspace.readme_path}") from exc
        if WORKSPACE_MARKER not in readme:
            raise ContextCanonError(
                f"Refusing to take over existing directory without ContextCanon onboarding marker: {root}"
            )
        _refresh_framework_owned_surfaces(workspace)
        return workspace

    if not create:
        raise ContextCanonError(
            f"Missing onboarding workspace: {root}; run 'contextcanon onboard structure-instruction ...' first "
            "or pass explicit proposal/structure paths"
        )

    root.mkdir(parents=True)
    write_utf8(workspace.readme_path, _workspace_readme())
    write_utf8(workspace.plan_path, _workspace_plan())
    return workspace
