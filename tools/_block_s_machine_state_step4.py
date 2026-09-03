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


def patch_real_upgrade_test() -> None:
    p = Path("tests/test_ai_workstation_parent_migration.py")
    text = p.read_text(encoding="utf-8")
    text = text.replace("import re\nimport sys\n", "import re\nimport shutil\nimport subprocess\nimport sys\n", 1)
    text = text.replace(
        "from contextcanon.onboarding_structure import STRUCTURE_PROPOSAL_SCHEMA, create_or_load_structure_markdown, load_structure_markdown, load_onboarding_structure_proposal\nfrom contextcanon.outputs import write_outputs\n",
        "from contextcanon.onboarding_structure import STRUCTURE_PROPOSAL_SCHEMA, create_or_load_structure_markdown, load_structure_markdown, load_onboarding_structure_proposal\nfrom contextcanon.outputs import write_outputs\nfrom contextcanon.sources import adopt_source_package, accept_parent_candidate, review_parent_candidate\n",
        1,
    )

    class_marker = "class RealAiWorkstationParentMigrationTests(unittest.TestCase):\n"
    constants = r'''WORKFLOW_SOURCE = ''' + "'''" + r'''# Development Workflow — Local Context Source
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
''' + "'''" + r'''

WORKFLOW_RESOURCE = "# Change workflow\n\nKeep changes recoverable, reviewed, and explicitly accepted.\n"


'''
    if class_marker not in text:
        raise SystemExit("real upgrade class marker missing")
    text = text.replace(class_marker, constants + class_marker, 1)

    method_marker = "    def test_real_nine_node_legacy_tree_migrates_all_expected_parent_edges(self):\n"
    helper = r'''    def publish_workflow_package(self, repo: Path):
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

'''
    if method_marker not in text:
        raise SystemExit("real upgrade test method marker missing")
    text = text.replace(method_marker, helper + method_marker, 1)

    end_marker = "\n\nif __name__ == \"__main__\":\n"
    test = r'''
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
        self.assertIn("Do not merge without explicit project-owner approval.", {r.title for r in root.inherited_rules})
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
        self.assertIn("CCW-006", goose_rule_ids)
        self.assertIn("P-001", goose_rule_ids)
        self.assertIn("P-004", goose_rule_ids)
        self.assertIn("P-005", goose_rule_ids)
        self.assertNotIn("P-002", goose_rule_ids)
        self.assertNotIn("P-003", goose_rule_ids)
        self.assertNotIn("P-006", goose_rule_ids)
        self.assertIn("CCW-TOPIC-CHANGE-WORKFLOW", {topic.id for topic in goose.inherited_topics})
        workflow_resource = (
            "CONTEXT/references/c4c94726-3cc7-4df6-b779-72bbf9c06f40/"
            "nodes/library/development-workflow/docs/change-workflow.md"
        )
        self.assertEqual(goose.resources[workflow_resource], WORKFLOW_RESOURCE.encode("utf-8"))

        ansible = Compiler(repo).compile(repo / "bootstrap/ansible")
        ansible_rule_ids = {rule.id for rule in (*ansible.inherited_rules, *ansible.local_rules)}
        self.assertIn("CCW-006", ansible_rule_ids)
        self.assertIn("P-001", ansible_rule_ids)
        self.assertIn("P-002", ansible_rule_ids)
        self.assertIn("P-003", ansible_rule_ids)
        self.assertNotIn("P-004", ansible_rule_ids)
        self.assertNotIn("P-005", ansible_rule_ids)

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
'''
    if end_marker not in text:
        raise SystemExit("real upgrade if-main marker missing")
    p.write_text(text.replace(end_marker, test + end_marker, 1), encoding="utf-8")


def patch_docs_and_plan() -> None:
    replace_once(
        "PLAN.md",
        "- [ ] 4. Prove the combined real upgrade shape end-to-end: pre-Parent/pre-Source machine state -> recovered Development Workflow Source at the intended ancestor -> exact Parent chain -> offline scoped descendant context.",
        "- [ ] 4. Prove the combined real upgrade shape end-to-end: pre-Parent/pre-Source machine state -> exact Parent migration -> explicit Development Workflow re-adoption at the root -> top-down reviewed Parent updates -> offline scoped descendant context.",
    )
    replace_once(
        "nodes/internal/framework-development/docs/external-sources.md",
        "This is appropriate only for **first adoption** of an exact package the operator has deliberately selected. Subsequent changes to that Source use the reviewable update loop below.",
        "This is appropriate only for **first adoption** of an exact package the operator has deliberately selected. Subsequent changes to that Source use the reviewable update loop below. If the consumer is an ancestor in a semantic Parent hierarchy, descendants do not change live: review/accept the affected Parent edges from the ancestor downward so each child deliberately advances to a Parent snapshot that already contains the newly adopted Source."
    )


