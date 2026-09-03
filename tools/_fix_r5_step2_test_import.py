from pathlib import Path

path = Path("tests/test_onboarding_placement_publish.py")
text = path.read_text(encoding="utf-8")
old = "from contextcanon.outputs import write_outputs\nfrom contextcanon.parser import ContextCanonError, parse_node\n"
new = "from contextcanon.outputs import write_outputs\nfrom contextcanon.package import load_package\nfrom contextcanon.parser import ContextCanonError, parse_node\n"
if text.count(old) != 1:
    raise SystemExit(f"placement publish import anchor count {text.count(old)}")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
