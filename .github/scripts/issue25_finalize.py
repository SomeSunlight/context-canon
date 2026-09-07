from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run(*args: str) -> None:
    print('+', *args, flush=True)
    subprocess.run(args, cwd=ROOT, check=True)


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')


def write(path: str, text: str) -> None:
    (ROOT / path).write_text(text, encoding='utf-8')


def replace_once(path: str, old: str, new: str) -> None:
    text = read(path)
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'{path}: expected exactly one replacement target, found {count}')
    write(path, text.replace(old, new, 1))


def append_plan_checkpoint() -> None:
    path = ROOT / 'PLAN.md'
    text = path.read_text(encoding='utf-8').rstrip()
    marker = '## Owner-test format correction: Issue #25'
    if marker not in text:
        raise RuntimeError('Issue #25 PLAN checkpoint must exist before product edits')


def _insert_name(attrs: str, name: str) -> str:
    if re.search(r'\bname="', attrs):
        return attrs
    if '"' in name:
        raise RuntimeError(f'Cannot migrate ctx:node name containing double quote: {name!r}')
    match = re.match(r'(?P<id>id="[^"]+")(?P<rest>.*)', attrs.rstrip())
    if match is None:
        raise RuntimeError(f'ctx:node metadata does not begin with id: {attrs!r}')
    return f'{match.group("id")} name="{name.strip()}"{match.group("rest")}'


def migrate_ctx_node_literals(text: str) -> str:
    # Real Markdown / triple-quoted fixtures with an actual newline.
    actual = re.compile(
        r'(?m)^(?P<prefix>[^\n]*?#\s+)(?P<name>.+?)\s+—\s+Local Context Source(?P<h1tail>[^\n]*)\n'
        r'(?P<indent>[ \t]*)(?P<open><!--\s*ctx:node\s+)(?P<attrs>[^>\n]*?)(?P<close>\s*-->)'
    )

    def actual_repl(match: re.Match[str]) -> str:
        attrs = _insert_name(match.group('attrs'), match.group('name'))
        return (
            match.group('prefix') + match.group('name') + ' — Local Context Source' + match.group('h1tail') + '\n'
            + match.group('indent') + match.group('open') + attrs + match.group('close')
        )

    text = actual.sub(actual_repl, text)

    # Python string fixtures that contain a literal "\\n" between H1 and metadata.
    escaped = re.compile(
        r'(?P<h1>#\s+(?P<name>.+?)\s+—\s+Local Context Source)\\n'
        r'(?P<open><!--\s*ctx:node\s+)(?P<attrs>[^>\n]*?)(?P<close>\s*-->)'
    )

    def escaped_repl(match: re.Match[str]) -> str:
        attrs = _insert_name(match.group('attrs'), match.group('name'))
        return match.group('h1') + r'\n' + match.group('open') + attrs + match.group('close')

    return escaped.sub(escaped_repl, text)


def migrate_nearby_python_literals(text: str) -> str:
    lines = text.splitlines(keepends=True)
    for index, line in enumerate(lines):
        if '<!-- ctx:node' not in line or 'name=' in line or '{name_attr}' in line:
            continue
        nearby = ''.join(lines[max(0, index - 8): index + 1])
        names = re.findall(r'#\s+(.+?)\s+—\s+Local Context Source', nearby)
        if not names:
            continue
        name = names[-1].strip()
        match = re.search(r'<!--\s*ctx:node\s+(id="[^"]+")', line)
        if match is None:
            continue
        line = line[:match.end()] + f' name="{name}"' + line[match.end():]
        lines[index] = line
    return ''.join(lines)


