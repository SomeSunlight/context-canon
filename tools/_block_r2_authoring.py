from __future__ import annotations

import argparse
from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one match, found {count}: {old[:100]!r}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


def activate_plan() -> None:
    path = Path("PLAN.md")
    text = path.read_text(encoding="utf-8")
    marker = "**Status: NEXT — Block R1 complete; continue with the remaining Block R follow-up slices. Fast-run remains ACTIVE.**"
    active = """**Status: ACTIVE — Block R2 normal post-onboarding authoring. Fast-run remains ACTIVE.**

R2 purpose: keep `CONTEXT.src.md` as the only authoring truth while making ordinary Rule/Topic creation safe and pleasant. ContextCanon should allocate stable hidden IDs once, write ordinary source syntax, and leave the familiar build/check loop intact.

R2 verification: focused authoring/CLI regressions first, then the complete deterministic suite plus self-hosted build/check and hygiene before the clean checkpoint."""
    if "R2 purpose:" not in text:
        if marker not in text:
            raise SystemExit("PLAN.md: R1 completion marker not found")
        path.write_text(text.replace(marker, active, 1), encoding="utf-8")


AUTHORING_PY = r'''from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path

from .parser import ContextCanonError, parse_node


@dataclass(frozen=True)
class AuthoringResult:
    element_id: str
    source_path: Path


def _one_line(value: str, label: str) -> str:
    result = " ".join(value.splitlines()).strip()
    if not result:
        raise ContextCanonError(f"{label} must not be empty")
    return result


def _fresh_id(prefix: str, existing: set[str]) -> str:
    for _ in range(100):
        candidate = f"{prefix}-{uuid.uuid4().hex[:12].upper()}"
        if candidate not in existing:
            return candidate
    raise ContextCanonError(f"Could not allocate a fresh {prefix} identity")


def _section_bounds(lines: list[str], name: str) -> tuple[int, int] | None:
    heading = f"## {name}"
    try:
        heading_index = lines.index(heading)
    except ValueError:
        return None
    end = len(lines)
    for index in range(heading_index + 1, len(lines)):
        if lines[index].startswith("## "):
            end = index
            break
    return heading_index, end


def _trim_insert(lines: list[str], index: int, block: list[str]) -> list[str]:
    before = list(lines[:index])
    after = list(lines[index:])
    while before and not before[-1].strip():
        before.pop()
    while after and not after[0].strip():
        after.pop(0)
    result = before + [""] + block
    if after:
        result += [""] + after
    return result


def _write_validated(node_root: Path, original: str, lines: list[str], expected_kind: str, element_id: str) -> AuthoringResult:
    source_path = node_root / "CONTEXT.src.md"
    source_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    try:
        parsed = parse_node(node_root)
        ids = {item.id for item in (parsed.rules if expected_kind == "rule" else parsed.topics)}
        if element_id not in ids:
            raise ContextCanonError(f"New {expected_kind} {element_id} was not readable after authoring")
    except Exception:
        source_path.write_text(original, encoding="utf-8")
        raise
    return AuthoringResult(element_id, source_path)


def add_rule(
    node_root: Path,
    *,
    title: str,
    statement: str,
    why: str,
    group: str = "General",
) -> AuthoringResult:
    node_root = node_root.resolve()
    parsed = parse_node(node_root)
    title = _one_line(title, "Rule title")
    statement = _one_line(statement, "Rule statement")
    why = _one_line(why, "Rule rationale")
    group = _one_line(group, "Rule group")
    element_id = _fresh_id("RULE", {rule.id for rule in parsed.rules})
    source_path = node_root / "CONTEXT.src.md"
    original = source_path.read_text(encoding="utf-8")
    lines = original.splitlines()
    rule_block = [
        f"- **{title}:** {statement}",
        f"  Why: {why}",
        f'  <!-- ctx:rule id="{element_id}" -->',
    ]

    bounds = _section_bounds(lines, "Rules")
    if bounds is None:
        lines = _trim_insert(lines, len(lines), ["## Rules", "", f"### {group}", ""] + rule_block)
    else:
        start, end = bounds
        group_heading = f"### {group}"
        group_index = next((i for i in range(start + 1, end) if lines[i] == group_heading), None)
        if group_index is None:
            lines = _trim_insert(lines, end, [group_heading, ""] + rule_block)
        else:
            group_end = end
            for i in range(group_index + 1, end):
                if lines[i].startswith("### "):
                    group_end = i
                    break
            lines = _trim_insert(lines, group_end, rule_block)
    return _write_validated(node_root, original, lines, "rule", element_id)


def add_topic(
    node_root: Path,
    *,
    title: str,
    condition: str,
    required_resources: tuple[str, ...] = (),
    optional_resources: tuple[str, ...] = (),
    required_nodes: tuple[str, ...] = (),
    optional_nodes: tuple[str, ...] = (),
) -> AuthoringResult:
    node_root = node_root.resolve()
    parsed = parse_node(node_root)
    title = _one_line(title, "Topic title")
    condition = _one_line(condition, "Topic condition")
    targets = required_resources or optional_resources or required_nodes or optional_nodes
    if not targets:
        raise ContextCanonError("Topic needs at least one --required-resource, --optional-resource, --required-node, or --optional-node target")
    element_id = _fresh_id("TOPIC", {topic.id for topic in parsed.topics})
    source_path = node_root / "CONTEXT.src.md"
    original = source_path.read_text(encoding="utf-8")
    lines = original.splitlines()
    block = [f"### {title}", "", condition, ""]
    if required_resources or required_nodes:
        block += ["Required:"]
        block += [f"- Resource: `{_one_line(value, 'Resource target')}`" for value in required_resources]
        block += [f"- Context Node: `{_one_line(value, 'Context Node target')}`" for value in required_nodes]
        block += [""]
    if optional_resources or optional_nodes:
        block += ["Optional:"]
        block += [f"- Resource: `{_one_line(value, 'Resource target')}`" for value in optional_resources]
        block += [f"- Context Node: `{_one_line(value, 'Context Node target')}`" for value in optional_nodes]
        block += [""]
    block += [f'<!-- ctx:topic id="{element_id}" -->']

    bounds = _section_bounds(lines, "Topics")
    if bounds is None:
        lines = _trim_insert(lines, len(lines), ["## Topics", ""] + block)
    else:
        _, end = bounds
        lines = _trim_insert(lines, end, block)
    return _write_validated(node_root, original, lines, "topic", element_id)
'''


