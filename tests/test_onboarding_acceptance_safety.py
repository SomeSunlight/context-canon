from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from contextcanon.compiler import Compiler
from contextcanon.onboarding import prepare_onboarding_evidence
from contextcanon.onboarding_proposal import load_evidence_snapshot, load_onboarding_proposal
from contextcanon.onboarding_review import accept_onboarding_review, create_or_load_onboarding_review
from contextcanon.outputs import check_outputs
from contextcanon.parser import ContextCanonError


class OnboardingAcceptanceSafetyTests(unittest.TestCase):
    def make_repo(self) -> Path:
        repo = Path(tempfile.mkdtemp())
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        return repo

    def write_proposal(self, repo: Path, prepared, items: list[dict]) -> Path:
        path = repo / "proposal.json"
        path.write_text(
            json.dumps(
                {
                    "schema": "contextcanon/onboarding-proposal/v0",
                    "evidence_digest": prepared.evidence_digest,
                    "items": items,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        load_onboarding_proposal(path, prepared.snapshot_root)
        return path

    def evidence_ref(self, prepared, path: str, start: int, end: int) -> dict[str, object]:
        snapshot = load_evidence_snapshot(prepared.snapshot_root)
        entry = snapshot.by_path[path]
        return {
            "path": path,
            "sha256": entry.sha256,
            "start_line": start,
            "end_line": end,
        }

    def accept_decisions(self, review_path: Path, decisions: dict[str, str]) -> None:
        value = json.loads(review_path.read_text(encoding="utf-8"))
        for decision in value["decisions"]:
            decision["decision"] = decisions[decision["id"]]
        review_path.write_text(
            json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def test_rejected_rule_is_not_published_but_remains_in_acceptance_record(self):
        repo = self.make_repo()
        (repo / "README.md").write_text(
            "# Demo\n\nRun tests before merging.\n",
            encoding="utf-8",
        )
        prepared = prepare_onboarding_evidence(repo)
        item = {
            "id": "TEST-001",
            "kind": "local-rule",
            "title": "Run tests before merging",
            "rationale": "The README contains the proposed convention.",
            "confidence": "high",
            "evidence": [self.evidence_ref(prepared, "README.md", 3, 3)],
            "payload": {
                "group": "Development",
                "statement": "Run tests before merging changes.",
                "why": "The proposal claims this is durable governance.",
            },
        }
        proposal_path = self.write_proposal(repo, prepared, [item])
        review_path = repo / "review.json"
        create_or_load_onboarding_review(
            prepared.snapshot_root,
            proposal_path,
            review_path,
            node_name="Demo Context",
            node_id="demo-context",
        )
        self.accept_decisions(review_path, {"TEST-001": "reject"})

        accepted = accept_onboarding_review(
            prepared.snapshot_root,
            proposal_path,
            review_path,
            repo,
        )

        source = (repo / "CONTEXT.src.md").read_text(encoding="utf-8")
        self.assertNotIn("TEST-001", source)
        receipt = json.loads(accepted.acceptance_path.read_text(encoding="utf-8"))
        self.assertEqual(receipt["accepted_item_ids"], [])
        self.assertEqual(receipt["rejected_item_ids"], ["TEST-001"])
        self.assertEqual(check_outputs(Compiler(repo).compile(repo)), [])

    def test_topic_resource_cannot_pull_unreviewed_markdown_link_into_package(self):
        repo = self.make_repo()
        (repo / "README.md").write_text("# Demo\n", encoding="utf-8")
        (repo / "docs").mkdir()
        (repo / "docs" / "architecture.md").write_text(
            "# Architecture\n\nThe reviewed architecture summary.\n\n[Hidden detail](../NOTES.txt)\n",
            encoding="utf-8",
        )
        # Root NOTES.txt is deliberately not an automatic onboarding context carrier.
        (repo / "NOTES.txt").write_text(
            "This file was never offered to the semantic reviewer.\n",
            encoding="utf-8",
        )
        prepared = prepare_onboarding_evidence(repo)
        snapshot = load_evidence_snapshot(prepared.snapshot_root)
        self.assertIn("docs/architecture.md", snapshot.by_path)
        self.assertNotIn("NOTES.txt", snapshot.by_path)

        item = {
            "id": "ARCH",
            "kind": "topic-resource",
            "title": "Architecture",
            "rationale": "Architecture belongs behind a task-specific Topic.",
            "confidence": "high",
            "evidence": [self.evidence_ref(prepared, "docs/architecture.md", 1, 3)],
            "payload": {
                "condition": "When changing architecture:",
                "resource_paths": ["docs/architecture.md"],
            },
        }
        proposal_path = self.write_proposal(repo, prepared, [item])
        review_path = repo / "review.json"
        create_or_load_onboarding_review(
            prepared.snapshot_root,
            proposal_path,
            review_path,
            node_name="Demo Context",
            node_id="demo-context",
        )
        self.accept_decisions(review_path, {"ARCH": "accept"})

        with self.assertRaisesRegex(ContextCanonError, "missing resource"):
            accept_onboarding_review(
                prepared.snapshot_root,
                proposal_path,
                review_path,
                repo,
            )
        self.assertFalse((repo / "CONTEXT.src.md").exists())


if __name__ == "__main__":
    unittest.main()
