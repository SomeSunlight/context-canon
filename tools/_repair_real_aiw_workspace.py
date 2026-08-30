from pathlib import Path

path = Path("tools/_real_aiw_review.py")
text = path.read_text(encoding="utf-8")
old_import = 'from contextcanon.outputs import write_outputs\n'
new_import = 'from contextcanon.outputs import write_outputs\nfrom contextcanon.onboarding_workspace import open_onboarding_workspace\n'
if text.count(old_import) != 1:
    raise SystemExit("import target changed")
text = text.replace(old_import, new_import, 1)
old = '''    workspace = aiw / "contextcanon-onboarding"\n    workspace.mkdir(exist_ok=True)\n'''
new = '''    owned_workspace = open_onboarding_workspace(snapshot, create=True)\n    workspace = owned_workspace.root\n'''
if text.count(old) != 1:
    raise SystemExit("workspace target changed")
path.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")
