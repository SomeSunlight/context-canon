from pathlib import Path

path = Path("src/contextcanon/sources.py")
text = path.read_text(encoding="utf-8")
old = "_SOURCE_LINE_RE = re.compile(\n    r'^(?P<bullet>- )\\[[^]]+\\]\\((?P<path>[^)]+)\\)(?P<separator>\\s+—\\s+)`[^`]+`(?P<ending>\\s*(?:\\r?\\n)?)$'\n)"
new = "_SOURCE_LINE_RE = re.compile(\n    r'^(?P<prefix>(?P<bullet>- )\\[[^]]+\\]\\((?P<path>[^)]+)\\)(?P<separator>\\s+—\\s+))`[^`]+`(?P<ending>\\s*(?:\\r?\\n)?)$'\n)"
if text.count(old) != 1:
    raise RuntimeError("Source line regex compatibility target missing")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
