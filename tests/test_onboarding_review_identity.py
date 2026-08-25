from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from contextcanon.onboarding import prepare_onboarding_evidence
from contextcanon.onboarding_review import create_or_load_onboarding_review


class OnboardingReviewIdentityTests(unittest.TestCase):
    def make_project(self):
        repo = Path(tempfile.mkdtemp())
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        (repo / "README.md").write_text(
            "# Identical Project Evidence\n\nThe same bytes may occur in unrelated repositories.\n",
            encoding="utf-8",
        )
        prepared = prepare_onboarding_evidence(repo)
        proposal = repo / "proposal.json"
        proposal.write_text(
            json.dumps(
                {
                    "schema": "contextcanon/onboarding-proposal/v0",
                    "evidence_digest": prepared.evidence_digest,
                    "items": [],
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        return repo, prepared, proposal

    def test_identical_evidence_does_not_create_same_new_node_identity(self):
        repo_a, prepared_a, proposal_a = self.make_project()
        repo_b, prepared_b, proposal_b = self.make_project()

        self.assertEqual(prepared_a.evidence_digest, prepared_b.evidence_digest)

        review_a, _, _, created_a = create_or_load_onboarding_review(
            prepared_a.snapshot_root,
            proposal_a,
            repo_a / "review.json",
            node_name="Project A",
        )
        review_b, _, _, created_b = create_or_load_onboarding_review(
            prepared_b.snapshot_root,
            proposal_b,
            repo_b / "review.json",
            node_name="Project B",
        )

        self.assertTrue(created_a)
        self.assertTrue(created_b)
        uuid.UUID(review_a.node.id)
        uuid.UUID(review_b.node.id)
        self.assertNotEqual(review_a.node.id, review_b.node.id)

        reloaded_a, _, _, created_again = create_or_load_onboarding_review(
            prepared_a.snapshot_root,
            proposal_a,
            repo_a / "review.json",
        )
        self.assertFalse(created_again)
        self.assertEqual(reloaded_a.node.id, review_a.node.id)
        self.assertEqual(reloaded_a.review_digest, review_a.review_digest)


if __name__ == "__main__":
    unittest.main()
