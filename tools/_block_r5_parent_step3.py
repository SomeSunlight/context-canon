from __future__ import annotations

import sys
from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one match, found {count}: {old[:120]!r}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


def patch_sources() -> None:
    replace_once(
        "src/contextcanon/sources.py",
        "from .model import CompiledNode, CompiledPackage, Rule, SourceRef\nfrom .package import PACKAGE_MANIFEST_PATH, load_package\n",
        "from .model import CompiledNode, CompiledPackage, ParentRef, Rule, SourceRef\nfrom .package import PACKAGE_MANIFEST_PATH, artifact_files, compiled_package, load_package\n",
    )
    replace_once(
        "src/contextcanon/sources.py",
        'REVIEW_SCHEMA = "contextcanon/source-review/v0"\n',
        'REVIEW_SCHEMA = "contextcanon/source-review/v0"\nPARENT_REVIEW_SCHEMA = "contextcanon/parent-review/v0"\n',
    )
    replace_once(
        "src/contextcanon/sources.py",
        "_SOURCE_COMMENT_RE = re.compile(r'^(?P<indent>\\s*)<!--\\s*ctx:source\\s+(?P<attrs>.*?)\\s*-->(?P<ending>\\r?\\n?)$')\n",
        "_SOURCE_COMMENT_RE = re.compile(r'^(?P<indent>\\s*)<!--\\s*ctx:source\\s+(?P<attrs>.*?)\\s*-->(?P<ending>\\r?\\n?)$')\n_PARENT_COMMENT_RE = re.compile(r'^(?P<indent>\\s*)<!--\\s*ctx:parent\\s+(?P<attrs>.*?)\\s*-->(?P<ending>\\r?\\n?)$')\n",
    )

    anchor = "\ndef install_source_package(node_root: Path, package_root: Path) -> CompiledPackage:\n"
    addition = r'''
def review_parent_candidate(node_root: Path) -> tuple[ContextDiff, Path]:
    """Compile the live semantic Parent explicitly and review it as an immutable candidate.

    Ordinary child builds never call this function and therefore remain bound
    to the accepted Parent package pin. Review snapshots the live Parent into a
    content-addressed candidate store without changing the accepted Child.
    """

    node_root = node_root.resolve()
    repo_root = find_repo_root(node_root)
    compiler = Compiler(repo_root)
    compiled = compiler.compile(node_root)
    parent_ref = _parent_ref(compiled)
    current = compiled.parent_package
    assert current is not None

    parent_root = compiler._resolve_source_root(node_root, parent_ref.locator)
    live_parent = Compiler(repo_root).compile(parent_root)
    candidate = compiled_package(live_parent)
    if candidate.metadata.id != parent_ref.id:
        raise ContextCanonError(
            f"Live Parent Node ID {candidate.metadata.id} does not match accepted Parent {parent_ref.name} ({parent_ref.id})"
        )

    _validate_parent_candidate_composition(compiler, compiled, candidate)
    candidate_root = _store_parent_candidate(node_root, live_parent)
    result = diff_packages(current, candidate)
    receipt = {
        "schema": PARENT_REVIEW_SCHEMA,
        "parent_id": parent_ref.id,
        "consumer_node_id": compiled.metadata.id,
        "source_file_sha256": _source_hash(node_root),
        "before": {
            "version": current.metadata.version,
            "normalized_digest": current.normalized_digest,
            "package_digest": current.package_digest,
        },
        "candidate": {
            "version": candidate.metadata.version,
            "normalized_digest": candidate.normalized_digest,
            "package_digest": candidate.package_digest,
        },
        "candidate_path": candidate_root.relative_to(node_root).as_posix(),
        "structural_validation": "passed",
        "diff": result.to_dict(),
    }
    path = _parent_review_path(node_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write_text(path, json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    return result, path


def accept_parent_candidate(node_root: Path) -> CompiledPackage:
    """Accept exactly the most recently reviewed semantic Parent snapshot."""

    node_root = node_root.resolve()
    receipt_path = _parent_review_path(node_root)
    if not receipt_path.is_file():
        raise ContextCanonError("Parent has no review receipt; run 'contextcanon parent review' first")
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContextCanonError(f"Invalid Parent review receipt {receipt_path}: {exc}") from exc
    if not isinstance(receipt, dict) or receipt.get("schema") != PARENT_REVIEW_SCHEMA:
        raise ContextCanonError(f"Invalid Parent review receipt schema in {receipt_path}")

    compiler = Compiler(find_repo_root(node_root))
    compiled = compiler.compile(node_root)
    parent_ref = _parent_ref(compiled)
    current = compiled.parent_package
    assert current is not None
    if receipt.get("parent_id") != parent_ref.id:
        raise ContextCanonError("Parent review receipt belongs to a different Parent")
    if receipt.get("consumer_node_id") != compiled.metadata.id:
        raise ContextCanonError("Parent review receipt belongs to a different consumer Node")
    if receipt.get("source_file_sha256") != _source_hash(node_root):
        raise ContextCanonError("CONTEXT.src.md changed after Parent review; review the Parent candidate again")

    before = receipt.get("before")
    candidate_receipt = receipt.get("candidate")
    if not isinstance(before, dict) or not isinstance(candidate_receipt, dict):
        raise ContextCanonError(f"Invalid Parent review receipt state in {receipt_path}")
    if (
        before.get("version") != current.metadata.version
        or before.get("normalized_digest") != current.normalized_digest
        or before.get("package_digest") != current.package_digest
    ):
        raise ContextCanonError("Accepted Parent state changed after review; review the Parent candidate again")

    candidate_digest = candidate_receipt.get("package_digest")
    if not isinstance(candidate_digest, str):
        raise ContextCanonError(f"Invalid Parent candidate digest in {receipt_path}")
    candidate_root = node_root / ".context" / "parent-candidates" / candidate_digest
    candidate = load_package(candidate_root)
    if candidate.metadata.id != parent_ref.id:
        raise ContextCanonError("Reviewed Parent candidate belongs to a different Node")
    if (
        candidate_receipt.get("version") != candidate.metadata.version
        or candidate_receipt.get("normalized_digest") != candidate.normalized_digest
        or candidate_receipt.get("package_digest") != candidate.package_digest
    ):
        raise ContextCanonError("Parent candidate package differs from the reviewed candidate")
    if receipt.get("structural_validation") != "passed":
        raise ContextCanonError("Parent candidate review did not pass structural validation")

    _validate_parent_candidate_composition(compiler, compiled, candidate)
    _install_package(node_root, candidate_root, candidate)
    _write_parent_pin(node_root, candidate)
    return candidate


def _parent_ref(compiled: CompiledNode) -> ParentRef:
    parent = compiled.parsed.parent
    if parent is None or compiled.parent_package is None:
        raise ContextCanonError(f"{compiled.metadata.name}: Node has no semantic Parent")
    return parent


def _validate_parent_candidate_composition(
    compiler: Compiler,
    compiled: CompiledNode,
    candidate: CompiledPackage,
) -> None:
    packages = [candidate, *compiled.source_packages]
    inherited, removals = compiler._compose_inherited_rule_state(packages, compiled.metadata.name)
    inherited, removals = compiler._apply_rule_changes(
        inherited,
        removals,
        compiled.local_changes,
        compiled.metadata.id,
        compiled.metadata.name,
    )
    seen: dict[str, Rule] = {}
    for rule in (*inherited, *compiled.local_rules):
        previous = seen.get(rule.id)
        if previous is not None and previous.origin_node_id != rule.origin_node_id:
            raise ContextCanonError(
                f"Visible Rule ID collision in {compiled.metadata.name}: {rule.id} comes from multiple Nodes"
            )
        seen[rule.id] = rule
    inherited_topics = compiler._compose_inherited_topics(packages, compiled.metadata.name)
    compiler._validate_visible_topic_ids(inherited_topics, compiled.local_topics, compiled.metadata.name)


def _store_parent_candidate(node_root: Path, compiled_parent: CompiledNode) -> Path:
    package = compiled_package(compiled_parent)
    store = node_root / ".context" / "parent-candidates"
    store.mkdir(parents=True, exist_ok=True)
    destination = store / package.package_digest
    if destination.exists():
        existing = load_package(destination)
        if (
            existing.metadata.id == package.metadata.id
            and existing.normalized_digest == package.normalized_digest
            and existing.package_digest == package.package_digest
        ):
            return destination
        raise ContextCanonError(f"Parent candidate store path exists with different content: {destination}")

    temporary = Path(tempfile.mkdtemp(prefix=f".{package.package_digest[:12]}-", dir=store))
    try:
        for rel, content in artifact_files(compiled_parent).items():
            target = temporary / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        staged = load_package(temporary)
        if staged.normalized_digest != package.normalized_digest or staged.package_digest != package.package_digest:
            raise ContextCanonError("Staged Parent candidate identity changed during review")
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    return destination


def _parent_review_path(node_root: Path) -> Path:
    return node_root / ".context" / "parent-review.json"


def _write_parent_pin(node_root: Path, candidate: CompiledPackage) -> None:
    path = node_root / "CONTEXT.src.md"
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    found = 0
    for index, line in enumerate(lines):
        visible = _SOURCE_LINE_RE.match(line)
        if not visible:
            continue
        search_end = min(index + 5, len(lines))
        for comment_index in range(index + 1, search_end):
            comment = _PARENT_COMMENT_RE.match(lines[comment_index])
            if not comment:
                continue
            attrs = _ATTR_RE.findall(comment.group("attrs"))
            if not attrs:
                continue
            found += 1
            if found > 1:
                raise ContextCanonError(f"More than one semantic Parent appears in {path}")
            lines[index] = visible.group("prefix") + f"`{candidate.metadata.version}`" + visible.group("ending")
            updated: list[tuple[str, str]] = []
            seen_version = False
            for key, value in attrs:
                if key == "version":
                    updated.append((key, candidate.metadata.version))
                    seen_version = True
                elif key not in {"normalized-digest", "package-digest"}:
                    updated.append((key, value))
            if not seen_version:
                updated.append(("version", candidate.metadata.version))
            updated.extend([
                ("normalized-digest", candidate.normalized_digest),
                ("package-digest", candidate.package_digest),
            ])
            attrs_text = " ".join(f'{key}="{value}"' for key, value in updated)
            lines[comment_index] = f"{comment.group('indent')}<!-- ctx:parent {attrs_text} -->{comment.group('ending')}"
            break
    if found != 1:
        raise ContextCanonError(f"Could not find exactly one semantic Parent in {path}")
    _atomic_write_text(path, "".join(lines))

'''
    p = Path("src/contextcanon/sources.py")
    text = p.read_text(encoding="utf-8")
    if anchor not in text:
        raise SystemExit("sources parent insertion anchor missing")
    p.write_text(text.replace(anchor, addition + anchor, 1), encoding="utf-8")


