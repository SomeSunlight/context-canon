from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from contextcanon.onboarding_placement import _read_json, _validate_authority_path
from contextcanon.onboarding_placement_instruction import _render_contract
from contextcanon.parser import ContextCanonError


class PlacementValidationUXTests(unittest.TestCase):
    def test_invalid_json_reports_line_column_source_and_caret(self):
        root = Path(tempfile.mkdtemp())
        proposal = root / "placement-proposal.json"
        bad_line = '  "statement": "do not perform unconfigured or "magic" rewrites"'
        proposal.write_text('{\n' + bad_line + '\n}\n', encoding="utf-8")

        with self.assertRaises(ContextCanonError) as raised:
            _read_json(proposal)

        message = str(raised.exception)
        self.assertIn("Expecting ',' delimiter at line 2, column", message)
        self.assertIn("(char ", message)
        self.assertIn(bad_line, message)
        self.assertIn("^", message)

    def test_non_markdown_technical_authority_does_not_need_fixed_markdown(self):
        _validate_authority_path("pyproject.toml", set(), "items[5]")
        _validate_authority_path(".editorconfig", set(), "items[7]")

    def test_markdown_authority_still_requires_owner_accepted_fixed_policy(self):
        _validate_authority_path("policy.md", {"policy.md"}, "items[0]")

        with self.assertRaises(ContextCanonError) as raised:
            _validate_authority_path("README.md", set(), "items[1]")

        self.assertIn("authority Markdown path 'README.md' is not marked fixed", str(raised.exception))

    def test_placement_contract_explains_authority_boundary_and_json_escaping(self):
        text = "\n".join(_render_contract("a" * 64, "b" * 64))

        self.assertIn("frozen non-Markdown technical Evidence", text)
        self.assertIn("Markdown authority paths must already be marked fixed", text)
        self.assertIn("JSON strings must escape embedded double quotes", text)
        self.assertIn("pyproject.toml", text)


if __name__ == "__main__":
    unittest.main()
