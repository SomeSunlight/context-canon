from __future__ import annotations

import json
import os
import re
import shlex
import tempfile
import time
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
RUN_INPUTS_SCHEMA = "contextcanon/onboarding-run-inputs/v0"
RUN_INPUTS_NAME = "run-inputs.json"
GITIGNORE_START = "# >>> ContextCanon onboarding (managed)"
GITIGNORE_END = "# <<< ContextCanon onboarding (managed)"

README_NAME = "README.md"
PLAN_NAME = "PLAN.md"
INVENTORY_NAME = "STEP-02-inventory.csv"
INVENTORY_GUIDE_NAME = "STEP-02-inventory-guide.md"
STRUCTURE_INSTRUCTION_NAME = "STEP-04a-structure-instruction.md"
STRUCTURE_PROPOSAL_NAME = "STEP-04b-structure-proposal.json"
STRUCTURE_REVIEW_NAME = "STEP-05-structure.md"
STRUCTURE_PREVIEW_NAME = "STEP-06-structure-preview.md"
REUSABLE_CONTEXTS_NAME = "STEP-07-reusable-contexts.md"
PLACEMENT_INSTRUCTION_NAME = "STEP-08a-placement-instruction.md"
PLACEMENT_PROPOSAL_NAME = "STEP-08b-placement-proposal.json"
PLACEMENT_REVIEW_NAME = "STEP-10-placement.md"
PLACEMENT_REVIEW_DIR_NAME = "STEP-10-placement"
PLACEMENT_SOURCE_EDIT_DIR_NAME = "STEP-10-source-edits"
PLACEMENT_AUDIT_NAME = "STEP-10a-source-audit.md"
PLACEMENT_PREVIEW_NAME = "STEP-11-placement-preview.md"
PLACEMENT_FOLLOWUP_NAME = "STEP-12-placement-followup.md"

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
    "STEP-02a-structure-instruction.md": STRUCTURE_INSTRUCTION_NAME,
    "STEP-02b-structure-proposal.json": STRUCTURE_PROPOSAL_NAME,
    "STEP-03-structure.md": STRUCTURE_REVIEW_NAME,
    "STEP-04-structure-preview.md": STRUCTURE_PREVIEW_NAME,
    "STEP-05-reusable-contexts.md": REUSABLE_CONTEXTS_NAME,
    "STEP-06a-placement-instruction.md": PLACEMENT_INSTRUCTION_NAME,
    "STEP-06b-placement-proposal.json": PLACEMENT_PROPOSAL_NAME,
    "STEP-08-placement.md": PLACEMENT_REVIEW_NAME,
    "STEP-08a-source-audit.md": PLACEMENT_AUDIT_NAME,
    "STEP-09-placement-preview.md": PLACEMENT_PREVIEW_NAME,
    "STEP-10-placement-followup.md": PLACEMENT_FOLLOWUP_NAME,
    "STEP-05a-placement-instruction.md": PLACEMENT_INSTRUCTION_NAME,
    "STEP-05b-placement-proposal.json": PLACEMENT_PROPOSAL_NAME,
    "STEP-07-placement.md": PLACEMENT_REVIEW_NAME,
    "STEP-07a-source-audit.md": PLACEMENT_AUDIT_NAME,
    "STEP-08-placement-preview.md": PLACEMENT_PREVIEW_NAME,
    "STEP-09-placement-followup.md": PLACEMENT_FOLLOWUP_NAME,
}

