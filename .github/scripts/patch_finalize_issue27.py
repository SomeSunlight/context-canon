from pathlib import Path

path = Path(__file__).with_name("finalize_issue27.py")
text = path.read_text(encoding="utf-8")

start_marker = "# Foundation deep documentation now uses the user-level propagation command.\n"
end_marker = "# Intentional Context Node versions for this feature-level documentation/UX block.\n"
start = text.index(start_marker)
end = text.index(end_marker, start)
text = text[:start] + text[end:]

insert_marker = "# Changelog and durable project status.\n"
extra = '''replace_once(
    "nodes/internal/framework-development/CONTEXT.src.md",
    '<!-- ctx:source id="4ca9d92c-59f2-4b1f-b7b3-0e2ff91fd001" version="0.1.1-draft" -->',
    '<!-- ctx:source id="4ca9d92c-59f2-4b1f-b7b3-0e2ff91fd001" version="0.2.0-draft" -->',
)
replace_once(
    "nodes/internal/framework-development/CONTEXT.src.md",
    '<!-- ctx:source id="c4c94726-3cc7-4df6-b779-72bbf9c06f40" version="0.2.1-draft" -->',
    '<!-- ctx:source id="c4c94726-3cc7-4df6-b779-72bbf9c06f40" version="0.3.0-draft" -->',
)

'''
if text.count(insert_marker) != 1:
    raise SystemExit("finalizer insertion marker missing")
text = text.replace(insert_marker, extra + insert_marker, 1)
path.write_text(text, encoding="utf-8")
