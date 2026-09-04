from __future__ import annotations

import json
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
RUN_INPUTS_SCHEMA = "contextcanon/onboarding-run-inputs/v0"
RUN_INPUTS_NAME = "run-inputs.json"

README_NAME = "README.md"
PLAN_NAME = "PLAN.md"
STRUCTURE_INSTRUCTION_NAME = "STEP-02a-structure-instruction.md"
STRUCTURE_PROPOSAL_NAME = "STEP-02b-structure-proposal.json"
STRUCTURE_REVIEW_NAME = "STEP-03-structure.md"
STRUCTURE_PREVIEW_NAME = "STEP-04-structure-preview.md"
REUSABLE_CONTEXTS_NAME = "STEP-05-reusable-contexts.md"
PLACEMENT_INSTRUCTION_NAME = "STEP-06a-placement-instruction.md"
PLACEMENT_PROPOSAL_NAME = "STEP-06b-placement-proposal.json"
PLACEMENT_REVIEW_NAME = "STEP-08-placement.md"
PLACEMENT_AUDIT_NAME = "STEP-08a-source-audit.md"
PLACEMENT_PREVIEW_NAME = "STEP-09-placement-preview.md"
PLACEMENT_FOLLOWUP_NAME = "STEP-10-placement-followup.md"

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
    "STEP-05a-placement-instruction.md": PLACEMENT_INSTRUCTION_NAME,
    "STEP-05b-placement-proposal.json": PLACEMENT_PROPOSAL_NAME,
    "STEP-07-placement.md": PLACEMENT_REVIEW_NAME,
    "STEP-07a-source-audit.md": PLACEMENT_AUDIT_NAME,
    "STEP-08-placement-preview.md": PLACEMENT_PREVIEW_NAME,
    "STEP-09-placement-followup.md": PLACEMENT_FOLLOWUP_NAME,
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
- `{REUSABLE_CONTEXTS_NAME}` — human-owned reusable Context Catalog locations, sparse assignments, and Why rationale.
- `{PLACEMENT_INSTRUCTION_NAME}` — generated instruction for the placement reasoning pass.
- `{PLACEMENT_PROPOSAL_NAME}` — LLM JSON describing where existing meaning belongs.
- Step 07 is validation-only and therefore intentionally has no separate artifact.
- `{PLACEMENT_REVIEW_NAME}` — human-owned placement decisions.
- `{PLACEMENT_AUDIT_NAME}` — generated read-only source-file-first audit of the currently validated placement review.
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

This is the **operator console** for the current onboarding. Work from top to bottom. Each step keeps its explanation, completion checkbox, exact command and produced artifact together so you do not have to scroll between a checklist and a separate command manual.

## Onboarding steps

{COMMANDS_START}
The exact snapshot-bound steps appear here after ContextCanon opens this workspace.
{COMMANDS_END}

## Current checkpoint

{CHECKPOINT_START}
No ContextCanon structure-first command has recorded a checkpoint in this workspace yet.
{CHECKPOINT_END}

The checkpoint is the **last state ContextCanon validated**, not a file watcher. After editing a human gate, rerun that same step before advancing.

## Human gates

- **LLM handoff 1:** `STEP-02a-structure-instruction.md` + only the frozen `evidence/` tree → `STEP-02b-structure-proposal.json`.
- **Human gate 1:** review/edit `STEP-03-structure.md`.
- **Reusable Context gate:** review/edit `STEP-05-reusable-contexts.md`; this owns Catalog locations, Source assignments and their Why rationale.
- **LLM handoff 2:** `STEP-06a-placement-instruction.md` + only the same frozen `evidence/` tree → `STEP-06b-placement-proposal.json`.
- **Human gate 2:** review/edit `STEP-08-placement.md`.