def patch_code() -> None:
    Path("src/contextcanon/authoring.py").write_text(AUTHORING_PY, encoding="utf-8")
    replace_once(
        "src/contextcanon/cli.py",
        "from .compiler import Compiler, discover_nodes\n",
        "from .authoring import add_rule, add_topic\nfrom .compiler import Compiler, discover_nodes\n",
    )
    replace_once(
        "src/contextcanon/cli.py",
        '    source_parser = sub.add_parser("source", help="fetch, review, and explicitly accept immutable Source packages")\n',
        '''    author_parser = sub.add_parser("author", help="write ordinary Rule/Topic authoring with stable IDs allocated by ContextCanon")
    author_sub = author_parser.add_subparsers(dest="author_command", required=True)
    author_rule = author_sub.add_parser("rule", help="add one Rule to CONTEXT.src.md and allocate its stable ID")
    author_rule.add_argument("path", nargs="?", default=".", help="Context Node root (default: current directory)")
    author_rule.add_argument("--group", default="General", help="Rule group heading (default: General)")
    author_rule.add_argument("--title", required=True, help="short human-facing Rule title")
    author_rule.add_argument("--statement", required=True, help="Rule statement")
    author_rule.add_argument("--why", required=True, help="Rule rationale")

    author_topic = author_sub.add_parser("topic", help="add one Topic to CONTEXT.src.md and allocate its stable ID")
    author_topic.add_argument("path", nargs="?", default=".", help="Context Node root (default: current directory)")
    author_topic.add_argument("--title", required=True, help="short human-facing Topic title")
    author_topic.add_argument("--condition", required=True, help="when this deeper context applies")
    author_topic.add_argument("--required-resource", action="append", default=[], metavar="PATH", help="required Resource target; may be repeated")
    author_topic.add_argument("--optional-resource", action="append", default=[], metavar="PATH", help="optional Resource target; may be repeated")
    author_topic.add_argument("--required-node", action="append", default=[], metavar="PATH", help="required Context Node navigation target; may be repeated")
    author_topic.add_argument("--optional-node", action="append", default=[], metavar="PATH", help="optional Context Node navigation target; may be repeated")

    source_parser = sub.add_parser("source", help="fetch, review, and explicitly accept immutable Source packages")
''',
    )
    replace_once(
        "src/contextcanon/cli.py",
        '        if args.command == "source":\n',
        '''        if args.command == "author":
            node_root = _node_root(Path(args.path))
            if args.author_command == "rule":
                result = add_rule(
                    node_root,
                    group=args.group,
                    title=args.title,
                    statement=args.statement,
                    why=args.why,
                )
                print(f"added Rule {result.element_id} to {result.source_path}")
            else:
                result = add_topic(
                    node_root,
                    title=args.title,
                    condition=args.condition,
                    required_resources=tuple(args.required_resource),
                    optional_resources=tuple(args.optional_resource),
                    required_nodes=tuple(args.required_node),
                    optional_nodes=tuple(args.optional_node),
                )
                print(f"added Topic {result.element_id} to {result.source_path}")
            print(f"Next: contextcanon build {node_root}")
            print(f"Then: contextcanon check {node_root}")
            return 0

        if args.command == "source":
''',
    )
    replace_once(
        "src/contextcanon/README.md",
        "- `model.py` — typed deterministic data structures;\n",
        "- `model.py` — typed deterministic data structures;\n- `authoring.py` — narrow safe writes to ordinary `CONTEXT.src.md`, including stable Rule/Topic ID allocation;\n",
    )


