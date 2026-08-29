from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .parser import ContextCanonError, find_repo_root


WORKSPACE_SCHEMA = "contextcanon/onboarding-workspace/v0"
DEFAULT_WORKSPACE_NAME = "contextcanon-onboarding"
WORKSPACE_MARKER = f'<!-- contextcanon:onboarding-workspace schema="{WORKSPACE_SCHEMA}" -->'

README_NAME = "README.md"
STRUCTURE_INSTRUCTION_NAME = "structure-instruction.md"
STRUCTURE_PROPOSAL_NAME = "structure-proposal.json"
STRUCTURE_REVIEW_NAME = "structure.md"
STRUCTURE_PREVIEW_NAME = "structure-preview.md"
PLACEMENT_INSTRUCTION_NAME = "placement-instruction.md"
PLACEMENT_PROPOSAL_NAME = "placement-proposal.json"
PLACEMENT_REVIEW_NAME = "placement.md"


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


def _workspace_readme() -> str:
    return f"""# ContextCanon onboarding workspace
{WORKSPACE_MARKER}

This directory is the **visible human working area** for ContextCanon onboarding. Files here are meant to be opened, reviewed, handed to a reasoning model, or edited by a human while onboarding is in progress.

It is intentionally separate from `.context/`:

- `.context/onboarding/<evidence-digest>/` contains immutable machine-owned frozen Evidence and review/acceptance state;
- `{DEFAULT_WORKSPACE_NAME}/` contains human-facing working artifacts that should remain easy to find in an IDE or file browser.

## Why frozen Evidence exists

Freezing does not freeze the live Git repository. ContextCanon copies the selected evidence into a content-addressed snapshot so every semantic pass and every human review can be tied to the **same exact project bytes**.

That has two benefits. First, ContextCanon can detect when a reviewed live file changed before acceptance. Second, onboarding itself becomes restartable: a different semantic assignment, a corrected prompt contract, or another review iteration can reuse the same frozen Evidence instead of rescanning and silently changing the basis of the experiment. Prepare a new snapshot only when you intentionally want a new evidence basis.

## Standard files for structure-first onboarding

- `{STRUCTURE_INSTRUCTION_NAME}` — generated UTF-8 instruction for the external strong reasoning LLM. ContextCanon owns this file; regenerate it rather than editing it.
- `{STRUCTURE_PROPOSAL_NAME}` — JSON returned by the external LLM for coarse structure discovery.
- `{STRUCTURE_REVIEW_NAME}` — human-editable accepted shelf map. Rename, re-indent, add, remove, or reserve Nodes here.
- `{STRUCTURE_PREVIEW_NAME}` — deterministic preview of existing protected Nodes and missing Node skeletons before materialization.
- `{PLACEMENT_INSTRUCTION_NAME}` — generated instruction for the second semantic pass after the owner has edited the structure.
- `{PLACEMENT_PROPOSAL_NAME}` — JSON returned by the external LLM describing where existing project knowledge belongs.
- `{PLACEMENT_REVIEW_NAME}` — readable evidence-rich placement review showing source excerpt, destination/action, and proposed canonical wording.

The structure file is the human-owned coarse map. The placement pass is not allowed to redesign it. None of these working files become canonical Context merely because they exist.

## Ownership

ContextCanon recognizes this directory by the marker directly below the H1 above. If a directory with the same name already exists without that marker, ContextCanon refuses to take it over. Use `--workspace <path>` to choose another directory instead.

This workspace may be kept while onboarding is active. Cleanup of transient onboarding material remains an explicit later operation; do not delete frozen Evidence or accepted provenance merely because the visible workspace is no longer needed.
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
