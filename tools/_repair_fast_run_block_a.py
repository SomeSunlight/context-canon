from pathlib import Path

path = Path("tools/_fast_run_block_a.py")
text = path.read_text(encoding="utf-8")
old = "    '''        '`kind` is exactly one of `rule`, `topic-resource`, `ordinary-documentation`, `state`, `plan`, `authority-mapping`, `unresolved`. `action` is exactly one of `keep`, `move`, `reference`, `map`. `confidence` is exactly `high`, `medium`, or `low`.',\\n''',"
new = "    '''        \"`kind` is exactly one of `rule`, `topic-resource`, `ordinary-documentation`, `state`, `plan`, `authority-mapping`, `unresolved`. `action` is exactly one of `keep`, `move`, `reference`, `map`. `confidence` is exactly `high`, `medium`, or `low`.\",\\n''',"
if text.count(old) != 1:
    raise SystemExit(f"old kind-contract patch target count={text.count(old)}")
text = text.replace(old, new)
old = "    '''        '`kind` is exactly one of `overview`, `rule`, `topic-resource`, `ordinary-documentation`, `state`, `plan`, `authority-mapping`, `unresolved`. `action` is exactly one of `keep`, `promote`, `reference`, `map`. `confidence` is exactly `high`, `medium`, or `low`.',\\n''',"
new = "    '''        \"`kind` is exactly one of `overview`, `rule`, `topic-resource`, `ordinary-documentation`, `state`, `plan`, `authority-mapping`, `unresolved`. `action` is exactly one of `keep`, `promote`, `reference`, `map`. `confidence` is exactly `high`, `medium`, or `low`.\",\\n''',"
if text.count(old) != 1:
    raise SystemExit(f"new kind-contract patch target count={text.count(old)}")
text = text.replace(old, new)
needle = '''replace_once(
    "src/contextcanon/onboarding_placement_instruction.py",
    ''' + "'''" + '''        '  "schema": "contextcanon/onboarding-placement-proposal/v0",',\\n''' + "'''" + ''',
    ''' + "'''" + '''        '  "schema": "contextcanon/onboarding-placement-proposal/v1",',\\n''' + "'''" + ''',
)
'''
addition = needle + '''replace_once(
    "src/contextcanon/onboarding_placement_instruction.py",
    '        \'  "action": "move",\',\\n',
    '        \'  "action": "promote",\',\\n',
)
replace_once(
    "src/contextcanon/onboarding_placement_instruction.py",
    '        "All resource/document/authority paths must exist in the frozen Evidence for this v0 experiment.",\\n',
    '        "All resource/document/authority paths must exist in the frozen Evidence for this v1 experiment.",\\n',
)
'''
if text.count(needle) != 1:
    raise SystemExit(f"schema insertion target count={text.count(needle)}")
text = text.replace(needle, addition)
path.write_text(text, encoding="utf-8", newline="\n")
