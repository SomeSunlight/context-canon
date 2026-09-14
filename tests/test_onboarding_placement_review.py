from __future__ import annotations

import json
import shutil
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

    def test_review_is_split_navigable_and_owner_source_is_distinct(self):
        prepared, workspace, source_root, package, proposal, review, created = self.make_review()
        self.assertTrue(created)
        index = workspace.placement_path.read_text(encoding="utf-8")
        finding = self.finding(workspace, proposal).read_text(encoding="utf-8")
        review_dir = placement_review_directory(workspace.placement_path)
        self.assertTrue(review_dir.is_dir())
        self.assertEqual(len(list(review_dir.glob("*.md"))), len(proposal.items))
        self.assertIn("cc:placement-review-layout: split-v1", index)
        self.assertIn("## Findings", index)
        self.assertIn("STEP-08-placement/", index)
        self.assertNotIn("### Source before — frozen Evidence", index)
        self.assertIn("### Into Node — editable", finding)
        self.assertIn("### Source before — frozen Evidence", finding)
        self.assertIn("✏️ Editable finding controls", finding)
        self.assertNotIn("```text", finding)
        self.assertIn("\n> ", finding)
        self.assertIn('origin="owner-selected"', index)
        self.assertEqual(len(review.sources), 1)
        self.assertEqual(review.sources[0].origin, "owner-selected")

    def test_human_edits_round_trip_and_authoring_identity_stays_stable(self):
        prepared, workspace, source_root, package, proposal, first, _ = self.make_review(owner_source=False)
        first_id = first.items[0].authoring_id
        path = self.finding(workspace, proposal)
        text = path.read_text(encoding="utf-8")
        text = text.replace("## P-001 — Repository is the installation specification", "## P-001 — Canonical installation authority")
        text = text.replace("Decision: `pending`", "Decision: `accept`", 1)
        text = text.replace(
            "Statement: The repository is the installation specification.",
            "Statement: The repository is the canonical installation specification.",
            1,
        )
        path.write_text(text, encoding="utf-8")
        second = load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)
        self.assertEqual(second.items[0].authoring_id, first_id)
        self.assertEqual(second.items[0].title, "Canonical installation authority")
        self.assertEqual(second.items[0].decision, "accept")
        self.assertEqual(second.items[0].payload["statement"], "The repository is the canonical installation specification.")
        self.assertEqual(len(second.source_edits), 1)

    def test_existing_human_review_is_loaded_not_overwritten(self):
        prepared, workspace, source_root, package, proposal, first, _ = self.make_review(owner_source=False)
        path = self.finding(workspace, proposal)
        text = path.read_text(encoding="utf-8").replace("Decision: `pending`", "Decision: `reject`", 1)
        path.write_text(text, encoding="utf-8")
        loaded, created = create_or_load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)
        self.assertFalse(created)
        self.assertEqual(loaded.items[0].decision, "reject")
        self.assertEqual(loaded.items[0].authoring_id, first.items[0].authoring_id)
        self.assertIn("`reject`", workspace.placement_path.read_text(encoding="utf-8"))

    def test_changed_proposal_refuses_to_replace_existing_review(self):
        prepared, workspace, source_root, package, proposal, _, _ = self.make_review(owner_source=False)
        index = workspace.placement_path.read_text(encoding="utf-8")
        workspace.placement_path.write_text(index.replace(proposal.proposal_digest, "0" * 64), encoding="utf-8")
        with self.assertRaisesRegex(ContextCanonError, "new review path"):
            create_or_load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)

    def test_action_is_derived_from_kind_and_rendered_text_is_not_a_control(self):
        prepared, workspace, source_root, package, proposal, _, _ = self.make_review(owner_source=False)
        path = self.finding(workspace, proposal)
        text = path.read_text(encoding="utf-8").replace(
            "Derived action: `promote` (from Kind; do not edit)",
            "Derived action: `reference` (tampered display text)",
            1,
        )
        path.write_text(text, encoding="utf-8")
        loaded = load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)
        self.assertEqual(loaded.items[0].kind, "rule")
        self.assertEqual(loaded.items[0].action, "promote")

    def test_invalid_or_duplicate_stable_authoring_id_is_rejected_early(self):
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

    def test_source_after_is_visually_quoted_but_round_trips_as_plain_markdown(self):
        prepared, workspace, source_root, package, proposal, _, _ = self.make_review(owner_source=False)
        path = self.finding(workspace, proposal)
        text = path.read_text(encoding="utf-8")
        old = "> Installation authority is maintained in [AI Workstation Context](../CONTEXT.md)."
        new_plain = "Architecture starts here; maintained installation authority lives in [AI Workstation Context](../CONTEXT.md)."
        text = text.replace(old, "> " + new_plain, 1)
        text = text.replace("Source edit decision: `pending`", "Source edit decision: `accept`", 1)
        text = text.replace("Decision: `pending`", "Decision: `accept`", 1)
        path.write_text(text, encoding="utf-8")
        loaded = load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)
        self.assertEqual(loaded.source_edits[0].replacement, new_plain)
        self.assertEqual(loaded.source_edits[0].decision, "accept")

    def test_source_after_requires_single_quote_frame(self):
        prepared, workspace, source_root, package, proposal, _, _ = self.make_review(owner_source=False)
        path = self.finding(workspace, proposal)
        text = path.read_text(encoding="utf-8").replace(
            "> Installation authority is maintained in [AI Workstation Context](../CONTEXT.md).",
            "Installation authority is maintained in [AI Workstation Context](../CONTEXT.md).",
            1,
        )
        path.write_text(text, encoding="utf-8")
        with self.assertRaisesRegex(ContextCanonError, "single Markdown quote frame"):
            load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)

    def test_source_edit_cannot_be_accepted_when_linked_finding_is_rejected(self):
        prepared, workspace, source_root, package, proposal, _, _ = self.make_review(owner_source=False)
        path = self.finding(workspace, proposal)
        text = path.read_text(encoding="utf-8")
        text = text.replace("Decision: `pending`", "Decision: `reject`", 1)
        text = text.replace("Source edit decision: `pending`", "Source edit decision: `accept`", 1)
        path.write_text(text, encoding="utf-8")
        with self.assertRaisesRegex(ContextCanonError, "cannot be accepted until all linked promoted findings are accepted"):
            load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)

    def test_state_and_plan_are_rendered_as_into_node(self):
        from contextcanon.onboarding_placement_review import _render_payload
        for kind in ("state", "plan"):
            lines = _render_payload(kind, {"text": "Example", "wording_origin": "synthesized"})
            self.assertEqual(lines[0], "### Into Node — editable")

    def test_promote_without_llm_source_edit_gets_rejected_editable_human_fallback(self):
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
        path = self.finding(workspace, proposal)
        rendered = path.read_text(encoding="utf-8")
        self.assertIn("Optional source cleanup — independent from promotion", rendered)
        self.assertIn("Source edit decision: `reject`", rendered)
        replacement = "Architecture in one sentence. Maintained detail lives in [AI Workstation Context](../CONTEXT.md)."
        start_marker = f'<!-- cc:source-after id="{fallback.proposal_id}":start -->'
        end_marker = f'<!-- cc:source-after id="{fallback.proposal_id}":end -->'
        start = rendered.index(start_marker) + len(start_marker)
        end = rendered.index(end_marker, start)
        rendered = rendered[:start] + "\n> " + replacement + "\n" + rendered[end:]
        rendered = rendered.replace("Decision: `pending`", "Decision: `accept`", 1)
        rendered = rendered.replace("Source edit decision: `reject`", "Source edit decision: `accept`", 1)
        path.write_text(rendered, encoding="utf-8")
        loaded = load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)
        self.assertEqual(loaded.source_edits[0].decision, "accept")
        self.assertEqual(loaded.source_edits[0].replacement, replacement)

    def test_review_fallback_does_not_offer_cleanup_for_topic_resource(self):
        helper = placement_fixture.OnboardingPlacementTests()
        _, prepared, workspace, readme, architecture, source_root, package = helper.make_case()
        raw = helper.placement_dict(prepared, workspace, readme, architecture, package)
        raw["source_edits"] = []
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
        self.assertEqual(review.source_edits, ())
        combined = "\n".join(path.read_text(encoding="utf-8") for path in placement_review_directory(workspace.placement_path).glob("*.md"))
        self.assertNotIn("Optional source cleanup", combined)

    def test_multiple_source_edits_owned_by_one_finding_parse_independently(self):
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
        rendered = self.finding(workspace, proposal).read_text(encoding="utf-8")
        self.assertEqual(rendered.count("Source edit note:"), 2)
        loaded = load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)
        self.assertEqual([edit.proposal_id for edit in loaded.source_edits], ["E-001", "E-002"])
        self.assertEqual(
            [edit.replacement for edit in loaded.source_edits],
            [
                "Installation authority is maintained in [AI Workstation Context](../CONTEXT.md).",
                "# Architecture gateway",
            ],
        )

    def test_legacy_monolith_migrates_without_losing_human_decisions(self):
        prepared, workspace, source_root, package, proposal, specs = self.make_proposal(owner_source=False)
        legacy = render_placement_review(proposal, prepared.snapshot_root)
        legacy = legacy.replace("## P-001 — Repository is the installation specification", "## P-001 — Human edited title", 1)
        legacy = legacy.replace("Decision: `pending`", "Decision: `accept`", 1)
        legacy = legacy.replace("Source edit decision: `pending`", "Source edit decision: `accept`", 1)
        workspace.placement_path.write_text(legacy, encoding="utf-8")
        review, created = create_or_load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)
        self.assertFalse(created)
        self.assertEqual(review.items[0].title, "Human edited title")
        self.assertEqual(review.items[0].decision, "accept")
        self.assertEqual(review.source_edits[0].decision, "accept")
        self.assertTrue(placement_review_directory(workspace.placement_path).is_dir())
        self.assertIn("cc:placement-review-layout: split-v1", workspace.placement_path.read_text(encoding="utf-8"))

    def test_many_findings_scale_as_index_plus_one_sheet_each(self):
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
        review_gate, created = create_or_load_placement_review(
            workspace.placement_path, proposal, prepared.snapshot_root
        )
        self.assertTrue(created)
        self.assertEqual(len(review_gate.items), 40)
        review_dir = placement_review_directory(workspace.placement_path)
        self.assertEqual(len(list(review_dir.glob("*.md"))), 40)
        index = workspace.placement_path.read_text(encoding="utf-8")
        self.assertEqual(index.count("STEP-08-placement/P-"), 40)
        self.assertNotIn("### Source before — frozen Evidence", index)
        self.assertLess(len(index.splitlines()), 130)

    def test_missing_or_foreign_split_finding_is_rejected(self):
        prepared, workspace, source_root, package, proposal, _, _ = self.make_review(owner_source=False)
        first = self.finding(workspace, proposal)
        original = first.read_text(encoding="utf-8")
        first.unlink()
        with self.assertRaisesRegex(ContextCanonError, "missing finding files"):
            load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)
        first.write_text(original, encoding="utf-8")
        foreign = placement_review_directory(workspace.placement_path) / "notes.md"
        foreign.write_text("human stray file", encoding="utf-8")
        with self.assertRaisesRegex(ContextCanonError, "foreign files"):
            load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)


if __name__ == "__main__":
    unittest.main()