Normal onboarding commands deliberately do not require you to reconstruct Source Node IDs, package digests, Catalog paths or one-time Source-selection syntax. Those machine identities are resolved and retained by ContextCanon from STEP 05.
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
    completed: set[int] | None = None,
) -> str:
    completed = completed or set()
    snapshot = _snapshot_label(snapshot_root)
    workspace_args = _workspace_option(workspace, snapshot_root)
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

    def cmd(name: str) -> str:
        return render(["contextcanon", "onboard", name, snapshot, *workspace_args])

    def mark(step: int) -> str:
        return "x" if step in completed else " "

    lines = [
        COMMANDS_START,
        "These commands are for **this exact Evidence snapshot**. ContextCanon carries forward machine identities and accepted human inputs; copy the short command shown in the current step.",
        "",
        "Set this run variable once in your terminal:",
        "",
        f"```{shell}",
        snapshot_assignment,
        "```",
        "",
        "### STEP 01 — Freeze Evidence",
        f"- [{mark(1)}] **Done**",
        "",
        "ContextCanon freezes the exact project files used as onboarding Evidence so every later LLM/human decision refers to the same bytes. Reuse the current snapshot unless you intentionally want new Evidence.",
        "",
        "```text",
        "contextcanon onboard prepare .",
        "```",
        "",
        "### STEP 02 — Structure proposal",
        f"- [{mark(2)}] **Done**",
        "",
        "A reasoning LLM proposes the project's **semantic Context Node structure** — the responsibility shelves, not merely the existing directory tree.",
        "",
        "Generate `STEP-02a-structure-instruction.md`:",
        "",
        "```text",
        cmd("structure-instruction"),
        "```",
        "",
        "Give that instruction plus only the frozen `evidence/` tree to the LLM and save its JSON exactly as `STEP-02b-structure-proposal.json`. Then validate:",
        "",
        "```text",
        cmd("structure-validate"),
        "```",
        "",
        "### STEP 03 — Structure review",
        f"- [{mark(3)}] **Done**",
        "",
        "You review the proposed project Context Node hierarchy: which semantic shelves exist, their names, paths and parent/child grouping.",
        "",
        "```text",
        cmd("structure-review"),
        "```",
        "",
        "Edit `STEP-03-structure.md` as needed, then run the same command again to validate the human gate.",
        "",
        "### STEP 04 — Materialize shelves",
        f"- [{mark(4)}] **Done**",
        "",
        "ContextCanon previews and then creates only the missing accepted Context Node directories/skeletons. No project knowledge is placed yet.",
        "",
        "```text",
        cmd("structure-preview"),
        cmd("structure-materialize"),
        "```",
        "",
        "Review `STEP-04-structure-preview.md` between the two commands.",
        "",
        "### STEP 05 — Reusable Contexts",
        f"- [{mark(5)}] **Done**",
        "",
        "You tell ContextCanon **where reusable external Context Nodes can be found, which accepted project Nodes they apply to, and why**. This prepares the foreign shelves before the placement LLM distributes project knowledge.",
        "",
        "```text",
        cmd("reusable-contexts"),
        "```",
        "",
        "The first run creates `STEP-05-reusable-contexts.md`. Edit its Catalog locations and sparse Assignments, set `Decision` to `accept` when correct, and rerun the same command after every edit. You work with names/path/version; ContextCanon owns IDs and digests.",
        "",
        "### STEP 06 — Placement proposal",
        f"- [{mark(6)}] **Done**",
        "",
        "A reasoning LLM now places the project's frozen knowledge onto the already accepted own/reusable Context shelves and proposes any reviewed source-document cleanup.",
        "",
        "Generate `STEP-06a-placement-instruction.md`:",
        "",
        "```text",
        cmd("placement-instruction"),
        "```",
        "",
        "Give that instruction plus only the frozen `evidence/` tree to the LLM and save its JSON exactly as `STEP-06b-placement-proposal.json`.",
        "",
        "### STEP 07 — Placement validate",
        f"- [{mark(7)}] **Done**",
        "",
        "ContextCanon checks the LLM proposal against the frozen Evidence, accepted project structure and exact reusable Context packages. This is machine validation; there is no separate STEP-07 artifact.",
        "",
        "```text",
        cmd("placement-validate"),
        "```",
        "",
        "### STEP 08 — Placement review",
        f"- [{mark(8)}] **Done**",
        "",
        "You review **which project knowledge goes into which Context Node**. Reusable Context assignments from STEP 05 are already decided and appear only as compact traceability, not as a giant selection matrix.",
        "",
        "```text",
        cmd("placement-review"),
        "```",
        "",
        "Edit `STEP-08-placement.md` as needed and rerun the same command to validate it. Every successful run regenerates read-only `STEP-08a-source-audit.md` for source-file-first semantic-loss checking.",
        "",
        "### STEP 09 — Publication preview",
        f"- [{mark(9)}] **Done**",
        "",
        "ContextCanon shows the exact Context/source-document changes that publication would make, including semantic Parent pins and reusable Source installation.",
        "",
        "```text",
        cmd("placement-preview"),
        "```",
        "",
        "Review `STEP-09-placement-preview.md` before publishing.",
        "",
        "### STEP 10 — Publish placement",
        f"- [{mark(10)}] **Done**",
        "",
        "ContextCanon transactionally publishes the fully reviewed Context Node authoring and produces the durable follow-up report.",
        "",
        "```text",
        cmd("placement-publish"),
        "```",
        "",
        "Inspect `STEP-10-placement-followup.md` afterwards.",
        "",
        "## Reset commands for testing",
        "",
        "Frozen Evidence is preserved. Restart from the semantic step you want to retest:",
        "",
        "```text",
    ]
    for step in range(2, 11):
        lines.append(render(["contextcanon", "onboard", "reset", snapshot, "--from", str(step), *workspace_args]))
    lines.extend(["```", COMMANDS_END])
    return "\n".join(lines)

def _completed_steps(stage: str, placement_review_complete: bool | None) -> set[int]:
    reset = re.fullmatch(r"reset before step (\d+)", stage)
    if reset is not None:
        target = int(reset.group(1))
        return set(range(1, max(1, target)))

    rank = {
        "structure instruction ready": 1,
        "structure proposal validated": 2,
        "human structure validated": 3,
        "structure previewed": 3,
        "structure materialized": 4,
        "reusable contexts review": 4,
        "reusable contexts accepted": 5,
        "placement instruction ready": 5,
        "placement proposal validated": 7,
        "human placement review": 7,
        "placement publication previewed": 9,
        "placement published": 10,
    }.get(stage, 1)
    completed = set(range(1, rank + 1))
    if stage == "human placement review" and placement_review_complete is True:
        completed.add(8)
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
    # STEP-05-reusable-contexts.md / machine state, not by this orchestration PLAN.
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
