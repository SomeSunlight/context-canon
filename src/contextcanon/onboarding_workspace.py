from __future__ import annotations

import os
import re
import shlex
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
COMMANDS_START = "<!-- contextcanon-onboarding-commands:start -->"
COMMANDS_END = "<!-- contextcanon-onboarding-commands:end -->"

README_NAME = "README.md"
PLAN_NAME = "PLAN.md"
STRUCTURE_INSTRUCTION_NAME = "STEP-02a-structure-instruction.md"
STRUCTURE_PROPOSAL_NAME = "STEP-02b-structure-proposal.json"
STRUCTURE_REVIEW_NAME = "STEP-03-structure.md"
STRUCTURE_PREVIEW_NAME = "STEP-04-structure-preview.md"
PLACEMENT_INSTRUCTION_NAME = "STEP-05a-placement-instruction.md"
PLACEMENT_PROPOSAL_NAME = "STEP-05b-placement-proposal.json"
PLACEMENT_REVIEW_NAME = "STEP-07-placement.md"
PLACEMENT_PREVIEW_NAME = "STEP-08-placement-preview.md"
PLACEMENT_FOLLOWUP_NAME = "STEP-09-placement-followup.md"

LEGACY_ARTIFACT_NAMES = {
    "structure-instruction.md": STRUCTURE_INSTRUCTION_NAME,
    "structure-proposal.json": STRUCTURE_PROPOSAL_NAME,
    "structure.md": STRUCTURE_REVIEW_NAME,
    "structure-preview.md": STRUCTURE_PREVIEW_NAME,
    "placement-instruction.md": PLACEMENT_INSTRUCTION_NAME,
    "placement-proposal.json": PLACEMENT_PROPOSAL_NAME,
    "placement.md": PLACEMENT_REVIEW_NAME,
    "placement-preview.md": PLACEMENT_PREVIEW_NAME,
    "placement-followup.md": PLACEMENT_FOLLOWUP_NAME,
}


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

This directory is the **visible human working area** for one structure-first ContextCanon onboarding. This README is the stable orientation page; the PLAN is the executable operator surface.

Start with [`{PLAN_NAME}`]({PLAN_NAME}). It is deliberately written as an operator runbook: the numbered flow, exact copy/paste commands for this Evidence snapshot, current validated checkpoint, and reset commands all live there. You should not need chat history or ContextCanon source-code archaeology to remember how to continue.

## Mental model

ContextCanon separates three jobs:

- `.context/onboarding/<evidence-digest>/` keeps immutable machine-owned frozen Evidence and acceptance/provenance state;
- this directory keeps human/LLM review artifacts in workflow order;
- the actual Context Nodes remain in their accepted repository locations and may use directories that did not exist before onboarding.

The repository's old directory tree is evidence about the project, not a taxonomy ContextCanon must preserve. Structure review designs the shelves first; placement review then decides where the existing meaning belongs.

## Human-facing artifacts — sorted in workflow order

- `{PLAN_NAME}` — generated operator runbook and current validated checkpoint.
- `{STRUCTURE_INSTRUCTION_NAME}` — generated instruction for the coarse-structure reasoning pass.
- `{STRUCTURE_PROPOSAL_NAME}` — LLM JSON for coarse structure discovery.
- `{STRUCTURE_REVIEW_NAME}` — human-editable accepted shelf map and fixed-Markdown decision.
- `{STRUCTURE_PREVIEW_NAME}` — deterministic preview before missing Node skeletons/directories are created.
- `{PLACEMENT_INSTRUCTION_NAME}` — generated instruction for the placement reasoning pass.
- `{PLACEMENT_PROPOSAL_NAME}` — LLM JSON describing where existing meaning belongs.
- Step 06 is validation-only and therefore intentionally has no separate artifact.
- `{PLACEMENT_REVIEW_NAME}` — human-owned placement decisions.
- `{PLACEMENT_PREVIEW_NAME}` — exact deterministic publication preview.
- `{PLACEMENT_FOLLOWUP_NAME}` — durable follow-up after placement publication.

None of these working files become canonical Context merely because they exist. Explicit publication changes reviewed Context Node authoring.

## Reset for testing

`contextcanon onboard reset <snapshot> --from N` removes workspace artifacts from step N onward and reverses recorded ContextCanon project mutations from those steps. Frozen Evidence is deliberately preserved.

