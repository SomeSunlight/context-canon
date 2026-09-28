from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from contextcanon.onboarding_workspace import _exact_commands, open_onboarding_workspace


class OnboardingPlanStepsTests(unittest.TestCase):
    def test_prefreeze_plan_warns_to_finish_moves_before_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".git").mkdir()
            workspace = open_onboarding_workspace(root, create=True)
            text = workspace.plan_path.read_text(encoding="utf-8")

            self.assertIn("> [!WARNING]", text)
            self.assertIn("**Finish renaming and moving project material now.**", text)
            self.assertIn("STEP 03 freezes repository-relative paths into immutable Evidence", text)
            self.assertIn("reset from STEP 03", text)
            self.assertIn("rerun the inventory", text)
            self.assertIn("freeze a new Evidence snapshot", text)
            self.assertLess(text.index("> [!WARNING]"), text.index("### STEP 02 — Review file inventory"))

    def test_plan_keeps_checkbox_explanation_and_command_together(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".git").mkdir()
            snapshot = root / ".context" / "onboarding" / ("a" * 64)
            snapshot.mkdir(parents=True)
            workspace = open_onboarding_workspace(snapshot, create=True)
            text = _exact_commands(
                workspace,
                snapshot,
                ("/legacy/catalog/package",),
                ("N-001=opaque-id",),
                completed={1, 2, 3, 4, 5, 6},
            )
            self.assertIn("### STEP 07 — Reusable Contexts", text)
            self.assertIn("already-curated reusable Context should apply here", text)
            self.assertIn("contextcanon onboard reusable-contexts", text)
            self.assertIn("### STEP 08 — Placement proposal", text)
            self.assertIn("STEP-08a-placement-instruction.md", text)
            self.assertIn("STEP-10-placement.md", text)
            self.assertIn("STEP-12-placement-followup.md", text)
            self.assertNotIn("--catalog-package", text)
            self.assertNotIn("--owner-source", text)
            self.assertNotIn("opaque-id", text)
            self.assertIn("- [x] **Done**", text)
            self.assertIn("- [ ] **Done**", text)