LEGACY_DIRECTORY_NAMES = {
    "STEP-08-placement": PLACEMENT_REVIEW_DIR_NAME,
    "STEP-08-source-edits": PLACEMENT_SOURCE_EDIT_DIR_NAME,
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
    def inventory_path(self) -> Path:
        return self.root / INVENTORY_NAME

    @property
    def inventory_guide_path(self) -> Path:
        return self.root / INVENTORY_GUIDE_NAME

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
    def reusable_contexts_path(self) -> Path:
        return self.root / REUSABLE_CONTEXTS_NAME

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
    def placement_dir_path(self) -> Path:
        return self.root / PLACEMENT_REVIEW_DIR_NAME

    @property
    def placement_source_edit_dir_path(self) -> Path:
        return self.root / PLACEMENT_SOURCE_EDIT_DIR_NAME

    @property
    def placement_audit_path(self) -> Path:
        return self.root / PLACEMENT_AUDIT_NAME

    @property
    def placement_preview_path(self) -> Path:
        return self.root / PLACEMENT_PREVIEW_NAME

    @property
    def placement_followup_path(self) -> Path:
        return self.root / PLACEMENT_FOLLOWUP_NAME


def _workspace_readme() -> str:
    return f"""# ContextCanon onboarding workspace
{WORKSPACE_MARKER}

This directory is the **visible human working area** for one ContextCanon onboarding. This README is the stable orientation page; the PLAN is the executable operator surface.

Start with [`{PLAN_NAME}`]({PLAN_NAME}). It keeps the numbered flow, current validated checkpoint and exact commands together so the onboarding can be resumed without chat history.

## Mental model

ContextCanon now separates the preflight from semantic onboarding:

- STEP 01 asks you to tidy obvious repository/document clutter **before durable Context references exist**;
- STEP 02 inventories the selected repository area in a human-editable CSV;
- STEP 03 freezes only the reviewed `source` / `interpret` rows as immutable Evidence;
- later steps design semantic shelves and place meaning onto them.

`.context/onboarding/` keeps machine-owned inventory state, frozen Evidence and acceptance/provenance. This directory keeps human review artifacts. The actual Context Nodes remain in their accepted repository locations.

Git storage is deliberately split: the visible workspace and heavy Evidence/review machinery are ignored by default, while the compact accepted inventory baseline (`.context/onboarding/inventory-acceptance.json`) and its small run configuration (`inventory-state.json`) remain Git-visible so a clone can reconstruct reviewed inventory choices.

The repository directory tree is evidence about the project, not a taxonomy ContextCanon must preserve.

## Why frozen Evidence exists

STEP 03 copies the reviewed `source` / `interpret` files into one immutable content-addressed snapshot. Later LLM proposals and human reviews therefore refer to the same exact bytes even if the live repository keeps changing. Start a new Evidence basis deliberately; do not let later semantic steps silently rescan the project.

## Human-facing artifacts — sorted in workflow order

- `{PLAN_NAME}` — generated operator runbook and current validated checkpoint.
- `{INVENTORY_NAME}` — human-editable file inventory.
- `{INVENTORY_GUIDE_NAME}` — short local reference for every inventory column, status and handling value.
- `{STRUCTURE_INSTRUCTION_NAME}` — generated instruction for the coarse-structure reasoning pass.
- `{STRUCTURE_PROPOSAL_NAME}` — LLM JSON for coarse structure discovery.
- `{STRUCTURE_REVIEW_NAME}` — human-editable accepted shelf map and fixed-Markdown decision.
- `{STRUCTURE_PREVIEW_NAME}` — deterministic preview before missing Node skeletons/directories are created.
- `{REUSABLE_CONTEXTS_NAME}` — human-owned reusable Context Catalog locations, sparse assignments, and Why rationale.
- `{PLACEMENT_INSTRUCTION_NAME}` — generated instruction for the placement reasoning pass.
- `{PLACEMENT_PROPOSAL_NAME}` — LLM JSON describing where existing meaning belongs.
- STEP 09 is validation-only and therefore intentionally has no separate artifact.
- `{PLACEMENT_REVIEW_NAME}` — compact STEP-10 index/status; `{PLACEMENT_REVIEW_DIR_NAME}/` contains per-finding semantic placement decisions, while `{PLACEMENT_SOURCE_EDIT_DIR_NAME}/` contains concrete source transformations.
- `{PLACEMENT_AUDIT_NAME}` — generated read-only source-file-first audit of the currently validated placement review.
- `{PLACEMENT_PREVIEW_NAME}` — exact deterministic publication preview.
- `{PLACEMENT_FOLLOWUP_NAME}` — durable follow-up after placement publication.

None of these working files become canonical Context merely because they exist. After publication, accepted structure, reusable-Context and placement meaning lives in the canonical ContextCanon sources/relationships. The compact accepted inventory baseline remains durable separately because ignored/lookup choices and owner descriptions are otherwise not represented by the canonical Nodes.

## Inventory semantics

STEP 02 deliberately keeps the PLAN short. The complete table reference lives next to the CSV in [`{INVENTORY_GUIDE_NAME}`]({INVENTORY_GUIDE_NAME}).

## Go back or restart

From the Git repository root, `contextcanon onboard reset . --from <STEP>` returns the onboarding to any STEP 01–12 without requiring a Git rollback or fresh clone. STEP 01 removes all ContextCanon-owned onboarding work/state; STEP 02 keeps only the initialized workspace; STEP 03 keeps the reviewed inventory CSV; STEP 04–12 preserve the accepted inventory and frozen Evidence while rolling back later managed work.

## Ownership

ContextCanon recognizes this workspace by the marker directly below the H1. Framework-owned README/PLAN surfaces may be regenerated; `{INVENTORY_NAME}`, `{STRUCTURE_REVIEW_NAME}` and the placement review sheets are human decision surfaces.

If a directory with the same name already exists without the marker, ContextCanon refuses to take it over. Use `--workspace <path>` to choose another directory instead.
"""

def _inventory_guide() -> str:
    return f"""# STEP 02 — Inventory guide

This page explains the human review table `{INVENTORY_NAME}`. The PLAN tells you **when** to use the table; this page tells you **how** to read and edit it.

## What you normally edit

Edit only these semantic columns unless you deliberately know why you are changing something else:

- `kind` — what the artifact is.
- `handling` — what onboarding should do with it.
- `description` — short human explanation of what the artifact represents. Required for `source` and `interpret`.
- `note` — optional owner context for the review.

Do not hand-edit `status`, `hint`, `size`, `sha256`, `accepted_sha256`, or `rule`. Rename/move files in the repository itself and rerun STEP 02 instead of editing `path` by hand.

## Columns

| Column | Meaning |
| --- | --- |
| `path` | Repository-relative file path. |
| `status` | Relation to the last known inventory/accepted baseline: `new`, `unchanged`, `changed`, or `missing`. |
| `kind` | Coarse artifact type: `document`, `transcription`, `structured-data`, `configuration`, `source-code`, `raw-record`, `generated`, `binary`, `other`, or `unknown`. |
| `handling` | Onboarding decision: `source`, `interpret`, `lookup`, `ignore`, or `undecided`. |
| `description` | Human explanation carried into frozen Evidence metadata. |
| `note` | Optional owner note. |
| `hint` | Machine-generated guidance for the row, for example that an opaque document needs a same-basename Markdown transcription. Do not edit it. |
| `size` | Current file size in bytes. Machine-owned. |
| `sha256` | Hash of the current file bytes when inventory was generated. Machine-owned. |
| `accepted_sha256` | Hash from the last successful STEP 03 acceptance; blank before first acceptance. Machine-owned. |
| `rule` | Deterministic rule that supplied the current automatic default; useful for understanding why a row started with that classification. It is not an owner decision. |

## Handling values

- `source` — direct project Evidence for the semantic onboarding passes.
- `interpret` — freeze the original bytes, but mark them as raw/ambiguous material whose meaning must be interpreted explicitly rather than silently promoted to truth.
- `lookup` — known material that may be consulted later but is not eagerly frozen into the semantic Evidence set.
- `ignore` — intentionally outside this onboarding Evidence.
- `undecided` — unresolved; STEP 03 refuses to freeze Evidence until you decide.

## Status values

- `new` — first time this path is seen in the current inventory history.
- `unchanged` — the path is still present with the same bytes as the previous inventory/accepted baseline.
- `changed` — the path is still present but its bytes changed.
- `missing` — the previously known path no longer exists in the repository scope.

You do **not** rerun inventory merely because you edited this CSV. Rerun `contextcanon onboard inventory .` only if repository files were added, changed, renamed/moved, or deleted before STEP 03. ContextCanon then preserves your semantic decisions for known paths while refreshing the machine columns and statuses.

## PDF, Word, PowerPoint and similar documents

Opaque office/PDF originals are not semantic Evidence by default. If one matters for onboarding, create a careful Markdown transcription beside it with the **same basename**, for example:

```text
architecture.pdf
architecture.md
```

On the next inventory refresh ContextCanon keeps the original as `binary / ignore` and recognizes the Markdown companion as `transcription / source`. The transcription should faithfully carry the source content; semantic condensation or reinterpretation belongs in the later onboarding review, not in a supposedly faithful transcription.

## Source code

Normal source-code files are intentionally omitted from this first-adoption CSV. Large repositories can contain hundreds or thousands of fast-changing source files, and treating each one as a durable onboarding row creates noise and change-management debt. ContextCanon will later need language/tool-aware code selection. Until then, use a deliberate custom `--rule` only when a particular source file really belongs in this onboarding Evidence review.

## Git submodules and nested repositories

Git can expose a submodule/gitlink as one path even though the working-tree path is a directory. ContextCanon shows such an entry as `other / ignore` with rule `git-directory-entry`; it does **not** descend into or hash that directory as part of the parent repository inventory. If the nested repository matters, onboard it separately from its own Git root.
"""


def _workspace_plan() -> str:
    return f"""# ContextCanon onboarding plan
{PLAN_MARKER}

This is the **operator console** for the current onboarding. Work from top to bottom. The first three steps are deliberately useful on their own: for a small document/architecture project you can stop after the reviewed Evidence snapshot and continue semantic onboarding later.

## Need to go back?

You do not need a Git rollback or a fresh clone. From the Git repository root, reset the onboarding from any numbered step and then continue from that step:

```text
contextcanon onboard reset . --from <STEP>
```

Examples: `--from 1` removes the owned onboarding workspace and onboarding machine state so you can run `contextcanon onboard init .` again; `--from 3` keeps the reviewed STEP-02 CSV but discards accepted Evidence and all later onboarding work. ContextCanon only rolls back files it can prove belong to the onboarding run.

For the exact reset options, run `contextcanon onboard reset --help`.

## Onboarding steps

{COMMANDS_START}
### STEP 01 — Tidy before durable references
- [ ] **Done**

Before ContextCanon starts creating durable references, use this cheapest moment to remove obvious duplicates, settle accidental `final-final` document versions, and move clearly misplaced files. This is guidance, not a machine gate.

### STEP 02 — Review file inventory
- [ ] **Done**

Generate or refresh the deterministic CSV inventory:

```text
contextcanon onboard inventory .
```

Open [`{INVENTORY_GUIDE_NAME}`]({INVENTORY_GUIDE_NAME}) and review/edit `{INVENTORY_NAME}`. The guide explains every column and value. **Do not rerun inventory just because you edited the CSV**; rerun only if repository files changed before STEP 03.

### STEP 03 — Freeze reviewed Evidence
- [ ] **Done**

Accept the current inventory as the Evidence boundary:

```text
contextcanon onboard prepare . --inventory {DEFAULT_WORKSPACE_NAME}/{INVENTORY_NAME}
```

ContextCanon refuses stale inventory, unresolved `undecided` rows, missing reviewed files, and newly discovered files that are absent from the CSV. Only `source` and `interpret` rows are copied into the immutable Evidence snapshot.

After STEP 03, ContextCanon replaces this section with the complete snapshot-bound STEP 01–12 runbook.
{COMMANDS_END}

## Current checkpoint

{CHECKPOINT_START}
No frozen Evidence snapshot has been accepted yet.
{CHECKPOINT_END}

The checkpoint is the **last state ContextCanon validated**, not a file watcher. Rerun inventory before STEP 03 after repository changes; after Evidence is frozen, later semantic steps stay bound to those exact bytes.

## Human gates

- **Inventory gate:** review/edit `{INVENTORY_NAME}` before freezing Evidence.
- **LLM handoff 1:** STEP 04 creates an isolated `handoffs/STEP-04-structure/` workspace plus matching ZIP.
- **Human structure gate:** review/edit `{STRUCTURE_REVIEW_NAME}`.
- **Reusable Context gate:** review/edit `{REUSABLE_CONTEXTS_NAME}`.
- **LLM handoff 2:** STEP 08 creates a fresh isolated `handoffs/STEP-08-placement/` workspace plus matching ZIP.

### Semantic handoff workspaces

Each external reasoning pass gets its **own disposable ContextCanon-prepared project**. Frozen Evidence is copied into that project at the original repository-relative paths; the only extra directory is `.contextcanon-handoff/`, which contains the one-task PLAN, exact instruction and deterministic manifest.

Open only that handoff directory in an IDE agent, or upload the matching ZIP where policy permits. Tell the model only: **follow `.contextcanon-handoff/PLAN.md`**. It may write only `.contextcanon-handoff/RESULT.json`. Earlier LLM proposals/reviews are never carried into a later handoff unless their owner-accepted meaning has already been deterministically incorporated into that later instruction.
- **Human placement gate:** use `{PLACEMENT_REVIEW_NAME}` as the index and review its linked finding/source-edit sheets.
"""

_ATOMIC_REPLACE_RETRY_DELAYS = (0.05, 0.10, 0.20, 0.40, 0.80)


def _replace_file_with_retry(temporary: Path, path: Path) -> None:
    """Publish one prepared sibling file atomically despite brief Windows locks."""

    for attempt in range(len(_ATOMIC_REPLACE_RETRY_DELAYS) + 1):
        try:
            os.replace(temporary, path)
            return
        except (PermissionError, FileExistsError) as exc:
            if attempt == len(_ATOMIC_REPLACE_RETRY_DELAYS):
                raise ContextCanonError(
                    f"Could not atomically write {path} after retrying a temporary filesystem lock: {exc}"
                ) from exc
            time.sleep(_ATOMIC_REPLACE_RETRY_DELAYS[attempt])


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
        _replace_file_with_retry(temporary, path)
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
    completed: set[int] | None = None,
) -> str:
    completed = completed or set()
    snapshot = _snapshot_label(snapshot_root)
    workspace_args = _workspace_option(workspace, snapshot_root)
    snapshot_literal = _quote_cli(snapshot)
    project_root = find_repo_root(snapshot_root)
    try:
        inventory_label = workspace.inventory_path.resolve().relative_to(project_root).as_posix()
    except ValueError:
        inventory_label = str(workspace.inventory_path.resolve())
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

    def cmd(name: str) -> str:
        return render(["contextcanon", "onboard", name, snapshot, *workspace_args])

    def mark(step: int) -> str:
        return "x" if step in completed else " "

    lines = [
        COMMANDS_START,
        "These commands continue from the **accepted inventory and exact Evidence snapshot**. The first three steps remain visible so the provenance of the semantic run is obvious.",
        "",
        "### STEP 01 — Tidy before durable references",
        f"- [{mark(1)}] **Done**",
        "",
        "Before inventory acceptance, remove obvious duplicates, settle accidental document versions and move clearly misplaced files. Once durable Topic/Resource references exist, moves deserve deliberate tooling instead of casual cleanup.",
        "",
        "### STEP 02 — Review file inventory",
        f"- [{mark(2)}] **Done**",
        "",
        "Generate or refresh the CSV whenever repository files change:",
        "",
        "```text",
        render(["contextcanon", "onboard", "inventory", ".", *workspace_args]),
        "```",
        "",
        f"Use `{INVENTORY_GUIDE_NAME}` while reviewing `{INVENTORY_NAME}`. Do not refresh merely because you edited the CSV; rerun inventory only when repository files changed.",
        "",
        "### STEP 03 — Freeze reviewed Evidence",
        f"- [{mark(3)}] **Done**",
        "",
        "Accept the current inventory and freeze only its `source` / `interpret` rows:",
        "",
        "```text",
        render(["contextcanon", "onboard", "prepare", ".", "--inventory", inventory_label, *workspace_args]),
        "```",
        "",
        "Set this run variable once for the snapshot-bound semantic steps:",
        "",
        f"```{shell}",
        snapshot_assignment,
        "```",
        "",
        "### STEP 04 — Structure proposal",
        f"- [{mark(4)}] **Done**",
        "",
        "A reasoning LLM proposes the project's semantic Context Node structure — the responsibility shelves, not merely the existing directory tree.",
        "",
        f"Generate `{STRUCTURE_INSTRUCTION_NAME}`:",
        "",
        "```text",
        cmd("structure-instruction"),
        "```",
        "",
        "The instruction command also creates the isolated handoff directory and matching ZIP:",
        "",
        "```text",
        "contextcanon-onboarding/handoffs/STEP-04-structure/",
        "contextcanon-onboarding/handoffs/STEP-04-structure.zip",
        "```",
        "",
        "Open **only** that directory as the agent project, or upload the ZIP. Tell the model: `Follow .contextcanon-handoff/PLAN.md`. When it has produced RESULT.json, import it and validate as two explicit steps:",
        "",
        "```text",
        render(["contextcanon", "onboard", "handoff-import", snapshot, "--step", "4", *workspace_args]),
        cmd("structure-validate"),
        "```",
        "",
        "### STEP 05 — Structure review",
        f"- [{mark(5)}] **Done**",
        "",
        "Review the proposed semantic shelf hierarchy.",
        "",
        "```text",
        cmd("structure-review"),
        "```",
        "",
        f"Edit `{STRUCTURE_REVIEW_NAME}` as needed, then run the same command again.",
        "",
        "### STEP 06 — Materialize shelves",
        f"- [{mark(6)}] **Done**",
        "",
        "Preview and create only missing accepted Context Node directories/skeletons. No project knowledge is placed yet.",
        "",
        "```text",
        cmd("structure-preview"),
        cmd("structure-materialize"),
        "```",
        "",
        f"Review `{STRUCTURE_PREVIEW_NAME}` between the two commands.",
        "",
        "### STEP 07 — Reusable Contexts",
        f"- [{mark(7)}] **Done**",
        "",
        "Configure reusable external Context Nodes, sparse assignments and their Why rationale.",
        "",
        "```text",
        cmd("reusable-contexts"),
        "```",
        "",
        f"The first run creates `{REUSABLE_CONTEXTS_NAME}`. Edit it and rerun the same command until accepted.",
        "",
        "### STEP 08 — Placement proposal",
        f"- [{mark(8)}] **Done**",
        "",
        "A reasoning LLM places frozen project knowledge onto the accepted own/reusable Context shelves.",
        "",
        f"Generate `{PLACEMENT_INSTRUCTION_NAME}`:",
        "",
        "```text",
        cmd("placement-instruction"),
        "```",
        "",
        "This instruction command creates a **new** isolated handoff; STEP 04's agent workspace is not reused:",
        "",
        "```text",
        "contextcanon-onboarding/handoffs/STEP-08-placement/",
        "contextcanon-onboarding/handoffs/STEP-08-placement.zip",
        "```",
        "",
        "Open/upload only that handoff and tell the model: `Follow .contextcanon-handoff/PLAN.md`. Then import the result explicitly:",
        "",
        "```text",
        render(["contextcanon", "onboard", "handoff-import", snapshot, "--step", "8", *workspace_args]),
        "```",
        "",
        "### STEP 09 — Placement validate",
        f"- [{mark(9)}] **Done**",
        "",
        "Machine-validate the proposal against frozen Evidence, accepted structure and exact reusable Context packages.",
        "",
        "```text",
        cmd("placement-validate"),
        "```",
        "",
        "### STEP 10 — Placement review",
        f"- [{mark(10)}] **Done**",
        "",
        "Review which project meaning belongs in which Context Node and any concrete source transformations.",
        "",
        "```text",
        cmd("placement-review"),
        "```",
        "",
        f"Use `{PLACEMENT_REVIEW_NAME}` as the index; rerun the same command after edits to validate and refresh `{PLACEMENT_AUDIT_NAME}`.",
        "",
        "### STEP 11 — Publication preview",
        f"- [{mark(11)}] **Done**",
        "",
        "Show the exact Context/source-document changes publication would make.",
        "",
        "```text",
        cmd("placement-preview"),
        "```",
        "",
        f"Review `{PLACEMENT_PREVIEW_NAME}` before publishing.",
        "",
        "### STEP 12 — Publish placement",
        f"- [{mark(12)}] **Done**",
        "",
        "Transactionally publish the fully reviewed Context Node authoring.",
        "",
        "```text",
        cmd("placement-publish"),
        "```",
        "",
        f"Inspect `{PLACEMENT_FOLLOWUP_NAME}` afterwards.",
        "",
        "## Go back or restart",
        "",
        "From the Git repository root, reset to any numbered step. STEP 01–03 progressively discard preflight/Evidence state; STEP 04–12 preserve the accepted inventory and frozen Evidence while rolling back later managed work:",
        "",
        "```text",
        "contextcanon onboard reset . --from <STEP>",
        "```",
        "",
        "Use `contextcanon onboard reset --help` for exact options.",
        COMMANDS_END,
    ]
    return "\n".join(lines)