For newly journaled runs, reset restores exact pre-command bytes and refuses to overwrite a managed file that changed afterward. For pre-journal structure tests, ContextCanon can also remove unmistakable untouched onboarding skeleton Nodes conservatively.

## Why frozen Evidence exists

Freezing does not lock the live Git repository. ContextCanon copies selected review material into a content-addressed snapshot so the LLM, human review, preview and publication can all refer to the **same exact project bytes**. Prepare a new snapshot only when you intentionally want a new evidence basis.

## Ownership

ContextCanon recognizes this workspace by the marker directly below the H1. Files such as this README and `{PLAN_NAME}` are framework-owned operating surfaces; `{STRUCTURE_REVIEW_NAME}` and `{PLACEMENT_REVIEW_NAME}` are the human-editable review gates.

If a directory with the same name already exists without the marker, ContextCanon refuses to take it over. Use `--workspace <path>` to choose another directory instead.
"""


def _workspace_plan() -> str:
    return f"""# ContextCanon onboarding plan
{PLAN_MARKER}

This is the **operator console** for the current onboarding. Read the numbered steps for meaning; copy commands from **Exact commands for this run** rather than reconstructing IDs/options from memory.

> **Exact commands:** the checklist is the overview; the copy/paste commands are in **Exact commands for this run** below.

## Checklist

{CHECKLIST_START}
- [ ] 1. Freeze Evidence — create or deliberately reuse one exact Evidence snapshot.
- [ ] 2. Structure proposal — generate `{STRUCTURE_INSTRUCTION_NAME}`, run LLM handoff 1, save `{STRUCTURE_PROPOSAL_NAME}`, validate it.
- [ ] 3. Structure review — create/edit `{STRUCTURE_REVIEW_NAME}` and validate the human shelf map.
- [ ] 4. Materialize shelves — review `{STRUCTURE_PREVIEW_NAME}`, then create only missing accepted Node skeletons.
- [ ] 5. Placement proposal — generate `{PLACEMENT_INSTRUCTION_NAME}`, run LLM handoff 2, save `{PLACEMENT_PROPOSAL_NAME}`.
- [ ] 6. Placement validate — validate the LLM proposal against the frozen Evidence, accepted structure, and exact Source catalog.
- [ ] 7. Placement review — create/edit `{PLACEMENT_REVIEW_NAME}` and rerun the review command until every human decision validates.
- [ ] 8. Publication preview — review exact `{PLACEMENT_PREVIEW_NAME}` changes.
- [ ] 9. Publish placement — publish reviewed canonical Context and inspect `{PLACEMENT_FOLLOWUP_NAME}`.
{CHECKLIST_END}

## Exact commands for this run

{COMMANDS_START}
The exact snapshot-bound commands appear here after ContextCanon opens this workspace.
{COMMANDS_END}

## Current checkpoint

{CHECKPOINT_START}
No ContextCanon structure-first command has recorded a checkpoint in this workspace yet.
{CHECKPOINT_END}

The checkpoint is the **last state ContextCanon validated**, not a file watcher. If you edit `{STRUCTURE_REVIEW_NAME}` or `{PLACEMENT_REVIEW_NAME}`, rerun that step's validation/review command before advancing.

## Human gates

- **LLM handoff 1:** `{STRUCTURE_INSTRUCTION_NAME}` + only the frozen `evidence/` tree → `{STRUCTURE_PROPOSAL_NAME}`.
- **Human gate 1:** review/edit `{STRUCTURE_REVIEW_NAME}`.
- **LLM handoff 2:** `{PLACEMENT_INSTRUCTION_NAME}` + only the same frozen `evidence/` tree → `{PLACEMENT_PROPOSAL_NAME}`.
- **Human gate 2:** review/edit `{PLACEMENT_REVIEW_NAME}`.

`--owner-source` is a one-time choice only when a new placement review is first created. The exact Source catalog paths are persisted in this PLAN so subsequent commands can be copied rather than reconstructed.
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


def _quote_cli(value: str) -> str:
    if os.name == "nt":
        return "'" + value.replace("'", "''") + "'"
    return shlex.quote(value)


