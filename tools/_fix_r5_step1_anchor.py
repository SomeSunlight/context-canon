from pathlib import Path

path = Path("tools/_block_r5_parent_step1.py")
text = path.read_text(encoding="utf-8")
old = '''    replace_once(
        "src/contextcanon/compiler.py",
        \'\'\'                compiled.source_packages,
                compiled.metadata.name,
            )
\'\'\',
        \'\'\'                composition_packages,
                compiled.metadata.name,
            )
\'\'\',
    )
'''
new = '''    replace_once(
        "src/contextcanon/compiler.py",
        \'\'\'            compiled.inherited_rules, compiled.removed_rules = self._compose_inherited_rule_state(
                compiled.source_packages,
                compiled.metadata.name,
            )
\'\'\',
        \'\'\'            compiled.inherited_rules, compiled.removed_rules = self._compose_inherited_rule_state(
                composition_packages,
                compiled.metadata.name,
            )
\'\'\',
    )
'''
if text.count(old) != 1:
    raise SystemExit(f"R5 generic compiler composition patch anchor count {text.count(old)}")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