def patch_docs() -> None:
    path = "nodes/library/foundation/docs/source-format.md"
    marker = "## Compiler-managed authoring help\n"
    section = '''## Normal authoring after onboarding

After a project has adopted ContextCanon, ordinary work does not repeat migration onboarding. The canonical source remains `CONTEXT.src.md` plus the Node's natural Resource files.

For existing text, edit `CONTEXT.src.md` directly. For a **new Rule or Topic**, prefer the deterministic authoring commands so ContextCanon allocates the hidden stable identity once instead of making the author invent a `ctx:rule` or `ctx:topic` comment:

```text
contextcanon author rule . --group Security --title "Keep secrets out of Git" --statement "Credentials and secret values must stay outside version control." --why "Version control is not a secret store."

contextcanon author topic . --title Logging --condition "When changing logging or diagnostics:" --required-resource docs/logging-contract.md
```

The commands write ordinary source syntax; they do **not** create another authoring database and they do not hide publication behind a write. The resulting `CONTEXT.src.md` is immediately readable and editable by hand. ContextCanon merely allocates the stable `RULE-...` or `TOPIC-...` identity and validates that the edited Node still parses.

The minimal daily loop is intentionally boring:

```text
read CONTEXT.md for the effective working context
→ edit CONTEXT.src.md and/or natural Resource files
→ use contextcanon author rule/topic when creating a new identified element
→ contextcanon build <node-or-repository>
→ contextcanon check <node-or-repository>
→ when a reusable Source has a candidate update, review it before explicit acceptance
```

Use `--all` with `build`/`check` when repository-wide generated state should be refreshed or verified. Source candidate discovery/review/acceptance remains a separate explicit workflow; normal authoring and normal builds never silently pull newer Source meaning.

'''
    replace_once(path, marker, section + marker)


def patch_tests() -> None:
    Path("tests/test_authoring.py").write_text(r'''from __future__ import annotations

import contextlib
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from contextcanon.cli import main
from contextcanon.parser import parse_node


class AuthoringTests(unittest.TestCase):
    def make_node(self) -> Path:
        root = Path(tempfile.mkdtemp())
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        (root / "CONTEXT.src.md").write_text(
            "# Example — Local Context Source\n"
            '<!-- ctx:node id="example-node" version="0.1.0" -->\n',
            encoding="utf-8",
        )
        return root

    def test_author_rule_allocates_identity_and_writes_normal_source(self):
        root = self.make_node()
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            result = main([
                "author", "rule", str(root),
                "--group", "Security",
                "--title", "Keep secrets out of Git",
                "--statement", "Credentials stay outside version control.",
                "--why", "Version control is not a secret store.",
            ])
        self.assertEqual(result, 0)
        parsed = parse_node(root)
        self.assertEqual(len(parsed.rules), 1)
        rule = parsed.rules[0]
        self.assertTrue(rule.id.startswith("RULE-"))
        self.assertEqual(rule.group, "Security")
        text = (root / "CONTEXT.src.md").read_text(encoding="utf-8")
        self.assertIn(f'<!-- ctx:rule id="{rule.id}" -->', text)
        self.assertIn("Next: contextcanon build", stdout.getvalue())

    def test_author_topic_allocates_identity_and_preserves_typed_targets(self):
        root = self.make_node()
        (root / "docs").mkdir()
        (root / "docs" / "logging.md").write_text("# Logging\n", encoding="utf-8")
        result = main([
            "author", "topic", str(root),
            "--title", "Logging",
            "--condition", "When changing logging or diagnostics:",
            "--required-resource", "docs/logging.md",
            "--optional-node", "../operations",
        ])
        self.assertEqual(result, 0)
        parsed = parse_node(root)
        self.assertEqual(len(parsed.topics), 1)
        topic = parsed.topics[0]
        self.assertTrue(topic.id.startswith("TOPIC-"))
        self.assertEqual(topic.condition, "When changing logging or diagnostics:")
        self.assertEqual([(target.intent, target.kind, target.path) for target in topic.targets], [
            ("required", "resource", "docs/logging.md"),
            ("optional", "context-node", "../operations"),
        ])

    def test_author_topic_requires_a_target_without_mutating_source(self):
        root = self.make_node()
        source = root / "CONTEXT.src.md"
        before = source.read_bytes()
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            result = main([
                "author", "topic", str(root),
                "--title", "Empty",
                "--condition", "When nothing is linked:",
            ])
        self.assertEqual(result, 2)
        self.assertEqual(source.read_bytes(), before)
        self.assertIn("Topic needs at least one", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
''', encoding="utf-8")


