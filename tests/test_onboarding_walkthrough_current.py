from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class OnboardingWalkthroughCurrentTests(unittest.TestCase):
    def test_walkthrough_matches_reviewed_twelve_step_flow(self) -> None:
        text = (ROOT / "docs" / "onboarding.md").read_text(encoding="utf-8")
        self.assertIn("## 0. Install and create the operator workspace", text)
        self.assertIn("contextcanon onboard init .", text)
        self.assertIn("STEP-02-inventory-guide.md", text)
        self.assertIn("## 1. Tidy before durable references", text)
        self.assertIn("## 2. Inventory and review the project files", text)
        self.assertIn("STEP-02-inventory.csv", text)
        self.assertIn("## 3. Freeze the reviewed Evidence", text)
        self.assertIn("## 7. Select reusable Contexts", text)
        self.assertIn("STEP-07-reusable-contexts.md", text)
        self.assertIn("sparse relationships", text)
        self.assertIn("why this whole reusable Context", text)
        self.assertIn("## 8. Generate the content-placement assignment", text)
        self.assertIn("STEP-08a-placement-instruction.md", text)
        self.assertIn("## 10. Review and revalidate `STEP-10-placement.md`", text)
        self.assertIn("STEP-11-placement-preview.md", text)
        self.assertIn("STEP-12-placement-followup.md", text)
        self.assertIn("PLAN is orchestration only", text)
        current = text.split("## Legacy single-pass first adoption", 1)[0]
        self.assertNotIn("--owner-source", current)
        self.assertNotIn("--catalog-package", current)
        self.assertNotIn("STEP-07-placement.md", current)
        self.assertNotIn("STEP-05a-placement-instruction.md", current)


    def test_root_readme_gets_new_user_into_generated_plan_without_reconstructing_workflow(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        onboarding = text.split("## Bring an existing project aboard", 1)[1].split("## Maintain an onboarded project", 1)[0]

        self.assertIn("uv tool install git+https://github.com/SomeSunlight/context-canon.git", onboarding)
        self.assertIn("contextcanon --version", onboarding)
        self.assertIn("contextcanon onboard init .", onboarding)
        self.assertIn("contextcanon-onboarding/PLAN.md", onboarding)
        self.assertIn("STEP-02-inventory-guide.md", onboarding)
        self.assertNotIn("contextcanon onboard inventory .", onboarding)
        self.assertNotIn("--inventory contextcanon-onboarding/STEP-02-inventory.csv", onboarding)
        self.assertNotIn("contextcanon onboard structure-instruction", onboarding)


if __name__ == "__main__":
    unittest.main()
