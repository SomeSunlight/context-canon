from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class OnboardingWalkthroughCurrentTests(unittest.TestCase):
    def test_walkthrough_matches_human_first_ten_step_flow(self) -> None:
        text = (ROOT / "docs" / "onboarding.md").read_text(encoding="utf-8")
        self.assertIn("## 5. Select reusable Contexts", text)
        self.assertIn("STEP-05-reusable-contexts.md", text)
        self.assertIn("sparse relationships", text)
        self.assertIn("why this whole reusable Context", text)
        self.assertIn("## 6. Generate the content-placement assignment", text)
        self.assertIn("STEP-06a-placement-instruction.md", text)
        self.assertIn("## 8. Review and revalidate `STEP-08-placement.md`", text)
        self.assertIn("STEP-09-placement-preview.md", text)
        self.assertIn("STEP-10-placement-followup.md", text)
        self.assertIn("PLAN is orchestration only", text)
        current = text.split("## Legacy single-pass first adoption", 1)[0]
        self.assertNotIn("--owner-source", current)
        self.assertNotIn("--catalog-package", current)
        self.assertNotIn("STEP-07-placement.md", current)
        self.assertNotIn("STEP-05a-placement-instruction.md", current)


if __name__ == "__main__":
    unittest.main()
