from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from contextcanon.onboarding_placement import load_onboarding_placement_proposal
from contextcanon.onboarding_placement_review import (
    create_or_load_placement_review,
    load_placement_review,
    render_placement_review,
)
from contextcanon.onboarding_placement_split_review import (
    placement_finding_path,
    placement_review_directory,
    placement_source_edit_directory,
    placement_source_edit_path,
)
from contextcanon.parser import ContextCanonError
import tests.test_onboarding_placement as placement_fixture


class EditablePlacementReviewTests(unittest.TestCase):
    def make_proposal(self, *, owner_source: bool = True):
        helper = placement_fixture.OnboardingPlacementTests()
        _, prepared, workspace, readme, architecture, source_root, package = helper.make_case()
        raw = helper.placement_dict(prepared, workspace, readme, architecture, package)
        if owner_source:
            raw["source_reuses"] = []
        workspace.placement_proposal_path.write_text(json.dumps(raw), encoding="utf-8")
        proposal = load_onboarding_placement_proposal(
            workspace.placement_proposal_path,
            prepared.snapshot_root,
            workspace.structure_proposal_path,
            workspace.structure_path,
            catalog_package_roots=[source_root],
        )
        specs = [f"N-001={package.metadata.id}"] if owner_source else []
        return prepared, workspace, source_root, package, proposal, specs

    def make_review(self, *, owner_source: bool = True):
        prepared, workspace, source_root, package, proposal, specs = self.make_proposal(owner_source=owner_source)
        review, created = create_or_load_placement_review(
            workspace.placement_path,
            proposal,
            prepared.snapshot_root,
            owner_source_specs=specs,
        )
        return prepared, workspace, source_root, package, proposal, review, created

    def finding(self, workspace, proposal, item_id="P-001") -> Path:
        item = next(item for item in proposal.items if item.id == item_id)
        return placement_finding_path(workspace.placement_path, item)

    def source_edit(self, workspace, review, edit_id=None) -> Path:
        edit = review.source_edits[0] if edit_id is None else next(
            value for value in review.source_edits if value.proposal_id == edit_id
        )
        return placement_source_edit_path(workspace.placement_path, edit)

    def accept_finding(self, workspace, proposal, item_id="P-001") -> None:
        path = self.finding(workspace, proposal, item_id)
        text = path.read_text(encoding="utf-8").replace("- Decision: `pending`", "- Decision: `accept`", 1)
        path.write_text(text, encoding="utf-8")

    def test_review_is_split_into_self_explanatory_p_and_e_sheets(self):
        prepared, workspace, source_root, package, proposal, review, created = self.make_review()
        self.assertTrue(created)
        index = workspace.placement_path.read_text(encoding="utf-8")
        finding = self.finding(workspace, proposal).read_text(encoding="utf-8")
        edit = self.source_edit(workspace, review).read_text(encoding="utf-8")

        self.assertIn("cc:placement-review-layout: split-v2", index)
        self.assertIn("## Findings", index)
        self.assertIn("## Source edits", index)
        self.assertIn("generated Markdown, not a live view", index)
        self.assertIn("contextcanon onboard placement-review $SNAPSHOT", index)
        self.assertEqual(len(list(placement_review_directory(workspace.placement_path).glob("*.md"))), len(proposal.items))
        self.assertEqual(len(list(placement_source_edit_directory(workspace.placement_path).glob("*.md"))), len(review.source_edits))

        self.assertTrue(finding.startswith("# P-001 — N-001 — AI Workstation · rule —"))
        self.assertIn("## What this page decides", finding)
        self.assertIn("P = **semantic interpretation/placement**", finding)
        self.assertIn("- Destination: `N-001`", finding)
        self.assertIn("- Decision: `pending`", finding)
        self.assertIn("- Kind: `rule`", finding)
        self.assertIn("## Into Node N-001 — AI Workstation", finding)
        self.assertIn("- Statement:", finding)
        self.assertIn("## Evidence", finding)
        self.assertIn("### Evidence 1", finding)
        self.assertNotIn("Source edit decision:", finding)
        self.assertIn("../STEP-10-source-edits/", finding)

        self.assertTrue(edit.startswith("# E-001 — P-001 —"))
        self.assertIn("concrete transformation", edit)
        self.assertIn("may be accepted only when every linked promoted P finding is accepted", edit)
        self.assertIn("- Source edit decision: `pending`", edit)
        self.assertIn("../STEP-10-placement/", edit)
        self.assertIn("## Before — frozen source", edit)
        self.assertIn("## After — editable replacement", edit)
        self.assertIn('cc:source-after id="E-001":start', edit)
        self.assertIn('origin="owner-selected"', index)

    def test_human_finding_edits_round_trip_and_headings_refresh(self):
        prepared, workspace, source_root, package, proposal, first, _ = self.make_review(owner_source=False)
        first_id = first.items[0].authoring_id
        path = self.finding(workspace, proposal)
        text = path.read_text(encoding="utf-8")
        first_line, rest = text.split("\n", 1)
        first_line = first_line.replace("Repository is the installation specification", "Canonical installation authority")
        text = first_line + "\n" + rest
        text = text.replace("- Decision: `pending`", "- Decision: `accept`", 1)
        text = text.replace(
            "- Statement: The repository is the installation specification.",
            "- Statement: The repository is the canonical installation specification.",
            1,
        )
        path.write_text(text, encoding="utf-8")

        second, created = create_or_load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)
        self.assertFalse(created)
        self.assertEqual(second.items[0].authoring_id, first_id)
        self.assertEqual(second.items[0].title, "Canonical installation authority")
        self.assertEqual(second.items[0].decision, "accept")
        self.assertEqual(second.items[0].payload["statement"], "The repository is the canonical installation specification.")
        refreshed = path.read_text(encoding="utf-8")
        self.assertIn("Canonical installation authority", refreshed.splitlines()[0])
        self.assertIn("- Decision: `accept`", refreshed)

    def test_source_edit_round_trips_from_its_own_sheet(self):
        prepared, workspace, source_root, package, proposal, review, _ = self.make_review(owner_source=False)
        self.accept_finding(workspace, proposal)
        path = self.source_edit(workspace, review)
        text = path.read_text(encoding="utf-8")
        old = "> Installation authority is maintained in [AI Workstation Context](../CONTEXT.md)."
        new_plain = "Architecture starts here; maintained installation authority lives in [AI Workstation Context](../CONTEXT.md)."
        text = text.replace(old, "> " + new_plain, 1)
        text = text.replace("- Source edit decision: `pending`", "- Source edit decision: `accept`", 1)
        path.write_text(text, encoding="utf-8")

        loaded = load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)
        self.assertEqual(loaded.source_edits[0].replacement, new_plain)
        self.assertEqual(loaded.source_edits[0].decision, "accept")

    def test_source_after_requires_single_quote_frame(self):
        prepared, workspace, source_root, package, proposal, review, _ = self.make_review(owner_source=False)
        path = self.source_edit(workspace, review)
        text = path.read_text(encoding="utf-8").replace(
            "> Installation authority is maintained in [AI Workstation Context](../CONTEXT.md).",
            "Installation authority is maintained in [AI Workstation Context](../CONTEXT.md).",
            1,
        )
        path.write_text(text, encoding="utf-8")
        with self.assertRaisesRegex(ContextCanonError, "single Markdown quote frame"):
            load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)

    def test_source_edit_acceptance_dependency_is_visible_and_enforced(self):
        prepared, workspace, source_root, package, proposal, review, _ = self.make_review(owner_source=False)
        finding = self.finding(workspace, proposal)
        finding.write_text(
            finding.read_text(encoding="utf-8").replace("- Decision: `pending`", "- Decision: `reject`", 1),
            encoding="utf-8",
        )
        edit = self.source_edit(workspace, review)
        rendered = edit.read_text(encoding="utf-8")
        self.assertIn("P-001", rendered)
        self.assertIn("decision `pending`", rendered)
        edit.write_text(
            rendered.replace("- Source edit decision: `pending`", "- Source edit decision: `accept`", 1),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ContextCanonError, "cannot be accepted until all linked promoted findings are accepted"):
            load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)

    def test_action_is_derived_from_kind_and_display_text_is_not_a_control(self):
        prepared, workspace, source_root, package, proposal, review, _ = self.make_review(owner_source=False)
        path = self.finding(workspace, proposal)
        text = path.read_text(encoding="utf-8").replace(
            "- Derived action: `promote` (from Kind; do not edit)",
            "- Derived action: `reference` (tampered display text)",
            1,
        )
        path.write_text(text, encoding="utf-8")
        loaded = load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)
        self.assertEqual(loaded.items[0].kind, "rule")
        self.assertEqual(loaded.items[0].action, "promote")

    def test_invalid_or_duplicate_stable_authoring_id_is_rejected(self):
        prepared, workspace, source_root, package, proposal, review, _ = self.make_review(owner_source=False)
        first_id = review.items[0].authoring_id
        second_id = review.items[1].authoring_id
        first_path = self.finding(workspace, proposal, "P-001")
        second_path = self.finding(workspace, proposal, "P-002")
        original_first = first_path.read_text(encoding="utf-8")
        first_path.write_text(original_first.replace(f'authoring-id="{first_id}"', 'authoring-id="bad id"', 1), encoding="utf-8")
        with self.assertRaisesRegex(ContextCanonError, "invalid stable authoring ID"):
            load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)
        first_path.write_text(original_first, encoding="utf-8")
        second = second_path.read_text(encoding="utf-8")
        second_path.write_text(second.replace(f'authoring-id="{second_id}"', f'authoring-id="{first_id}"', 1), encoding="utf-8")
        with self.assertRaisesRegex(ContextCanonError, "duplicate stable authoring ID"):
            load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)

    def test_promote_without_llm_source_edit_gets_separate_rejected_fallback_e_sheet(self):
        helper = placement_fixture.OnboardingPlacementTests()
        _, prepared, workspace, readme, architecture, source_root, package = helper.make_case()
        raw = helper.placement_dict(prepared, workspace, readme, architecture, package)
        raw["source_edits"] = []
        raw["items"][0]["evidence"] = [{"path": "README.md", "sha256": readme.sha256, "start_line": 2, "end_line": 2}]
        workspace.placement_proposal_path.write_text(json.dumps(raw), encoding="utf-8")
        proposal = load_onboarding_placement_proposal(
            workspace.placement_proposal_path,
            prepared.snapshot_root,
            workspace.structure_proposal_path,
            workspace.structure_path,
            catalog_package_roots=[source_root],
        )
        review, created = create_or_load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)
        self.assertTrue(created)
        self.assertEqual(len(review.source_edits), 1)
        fallback = review.source_edits[0]
        self.assertTrue(fallback.proposal_id.startswith("H-"))
        self.assertEqual(fallback.decision, "reject")
        finding = self.finding(workspace, proposal).read_text(encoding="utf-8")
        edit_path = self.source_edit(workspace, review)
        edit = edit_path.read_text(encoding="utf-8")
        self.assertNotIn("Optional cleanup", finding)
        self.assertIn("**Optional cleanup:**", edit)
        self.assertIn("- Source edit decision: `reject`", edit)

    def test_multiple_source_edits_are_independent_e_files_and_linked_from_p(self):
        helper = placement_fixture.OnboardingPlacementTests()
        _, prepared, workspace, readme, architecture, source_root, package = helper.make_case()
        raw = helper.placement_dict(prepared, workspace, readme, architecture, package)
        raw["items"][0]["evidence"][0]["start_line"] = 1
        raw["source_edits"].append(
            {
                "id": "E-002",
                "path": "docs/architecture.md",
                "sha256": architecture.sha256,
                "start_line": 1,
                "end_line": 1,
                "linked_item_ids": ["P-001"],
                "replacement": "# Architecture gateway",
                "rationale": "Keep a compact architecture gateway beside the promoted canonical rule.",
                "confidence": "high",
            }
        )
        workspace.placement_proposal_path.write_text(json.dumps(raw), encoding="utf-8")
        proposal = load_onboarding_placement_proposal(
            workspace.placement_proposal_path,
            prepared.snapshot_root,
            workspace.structure_proposal_path,
            workspace.structure_path,
            catalog_package_roots=[source_root],
        )
        review, created = create_or_load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)
        self.assertTrue(created)
        self.assertEqual(len(list(placement_source_edit_directory(workspace.placement_path).glob("*.md"))), 2)
        finding = self.finding(workspace, proposal).read_text(encoding="utf-8")
        self.assertIn("E-001", finding)
        self.assertIn("E-002", finding)
        loaded = load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)
        self.assertEqual([edit.proposal_id for edit in loaded.source_edits], ["E-001", "E-002"])

    def test_interim_split_v1_is_not_migrated(self):
        prepared, workspace, source_root, package, proposal, review, _ = self.make_review(owner_source=False)
        index = workspace.placement_path.read_text(encoding="utf-8")
        workspace.placement_path.write_text(index.replace("split-v2", "split-v1", 1), encoding="utf-8")
        with self.assertRaisesRegex(ContextCanonError, "not migrated|Reset from STEP 08"):
            create_or_load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)

    def test_legacy_monolith_can_still_enter_current_review_layout(self):
        prepared, workspace, source_root, package, proposal, specs = self.make_proposal(owner_source=False)
        legacy = render_placement_review(proposal, prepared.snapshot_root)
        legacy = legacy.replace("Decision: `pending`", "Decision: `accept`", 1)
        workspace.placement_path.write_text(legacy, encoding="utf-8")
        review, created = create_or_load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)
        self.assertFalse(created)
        self.assertEqual(review.items[0].decision, "accept")
        self.assertIn("split-v2", workspace.placement_path.read_text(encoding="utf-8"))
        self.assertTrue(placement_review_directory(workspace.placement_path).is_dir())
        self.assertTrue(placement_source_edit_directory(workspace.placement_path).is_dir())

    def test_many_findings_scale_as_index_plus_one_p_sheet_each(self):
        helper = placement_fixture.OnboardingPlacementTests()
        _, prepared, workspace, readme, architecture, source_root, package = helper.make_case()
        raw = helper.placement_dict(prepared, workspace, readme, architecture, package)
        template = raw["items"][1]
        raw["items"] = []
        for number in range(1, 41):
            item = json.loads(json.dumps(template))
            item["id"] = f"P-{number:03d}"
            item["title"] = f"Architecture reference {number:02d}"
            raw["items"].append(item)
        raw["source_edits"] = []
        raw["source_reuses"] = []
        workspace.placement_proposal_path.write_text(json.dumps(raw), encoding="utf-8")
        proposal = load_onboarding_placement_proposal(
            workspace.placement_proposal_path,
            prepared.snapshot_root,
            workspace.structure_proposal_path,
            workspace.structure_path,
            catalog_package_roots=[source_root],
        )
        review_gate, created = create_or_load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)
        self.assertTrue(created)
        self.assertEqual(len(review_gate.items), 40)
        self.assertEqual(len(list(placement_review_directory(workspace.placement_path).glob("*.md"))), 40)
        self.assertEqual(len(list(placement_source_edit_directory(workspace.placement_path).glob("*.md"))), 0)
        index = workspace.placement_path.read_text(encoding="utf-8")
        self.assertEqual(index.count("STEP-10-placement/P-"), 40)
        self.assertNotIn("## Evidence", index)
        self.assertLess(len(index.splitlines()), 150)

    def test_missing_or_foreign_p_and_e_files_are_rejected(self):
        prepared, workspace, source_root, package, proposal, review, _ = self.make_review(owner_source=False)
        first = self.finding(workspace, proposal)
        original = first.read_text(encoding="utf-8")
        first.unlink()
        with self.assertRaisesRegex(ContextCanonError, "missing finding files"):
            load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)
        first.write_text(original, encoding="utf-8")

        edit = self.source_edit(workspace, review)
        original_edit = edit.read_text(encoding="utf-8")
        edit.unlink()
        with self.assertRaisesRegex(ContextCanonError, "missing Source-edit files"):
            load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)
        edit.write_text(original_edit, encoding="utf-8")

        foreign = placement_source_edit_directory(workspace.placement_path) / "notes.md"
        foreign.write_text("human stray file", encoding="utf-8")
        with self.assertRaisesRegex(ContextCanonError, "foreign Source-edit"):
            load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)


if __name__ == "__main__":
    unittest.main()
