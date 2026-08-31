from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .parser import ContextCanonError, find_repo_root


WORKSPACE_SCHEMA = "contextcanon/onboarding-workspace/v0"
DEFAULT_WORKSPACE_NAME = "contextcanon-onboarding"
WORKSPACE_MARKER = f'<!-- contextcanon:onboarding-workspace schema="{WORKSPACE_SCHEMA}" -->'
CHECKPOINT_START = "<!-- contextcanon-onboarding-checkpoint:start -->"
CHECKPOINT_END = "<!-- contextcanon-onboarding-checkpoint:end -->"

README_NAME = "README.md"
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

This directory is the **visible human working area** for one structure-first ContextCanon onboarding. Open this README when returning after a pause: the numbered runbook explains the complete sequence, and **Current checkpoint** below says which validated step comes next.

It is intentionally separate from `.context/`:

- `.context/onboarding/<evidence-digest>/` contains immutable machine-owned frozen Evidence and review/acceptance state;
- `{DEFAULT_WORKSPACE_NAME}/` contains human-facing working artifacts that should remain easy to find in an IDE or file browser.

## Runbook — do these in order

The workflow has two deliberately visible LLM handoffs and two human review gates. ContextCanon owns the deterministic steps around them.

### 1. Freeze Evidence

```text
contextcanon onboard prepare .
```

Keep the resulting `.context/onboarding/<evidence-digest>` path. Reuse the same snapshot while you intentionally want to review the same source bytes; do not refreeze merely because you restart the experiment.

### 2. Generate the structure assignment

```text
contextcanon onboard structure-instruction .context/onboarding/<evidence-digest>
```

Add any reusable catalog package with repeated `--catalog-package <package-root>` when you want the structure reviewer to compare it.

**LLM handoff 1:** give `{STRUCTURE_INSTRUCTION_NAME}` and only the frozen snapshot's `evidence/` tree to a strong reasoning LLM. Save its single JSON result as `{STRUCTURE_PROPOSAL_NAME}`.

### 3. Validate and human-review the shelves

```text
contextcanon onboard structure-validate .context/onboarding/<evidence-digest>
contextcanon onboard structure-review .context/onboarding/<evidence-digest>
```

**Human gate 1:** edit `{STRUCTURE_REVIEW_NAME}` until the Node hierarchy matches the project's mental model. Nodes are semantic landing points, not aliases for today's directory tree. An accepted Node path may name a directory that does not exist yet; materialization can create it safely.

The same file also lets the owner mark Markdown as fixed/authoritative instead of mutable migration material.

### 4. Preview and materialize the accepted shelves

```text
contextcanon onboard structure-preview .context/onboarding/<evidence-digest>
contextcanon onboard structure-materialize .context/onboarding/<evidence-digest>
```

Review `{STRUCTURE_PREVIEW_NAME}` before materializing. Missing accepted Node directories/skeletons are created; existing Context Nodes and ordinary project files are preserved.

### 5. Generate the placement assignment

```text
contextcanon onboard placement-instruction .context/onboarding/<evidence-digest> \
  --catalog-package <package-root>
```

Use the same exact reusable Source catalog for the placement commands that follow.

**LLM handoff 2:** give `{PLACEMENT_INSTRUCTION_NAME}` and only the same frozen `evidence/` tree to the reasoning LLM. Save its single JSON result as `{PLACEMENT_PROPOSAL_NAME}`.

### 6. Validate and human-review where meaning belongs

```text
contextcanon onboard placement-validate .context/onboarding/<evidence-digest> \
  --catalog-package <package-root>

contextcanon onboard placement-review .context/onboarding/<evidence-digest> \
  --catalog-package <package-root> \
  --owner-source N-001=<source-node-id>
```

`--owner-source` is optional and is used **only when creating the human review** to add a deliberate owner-selected Source. Once written into `{PLACEMENT_REVIEW_NAME}`, that choice is part of the review and is not repeated on preview/publish commands.

**Human gate 2:** edit `{PLACEMENT_REVIEW_NAME}`. Resolve every Decision and correct destination, kind/action, title, or maintained wording where necessary.

### 7. Preview exact publication

```text
contextcanon onboard placement-preview .context/onboarding/<evidence-digest> \
  --catalog-package <package-root>
```

Review `{PLACEMENT_PREVIEW_NAME}`. It shows exact Context source changes and reusable Source state before project mutation.

### 8. Publish the reviewed placement

```text
contextcanon onboard placement-publish .context/onboarding/<evidence-digest> \
  --catalog-package <package-root>
```

Publication makes reviewed ContextCanon authoring canonical. It does **not** immediately rewrite ordinary README/CONTRIBUTING/docs prose. Any duplicate source prose created by migration is transitional and must later be removed or reduced to concise orientation/reference through a separate reviewed cleanup operation.

