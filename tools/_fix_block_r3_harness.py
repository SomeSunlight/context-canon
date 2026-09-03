from pathlib import Path

path = Path("tools/_block_r3_source_audit.py")
text = path.read_text(encoding="utf-8")
old = '''        'f"- `{PLACEMENT_REVIEW_NAME}` — human-owned placement decisions.\\\\n"\\n',
        'f"- `{PLACEMENT_REVIEW_NAME}` — human-owned placement decisions.\\\\n"\\n        f"- `{PLACEMENT_AUDIT_NAME}` — generated read-only source-file-first audit of the currently validated placement review.\\\\n"\\n',
'''
new = '''        '- `{PLACEMENT_REVIEW_NAME}` — human-owned placement decisions.\\n- `{PLACEMENT_PREVIEW_NAME}` — exact deterministic publication preview.\\n',
        '- `{PLACEMENT_REVIEW_NAME}` — human-owned placement decisions.\\n- `{PLACEMENT_AUDIT_NAME}` — generated read-only source-file-first audit of the currently validated placement review.\\n- `{PLACEMENT_PREVIEW_NAME}` — exact deterministic publication preview.\\n',
'''
if old not in text:
    raise SystemExit("Block R3 helper artifact-list patch anchor not found")
text = text.replace(old, new, 1)
text = text.replace(
    r'workspace.placement_path.write_text("human review\n", encoding="utf-8")',
    r'workspace.placement_path.write_text("human review\\n", encoding="utf-8")',
    1,
)
text = text.replace(
    r'workspace.placement_audit_path.write_text("generated audit\n", encoding="utf-8")',
    r'workspace.placement_audit_path.write_text("generated audit\\n", encoding="utf-8")',
    1,
)
checkpoint_old = 'state.write_text(state_text.rstrip() + block + "\\n", encoding="utf-8")'
checkpoint_new = 'state.write_text(state_text.rstrip() + block.rstrip() + "\\n", encoding="utf-8")'
if checkpoint_old not in text:
    raise SystemExit("Block R3 helper STATE checkpoint anchor not found")
text = text.replace(checkpoint_old, checkpoint_new, 1)
path.write_text(text, encoding="utf-8")