def migrate_files() -> None:
    for path in ROOT.rglob('CONTEXT.src.md'):
        rel = path.relative_to(ROOT).as_posix()
        if '/.context/' in f'/{rel}/' or '/CONTEXT/references/' in f'/{rel}/':
            continue
        before = path.read_text(encoding='utf-8')
        after = migrate_ctx_node_literals(before)
        if before == after and 'ctx:node' in before and ' name="' not in before.split('ctx:node', 1)[1].split('-->', 1)[0]:
            raise RuntimeError(f'Could not migrate authored Node metadata in {rel}')
        if after != before:
            path.write_text(after, encoding='utf-8')

    for path in (ROOT / 'tests').glob('test_*.py'):
        before = path.read_text(encoding='utf-8')
        after = migrate_nearby_python_literals(migrate_ctx_node_literals(before))
        if after != before:
            path.write_text(after, encoding='utf-8')


def update_parser() -> None:
    path = 'src/contextcanon/parser.py'
    replace_once(path, "H1_RE = re.compile(r'^#\\s+(.+?)\\s+—\\s+Local Context Source\\s*$')\n", '')
    old = '''    name = None\n    for line in lines:\n        match = H1_RE.match(line)\n        if match:\n            name = match.group(1).strip()\n            break\n    if not name:\n        raise ContextCanonError(f"{source_path}: first H1 must end with '— Local Context Source'")\n\n    node_attrs = _find_ctx_attrs(lines, NODE_COMMENT_RE)\n    if not node_attrs or not node_attrs.get("id") or not node_attrs.get("version"):\n        raise ContextCanonError(f"{source_path}: missing compiler-managed ctx:node id/version metadata")\n    adapters = tuple(filter(None, (part.strip() for part in node_attrs.get("adapters", "").split(","))))\n    metadata = NodeMetadata(node_attrs["id"], name, node_attrs["version"], adapters)\n'''
    new = '''    node_attrs = _find_ctx_attrs(lines, NODE_COMMENT_RE)\n    if not node_attrs or not all(node_attrs.get(key) for key in ("id", "name", "version")):\n        raise ContextCanonError(f"{source_path}: missing compiler-managed ctx:node id/name/version metadata")\n    name = node_attrs["name"].strip()\n    adapters = tuple(filter(None, (part.strip() for part in node_attrs.get("adapters", "").split(","))))\n    metadata = NodeMetadata(node_attrs["id"], name, node_attrs["version"], adapters)\n'''
    replace_once(path, old, new)


def update_generators() -> None:
    path = 'src/contextcanon/onboarding_structure_materialize.py'
    old = '''    return (\n        f"# {canonical_name or node.name} — Local Context Source\\n"\n        f'<!-- ctx:node id="{node_id}" version="{version}" -->\\n\\n'\n        "## Local Overview\\n\\n"\n'''
    new = '''    name = canonical_name or node.name\n    if '"' in name:\n        raise ContextCanonError('Context Node name must not contain a double quote')\n    return (\n        f"# {name} — Local Context Source\\n"\n        f'<!-- ctx:node id="{node_id}" name="{name}" version="{version}" -->\\n\\n'\n        "## Local Overview\\n\\n"\n'''
    replace_once(path, old, new)

    replace_once(
        'src/contextcanon/onboarding_review.py',
        '''        f'<!-- ctx:node id="{node.id}" version="{node.version}" -->',\n''',
        '''        f'<!-- ctx:node id="{node.id}" name="{node.name}" version="{node.version}" -->',\n''',
    )
    replace_once(
        'src/contextcanon/onboarding_reset.py',
        '''        r'<!-- ctx:node id="[^"]+" version="0\\.1\\.0-draft" -->\\n\\n'\n''',
        '''        r'<!-- ctx:node id="[^"]+" name="[^"]+" version="0\\.1\\.0-draft" -->\\n\\n'\n''',
    )