def _workspace_option(workspace: OnboardingWorkspace, snapshot_root: Path) -> list[str]:
    try:
        default = (find_repo_root(snapshot_root) / DEFAULT_WORKSPACE_NAME).resolve()
    except ContextCanonError:
        return ["--workspace", str(workspace.root)]
    return [] if workspace.root.resolve() == default else ["--workspace", str(workspace.root)]


def _render_command(parts: list[str]) -> str:
    rendered: list[str] = []
    for index, part in enumerate(parts):
        value = str(part)
        if index < 3 or value.startswith("--"):
            rendered.append(value)
        else:
            rendered.append(_quote_cli(value))
    return " ".join(rendered)


def _catalog_args(inputs: tuple[str, ...]) -> list[str]:
    result: list[str] = []
    for item in inputs:
        result.extend(["--catalog-package", item])
    return result


def _owner_args(inputs: tuple[str, ...]) -> list[str]:
    result: list[str] = []
    for item in inputs:
        result.extend(["--owner-source", item])
    return result


def _exact_commands(
    workspace: OnboardingWorkspace,
    snapshot_root: Path,
    catalog_inputs: tuple[str, ...],
    owner_source_specs: tuple[str, ...],
) -> str:
    snapshot = _snapshot_label(snapshot_root)
    workspace_args = _workspace_option(workspace, snapshot_root)
    catalog = _catalog_args(catalog_inputs)
    owner = _owner_args(owner_source_specs)
    snapshot_literal = _quote_cli(snapshot)
    if os.name == "nt":
        snapshot_assignment = f"$SNAPSHOT = {snapshot_literal}"
        snapshot_token = "$SNAPSHOT"
        shell = "powershell"
    else:
        snapshot_assignment = f"SNAPSHOT={snapshot_literal}"
        snapshot_token = '"$SNAPSHOT"'
        shell = "sh"

    def render(parts: list[str]) -> str:
        command = _render_command(parts)
        return command.replace(snapshot_literal, snapshot_token, 1)

    def cmd(name: str, *, cat: bool = False, own: bool = False) -> str:
        parts = ["contextcanon", "onboard", name, snapshot, *workspace_args]
        if cat:
            parts.extend(catalog)
        if own:
            parts.extend(owner)
        return render(parts)

    lines = [
        COMMANDS_START,
        "These are the commands for **this exact snapshot**. Copy them; do not rebuild them from IDs or terminal history.",
        "",
        "Set this run variable once in your terminal; every snapshot-bound command below reuses it:",
        "",
        f"```{shell}",
        snapshot_assignment,
        "```",
        "",
        "### 1. Freeze Evidence",
        "",
        "Only run this when you intentionally need a new Evidence basis. Reusing the current frozen snapshot is valid.",
        "",
        "```text",
        "contextcanon onboard prepare .",
        "```",
        "",
        "### 2. Structure proposal",
        "",
        "Generate the instruction:",
        "",
        "```text",
        cmd("structure-instruction", cat=True),
        "```",
        "",
        f"Give `{STRUCTURE_INSTRUCTION_NAME}` plus only the frozen `evidence/` tree to the reasoning LLM. Save its JSON exactly as `{STRUCTURE_PROPOSAL_NAME}`. Then validate:",
        "",
        "```text",
        cmd("structure-validate"),
        "```",
        "",
        "### 3. Structure review",
        "",
        "```text",
        cmd("structure-review"),
        "```",
        "",
        f"Edit `{STRUCTURE_REVIEW_NAME}` as needed, then run the same command again to validate the edited human gate.",
        "",
        "### 4. Materialize shelves",
        "",
        "```text",
        cmd("structure-preview"),
        cmd("structure-materialize"),
        "```",
        "",
        "### 5. Placement proposal",
        "",
        "```text",
        cmd("placement-instruction", cat=True),
        "```",
        "",
        f"Give `{PLACEMENT_INSTRUCTION_NAME}` plus only the same frozen `evidence/` tree to the reasoning LLM. Save its JSON exactly as `{PLACEMENT_PROPOSAL_NAME}`.",
        "",
        "### 6. Placement validate",
        "",
        "```text",
        cmd("placement-validate", cat=True),
        "```",
        "",
        "### 7. Placement review",
        "",
        "Create/load the review:",
        "",
        "```text",
        cmd("placement-review", cat=True, own=bool(owner)),
        "```",
        "",
    ]
    if owner:
        lines.extend(
            [
                "`--owner-source` above is only for first creation. After editing the existing review, validate it with this command **without** `--owner-source`:",
                "",
                "```text",
                cmd("placement-review", cat=True),
                "```",
                "",
            ]
        )
    else:
        lines.extend(
            [
                f"Edit `{PLACEMENT_REVIEW_NAME}`. Run the same command again after every edit until all decisions validate. If you deliberately choose an owner Source, add `--owner-source TARGET_NODE_KEY=SOURCE_NODE_ID` only when creating the review.",
                "",
            ]
        )
    lines.extend(
        [
            "### 8. Publication preview",
            "",
            "```text",
            cmd("placement-preview", cat=True),
            "```",
            "",
            "### 9. Publish placement",
            "",
            "```text",
            cmd("placement-publish", cat=True),
            "```",
            "",
            "## Reset commands for testing",
            "",
            "Frozen Evidence is preserved. Pick the step you want to restart from and copy the corresponding line:",
            "",
            "```text",
        ]
    )
    for step in range(2, 10):
        parts = ["contextcanon", "onboard", "reset", snapshot, "--from", str(step), *workspace_args]
        lines.append(render(parts))
    lines.extend(["```", COMMANDS_END])
    return "\n".join(lines)