def patch_cli() -> None:
    replace_once(
        "src/contextcanon/cli.py",
        "from .sources import accept_source_candidate, review_source_candidate\n",
        "from .sources import accept_parent_candidate, accept_source_candidate, review_parent_candidate, review_source_candidate\n",
    )
    anchor = '    source_parser = sub.add_parser("source", help="fetch, review, and explicitly accept immutable Source packages")\n'
    parent_block = '''    parent_parser = sub.add_parser("parent", help="review and explicitly accept a newer semantic Parent snapshot")\n    parent_sub = parent_parser.add_subparsers(dest="parent_command", required=True)\n    parent_review = parent_sub.add_parser("review", help="compile the live Parent explicitly and review its immutable candidate snapshot")\n    parent_review.add_argument("--node", default=".", help="child Context Node root (default: current directory)")\n    parent_accept = parent_sub.add_parser("accept", help="accept exactly the most recently reviewed Parent snapshot")\n    parent_accept.add_argument("--node", default=".", help="child Context Node root (default: current directory)")\n\n'''
    p = Path("src/contextcanon/cli.py")
    text = p.read_text(encoding="utf-8")
    if anchor not in text:
        raise SystemExit("cli parent parser anchor missing")
    p.write_text(text.replace(anchor, parent_block + anchor, 1), encoding="utf-8")

    handler_anchor = '        if args.command == "source":\n'
    handler = '''        if args.command == "parent":\n            node_root = _node_root(Path(args.node))\n            if args.parent_command == "review":\n                result, receipt = review_parent_candidate(node_root)\n                print(render_diff(result), end="")\n                try:\n                    label = receipt.relative_to(node_root).as_posix()\n                except ValueError:\n                    label = str(receipt)\n                print(f"Parent review receipt: {label}")\n                print("Accepted Parent pin is unchanged until 'contextcanon parent accept'.")\n                return 0\n            accepted = accept_parent_candidate(node_root)\n            print(f"accepted Parent {accepted.metadata.name} {accepted.metadata.version} ({accepted.package_digest})")\n            print(f"Next: contextcanon build {node_root}")\n            print(f"Then: contextcanon check {node_root}")\n            return 0\n\n'''
    p = Path("src/contextcanon/cli.py")
    text = p.read_text(encoding="utf-8")
    if handler_anchor not in text:
        raise SystemExit("cli parent handler anchor missing")
    p.write_text(text.replace(handler_anchor, handler + handler_anchor, 1), encoding="utf-8")


