from pathlib import Path

# Correct only the temporary regression harness; product behavior is unchanged.
path = Path('.github/scripts/apply_issue27_windows_resume_fix.py')
text = path.read_text(encoding='utf-8')
old = '''            self.assertIn('Apply this Parent update to Child "Grand"?', text)\n            self.assertEqual(prompt.call_count, 1)'''
new = '''            self.assertEqual(prompt.call_count, 1)\n            self.assertIn('Apply this Parent update to Child "Grand"?', prompt.call_args.args[0])'''
if text.count(old) != 1:
    raise SystemExit('expected one resume prompt assertion block')
path.write_text(text.replace(old, new, 1), encoding='utf-8')
