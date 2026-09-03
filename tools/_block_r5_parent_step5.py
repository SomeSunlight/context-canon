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


def patch_publish() -> None:
    anchor = "\ndef publish_placement_review(\n"
    helper = r'''
def _legacy_parent_acceptance_upgrade(
    content: bytes | None,
    preview: PlacementPublicationPreview,
) -> bool:
    """Recognize the one safe in-place upgrade from pre-Parent placement acceptance.

    The legacy acceptance must be the exact same reviewed placement and every
    Node source byte it certified must still be current. This is deliberately
    narrower than general acceptance replacement: post-publication human edits
    require a fresh explicit workflow rather than being swept into migration.
    """

    if content is None:
        return False
    try:
        raw = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return False
    if not isinstance(raw, dict) or "parents" in raw:
        return False
    identity = {
        "evidence_digest": preview.evidence_digest,
        "structure_digest": preview.structure_digest,
        "proposal_digest": preview.proposal_digest,
        "review_digest": preview.review_digest,
    }
    if any(raw.get(key) != value for key, value in identity.items()):
        return False
    if raw.get("schema") != PLACEMENT_ACCEPTANCE_SCHEMA:
        return False

    nodes = raw.get("nodes")
    if not isinstance(nodes, dict):
        raise _error("legacy placement acceptance has no verifiable Node state for Parent migration")
    by_key = {delta.key: delta for delta in preview.nodes}
    missing = sorted(set(by_key) - set(nodes))
    if missing:
        raise _error(
            "legacy placement acceptance does not cover every accepted structure Node needed for automatic Parent migration: "
            + ", ".join(missing)
        )
    for key, delta in by_key.items():
        state = nodes.get(key)
        if not isinstance(state, dict):
            raise _error(f"legacy placement acceptance Node state is invalid for {key}")
        expected_source = state.get("source_sha256")
        current_source = _sha256_bytes(delta.before.encode("utf-8"))
        if state.get("node_id") != delta.node_id or state.get("path") != delta.path:
            raise _error(f"legacy placement acceptance Node identity changed for {key}; refuse automatic Parent migration")
        if expected_source != current_source:
            raise _error(
                f"{delta.name} changed after the legacy placement acceptance; refuse automatic Parent migration and review the current Node explicitly"
            )
    return True

'''
    p = Path("src/contextcanon/onboarding_placement_publish.py")
    text = p.read_text(encoding="utf-8")
    if anchor not in text:
        raise SystemExit("publish legacy acceptance insertion anchor missing")
    p.write_text(text.replace(anchor, helper + anchor, 1), encoding="utf-8")

    replace_once(
        "src/contextcanon/onboarding_placement_publish.py",
        "    acceptance_before = acceptance_path.read_bytes() if acceptance_path.is_file() else None\n\n    try:\n",
        "    acceptance_before = acceptance_path.read_bytes() if acceptance_path.is_file() else None\n    legacy_parent_upgrade = _legacy_parent_acceptance_upgrade(acceptance_before, preview)\n\n    try:\n",
    )
    replace_once(
        "src/contextcanon/onboarding_placement_publish.py",
        '''        if acceptance_path.is_file() and acceptance_path.read_bytes() != encoded:\n            raise _error(\n                f"placement acceptance record already exists with different exact content: {acceptance_path}"\n            )\n        _atomic_write(acceptance_path, encoded)\n''',
        '''        if acceptance_path.is_file() and acceptance_path.read_bytes() != encoded and not legacy_parent_upgrade:\n            raise _error(\n                f"placement acceptance record already exists with different exact content: {acceptance_path}"\n            )\n        if not acceptance_path.is_file() or acceptance_path.read_bytes() != encoded:\n            _atomic_write(acceptance_path, encoded)\n''',
    )


def patch_reset() -> None:
    old = '''    if argv[1] == "placement-publish":\n        extra_paths = tuple(\n            entry.path for entry in load_evidence_snapshot(snapshot).entries if entry.path.lower().endswith(".md")\n        )\n'''
    new = '''    if argv[1] == "placement-publish":\n        extras = [\n            entry.path for entry in load_evidence_snapshot(snapshot).entries if entry.path.lower().endswith(".md")\n        ]\n        acceptance = snapshot / "placement-acceptance.json"\n        if "--acceptance" in argv:\n            index = argv.index("--acceptance")\n            if index + 1 < len(argv):\n                acceptance = Path(argv[index + 1]).resolve()\n        try:\n            extras.append(acceptance.resolve().relative_to(project).as_posix())\n        except ValueError:\n            # An explicitly external acceptance path remains outside project reset scope.\n            pass\n        extra_paths = tuple(extras)\n'''
    replace_once("src/contextcanon/onboarding_reset.py", old, new)