def complete_plan_and_state() -> None:
    plan = Path("PLAN.md")
    text = plan.read_text(encoding="utf-8")
    text = text.replace(
        "**Status: ACTIVE — Block R2 normal post-onboarding authoring. Fast-run remains ACTIVE.**",
        "**Status: NEXT — Blocks R1/R2 complete; continue with the remaining Block R follow-up slices. Fast-run remains ACTIVE.**",
        1,
    )
    for old in [
        "- [ ] Add first-class authoring ergonomics for new Rules/Topics after onboarding so humans do not have to invent or hand-maintain invisible `ctx:*` identity comments. Preserve stable IDs, but provide an explicit ContextCanon authoring/write command or equivalent safe mechanism that allocates the ID once.",
        "- [ ] Document the minimal post-onboarding daily loop for ordinary projects: read `CONTEXT.md`, edit `CONTEXT.src.md`/Resources, build, check, and review Source updates when present.",
    ]:
        if old not in text:
            raise SystemExit(f"PLAN.md: expected R2 checklist item not found: {old[:100]}")
        text = text.replace(old, old.replace("- [ ]", "- [x]", 1), 1)
    text = text.replace(
        "R2 verification: focused authoring/CLI regressions first, then the complete deterministic suite plus self-hosted build/check and hygiene before the clean checkpoint.",
        "R2 verification: focused authoring/CLI regressions passed, followed by the complete deterministic suite, self-hosted build/check and `git diff --check`. `contextcanon author rule` and `contextcanon author topic` now allocate stable IDs and write ordinary validated `CONTEXT.src.md`; Foundation documents the minimal native-project daily loop.",
        1,
    )
    plan.write_text(text, encoding="utf-8")

    state = Path("STATE.md")
    st = state.read_text(encoding="utf-8")
    marker = "## Latest Block R2 normal-authoring checkpoint"
    if marker not in st:
        st = st.rstrip() + "\n\n" + marker + "\n\n" + (
            "Normal ContextCanon-native project work no longer requires authors to invent hidden Rule/Topic IDs. `contextcanon author rule` and `contextcanon author topic` write the same ordinary `CONTEXT.src.md` syntax humans already maintain, allocate one stable `RULE-...` / `TOPIC-...` identity, validate the resulting Node, and leave build/check explicit. There is no secondary authoring database.\n\n"
            "The reusable Source-format guidance now records the minimal post-onboarding loop: read effective `CONTEXT.md`, edit `CONTEXT.src.md` and natural Resources, use the authoring commands for new identified elements, build, check, and review Source candidates explicitly before acceptance. The remaining Block R work is the source-file-first transformation audit plus the larger semantic-parent/Topic-inheritance and Source-update UX blocks. Fast-run remains active; PR #13 remains draft and unmerged.\n"
        )
        state.write_text(st, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--complete", action="store_true")
    args = parser.parse_args()
    if args.complete:
        complete_plan_and_state()
        return
    activate_plan()
    patch_code()
    patch_docs()
    patch_tests()


if __name__ == "__main__":
    main()
