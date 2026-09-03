from __future__ import annotations

import sys
from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one match, found {count}: {old[:140]!r}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


def patch_git_transport() -> None:
    p = Path("src/contextcanon/git_transport.py")
    text = p.read_text(encoding="utf-8")
    anchor = "\ndef fetch_git_candidate(node_root: Path, source_id: str) -> tuple[CompiledPackage, Path]:\n"
    helper = r'''
def resolve_git_package_provenance(package_root: Path) -> dict[str, str]:
    """Resolve clean, exact Git provenance for one already-published package Node.

    This is a read-only first-adoption helper. It never fetches and never
    guesses a branch: the package bytes must already exist in a clean Git
    checkout, and the returned ``ref`` is the checkout's exact HEAD commit.
    """

    package_root = package_root.resolve()

    def read(root: Path, *args: str) -> str:
        try:
            completed = subprocess.run(
                ["git", "-C", str(root), *args],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
        except FileNotFoundError as exc:
            raise ContextCanonError("Git Source provenance requires the 'git' executable on PATH") from exc
        except OSError as exc:
            raise ContextCanonError(f"Could not start Git Source provenance lookup: {exc}") from exc
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip() or f"exit code {completed.returncode}"
            raise ContextCanonError(f"Could not resolve Git Source provenance: {detail}")
        return completed.stdout.strip()

    repository = Path(read(package_root, "rev-parse", "--show-toplevel")).resolve()
    try:
        node_path = package_root.relative_to(repository).as_posix() or "."
    except ValueError as exc:
        raise ContextCanonError(f"Source package root is not inside its Git repository: {package_root}") from exc

    status = read(
        repository,
        "status",
        "--porcelain",
        "--untracked-files=all",
        "--",
        node_path,
    )
    if status:
        raise ContextCanonError(
            "Source package path has uncommitted changes; exact first-adoption provenance would be ambiguous"
        )

    ref = read(repository, "rev-parse", "HEAD")
    if not _GIT_SHA_RE.fullmatch(ref):
        raise ContextCanonError(f"Source Git HEAD is not an exact commit SHA: {ref!r}")
    locator = read(repository, "remote", "get-url", "origin")
    if not locator:
        raise ContextCanonError("Source Git repository has no usable origin locator")
    if any(char in locator for char in '"\n\r])'):
        raise ContextCanonError("Source Git origin cannot be represented safely in Context authoring")
    if any(char in node_path for char in '"\n\r'):
        raise ContextCanonError("Source Git node path cannot be represented safely in Context authoring")
    return {"locator": locator, "ref": ref, "node_path": node_path}

'''
    if anchor not in text:
        raise SystemExit("git transport fetch anchor missing")
    p.write_text(text.replace(anchor, helper + anchor, 1), encoding="utf-8")


