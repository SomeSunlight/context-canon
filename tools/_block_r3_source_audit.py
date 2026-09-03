from __future__ import annotations

import argparse
from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one match, found {count}: {old[:120]!r}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


def activate_plan() -> None:
    path = Path("PLAN.md")
    text = path.read_text(encoding="utf-8")
    marker = "**Status: NEXT — Blocks R1/R2 complete; continue with the remaining Block R follow-up slices. Fast-run remains ACTIVE.**"
    active = """**Status: ACTIVE — Block R3 source-file-first transformation audit. Fast-run remains ACTIVE.**

R3 purpose: keep `STEP-07-placement.md` as the single human-editable review truth while generating a deterministic source-file-first audit from the currently parsed review. The audit must group Source edits by original file/range and show exact Before, effective After, every linked P-finding, and the current reviewed destination/content so zero semantic loss can be checked without hunting through destination-first sections.

R3 verification: focused source-audit, placement-review and reset regressions first, then the complete deterministic suite plus self-hosted build/check and hygiene before the clean checkpoint."""
    if "R3 purpose:" not in text:
        if marker not in text:
            raise SystemExit("PLAN.md: R1/R2 completion marker not found")
        path.write_text(text.replace(marker, active, 1), encoding="utf-8")


AUDIT_PY = r'''from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from .onboarding_placement import OnboardingPlacementProposal
from .onboarding_placement_review import OnboardingPlacementReview, PlacementReviewItem, PlacementReviewSourceEdit
from .onboarding_proposal import EvidenceSnapshot, load_evidence_snapshot
from .parser import ContextCanonError


PLACEMENT_SOURCE_AUDIT_SCHEMA = "contextcanon/onboarding-placement-source-audit/v0"


def _fenced(text: str, language: str = "text") -> list[str]:
    longest = 2
    run = 0
    for char in text:
        if char == "`":
            run += 1
            longest = max(longest, run)
        else:
            run = 0
    fence = "`" * max(3, longest + 1)
    return [f"{fence}{language}", *text.split("\n"), fence]


def _before_text(edit: PlacementReviewSourceEdit, snapshot: EvidenceSnapshot) -> str:
    entry = snapshot.by_path.get(edit.path)
    if entry is None or entry.sha256 != edit.sha256:
        raise ContextCanonError(f"Source audit Evidence binding no longer matches snapshot: {edit.path}")
    path = snapshot.root / "evidence" / edit.path
    lines = path.read_text(encoding="utf-8").splitlines()
    if edit.start_line < 1 or edit.end_line > len(lines) or edit.end_line < edit.start_line:
        raise ContextCanonError(f"Source audit range is outside frozen Evidence: {edit.path}:{edit.start_line}-{edit.end_line}")
    return "\n".join(lines[edit.start_line - 1 : edit.end_line])


def _destination_line(item: PlacementReviewItem, proposal: OnboardingPlacementProposal) -> str:
    if item.destination_node_key is None:
        return "Destination: none / outside Node authoring"
    nodes = {node.key: node for node in proposal.structure.nodes}
    node = nodes.get(item.destination_node_key)
    if node is None:
        raise ContextCanonError(f"Source audit references unknown destination Node: {item.destination_node_key}")
    return f"Destination: `{node.key}` — **{node.name}** (`{node.path}`)"


def _payload_lines(item: PlacementReviewItem) -> list[str]:
    payload = item.payload
    if item.kind == "rule":
        return [
            f"Statement: {payload['statement']}",
            f"Why: {payload['why']}",
            f"Wording: `{payload['wording_origin']}`",
        ]
    if item.kind in {"overview", "state", "plan"}:
        return [f"Summary: {payload['text']}", f"Wording: `{payload['wording_origin']}`"]
    if item.kind == "topic-resource":
        resources = ", ".join(f"`{path}`" for path in payload["resource_paths"])
        return [f"Condition: {payload['condition']}", f"Resources: {resources}"]
    if item.kind == "ordinary-documentation":
        documents = ", ".join(f"`{path}`" for path in payload["document_paths"])
        return [f"Documents: {documents}", f"Reason: {payload['reason']}"]
    if item.kind == "authority-mapping":
        authorities = ", ".join(f"`{path}`" for path in payload["authority_paths"])
        return [
            f"Authorities: {authorities}",
            f"Mapping: {payload['mapping']}",
            f"Wording: `{payload['wording_origin']}`",
        ]
    if item.kind == "unresolved":
        return [f"Question: {payload['question']}"]
    raise ContextCanonError(f"Source audit cannot render unsupported placement kind: {item.kind}")


def render_placement_source_audit(
    proposal: OnboardingPlacementProposal,
    review: OnboardingPlacementReview,
    snapshot_root: Path,
    *,
    review_filename: str = "STEP-07-placement.md",
) -> str:
    if review.evidence_digest != proposal.evidence_digest:
        raise ContextCanonError("Source audit review Evidence digest does not match placement proposal")
    if review.structure_digest != proposal.structure_digest:
        raise ContextCanonError("Source audit review structure digest does not match placement proposal")
    if review.proposal_digest != proposal.proposal_digest:
        raise ContextCanonError("Source audit review proposal digest does not match placement proposal")

    snapshot = load_evidence_snapshot(snapshot_root)
    items = {item.proposal_id: item for item in review.items}
    grouped: dict[str, list[PlacementReviewSourceEdit]] = defaultdict(list)
    for edit in review.source_edits:
        grouped[edit.path].append(edit)

    lines = [
        "# ContextCanon source transformation audit",
        "",
        "> **Generated, read-only view.** Edit `STEP-07-placement.md`, not this file. Rerunning `contextcanon onboard placement-review ...` validates the human gate and regenerates this audit from that exact parsed review.",
        "",
        "This view answers one question per source range: **if this text is shortened or replaced, where does every linked piece of maintained meaning land?** It is grouped by original source file rather than destination Node so semantic-loss review does not require chasing scattered findings.",
        "",
        "<!-- contextcanon-placement-source-audit",
        f"schema: {PLACEMENT_SOURCE_AUDIT_SCHEMA}",
        f"evidence_digest: {review.evidence_digest}",
        f"structure_digest: {review.structure_digest}",
        f"proposal_digest: {review.proposal_digest}",
        f"review_digest: {review.review_digest}",
        "-->",
        "",
    ]

    if not grouped:
        lines.extend([
            "No Source After transformations are currently present in the reviewed placement.",
            "",
            "That is valid: promoted meaning may leave its source untouched when the original document remains independently useful or authoritative.",
        ])
        return "\n".join(lines).rstrip() + "\n"

    for path in sorted(grouped):
        lines.extend([f"## `{path}`", ""])
        for edit in sorted(grouped[path], key=lambda value: (value.start_line, value.end_line, value.proposal_id)):
            before = _before_text(edit, snapshot)
            lines.extend([
                f"### {edit.proposal_id} — lines {edit.start_line}-{edit.end_line}",
                "",
                f"Review control: [`{edit.proposal_id}` in {review_filename}]({review_filename}#source-edit-{edit.proposal_id.lower()})",
                "",
                f"Source edit decision: `{edit.decision}`",
                f"Source edit note: {edit.review_note or '-'}",
                f"Frozen SHA-256: `{edit.sha256}`",
                "",
                "#### Before — exact frozen source range",
                "",
            ])
            lines.extend(_fenced(before))
            lines.append("")

            if edit.decision == "accept":
                lines.extend(["#### Effective after — accepted replacement", ""])
                lines.extend(_fenced(edit.replacement))
            elif edit.decision == "reject":
                lines.extend([
                    "#### Effective after — unchanged because this Source edit is rejected",
                    "",
                ])
                lines.extend(_fenced(before))
                lines.extend(["", "#### Proposed replacement — not applied", ""])
                lines.extend(_fenced(edit.replacement))
            else:
                lines.extend([
                    "#### Effective after — undecided",
                    "",
                    "No effective replacement exists while this Source edit remains `pending`.",
                    "",
                    "#### Proposed replacement — candidate under review",
                    "",
                ])
                lines.extend(_fenced(edit.replacement))
            lines.extend(["", "#### Linked maintained meaning", ""])

            for item_id in edit.linked_item_ids:
                item = items.get(item_id)
                if item is None:
                    raise ContextCanonError(f"Source audit edit {edit.proposal_id} references missing review item {item_id}")
                lines.extend([
                    f"##### {item.proposal_id} — {item.title}",
                    "",
                    f"Finding decision: `{item.decision}`",
                    _destination_line(item, proposal),
                    f"Kind: `{item.kind}` · Derived action: `{item.action}`",
                    "",
                    "Reviewed destination content (effective only when this finding is accepted):",
                    "",
                ])
                lines.extend(_payload_lines(item))
                lines.append("")

            lines.extend(["---", ""])

    return "\n".join(lines).rstrip() + "\n"
'''


