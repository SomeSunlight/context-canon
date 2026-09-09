from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "src/contextcanon/cli.py"
TEST = ROOT / "tests/test_propagation_review_ux.py"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one match, found {count}")
    return text.replace(old, new, 1)


text = CLI.read_text(encoding="utf-8")
start = text.index("def _parent_edges(")
end = text.index("\n\ndef main(", start)
helpers = r'''def _parent_edges(repo_root: Path, start_root: Path | None = None):
    compiler = Compiler(repo_root)
    roots = [root.resolve() for root in discover_nodes(repo_root)]
    parsed = {root: parse_node(root, repo_root) for root in roots}
    parent_roots: dict[Path, list[tuple[object, Path]]] = {}
    for child_root, node in parsed.items():
        for parent in node.parents:
            parent_root = compiler._resolve_source_root(child_root, parent.locator).resolve()
            if parent_root not in parsed:
                raise ContextCanonError(
                    f"{node.metadata.name}: Parent {parent.name} is outside the repository-wide propagation set; update that edge explicitly"
                )
            parent_roots.setdefault(child_root, []).append((parent, parent_root))

    depths: dict[Path, int] = {}
    active: set[Path] = set()

    def depth(root: Path) -> int:
        if root in depths:
            return depths[root]
        if root in active:
            raise ContextCanonError("Semantic Parent cycle prevents top-down propagation")
        active.add(root)
        parents = parent_roots.get(root, [])
        value = 0 if not parents else 1 + max(depth(parent_root) for _, parent_root in parents)
        active.remove(root)
        depths[root] = value
        return value

    edges = [
        (child_root, parent, parent_root)
        for child_root, items in parent_roots.items()
        for parent, parent_root in items
    ]
    edges.sort(
        key=lambda item: (
            depth(item[0]),
            item[0].relative_to(repo_root).as_posix(),
            item[1].id,
        )
    )
    if start_root is None:
        return edges

    start_root = start_root.resolve()
    if start_root not in parsed:
        raise ContextCanonError(f"Propagation start is not a Context Node root: {start_root}")
    reachable = {start_root}
    changed = True
    while changed:
        changed = False
        for child_root, _, parent_root in edges:
            if parent_root in reachable and child_root not in reachable:
                reachable.add(child_root)
                changed = True
    return [edge for edge in edges if edge[2] in reachable]


def _containing_node_root(path: Path, repo_root: Path) -> Path | None:
    cursor = path.resolve()
    if cursor.is_file():
        cursor = cursor.parent
    while True:
        if (cursor / "CONTEXT.src.md").is_file():
            return cursor
        if cursor == repo_root or cursor.parent == cursor:
            return None
        cursor = cursor.parent


def _propagation_scope(path: Path, all_edges: bool):
    resolved = path.resolve()
    repo_root = resolved if (resolved / ".git").exists() else find_repo_root(resolved)
    if all_edges:
        return repo_root, None, _parent_edges(repo_root)
    start_root = _containing_node_root(resolved, repo_root)
    if start_root is None:
        raise ContextCanonError(
            "Propagation without --all must start in a Context Node; run from that Node or use --all for every Parent graph"
        )
    return repo_root, start_root, _parent_edges(repo_root, start_root)


def _print_propagation_review_guide(scope: str, edge_count: int) -> None:
    print("Propagation review")
    print(f"Scope: {scope} ({edge_count} Parent edge(s))")
    print("Before accepting each changed Parent -> Child edge, check:")
    print("  1. Applies here? If not, does this Child need a justified Override/Remove?")
    print("  2. Compatible with other imported Contexts? Import order is never precedence.")
    print("  3. Upstream change itself correct, complete, and well-scoped from this Child's viewpoint?")
    print("If not: fix upstream, make an explicit local Override/Remove, or add a narrower local Rule.")
    print("ContextCanon checks deterministic structural conflicts; semantic correctness remains a human decision.")


def _run_propagation(path: Path, *, all_edges: bool, yes: bool) -> int:
    repo_root, start_root, edges = _propagation_scope(path, all_edges)
    if not edges:
        print("No semantic Parent edges found in the selected propagation scope.")
        return 0
    if all_edges:
        scope = "all semantic Parent graphs in this repository"
    else:
        start = parse_node(start_root, repo_root)
        scope = f"descendants of {start.metadata.name}"
    _print_propagation_review_guide(scope, len(edges))

    accepted_count = 0
    for index, (child_root, parent, parent_root) in enumerate(edges, start=1):
        _report_version_bump(ensure_node_version_advanced(parent_root, repo_root))
        child = parse_node(child_root, repo_root)
        child_label = child_root.relative_to(repo_root).as_posix() or "."
        print(f"\nReview {index}/{len(edges)}: Parent {parent.name} -> Child {child.metadata.name} ({child_label})")
        print("Quick check: applicability · compatibility with other imports · upstream quality")
        result, receipt = review_parent_candidate(child_root, parent.id)
        print("Parent package change:")
        print(render_diff(result), end="")
        if result.is_empty:
            print("Parent pin is already current; no acceptance needed.")
            continue
        if not yes and not _confirm(f"Accept this reviewed Parent update for Child {child.metadata.name}?"):
            print("Stopped before acceptance; the reviewed receipt remains available for explicit acceptance.")
            return 0
        accepted = accept_parent_candidate(child_root, parent.id)
        accepted_count += 1
        print(f"accepted Parent {accepted.metadata.name} {accepted.metadata.version} for Child {child.metadata.name}")
        _report_version_bump(ensure_node_version_advanced(child_root, repo_root))

    print(f"Propagation review complete: accepted {accepted_count} changed Parent edge(s).")
    print("Next from the repository root: contextcanon build --all .")
    print("Then: contextcanon check --all .")
    return 0
'''
text = text[:start] + helpers + text[end:]