After publication, inspect `{PLACEMENT_FOLLOWUP_NAME}` for accepted state/plan/documentation/unresolved work that intentionally remains outside current Node authoring.

## Standard files

- `{STRUCTURE_INSTRUCTION_NAME}` — generated instruction for LLM handoff 1.
- `{STRUCTURE_PROPOSAL_NAME}` — LLM JSON for coarse structure discovery.
- `{STRUCTURE_REVIEW_NAME}` — human-editable accepted shelf map and fixed-Markdown decision.
- `{STRUCTURE_PREVIEW_NAME}` — deterministic preview before Node skeleton creation.
- `{PLACEMENT_INSTRUCTION_NAME}` — generated instruction for LLM handoff 2.
- `{PLACEMENT_PROPOSAL_NAME}` — LLM JSON describing where existing meaning belongs.
- `{PLACEMENT_REVIEW_NAME}` — human-owned placement decisions.
- `{PLACEMENT_PREVIEW_NAME}` — exact deterministic publication preview.
- `{PLACEMENT_FOLLOWUP_NAME}` — durable follow-up after placement publication.

None of these working files become canonical Context merely because they exist; only explicit publication changes reviewed Context Node authoring.

## Why frozen Evidence exists

Freezing does not freeze the live Git repository. ContextCanon copies selected evidence into a content-addressed snapshot so every semantic pass and human review can be tied to the **same exact project bytes**.

That gives two benefits. ContextCanon can detect when a reviewed live file changed before acceptance, and an onboarding iteration can reuse the same Evidence rather than rescanning and silently changing the comparison basis. Prepare a new snapshot only when you intentionally want a new evidence basis.

## Current checkpoint

{CHECKPOINT_START}
No ContextCanon structure-first command has recorded a checkpoint in this workspace yet.
{CHECKPOINT_END}

The checkpoint above is the **last state ContextCanon validated**, not a file watcher. If you edit `{STRUCTURE_REVIEW_NAME}` or `{PLACEMENT_REVIEW_NAME}`, the edit becomes validated human input only after the next ContextCanon command loads it successfully and advances this checkpoint.

## Ownership

ContextCanon recognizes this directory by the marker directly below the H1 above. If a directory with the same name already exists without that marker, ContextCanon refuses to take it over. Use `--workspace <path>` to choose another directory instead.

This workspace may be kept while onboarding is active. Cleanup of transient onboarding material remains explicit; do not delete frozen Evidence or accepted provenance merely because the visible workspace is no longer needed.
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
    """Rewrite only the framework-owned checkpoint inside the visible README."""

    try:
        text = workspace.readme_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ContextCanonError(f"Missing onboarding workspace README: {workspace.readme_path}") from exc
    if WORKSPACE_MARKER not in text:
        raise ContextCanonError(f"Refusing to update unowned onboarding workspace README: {workspace.readme_path}")

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

    if CHECKPOINT_START in text or CHECKPOINT_END in text:
        if text.count(CHECKPOINT_START) != 1 or text.count(CHECKPOINT_END) != 1:
            raise ContextCanonError(f"Malformed onboarding checkpoint markers in {workspace.readme_path}")
        start = text.index(CHECKPOINT_START)
        end = text.index(CHECKPOINT_END, start) + len(CHECKPOINT_END)
        text = text[:start] + block + text[end:]
    else:
        anchor = "\n## Ownership\n"
        if anchor not in text:
            raise ContextCanonError(f"Cannot add onboarding checkpoint to unexpected README layout: {workspace.readme_path}")
        text = text.replace(
            anchor,
            "\n## Current checkpoint\n\n" + block +
            "\n\nThe checkpoint above is the **last state ContextCanon validated**, not a file watcher. "
            "If you edit `structure.md` or `placement.md`, the edit becomes authoritative human input only after "
            "the next ContextCanon command validates it and advances this checkpoint.\n" + anchor,
            1,
        )
    write_utf8(workspace.readme_path, text)


def _default_workspace_root(snapshot_root: Path) -> Path:
    project_root = find_repo_root(snapshot_root)
    if not (project_root / ".git").exists():
        raise ContextCanonError(
            "Cannot infer the onboarding project root from the Evidence snapshot; "
            "run from/use a snapshot inside its Git repository or pass --workspace explicitly"
        )
    return project_root / DEFAULT_WORKSPACE_NAME


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
        return workspace

    if not create:
        raise ContextCanonError(
            f"Missing onboarding workspace: {root}; run 'contextcanon onboard structure-instruction ...' first "
            "or pass explicit proposal/structure paths"
        )

    root.mkdir(parents=True)
    write_utf8(workspace.readme_path, _workspace_readme())
    return workspace
