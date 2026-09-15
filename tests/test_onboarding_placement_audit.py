from __future__ import annotations

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
from contextcanon.onboarding_placement_split_review import placement_finding_path, placement_source_edit_path
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

    def accept_first_finding_and_edit(self, workspace, proposal, review):
        finding_path = placement_finding_path(workspace.placement_path, proposal.items[0])
        text = finding_path.read_text(encoding="utf-8").replace(
            "- Decision: `pending`", "- Decision: `accept`", 1
        )
        finding_path.write_text(text, encoding="utf-8")
        edit_path = placement_source_edit_path(workspace.placement_path, review.source_edits[0])
        text = edit_path.read_text(encoding="utf-8").replace(
            "- Source edit decision: `pending`", "- Source edit decision: `accept`", 1
        )
        edit_path.write_text(text, encoding="utf-8")

    def test_source_first_audit_groups_exact_range_and_links_e_sheet(self):
        prepared, workspace, _, proposal, review = self.make_review()
        self.accept_first_finding_and_edit(workspace, proposal, review)
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
        self.assertIn("STEP-08-source-edits/E-001-", audit)
        self.assertNotIn("#source-edit-e-001", audit)

    def test_rejected_source_edit_shows_unchanged_effective_after_and_candidate(self):
        prepared, workspace, _, proposal, review = self.make_review()
        edit_path = placement_source_edit_path(workspace.placement_path, review.source_edits[0])
        text = edit_path.read_text(encoding="utf-8").replace(
            "- Source edit decision: `pending`", "- Source edit decision: `reject`", 1
        )
        edit_path.write_text(text, encoding="utf-8")
        review = load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)

        audit = render_placement_source_audit(proposal, review, prepared.snapshot_root)
        self.assertIn("Effective after — unchanged because this Source edit is rejected", audit)
        self.assertIn("Proposed replacement — not applied", audit)
        self.assertGreaterEqual(audit.count("The repository is the installation specification."), 2)

    def test_cli_placement_review_refreshes_index_and_read_only_audit(self):
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
        first_audit = workspace.placement_audit_path.read_text(encoding="utf-8")
        first_index = workspace.placement_path.read_text(encoding="utf-8")
        self.assertIn("Generated, read-only view", first_audit)
        self.assertIn("`pending`", first_index)

        proposal = load_onboarding_placement_proposal(
            workspace.placement_proposal_path,
            prepared.snapshot_root,
            workspace.structure_proposal_path,
            workspace.structure_path,
            catalog_package_roots=[source_root],
        )
        review = load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)
        self.accept_first_finding_and_edit(workspace, proposal, review)

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            result = main([
                "onboard", "placement-review", str(prepared.snapshot_root),
                "--catalog-package", str(source_root),
            ])
        self.assertEqual(result, 0)
        refreshed_audit = workspace.placement_audit_path.read_text(encoding="utf-8")
        refreshed_index = workspace.placement_path.read_text(encoding="utf-8")
        self.assertNotEqual(first_audit, refreshed_audit)
        self.assertIn("Source edit decision: `accept`", refreshed_audit)
        self.assertIn("Effective after — accepted replacement", refreshed_audit)
        self.assertIn("`accept`", refreshed_index)
        self.assertIn("Source audit:", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
