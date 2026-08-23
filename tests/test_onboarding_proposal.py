from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from contextcanon.onboarding import prepare_onboarding_evidence
from contextcanon.onboarding_proposal import (
    PROPOSAL_SCHEMA,
    load_evidence_snapshot,
    load_onboarding_proposal,
)
from contextcanon.parser import ContextCanonError


class OnboardingProposalTests(unittest.TestCase):
    def make_snapshot(self):
        repo = Path(tempfile.mkdtemp())
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        (repo / "README.md").write_text(
            "# Demo project\n"
            "\n"
            "Use Python 3.12 and run tests before merging.\n"
            "Current migration work is still incomplete.\n",
            encoding="utf-8",
        )
        (repo / "docs").mkdir()
        (repo / "docs/architecture.md").write_text(
            "# Architecture\n"
            "\n"
            "The service exposes one HTTP API.\n"
            "Keep deployment details in this document.\n",
            encoding="utf-8",
        )
        prepared = prepare_onboarding_evidence(repo)
        return repo, prepared

    def write_proposal(self, repo: Path, value: dict, name: str = "proposal.json") -> Path:
        path = repo / name
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return path

    def evidence_ref(self, prepared, path: str, start: int, end: int) -> dict[str, object]:
        entry = next(item for item in prepared.included if item.path == path)
        return {
            "path": path,
            "sha256": entry.sha256,
            "start_line": start,
            "end_line": end,
        }

    def complete_proposal(self, prepared) -> dict[str, object]:
        readme_rule = self.evidence_ref(prepared, "README.md", 3, 3)
        readme_state = self.evidence_ref(prepared, "README.md", 4, 4)
        architecture = self.evidence_ref(prepared, "docs/architecture.md", 3, 4)
        return {
            "schema": PROPOSAL_SCHEMA,
            "evidence_digest": prepared.evidence_digest,
            "items": [
                {
                    "id": "P-001",
                    "kind": "local-rule",
                    "title": "Run tests before merging",
                    "rationale": "The README states this as a project development convention.",
                    "confidence": "high",
                    "evidence": [readme_rule],
                    "payload": {
                        "group": "Development",
                        "statement": "Run the project tests before merging changes.",
                        "why": "The repository documents this as part of its development workflow.",
                    },
                },
                {
                    "id": "P-002",
                    "kind": "existing-source",
                    "title": "Consider the shared Python development Source",
                    "rationale": "The Python version and test convention look reusable rather than domain-specific.",
                    "confidence": "medium",
                    "evidence": [readme_rule],
                    "payload": {
                        "source_node_id": "example-python-source",
                        "source_name": "Python Development",
                        "reason": "Prefer an existing reusable Source if the configured catalog contains this practice.",
                    },
                },
                {
                    "id": "P-003",
                    "kind": "candidate-reusable-node",
                    "title": "Python development conventions",
                    "rationale": "The convention could apply to several Python repositories if no equivalent Source exists.",
                    "confidence": "medium",
                    "evidence": [readme_rule],
                    "payload": {
                        "suggested_name": "Python Development",
                        "scope": "Reusable Python runtime and test conventions.",
                        "why_reusable": "Nothing in the cited convention is specific to the Demo domain.",
                    },
                },
                {
                    "id": "P-004",
                    "kind": "topic-resource",
                    "title": "Architecture work",
                    "rationale": "The architecture document contains deeper task-specific material.",
                    "confidence": "high",
                    "evidence": [architecture],
                    "payload": {
                        "condition": "When changing service architecture or deployment structure:",
                        "resource_paths": ["docs/architecture.md"],
                    },
                },
                {
                    "id": "P-005",
                    "kind": "state-planning",
                    "title": "Migration remains incomplete",
                    "rationale": "This is temporary project status rather than reusable governance.",
                    "confidence": "high",
                    "evidence": [readme_state],
                    "payload": {
                        "destination": "state",
                        "summary": "The current migration work is still incomplete.",
                    },
                },
                {
                    "id": "P-006",
                    "kind": "ordinary-documentation",
                    "title": "Keep deployment detail in architecture documentation",
                    "rationale": "The evidence explicitly says the details belong in the existing document.",
                    "confidence": "high",
                    "evidence": [architecture],
                    "payload": {
                        "document_paths": ["docs/architecture.md"],
                        "reason": "This material is useful documentation but does not need to become an always-on Rule.",
                    },
                },
                {
                    "id": "P-007",
                    "kind": "unresolved-question",
                    "title": "Test command is unspecified",
                    "rationale": "The evidence requires tests but does not identify the command or suite.",
                    "confidence": "low",
                    "evidence": [readme_rule],
                    "payload": {
                        "question": "Which exact test command should ContextCanon document for this project?",
                        "why_unresolved": "The supplied evidence says to run tests but provides no command.",
                    },
                },
            ],
        }

    def test_complete_typed_proposal_validates_and_has_stable_digest(self):
        repo, prepared = self.make_snapshot()
        proposal_value = self.complete_proposal(prepared)
        first_path = self.write_proposal(repo, proposal_value, "proposal-a.json")

        second_value = {
            "items": proposal_value["items"],
            "evidence_digest": proposal_value["evidence_digest"],
            "schema": proposal_value["schema"],
        }
        second_path = repo / "proposal-b.json"
        second_path.write_text(json.dumps(second_value, separators=(",", ":")), encoding="utf-8")

        first = load_onboarding_proposal(first_path, prepared.snapshot_root)
        second = load_onboarding_proposal(second_path, prepared.snapshot_root)

        self.assertEqual(first.proposal_digest, second.proposal_digest)
        self.assertEqual(len(first.items), 7)
        self.assertEqual([item.kind for item in first.items], [
            "local-rule",
            "existing-source",
            "candidate-reusable-node",
            "topic-resource",
            "state-planning",
            "ordinary-documentation",
            "unresolved-question",
        ])
        self.assertEqual(first.to_dict()["evidence_digest"], prepared.evidence_digest)

    def test_wrong_evidence_digest_is_rejected(self):
        repo, prepared = self.make_snapshot()
        value = self.complete_proposal(prepared)
        value["evidence_digest"] = "0" * 64
        path = self.write_proposal(repo, value)

        with self.assertRaisesRegex(ContextCanonError, "evidence_digest does not match"):
            load_onboarding_proposal(path, prepared.snapshot_root)

    def test_reference_hash_and_line_range_are_verified(self):
        repo, prepared = self.make_snapshot()
        value = self.complete_proposal(prepared)
        value["items"][0]["evidence"][0]["sha256"] = "0" * 64
        path = self.write_proposal(repo, value, "bad-hash.json")
        with self.assertRaisesRegex(ContextCanonError, "evidence hash does not match"):
            load_onboarding_proposal(path, prepared.snapshot_root)

        value = self.complete_proposal(prepared)
        value["items"][0]["evidence"][0]["end_line"] = 99
        path = self.write_proposal(repo, value, "bad-range.json")
        with self.assertRaisesRegex(ContextCanonError, "exceeds README.md line count"):
            load_onboarding_proposal(path, prepared.snapshot_root)

    def test_reference_must_exist_in_frozen_snapshot(self):
        repo, prepared = self.make_snapshot()
        value = self.complete_proposal(prepared)
        value["items"][0]["evidence"][0]["path"] = "src/main.py"
        path = self.write_proposal(repo, value)

        with self.assertRaisesRegex(ContextCanonError, "not present in snapshot"):
            load_onboarding_proposal(path, prepared.snapshot_root)

    def test_unknown_fields_duplicate_ids_and_invalid_confidence_fail(self):
        repo, prepared = self.make_snapshot()
        value = self.complete_proposal(prepared)
        value["items"][0]["surprise"] = True
        with self.assertRaisesRegex(ContextCanonError, "unknown field"):
            load_onboarding_proposal(self.write_proposal(repo, value, "unknown.json"), prepared.snapshot_root)

        value = self.complete_proposal(prepared)
        value["items"][1]["id"] = "P-001"
        with self.assertRaisesRegex(ContextCanonError, "duplicate item id"):
            load_onboarding_proposal(self.write_proposal(repo, value, "duplicate.json"), prepared.snapshot_root)

        value = self.complete_proposal(prepared)
        value["items"][0]["confidence"] = "certain"
        with self.assertRaisesRegex(ContextCanonError, "confidence must be"):
            load_onboarding_proposal(self.write_proposal(repo, value, "confidence.json"), prepared.snapshot_root)

    def test_kind_specific_payload_is_strict(self):
        repo, prepared = self.make_snapshot()
        value = self.complete_proposal(prepared)
        del value["items"][0]["payload"]["why"]
        with self.assertRaisesRegex(ContextCanonError, "missing field.*why"):
            load_onboarding_proposal(self.write_proposal(repo, value, "missing.json"), prepared.snapshot_root)

        value = self.complete_proposal(prepared)
        value["items"][4]["payload"]["destination"] = "governance"
        with self.assertRaisesRegex(ContextCanonError, "must be 'state' or 'plan'"):
            load_onboarding_proposal(self.write_proposal(repo, value, "destination.json"), prepared.snapshot_root)

    def test_resource_and_document_paths_must_be_in_snapshot(self):
        repo, prepared = self.make_snapshot()
        value = self.complete_proposal(prepared)
        value["items"][3]["payload"]["resource_paths"] = ["docs/missing.md"]
        with self.assertRaisesRegex(ContextCanonError, "topic resource path is not in evidence snapshot"):
            load_onboarding_proposal(self.write_proposal(repo, value, "resource.json"), prepared.snapshot_root)

        value = self.complete_proposal(prepared)
        value["items"][5]["payload"]["document_paths"] = ["docs/missing.md"]
        with self.assertRaisesRegex(ContextCanonError, "ordinary document path is not in evidence snapshot"):
            load_onboarding_proposal(self.write_proposal(repo, value, "document.json"), prepared.snapshot_root)

    def test_snapshot_manifest_tampering_and_extra_file_are_rejected(self):
        repo, prepared = self.make_snapshot()
        manifest = json.loads(prepared.manifest_path.read_text(encoding="utf-8"))
        manifest["selection"]["policy"] = "tampered"
        prepared.manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(ContextCanonError, "selection policy"):
            load_evidence_snapshot(prepared.snapshot_root)

        repo2, prepared2 = self.make_snapshot()
        extra = prepared2.snapshot_root / "evidence/extra.md"
        extra.write_text("unexpected\n", encoding="utf-8")
        with self.assertRaisesRegex(ContextCanonError, "file set does not match"):
            load_evidence_snapshot(prepared2.snapshot_root)

    def test_rehashed_weakened_selection_policy_is_rejected(self):
        repo, prepared = self.make_snapshot()
        manifest = json.loads(prepared.manifest_path.read_text(encoding="utf-8"))
        manifest["selection"]["max_total_bytes"] = 10**12
        payload = {key: manifest[key] for key in ("schema", "selection", "included", "excluded")}
        canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        manifest["evidence_digest"] = hashlib.sha256(canonical).hexdigest()
        prepared.manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        with self.assertRaisesRegex(ContextCanonError, "selection policy"):
            load_evidence_snapshot(prepared.snapshot_root)

    def test_empty_items_is_valid_but_every_item_needs_evidence(self):
        repo, prepared = self.make_snapshot()
        empty = {
            "schema": PROPOSAL_SCHEMA,
            "evidence_digest": prepared.evidence_digest,
            "items": [],
        }
        proposal = load_onboarding_proposal(self.write_proposal(repo, empty, "empty.json"), prepared.snapshot_root)
        self.assertEqual(proposal.items, ())

        value = self.complete_proposal(prepared)
        value["items"][0]["evidence"] = []
        with self.assertRaisesRegex(ContextCanonError, "evidence must be a non-empty list"):
            load_onboarding_proposal(self.write_proposal(repo, value, "no-evidence.json"), prepared.snapshot_root)


if __name__ == "__main__":
    unittest.main()