TEST_AUDIT = r'''from __future__ import annotations

import contextlib
import io
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from contextcanon.cli import main
from contextcanon.onboarding_placement import load_onboarding_placement_proposal
from contextcanon.onboarding_placement_audit import render_placement_source_audit
from contextcanon.onboarding_placement_review import create_or_load_placement_review, load_placement_review
import tests.test_onboarding_placement as placement_fixture


class PlacementSourceAuditTests(unittest.TestCase):
    def make_review(self):
        helper = placement_fixture.OnboardingPlacementTests()
        _, prepared, workspace, readme, architecture, source_root, package = helper.make_case()
        raw = helper.placement_dict(prepared, workspace, readme, architecture, package)
        workspace.placement_proposal_path.write_text(json.dumps(raw), encoding="utf-8")
        proposal = load_onboarding_placement_proposal(
            workspace.placement_proposal_path,
            prepared.snapshot_root,
            workspace.structure_proposal_path,
            workspace.structure_path,
            catalog_package_roots=[source_root],
        )
        review, _ = create_or_load_placement_review(
            workspace.placement_path,
            proposal,
            prepared.snapshot_root,
        )
        return prepared, workspace, source_root, proposal, review

    def test_source_first_audit_groups_exact_range_and_destination_content(self):
        prepared, workspace, _, proposal, review = self.make_review()
        text = workspace.placement_path.read_text(encoding="utf-8")
        text = text.replace("Decision: `pending`", "Decision: `accept`", 1)
        text = text.replace("Source edit decision: `pending`", "Source edit decision: `accept`", 1)
        workspace.placement_path.write_text(text, encoding="utf-8")
        review = load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)

        audit = render_placement_source_audit(proposal, review, prepared.snapshot_root)
        self.assertIn("## `docs/architecture.md`", audit)
        self.assertIn("### E-001 — lines 2-2", audit)
        self.assertIn("The repository is the installation specification.", audit)
        self.assertIn("Effective after — accepted replacement", audit)
        self.assertIn("Installation authority is maintained in [AI Workstation Context](../CONTEXT.md).", audit)
        self.assertIn("##### P-001 — Repository is the installation specification", audit)
        self.assertIn("Finding decision: `accept`", audit)
        self.assertIn("Destination: `N-001` — **AI Workstation** (`.`)", audit)
        self.assertIn("Statement: The repository is the installation specification.", audit)
        self.assertIn("Why: Running state must not become undocumented authority.", audit)

    def test_rejected_source_edit_shows_unchanged_effective_after_and_candidate(self):
        prepared, workspace, _, proposal, _ = self.make_review()
        text = workspace.placement_path.read_text(encoding="utf-8")
        text = text.replace("Source edit decision: `pending`", "Source edit decision: `reject`", 1)
        workspace.placement_path.write_text(text, encoding="utf-8")
        review = load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)

        audit = render_placement_source_audit(proposal, review, prepared.snapshot_root)
        self.assertIn("Effective after — unchanged because this Source edit is rejected", audit)
        self.assertIn("Proposed replacement — not applied", audit)
        self.assertGreaterEqual(audit.count("The repository is the installation specification."), 2)
        self.assertIn("Installation authority is maintained in [AI Workstation Context](../CONTEXT.md).", audit)

    def test_cli_placement_review_regenerates_read_only_audit(self):
        helper = placement_fixture.OnboardingPlacementTests()
        _, prepared, workspace, readme, architecture, source_root, package = helper.make_case()
        raw = helper.placement_dict(prepared, workspace, readme, architecture, package)
        workspace.placement_proposal_path.write_text(json.dumps(raw), encoding="utf-8")

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            result = main([
                "onboard", "placement-review", str(prepared.snapshot_root),
                "--catalog-package", str(source_root),
            ])
        self.assertEqual(result, 0)
        self.assertTrue(workspace.placement_audit_path.is_file())
        first = workspace.placement_audit_path.read_text(encoding="utf-8")
        self.assertIn("Generated, read-only view", first)
        self.assertIn("Source edit decision: `pending`", first)
        self.assertIn("Source audit:", stdout.getvalue())

        review_text = workspace.placement_path.read_text(encoding="utf-8")
        review_text = review_text.replace("Decision: `pending`", "Decision: `accept`", 1)
        review_text = review_text.replace("Source edit decision: `pending`", "Source edit decision: `accept`", 1)
        workspace.placement_path.write_text(review_text, encoding="utf-8")
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            result = main([
                "onboard", "placement-review", str(prepared.snapshot_root),
                "--catalog-package", str(source_root),
            ])
        self.assertEqual(result, 0)
        refreshed = workspace.placement_audit_path.read_text(encoding="utf-8")
        self.assertNotEqual(first, refreshed)
        self.assertIn("Source edit decision: `accept`", refreshed)
        self.assertIn("Effective after — accepted replacement", refreshed)


if __name__ == "__main__":
    unittest.main()
'''


