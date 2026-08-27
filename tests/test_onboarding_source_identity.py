from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from contextcanon.onboarding import prepare_onboarding_evidence
from contextcanon.onboarding_proposal import load_onboarding_proposal
from contextcanon.parser import ContextCanonError


class OnboardingSourceIdentityProposalTests(unittest.TestCase):
    def make_case(self):
        repo = Path(tempfile.mkdtemp())
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        (repo / "README.md").write_text("# Demo\n\nRun tests before merging.\n", encoding="utf-8")
        prepared = prepare_onboarding_evidence(repo)
        entry = prepared.included[0]
        item = {
            "id": "USE-SHARED",
            "kind": "existing-source",
            "title": "Use shared development context",
            "rationale": "A supplied reusable Source covers the evidence-backed practice.",
            "confidence": "high",
            "evidence": [
                {
                    "path": "README.md",
                    "sha256": entry.sha256,
                    "start_line": 3,
                    "end_line": 3,
                }
            ],
            "payload": {
                "source_node_id": "shared-development",
                "source_name": "Shared Development",
                "reason": "Reuse the supplied package rather than duplicate the practice.",
            },
        }
        return repo, prepared, item

    def write(self, repo: Path, prepared, item: dict, name: str) -> Path:
        path = repo / name
        path.write_text(
            json.dumps(
                {
                    "schema": "contextcanon/onboarding-proposal/v0",
                    "evidence_digest": prepared.evidence_digest,
                    "items": [item],
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        return path

    def test_legacy_shape_still_validates_but_exact_identity_is_all_or_nothing(self):
        repo, prepared, item = self.make_case()

        legacy = load_onboarding_proposal(
            self.write(repo, prepared, item, "legacy.json"),
            prepared.snapshot_root,
        )
        self.assertNotIn("source_version", legacy.items[0].payload)

        item["payload"].update(
            {
                "source_version": "1.2.0",
                "source_normalized_digest": "1" * 64,
                "source_package_digest": "2" * 64,
            }
        )
        exact = load_onboarding_proposal(
            self.write(repo, prepared, item, "exact.json"),
            prepared.snapshot_root,
        )
        self.assertEqual(exact.items[0].payload["source_version"], "1.2.0")
        self.assertEqual(exact.items[0].payload["source_package_digest"], "2" * 64)

        del item["payload"]["source_package_digest"]
        with self.assertRaisesRegex(ContextCanonError, "exact package identity is incomplete"):
            load_onboarding_proposal(
                self.write(repo, prepared, item, "partial.json"),
                prepared.snapshot_root,
            )


if __name__ == "__main__":
    unittest.main()
