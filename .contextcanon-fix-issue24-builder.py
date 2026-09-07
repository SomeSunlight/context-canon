from pathlib import Path

path = Path(".contextcanon-issue24-legacy-migration.py")
text = path.read_text(encoding="utf-8")
start = text.find("new_test = '''")
if start < 0:
    raise RuntimeError("Issue 24 builder test start delimiter missing")
text = text[:start] + 'new_test = """' + text[start + len("new_test = '''"):]
write_call = text.find("\ntest_path.write_text(test_text.replace(anchor, new_test + anchor, 1)", start)
if write_call < 0:
    raise RuntimeError("Issue 24 builder test write call missing")
closing = text.rfind("'''", start, write_call)
if closing < 0:
    raise RuntimeError("Issue 24 builder test end delimiter missing")
text = text[:closing] + '"""' + text[closing + 3:]
old_state_write = 'state_path.write_text(state, encoding="utf-8")'
new_state_write = 'state_path.write_text(state.rstrip() + "\\n", encoding="utf-8")'
if text.count(old_state_write) != 1:
    raise RuntimeError("Issue 24 STATE write target missing")
text = text.replace(old_state_write, new_state_write, 1)
path.write_text(text, encoding="utf-8")