parser_marker = '    parent_parser = sub.add_parser("parent", help="review and explicitly accept a newer semantic Parent snapshot")\n'
parser_insert = '''    propagate_parser = sub.add_parser(
        "propagate",
        help="review downstream Parent updates top-down; each changed edge remains an explicit acceptance",
    )
    propagate_parser.add_argument(
        "path", nargs="?", default=".",
        help="starting Context Node; with --all any path inside the repository (default: current directory)",
    )
    propagate_parser.add_argument(
        "--all", action="store_true",
        help="broaden review scope to every semantic Parent edge in the repository",
    )
    propagate_parser.add_argument(
        "--yes", action="store_true",
        help="accept each displayed changed Parent edge without interactive confirmation (controlled automation)",
    )

'''
text = replace_once(text, parser_marker, parser_insert + parser_marker, "top-level propagate parser")

text = text.replace(
    '    parent_propagate = parent_sub.add_parser("propagate", help="review and accept stale Parent edges top-down across a repository")\n'
    '    parent_propagate.add_argument("path", nargs="?", default=".", help="repository root or path inside it (default: current directory)")\n'
    '    parent_propagate.add_argument("--all", action="store_true", help="explicitly select all semantic Parent edges in the repository")\n'
    '    parent_propagate.add_argument("--yes", action="store_true", help="accept each displayed Parent diff without interactive confirmation")\n',
    '    parent_propagate = parent_sub.add_parser("propagate", help="explicit Parent-oriented form of guided downstream propagation")\n'
    '    parent_propagate.add_argument("path", nargs="?", default=".", help="starting Context Node; with --all any path inside the repository")\n'
    '    parent_propagate.add_argument("--all", action="store_true", help="broaden review scope to every semantic Parent edge in the repository")\n'
    '    parent_propagate.add_argument("--yes", action="store_true", help="accept each displayed changed Parent edge without interactive confirmation (controlled automation)")\n',
    1,
)

parent_start = text.index('        if args.command == "parent":\n            if args.parent_command == "propagate":')
parent_end = text.index('\n\n            node_root = _node_root(Path(args.node))', parent_start)
parent_block = '''        if args.command == "propagate":
            return _run_propagation(Path(args.path), all_edges=args.all, yes=args.yes)

        if args.command == "parent":
            if args.parent_command == "propagate":
                return _run_propagation(Path(args.path), all_edges=args.all, yes=args.yes)'''