def update_docs() -> None:
    path = 'nodes/library/foundation/docs/source-format.md'
    text = read(path)
    old = '''## Node header\n\nA source begins with a human-readable H1 and compiler-managed Node metadata:\n\n```markdown\n# Example Project — Local Context Source\n<!-- ctx:node id="<stable-node-id>" version="0.1.0" -->\n```\n\nThe stable ID is independent of the Node's directory path or display name. A root Node may additionally declare generated harness adapters, for example `adapters="agents,goose"`.\n'''
    new = '''## Node header\n\nA source normally begins with a human-readable Markdown H1 followed by explicitly machine-marked Node metadata:\n\n```markdown\n# Example Project\n<!-- ctx:node id="<stable-node-id>" name="Example Project" version="0.1.0" -->\n```\n\nThe `ctx:node` comment is authoritative for machine-significant Node metadata. `id`, `name`, and `version` are required. The Markdown H1 is ordinary human presentation: ContextCanon does not derive Node identity or the canonical Node name from its wording, and changing only the H1 does not change canonical semantics. A project may keep the descriptive `— Local Context Source` suffix as presentation if useful; it is not syntax.\n\nThis is a general authoring boundary: machine-significant ContextCanon fields are carried in visibly marked `ctx:*` metadata or other explicitly specified control structures, not hidden in presentation wording that merely looks like ordinary Markdown.\n\nThe stable ID is independent of the Node's directory path or display name. A root Node may additionally declare generated harness adapters, for example `adapters="agents,goose"`.\n'''
    if old not in text:
        raise RuntimeError('source-format.md Node header section did not match expected text')
    write(path, text.replace(old, new, 1))


def add_regression_tests() -> None:
    path = ROOT / 'tests' / 'test_explicit_node_name.py'
    path.write_text('''from __future__ import annotations\n\nimport sys\nimport tempfile\nimport unittest\nfrom pathlib import Path\n\nROOT = Path(__file__).resolve().parents[1]\nsys.path.insert(0, str(ROOT / "src"))\n\nfrom contextcanon.compiler import Compiler\nfrom contextcanon.parser import ContextCanonError, parse_node\n\n\nclass ExplicitNodeNameTests(unittest.TestCase):\n    def make_repo(self, h1: str, name: str, *, include_name: bool = True) -> Path:\n        root = Path(tempfile.mkdtemp())\n        (root / ".git").mkdir()\n        name_attr = f' name="{name}"' if include_name else ""\n        (root / "CONTEXT.src.md").write_text(\n            f'# {h1}\\n<!-- ctx:node id="node-demo"{name_attr} version="0.1.0" -->\\n',\n            encoding="utf-8",\n        )\n        return root\n\n    def test_canonical_name_comes_from_explicit_machine_metadata(self):\n        repo = self.make_repo("A presentation title with no special suffix", "Canonical Demo")\n        self.assertEqual(parse_node(repo).metadata.name, "Canonical Demo")\n\n    def test_changing_h1_does_not_change_normalized_semantics(self):\n        repo = self.make_repo("First presentation", "Canonical Demo")\n        first = Compiler(repo).compile(repo)\n        source = repo / "CONTEXT.src.md"\n        source.write_text(source.read_text(encoding="utf-8").replace("# First presentation", "# Entirely different presentation"), encoding="utf-8")\n        second = Compiler(repo).compile(repo)\n        self.assertEqual(first.metadata.name, second.metadata.name)\n        self.assertEqual(first.normalized_digest, second.normalized_digest)\n\n    def test_changing_explicit_name_changes_canonical_semantics(self):\n        repo = self.make_repo("Presentation stays fixed", "Canonical Demo")\n        first = Compiler(repo).compile(repo)\n        source = repo / "CONTEXT.src.md"\n        source.write_text(source.read_text(encoding="utf-8").replace('name="Canonical Demo"', 'name="Renamed Demo"'), encoding="utf-8")\n        second = Compiler(repo).compile(repo)\n        self.assertEqual(second.metadata.name, "Renamed Demo")\n        self.assertNotEqual(first.normalized_digest, second.normalized_digest)\n\n    def test_missing_explicit_name_fails_clearly(self):\n        repo = self.make_repo("Presentation", "unused", include_name=False)\n        with self.assertRaisesRegex(ContextCanonError, "ctx:node id/name/version"):\n            parse_node(repo)\n\n\nif __name__ == "__main__":\n    unittest.main()\n''', encoding='utf-8')


