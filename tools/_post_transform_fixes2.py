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

path = root / "src/contextcanon/onboarding_placement_instruction.py"
text = path.read_text(encoding="utf-8")
old = '2. The primary question is **where should this meaning be maintained from now on?** Minimize future redundancy. Every durable meaning should have one canonical maintenance surface. Do not preserve a poor current file boundary merely because the text happens to live there.'
new = '2. The primary question is **where should this meaning be maintained from now on?** Minimize future redundancy. Every durable meaning should have one canonical maintenance surface: promotion must leave a single canonical maintenance surface for that meaning. Do not preserve a poor current file boundary merely because the text happens to live there.'
if old not in text:
    raise RuntimeError("canonical ownership instruction anchor not found")
text = text.replace(old, new, 1)
old = '5. When promoted meaning came from mutable Markdown and leaving the original full prose would create duplicate maintenance, propose a `source_edits` entry in this same semantic pass. It names one exact frozen source range and the promoted item IDs that justify replacing it. The replacement is **orientation, not a second canonical copy**: keep it short, plain and useful to a first-time reader, and point to the owning `CONTEXT.md` when that helps. When the meaning is unambiguous, rewrite freely for readability and a light human touch is welcome; when anything is uncertain, stay close to the original wording and do not invent. Do not create a source edit merely to change style.'
new = '5. When promoted meaning came from mutable Markdown and leaving the original full prose would create duplicate maintenance, propose a `source_edits` entry in this same semantic pass. It names one exact frozen source range and the promoted item IDs that justify replacing it. The replacement is **orientation, not a second canonical copy**: prefer concise human orientation plus a link/reference to the owning `CONTEXT.md` when that helps. When the meaning is unambiguous, rewrite freely for readability and a light human touch is welcome; when anything is uncertain, stay close to the original wording and do not invent. If no safe Source After edit is proposed or accepted, a temporary duplicate may exist during migration, but it remains migration debt. Do not plan to maintain the same full rule or explanation in both places. Do not create a source edit merely to change style.'
if old not in text:
    raise RuntimeError("source-after contract instruction anchor not found")
text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8", newline="\n")

path = root / "tests/test_onboarding_placement.py"
text = path.read_text(encoding="utf-8")
replacements = {
    '        self.assertIn("Overview is different", instruction.text)':
        '        self.assertIn("Overview is a condensation task", instruction.text)',
    '        self.assertIn("use it verbatim", instruction.text)':
        '        self.assertIn("move with minimal wording change", instruction.text)',
}
for old, new in replacements.items():
    if old not in text:
        raise RuntimeError(f"legacy instruction assertion not found: {old}")
    text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8", newline="\n")