def write_tests() -> None:
    test = r'''from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from contextcanon.cli import main
from contextcanon.compiler import Compiler
from contextcanon.package import artifact_files
from contextcanon.parser import ContextCanonError
from contextcanon.sources import accept_parent_candidate, review_parent_candidate


PARENT_TEMPLATE = """# Project Parent — Local Context Source
<!-- ctx:node id="node-parent" version="{version}" -->

## Rules

### Policy

- **Parent policy:** {statement}
  Why: Descendants consume only accepted Parent snapshots.
  <!-- ctx:rule id="PARENT-001" -->
"""


def child_text(parent) -> str:
    return f"""# Child — Local Context Source
<!-- ctx:node id="node-child" version="0.1.0" -->

## Parent

- [Project Parent](../parent) — `{parent.metadata.version}`
  <!-- ctx:parent id="node-parent" version="{parent.metadata.version}" normalized-digest="{parent.normalized_digest}" package-digest="{parent.package_digest}" -->
"""


class ParentAcceptanceTests(unittest.TestCase):
    def make_case(self):
        repo = Path(tempfile.mkdtemp())
        (repo / ".git").mkdir()
        parent_root = repo / "parent"
        child_root = repo / "child"
        parent_root.mkdir()
        child_root.mkdir()
        (parent_root / "CONTEXT.src.md").write_text(
            PARENT_TEMPLATE.format(version="1.0.0", statement="Use accepted parent policy v1."),
            encoding="utf-8",
        )
        parent_v1 = Compiler(repo).compile(parent_root)
        destination = child_root / ".context" / "sources" / parent_v1.package_digest
        for rel, content in artifact_files(parent_v1).items():
            path = destination / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        (child_root / "CONTEXT.src.md").write_text(child_text(parent_v1), encoding="utf-8")
        return repo, parent_root, child_root, parent_v1

    def test_live_parent_change_is_non_live_until_review_and_accept(self):
        repo, parent_root, child_root, parent_v1 = self.make_case()
        before = Compiler(repo).compile(child_root)
        self.assertEqual(before.parent_package.package_digest, parent_v1.package_digest)
        self.assertEqual(before.inherited_rules[0].statement, "Use accepted parent policy v1.")

        (parent_root / "CONTEXT.src.md").write_text(
            PARENT_TEMPLATE.format(version="2.0.0", statement="Use reviewed parent policy v2."),
            encoding="utf-8",
        )
        still_v1 = Compiler(repo).compile(child_root)
        self.assertEqual(still_v1.parent_package.package_digest, parent_v1.package_digest)
        self.assertEqual(still_v1.inherited_rules[0].statement, "Use accepted parent policy v1.")

        diff, receipt = review_parent_candidate(child_root)
        self.assertFalse(diff.is_empty)
        self.assertTrue(receipt.is_file())
        reviewed_source = (child_root / "CONTEXT.src.md").read_text(encoding="utf-8")
        self.assertIn(f'package-digest="{parent_v1.package_digest}"', reviewed_source)
        still_v1_after_review = Compiler(repo).compile(child_root)
        self.assertEqual(still_v1_after_review.parent_package.package_digest, parent_v1.package_digest)

        # The review is an exact snapshot. Later live Parent edits must not move
        # what accept means.
        (parent_root / "CONTEXT.src.md").write_text(
            PARENT_TEMPLATE.format(version="3.0.0", statement="Unreviewed parent policy v3."),
            encoding="utf-8",
        )
        accepted = accept_parent_candidate(child_root)
        self.assertEqual(accepted.metadata.version, "2.0.0")
        self.assertNotEqual(accepted.package_digest, parent_v1.package_digest)
        child_source = (child_root / "CONTEXT.src.md").read_text(encoding="utf-8")
        self.assertIn("— `2.0.0`", child_source)
        self.assertIn(f'package-digest="{accepted.package_digest}"', child_source)
        compiled = Compiler(repo).compile(child_root)
        self.assertEqual(compiled.parent_package.package_digest, accepted.package_digest)
        self.assertEqual(compiled.inherited_rules[0].statement, "Use reviewed parent policy v2.")

    def test_child_edit_after_review_invalidates_parent_receipt(self):
        _, parent_root, child_root, _ = self.make_case()
        (parent_root / "CONTEXT.src.md").write_text(
            PARENT_TEMPLATE.format(version="2.0.0", statement="Use reviewed parent policy v2."),
            encoding="utf-8",
        )
        review_parent_candidate(child_root)
        source = child_root / "CONTEXT.src.md"
        source.write_text(source.read_text(encoding="utf-8") + "\n<!-- human child edit -->\n", encoding="utf-8")
        with self.assertRaisesRegex(ContextCanonError, "changed after Parent review"):
            accept_parent_candidate(child_root)

    def test_cli_parent_review_and_accept_keep_explicit_gate(self):
        repo, parent_root, child_root, parent_v1 = self.make_case()
        (parent_root / "CONTEXT.src.md").write_text(
            PARENT_TEMPLATE.format(version="2.0.0", statement="Use reviewed parent policy v2."),
            encoding="utf-8",
        )
        self.assertEqual(main(["parent", "review", "--node", str(child_root)]), 0)
        self.assertEqual(Compiler(repo).compile(child_root).parent_package.package_digest, parent_v1.package_digest)
        self.assertEqual(main(["parent", "accept", "--node", str(child_root)]), 0)
        self.assertEqual(Compiler(repo).compile(child_root).parent_package.metadata.version, "2.0.0")

    def test_parent_commands_require_semantic_parent(self):
        root = Path(tempfile.mkdtemp())
        (root / ".git").mkdir()
        (root / "CONTEXT.src.md").write_text(
            '# Lone Node — Local Context Source\n<!-- ctx:node id="node-lone" version="0.1.0" -->\n',
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ContextCanonError, "has no semantic Parent"):
            review_parent_candidate(root)


if __name__ == "__main__":
    unittest.main()
'''
    Path("tests/test_parent_acceptance.py").write_text(test, encoding="utf-8")


