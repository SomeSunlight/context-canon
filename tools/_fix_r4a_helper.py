from pathlib import Path

path = Path("tools/_block_r4a_topic_inheritance.py")
text = path.read_text(encoding="utf-8")

# The collision regression itself contains triple-single-quoted Context sources,
# so the outer helper template must use triple double quotes.
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

# Replace the two large renderer functions by function boundaries rather than
# byte-for-byte source blocks.
old_render_call = '    replace_once("src/contextcanon/render.py", old, new)\n'
new_render_call = '''    render_path = Path("src/contextcanon/render.py")
    render_text = render_path.read_text(encoding="utf-8")
    start_marker = "def render_official(compiled: CompiledNode, repo_root: Path) -> str:\\n"
    end_marker = "\\ndef _append_rules(lines: list[str], rules: list[Rule]) -> None:\\n"
    start_index = render_text.find(start_marker)
    end_index = render_text.find(end_marker, start_index)
    if start_index < 0 or end_index < 0:
        raise SystemExit("src/contextcanon/render.py: render_official function boundary not found")
    render_text = render_text[:start_index] + new + render_text[end_index:]
    render_path.write_text(render_text, encoding="utf-8")
'''
if old_render_call not in text:
    raise SystemExit("R4a render_official replacement call not found")
text = text.replace(old_render_call, new_render_call, 1)

old_target_call = '    replace_once("src/contextcanon/render.py", old_target, new_target)\n'
new_target_call = '''    render_path = Path("src/contextcanon/render.py")
    render_text = render_path.read_text(encoding="utf-8")
    start_marker = "def _render_target(compiled: CompiledNode, target, repo_root: Path) -> tuple[str, str]:\\n"
    end_marker = "\\ndef render_adapters(compiled: CompiledNode) -> dict[str, str]:\\n"
    start_index = render_text.find(start_marker)
    end_index = render_text.find(end_marker, start_index)
    if start_index < 0 or end_index < 0:
        raise SystemExit("src/contextcanon/render.py: _render_target function boundary not found")
    render_text = render_text[:start_index] + new_target + render_text[end_index:]
    render_path.write_text(render_text, encoding="utf-8")
'''
if old_target_call not in text:
    raise SystemExit("R4a _render_target replacement call not found")
text = text.replace(old_target_call, new_target_call, 1)

# Preserve backslash escapes inside generated Python functions.
render_template = "    new = '''def render_official(compiled: CompiledNode, repo_root: Path) -> str:\n"
if render_template not in text:
    raise SystemExit("R4a render_official template anchor not found")
text = text.replace(
    render_template,
    "    new = r'''def render_official(compiled: CompiledNode, repo_root: Path) -> str:\n",
    1,
)
target_template = "    new_target = '''def _append_topics(lines: list[str], topics, compiled: CompiledNode, repo_root: Path) -> None:\n"
if target_template not in text:
    raise SystemExit("R4a render target template anchor not found")
text = text.replace(
    target_template,
    "    new_target = r'''def _append_topics(lines: list[str], topics, compiled: CompiledNode, repo_root: Path) -> None:\n",
    1,
)

# The external-Source regression embeds a bytes literal containing \n escapes.
# Keep that replacement raw too so the generated test remains valid Python.
external_assertion_template = "        '''        self.assertEqual([topic.id for topic in compiled.inherited_topics], [\"PY-GUIDE\"])\n"
if external_assertion_template not in text:
    raise SystemExit("R4a external-Source assertion template anchor not found")
text = text.replace(
    external_assertion_template,
    "        r'''        self.assertEqual([topic.id for topic in compiled.inherited_topics], [\"PY-GUIDE\"])\n",
    1,
)

path.write_text(text, encoding="utf-8")