def complete() -> None:
    replace_once(
        "PLAN.md",
        "**Status: ACTIVE — step 4 of 4.**",
        "**Status: COMPLETE — real machine-state upgrade hardening finished.**",
    )
    replace_once(
        "PLAN.md",
        "- [ ] 4. Prove the combined real upgrade shape end-to-end: pre-Parent/pre-Source machine state -> exact Parent migration -> explicit Development Workflow re-adoption at the root -> top-down reviewed Parent updates -> offline scoped descendant context.",
        "- [x] 4. Prove the combined real upgrade shape end-to-end: pre-Parent/pre-Source machine state -> exact Parent migration -> explicit Development Workflow re-adoption at the root -> top-down reviewed Parent updates -> offline scoped descendant context.",
    )
    replace_once(
        "PLAN.md",
        "**Status: DEFERRED — known defect, not a blocker for the current end-to-end `ai-workstation` run.** Do not reopen the current placement reasoning pass merely to solve this compatibility edge case.\n\n- [ ] Add a regression starting from a legacy/in-flight workspace where the owner Source exists only in the older human/PLAN state and `run-inputs.json` has no owner choice.\n- [ ] Make legacy PLAN-only owner Source values migrate into snapshot-owned machine run state before reset/recreation can remove the last human artifact that contains the choice.\n- [ ] Decide whether recreating Step 7 with an exact Source catalog but a previously expected owner choice that cannot be recovered should emit a visible warning instead of silently rendering `No reusable Source is currently proposed or owner-selected.`\n- [ ] Verify both paths: a fresh onboarding started with current ContextCanon and an upgraded in-flight onboarding that began before run-input persistence existed.\n\nLive reproduction: the real `ai-workstation` snapshot still renders `No reusable Source is currently proposed or owner-selected.` after `reset --from 7`, even after the correction that consumes remembered owner specs when they are present. This strongly indicates a migration/recovery gap in the older in-flight snapshot state rather than a failure of the current fresh-run persistence path.\n\nFast-run decision: continue the vertical onboarding through human review, publication preview and publication. Revisit this block with another project or a dedicated compatibility test rather than extending the current correction loop.",
        "**Status: RESOLVED BY BLOCK S — do not invent owner history that no longer exists.**\n\nThe supplied real `ai-workstation` machine state proved the stronger legacy case: the former Development Workflow choice can be absent from `STEP-07`, placement acceptance, run state, Source store, and reset journal simultaneously. There is then no exact historical package choice left to migrate safely. Block S therefore replaces hidden reconstruction with an explicit normal owner action: `contextcanon source adopt` re-adopts a deliberately selected exact current package without replaying placement, while fresh/current onboarding continues to persist owner-selected Sources normally. The combined real-tree regression proves subsequent top-down Parent propagation and offline descendant use."
    )
    state = Path("STATE.md")
    state.write_text(
        state.read_text(encoding="utf-8").rstrip()
        + "\n\n## Latest Block S complete real machine-state upgrade checkpoint\n\n"
        + "Block S is complete against a compact regression distilled from the owner's supplied `ai-workstation` machine state. The exact nine authored Node identities produce eight semantic Parent edges; compiler-0.4 generated-Resource feedback is removed; a genuinely lost legacy owner Source is recovered only through explicit normal `source adopt`, not invented historical state; and the combined upgrade is proven end-to-end. The safe order is: migrate the still-byte-exact legacy placement to Parent pins first, explicitly adopt the current Development Workflow package at the root, then review/accept Parent updates top-down. Goose and Ansible receive the workflow plus only their own ancestor/local project context, siblings remain excluded, and a deep leaf still compiles with the workflow Resource after both the original reusable Node checkout and the root's direct Source package are removed. Historical placement acceptance remains byte-stable through ordinary Source adoption and Parent updates. PR #13 remains draft/unmerged pending explicit owner approval.\n",
        encoding="utf-8",
    )


def apply() -> None:
    patch_real_upgrade_test()
    patch_docs_and_plan()


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--complete":
        complete()
    elif len(sys.argv) == 1:
        apply()
    else:
        raise SystemExit("usage: _block_s_machine_state_step4.py [--complete]")
