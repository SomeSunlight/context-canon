from pathlib import Path

# Correct the generated legacy fixture: pre-Parent publication had no Parent
# section at all, not an empty one.
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

# Step-9 reset historically deleted placement-acceptance.json after restoring
# the journal because no older accepted state could exist. Parent migration can
# now upgrade an exact pre-Parent acceptance, so the journal may intentionally
# restore real previous bytes. Only use the old cleanup fallback when the
# acceptance path was not itself restored by the selected journal record.
path = Path("src/contextcanon/onboarding_reset.py")
text = path.read_text(encoding="utf-8")
old = '''    if 9 in selected_steps:\n        (snapshot / "placement-acceptance.json").unlink(missing_ok=True)\n'''
new = '''    if 9 in selected_steps:\n        acceptance = snapshot / "placement-acceptance.json"\n        try:\n            acceptance_rel = acceptance.relative_to(project).as_posix()\n        except ValueError:\n            acceptance_rel = None\n        if acceptance_rel is None or acceptance_rel not in project_files:\n            acceptance.unlink(missing_ok=True)\n'''
if text.count(old) != 1:
    raise SystemExit(f"reset legacy acceptance cleanup count {text.count(old)}")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
