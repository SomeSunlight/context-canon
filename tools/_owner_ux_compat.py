from pathlib import Path

root = Path(__file__).resolve().parents[1]

workspace = root / "src/contextcanon/onboarding_workspace.py"
text = workspace.read_text(encoding="utf-8")
old = "This directory is the **visible human working area** for one structure-first ContextCanon onboarding.\n\nStart with [`{PLAN_NAME}`]({PLAN_NAME}). It is deliberately written as an operator runbook:"
new = "This directory is the **visible human working area** for one structure-first ContextCanon onboarding. This README is the stable orientation page; the PLAN is the executable operator surface.\n\nStart with [`{PLAN_NAME}`]({PLAN_NAME}). It is deliberately written as an operator runbook:"
if text.count(old) != 1:
    raise RuntimeError("workspace orientation anchor missing")
workspace.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")

instruction = root / "src/contextcanon/onboarding_placement_instruction.py"
text = instruction.read_text(encoding="utf-8")
old = "1. Preserve precise existing language for facts, constraints, and Rules when it is already the best canonical wording. **Overview is different:**"
new = "1. Preserve precise existing language for facts, constraints, and Rules when it is already the best canonical wording; when a clear self-contained statement already says the right thing, use it verbatim. **Overview is different:**"
if text.count(old) != 1:
    raise RuntimeError("placement wording anchor missing")
instruction.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")

followup_test = root / "tests/test_onboarding_owner_review_followup.py"
text = followup_test.read_text(encoding="utf-8")
old = '        self.assertIn("- [ ] 8. Publish placement", plan)\n'
new = '        self.assertIn("- [ ] 8. Publication preview", plan)\n        self.assertIn("- [ ] 9. Publish placement", plan)\n'
if text.count(old) != 1:
    raise RuntimeError("owner followup nine-step assertion anchor missing")
followup_test.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")