def _completed_steps(stage: str, placement_review_complete: bool | None) -> set[int]:
    completed = {1}
    after_structure_proposal = {
        "structure proposal validated", "human structure validated", "structure previewed", "structure materialized",
        "placement instruction ready", "placement proposal validated", "human placement review",
        "placement publication previewed", "placement published",
    }
    after_structure_review = after_structure_proposal - {"structure proposal validated"}
    after_materialize = {
        "structure materialized", "placement instruction ready", "placement proposal validated",
        "human placement review", "placement publication previewed", "placement published",
    }
    after_placement_validate = {
        "placement proposal validated", "human placement review", "placement publication previewed", "placement published",
    }
    if stage in after_structure_proposal:
        completed.add(2)
    if stage in after_structure_review:
        completed.add(3)
    if stage in after_materialize:
        completed.add(4)
    if stage in after_placement_validate:
        completed.update({5, 6})
    if stage in {"placement publication previewed", "placement published"} or (
        stage == "human placement review" and placement_review_complete is True
    ):
        completed.add(7)
    if stage in {"placement publication previewed", "placement published"}:
        completed.add(8)
    if stage == "placement published":
        completed.add(9)
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


def _replace_commands(
    text: str,
    workspace: OnboardingWorkspace,
    snapshot_root: Path,
    catalog_inputs: tuple[str, ...],
    owner_source_specs: tuple[str, ...],
) -> str:
    block = _exact_commands(workspace, snapshot_root, catalog_inputs, owner_source_specs)
    if COMMANDS_START not in text or COMMANDS_END not in text:
        anchor = "## Current checkpoint"
        if anchor not in text:
            raise ContextCanonError(f"Malformed onboarding plan; missing {anchor}")
        return text.replace(anchor, block + "\n\n" + anchor, 1)
    start = text.index(COMMANDS_START)
    end = text.index(COMMANDS_END, start) + len(COMMANDS_END)
    return text[:start] + block + text[end:]


def _remembered_values(text: str, heading: str) -> tuple[str, ...]:
    lines = text.splitlines()
    try:
        start = lines.index(heading)
    except ValueError:
        return ()
    result: list[str] = []
    for line in lines[start + 1 :]:
        if line.startswith("- ") and not line.startswith("  - "):
            break
        if not line.strip():
            if result:
                break
            continue
        match = re.match(r"^\s+- `(.+)`$", line)
        if match:
            result.append(match.group(1))
    return tuple(result)


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
    """Rewrite framework-owned checklist, exact commands, and checkpoint surfaces."""

    try:
        text = workspace.plan_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        write_utf8(workspace.plan_path, _workspace_plan())
        text = workspace.plan_path.read_text(encoding="utf-8")
    if PLAN_MARKER not in text:
        raise ContextCanonError(f"Refusing to update unowned onboarding plan: {workspace.plan_path}")

    remembered_catalog = _remembered_values(
        text, "- Reuse these exact `--catalog-package` inputs for copy/paste commands:"
    )
    remembered_owner = _remembered_values(
        text, "- Owner-selected Source choices already recorded in the human review (do not repeat on preview/publish):"
    )
    catalog_inputs = source_catalog_inputs or remembered_catalog
    owner_specs = owner_source_specs or remembered_owner

    text = _rewrite_checklist(text, _completed_steps(stage, placement_review_complete), workspace.plan_path)
    text = _replace_commands(text, workspace, snapshot_root, catalog_inputs, owner_specs)

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
    if catalog_inputs:
        lines.append("- Reuse these exact `--catalog-package` inputs for copy/paste commands:")
        lines.extend(f"  - `{item}`" for item in catalog_inputs)
    if owner_specs:
        lines.append("- Owner-selected Source choices already recorded in the human review (do not repeat on preview/publish):")
        lines.extend(f"  - `{item}`" for item in owner_specs)
    if acceptance_digest is not None:
        lines.append(f"- Placement acceptance: `{acceptance_digest}`")
    lines.extend([
        "", "**Next:**", "", next_action, "",
        "The exact runnable command is also shown in **Exact commands for this run** above.",
    ])
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


