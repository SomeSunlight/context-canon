from pathlib import Path

path = Path(__file__).with_name("finalize_issue27.py")
text = path.read_text(encoding="utf-8")
start_marker = "# Foundation deep documentation now uses the user-level propagation command.\n"
end_marker = "# Intentional Context Node versions for this feature-level documentation/UX block.\n"
start = text.index(start_marker)
end = text.index(end_marker, start)
text = text[:start] + text[end:]
path.write_text(text, encoding="utf-8")
