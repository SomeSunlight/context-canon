from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from contextcanon.compiler import Compiler


DEVELOPMENT_WORKFLOW_ID = "c4c94726-3cc7-4df6-b779-72bbf9c06f40"
FOUNDATION_RULE_ID = "CC-001"


class DevelopmentWorkflowProviderTests(unittest.TestCase):
    def test_github_provider_composes_workflow_without_foundation(self):
        node = Compiler(ROOT).compile(ROOT / "nodes/library/github")

        inherited_ids = {rule.id for rule in node.inherited_rules}
        local_ids = {rule.id for rule in node.local_rules}

        self.assertIn("CCW-010", inherited_ids)
        self.assertNotIn(FOUNDATION_RULE_ID, inherited_ids)
        self.assertEqual(local_ids, {"GH-001"})
        self.assertIn("Rules from Development Workflow", node.official_markdown)
        self.assertIn("GitHub repository", node.official_markdown)

    def test_github_local_provider_keeps_workflow_and_visible_issue_contract(self):
        node = Compiler(ROOT).compile(ROOT / "nodes/library/github-local")

        inherited_ids = {rule.id for rule in node.inherited_rules}
        local_ids = {rule.id for rule in node.local_rules}
        topic_ids = {topic.id for topic in node.local_topics}

        self.assertIn("CCW-010", inherited_ids)
        self.assertNotIn(FOUNDATION_RULE_ID, inherited_ids)
        self.assertEqual(local_ids, {"GHL-001", "GHL-002", "GHL-003"})
        self.assertEqual(topic_ids, {"GHL-TOPIC-PROVIDER"})
        self.assertIn("issues/", node.official_markdown)
        self.assertTrue(
            any(path.endswith("nodes/library/github-local/docs/provider.md") for path in node.resources),
            sorted(node.resources),
        )


if __name__ == "__main__":
    unittest.main()