def patch_sources() -> None:
    replace_once(
        "src/contextcanon/sources.py",
        "from .git_transport import load_candidate_provenance\n",
        "from .git_transport import load_candidate_provenance, resolve_git_package_provenance\n",
    )

    p = Path("src/contextcanon/sources.py")
    text = p.read_text(encoding="utf-8")
    anchor = "\ndef review_source_candidate(\n"
    helper = r'''
def adopt_source_package(node_root: Path, package_root: Path) -> tuple[CompiledPackage, bool]:
    """Explicitly adopt one exact published Git-backed package as a new Source.

    The operator's invocation is the first-adoption decision. ContextCanon
    resolves exact clean Git provenance, validates the *future* consumer
    composition in memory, installs the immutable package, and only then
    atomically publishes one Source declaration. Existing Source identities are
    never upgraded through this path; they stay on fetch/review/accept.
    """

    node_root = node_root.resolve()
    package_root = package_root.resolve()
    repo_root = find_repo_root(node_root)
    parsed = parse_node(node_root, repo_root)
    candidate = load_package(package_root)

    if candidate.metadata.id == parsed.metadata.id:
        raise ContextCanonError(f"{parsed.metadata.name}: a Node cannot adopt itself as a Source")
    if parsed.parent is not None and parsed.parent.id == candidate.metadata.id:
        raise ContextCanonError(
            f"{parsed.metadata.name}: Node {candidate.metadata.id} is already the semantic Parent and cannot also be a Source"
        )

    matches = [source for source in parsed.sources if source.id == candidate.metadata.id]
    if matches:
        if len(matches) != 1:
            raise ContextCanonError(
                f"{parsed.metadata.name}: Source Node ID {candidate.metadata.id} is not unique"
            )
        existing = matches[0]
        if (
            existing.is_pinned
            and existing.version == candidate.metadata.version
            and existing.normalized_digest == candidate.normalized_digest
            and existing.package_digest == candidate.package_digest
        ):
            _install_package(node_root, package_root, candidate)
            Compiler(repo_root).compile(node_root)
            return candidate, False
        raise ContextCanonError(
            f"{parsed.metadata.name}: Source {candidate.metadata.name} ({candidate.metadata.id}) already exists with a different accepted package; use 'contextcanon source fetch/review/accept' for updates"
        )

    provenance = resolve_git_package_provenance(package_root)
    entry = _render_adopted_source(candidate, provenance)
    source_path = node_root / "CONTEXT.src.md"
    before = source_path.read_text(encoding="utf-8")
    after = _insert_source_entry(before, entry)

    resources = {
        file.path: (package_root / file.path).read_bytes()
        for file in candidate.files
        if file.path.startswith("CONTEXT/references/")
    }
    preview = Compiler(
        repo_root,
        source_overrides={node_root: after},
        package_overrides={(node_root, candidate.package_digest): (candidate, resources)},
    )
    preview.compile(node_root)

    destination = node_root / ".context" / "sources" / candidate.package_digest
    existed = destination.exists()
    _install_package(node_root, package_root, candidate)
    try:
        _atomic_write_text(source_path, after)
        Compiler(repo_root).compile(node_root)
    except Exception:
        _atomic_write_text(source_path, before)
        if not existed and destination.exists():
            shutil.rmtree(destination, ignore_errors=True)
        raise
    return candidate, True


def _render_adopted_source(candidate: CompiledPackage, provenance: dict[str, str]) -> str:
    name = candidate.metadata.name
    if any(char in name for char in "]\n\r"):
        raise ContextCanonError(f"Source name cannot be represented safely: {name!r}")
    return "\n".join(
        [
            f"- [{name}]({provenance['locator']}) — `{candidate.metadata.version}`",
            (
                f'  <!-- ctx:source id="{candidate.metadata.id}" version="{candidate.metadata.version}" '
                f'normalized-digest="{candidate.normalized_digest}" '
                f'package-digest="{candidate.package_digest}" transport="git" '
                f'ref="{provenance["ref"]}" node-path="{provenance["node_path"]}" -->'
            ),
        ]
    )


def _insert_source_entry(text: str, entry: str) -> str:
    heading = re.search(r"(?m)^## Sources\s*$", text)
    if heading is None:
        return text.rstrip() + "\n\n## Sources\n\n" + entry.rstrip() + "\n"
    next_heading = re.compile(r"(?m)^## .+$").search(text, heading.end())
    insert_at = next_heading.start() if next_heading else len(text)
    before = text[:insert_at].rstrip()
    after = text[insert_at:].lstrip("\n")
    result = before + "\n\n" + entry.rstrip() + "\n"
    if after:
        result += "\n" + after
    return result.rstrip() + "\n"

'''
    if anchor not in text:
        raise SystemExit("sources review anchor missing")
    p.write_text(text.replace(anchor, helper + anchor, 1), encoding="utf-8")


