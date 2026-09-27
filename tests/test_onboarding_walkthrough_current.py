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
        self.assertIn("existing project deliveries", text)
        self.assertIn("[coming soon] interpret raw/ambiguous Evidence", text)
        self.assertIn("STEP-02-inventory.csv", text)
        self.assertIn("## 3. Freeze the reviewed Evidence", text)
        self.assertIn("## 7. Select reusable Contexts", text)
        self.assertIn("STEP-07-reusable-contexts.md", text)
        self.assertIn("sparse relationships", text)
        self.assertIn("why this whole reusable Context", text)
        self.assertIn("## 8. Generate the content-placement assignment", text)
        self.assertIn("STEP-08a-placement-instruction.md", text)
        self.assertIn("handoffs/STEP-04-structure/", text)
        self.assertIn("handoffs/STEP-08-placement/", text)
        self.assertIn(".contextcanon-handoff/PLAN.md", text)
        self.assertIn("contextcanon onboard handoff-import", text)
        self.assertIn("## 10. Review and revalidate `STEP-10-placement.md`", text)
        self.assertIn("STEP-11-placement-preview.md", text)
        self.assertIn("STEP-12-placement-followup.md", text)
        self.assertIn("PLAN is orchestration only", text)
        current = text.split("## Legacy single-pass first adoption", 1)[0]
        self.assertNotIn("--owner-source", current)
        self.assertNotIn("--catalog-package", current)
        self.assertNotIn("STEP-07-placement.md", current)
        self.assertNotIn("STEP-05a-placement-instruction.md", current)


    def test_onboarding_docs_separate_walkthrough_commands_and_framework_design(self) -> None:
        walkthrough = (ROOT / "docs" / "onboarding.md").read_text(encoding="utf-8")
        cli = (ROOT / "docs" / "onboarding-cli.md").read_text(encoding="utf-8")
        cli_index = (ROOT / "docs" / "cli.md").read_text(encoding="utf-8")
        docs_index = (ROOT / "docs" / "README.md").read_text(encoding="utf-8")
        framework_source = (ROOT / "nodes" / "internal" / "framework-development" / "CONTEXT.src.md").read_text(encoding="utf-8")
        design = (ROOT / "nodes" / "internal" / "framework-development" / "docs" / "onboarding-design.md").read_text(encoding="utf-8")

        self.assertIn("existing project deliveries", walkthrough)
        self.assertIn("human triage: source / interpret / lookup / ignore", walkthrough)
        self.assertIn("[coming soon] interpret raw/ambiguous Evidence", walkthrough)
        self.assertIn("[Onboarding CLI reference](onboarding-cli.md)", walkthrough)
        self.assertIn("exact reusable Context packages from STEP 07", walkthrough)
        self.assertNotIn("exact reusable Context packages from Step 5", walkthrough)
        self.assertNotIn("not established in Step 5", walkthrough)

        self.assertIn("contextcanon onboard reset . --from <STEP>", cli)
        self.assertIn("contextcanon onboard handoff-import", cli)
        self.assertIn("contextcanon onboard handoff .context/onboarding/<evidence-digest> --step 4", cli)
        self.assertIn("`--from 1`", cli)
        self.assertIn("`--from 3`", cli)
        self.assertIn("[Onboarding CLI reference](onboarding-cli.md)", cli_index)
        self.assertIn("onboarding-cli.md", docs_index)
        self.assertNotIn("onboarding-reference.md", docs_index)
        self.assertFalse((ROOT / "docs" / "onboarding-reference.md").exists())

        self.assertIn("Resource: `docs/onboarding-design.md`", framework_source)
        self.assertNotIn("Resource: `docs/onboarding-reference.md`", framework_source)
        self.assertTrue((ROOT / "nodes" / "internal" / "framework-development" / "docs" / "onboarding-design.md").is_file())
        self.assertFalse((ROOT / "nodes" / "internal" / "framework-development" / "docs" / "onboarding-reference.md").exists())
        self.assertIn("framework-development document", design)
        self.assertIn("STEP 12  explicit transactional publication", design)
        self.assertIn("Legacy single-pass semantic instruction contract", design)
        self.assertNotIn("Step-9 reset journals", design)
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
