from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def patch(path, old, new, label):
    p = ROOT / path
    text = p.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"{label}: expected one anchor, found {text.count(old)}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


patch(
    "src/contextcanon/onboarding_workspace.py",
    'PLACEMENT_REVIEW_DIR_NAME = "STEP-08-placement"\nPLACEMENT_AUDIT_NAME = "STEP-08a-source-audit.md"',
    'PLACEMENT_REVIEW_DIR_NAME = "STEP-08-placement"\nPLACEMENT_SOURCE_EDIT_DIR_NAME = "STEP-08-source-edits"\nPLACEMENT_AUDIT_NAME = "STEP-08a-source-audit.md"',
    "workspace source-edit constant",
)
patch(
    "src/contextcanon/onboarding_workspace.py",
    '    @property\n    def placement_dir_path(self) -> Path:\n        return self.root / PLACEMENT_REVIEW_DIR_NAME\n\n    @property\n    def placement_audit_path(self) -> Path:',
    '    @property\n    def placement_dir_path(self) -> Path:\n        return self.root / PLACEMENT_REVIEW_DIR_NAME\n\n    @property\n    def placement_source_edit_dir_path(self) -> Path:\n        return self.root / PLACEMENT_SOURCE_EDIT_DIR_NAME\n\n    @property\n    def placement_audit_path(self) -> Path:',
    "workspace source-edit property",
)
patch(
    "src/contextcanon/onboarding_workspace.py",
    '- `{PLACEMENT_REVIEW_NAME}` — compact STEP-08 index/status; linked files in `{PLACEMENT_REVIEW_DIR_NAME}/` are the human-owned per-finding placement decisions.',
    '- `{PLACEMENT_REVIEW_NAME}` — compact STEP-08 index/status; `{PLACEMENT_REVIEW_DIR_NAME}/` contains per-finding semantic placement decisions (P), while `{PLACEMENT_SOURCE_EDIT_DIR_NAME}/` contains concrete source transformations (E).',
    "workspace README artifact description",
)
patch(
    "src/contextcanon/onboarding_workspace.py",
    '- **Human gate 2:** use `STEP-08-placement.md` as the index and review/edit the linked files under `STEP-08-placement/`.',
    '- **Human gate 2:** use `STEP-08-placement.md` as the index; review semantic P findings under `STEP-08-placement/` and concrete E source transformations under `STEP-08-source-edits/`.',
    "workspace plan human gate",
)
patch(
    "src/contextcanon/onboarding_workspace.py",
    '        "Edit `STEP-08-placement.md` as needed and rerun the same command to validate it. Every successful run regenerates read-only `STEP-08a-source-audit.md` for source-file-first semantic-loss checking.",',
    '        "Review/edit the linked P sheets in `STEP-08-placement/` and E sheets in `STEP-08-source-edits/`. The tables in `STEP-08-placement.md` are generated snapshots, not live views; rerun this same `placement-review` command after edits to validate dependencies and refresh the index. Every successful run also regenerates read-only `STEP-08a-source-audit.md`.",',
    "workspace STEP 08 guidance",
)

patch(
    "src/contextcanon/onboarding_reset.py",
    '    PLACEMENT_REVIEW_NAME,\n    PLACEMENT_REVIEW_DIR_NAME,\n    PLAN_MARKER,',
    '    PLACEMENT_REVIEW_NAME,\n    PLACEMENT_REVIEW_DIR_NAME,\n    PLACEMENT_SOURCE_EDIT_DIR_NAME,\n    PLAN_MARKER,',
    "reset import",
)
patch(
    "src/contextcanon/onboarding_reset.py",
    '    PLACEMENT_REVIEW_DIR_NAME: 8,\n    PLACEMENT_AUDIT_NAME: 8,',
    '    PLACEMENT_REVIEW_DIR_NAME: 8,\n    PLACEMENT_SOURCE_EDIT_DIR_NAME: 8,\n    PLACEMENT_AUDIT_NAME: 8,',
    "reset artifact step",
)
patch(
    "src/contextcanon/onboarding_reset.py",
    '        if name == PLACEMENT_REVIEW_DIR_NAME and path.is_dir() and not path.is_symlink():',
    '        if name in {PLACEMENT_REVIEW_DIR_NAME, PLACEMENT_SOURCE_EDIT_DIR_NAME} and path.is_dir() and not path.is_symlink():',
    "reset recursive review directories",
)

patch(
    "src/contextcanon/onboarding_placement_audit.py",
    'from .onboarding_placement_split_review import placement_finding_filename',
    'from .onboarding_placement_split_review import placement_source_edit_filename',
    "audit import",
)
patch(
    "src/contextcanon/onboarding_placement_audit.py",
    '            finding_dir = Path(review_filename).with_suffix("").name\n            control_target = f"{finding_dir}/{placement_finding_filename(proposal_item)}#source-edit-{edit.proposal_id.lower()}"',
    '            control_target = f"STEP-08-source-edits/{placement_source_edit_filename(edit)}"',
    "audit E control target",
)
patch(
    "src/contextcanon/onboarding_placement_audit.py",
    'f"> **Generated, read-only view.** Use `{review_filename}` as the STEP-08 index and edit its linked finding files, not this audit. Rerunning `contextcanon onboard placement-review ...` validates the human gate and regenerates this audit from that exact parsed review.",',
    'f"> **Generated, read-only view.** Use `{review_filename}` as the STEP-08 index and edit its linked P/E review files, not this audit. Rerunning `contextcanon onboard placement-review ...` validates the human gate and regenerates this audit from that exact parsed review.",',
    "audit guidance",
)

plan = ROOT / "PLAN.md"
text = plan.read_text(encoding="utf-8")
anchor = "## Project-owner accepted block: structure-first onboarding on ai-workstation"
if "## Owner-test follow-up: separate STEP 08 P/E review sheets — Issue #36" not in text:
    block = '''## Owner-test follow-up: separate STEP 08 P/E review sheets — Issue #36

Purpose: keep the successful per-finding STEP-08 review while separating semantic placement decisions from concrete source transformations and making both review surfaces self-explanatory.

- [x] Keep P findings as focused semantic placement/handling sheets under `STEP-08-placement/`, with Destination and Kind in the title, a first-contact explanation, proper Markdown bullet controls, explicit `Into Node N-xxx — Name` headings, and numbered Evidence sections.
- [x] Move every E Source edit into its own Markdown sheet under `STEP-08-source-edits/`, link P↔E in both directions, and show the linked P acceptance dependency before the E decision.
- [x] Add separate P/E tables to `STEP-08-placement.md` and state next to them that they are generated snapshots refreshed by rerunning `contextcanon onboard placement-review $SNAPSHOT`.
- [x] Keep split-v1 owner-test state deliberately non-migrating: reset from STEP 08 and recreate instead of carrying transitional compatibility code.
- [ ] Run focused/full deterministic regressions, zero-drift check and clean-diff verification; keep PR #31 draft/unmerged for continued owner validation.

Checkpoint: Issue #36 is implemented for a fresh STEP-08 owner test. P owns semantic interpretation/placement; E owns concrete source-file transformation. Verification is still pending on the final product tree; PR #31 remains draft and unmerged.

'''
    if anchor not in text:
        raise RuntimeError("PLAN insertion anchor missing")
    plan.write_text(text.replace(anchor, block + anchor, 1), encoding="utf-8")

print("Issue #36 support surfaces patched")