def patch_cli() -> None:
    replace_once(
        "src/contextcanon/cli.py",
        "from .sources import accept_parent_candidate, accept_source_candidate, review_parent_candidate, review_source_candidate\n",
        "from .sources import adopt_source_package, accept_parent_candidate, accept_source_candidate, review_parent_candidate, review_source_candidate\n",
    )
    replace_once(
        "src/contextcanon/cli.py",
        '''    source_sub = source_parser.add_subparsers(dest="source_command", required=True)\n    source_fetch = source_sub.add_parser("fetch", help="fetch a Source candidate through its declared transport")\n''',
        '''    source_sub = source_parser.add_subparsers(dest="source_command", required=True)\n    source_adopt = source_sub.add_parser("adopt", help="explicitly adopt one exact published Git package as a new Source")\n    source_adopt.add_argument("package", help="local root of the exact published Source package Node")\n    source_adopt.add_argument("--node", default=".", help="consumer Context Node root (default: current directory)")\n    source_fetch = source_sub.add_parser("fetch", help="fetch a Source candidate through its declared transport")\n''',
    )
    replace_once(
        "src/contextcanon/cli.py",
        '''        if args.command == "source":\n            node_root = _node_root(Path(args.node))\n            if args.source_command == "fetch":\n''',
        '''        if args.command == "source":\n            node_root = _node_root(Path(args.node))\n            if args.source_command == "adopt":\n                adopted, changed = adopt_source_package(node_root, Path(args.package))\n                verb = "adopted" if changed else "already adopted"\n                print(f"{verb} Source {adopted.metadata.name} {adopted.metadata.version} ({adopted.package_digest})")\n                print(f"Next: contextcanon build {node_root}")\n                print(f"Then: contextcanon check {node_root}")\n                return 0\n            if args.source_command == "fetch":\n''',
    )