def patch_code() -> None:
    Path("src/contextcanon/onboarding_placement_audit.py").write_text(AUDIT_PY, encoding="utf-8")
    Path("tests/test_onboarding_placement_audit.py").write_text(TEST_AUDIT, encoding="utf-8")

    replace_once(
        "src/contextcanon/cli.py",
        "from .onboarding_placement import load_onboarding_placement_proposal\n",
        "from .onboarding_placement import load_onboarding_placement_proposal\nfrom .onboarding_placement_audit import render_placement_source_audit\n",
    )
    replace_once(
        "src/contextcanon/cli.py",
        '''                    verb = "created" if created else "loaded"
                    print(f"{verb} onboarding placement review {review.review_digest}")
                    print(f"Review file: {review_path}")
                    print(f"Items: {len(review.items)} · Source edits: {len(review.source_edits)} · Sources: {len(review.sources)} · complete: {review.is_complete}")
                    next_action = (
                        f"Run `contextcanon onboard placement-preview {_snapshot_cli(snapshot)}` after checking the exact command in PLAN.md."
                        if review.is_complete else
                        f"Edit `{workspace.placement_path.name}`: review Into Node, Source Before/After, and set every item/Source-edit/Source Decision to `accept` or `reject`. "
                        f"Then rerun `contextcanon onboard placement-review {_snapshot_cli(snapshot)}` to validate the edited human gate before preview."
                    )
''',
        '''                    verb = "created" if created else "loaded"
                    write_utf8(
                        workspace.placement_audit_path,
                        render_placement_source_audit(proposal, review, snapshot, review_filename=review_path.name),
                    )
                    print(f"{verb} onboarding placement review {review.review_digest}")
                    print(f"Review file: {review_path}")
                    print(f"Source audit: {workspace.placement_audit_path}")
                    print(f"Items: {len(review.items)} · Source edits: {len(review.source_edits)} · Sources: {len(review.sources)} · complete: {review.is_complete}")
                    next_action = (
                        f"Review `{workspace.placement_audit_path.name}` for source-by-source semantic loss, then run `contextcanon onboard placement-preview {_snapshot_cli(snapshot)}` after checking the exact command in PLAN.md."
                        if review.is_complete else
                        f"Inspect `{workspace.placement_audit_path.name}` source-by-source, edit `{workspace.placement_path.name}` where needed, and set every item/Source-edit/Source Decision to `accept` or `reject`. "
                        f"Then rerun `contextcanon onboard placement-review {_snapshot_cli(snapshot)}`; it validates the edited human gate and regenerates the audit."
                    )
''',
    )

    replace_once(
        "src/contextcanon/onboarding_workspace.py",
        'PLACEMENT_REVIEW_NAME = "STEP-07-placement.md"\nPLACEMENT_PREVIEW_NAME = "STEP-08-placement-preview.md"\n',
        'PLACEMENT_REVIEW_NAME = "STEP-07-placement.md"\nPLACEMENT_AUDIT_NAME = "STEP-07a-source-audit.md"\nPLACEMENT_PREVIEW_NAME = "STEP-08-placement-preview.md"\n',
    )
    replace_once(
        "src/contextcanon/onboarding_workspace.py",
        '''    def placement_path(self) -> Path:
        return self.root / PLACEMENT_REVIEW_NAME

    @property
    def placement_preview_path(self) -> Path:
''',
        '''    def placement_path(self) -> Path:
        return self.root / PLACEMENT_REVIEW_NAME

    @property
    def placement_audit_path(self) -> Path:
        return self.root / PLACEMENT_AUDIT_NAME

    @property
    def placement_preview_path(self) -> Path:
''',
    )
    replace_once(
        "src/contextcanon/onboarding_workspace.py",
        'f"- `{PLACEMENT_REVIEW_NAME}` — human-owned placement decisions.\\n"\n',
        'f"- `{PLACEMENT_REVIEW_NAME}` — human-owned placement decisions.\\n"\n        f"- `{PLACEMENT_AUDIT_NAME}` — generated read-only source-file-first audit of the currently validated placement review.\\n"\n',
    )
    replace_once(
        "src/contextcanon/onboarding_workspace.py",
        '- [ ] 7. Placement review — create/edit `{PLACEMENT_REVIEW_NAME}` and rerun the review command until every human decision validates.\n',
        '- [ ] 7. Placement review — create/edit `{PLACEMENT_REVIEW_NAME}`; every review validation regenerates `{PLACEMENT_AUDIT_NAME}` for source-file-first semantic-loss checking.\n',
    )
    replace_once(
        "src/contextcanon/onboarding_workspace.py",
        '            "### 8. Publication preview",\n',
        '            f"`{PLACEMENT_AUDIT_NAME}` is read-only and is regenerated by every successful placement-review validation. Use it to audit Source After transformations by original file/range; make corrections only in `{PLACEMENT_REVIEW_NAME}`.",\n            "",\n            "### 8. Publication preview",\n',
    )

    replace_once(
        "src/contextcanon/onboarding_reset.py",
        "    PLACEMENT_FOLLOWUP_NAME,\n",
        "    PLACEMENT_AUDIT_NAME,\n    PLACEMENT_FOLLOWUP_NAME,\n",
    )
    replace_once(
        "src/contextcanon/onboarding_reset.py",
        "    PLACEMENT_REVIEW_NAME: 7,\n    PLACEMENT_PREVIEW_NAME: 8,\n",
        "    PLACEMENT_REVIEW_NAME: 7,\n    PLACEMENT_AUDIT_NAME: 7,\n    PLACEMENT_PREVIEW_NAME: 8,\n",
    )

    replace_once(
        "src/contextcanon/README.md",
        "- `onboarding.py`, `onboarding_instruction.py`, `onboarding_proposal.py`, `onboarding_review.py` — the reviewed first-adoption pipeline;\n",
        "- `onboarding.py`, `onboarding_instruction.py`, `onboarding_proposal.py`, `onboarding_review.py` — the reviewed first-adoption pipeline;\n- `onboarding_placement_audit.py` — generated source-file-first audit projection of the current human placement review;\n",
    )

    replace_once(
        "tests/test_onboarding_reset.py",
        "from contextcanon.onboarding_workspace import (\n    PLACEMENT_REVIEW_NAME,\n",
        "from contextcanon.onboarding_workspace import (\n    PLACEMENT_AUDIT_NAME,\n    PLACEMENT_REVIEW_NAME,\n",
    )
    replace_once(
        "tests/test_onboarding_reset.py",
        '        self.assertEqual(PLACEMENT_REVIEW_NAME, "STEP-07-placement.md")\n',
        '        self.assertEqual(PLACEMENT_REVIEW_NAME, "STEP-07-placement.md")\n        self.assertEqual(PLACEMENT_AUDIT_NAME, "STEP-07a-source-audit.md")\n        self.assertIn(PLACEMENT_AUDIT_NAME, plan)\n',
    )
    replace_once(
        "tests/test_onboarding_reset.py",
        "    def test_journaled_materialization_reset_restores_only_contextcanon_managed_bytes(self):\n",
        '''    def test_reset_from_step7_removes_generated_source_audit(self):
        _, prepared = self.make_repo()
        workspace = open_onboarding_workspace(prepared.snapshot_root, create=True)
        workspace.placement_path.write_text("human review\n", encoding="utf-8")
        workspace.placement_audit_path.write_text("generated audit\n", encoding="utf-8")

        reset = reset_onboarding(prepared.snapshot_root, from_step=7)
        self.assertFalse(workspace.placement_path.exists())
        self.assertFalse(workspace.placement_audit_path.exists())
        self.assertIn(PLACEMENT_AUDIT_NAME, reset["workspace_files_removed"])

    def test_journaled_materialization_reset_restores_only_contextcanon_managed_bytes(self):
''',
    )


