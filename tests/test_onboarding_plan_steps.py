from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from contextcanon.onboarding_workspace import _exact_commands, open_onboarding_workspace


class OnboardingPlanStepsTests(unittest.TestCase):
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
                completed={1, 2, 3, 4},
            )
            self.assertIn("### STEP 05 — Reusable Contexts", text)
            self.assertIn("where reusable external Context Nodes can be found", text)
            self.assertIn("contextcanon onboard reusable-contexts", text)
            self.assertIn("### STEP 06 — Placement proposal", text)
            self.assertIn("STEP-06a-placement-instruction.md", text)
            self.assertIn("STEP-08-placement.md", text)
            self.assertIn("STEP-10-placement-followup.md", text)
            self.assertNotIn("--catalog-package", text)
            self.assertNotIn("--owner-source", text)
            self.assertNotIn("opaque-id", text)
            self.assertIn("- [x] **Done**", text)
            self.assertIn("- [ ] **Done**", text)
