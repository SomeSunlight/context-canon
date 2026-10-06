from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from contextcanon.compiler import Compiler
from contextcanon.onboarding import prepare_onboarding_evidence, project_root_from_snapshot
from contextcanon.onboarding_proposal import load_evidence_snapshot
from contextcanon.onboarding_reset import _restore_change, record_transition, reset_onboarding, run_journaled
from contextcanon.onboarding_storage import (
    RUN_MARKER, SCOPE_MARKER, default_workspace, enclosing_parent,
    freeze_package, provenance_path, scope_root,
)
from contextcanon.onboarding_reusable_contexts import load_accepted_reusable_contexts
from contextcanon.onboarding_structure_instruction import build_onboarding_structure_instruction
from contextcanon.onboarding_placement_instruction import build_onboarding_placement_instruction
from contextcanon.onboarding_workspace import open_inventory_workspace, open_onboarding_workspace
from contextcanon.package import compiled_package, load_package
from contextcanon.outputs import write_outputs
from contextcanon.outputs import expected_outputs
from contextcanon.parser import ContextCanonError
from contextcanon.version_store import library_root
import tests.test_onboarding_relationships as relationships
import tests.test_version_store as versions


class OnboardingStorageTests(unittest.TestCase):
    def repo(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        repo = Path(temporary.name).resolve()
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        return repo

    def project(self, repo, relative):
        project = repo / relative
        project.mkdir(parents=True, exist_ok=True)
        (project / "README.md").write_text("# Project\nFrozen knowledge.\n", encoding="utf-8")
        return project

    def fixture(self, *, subtree=False):
        helper = relationships.OnboardingRelationshipTests()
        self.addCleanup(helper.doCleanups)
        return helper, helper.make_case(subtree=subtree)

    def test_deep_scopes_keep_payload_and_workspace_overhead_at_repository_root(self):
        repo = self.repo()
        project = self.project(repo, "/".join(["nested-project"] * 7))
        with patch("contextcanon.path_budget._windows", return_value=True):
            prepared = prepare_onboarding_evidence(project)
        relative = prepared.snapshot_root.relative_to(repo)
        self.assertEqual(len(relative.parts), 4)
        self.assertEqual(len(relative.parts[-1]), 16)
        self.assertEqual(project_root_from_snapshot(prepared.snapshot_root), project)
        self.assertEqual(default_workspace(project).parent, repo)
        self.assertEqual(load_evidence_snapshot(prepared.snapshot_root).evidence_digest, prepared.evidence_digest)
        old = project / ".context/onboarding" / prepared.evidence_digest / "manifest.json"
        self.assertGreater(len(str(old)) - len(str(prepared.manifest_path)), 120)

    def test_identical_evidence_isolated_by_project_and_reset_preserves_other_run(self):
        repo = self.repo()
        projects = [self.project(repo, name) for name in ("a", "b")]
        prepared = [prepare_onboarding_evidence(project) for project in projects]
        self.assertEqual(prepared[0].evidence_digest, prepared[1].evidence_digest)
        self.assertNotEqual(prepared[0].snapshot_root, prepared[1].snapshot_root)
        workspaces = [open_inventory_workspace(project) for project in projects]
        (prepared[1].snapshot_root / "run-inputs.json").write_text("other run", encoding="utf-8")
        reset_onboarding(projects[0], from_step=1)
        self.assertTrue(prepared[1].manifest_path.is_file())
        self.assertTrue(workspaces[1].plan_path.is_file())
        self.assertEqual((prepared[1].snapshot_root / "run-inputs.json").read_text(), "other run")

    def test_scope_marker_and_inventory_visible_but_run_and_workspace_ignored(self):
        repo = self.repo()
        project = self.project(repo, "deep/project")
        workspace = open_inventory_workspace(project)
        prepared = prepare_onboarding_evidence(project)
        root = scope_root(project)
        for name in ("inventory-state.json", "inventory-acceptance.json"):
            (root / name).write_text("{}", encoding="utf-8")
        for path, ignored in ((root / SCOPE_MARKER, False), (root / "inventory-state.json", False),
                              (root / "inventory-acceptance.json", False),
                              (prepared.manifest_path, True), (workspace.plan_path, True)):
            result = subprocess.run(["git", "-C", str(repo), "check-ignore", str(path)], capture_output=True)
            self.assertEqual(result.returncode == 0, ignored, str(path))

    def test_run_ownership_tampering_is_rejected(self):
        repo = self.repo()
        project = self.project(repo, "a")
        prepared = prepare_onboarding_evidence(project)
        marker = prepared.snapshot_root / RUN_MARKER
        value = json.loads(marker.read_text())
        value["project_path"] = "../elsewhere"
        marker.write_text(json.dumps(value), encoding="utf-8")
        with self.assertRaisesRegex(ContextCanonError, "Unsafe onboarding project"):
            project_root_from_snapshot(prepared.snapshot_root)

    def test_equal_package_bytes_of_different_nodes_get_distinct_frozen_bindings(self):
        repo = self.repo()
        prepared = prepare_onboarding_evidence(self.project(repo, "project"))
        compiled = []
        for index in range(2):
            provider = repo / f"provider-{index}"
            versions.node(provider, f"identity-{index}")
            value = Compiler(repo).compile(provider)
            write_outputs(value)
            compiled.append((provider, value))
        self.assertEqual(compiled[0][1].package_digest, compiled[1][1].package_digest)
        roots = []
        for provider, value in compiled:
            provenance = {"schema": "contextcanon/onboarding-reusable-package-provenance/v0", "package_digest": value.package_digest}
            roots.append(freeze_package(prepared.snapshot_root, provider, compiled_package(value), provenance))
        self.assertNotEqual(roots[0], roots[1])
        self.assertEqual([load_package(root).metadata.id for root in roots], ["identity-0", "identity-1"])

    def test_reset_refuses_unknown_scope_files_and_keeps_other_project(self):
        repo = self.repo()
        projects = [self.project(repo, name) for name in ("a", "b")]
        prepared = [prepare_onboarding_evidence(project) for project in projects]
        foreign = scope_root(projects[0]) / "owner-notes.txt"
        foreign.write_text("Preserve me.", encoding="utf-8")
        workspace = open_onboarding_workspace(prepared[0].snapshot_root, create=True)
        workspace.reusable_contexts_path.write_text("Pending human decisions.\n", encoding="utf-8")
        before = {path: path.read_bytes() for path in workspace.root.rglob("*") if path.is_file()}
        with self.assertRaisesRegex(ContextCanonError, "unrecognized onboarding state"):
            reset_onboarding(projects[0], from_step=1)
        self.assertEqual(foreign.read_text(), "Preserve me.")
        self.assertTrue(prepared[1].manifest_path.is_file())
        self.assertTrue(all(path.read_bytes() == data for path, data in before.items()))

    def test_project_override_cannot_reset_another_owned_run(self):
        repo = self.repo()
        projects = [self.project(repo, name) for name in ("a", "b")]
        prepared = [prepare_onboarding_evidence(project) for project in projects]
        with self.assertRaisesRegex(ContextCanonError, "belongs to"):
            reset_onboarding(prepared[0].snapshot_root, from_step=1, project_root=projects[1])
        self.assertTrue(all(item.manifest_path.exists() for item in prepared))

    def test_legacy_journal_path_cannot_escape_selected_project(self):
        repo = self.repo()
        project = self.project(repo, "project")
        prepared = prepare_onboarding_evidence(project)
        sentinel = repo / "owner.md"
        sentinel.write_bytes(b"Owner's file.")
        record_transition(prepared.snapshot_root, project, step=12, command=["test"],
                          before={"../owner.md": None}, after={"../owner.md": sentinel.read_bytes()})
        with self.assertRaisesRegex(ContextCanonError, "unsafe reset journal path"):
            reset_onboarding(prepared.snapshot_root, from_step=12)
        self.assertEqual(sentinel.read_bytes(), b"Owner's file.")

    def test_real_scope_collision_extends_locator_and_authenticates_full_scope(self):
        repo = self.repo()
        seen = {}
        pair = None
        for index in range(100):
            name = f"project-{index}"
            prefix = hashlib.sha256(name.encode()).hexdigest()[:1]
            if prefix in seen:
                pair = (seen[prefix], name)
                break
            seen[prefix] = name
        self.assertIsNotNone(pair)
        with patch("contextcanon.onboarding_storage.TOKEN_LENGTHS", (1, 2, 64)):
            roots = [scope_root(self.project(repo, name), create=True) for name in pair]
            self.assertNotEqual(roots[0], roots[1])
            self.assertEqual([len(root.name) for root in roots], [1, 2])
            self.assertEqual(scope_root(repo / pair[0]), roots[0])

    def test_catalog_freeze_shared_exact_bytes_and_provenance_remains_run_owned_offline(self):
        helper, case = self.fixture()
        repo, _, prepared, workspace, structure, catalog = case
        accepted = helper.accept_imports(case, [("Project (.)", "Workflow", "reference")])
        for root, package in zip(accepted.catalog_roots, accepted.catalog_packages):
            self.assertEqual(root.parent, library_root(repo))
            self.assertTrue(provenance_path(prepared.snapshot_root, package).is_file())
            self.assertFalse((root / ".context/onboarding-provenance.json").exists())
        other = prepare_onboarding_evidence(self.project(repo, "other"))
        package = accepted.catalog_packages[0]
        provenance = json.loads(provenance_path(prepared.snapshot_root, package).read_text())
        provenance["locator"] = "another discovery location"
        shared = freeze_package(other.snapshot_root, accepted.catalog_roots[0], package, provenance)
        self.assertEqual(shared, accepted.catalog_roots[0])
        self.assertNotEqual(provenance_path(other.snapshot_root, package).read_bytes(),
                            provenance_path(prepared.snapshot_root, package).read_bytes())
        shutil.rmtree(catalog)
        loaded = load_accepted_reusable_contexts(workspace.reusable_contexts_path, prepared.snapshot_root,
                                                prepared.evidence_digest, structure)
        self.assertEqual(loaded.review_digest, accepted.review_digest)
        self.assertEqual(loaded.catalog_roots, accepted.catalog_roots)
        reset_onboarding(prepared.snapshot_root, from_step=7)
        self.assertTrue(shared.is_dir())
        self.assertTrue(provenance_path(other.snapshot_root, package).is_file())

    def test_frozen_enclosing_parent_survives_provider_edit_and_removal(self):
        helper, case = self.fixture(subtree=True)
        repo, _, prepared, workspace, _, _ = case
        initial_instruction = build_onboarding_structure_instruction(prepared.snapshot_root)
        first = enclosing_parent(prepared.snapshot_root)
        source = repo / "CONTEXT.src.md"
        source.write_text(source.read_text().replace("Apply Enclosing constraints.", "Changed provider."), encoding="utf-8")
        write_outputs(Compiler(repo).compile(repo))
        source.unlink()
        second = enclosing_parent(prepared.snapshot_root)
        self.assertEqual(first[0].package_digest, second[0].package_digest)
        self.assertEqual(first[1], second[1])
        self.assertEqual(build_onboarding_structure_instruction(prepared.snapshot_root).text, initial_instruction.text)
        placement = build_onboarding_placement_instruction(prepared.snapshot_root, workspace.structure_proposal_path, workspace.structure_path)
        self.assertEqual(placement.enclosing_parent_package.package_digest, first[0].package_digest)

    def test_subtree_publication_reset_restores_run_acceptance_and_preserves_shared_versions(self):
        helper, case = self.fixture(subtree=True)
        helper.accept_imports(case, [("Project (.)", "Workflow", "parent"), ("Project (.)", "Knowledge", "reference")])
        repo, project, prepared, _, _, _ = case
        helper.placement(case)
        helper.publish(case)
        acceptance = prepared.snapshot_root / "placement-acceptance.json"
        self.assertTrue(acceptance.exists())
        journal = json.loads((prepared.snapshot_root / "onboarding-reset-journal.json").read_text())
        self.assertTrue(any(change["path"] == "@run/placement-acceptance.json"
                            for record in journal["records"] for change in record["changes"]))
        versions = {path: (path / ".context/package.json").read_bytes() for path in library_root(repo).iterdir() if path.is_dir()}
        reset_onboarding(prepared.snapshot_root, from_step=12)
        self.assertFalse(acceptance.exists())
        self.assertTrue(all((path / ".context/package.json").read_bytes() == data for path, data in versions.items()))
        self.assertEqual(len(Compiler(repo).compile(project).parsed.sources), 0)

    def test_interrupted_reset_resumes_verified_partial_record(self):
        repo = self.repo()
        project = self.project(repo, "project")
        prepared = prepare_onboarding_evidence(project)
        open_onboarding_workspace(prepared.snapshot_root, create=True)
        before = {"one.md": b"old one", "two.md": None}
        after = {"one.md": b"new one", "two.md": b"new two"}
        for rel, data in after.items():
            (project / rel).write_bytes(data)
        record_transition(prepared.snapshot_root, project, step=12, command=["test"], before=before, after=after)
        calls = []
        def interrupted(*args):
            calls.append(args)
            if len(calls) == 2:
                raise OSError("simulated interruption")
            return _restore_change(*args)
        with patch("contextcanon.onboarding_reset._restore_change", interrupted):
            with self.assertRaisesRegex(OSError, "interruption"):
                reset_onboarding(prepared.snapshot_root, from_step=12)
        reset_onboarding(prepared.snapshot_root, from_step=12)
        self.assertEqual((project / "one.md").read_bytes(), b"old one")
        self.assertFalse((project / "two.md").exists())
        self.assertFalse((prepared.snapshot_root / "onboarding-reset-journal.json").exists())

    def test_reset_restores_prior_generated_resource_layout_byte_for_byte(self):
        repo = self.repo()
        versions.node(repo, "11111111-1111-4111-8111-111111111111", topic=True)
        # Reproduce the earlier compiler's full-ID Resource namespace.
        with patch.object(Compiler, "_resource_namespace", staticmethod(lambda identity: identity)), patch("contextcanon.render._resource_namespace", lambda identity: identity):
            legacy = Compiler(repo, legacy_carriers=True).compile(repo)
        write_outputs(legacy)
        before = {repo / rel: (repo / rel).read_bytes() for rel in expected_outputs(legacy) if (repo / rel).is_file()}
        prepared = prepare_onboarding_evidence(repo)
        open_onboarding_workspace(prepared.snapshot_root, create=True)
        def publish(_argv):
            write_outputs(Compiler(repo).compile(repo))
            return 0
        self.assertEqual(run_journaled(["onboard", "placement-publish", str(prepared.snapshot_root)], publish), 0)
        self.assertNotEqual((repo / ".context/package.json").read_bytes(), before[repo / ".context/package.json"])
        reset_onboarding(prepared.snapshot_root, from_step=12)
        self.assertTrue(all(path.is_file() and path.read_bytes() == data for path, data in before.items()))
        expected_context = {path for path in before if repo / "CONTEXT" in path.parents}
        self.assertEqual({path for path in (repo / "CONTEXT").rglob("*") if path.is_file()}, expected_context)

    def test_handoffs_for_identical_evidence_in_two_deep_scopes_are_owned_and_short(self):
        from contextcanon.onboarding_handoff import build_semantic_handoff
        from contextcanon.onboarding_storage import HANDOFF_MARKER
        repo = self.repo()
        projects = [self.project(repo, '/'.join(['level'] * 10) + '/' + name) for name in ('a', 'b')]
        prepared = [prepare_onboarding_evidence(project) for project in projects]
        workspaces = [open_onboarding_workspace(run.snapshot_root, create=True) for run in prepared]
        handoffs = []
        for run, workspace in zip(prepared, workspaces):
            workspace.structure_instruction_path.write_text('# Instruction\nReturn JSON.\n', encoding='utf-8')
            with patch('contextcanon.path_budget._windows', return_value=True):
                handoffs.append(build_semantic_handoff(run.snapshot_root, workspace.root, step=4))
        self.assertEqual(prepared[0].evidence_digest, prepared[1].evidence_digest)
        self.assertNotEqual(handoffs[0].root, handoffs[1].root)
        self.assertEqual(handoffs[0].root.parent, repo / '.context/handoffs')
        self.assertLess(len(str(handoffs[0].root / '.contextcanon-handoff/manifest.json')), 160)
        self.assertTrue((handoffs[0].root / HANDOFF_MARKER).exists())
        reset_onboarding(projects[0], from_step=4)
        self.assertFalse(handoffs[0].root.exists())
        self.assertTrue(handoffs[1].root.exists())