def patch_tests() -> None:
    p = Path("tests/test_source_adoption.py")
    p.write_text(r'''from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from contextcanon.cli import main
from contextcanon.compiler import Compiler
from contextcanon.package import artifact_files
from contextcanon.parser import ContextCanonError, parse_node
from contextcanon.sources import adopt_source_package
from tests.test_git_transport import GitTransportTests


CONSUMER = ''' + "'''" + r'''# AI Workstation — Local Context Source
<!-- ctx:node id="node-consumer" version="0.1.0" -->

## Overview

Already-published onboarding meaning remains untouched.
''' + "'''" + r'''


class SourceAdoptionTests(unittest.TestCase):
    def setUp(self):
        helper = GitTransportTests()
        self.provider, self.v1, self.v2 = helper.make_provider()
        subprocess.run(
            ["git", "remote", "add", "origin", "https://example.test/shared-context.git"],
            cwd=self.provider,
            check=True,
        )
        self.package_root = self.provider / "nodes/library/python-development"
        self.consumer = Path(tempfile.mkdtemp())
        (self.consumer / ".git").mkdir()
        (self.consumer / "CONTEXT.src.md").write_text(CONSUMER, encoding="utf-8")
        acceptance = self.consumer / ".context/onboarding/frozen/placement-acceptance.json"
        acceptance.parent.mkdir(parents=True)
        acceptance.write_text(
            json.dumps({"schema": "legacy-placement", "sources": []}, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        self.acceptance = acceptance
        self.acceptance_before = acceptance.read_bytes()

    def test_explicit_first_adoption_preserves_placement_and_builds_offline(self):
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=self.provider, check=True, text=True, capture_output=True
        ).stdout.strip()
        adopted, changed = adopt_source_package(self.consumer, self.package_root)
        self.assertTrue(changed)
        self.assertEqual(adopted.package_digest, self.v2.package_digest)
        self.assertEqual(self.acceptance.read_bytes(), self.acceptance_before)

        parsed = parse_node(self.consumer, self.consumer)
        self.assertEqual(len(parsed.sources), 1)
        source = parsed.sources[0]
        self.assertEqual(source.id, "node-python")
        self.assertEqual(source.package_digest, self.v2.package_digest)
        self.assertEqual(source.transport, "git")
        self.assertEqual(source.transport_ref, head)
        self.assertEqual(source.node_path, "nodes/library/python-development")
        self.assertEqual(source.locator, "https://example.test/shared-context.git")
        self.assertTrue((self.consumer / ".context/sources" / self.v2.package_digest).is_dir())

        again, second_changed = adopt_source_package(self.consumer, self.package_root)
        self.assertFalse(second_changed)
        self.assertEqual(again.package_digest, self.v2.package_digest)
        self.assertEqual((self.consumer / "CONTEXT.src.md").read_text(encoding="utf-8").count("ctx:source"), 1)

        shutil.rmtree(self.provider)
        compiled = Compiler(self.consumer).compile(self.consumer)
        self.assertEqual(compiled.source_packages[0].package_digest, self.v2.package_digest)
        self.assertEqual(compiled.inherited_rules[0].statement, "Prefer explicit Python v2.")
        self.assertEqual(self.acceptance.read_bytes(), self.acceptance_before)

    def test_cli_adopt_is_a_single_explicit_operator_action(self):
        self.assertEqual(
            main(["source", "adopt", str(self.package_root), "--node", str(self.consumer)]),
            0,
        )
        compiled = Compiler(self.consumer).compile(self.consumer)
        self.assertEqual(compiled.source_packages[0].package_digest, self.v2.package_digest)

    def test_existing_source_identity_cannot_be_silently_replaced(self):
        adopt_source_package(self.consumer, self.package_root)
        old_package = Path(tempfile.mkdtemp())
        for rel, content in artifact_files(self.v1).items():
            target = old_package / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        before = (self.consumer / "CONTEXT.src.md").read_bytes()
        with self.assertRaisesRegex(ContextCanonError, "already exists with a different accepted package"):
            adopt_source_package(self.consumer, old_package)
        self.assertEqual((self.consumer / "CONTEXT.src.md").read_bytes(), before)

    def test_dirty_package_checkout_is_rejected_before_consumer_mutation(self):
        before = (self.consumer / "CONTEXT.src.md").read_bytes()
        (self.package_root / "CONTEXT.src.md").write_text(
            (self.package_root / "CONTEXT.src.md").read_text(encoding="utf-8") + "\n<!-- dirty -->\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ContextCanonError, "uncommitted changes"):
            adopt_source_package(self.consumer, self.package_root)
        self.assertEqual((self.consumer / "CONTEXT.src.md").read_bytes(), before)
        self.assertFalse((self.consumer / ".context/sources" / self.v2.package_digest).exists())

    def test_structural_conflict_is_rejected_before_install_or_authoring_change(self):
        source = self.consumer / "CONTEXT.src.md"
        source.write_text(
            CONSUMER
            + "\n## Rules\n\n### Local\n\n"
            + "- **Collision:** Local rule deliberately collides with the Source visible ID.\n"
            + "  Why: Exercise prospective composition validation.\n"
            + '  <!-- ctx:rule id="PY-001" -->\n',
            encoding="utf-8",
        )
        before = source.read_bytes()
        with self.assertRaisesRegex(ContextCanonError, "Visible Rule ID collision"):
            adopt_source_package(self.consumer, self.package_root)
        self.assertEqual(source.read_bytes(), before)
        self.assertFalse((self.consumer / ".context/sources" / self.v2.package_digest).exists())


if __name__ == "__main__":
    unittest.main()
''', encoding="utf-8")