def _migrate_legacy_artifacts(workspace: OnboardingWorkspace) -> None:
    for legacy_name, numbered_name in LEGACY_ARTIFACT_NAMES.items():
        legacy = workspace.root / legacy_name
        numbered = workspace.root / numbered_name
        if not legacy.exists():
            continue
        if numbered.exists():
            if legacy.read_bytes() == numbered.read_bytes():
                legacy.unlink()
                continue
            raise ContextCanonError(
                f"Onboarding workspace contains both legacy and numbered artifacts with different bytes: "
                f"{legacy.name}, {numbered.name}"
            )
        legacy.rename(numbered)


def _checkpoint_block(text: str, path: Path) -> str | None:
    starts = text.count(CHECKPOINT_START)
    ends = text.count(CHECKPOINT_END)
    if starts == 0 and ends == 0:
        return None
    if starts != 1 or ends != 1:
        raise ContextCanonError(f"Malformed onboarding checkpoint markers in {path}")
    start = text.index(CHECKPOINT_START)
    end = text.index(CHECKPOINT_END, start) + len(CHECKPOINT_END)
    return text[start:end]


def _checkpoint_stage(block: str | None) -> str | None:
    if block is None:
        return None
    match = re.search(r"^- Stage: \*\*(.+?)\*\*$", block, re.MULTILINE)
    return match.group(1) if match else None


def _checkpoint_review_complete(block: str | None) -> bool | None:
    if block is None:
        return None
    line = next((line for line in block.splitlines() if line.startswith("- Placement review:")), None)
    if line is None:
        return None
    return line.rstrip().endswith("— complete")


def _remember_first(text: str, headings: tuple[str, ...]) -> tuple[str, ...]:
    for heading in headings:
        values = _remembered_values(text, heading)
        if values:
            return values
    return ()


def _refresh_framework_owned_surfaces(workspace: OnboardingWorkspace, snapshot_root: Path) -> None:
    _migrate_legacy_artifacts(workspace)
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

    checkpoint = _checkpoint_block(plan, workspace.plan_path)
    stage = _checkpoint_stage(checkpoint)
    review_complete = _checkpoint_review_complete(checkpoint)
    catalog_inputs = _remember_first(
        plan,
        (
            "- Reuse these exact `--catalog-package` inputs for copy/paste commands:",
            "- Reuse these exact `--catalog-package` inputs on the next placement command:",
        ),
    )
    owner_specs = _remember_first(
        plan,
        (
            "- Owner-selected Source choices already recorded in the human review (do not repeat on preview/publish):",
            "- Owner-selected Source choices already recorded in `placement.md` (do not repeat on preview/publish):",
        ),
    )

    refreshed = _workspace_plan()
    if checkpoint is not None:
        default_checkpoint = _checkpoint_block(refreshed, workspace.plan_path)
        assert default_checkpoint is not None
        refreshed = refreshed.replace(default_checkpoint, checkpoint, 1)
    if stage is not None:
        refreshed = _rewrite_checklist(
            refreshed,
            _completed_steps(stage, review_complete),
            workspace.plan_path,
        )
    refreshed = _replace_commands(refreshed, workspace, snapshot_root, catalog_inputs, owner_specs)
    write_utf8(workspace.plan_path, refreshed)


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
        _refresh_framework_owned_surfaces(workspace, snapshot_root)
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