def patch_docs() -> None:
    replace_once(
        "nodes/library/foundation/docs/composition.md",
        "The accepted Parent pin is intentionally non-live. Editing or rebuilding the Parent Node elsewhere does not change an ordinary Child build. A Parent update is a later candidate/review/accept operation, not implicit inheritance from current filesystem bytes.\n",
        "The accepted Parent pin is intentionally non-live. Editing or rebuilding the Parent Node elsewhere does not change an ordinary Child build. A Parent update is a later candidate/review/accept operation, not implicit inheritance from current filesystem bytes.\n\nFor the normal same-project semantic hierarchy the operator does not manage candidate paths manually:\n\n```text\ncontextcanon parent review --node <child-node>\n        ↓\nexplicitly compile the current Parent locator into .context/parent-candidates/<package-digest>/\n        ↓\nexact package diff + Child structural validation + parent-review receipt\n        ↓\ncontextcanon parent accept --node <child-node>\n        ↓\ninstall exactly the reviewed immutable package + update only the Child's Parent pin\n```\n\n`parent review` is the only step that consults the live Parent locator. `build`, `check`, and `parent accept` continue to use immutable local package bytes; even if the live Parent changes again after review, acceptance means the exact reviewed candidate snapshot.\n",
    )


def patch_plan_active() -> None:
    replace_once(
        "PLAN.md",
        "**Status: ACTIVE — R5 Semantic Parent relationship, step 3 of 5. Fast-run remains ACTIVE.**",
        "**Status: ACTIVE — R5 Semantic Parent relationship, step 3 of 5. Fast-run remains ACTIVE.**",
    )