def _completed_steps(stage: str, placement_review_complete: bool | None) -> set[int]:
    reset = re.fullmatch(r"reset before step (\d+)", stage)
    if reset is not None:
        target = int(reset.group(1))
        return set(range(1, max(1, target)))

    rank = {
        "evidence prepared": 3,
        "structure instruction ready": 3,
        "structure proposal validated": 4,
        "human structure validated": 5,
        "structure previewed": 5,
        "structure materialized": 6,
        "reusable contexts review": 6,
        "reusable contexts accepted": 7,
        "placement instruction ready": 7,
        "placement proposal validated": 9,
        "human placement review": 9,
        "placement publication previewed": 11,
        "placement published": 12,
    }.get(stage, 3)
    completed = set(range(1, rank + 1))
    if stage == "human placement review" and placement_review_complete is True:
        completed.add(10)
    return completed

def _rewrite_checklist(text: str, completed: set[int], path: Path) -> str:
    return text

def _replace_commands(
    text: str,
    workspace: OnboardingWorkspace,
    snapshot_root: Path,
    catalog_inputs: tuple[str, ...],
    owner_source_specs: tuple[str, ...],
    completed: set[int] | None = None,
) -> str:
    block = _exact_commands(
        workspace,
        snapshot_root,
        catalog_inputs,
        owner_source_specs,
        completed=completed,
    )
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


