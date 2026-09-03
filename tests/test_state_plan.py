from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from contextcanon.compiler import Compiler
from contextcanon.parser import parse_node


class StatePlanTests(unittest.TestCase):
    def _write_source(self, root: Path, state: str, plan: str) -> None:
        (root / "CONTEXT.src.md").write_text(
            "# Demo Project — Local Context Source\n"
            '<!-- ctx:node id="12345678-1234-4234-8234-123456789abc" version="0.1.0" -->\n\n'
            "## Overview\n\n"
            "Stable demo orientation.\n\n"
            "## State\n\n"
            f"- {state}\n\n"
            "## Plan\n\n"
            f"- {plan}\n",
            encoding="utf-8",
        )

    def test_state_and_plan_are_local_official_content(self):
        repo = Path(tempfile.mkdtemp())
        (repo / ".git").mkdir()
        self._write_source(repo, "Current migration is active.", "Finish onboarding before feature work.")

        parsed = parse_node(repo, repo)
        self.assertEqual(parsed.state, "- Current migration is active.")
        self.assertEqual(parsed.plan, "- Finish onboarding before feature work.")

        first = Compiler(repo).compile(repo)
        self.assertIn("## Local State\n\n- Current migration is active.", first.official_markdown)
        self.assertIn("## Local Plan\n\n- Finish onboarding before feature work.", first.official_markdown)
        self.assertIn('state: "- Current migration is active."', first.machine_yaml)
        self.assertIn('plan: "- Finish onboarding before feature work."', first.machine_yaml)

        normalized = first.normalized_digest
        package = first.package_digest
        self._write_source(repo, "Current migration is complete.", "Start feature work.")
        second = Compiler(repo).compile(repo)
        self.assertEqual(second.normalized_digest, normalized)
        self.assertNotEqual(second.package_digest, package)


if __name__ == "__main__":
    unittest.main()
