from pathlib import Path

root = Path(__file__).resolve().parents[1]

path = root / "src/contextcanon/cli.py"
text = path.read_text(encoding="utf-8")
wrong = '''                print(f"Source edits: {len(proposal.source_edits)}")
                    print(f"Source reuses: {len(proposal.source_reuses)}")'''
if wrong not in text:
    raise RuntimeError("expected misplaced Source edits output not found")
text = text.replace(wrong, '''                print(f"Source reuses: {len(proposal.source_reuses)}")''', 1)
anchor = '''                    print(f"Placement items: {len(proposal.items)}")
                    print(f"Source reuses: {len(proposal.source_reuses)}")'''
if anchor not in text:
    raise RuntimeError("placement validation output anchor not found")
text = text.replace(anchor, '''                    print(f"Placement items: {len(proposal.items)}")
                    print(f"Source edits: {len(proposal.source_edits)}")
                    print(f"Source reuses: {len(proposal.source_reuses)}")''', 1)
path.write_text(text, encoding="utf-8", newline="\n")

path = root / "tests/test_onboarding_placement.py"
text = path.read_text(encoding="utf-8")
replacements = {
    '        self.assertIn("Overview is different", instruction.text)':
        '        self.assertIn("Overview is a condensation task", instruction.text)',
    '        self.assertIn("split them into separate findings", instruction.text)':
        '        self.assertIn("Consolidate closely related overview statements", instruction.text)',
    '        self.assertIn("use it verbatim", instruction.text)':
        '        self.assertIn("move with minimal wording change", instruction.text)',
}
for old, new in replacements.items():
    if old not in text:
        raise RuntimeError(f"legacy instruction assertion not found: {old}")
    text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8", newline="\n")
