from pathlib import Path

path = Path("tools/_real_aiw_publish.py")
text = path.read_text(encoding="utf-8")
old = 'for entry in manifest["files"]'
new = 'for entry in manifest["included"]'
if text.count(old) != 1:
    raise SystemExit(f"manifest target count={text.count(old)}")
text = text.replace(old, new, 1)
old = '("Keep project version in `pyproject.toml` aligned", root_source),'
new = '("Keep the project version in `pyproject.toml` aligned", root_source),'
if text.count(old) != 1:
    raise SystemExit(f"version assertion target count={text.count(old)}")
text = text.replace(old, new, 1)
old = 'if "No `CONTEXT.src.md` delta" not in second_preview:'
new = 'if "No source delta; the reviewed placement is already materialized." not in second_preview:'
if text.count(old) != 1:
    raise SystemExit(f"idempotence assertion target count={text.count(old)}")
path.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")
