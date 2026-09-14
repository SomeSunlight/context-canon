from pathlib import Path

path = Path("tests/test_onboarding_placement.py")
text = path.read_text(encoding="utf-8")
old = '''        review_text = workspace.placement_path.read_text(encoding="utf-8")
        self.assertIn("Wording: `exact`", review_text)
        self.assertIn("### Into Node — editable", review_text)
        self.assertIn("### Source before — frozen Evidence", review_text)
        self.assertIn("### Source after promotion", review_text)
'''
new = '''        index_text = workspace.placement_path.read_text(encoding="utf-8")
        self.assertIn("cc:placement-review-layout: split-v1", index_text)
        finding_path = next(workspace.placement_dir_path.glob("P-001-*.md"))
        finding_text = finding_path.read_text(encoding="utf-8")
        self.assertIn("Wording: `exact`", finding_text)
        self.assertIn("### Into Node — editable", finding_text)
        self.assertIn("### Source before — frozen Evidence", finding_text)
        self.assertIn("### Source after promotion", finding_text)
        self.assertNotIn("```text", finding_text)
'''
if text.count(old) != 1:
    raise SystemExit(f"placement CLI assertion block count: {text.count(old)}")
path.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")
print("Issue 35 follow-up patch applied")
