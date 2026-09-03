from pathlib import Path

path = Path("tests/test_parent_migration.py")
text = path.read_text(encoding="utf-8")
old = r'''PARENT_BLOCK_RE = re.compile(
    r"\n?<!-- contextcanon-placement-parent:start -->\n.*?\n<!-- contextcanon-placement-parent:end -->\n?",
    re.DOTALL,
)
'''
new = r'''PARENT_BLOCK_RE = re.compile(
    r"\n## Parent\n\n<!-- contextcanon-placement-parent:start -->\n.*?\n<!-- contextcanon-placement-parent:end -->\n?(?=\n## |\Z)",
    re.DOTALL,
)
'''
if text.count(old) != 1:
    raise SystemExit(f"legacy Parent fixture regex count {text.count(old)}")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
