from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise SystemExit(f"expected one match in {path}, found {text.count(old)}")
    target.write_text(text.replace(old, new), encoding="utf-8")


def append_once(path: str, marker: str, addition: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    if marker in text:
        return
    target.write_text(text.rstrip() + "\n\n" + addition.strip() + "\n", encoding="utf-8")


def apply() -> None:
    replace_once(
        "src/contextcanon/onboarding_placement.py",
        '''def _replacement(value: object, label: str) -> str:\n    if not isinstance(value, str):\n        raise _error(f"{label} must be a string")\n    if "\\x00" in value:\n        raise _error(f"{label} contains an unsupported NUL character")\n    return value.replace("\\r\\n", "\\n").replace("\\r", "\\n").strip("\\n")\n''',
        '''def _replacement(value: object, label: str) -> str:\n    if not isinstance(value, str):\n        raise _error(f"{label} must be a string")\n    if "\\x00" in value:\n        raise _error(f"{label} contains an unsupported NUL character")\n    return value.replace("\\r\\n", "\\n").replace("\\r", "\\n").strip("\\n")\n\n\ndef _nonblank_line_numbers(text: str, start_line: int, end_line: int) -> set[int]:\n    lines = text.splitlines()\n    return {\n        line_number\n        for line_number in range(start_line, end_line + 1)\n        if lines[line_number - 1].strip()\n    }\n''',
    )
    replace_once(
        "src/contextcanon/onboarding_placement.py",
        '''        if not set(range(start, end + 1)).issubset(covered):\n            raise _error(f"{label} range is not fully covered by Evidence of its linked promoted items")\n''',
        '''        evidence_text = (snapshot.root / "evidence" / edit_path).read_text(encoding="utf-8")\n        required_lines = _nonblank_line_numbers(evidence_text, start, end)\n        missing_lines = sorted(required_lines - covered)\n        if missing_lines:\n            missing = ", ".join(str(line) for line in missing_lines)\n            raise _error(\n                f"{label} non-blank range lines are not fully covered by Evidence of its linked promoted items; "\n                f"missing lines: {missing}"\n            )\n''',
    )
    replace_once(
        "src/contextcanon/onboarding_placement_instruction.py",
        '''        "`source_edits` is the proposed A → A′ side of promotion. Use only mutable `.md` Evidence that is not listed as fixed Markdown. Every edited line must be covered by Evidence cited by the linked promoted items; linked IDs must all be `promote` items and must not be `unresolved` findings, because an unanswered question cannot justify deleting uncertain source meaning. One source range may be linked to several findings, but source edits in one file must never overlap. `replacement` may be empty only when removing the range entirely is clearly better than leaving orientation. If no promoted mutable prose needs cleanup, return an empty array.",\n''',
        '''        "`source_edits` is the proposed A → A′ side of promotion. Use only mutable `.md` Evidence that is not listed as fixed Markdown. Every **non-blank** edited line must be covered by Evidence cited by the linked promoted items; blank Markdown separator lines may sit inside one contiguous edit range without their own Evidence citation. Linked IDs must all be `promote` items and must not be `unresolved` findings, because an unanswered question cannot justify deleting uncertain source meaning. One source range may be linked to several findings, but source edits in one file must never overlap. `replacement` may be empty only when removing the range entirely is clearly better than leaving orientation. If no promoted mutable prose needs cleanup, return an empty array.",\n''',
    )
    replace_once(
        "tests/test_onboarding_placement.py",
        '''from contextcanon.onboarding_placement import PLACEMENT_PROPOSAL_SCHEMA, load_onboarding_placement_proposal, render_placement_review\n''',
        '''from contextcanon.onboarding_placement import (\n    PLACEMENT_PROPOSAL_SCHEMA,\n    _nonblank_line_numbers,\n    load_onboarding_placement_proposal,\n    render_placement_review,\n)\n''',
    )
    replace_once(
        "tests/test_onboarding_placement.py",
        '''        self.assertIn("Zero semantic loss per Source edit", instruction.text)\n''',
        '''        self.assertIn("Zero semantic loss per Source edit", instruction.text)\n        self.assertIn("blank Markdown separator lines", instruction.text)\n''',
    )
    replace_once(
        "tests/test_onboarding_placement.py",
        '''    def test_placement_validates_exact_evidence_structure_and_catalog(self):\n''',
        '''    def test_source_edit_coverage_ignores_only_blank_separator_lines(self):\n        self.assertEqual(_nonblank_line_numbers("table\\n\\nrule\\n", 1, 3), {1, 3})\n\n        _, prepared, workspace, readme, architecture, source_root, package = self.make_case()\n        raw = self.placement_dict(prepared, workspace, readme, architecture, package)\n        raw["source_edits"][0]["start_line"] = 1\n        workspace.placement_proposal_path.write_text(json.dumps(raw), encoding="utf-8")\n        with self.assertRaisesRegex(ContextCanonError, "missing lines: 1"):\n            load_onboarding_placement_proposal(\n                workspace.placement_proposal_path,\n                prepared.snapshot_root,\n                workspace.structure_proposal_path,\n                workspace.structure_path,\n                catalog_package_roots=[source_root],\n            )\n\n    def test_placement_validates_exact_evidence_structure_and_catalog(self):\n''',
    )


def finalize() -> None:
    append_once(
        "PLAN.md",
        "#### Block O — allow blank Markdown separators inside reviewed Source edits",
        '''#### Block O — allow blank Markdown separators inside reviewed Source edits\n\nPurpose: fix the live `ai-workstation` Step-6 validation failure where one coherent `docs/architecture.md` Source After edit spans a blank separator line between two Evidence-backed semantic blocks.\n\n- [x] Keep Source-edit provenance strict for every non-blank line while allowing blank/whitespace-only Markdown separators inside a contiguous reviewed edit range.\n- [x] Align the placement instruction with that deterministic rule so the LLM is not asked to invent semantic Evidence for formatting-only blank lines.\n- [x] Add a regression proving blank separators are ignored and a substantive uncovered line still fails with its exact missing line number.\n- [x] Run the focused placement test, complete deterministic suite, build/check and diff hygiene, then remove the temporary verification harness.\n\nBlank-separator checkpoint: the live proposal was semantically sound. Its architecture edit covers lines 3–13 while linked findings cover the table (3–10) and source-of-truth statement (12–13); line 11 is only the Markdown separator between them. Validation now requires provenance for every non-blank edited line, not for formatting-only blank separators, while substantive uncovered lines remain a hard error.''',
    )
    append_once(
        "STATE.md",
        "## Latest Source-edit blank-separator validation correction",
        '''## Latest Source-edit blank-separator validation correction\n\nThe next real `ai-workstation` placement validation exposed an intentionally narrow mismatch between semantic provenance and contiguous Markdown editing. A reviewed Source After edit may need to span a blank separator line between two Evidence-backed blocks; requiring a promoted finding to cite that empty line adds no semantic safety and rejected an otherwise sound proposal. Placement validation now requires linked promoted Evidence to cover every non-blank line in the edited frozen range while allowing blank/whitespace-only separators. Content-bearing headings, table rows, comments and prose remain covered or validation fails with the exact missing line numbers.''',
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2 or sys.argv[1] not in {"apply", "finalize"}:
        raise SystemExit("usage: _blank_source_separator_fix.py apply|finalize")
    globals()[sys.argv[1]]()