def _run_inputs_path(snapshot_root: Path) -> Path:
    return snapshot_root.resolve() / RUN_INPUTS_NAME


def _load_run_inputs(snapshot_root: Path) -> tuple[tuple[str, ...], tuple[str, ...]]:
    path = _run_inputs_path(snapshot_root)
    if not path.is_file():
        return (), ()
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContextCanonError(f"Invalid onboarding run input state: {path}") from exc
    if not isinstance(value, dict) or set(value) != {"schema", "catalog_package_inputs", "owner_source_specs"}:
        raise ContextCanonError(f"Invalid onboarding run input state shape: {path}")
    if value.get("schema") != RUN_INPUTS_SCHEMA:
        raise ContextCanonError(f"Unsupported onboarding run input state schema: {value.get('schema')!r}")
    catalog = value.get("catalog_package_inputs")
    owners = value.get("owner_source_specs")
    if not isinstance(catalog, list) or not all(isinstance(item, str) and item for item in catalog):
        raise ContextCanonError(f"Invalid catalog inputs in onboarding run state: {path}")
    if not isinstance(owners, list) or not all(isinstance(item, str) and item for item in owners):
        raise ContextCanonError(f"Invalid owner Source inputs in onboarding run state: {path}")
    return tuple(catalog), tuple(owners)


