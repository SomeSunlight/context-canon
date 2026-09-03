from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from contextcanon.compiler import Compiler
from contextcanon.onboarding_placement import PLACEMENT_PROPOSAL_SCHEMA, load_onboarding_placement_proposal
from contextcanon.onboarding_placement_publish import build_placement_publication_preview, publish_placement_review
from contextcanon.onboarding_placement_review import create_or_load_placement_review, load_placement_review
from contextcanon.onboarding_structure import STRUCTURE_PROPOSAL_SCHEMA, create_or_load_structure_markdown, load_structure_markdown, load_onboarding_structure_proposal
from contextcanon.outputs import write_outputs
from contextcanon.sources import adopt_source_package, accept_parent_candidate, review_parent_candidate
from tests.test_onboarding_placement import OnboardingPlacementTests


PARENT_BLOCK_RE = re.compile(
    r"\n## (?:Parent Context Node|Parent)\n\n<!-- contextcanon-placement-parent:start -->\n.*?\n<!-- contextcanon-placement-parent:end -->\n?(?=\n## |\Z)",
    re.DOTALL,
)

REAL_NODES = (
    ("N-001", "AI Workstation", ".", None, "aea56adf-2a26-43f0-b712-3bbeab7a3097"),
    ("N-002", "Bootstrap", "bootstrap", "N-001", "f78265e4-e023-4d7a-9b26-9a917ef68a4a"),
    ("N-003", "Windows and WSL bootstrap", "bootstrap/windows", "N-002", "a46c5141-dcdf-4f28-9839-4053a02e04cf"),
    ("N-004", "Linux bootstrap", "bootstrap/linux", "N-002", "1e85ca79-6021-4b66-ae0c-4da90f78d6e9"),
    ("N-005", "Ansible host configuration", "bootstrap/ansible", "N-002", "ad9cbb59-ae04-4290-9c53-5d70cfefe434"),
    ("N-006", "aiw operator interface", "bin", "N-001", "6417ee7c-a9d0-40c7-ada3-6762d4a3900b"),
    ("N-007", "Application runtimes", "compose", "N-001", "90dd976e-8753-495b-a631-d708b13878d1"),
    ("N-008", "Goose", "compose/goose", "N-007", "3fd2ae4e-d712-4232-917a-7059b03a3cd4"),
    ("N-009", "Open WebUI", "compose/open-webui", "N-007", "dbf13d04-e686-4cda-9434-c439e23bb400"),
)

EXPECTED_PARENT_KEYS = {
    ("N-002", "N-001"),
    ("N-003", "N-002"),
    ("N-004", "N-002"),
    ("N-005", "N-002"),
    ("N-006", "N-001"),
    ("N-007", "N-001"),
    ("N-008", "N-007"),
    ("N-009", "N-007"),
}


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


WORKFLOW_SOURCE = '''# Development Workflow — Local Context Source
<!-- ctx:node id="c4c94726-3cc7-4df6-b779-72bbf9c06f40" version="0.2.0-draft" -->

## Rules

### Human review gate

- **Do not merge without explicit project-owner approval:** Keep a review PR open until the project owner explicitly approves the reviewed result.
  Why: Automation does not decide product acceptance.
  <!-- ctx:rule id="CCW-006" -->

## Topics

### Executing a development block

When planning or reviewing a coherent development block:

Required:
- Resource: `docs/change-workflow.md`
<!-- ctx:topic id="CCW-TOPIC-CHANGE-WORKFLOW" -->
'''

WORKFLOW_RESOURCE = "# Change workflow\n\nKeep changes recoverable, reviewed, and explicitly accepted.\n"


