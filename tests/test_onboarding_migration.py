from __future__ import annotations

from dataclasses import replace
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
from contextcanon.onboarding_migration import migrate_onboarding, _copy_binary, _retire_file, _receipt_path
from contextcanon.onboarding_proposal import load_evidence_snapshot
from contextcanon.onboarding_reusable_contexts import load_accepted_reusable_contexts
from contextcanon.onboarding_reset import reset_onboarding
from contextcanon.onboarding_storage import ACTIVE_MARKER, RUN_MARKER, default_workspace, package_files, provenance_path, scope_root
from contextcanon.onboarding_workspace import OnboardingWorkspace, _snapshot_label
from contextcanon.onboarding_handoff import handoff_relative_paths
from contextcanon.onboarding_storage import HANDOFF_MARKER, handoff_path
from contextcanon.parser import ContextCanonError
from contextcanon.version_store import library_root
import tests.test_onboarding_relationships as relationships


class OnboardingMigrationTests(unittest.TestCase):
    def case(self, *, subtree=False, stage=7, custom=False):
        helper = relationships.OnboardingRelationshipTests()
        self.addCleanup(helper.doCleanups)
        case = helper.make_case(subtree=subtree)
        repo, project, prepared, workspace, structure, catalog = case
        accepted = helper.accept_imports(case, [("Project (.)", "Workflow", "parent"), ("Project (.)", "Knowledge", "reference")])
        if stage >= 8:
            helper.placement(case)
        if stage >= 12:
            helper.publish(case)
        old = project / ".context/onboarding" / prepared.evidence_digest
        old.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(prepared.snapshot_root, old)
        (old / RUN_MARKER).unlink()
        for root, package in zip(accepted.catalog_roots, accepted.catalog_packages):
            destination = old / "reusable-context-packages" / package.package_digest
            for rel, data in package_files(root, package).items():
                path = destination / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
            provenance = provenance_path(prepared.snapshot_root, package).read_bytes()
            (destination / ".context/onboarding-provenance.json").write_bytes(provenance)
        old_workspace = project / ("custom-review" if custom else "contextcanon-onboarding")
        if workspace.root != old_workspace:
            shutil.copytree(workspace.root, old_workspace)
            shutil.rmtree(workspace.root)
        for step in (4, 8):
            central = handoff_path(project, prepared.evidence_digest, step)
            if central.exists():
                relative, relative_zip = handoff_relative_paths(step)
                shutil.copytree(central, old_workspace / relative)
                (old_workspace / relative / HANDOFF_MARKER).unlink()
                shutil.copy2(central.with_suffix(".zip"), old_workspace / relative_zip)
                shutil.rmtree(central)
                central.with_suffix(".zip").unlink()
        plan = old_workspace / "PLAN.md"
        text = plan.read_text().replace(_snapshot_label(prepared.snapshot_root), _snapshot_label(old))
        if workspace.root != old_workspace:
            text = text.replace(str(workspace.root), str(old_workspace))
        plan.write_text(text, encoding="utf-8")
        shutil.rmtree(prepared.snapshot_root)
        return helper, (repo, project, replace(prepared, snapshot_root=old), OnboardingWorkspace(old_workspace), structure, catalog), accepted

    def snapshot(self, root):
        return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file() and ".git" not in p.relative_to(root).parts}

    def test_preview_is_read_only_and_acceptance_survives_offline_for_root_and_subtree(self):
        for subtree in (False, True):
            with self.subTest(subtree=subtree):
                helper, case, accepted = self.case(subtree=subtree, stage=8)
                repo, project, prepared, workspace, structure, catalog = case
                shutil.rmtree(catalog)
                before = self.snapshot(repo)
                result = migrate_onboarding(project)
                self.assertEqual(self.snapshot(repo), before)
                self.assertFalse(_receipt_path(project).exists())
                human = workspace.reusable_contexts_path.read_bytes()
                proposal = workspace.placement_proposal_path.read_bytes()
                handoff = {rel: data for rel, data in self.snapshot(workspace.root).items() if rel.startswith("handoffs/")}
                result = migrate_onboarding(project, apply=True)
                new, visible = Path(result["snapshot"]), OnboardingWorkspace(Path(result["workspace"]))
                self.assertFalse(prepared.snapshot_root.exists())
                self.assertEqual(project_root_from_snapshot(new), project)
                self.assertEqual(load_evidence_snapshot(new).evidence_digest, prepared.evidence_digest)
                self.assertEqual(visible.reusable_contexts_path.read_bytes(), human)
                self.assertEqual(visible.placement_proposal_path.read_bytes(), proposal)
                for step in (4, 8):
                    relative, relative_zip = handoff_relative_paths(step)
                    retained = handoff_path(project, prepared.evidence_digest, step)
                    for rel, data in handoff.items():
                        if rel.startswith(relative + "/"):
                            self.assertEqual((retained / rel[len(relative) + 1:]).read_bytes(), data)
                        elif rel == relative_zip:
                            self.assertEqual(retained.with_suffix(".zip").read_bytes(), data)
                loaded = load_accepted_reusable_contexts(visible.reusable_contexts_path, new, prepared.evidence_digest, structure)
                self.assertEqual(loaded.review_digest, accepted.review_digest)
                self.assertEqual([a.relationship for a in loaded.assignments], ["parent", "reference"])
                self.assertTrue(all(root.parent == library_root(repo) for root in loaded.catalog_roots))
                migrated_case = repo, project, replace(prepared, snapshot_root=new), visible, structure, catalog
                helper.publish(migrated_case)
                self.assertEqual(migrate_onboarding(project, apply=True)["status"], "complete")

    def test_completed_receipt_does_not_overwrite_later_human_edits(self):
        _, case, _ = self.case()
        repo, project, prepared, workspace, _, _ = case
        result = migrate_onboarding(project, apply=True)
        path = Path(result["workspace"]) / "STEP-07-reusable-contexts.md"
        path.write_bytes(path.read_bytes() + b"\nLater human note.\n")
        before = self.snapshot(repo)
        migrate_onboarding(project, apply=True)
        self.assertEqual(self.snapshot(repo), before)

    def test_stale_review_remains_stale_and_unrelated_prose_not_rewritten(self):
        _, case, accepted = self.case()
        _, project, prepared, workspace, structure, _ = case
        path = workspace.reusable_contexts_path
        path.write_bytes(path.read_bytes() + ("\nHuman note: " + str(prepared.snapshot_root) + "\n").encode())
        human = path.read_bytes()
        result = migrate_onboarding(project, apply=True)
        new = Path(result["snapshot"])
        moved = Path(result["workspace"]) / path.name
        self.assertEqual(moved.read_bytes(), human)
        state = json.loads((new / "reusable-contexts.json").read_text())
        self.assertEqual(state["review_digest"], accepted.review_digest)
        with self.assertRaisesRegex(ContextCanonError, "changed after validation"):
            load_accepted_reusable_contexts(moved, new, prepared.evidence_digest, structure)

    def test_publication_journal_reset_restores_acceptance_and_retains_shared_versions(self):
        _, case, _ = self.case(subtree=True, stage=12)
        repo, project, prepared, _, _, _ = case
        acceptance = (prepared.snapshot_root / "placement-acceptance.json").read_bytes()
        journal_path = prepared.snapshot_root / "onboarding-reset-journal.json"
        journal = json.loads(journal_path.read_text())
        old_locator = (prepared.snapshot_root / "placement-acceptance.json").relative_to(project).as_posix()
        for record in journal["records"]:
            for change in record["changes"]:
                if change["path"] == "@run/placement-acceptance.json":
                    change["path"] = old_locator
        journal_path.write_text(json.dumps(journal), encoding="utf-8")
        versions = self.snapshot(library_root(repo))
        result = migrate_onboarding(project, apply=True)
        new = Path(result["snapshot"])
        self.assertEqual((new / "placement-acceptance.json").read_bytes(), acceptance)
        reset_onboarding(project, from_step=12)
        self.assertFalse((new / "placement-acceptance.json").exists())
        self.assertEqual(self.snapshot(library_root(repo)), versions)
        self.assertEqual(len(Compiler(repo).compile(project).parsed.sources), 0)

    def test_copy_and_retirement_interruptions_resume_without_losing_decisions(self):
        for phase in ("copy", "retire"):
            with self.subTest(phase=phase):
                _, case, _ = self.case(subtree=True, stage=8)
                _, project, prepared, workspace, _, _ = case
                human = workspace.reusable_contexts_path.read_bytes()
                calls = []
                def interrupted(*args):
                    calls.append(args)
                    if len(calls) == 3:
                        raise OSError("simulated interruption")
                    return (_copy_binary if phase == "copy" else _retire_file)(*args)
                with patch("contextcanon.onboarding_migration." + ("_copy_binary" if phase == "copy" else "_retire_file"), interrupted):
                    with self.assertRaisesRegex(OSError, "interruption"):
                        migrate_onboarding(project, apply=True)
                result = migrate_onboarding(project, apply=True)
                self.assertEqual(result["status"], "complete")
                self.assertEqual((Path(result["workspace"]) / workspace.reusable_contexts_path.name).read_bytes(), human)
                reset_onboarding(project, from_step=7)
                self.assertFalse((Path(result["snapshot"]) / "reusable-contexts.json").exists())

    def test_root_in_place_plan_copy_interruption_and_activation_interruption_resume(self):
        for boundary in ("plan", "activation"):
            with self.subTest(boundary=boundary):
                _, case, _ = self.case(stage=8)
                _, project, _, _, _, _ = case
                if boundary == "plan":
                    def after_plan(path, data):
                        _copy_binary(path, data)
                        if path.name == "PLAN.md":
                            raise OSError("after PLAN")
                    target, replacement = "_copy_binary", after_plan
                else:
                    target, replacement = "_write_marker", lambda *args: (_ for _ in ()).throw(OSError("before activation"))
                with patch("contextcanon.onboarding_migration." + target, replacement):
                    with self.assertRaises(OSError):
                        migrate_onboarding(project, apply=True)
                self.assertEqual(migrate_onboarding(project, apply=True)["status"], "complete")

    def test_foreign_files_packages_destinations_and_symlinks_refuse_before_mutation(self):
        for kind in ("run", "workspace", "package", "destination", "symlink"):
            with self.subTest(kind=kind):
                _, case, _ = self.case(subtree=True)
                repo, project, prepared, workspace, _, _ = case
                if kind == "run":
                    (prepared.snapshot_root / "owner-note.txt").write_bytes(b"Mine")
                elif kind == "workspace":
                    (workspace.root / "owner-note.txt").write_bytes(b"Mine")
                elif kind == "package":
                    root = next((prepared.snapshot_root / "reusable-context-packages").iterdir())
                    (root / "extra.txt").write_bytes(b"Mine")
                elif kind == "destination":
                    preview = migrate_onboarding(project)
                    path = Path(preview["snapshot"]) / "foreign.txt"
                    path.parent.mkdir(parents=True)
                    path.write_bytes(b"Mine")
                else:
                    path = prepared.snapshot_root / "evidence/README.md"
                    original = repo / "original.md"
                    original.write_bytes(path.read_bytes())
                    path.unlink()
                    try:
                        path.symlink_to(original)
                    except OSError:
                        continue  # Windows runner can restrict symlink creation.
                before = self.snapshot(repo)
                with self.assertRaises(ContextCanonError):
                    migrate_onboarding(project, apply=True)
                self.assertEqual(self.snapshot(repo), before)

    def test_custom_workspace_unchanged_and_historical_runs_protected_by_activation(self):
        _, case, _ = self.case(subtree=True, custom=True)
        repo, project, prepared, workspace, _, _ = case
        historical = prepared.snapshot_root.with_name("a" * 64)
        historical.mkdir()
        (historical / "owner-marker").write_bytes(b"Older run; leave alone")
        result = migrate_onboarding(project, workspace=workspace.root, apply=True)
        self.assertEqual(Path(result["workspace"]), workspace.root)
        self.assertEqual(default_workspace(project), workspace.root)
        self.assertNotEqual(scope_root(project), project / ".context/onboarding")
        reset_onboarding(project, from_step=1)
        self.assertEqual((historical / "owner-marker").read_bytes(), b"Older run; leave alone")
        self.assertEqual(scope_root(project) / ACTIVE_MARKER, Path(result["snapshot"]).parent / ACTIVE_MARKER)
        prepared_new = prepare_onboarding_evidence(project)
        self.assertNotEqual(prepared_new.snapshot_root.parent, project / ".context/onboarding")

    def test_activation_inventory_and_scope_git_visible_but_receipt_and_payload_ignored(self):
        _, case, _ = self.case(subtree=True)
        repo, project, prepared, workspace, _, _ = case
        csv = workspace.root / "STEP-02-inventory.csv"
        csv.write_bytes(b"path,description\nREADME.md,Reviewed\n")
        old_scope = prepared.snapshot_root.parent
        (old_scope / "inventory-state.json").write_text(json.dumps({"schema": "contextcanon/onboarding-inventory-state/v0", "csv_path": "contextcanon-onboarding/STEP-02-inventory.csv"}), encoding="utf-8")
        (old_scope / "inventory-acceptance.json").write_text(json.dumps({"schema": "contextcanon/onboarding-inventory-acceptance/v0", "evidence_digest": prepared.evidence_digest, "inventory_path": str(csv), "inventory_sha256": hashlib.sha256(csv.read_bytes()).hexdigest()}), encoding="utf-8")
        result = migrate_onboarding(project, apply=True)
        new = Path(result["snapshot"])
        for path, ignored in ((new.parent / ACTIVE_MARKER, False), (new.parent / "inventory-acceptance.json", False),
                              (new / "manifest.json", True), (_receipt_path(project), True)):
            actual = subprocess.run(["git", "-C", str(repo), "check-ignore", str(path)], capture_output=True)
            self.assertEqual(actual.returncode == 0, ignored, str(path))
        state = json.loads((new.parent / "inventory-state.json").read_text())
        self.assertEqual(Path(state["csv_path"]), Path(result["workspace"]) / csv.name)

    def test_missing_exact_frozen_bytes_never_substitutes_new_provider(self):
        _, case, _ = self.case()
        repo, project, prepared, workspace, _, catalog = case
        shutil.rmtree(prepared.snapshot_root / "reusable-context-packages")
        shutil.rmtree(library_root(repo))
        shutil.rmtree(catalog)
        before = self.snapshot(repo)
        with self.assertRaises(ContextCanonError):
            migrate_onboarding(project, apply=True)
        self.assertEqual(self.snapshot(repo), before)

    def test_receipt_cannot_retire_an_unrelated_project_file(self):
        _, case, _ = self.case(subtree=True)
        repo, project, _, _, _, _ = case
        with patch("contextcanon.onboarding_migration._retire_file", side_effect=OSError("stop")):
            with self.assertRaises(OSError):
                migrate_onboarding(project, apply=True)
        sentinel = project / "owner.md"
        sentinel.write_bytes(b"Owner")
        path = _receipt_path(project)
        value = json.loads(path.read_text())
        value["retire"].append({"path": sentinel.relative_to(repo).as_posix(), "sha256": hashlib.sha256(b"Owner").hexdigest()})
        path.write_text(json.dumps(value), encoding="utf-8")
        with self.assertRaisesRegex(ContextCanonError, "escapes"):
            migrate_onboarding(project, apply=True)
        self.assertEqual(sentinel.read_bytes(), b"Owner")

    def test_windows_final_and_staging_budgets_are_checked_in_read_only_preview(self):
        _, case, _ = self.case(subtree=True)
        repo, project, _, _, _, _ = case
        before = self.snapshot(repo)
        with patch("contextcanon.path_budget._windows", return_value=True):
            preview = migrate_onboarding(project)
            migrate_onboarding(project, apply=True)
        new = Path(preview["snapshot"])
        self.assertEqual(len(new.relative_to(repo).parts), 4)
        self.assertFalse(new / "reusable-context-packages" in new.parents)
        self.assertTrue(before)

    def test_old_handoff_retains_parent_after_provider_source_removed(self):
        _, case, _ = self.case(subtree=True, stage=8)
        repo, project, prepared, workspace, _, _ = case
        record = json.loads((prepared.snapshot_root / "enclosing-parent.json").read_text())
        (prepared.snapshot_root / "enclosing-parent.json").unlink()
        (repo / "CONTEXT.src.md").unlink()
        before = self.snapshot(repo)
        preview = migrate_onboarding(project)
        self.assertEqual(self.snapshot(repo), before)
        result = migrate_onboarding(project, apply=True)
        actual = json.loads((Path(result["snapshot"]) / "enclosing-parent.json").read_text())
        self.assertEqual(actual["binding"], record["binding"])
        self.assertEqual(actual["node_path"], ".")

    def test_post_activation_human_edits_survive_interrupted_retirement_retry(self):
        _, case, _ = self.case(subtree=True, stage=8)
        _, project, _, workspace, _, _ = case
        with patch("contextcanon.onboarding_migration._retire_file", side_effect=OSError("stop")):
            with self.assertRaises(OSError):
                migrate_onboarding(project, apply=True)
        path = default_workspace(project) / workspace.reusable_contexts_path.name
        path.write_bytes(path.read_bytes() + b"\nLater decision.\n")
        before = path.read_bytes()
        self.assertEqual(migrate_onboarding(project, apply=True)["status"], "complete")
        self.assertEqual(path.read_bytes(), before)

    def test_migration_survives_relocated_checkout_and_restores_from_step10(self):
        _, case, _ = self.case(subtree=True, stage=8)
        repo, project, _, workspace, _, _ = case
        with patch("contextcanon.onboarding_migration._retire_file", side_effect=OSError("stop")):
            with self.assertRaises(OSError):
                migrate_onboarding(project, apply=True)
        moved = repo.with_name("moved-repository")
        repo.rename(moved)
        project = moved / project.relative_to(repo)
        self.assertEqual(migrate_onboarding(project, apply=True)["status"], "complete")
        self.assertEqual(default_workspace(project).parent, moved)
        reset_onboarding(project, from_step=10)
        self.assertTrue((default_workspace(project) / workspace.reusable_contexts_path.name).exists())
