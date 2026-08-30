from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from contextcanon.onboarding_placement import load_onboarding_placement_proposal
from contextcanon.onboarding_placement_review import create_or_load_placement_review, load_placement_review
from contextcanon.parser import ContextCanonError
import tests.test_onboarding_placement as placement_fixture


class EditablePlacementReviewTests(unittest.TestCase):
    def make_review(self, *, owner_source: bool = True):
        helper = placement_fixture.OnboardingPlacementTests()
        _, prepared, workspace, readme, architecture, source_root, package = helper.make_case()
        raw = helper.placement_dict(prepared, workspace, readme, architecture, package)
        if owner_source:
            # Exercise explicit owner selection independently from an LLM Source match.
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
        review, created = create_or_load_placement_review(
            workspace.placement_path,
            proposal,
            prepared.snapshot_root,
            owner_source_specs=specs,
        )
        return prepared, workspace, source_root, package, proposal, review, created

    def test_review_is_destination_first_editable_and_owner_source_is_distinct(self):
        prepared, workspace, source_root, package, proposal, review, created = self.make_review()
        self.assertTrue(created)
        text = workspace.placement_path.read_text(encoding="utf-8")
        item = text.index("## P-001")
        destination = text.index("Destination:", item)
        decision = text.index("Decision:", item)
        rationale = text.index("### Proposal rationale", item)
        self.assertLess(destination, decision)
        self.assertLess(decision, rationale)
        self.assertIn("### Maintained meaning", text)
        self.assertIn('origin="owner-selected"', text)
        self.assertEqual(len(review.sources), 1)
        self.assertEqual(review.sources[0].origin, "owner-selected")

    def test_human_edits_round_trip_and_authoring_identity_stays_stable(self):
        prepared, workspace, source_root, package, proposal, first, _ = self.make_review(owner_source=False)
        first_id = first.items[0].authoring_id
        text = workspace.placement_path.read_text(encoding="utf-8")
        text = text.replace("## P-001 — Repository is the installation specification", "## P-001 — Canonical installation authority")
        text = text.replace("Decision: `pending`", "Decision: `accept`", 1)
        text = text.replace(
            "Statement: The repository is the installation specification.",
            "Statement: The repository is the canonical installation specification.",
            1,
        )
        workspace.placement_path.write_text(text, encoding="utf-8")
        second = load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)
        self.assertEqual(second.items[0].authoring_id, first_id)
        self.assertEqual(second.items[0].title, "Canonical installation authority")
        self.assertEqual(second.items[0].decision, "accept")
        self.assertEqual(
            second.items[0].payload["statement"],
            "The repository is the canonical installation specification.",
        )

    def test_existing_human_review_is_loaded_not_overwritten(self):
        prepared, workspace, source_root, package, proposal, first, _ = self.make_review(owner_source=False)
        text = workspace.placement_path.read_text(encoding="utf-8").replace("Decision: `pending`", "Decision: `reject`", 1)
        workspace.placement_path.write_text(text, encoding="utf-8")
        loaded, created = create_or_load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)
        self.assertFalse(created)
        self.assertEqual(loaded.items[0].decision, "reject")
        self.assertEqual(loaded.items[0].authoring_id, first.items[0].authoring_id)

    def test_changed_proposal_refuses_to_replace_existing_review(self):
        prepared, workspace, source_root, package, proposal, _, _ = self.make_review(owner_source=False)
        text = workspace.placement_path.read_text(encoding="utf-8")
        workspace.placement_path.write_text(text.replace(proposal.proposal_digest, "0" * 64), encoding="utf-8")
        with self.assertRaisesRegex(ContextCanonError, "new review path"):
            create_or_load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)

    def test_invalid_human_rule_reference_is_rejected(self):
        prepared, workspace, source_root, package, proposal, _, _ = self.make_review(owner_source=False)
        text = workspace.placement_path.read_text(encoding="utf-8").replace("Action: `promote`", "Action: `reference`", 1)
        workspace.placement_path.write_text(text, encoding="utf-8")
        with self.assertRaisesRegex(ContextCanonError, "Kind rule must use Action promote"):
            load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)


if __name__ == "__main__":
    unittest.main()
