from pathlib import Path

path = Path("tools/_fast_run_block_a.py")
text = path.read_text(encoding="utf-8")
replacements = [
    (
        "    '''        '`kind` is exactly one of `rule`, `topic-resource`, `ordinary-documentation`, `state`, `plan`, `authority-mapping`, `unresolved`. `action` is exactly one of `keep`, `move`, `reference`, `map`. `confidence` is exactly `high`, `medium`, or `low`.',\\n''',",
        "    '''        \"`kind` is exactly one of `rule`, `topic-resource`, `ordinary-documentation`, `state`, `plan`, `authority-mapping`, `unresolved`. `action` is exactly one of `keep`, `move`, `reference`, `map`. `confidence` is exactly `high`, `medium`, or `low`.\",\\n''',",
    ),
    (
        "    '''        '`kind` is exactly one of `overview`, `rule`, `topic-resource`, `ordinary-documentation`, `state`, `plan`, `authority-mapping`, `unresolved`. `action` is exactly one of `keep`, `promote`, `reference`, `map`. `confidence` is exactly `high`, `medium`, or `low`.',\\n''',",
        "    '''        \"`kind` is exactly one of `overview`, `rule`, `topic-resource`, `ordinary-documentation`, `state`, `plan`, `authority-mapping`, `unresolved`. `action` is exactly one of `keep`, `promote`, `reference`, `map`. `confidence` is exactly `high`, `medium`, or `low`.\",\\n''',",
    ),
]
for old, new in replacements:
    if text.count(old) != 1:
        raise SystemExit(f"repair target count={text.count(old)} for {old[:70]!r}")
    text = text.replace(old, new)
path.write_text(text, encoding="utf-8", newline="\n")