def complete() -> None:
    replace_once(
        "PLAN.md",
        "**Status: ACTIVE — R5 Semantic Parent relationship, step 3 of 5. Fast-run remains ACTIVE.**",
        "**Status: ACTIVE — R5 Semantic Parent relationship, step 4 of 5. Fast-run remains ACTIVE.**",
    )
    replace_once(
        "PLAN.md",
        "- [ ] 3. Make Parent changes non-live: normal builds use the accepted package pin; a changed Parent can only become a candidate until reviewed/accepted.",
        "- [x] 3. Make Parent changes non-live: normal builds use the accepted package pin; a changed Parent can only become a candidate until reviewed/accepted.",
    )
    state = Path("STATE.md")
    text = state.read_text(encoding="utf-8").rstrip() + "\n\n## Latest Block R5 step 3 Parent-update checkpoint\n\nSemantic Parent updates now have their own explicit `contextcanon parent review` / `contextcanon parent accept` gate. Ordinary Child builds remain pinned to accepted package bytes and never dereference the live Parent locator. Review explicitly compiles the current same-project Parent into a content-addressed candidate, validates it against the Child's real Rule/Topic composition and stores an exact receipt; accept installs and pins exactly that reviewed snapshot even if the live Parent changes again afterwards. R5 now proceeds to the full transitive Parent-chain proof.\n"
    state.write_text(text, encoding="utf-8")


def apply() -> None:
    patch_sources()
    patch_cli()
    write_tests()
    patch_docs()
    patch_plan_active()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--complete":
        complete()
    else:
        apply()