def complete_plan_state() -> None:
    path = Path("PLAN.md")
    text = path.read_text(encoding="utf-8")
    active = "**Status: ACTIVE — Block R3 source-file-first transformation audit. Fast-run remains ACTIVE.**"
    done = "**Status: NEXT — Blocks R1/R2/R3 complete; continue with semantic parent composition and Source-update UX. Fast-run remains ACTIVE.**"
    if active not in text:
        raise SystemExit("PLAN.md: active R3 marker not found")
    text = text.replace(active, done, 1)
    text = text.replace(
        "- [ ] Reduce rendered/source switching during review. Evaluate a separate source-file-first transformation review surface for Source After edits, grouped by original file/range and showing exact before/after plus every linked P-finding and final destination Node/content.",
        "- [x] Reduce rendered/source switching during review. Evaluate a separate source-file-first transformation review surface for Source After edits, grouped by original file/range and showing exact before/after plus every linked P-finding and final destination Node/content.",
        1,
    )
    text = text.replace(
        "- [ ] Make cross-linked E-edits easy to audit for zero semantic loss: from one source edit, the owner should be able to see where each removed substantive meaning lands without chasing findings from unrelated parts of the document.",
        "- [x] Make cross-linked E-edits easy to audit for zero semantic loss: from one source edit, the owner should be able to see where each removed substantive meaning lands without chasing findings from unrelated parts of the document.",
        1,
    )
    verification = """

R3 purpose: keep Step 07 as the single editable review while making source-side semantic-loss checking source-first rather than destination-first. Each successful placement-review validation now regenerates `STEP-07a-source-audit.md` from the parsed human review.

R3 verification: focused source-audit/placement-review/reset regressions passed, followed by the complete deterministic suite, self-hosted build/check and `git diff --check`. The generated audit groups transformations by original file/range, shows exact frozen Before and decision-dependent effective After, and inlines every linked finding's current decision, destination, Kind/Action and reviewed destination content. The audit is reset with Step 07 and is never an editable truth surface.
"""
    anchor = "R2 verification: focused authoring/CLI regressions passed, followed by the complete deterministic suite, self-hosted build/check and `git diff --check`. `contextcanon author rule` and `contextcanon author topic` now allocate stable IDs and write ordinary validated `CONTEXT.src.md`; Foundation documents the minimal native-project daily loop.\n"
    if "R3 verification:" not in text:
        if anchor not in text:
            raise SystemExit("PLAN.md: R2 verification anchor not found")
        text = text.replace(anchor, anchor + verification, 1)
    path.write_text(text, encoding="utf-8")

    state = Path("STATE.md")
    state_text = state.read_text(encoding="utf-8")
    block = """

## Latest Block R3 source-transformation-audit checkpoint

The remaining post-publish review-UX gap is closed without creating a second human gate. Every successful `contextcanon onboard placement-review` validation now deterministically regenerates `STEP-07a-source-audit.md` from the currently parsed `STEP-07-placement.md`. Step 07 remains the only editable placement truth; the audit is explicitly generated/read-only and reset together with Step 07.

The audit reverses the review axis from destination-first to source-first. Source edits are grouped by original file and exact frozen range; each shows exact Before, the decision-dependent effective After (or unchanged source for rejection), any non-applied candidate replacement, and every linked P-finding with its current decision, destination Node, Kind/derived Action and reviewed destination content. This makes zero-semantic-loss review possible from one source transformation without hunting across unrelated finding sections.

Blocks R1-R3 now close the immediate production review/authoring UX findings. The next substantial Block R work is semantic parent composition: persisting the owner-accepted Step-03 hierarchy as explicit accepted package relationships, extending inheritance to Topics/resources, and rendering complete effective context. Source-update discovery UX remains a later adjacent slice. Fast-run remains active; PR #13 remains draft and unmerged.
"""
    if "Latest Block R3 source-transformation-audit checkpoint" not in state_text:
        state.write_text(state_text.rstrip() + block + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--complete", action="store_true")
    args = parser.parse_args()
    if args.complete:
        complete_plan_state()
        return
    activate_plan()
    patch_code()


if __name__ == "__main__":
    main()
