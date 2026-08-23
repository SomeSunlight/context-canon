from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from contextcanon.compiler import Compiler
from contextcanon.package import PACKAGE_MANIFEST_PATH, artifact_files, load_package
from contextcanon.parser import ContextCanonError


FOUNDATION = '''# Demo Foundation — Local Context Source
<!-- ctx:node id="node-foundation" version="1.0.0" -->

## Rules

### Policy

- **Keep behavior stable:** Preserve the original behavior.
  Why: Consumers rely on this contract.
  <!-- ctx:rule id="F-001" -->

- **Keep legacy marker:** Preserve the legacy marker.
  Why: This fixture exercises transitive removal provenance.
  <!-- ctx:rule id="F-002" -->
'''

TEAM = '''# Demo Team Standard — Local Context Source
<!-- ctx:node id="node-team" version="2.0.0" -->

## Sources

- [Demo Foundation](../foundation/) — `1.0.0`
  <!-- ctx:source id="node-foundation" version="1.0.0" -->

## Rules

### Team

- **Keep team output explicit:** Emit deterministic team output.
  Why: The standalone package must preserve local Rule detail too.
  <!-- ctx:rule id="T-001" -->

## Changes

### Override

- `Demo Foundation / F-001` — Keep behavior stable
  New rule: Preserve the reviewed behavior.
  Why: The team has accepted the reviewed contract.
  <!-- ctx:change op="override" source-id="node-foundation" rule-id="F-001" -->

### Remove

- `Demo Foundation / F-002` — Keep legacy marker
  Why: The team no longer uses the legacy marker.
  <!-- ctx:change op="remove" source-id="node-foundation" rule-id="F-002" -->

## Topics

### Team guide

When working on team-specific output:

Required:
- Resource: `../../docs/team-guide.md`
<!-- ctx:topic id="TEAM-GUIDE" -->
'''


class CompiledPackageTests(unittest.TestCase):
    def make_repo(self) -> Path:
        root = Path(tempfile.mkdtemp())
        (root / ".git").mkdir()
        (root / "docs").mkdir()
        (root / "docs/team-guide.md").write_text("# Team Guide\n\nUse the reviewed contract.\n", encoding="utf-8")
        foundation = root / "nodes/foundation"
        team = root / "nodes/team"
        foundation.mkdir(parents=True)
        team.mkdir(parents=True)
        (foundation / "CONTEXT.src.md").write_text(FOUNDATION, encoding="utf-8")
        (team / "CONTEXT.src.md").write_text(TEAM, encoding="utf-8")
        return root

    def compile_team(self, root: Path):
        compiler = Compiler(root)
        foundation = compiler.compile(root / "nodes/foundation")
        team = compiler.compile(root / "nodes/team")
        return foundation, team

    def write_artifact(self, compiled) -> Path:
        root = Path(tempfile.mkdtemp())
        for rel, content in artifact_files(compiled).items():
            destination = root / rel
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)
        return root

    def test_roundtrip_loads_complete_compiled_state_without_source_repository(self):
        repo = self.make_repo()
        foundation, team = self.compile_team(repo)
        artifact = self.write_artifact(team)
        foundation_normalized = foundation.normalized_digest
        foundation_package = foundation.package_digest

        shutil.rmtree(repo)
        loaded = load_package(artifact)

        self.assertEqual(loaded.metadata.id, "node-team")
        self.assertEqual(loaded.metadata.version, "2.0.0")
        self.assertEqual(loaded.normalized_digest, team.normalized_digest)
        self.assertEqual(loaded.package_digest, team.package_digest)

        self.assertEqual(len(loaded.sources), 1)
        self.assertEqual(loaded.sources[0].id, "node-foundation")
        self.assertEqual(loaded.sources[0].normalized_digest, foundation_normalized)
        self.assertEqual(loaded.sources[0].package_digest, foundation_package)

        self.assertEqual([rule.id for rule in loaded.rules], ["F-001", "T-001"])
        inherited = next(rule for rule in loaded.rules if rule.id == "F-001")
        self.assertEqual(inherited.origin_node_id, "node-foundation")
        self.assertEqual(inherited.group, "Policy")
        self.assertEqual(inherited.statement, "Preserve the reviewed behavior.")
        self.assertEqual(inherited.why, "Consumers rely on this contract.")
        self.assertEqual([mod.node_id for mod in inherited.modifications], ["node-team"])
        self.assertEqual(inherited.modifications[0].why, "The team has accepted the reviewed contract.")

        self.assertEqual(len(loaded.removed_rules), 1)
        self.assertEqual(loaded.removed_rules[0].rule_id, "F-002")
        self.assertEqual(loaded.removed_rules[0].removed_by_node_id, "node-team")
        self.assertEqual([topic.id for topic in loaded.topics], ["TEAM-GUIDE"])
        self.assertIn("CONTEXT/references/docs/team-guide.md", [file.path for file in loaded.files])

    def test_manifest_is_deterministic_for_equivalent_compiles(self):
        first_repo = self.make_repo()
        second_repo = self.make_repo()
        _, first = self.compile_team(first_repo)
        _, second = self.compile_team(second_repo)

        self.assertEqual(first.normalized_digest, second.normalized_digest)
        self.assertEqual(first.package_digest, second.package_digest)
        self.assertEqual(first.package_manifest, second.package_manifest)

    def test_tampered_semantic_manifest_fails_normalized_digest_verification(self):
        repo = self.make_repo()
        _, team = self.compile_team(repo)
        artifact = self.write_artifact(team)
        manifest_path = artifact / PACKAGE_MANIFEST_PATH
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        rule = next(rule for rule in payload["rules"] if rule["id"] == "F-001")
        rule["statement"] = "Tampered semantic statement."
        manifest_path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")

        with self.assertRaisesRegex(ContextCanonError, "normalized digest mismatch"):
            load_package(artifact)

    def test_tampered_human_package_file_fails_file_verification(self):
        repo = self.make_repo()
        _, team = self.compile_team(repo)
        artifact = self.write_artifact(team)
        (artifact / "CONTEXT.md").write_text("tampered\n", encoding="utf-8")

        with self.assertRaisesRegex(ContextCanonError, "package file mismatch"):
            load_package(artifact)

    def test_missing_materialized_resource_fails_exact_file_set_verification(self):
        repo = self.make_repo()
        _, team = self.compile_team(repo)
        artifact = self.write_artifact(team)
        (artifact / "CONTEXT/references/docs/team-guide.md").unlink()

        with self.assertRaisesRegex(ContextCanonError, "package file set mismatch"):
            load_package(artifact)

    def test_manifest_rejects_path_outside_human_package(self):
        repo = self.make_repo()
        _, team = self.compile_team(repo)
        artifact = self.write_artifact(team)
        manifest_path = artifact / PACKAGE_MANIFEST_PATH
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        payload["files"][0]["path"] = "../outside.txt"
        manifest_path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")

        with self.assertRaisesRegex(ContextCanonError, "Invalid package file path"):
            load_package(artifact)


if __name__ == "__main__":
    unittest.main()
