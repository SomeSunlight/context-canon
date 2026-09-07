from pathlib import Path

path = Path(".contextcanon-issue24-legacy-migration.py")
text = path.read_text(encoding="utf-8")
old_start = "new_test = '''    def test_guided_update_migrates_legacy_git_discovery_without_persisting_one_off_ref(self):"
new_start = 'new_test = """    def test_guided_update_migrates_legacy_git_discovery_without_persisting_one_off_ref(self):'
old_end = "\n'''\ntest_path.write_text(test_text.replace(anchor, new_test + anchor, 1), encoding=\"utf-8\")"
new_end = '\n"""\ntest_path.write_text(test_text.replace(anchor, new_test + anchor, 1), encoding="utf-8")'
if text.count(old_start) != 1 or text.count(old_end) != 1:
    raise RuntimeError("Issue 24 builder delimiter target missing")
text = text.replace(old_start, new_start, 1).replace(old_end, new_end, 1)
path.write_text(text, encoding="utf-8")