def remember_run_inputs(
    snapshot_root: Path, *, catalog_inputs: tuple[str, ...] = (), owner_source_specs: tuple[str, ...] = ()
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    remembered_catalog, remembered_owner = _load_run_inputs(snapshot_root)
    catalog = catalog_inputs or remembered_catalog
    owners = owner_source_specs or remembered_owner
    if not catalog and not owners and not _run_inputs_path(snapshot_root).exists():
        return (), ()
    payload = {
        "schema": RUN_INPUTS_SCHEMA,
        "catalog_package_inputs": list(catalog),
        "owner_source_specs": list(owners),
    }
    write_utf8(_run_inputs_path(snapshot_root), json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    return catalog, owners


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
    machine_catalog, machine_owner = _load_run_inputs(snapshot_root)
    catalog_inputs = source_catalog_inputs or machine_catalog or remembered_catalog
    owner_specs = owner_source_specs or machine_owner or remembered_owner
    if source_catalog_inputs or owner_source_specs or machine_catalog or machine_owner:
        catalog_inputs, owner_specs = remember_run_inputs(
            snapshot_root, catalog_inputs=catalog_inputs, owner_source_specs=owner_specs
        )

    completed = _completed_steps(stage, placement_review_complete)
    text = _replace_commands(text, workspace, snapshot_root, catalog_inputs, owner_specs, completed=completed)

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
    # Catalog paths, package identities and Source assignments are domain inputs owned by
    # STEP-07-reusable-contexts.md / machine state, not by this orchestration PLAN.
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
    for legacy_name, numbered_name in LEGACY_DIRECTORY_NAMES.items():
        legacy = workspace.root / legacy_name
        numbered = workspace.root / numbered_name
        if not legacy.exists():
            continue
        if not legacy.is_dir() or legacy.is_symlink():
            raise ContextCanonError(f"Legacy onboarding review path is not a normal directory: {legacy}")
        if numbered.exists():
            raise ContextCanonError(
                f"Onboarding workspace contains both legacy and numbered review directories: "
                f"{legacy.name}, {numbered.name}"
            )
        legacy.rename(numbered)

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


def _checkpoint_snapshot(block: str | None) -> str | None:
    if block is None:
        return None
    match = re.search(r"^- Snapshot: \`(.+?)\`$", block, re.MULTILINE)
    return match.group(1) if match else None


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
    snapshot = snapshot_root.resolve()
    if not snapshot.is_dir() or not (snapshot / "manifest.json").is_file():
        raise ContextCanonError(
            f"Expected a prepared Evidence snapshot directory, got: {snapshot_root}. "
            "The onboarding PLAN was not changed."
        )

    existing_plan = None
    if workspace.plan_path.exists():
        try:
            existing_plan = workspace.plan_path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise ContextCanonError(f"Onboarding workspace PLAN is not valid UTF-8: {workspace.plan_path}") from exc
        if PLAN_MARKER not in existing_plan:
            raise ContextCanonError(f"Refusing to take over existing unowned onboarding plan: {workspace.plan_path}")
        checkpoint = _checkpoint_block(existing_plan, workspace.plan_path)
        bound_snapshot = _checkpoint_snapshot(checkpoint)
        supplied_snapshot = _snapshot_label(snapshot)
        if bound_snapshot is not None and bound_snapshot != supplied_snapshot:
            raise ContextCanonError(
                "Onboarding workspace is bound to a different frozen Evidence snapshot. "
                f"PLAN snapshot: {bound_snapshot}; supplied snapshot: {supplied_snapshot}. "
                "The PLAN was not changed. Use the snapshot shown in PLAN.md or reset to STEP 03."
            )

    _migrate_legacy_artifacts(workspace)
    write_utf8(workspace.readme_path, _workspace_readme())
    write_utf8(workspace.inventory_guide_path, _inventory_guide())
    if not workspace.plan_path.exists():
        write_utf8(workspace.plan_path, _workspace_plan())
        plan = workspace.plan_path.read_text(encoding="utf-8")
        catalog_inputs, owner_specs = _load_run_inputs(snapshot_root)
        plan = _replace_commands(plan, workspace, snapshot_root, catalog_inputs, owner_specs)
        write_utf8(workspace.plan_path, plan)
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
    machine_catalog, machine_owner = _load_run_inputs(snapshot_root)
    catalog_inputs = machine_catalog or _remember_first(
        plan,
        (
            "- Reuse these exact `--catalog-package` inputs for copy/paste commands:",
            "- Reuse these exact `--catalog-package` inputs on the next placement command:",
        ),
    )
    owner_specs = machine_owner or _remember_first(
        plan,
        (
            "- Owner-selected Source choices already recorded in the human review (do not repeat on preview/publish):",
            "- Owner-selected Source choices already recorded in `placement.md` (do not repeat on preview/publish):",
        ),
    )
    if (catalog_inputs or owner_specs) and not (machine_catalog or machine_owner):
        catalog_inputs, owner_specs = remember_run_inputs(
            snapshot_root, catalog_inputs=catalog_inputs, owner_source_specs=owner_specs
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


def ensure_onboarding_gitignore(project_root: Path, workspace_root: Path) -> Path:
    """Ignore transient onboarding artifacts while keeping compact accepted inventory state Git-visible."""

    project = _require_project_root_for_inventory(project_root)
    gitignore = project / ".gitignore"
    try:
        existing = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    except UnicodeDecodeError as exc:
        raise ContextCanonError(f"Project .gitignore is not valid UTF-8: {gitignore}") from exc

    try:
        workspace_rel = workspace_root.resolve().relative_to(project).as_posix().rstrip("/")
    except ValueError:
        workspace_rel = ""

    lines = [GITIGNORE_START]
    if workspace_rel:
        lines.append(f"/{workspace_rel}/")
    lines.extend([
        "/.context/onboarding/*",
        "!/.context/onboarding/inventory-state.json",
        "!/.context/onboarding/inventory-acceptance.json",
        GITIGNORE_END,
    ])
    block = "\n".join(lines)

    start = existing.find(GITIGNORE_START)
    end = existing.find(GITIGNORE_END)
    if (start >= 0) != (end >= 0) or (start >= 0 and end < start):
        raise ContextCanonError(
            f"Project .gitignore contains an incomplete ContextCanon managed block: {gitignore}"
        )
    if start >= 0:
        end += len(GITIGNORE_END)
        prefix = existing[:start].rstrip("\n")
        suffix = existing[end:].lstrip("\n")
        updated = (prefix + ("\n\n" if prefix else "") + block)
        if suffix:
            updated += "\n\n" + suffix.rstrip("\n")
        updated += "\n"
    else:
        updated = existing.rstrip("\n")
        if updated:
            updated += "\n\n"
        updated += block + "\n"

    if updated != existing:
        write_utf8(gitignore, updated)
    return gitignore


def remove_onboarding_gitignore(project_root: Path) -> bool:
    """Remove only ContextCanon's marked onboarding block from the project .gitignore."""

    project = _require_project_root_for_inventory(project_root)
    gitignore = project / ".gitignore"
    if not gitignore.exists():
        return False
    try:
        existing = gitignore.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ContextCanonError(f"Project .gitignore is not valid UTF-8: {gitignore}") from exc

    start = existing.find(GITIGNORE_START)
    end = existing.find(GITIGNORE_END)
    if start < 0 and end < 0:
        return False
    if start < 0 or end < start:
        raise ContextCanonError(
            f"Project .gitignore contains an incomplete ContextCanon managed block: {gitignore}"
        )
    end += len(GITIGNORE_END)
    prefix = existing[:start].rstrip("\n")
    suffix = existing[end:].lstrip("\n")
    parts = [part for part in (prefix, suffix.rstrip("\n")) if part]
    updated = "\n\n".join(parts)
    if updated:
        write_utf8(gitignore, updated + "\n")
    else:
        gitignore.unlink()
    return True


def open_inventory_workspace(
    project_root: Path,
    workspace_root: Path | None = None,
) -> OnboardingWorkspace:
    """Open/create the visible workspace before an Evidence snapshot exists."""

    project = _require_project_root_for_inventory(project_root)
    root = workspace_root.resolve() if workspace_root is not None else project / DEFAULT_WORKSPACE_NAME
    workspace = OnboardingWorkspace(root)
    ensure_onboarding_gitignore(project, root)

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
        write_utf8(workspace.readme_path, _workspace_readme())
        write_utf8(workspace.inventory_guide_path, _inventory_guide())
        if workspace.plan_path.exists():
            try:
                plan = workspace.plan_path.read_text(encoding="utf-8")
            except UnicodeDecodeError as exc:
                raise ContextCanonError(f"Onboarding workspace PLAN is not valid UTF-8: {workspace.plan_path}") from exc
            if PLAN_MARKER not in plan:
                raise ContextCanonError(f"Refusing to take over existing unowned onboarding plan: {workspace.plan_path}")
        else:
            write_utf8(workspace.plan_path, _workspace_plan())
        return workspace

    root.mkdir(parents=True)
    write_utf8(workspace.readme_path, _workspace_readme())
    write_utf8(workspace.plan_path, _workspace_plan())
    write_utf8(workspace.inventory_guide_path, _inventory_guide())
    return workspace


def reset_inventory_workspace_plan(
    project_root: Path,
    workspace_root: Path | None = None,
    *,
    completed_steps: tuple[int, ...] = (),
) -> OnboardingWorkspace:
    """Regenerate the pre-Evidence operator PLAN after a STEP 01-03 reset."""

    workspace = open_inventory_workspace(project_root, workspace_root)
    plan = _workspace_plan()
    if completed_steps:
        plan = _rewrite_checklist(plan, set(completed_steps), workspace.plan_path)
    write_utf8(workspace.plan_path, plan)
    return workspace


def _require_project_root_for_inventory(project_root: Path) -> Path:
    project = project_root.resolve()
    if not (project / ".git").exists():
        raise ContextCanonError(
            f"Inventory workspace must be opened at the Git repository root: {project}"
        )
    return project


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