text = text[:parent_start] + parent_block + text[parent_end:]

source_intro_old = '''            if args.source_command in {"fetch", "update"}:
                candidate, location = fetch_git_candidate(node_root, source_id, discovery_ref=args.ref)
'''
source_intro_new = '''            if args.source_command in {"fetch", "update"}:
                parsed = parse_node(node_root, repo_root)
                current = next(source for source in parsed.sources if source.id == source_id)
                if args.source_command == "update":
                    print(f"Reviewing Source update for local Node: {parsed.metadata.name}")
                    print(f"Accepted Source: {current.name} {current.version}")
                    print("This first reviews the external Source candidate. Nothing local changes until you accept it.")
                    print("")
                candidate, location = fetch_git_candidate(node_root, source_id, discovery_ref=args.ref)
'''
text = replace_once(text, source_intro_old, source_intro_new, "source update intro")
text = replace_once(
    text,
    '''                parsed = parse_node(node_root, repo_root)
                current = next(source for source in parsed.sources if source.id == source_id)
                if args.source_command == "update":
''',
    '''                if args.source_command == "update":
''',
    "remove duplicate source parse",
)

source_review_old = '''                result, receipt = review_source_candidate(node_root, source_id, location)
                print(render_diff(result), end="")
                if not args.yes and not _confirm(f"Accept this reviewed Source update for {current.name}?"):
                    print(f"Stopped before acceptance. Review receipt: {receipt}")
                    return 0
                accepted = accept_source_candidate(node_root, source_id, location)
                print(f"accepted Source {accepted.metadata.name} {accepted.metadata.version} ({accepted.package_digest})")
                _report_version_bump(ensure_node_version_advanced(node_root, repo_root))
                print("If this Node has descendants, run 'contextcanon parent propagate --all' from the repository root.")
                return 0
'''
source_review_new = '''                result, receipt = review_source_candidate(node_root, source_id, location)
                print("\nExternal Source change:")
                print(render_diff(result), end="")
                print("Local effect if accepted:")
                print(f"  - {parsed.metadata.name} will accept Source {candidate.metadata.name} {candidate.metadata.version}.")
                print("  - The reviewed Source changes become input to this Node's effective Context; explicit local Override/Remove still apply.")
                print("  - Generated CONTEXT.md is not rebuilt by this acceptance.")
                downstream = _parent_edges(repo_root, node_root)
                downstream_nodes = []
                seen_downstream = set()
                for child_root, _, _ in downstream:
                    child = parse_node(child_root, repo_root)
                    if child.metadata.id in seen_downstream:
                        continue
                    seen_downstream.add(child.metadata.id)
                    downstream_nodes.append((child.metadata.name, child_root.relative_to(repo_root).as_posix() or "."))
                if downstream_nodes:
                    print("Downstream review still pending:")
                    print("  No Child is changed by this Source acceptance.")
                    print("  Potentially affected dependent Nodes:")
                    for name, label in downstream_nodes:
                        print(f"    - {name} ({label})")
                else:
                    print("Downstream review: this Node has no dependent Child Nodes in the repository propagation graph.")
                if not args.yes and not _confirm(f"Accept this reviewed Source update for {candidate.metadata.name}?"):
                    print(f"Stopped before acceptance. Review receipt: {receipt}")
                    return 0
                accepted = accept_source_candidate(node_root, source_id, location)
                print(f"accepted Source {accepted.metadata.name} {accepted.metadata.version} ({accepted.package_digest})")
                _report_version_bump(ensure_node_version_advanced(node_root, repo_root))
                if downstream_nodes:
                    start_label = node_root.relative_to(repo_root).as_posix() or "."
                    print("Next: review downstream applicability when ready; this is not automatic acceptance:")
                    print(f"  contextcanon propagate {start_label}")
                    print("The propagation review checks each changed Parent -> Child edge and asks before acceptance.")
                    print("After the intended propagation reviews: contextcanon build --all . && contextcanon check --all .")
                else:
                    print("Next from the repository root: contextcanon build --all .")
                    print("Then: contextcanon check --all .")
                return 0
'''
text = replace_once(text, source_review_old, source_review_new, "source local-impact review")
CLI.write_text(text, encoding="utf-8")