def write_tests() -> None:
    test = r'''from __future__ import annotations

import hashlib
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from contextcanon.cli import main
from contextcanon.compiler import Compiler
from contextcanon.onboarding_placement_publish import build_placement_publication_preview, publish_placement_review
from contextcanon.onboarding_reset import reset_onboarding, run_journaled
from contextcanon.outputs import write_outputs
from contextcanon.parser import ContextCanonError
from contextcanon.sources import install_source_package
from tests.test_onboarding_placement_publish import PlacementPublicationTests


PARENT_BLOCK_RE = re.compile(
    r"\n?<!-- contextcanon-placement-parent:start -->\n.*?\n<!-- contextcanon-placement-parent:end -->\n?",
    re.DOTALL,
)


def sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


class LegacyParentMigrationTests(unittest.TestCase):
    def make_legacy_publication(self):
        helper = PlacementPublicationTests()
        repo, prepared, workspace, source_root, proposal, review, _ = helper.make_case()
        preview = build_placement_publication_preview(
            proposal,
            review,
            prepared.snapshot_root,
            catalog_package_roots=[source_root],
            project_root=repo,
        )

        # Materialize exactly the old placement semantics: reviewed local
        # content and Source reuse, but no semantic Parent blocks/packages.
        for delta in preview.nodes:
            legacy = PARENT_BLOCK_RE.sub("\n", delta.after).rstrip() + "\n"
            delta.source_path.write_text(legacy, encoding="utf-8")
        for document in preview.documents:
            document.source_path.write_text(document.after, encoding="utf-8")
        install_source_package(repo, source_root)

        compiled_nodes = {}
        for delta in preview.nodes:
            compiled = Compiler(repo).compile(delta.source_path.parent)
            write_outputs(compiled)
            compiled_nodes[delta.key] = compiled

        nodes = {}
        for delta in preview.nodes:
            compiled = Compiler(repo).compile(delta.source_path.parent)
            nodes[delta.key] = {
                "node_id": compiled.metadata.id,
                "path": delta.path,
                "normalized_digest": compiled.normalized_digest,
                "package_digest": compiled.package_digest,
                "source_sha256": sha(delta.source_path.read_bytes()),
            }
        legacy_acceptance = {
            "schema": "contextcanon/onboarding-placement-acceptance/v1",
            "evidence_digest": preview.evidence_digest,
            "structure_digest": preview.structure_digest,
            "proposal_digest": preview.proposal_digest,
            "review_digest": preview.review_digest,
            "nodes": nodes,
            "sources": [],
            "followups": [],
            "source_edits": [],
            "documents": [],
        }
        acceptance = prepared.snapshot_root / "placement-acceptance.json"
        encoded = (json.dumps(legacy_acceptance, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
        acceptance.write_bytes(encoded)
        return repo, prepared, workspace, source_root, proposal, review, acceptance, encoded

    def test_legacy_published_tree_migrates_idempotently_and_reset_restores_old_acceptance(self):
        repo, prepared, workspace, source_root, proposal, review, acceptance, legacy_bytes = self.make_legacy_publication()
        child = repo / "compose" / "goose"
        legacy_child = (child / "CONTEXT.src.md").read_bytes()

        preview = build_placement_publication_preview(
            proposal, review, prepared.snapshot_root,
            catalog_package_roots=[source_root], project_root=repo,
        )
        self.assertEqual(len(preview.parents), 1)
        self.assertTrue(any(delta.changed for delta in preview.nodes))

        args = [
            "onboard", "placement-publish", str(prepared.snapshot_root),
            "--catalog-package", str(source_root), "--project", str(repo),
        ]
        self.assertEqual(run_journaled(args, main), 0)
        migrated = json.loads(acceptance.read_text(encoding="utf-8"))
        self.assertEqual(len(migrated["parents"]), 1)
        child_text = (child / "CONTEXT.src.md").read_text(encoding="utf-8")
        self.assertIn("ctx:parent", child_text)
        child_compiled = Compiler(repo).compile(child)
        self.assertIsNotNone(child_compiled.parent_package)
        parent_store = child / ".context" / "sources" / child_compiled.parent_package.package_digest
        self.assertTrue(parent_store.is_dir())

        second = build_placement_publication_preview(
            proposal, review, prepared.snapshot_root,
            catalog_package_roots=[source_root], project_root=repo,
        )
        self.assertTrue(all(not delta.changed for delta in second.nodes))
        second_result = publish_placement_review(
            second, review, snapshot_root=prepared.snapshot_root,
            catalog_package_roots=[source_root], acceptance_path=acceptance,
        )
        self.assertEqual(acceptance.read_bytes(), (json.dumps(migrated, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"))
        self.assertTrue(second_result.acceptance_digest)

        reset = reset_onboarding(prepared.snapshot_root, from_step=9)
        self.assertGreaterEqual(reset["journal_records_reversed"], 1)
        self.assertEqual((child / "CONTEXT.src.md").read_bytes(), legacy_child)
        self.assertEqual(acceptance.read_bytes(), legacy_bytes)
        self.assertFalse(parent_store.exists())
        restored_child = Compiler(repo).compile(child)
        self.assertIsNone(restored_child.parent_package)

    def test_legacy_acceptance_with_later_child_edit_refuses_automatic_parent_migration(self):
        repo, prepared, _, source_root, proposal, review, acceptance, legacy_bytes = self.make_legacy_publication()
        child = repo / "compose" / "goose"
        source = child / "CONTEXT.src.md"
        source.write_text(source.read_text(encoding="utf-8") + "\n<!-- later human edit -->\n", encoding="utf-8")
        before = source.read_bytes()
        preview = build_placement_publication_preview(
            proposal, review, prepared.snapshot_root,
            catalog_package_roots=[source_root], project_root=repo,
        )
        with self.assertRaisesRegex(ContextCanonError, "changed after the legacy placement acceptance"):
            publish_placement_review(
                preview, review, snapshot_root=prepared.snapshot_root,
                catalog_package_roots=[source_root], acceptance_path=acceptance,
            )
        self.assertEqual(source.read_bytes(), before)
        self.assertEqual(acceptance.read_bytes(), legacy_bytes)


if __name__ == "__main__":
    unittest.main()
'''
    Path("tests/test_parent_migration.py").write_text(test, encoding="utf-8")