class RealAiWorkstationParentMigrationTests(unittest.TestCase):
    """Regression fixture distilled from the owner's current ai-workstation onboarding.

    The frozen production workspace has this nine-Node hierarchy, including the
    later-added bootstrap/ansible Node. The full 139 KiB human review is not
    embedded here; this fixture keeps the exact hierarchy/Node identities and
    enough local Rules to prove scoped transitive visibility after migration.
    """

    def make_case(self):
        helper = OnboardingPlacementTests()
        repo, prepared, workspace, readme, architecture, _, _ = helper.make_case()

        structure_raw = {
            "schema": STRUCTURE_PROPOSAL_SCHEMA,
            "evidence_digest": prepared.evidence_digest,
            "nodes": [
                {
                    "key": key,
                    "name": name,
                    "parent_key": parent,
                    "suggested_path": path,
                    "lifecycle": "current",
                    "purpose": f"Real ai-workstation regression fixture for {name}.",
                    "rationale": "Preserve the owner-reviewed production hierarchy.",
                    "confidence": "high",
                    "evidence": [{
                        "path": "README.md",
                        "sha256": readme.sha256,
                        "start_line": 1,
                        "end_line": 4,
                    }],
                }
                for key, name, path, parent, _ in REAL_NODES
            ],
            "knowledge_bodies": [],
            "source_reuses": [],
        }
        workspace.structure_proposal_path.write_text(json.dumps(structure_raw, indent=2), encoding="utf-8")
        workspace.structure_path.unlink(missing_ok=True)
        create_or_load_structure_markdown(
            prepared.snapshot_root,
            workspace.structure_proposal_path,
            workspace.structure_path,
        )

        # Materialize the production Node identities as the pre-Parent authored
        # state. Filesystem nesting by itself must still carry no semantics.
        for _, name, rel, _, node_id in REAL_NODES:
            node = repo if rel == "." else repo / rel
            node.mkdir(parents=True, exist_ok=True)
            (node / "CONTEXT.src.md").write_text(
                f"# {name} — Local Context Source\n"
                f'<!-- ctx:node id="{node_id}" version="0.1.0-draft" -->\n\n'
                "## Overview\n\n"
                f"Legacy parentless onboarding content for {name}.\n",
                encoding="utf-8",
            )

        for _, _, rel, _, _ in sorted(REAL_NODES, key=lambda item: len(Path(item[2]).parts)):
            node = repo if rel == "." else repo / rel
            write_outputs(Compiler(repo).compile(node))

        structure_proposal = load_onboarding_structure_proposal(
            workspace.structure_proposal_path, prepared.snapshot_root
        )
        structure = load_structure_markdown(workspace.structure_path, structure_proposal)
        statements = (
            ("P-001", "N-001", "AI Workstation root policy."),
            ("P-002", "N-002", "Bootstrap policy."),
            ("P-003", "N-005", "Ansible host policy."),
            ("P-004", "N-007", "Application runtime policy."),
            ("P-005", "N-008", "Goose policy."),
            ("P-006", "N-009", "Open WebUI policy."),
        )
        raw = {
            "schema": PLACEMENT_PROPOSAL_SCHEMA,
            "evidence_digest": prepared.evidence_digest,
            "structure_digest": structure.structure_digest,
            "items": [
                {
                    "id": item_id,
                    "title": statement.rstrip("."),
                    "kind": "rule",
                    "action": "promote",
                    "destination_node_key": destination,
                    "rationale": "Minimal durable rule used to prove real-tree visibility.",
                    "confidence": "high",
                    "evidence": [{
                        "path": "README.md",
                        "sha256": readme.sha256,
                        "start_line": 1,
                        "end_line": 1,
                    }],
                    "payload": {
                        "statement": statement,
                        "why": "Prove semantic Parent scope on the real hierarchy.",
                        "wording_origin": "synthesized",
                    },
                }
                for item_id, destination, statement in statements
            ],
            "source_edits": [],
            "source_reuses": [],
        }
        workspace.placement_proposal_path.write_text(json.dumps(raw, indent=2), encoding="utf-8")
        proposal = load_onboarding_placement_proposal(
            workspace.placement_proposal_path,
            prepared.snapshot_root,
            workspace.structure_proposal_path,
            workspace.structure_path,
        )
        review, created = create_or_load_placement_review(
            workspace.placement_path, proposal, prepared.snapshot_root
        )
        self.assertTrue(created)
        workspace.placement_path.write_text(
            workspace.placement_path.read_text(encoding="utf-8").replace(
                "Decision: `pending`", "Decision: `accept`"
            ),
            encoding="utf-8",
        )
        review = load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)
        self.assertTrue(review.is_complete)
        return repo, prepared, workspace, proposal, review

    def make_legacy_publication(self):
        repo, prepared, workspace, proposal, review = self.make_case()
        preview = build_placement_publication_preview(
            proposal,
            review,
            prepared.snapshot_root,
            project_root=repo,
        )
        self.assertEqual(
            {(parent.child_key, parent.parent_key) for parent in preview.parents},
            EXPECTED_PARENT_KEYS,
        )

        # Recreate the exact class of production state that existed before R5:
        # reviewed placement content is published, but Parent blocks/packages do
        # not yet exist.
        for delta in preview.nodes:
            legacy = PARENT_BLOCK_RE.sub("\n", delta.after).rstrip() + "\n"
            delta.source_path.write_text(legacy, encoding="utf-8")

        for _, _, rel, _, _ in sorted(REAL_NODES, key=lambda item: len(Path(item[2]).parts)):
            node = repo if rel == "." else repo / rel
            write_outputs(Compiler(repo).compile(node))

        nodes = {}
        for delta in preview.nodes:
            compiled = Compiler(repo).compile(delta.source_path.parent)
            nodes[delta.key] = {
                "node_id": compiled.metadata.id,
                "path": delta.path,
                "normalized_digest": compiled.normalized_digest,
                "package_digest": compiled.package_digest,
                "source_sha256": _sha(delta.source_path.read_bytes()),
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
        acceptance.write_text(
            json.dumps(legacy_acceptance, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return repo, prepared, workspace, proposal, review, acceptance

    def publish_workflow_package(self, repo: Path):
        workflow = repo / "nodes/library/development-workflow"
        docs = workflow / "docs"
        docs.mkdir(parents=True, exist_ok=True)
        (workflow / "CONTEXT.src.md").write_text(WORKFLOW_SOURCE, encoding="utf-8")
        (docs / "change-workflow.md").write_text(WORKFLOW_RESOURCE, encoding="utf-8")
        compiled = Compiler(repo).compile(workflow)
        write_outputs(compiled)

        subprocess.run(["git", "-C", str(repo), "config", "user.email", "contextcanon@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.name", "ContextCanon Tests"], check=True)
        remote = subprocess.run(
            ["git", "-C", str(repo), "remote", "get-url", "origin"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if remote.returncode != 0:
            subprocess.run(
                ["git", "-C", str(repo), "remote", "add", "origin", "https://example.test/context-canon.git"],
                check=True,
            )
        subprocess.run(["git", "-C", str(repo), "add", "--", "nodes/library/development-workflow"], check=True)
        subprocess.run(
            ["git", "-C", str(repo), "commit", "-qm", "Publish Development Workflow package"],
            check=True,
        )
        return workflow, compiled

    @staticmethod
    def _node_depths():
        by_key = {key: (rel, parent) for key, _, rel, parent, _ in REAL_NODES}
        cache = {}

        def depth(key):
            if key in cache:
                return cache[key]
            parent = by_key[key][1]
            cache[key] = 0 if parent is None else depth(parent) + 1
            return cache[key]

        return {key: depth(key) for key in by_key}

    def test_real_nine_node_legacy_tree_migrates_all_expected_parent_edges(self):
        repo, prepared, _, proposal, review, acceptance = self.make_legacy_publication()

        preview = build_placement_publication_preview(
            proposal,
            review,
            prepared.snapshot_root,
            project_root=repo,
        )
        self.assertEqual(len(preview.parents), 8)
        self.assertEqual(
            {(parent.child_key, parent.parent_key) for parent in preview.parents},
            EXPECTED_PARENT_KEYS,
        )

        publish_placement_review(
            preview,
            review,
            snapshot_root=prepared.snapshot_root,
            acceptance_path=acceptance,
        )
        migrated = json.loads(acceptance.read_text(encoding="utf-8"))
        self.assertEqual(len(migrated["parents"]), 8)

        for key, _, rel, parent_key, _ in REAL_NODES:
            node = repo if rel == "." else repo / rel
            text = (node / "CONTEXT.src.md").read_text(encoding="utf-8")
            if parent_key is None:
                self.assertNotIn("ctx:parent", text)
            else:
                self.assertIn("ctx:parent", text, key)
                compiled = Compiler(repo).compile(node)
                self.assertIsNotNone(compiled.parent_package, key)

        goose = Compiler(repo).compile(repo / "compose" / "goose")
        goose_rules = {rule.statement for rule in (*goose.inherited_rules, *goose.local_rules)}
        self.assertEqual(
            goose_rules,
            {"AI Workstation root policy.", "Application runtime policy.", "Goose policy."},
        )

        ansible = Compiler(repo).compile(repo / "bootstrap" / "ansible")
        ansible_rules = {rule.statement for rule in (*ansible.inherited_rules, *ansible.local_rules)}
        self.assertEqual(
            ansible_rules,
            {"AI Workstation root policy.", "Bootstrap policy.", "Ansible host policy."},
        )

        open_webui = Compiler(repo).compile(repo / "compose" / "open-webui")
        open_webui_rules = {rule.statement for rule in (*open_webui.inherited_rules, *open_webui.local_rules)}
        self.assertEqual(
            open_webui_rules,
            {"AI Workstation root policy.", "Application runtime policy.", "Open WebUI policy."},
        )

        second = build_placement_publication_preview(
            proposal,
            review,
            prepared.snapshot_root,
            project_root=repo,
        )
        self.assertTrue(all(not delta.changed for delta in second.nodes))

    def test_real_pre_parent_pre_source_upgrade_carries_workflow_offline_to_scoped_descendants(self):
        repo, prepared, _, proposal, review, acceptance = self.make_legacy_publication()

        # 1. Migrate the exact untouched historical placement first. The legacy
        # acceptance byte hashes are the safety proof for this one-time Parent
        # publication, so later ordinary authoring must not be smuggled through it.
        preview = build_placement_publication_preview(
            proposal,
            review,
            prepared.snapshot_root,
            project_root=repo,
        )
        publish_placement_review(
            preview,
            review,
            snapshot_root=prepared.snapshot_root,
            acceptance_path=acceptance,
        )
        parent_migration_acceptance = acceptance.read_bytes()

        # 2. Explicitly re-adopt the reusable Development Workflow at the Root
        # as a new post-onboarding owner decision. Historical placement remains
        # unchanged and direct children stay on their previous Parent snapshots.
        workflow_root, workflow = self.publish_workflow_package(repo)
        adopted, changed = adopt_source_package(repo, workflow_root)
        self.assertTrue(changed)
        self.assertEqual(adopted.package_digest, workflow.package_digest)
        self.assertEqual(acceptance.read_bytes(), parent_migration_acceptance)

        root = Compiler(repo).compile(repo)
        self.assertIn("Do not merge without explicit project-owner approval", {r.title for r in root.inherited_rules})
        compose_before = Compiler(repo).compile(repo / "compose")
        self.assertNotIn("CCW-006", {r.id for r in compose_before.inherited_rules})

        # 3. Non-live Parent semantics require deliberate top-down propagation.
        # Each edge reviews/accepts the current live Parent snapshot; children at
        # the next depth then inherit an already accepted upstream snapshot.
        depths = self._node_depths()
        for key, _, rel, parent_key, _ in sorted(
            REAL_NODES,
            key=lambda item: (depths[item[0]], item[2], item[0]),
        ):
            if parent_key is None:
                continue
            child = repo / rel
            diff, receipt = review_parent_candidate(child)
            self.assertTrue(receipt.is_file(), key)
            self.assertFalse(diff.is_empty, key)
            accepted_parent = accept_parent_candidate(child)
            self.assertEqual(accepted_parent.metadata.id, next(node_id for k, _, _, _, node_id in REAL_NODES if k == parent_key))

        # Parent updates are ordinary post-onboarding evolution too; they must
        # not rewrite the historical placement acceptance record.
        self.assertEqual(acceptance.read_bytes(), parent_migration_acceptance)

        goose = Compiler(repo).compile(repo / "compose/goose")
        goose_rule_ids = {rule.id for rule in (*goose.inherited_rules, *goose.local_rules)}
        goose_statements = {rule.statement for rule in (*goose.inherited_rules, *goose.local_rules)}
        self.assertIn("CCW-006", goose_rule_ids)
        self.assertEqual(
            goose_statements,
            {
                "Keep a review PR open until the project owner explicitly approves the reviewed result.",
                "AI Workstation root policy.",
                "Application runtime policy.",
                "Goose policy.",
            },
        )
        self.assertIn("CCW-TOPIC-CHANGE-WORKFLOW", {topic.id for topic in goose.inherited_topics})
        workflow_resource = (
            "CONTEXT/references/c4c94726-3cc7-4df6-b779-72bbf9c06f40/"
            "nodes/library/development-workflow/docs/change-workflow.md"
        )
        self.assertEqual(goose.resources[workflow_resource], WORKFLOW_RESOURCE.encode("utf-8"))

        ansible = Compiler(repo).compile(repo / "bootstrap/ansible")
        ansible_rule_ids = {rule.id for rule in (*ansible.inherited_rules, *ansible.local_rules)}
        ansible_statements = {rule.statement for rule in (*ansible.inherited_rules, *ansible.local_rules)}
        self.assertIn("CCW-006", ansible_rule_ids)
        self.assertEqual(
            ansible_statements,
            {
                "Keep a review PR open until the project owner explicitly approves the reviewed result.",
                "AI Workstation root policy.",
                "Bootstrap policy.",
                "Ansible host policy.",
            },
        )

        # 4. Remove both the original reusable Node and the Root's direct Source
        # package. A deep leaf still compiles from its own accepted direct Parent
        # package, proving the complete effective workflow travelled through the
        # immutable Parent chain rather than via a live Source checkout.
        shutil.rmtree(workflow_root)
        shutil.rmtree(repo / ".context/sources" / workflow.package_digest)
        offline_goose = Compiler(repo).compile(repo / "compose/goose")
        self.assertIn("CCW-006", {rule.id for rule in offline_goose.inherited_rules})
        self.assertEqual(offline_goose.resources[workflow_resource], WORKFLOW_RESOURCE.encode("utf-8"))
        self.assertEqual(acceptance.read_bytes(), parent_migration_acceptance)


if __name__ == "__main__":
    unittest.main()