TEST.write_text(r'''from __future__ import annotations

import contextlib
import io
import shutil
import tempfile
import unittest
from pathlib import Path

from contextcanon.cli import main as cli_main
from contextcanon.compiler import Compiler
from contextcanon.outputs import write_outputs
from contextcanon.package import artifact_files


def write_node(repo: Path, root: Path, node_id: str, name: str, version: str, statement: str):
    root.mkdir(parents=True, exist_ok=True)
    root.joinpath("CONTEXT.src.md").write_text(
        f'''# {name} — Local Context Source\n<!-- ctx:node id="{node_id}" name="{name}" version="{version}" -->\n\n## Local Rules\n\n### General\n\n- **Policy:** {statement}\n  Why: Test.\n  <!-- ctx:rule id="RULE-1" -->\n''',
        encoding="utf-8",
    )
    compiled = Compiler(repo).compile(root)
    write_outputs(compiled)
    return Compiler(repo).compile(root)


def install_package(child: Path, compiled) -> None:
    destination = child / ".context" / "sources" / compiled.package_digest
    for rel, content in artifact_files(compiled).items():
        target = destination / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)


def write_child(repo: Path, root: Path, node_id: str, name: str, parent_path: str, parent):
    root.mkdir(parents=True, exist_ok=True)
    root.joinpath("CONTEXT.src.md").write_text(
        f'''# {name} — Local Context Source\n<!-- ctx:node id="{node_id}" name="{name}" version="0.1.0" -->\n\n## Parent Context Node\n\n- [{parent.metadata.name}]({parent_path}) — `{parent.metadata.version}`\n  <!-- ctx:parent id="{parent.metadata.id}" version="{parent.metadata.version}" normalized-digest="{parent.normalized_digest}" package-digest="{parent.package_digest}" -->\n''',
        encoding="utf-8",
    )
    install_package(root, parent)
    compiled = Compiler(repo).compile(root)
    write_outputs(compiled)
    return Compiler(repo).compile(root)


class PropagationReviewUXTests(unittest.TestCase):
    def test_top_level_propagate_scopes_from_current_node_and_all_broadens_scope(self):
        repo = Path(tempfile.mkdtemp())
        try:
            (repo / ".git").mkdir()
            root = write_node(repo, repo, "root", "Root", "1.0.0", "Root old.")
            child = write_child(repo, repo / "child", "child", "Child", "..", root)
            write_child(repo, repo / "child" / "grand", "grand", "Grand", "..", child)

            other = write_node(repo, repo / "other", "other", "Other", "1.0.0", "Other old.")
            other_leaf = write_child(repo, repo / "other" / "leaf", "other-leaf", "Other Leaf", "..", other)

            write_node(repo, repo, "root", "Root", "1.1.0", "Root new.")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                rc = cli_main(["propagate", str(repo), "--yes"])
            self.assertEqual(rc, 0, out.getvalue())
            self.assertIn("Propagation review", out.getvalue())
            self.assertIn("Applies here?", out.getvalue())
            self.assertIn("Import order is never precedence", out.getvalue())
            grand = Compiler(repo).compile(repo / "child" / "grand")
            self.assertIn("Root new.", [rule.statement for rule in grand.inherited_rules])
            unchanged_other = Compiler(repo).compile(repo / "other" / "leaf").parent_packages[0]
            self.assertEqual(unchanged_other.package_digest, other_leaf.parent_packages[0].package_digest)

            write_node(repo, repo / "other", "other", "1.1.0", "Other new.")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                rc = cli_main(["propagate", str(repo), "--all", "--yes"])
            self.assertEqual(rc, 0, out.getvalue())
            updated_other = Compiler(repo).compile(repo / "other" / "leaf")
            self.assertIn("Other new.", [rule.statement for rule in updated_other.inherited_rules])
        finally:
            shutil.rmtree(repo, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
''', encoding="utf-8")