def patch_docs() -> None:
    p = Path("nodes/internal/framework-development/docs/onboarding-reference.md")
    text = p.read_text(encoding="utf-8").rstrip()
    addition = '''\n\n## Upgrading a placement published before semantic Parent edges\n\nA placement accepted by an older ContextCanon build may already contain the reviewed Nodes and Sources while its Step-03 hierarchy was not yet persisted as semantic Parent pins. Re-running the same exact placement preview/publication is the migration path; no new semantic LLM pass is required.\n\nContextCanon allows this acceptance upgrade only when the old record is the same Evidence/Structure/Proposal/Review identity, has no Parent state yet, covers every accepted structure Node, and every current `CONTEXT.src.md` still has the exact `source_sha256` recorded by that old acceptance. The migration then adds the reviewed Parent blocks/packages parent-first and replaces the acceptance record transactionally. A later human Node edit disables automatic migration and requires explicit review instead.\n\nStep-9 reset journals the placement acceptance file together with Node sources, generated outputs and immutable package-store changes. Reset after such a migration therefore restores both the pre-Parent Node tree and its exact legacy acceptance record rather than leaving machine acceptance ahead of canonical source.\n'''
    if "## Upgrading a placement published before semantic Parent edges" not in text:
        p.write_text(text + addition, encoding="utf-8")


def complete() -> None:
    replace_once(
        "PLAN.md",
        "**Status: ACTIVE — R5 Semantic Parent relationship, step 5 of 5. Fast-run remains ACTIVE.**",
        "**Status: ACTIVE — R6 reusable Source update discovery UX, step 1 of 3. Fast-run remains ACTIVE.**",
    )
    replace_once(
        "PLAN.md",
        "- [ ] 5. Cover migration/idempotency/recovery for an already-published `ai-workstation`-like tree, then run the focused tests, complete suite, self-hosted build/check and hygiene gate.",
        "- [x] 5. Cover migration/idempotency/recovery for an already-published `ai-workstation`-like tree, then run the focused tests, complete suite, self-hosted build/check and hygiene gate.",
    )
    marker = "Expected practical result: when working inside a subsystem, an agent can start at that subsystem's Node and receive the accepted higher-level context through the semantic Parent chain without loading unrelated sibling context."
    replace_once(
        "PLAN.md",
        marker,
        marker + "\n\nCheckpoint: R5 is complete. Step-03 hierarchy is persisted as exact non-live Parent packages; Parent updates are candidate/review/accept only; full Rules/Topics/Resources flow transitively while siblings stay out; and a pre-Parent published placement can migrate idempotently only from its exact unchanged accepted Node bytes, with Step-9 reset restoring the prior acceptance and package state.",
    )
    state = Path("STATE.md")
    text = state.read_text(encoding="utf-8").rstrip() + "\n\n## Latest Block R5 complete semantic-Parent checkpoint\n\nBlock R5 is complete. The accepted Step-03 hierarchy is now durable package semantics rather than a review-only tree: non-root Nodes pin exact Parent packages, ordinary builds are non-live, Parent changes require explicit review/accept, reusable Sources and complete effective Rules/Topics/Resources flow through the Parent chain without sibling leakage, and already-published pre-Parent placements have a narrow exact-byte migration path with idempotent republish and Step-9 recovery of the prior acceptance/package state. The next Block R work is R6 Source-update discovery UX.\n"
    state.write_text(text, encoding="utf-8")


def apply() -> None:
    patch_publish()
    patch_reset()
    write_tests()
    patch_docs()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--complete":
        complete()
    else:
        apply()