def verify_no_legacy_literals() -> None:
    offenders: list[str] = []
    for base in (ROOT / 'src', ROOT / 'tests'):
        for path in base.rglob('*.py'):
            for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
                if '<!-- ctx:node' in line and 'name=' not in line and '{name_attr}' not in line:
                    offenders.append(f'{path.relative_to(ROOT)}:{number}: {line.strip()}')
    for path in ROOT.rglob('CONTEXT.src.md'):
        rel = path.relative_to(ROOT).as_posix()
        if '/.context/' in f'/{rel}/' or '/CONTEXT/references/' in f'/{rel}/':
            continue
        for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
            if '<!-- ctx:node' in line and 'name=' not in line:
                offenders.append(f'{rel}:{number}: {line.strip()}')
    if offenders:
        raise RuntimeError('Legacy ctx:node literals remain:\n' + '\n'.join(offenders))


def finalize_plan_and_state() -> None:
    plan = read('PLAN.md')
    for old, new in (
        ('- [ ] Require explicit `name="..."` in `ctx:node` and make parser/compiler use that field only.', '- [x] Require explicit `name="..."` in `ctx:node` and make parser/compiler use that field only.'),
        ('- [ ] Keep the H1 as ordinary human presentation; changing it alone must not change canonical Node semantics.', '- [x] Keep the H1 as ordinary human presentation; changing it alone must not change canonical Node semantics.'),
        ('- [ ] Update structure/onboarding materialization and all authored ContextCanon Nodes to emit/use explicit machine name metadata.', '- [x] Update structure/onboarding materialization and all authored ContextCanon Nodes to emit/use explicit machine name metadata.'),
        ('- [ ] Migrate tests/documentation and add regressions proving H1 independence and explicit-name authority.', '- [x] Migrate tests/documentation and add regressions proving H1 independence and explicit-name authority.'),
        ('- [ ] Regenerate self-hosted outputs and pass full tests/build/check/diff hygiene before returning to the `ai-workstation` owner test.', '- [x] Regenerate self-hosted outputs and pass full tests/build/check/diff hygiene before returning to the `ai-workstation` owner test.'),
    ):
        plan = plan.replace(old, new)
    plan += '\nIssue #25 implementation checkpoint: canonical Node names now come only from explicit `ctx:node name` metadata. H1 presentation is non-semantic, all ContextCanon authored Nodes and fixtures are migrated, structure materialization emits the explicit field, and regression coverage protects the boundary.\n'
    write('PLAN.md', plan)

    state = read('STATE.md').rstrip() + '''\n\n## Explicit Node-name metadata correction\n\nIssue #25 removes the implicit Node-name syntax from the Markdown H1. Canonical Node names are explicit `ctx:node name="..."` machine metadata; H1 wording is ordinary presentation and may change without changing normalized Context semantics. Structure materialization and all self-hosted ContextCanon Nodes use the explicit form.\n'''
    write('STATE.md', state)


def main() -> None:
    run('git', 'config', 'user.name', 'github-actions[bot]')
    run('git', 'config', 'user.email', '41898282+github-actions[bot]@users.noreply.github.com')
    append_plan_checkpoint()
    update_parser()
    update_generators()
    migrate_files()
    update_docs()
    add_regression_tests()
    verify_no_legacy_literals()
    finalize_plan_and_state()

    run(sys.executable, '-m', 'pip', 'install', '-e', '.')
    run(sys.executable, '-m', 'compileall', '-q', 'src', 'tests')
    run('contextcanon', 'build', '--all', '.')
    run(sys.executable, '-m', 'pytest', '-q')
    run('contextcanon', 'check', '--all', '.')
    run('git', 'diff', '--check')

    run('git', 'rm', '.github/scripts/issue25_finalize.py', '.github/workflows/issue25-finalizer.yml')
    run('git', 'add', '-A')
    run('git', 'commit', '-m', 'Make Context Node name explicit machine metadata (#25)')
    run('git', 'push', 'origin', 'HEAD:agent/issues-14-15-multi-parent')


if __name__ == '__main__':
    main()
