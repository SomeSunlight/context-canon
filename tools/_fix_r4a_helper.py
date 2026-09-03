from pathlib import Path

path = Path("tools/_block_r4a_topic_inheritance.py")
text = path.read_text(encoding="utf-8")
old_start = "    collision_test = r'''\n    def test_visible_topic_id_collision_from_different_origins_fails(self):\n"
new_start = '    collision_test = r"""\n    def test_visible_topic_id_collision_from_different_origins_fails(self):\n'
if old_start not in text:
    raise SystemExit("R4a collision-test opening quote anchor not found")
text = text.replace(old_start, new_start, 1)
old_end = "            Compiler(repo).compile(consumer)\n\n'''\n    anchor = \"    def test_conflicting_diamond_rule_fails_without_source_precedence(self):\\n\"\n"
new_end = '            Compiler(repo).compile(consumer)\n\n"""\n    anchor = "    def test_conflicting_diamond_rule_fails_without_source_precedence(self):\\n"\n'
if old_end not in text:
    raise SystemExit("R4a collision-test closing quote anchor not found")
text = text.replace(old_end, new_end, 1)
path.write_text(text, encoding="utf-8")