def patch_docs() -> None:
    replace_once(
        "nodes/internal/framework-development/docs/external-sources.md",
        "Transport metadata is used for **updates of an already accepted pinned Source**. Initial selection/addition of reusable Sources is handled by the reviewed first-adoption onboarding path: the semantic reviewer may propose an `existing-source`, but final acceptance requires the exact immutable package identity the reviewer saw. A transport locator never bypasses review or exact package binding.\n\nThe larger real-project onboarding test still needs to validate how natural this Source-selection/reuse experience feels in practice.",
        "Transport metadata is used for **updates of an already accepted pinned Source**. Initial onboarding may select reusable Sources through its reviewed placement path. Normal post-onboarding work also has one explicit first-adoption command when the human already knows the exact published package to compose:\n\n```text\ncontextcanon source adopt <published-package-node> --node <consumer-node>\n```\n\n`source adopt` is the first-adoption decision itself; it is not an update shortcut. ContextCanon loads and verifies the exact package, requires its package path to be clean in Git, records the repository origin, exact current commit and Node path, validates the consumer's complete prospective composition in memory, installs the immutable package locally, then atomically adds one normal Source declaration. It does not touch or rewrite historical onboarding acceptance. If the same Source identity is already present with a different package, adoption refuses and the existing fetch/review/accept update path remains mandatory. Repeating adoption of the exact same package is idempotent.\n\nA transport locator never bypasses exact package binding. This command is especially useful when a reusable Source is deliberately added after onboarding or when an old migration run lost a pre-`run-inputs.json` owner choice: recovery becomes a new explicit owner decision instead of pretending lost historical state can be inferred."
    )
    replace_once(
        "nodes/internal/framework-development/docs/external-sources.md",
        "## Fetch, review, accept\n",
        "## First adoption after onboarding\n\nWhen a reusable published Node is not yet a Source of the consumer, adoption is intentionally one explicit operation followed by the ordinary build/check loop:\n\n```text\ncontextcanon source adopt <published-package-node> --node <consumer-node>\ncontextcanon build <consumer-node>\ncontextcanon check <consumer-node>\n```\n\nThis is appropriate only for **first adoption** of an exact package the operator has deliberately selected. Subsequent changes to that Source use the reviewable update loop below.\n\n## Fetch, review, accept\n"
    )


def complete() -> None:
    replace_once(
        "PLAN.md",
        "**Status: ACTIVE — step 3 of 4.**",
        "**Status: ACTIVE — step 4 of 4.**",
    )
    replace_once(
        "PLAN.md",
        "- [ ] 3. Provide a safe explicit recovery/re-adoption path for a reusable owner Source whose legacy onboarding choice is no longer present in machine state, without replaying the already accepted placement review.",
        "- [x] 3. Provide a safe explicit recovery/re-adoption path for a reusable owner Source whose legacy onboarding choice is no longer present in machine state, without replaying the already accepted placement review.",
    )
    state = Path("STATE.md")
    state.write_text(
        state.read_text(encoding="utf-8").rstrip()
        + "\n\n## Latest Block S explicit Source re-adoption checkpoint\n\n"
        + "A reusable Source that is genuinely absent from old machine/onboarding state is no longer treated as reconstructible history. `contextcanon source adopt <package-node> --node <consumer>` provides a normal post-onboarding first-adoption action: it fully verifies the exact published package, requires a clean Git package path, freezes origin/exact HEAD/node-path provenance, validates the future consumer composition before mutation, installs the immutable package, and atomically adds one ordinary Source declaration. Historical placement acceptance remains unchanged. Exact repeat adoption is idempotent; an existing Source identity with different package state is refused so updates stay on fetch/review/accept. This gives the real ai-workstation a safe way to explicitly re-adopt the Development Workflow at the root without replaying its 58 accepted placement decisions. Block S proceeds to the combined real-machine upgrade proof with Source plus Parent chain and offline descendant context.\n",
        encoding="utf-8",
    )


def apply() -> None:
    patch_git_transport()
    patch_sources()
    patch_cli()
    patch_tests()
    patch_docs()


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--complete":
        complete()
    elif len(sys.argv) == 1:
        apply()
    else:
        raise SystemExit("usage: _block_s_machine_state_step3.py [--complete]")
