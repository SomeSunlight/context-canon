from pathlib import Path

path = Path(__file__).with_name("issue27_propagation_ux.py")
text = path.read_text(encoding="utf-8")
old_start = "TEST.write_text(r'''"
if text.count(old_start) != 1:
    raise SystemExit("unexpected test-string opener")
text = text.replace(old_start, 'TEST.write_text(r"""', 1)
old_end = "''', encoding=\"utf-8\")"
pos = text.rfind(old_end)
if pos < 0:
    raise SystemExit("unexpected test-string closer")
text = text[:pos] + '""", encoding="utf-8")' + text[pos + len(old_end):]
path.write_text(text, encoding="utf-8")
