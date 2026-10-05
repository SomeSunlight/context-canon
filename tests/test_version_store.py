from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from contextcanon.cli import main
from contextcanon.compiler import Compiler
from contextcanon.outputs import check_outputs, write_outputs
from contextcanon.package import artifact_files, compiled_package, load_package
from contextcanon.parser import ContextCanonError
from contextcanon.sources import accept_source_candidate, review_source_candidate
from contextcanon.storage_migration import migrate_versions
from contextcanon.version_history import publish_outputs, version_inventory
from contextcanon.version_store import (accepted_package_path, install_version, library_root,
                                       package_key, scratch_root, store_package, version_path)
from contextcanon.links import local_markdown_targets


def node(root: Path, node_id: str, *, name="Policy", version="1.0.0", statement="Apply policy.", topic=False):
    root.mkdir(parents=True, exist_ok=True)
    text = f'''# {name}
<!-- ctx:node id="{node_id}" name="{name}" version="{version}" -->

## Local Rules

### Policy

- **Policy:** {statement}
  Why: Explicitly accepted governance.
  <!-- ctx:rule id="POLICY" -->
'''
    if topic:
        text += '''
## Local Topics

### Guide
<!-- ctx:topic id="GUIDE" -->
When working:

Required:
- Resource: `docs/guide.md`
  <!-- ctx:resource id="GUIDE-DOC" -->
'''
        (root / "docs").mkdir(exist_ok=True)
        (root / "docs/guide.md").write_text("# Guide\n\n[Details](details.md)\n", encoding="utf-8")
        (root / "docs/details.md").write_text("# Details\n", encoding="utf-8")
    (root / "CONTEXT.src.md").write_text(text, encoding="utf-8")


def consumer(root: Path, package, *, node_id="consumer", relationship="parent"):
    root.mkdir(parents=True, exist_ok=True)
    (root / "CONTEXT.src.md").write_text(f'''# Consumer
<!-- ctx:node id="{node_id}" name="Consumer" version="1.0.0" -->

## Context Imports

- [{package.metadata.name}](../provider) — `{package.metadata.version}` — `relationship={relationship}`
  <!-- ctx:source id="{package.metadata.id}" version="{package.metadata.version}" normalized-digest="{package.normalized_digest}" package-digest="{package.package_digest}" -->
''', encoding="utf-8")


def legacy(root: Path, compiled):
    destination = root / ".context/sources" / compiled.package_digest
    for rel, content in artifact_files(compiled).items():
        path = destination / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    return destination


class VersionStoreTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.repo = Path(temporary.name).resolve()
        (self.repo / ".git").mkdir()

    def provider(self, *, topic=False):
        root = self.repo / "provider"
        node(root, "provider", topic=topic)
        compiled = Compiler(self.repo).compile(root)
        write_outputs(compiled)
        return root, compiled

    def test_one_exact_version_shared_across_children_and_offline(self):
        provider, compiled = self.provider(topic=True)
        package = compiled_package(compiled)
        children = [self.repo / "P1/F1", self.repo / "P1/F2"]
        for index, child in enumerate(children):
            consumer(child, package, node_id=f"child-{index}", relationship="parent" if index == 0 else "reference")
            install_version(child, provider, package)
        self.assertEqual(version_path(children[0], package), version_path(children[1], package))
        self.assertEqual(len(list(library_root(self.repo).iterdir())), 1)
        shutil.rmtree(provider)
        parent = Compiler(self.repo).compile(children[0])
        reference = Compiler(self.repo).compile(children[1])
        self.assertEqual(parent.inherited_rules[0].statement, "Apply policy.")
        self.assertEqual(reference.inherited_rules, [])
        self.assertTrue(reference.resources)
        for child in (parent, reference):
            write_outputs(child)
            self.assertEqual(check_outputs(Compiler(self.repo).compile(child.parsed.root)), [])

    def test_identical_human_bytes_are_not_identical_node_versions(self):
        roots = [self.repo / "a", self.repo / "b"]
        compiled = []
        for index, root in enumerate(roots):
            node(root, f"different-id-{index}")
            value = Compiler(self.repo).compile(root)
            compiled.append(value)
        self.assertEqual(compiled[0].package_digest, compiled[1].package_digest)
        packages = [compiled_package(value) for value in compiled]
        paths = [store_package(library_root(self.repo), package, artifact_files(value), action="test", node_root=self.repo)
                 for package, value in zip(packages, compiled)]
        self.assertNotEqual(paths[0], paths[1])
        self.assertNotEqual(package_key(packages[0]), package_key(packages[1]))
        self.assertEqual([load_package(path).metadata.id for path in paths], ["different-id-0", "different-id-1"])

    def test_real_token_collision_extends_and_tampering_fails(self):
        root = self.repo / "provider"
        seen = {}
        pair = None
        for index in range(40):
            node(root, "provider", version=f"1.0.{index}")
            compiled = Compiler(self.repo).compile(root)
            key = package_key(compiled_package(compiled))
            if key[:1] in seen:
                pair = (seen[key[:1]], compiled)
                break
            seen[key[:1]] = compiled
        self.assertIsNotNone(pair)
        paths = [store_package(library_root(self.repo), compiled_package(value), artifact_files(value),
                               action="test", node_root=self.repo, lengths=(1, 2, 64)) for value in pair]
        self.assertEqual([len(path.name) for path in paths], [1, 2])
        (paths[1] / "CONTEXT.md").write_text("tampered", encoding="utf-8")
        with self.assertRaises(ContextCanonError):
            store_package(library_root(self.repo), compiled_package(pair[1]), artifact_files(pair[1]),
                          action="test", node_root=self.repo, lengths=(1, 2, 64))

    def test_normal_build_retains_local_history_and_is_repeatable(self):
        root = self.repo / "P1"
        node(root, "product")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(["build", str(root)]), 0)
        first = load_package(root)
        node(root, "product", version="2.0.0", statement="New policy.")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(["build", str(root)]), 0)
            self.assertEqual(main(["build", str(root)]), 0)
            self.assertEqual(main(["check", str(root)]), 0)
        entries = version_inventory(self.repo)
        self.assertEqual({entry.package.metadata.version for entry in entries}, {"1.0.0", "2.0.0"})
        self.assertEqual(load_package(version_path(root, first)).rules[0].statement, "Apply policy.")
        self.assertIn("retained history", (library_root(root) / "README.md").read_text(encoding="utf-8"))
        result = io.StringIO()
        with contextlib.redirect_stdout(result):
            self.assertEqual(main(["versions", "list", str(root)]), 0)
        self.assertIn("P1 [current publication]", result.getvalue())

    def test_deep_nodes_have_shallow_shared_storage_and_node_relative_resources(self):
        provider = self.repo.joinpath(*[f"F{index}" for index in range(10)])
        node(provider, "c4c94726-3cc7-4df6-b779-72bbf9c06f40", topic=True)
        compiled = Compiler(self.repo).compile(provider)
        target = compiled.local_topics[0].targets[0].locator
        self.assertEqual(target.split("/")[-2:], ["docs", "guide.md"])
        self.assertEqual(len(target.split("/")[2]), 16)
        self.assertNotIn("F0", target)
        write_outputs(compiled)
        package = compiled_package(compiled)
        for depth in (1, 5, 10):
            child = self.repo.joinpath(*[f"C{index}" for index in range(depth)])
            consumer(child, package, node_id=f"depth-{depth}")
            with patch("contextcanon.path_budget._windows", return_value=True):
                path = install_version(child, provider, package)
            self.assertEqual(path.parent, library_root(self.repo))
            self.assertLess(len(str(path / target).encode("utf-16-le")) // 2, 240)
            self.assertEqual(load_package(path).resource_origins[0].node_id, package.metadata.id)

    def test_resource_closure_keeps_exact_links_and_authenticated_origin(self):
        provider = self.repo / "nodes/library/knowledge"
        node(provider, "very-long-stable-node-identity", topic=True)
        outside = self.repo / "nodes/library/shared"
        outside.mkdir()
        (outside / "asset 𝄞.txt").write_bytes(b"original asset")
        (provider / "docs/details.md").write_text("[Asset](../../shared/asset%20%F0%9D%84%9E.txt)\n", encoding="utf-8")
        compiled = Compiler(self.repo).compile(provider)
        package_root = self.repo / "export"
        for rel, content in artifact_files(compiled).items():
            target = package_root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        package = load_package(package_root)
        for file in package.files:
            if file.path.endswith(".md") and file.path.startswith("CONTEXT/references/"):
                path = package_root / file.path
                for target in local_markdown_targets(path.read_text(encoding="utf-8")):
                    self.assertTrue((path.parent / target).resolve().is_file())
        self.assertIn("nodes/library/shared/asset 𝄞.txt", {origin.repo_path for origin in package.resource_origins})
        origins = package_root / ".context/resource-origins.json"
        origins.write_bytes(origins.read_bytes().replace(b"very-long-stable-node-identity", b"different-origin"))
        with self.assertRaises(ContextCanonError):
            load_package(package_root)

    def migration_case(self):
        provider, compiled = self.provider(topic=True)
        package = compiled_package(compiled)
        children = [self.repo / "P1/F1", self.repo / "P1/F2"]
        old = []
        for index, child in enumerate(children):
            consumer(child, package, node_id=f"child-{index}")
            old.append(legacy(child, compiled))
        shutil.rmtree(provider)
        return package, children, old

    def test_migration_preview_apply_repeat_preserves_pins_and_offline_state(self):
        package, children, old = self.migration_case()
        before = {path.relative_to(self.repo): path.read_bytes() for path in self.repo.rglob("*") if path.is_file()}
        preview = migrate_versions(self.repo)
        after = {path.relative_to(self.repo): path.read_bytes() for path in self.repo.rglob("*") if path.is_file()}
        self.assertEqual(before, after)
        self.assertIn("preview (no changes)", preview)
        migrate_versions(self.repo, apply=True)
        self.assertTrue(all(not path.exists() for path in old))
        self.assertEqual(len(version_inventory(self.repo)), 1)
        for child in children:
            self.assertEqual((child / "CONTEXT.src.md").read_bytes(), before[(child / "CONTEXT.src.md").relative_to(self.repo)])
            self.assertEqual(Compiler(self.repo).compile(child).source_packages[0].package_digest, package.package_digest)
        migrate_versions(self.repo, apply=True)
        self.assertEqual(len(version_inventory(self.repo)), 1)

    def test_migration_resumes_partial_cleanup_and_preserves_changed_trash(self):
        package, children, old = self.migration_case()
        def partial(path, *args, **kwargs):
            (Path(path) / "CONTEXT.md").unlink()
            raise PermissionError("simulated interrupted cleanup")
        with patch("contextcanon.storage_migration.shutil.rmtree", side_effect=partial):
            with self.assertRaises(PermissionError):
                migrate_versions(self.repo, apply=True)
        self.assertEqual(load_package(version_path(children[0], package)).package_digest, package.package_digest)
        self.assertFalse(old[0].exists())
        migrate_versions(self.repo, apply=True)
        self.assertFalse((self.repo / ".context/migration-trash").exists())
        self.assertTrue(all(not path.exists() for path in old))

    def test_migration_refuses_corruption_before_mutation_and_keeps_foreign_files(self):
        package, children, old = self.migration_case()
        (old[0] / "CONTEXT.md").write_text("tampered", encoding="utf-8")
        with self.assertRaises(ContextCanonError):
            migrate_versions(self.repo, apply=True)
        self.assertFalse(library_root(self.repo).exists())
        self.assertTrue(old[1].exists())
        shutil.copyfile(old[1] / "CONTEXT.md", old[0] / "CONTEXT.md")
        foreign = old[0] / "personal-note.txt"
        foreign.write_text("keep", encoding="utf-8")
        migrate_versions(self.repo, apply=True)
        self.assertEqual(foreign.read_text(encoding="utf-8"), "keep")
        self.assertFalse(old[1].exists())
        self.assertEqual(accepted_package_path(children[0], package), version_path(children[0], package))

    def carrier_review_case(self, *, relationship="parent"):
        provider, first = self.provider(topic=True)
        child = self.repo / "P1/F1"
        consumer(child, compiled_package(first), relationship=relationship)
        old = legacy(child, first)
        source = child / "CONTEXT.src.md"
        # Use a real historical carrier URL; unrelated prose is never rewritten.
        before = source.read_text(encoding="utf-8").replace("../provider", ".context/sources/" + first.package_digest + "/CONTEXT.md")
        source.write_bytes((before + "\nUnrelated: .context/sources/" + first.package_digest + "\n").replace("\n", "\r\n").encode("utf-8"))
        node(provider, "provider", version="2.0.0", statement="New policy.", topic=True)
        second = Compiler(self.repo).compile(provider)
        write_outputs(second)
        _diff, receipt = review_source_candidate(child, "provider", provider)
        # A pre-107 receipt remains readable and must survive link migration.
        local_receipt = child / ".context/source-reviews" / (second.package_digest + ".json")
        local_receipt.parent.mkdir(parents=True, exist_ok=True)
        receipt.replace(local_receipt)
        return provider, child, old, source, local_receipt, first, second

    def test_owned_carrier_migration_preserves_exact_pins_and_pending_parent_or_reference_review(self):
        for relationship in ("parent", "reference"):
            with self.subTest(relationship=relationship):
                provider, child, old, source, receipt, first, second = self.carrier_review_case(relationship=relationship)
                before = source.read_bytes()
                stale = receipt.parent / "stale.json"
                record = json.loads(receipt.read_text(encoding="utf-8"))
                record["source_file_sha256"] = "0" * 64
                stale.write_text(json.dumps(record), encoding="utf-8")
                migrate_versions(self.repo, apply=True)
                after = source.read_bytes()
                self.assertFalse(old.exists())
                self.assertIn(b"\r\n", after)
                for field in ("normalized-digest", "package-digest", "relationship"):
                    self.assertEqual(before.split(field.encode())[1].splitlines()[0], after.split(field.encode())[1].splitlines()[0])
                self.assertIn(("Unrelated: .context/sources/" + first.package_digest).encode(), after)
                self.assertEqual(json.loads(stale.read_text(encoding="utf-8"))["source_file_sha256"], "0" * 64)
                self.assertEqual(json.loads(receipt.read_text(encoding="utf-8"))["source_file_sha256"], hashlib.sha256(after).hexdigest())
                accepted = accept_source_candidate(child, "provider", provider)
                self.assertEqual(accepted.package_digest, second.package_digest)
                compiled = Compiler(self.repo).compile(child)
                self.assertEqual(bool(compiled.inherited_rules), relationship == "parent")
                # Fresh independent fixture for the next semantic relationship.
                shutil.rmtree(self.repo / ".context")
                shutil.rmtree(self.repo / "P1")
                shutil.rmtree(provider)

    def test_carrier_migration_resumes_between_source_publication_and_review_rebinding(self):
        provider, child, old, source, receipt, first, second = self.carrier_review_case()
        with patch("contextcanon.storage_migration._rebind_link_reviews", side_effect=PermissionError("interrupted")):
            with self.assertRaises(PermissionError):
                migrate_versions(self.repo, apply=True)
        self.assertTrue(old.exists())
        self.assertIn(b"versions/", source.read_bytes())
        self.assertTrue(list((self.repo / ".context/migration-trash").glob("*.links.json")))
        migrate_versions(self.repo, apply=True)
        self.assertFalse(old.exists())
        self.assertEqual(accept_source_candidate(child, "provider", provider).package_digest, second.package_digest)

    def test_concurrent_publication_reuses_only_a_verified_complete_binding(self):
        provider, compiled = self.provider()
        package = compiled_package(compiled)
        destination = install_version(self.repo, provider, package)
        staged = self.repo / "stage"
        shutil.copytree(destination, staged)
        from contextcanon.version_store import publish_directory
        import errno
        with patch("contextcanon.version_store.os.replace", side_effect=OSError(errno.ENOTEMPTY, "winner already published")):
            publish_directory(staged, destination, package)
        (destination / "CONTEXT.md").write_bytes(b"tampered winner")
        with patch("contextcanon.version_store.os.replace", side_effect=OSError(errno.ENOTEMPTY, "winner already published")):
            with self.assertRaises(ContextCanonError):
                publish_directory(staged, destination, package)

    def test_review_scopes_are_isolated_and_full_owner_is_verified(self):
        a, b = self.repo / "a", self.repo / "b"
        node(a, "owner-a")
        node(b, "owner-b")
        with patch("contextcanon.version_store.identity_token", return_value="collision"):
            scratch_root(a, "parent-reviews", create=True)
            with self.assertRaisesRegex(ContextCanonError, "scope token collision"):
                scratch_root(b, "parent-reviews", create=True)
