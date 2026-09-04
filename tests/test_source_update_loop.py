from __future__ import annotations

import shutil
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from contextcanon.compiler import Compiler
from contextcanon.git_transport import fetch_git_candidate, load_candidate_provenance
from contextcanon.outputs import check_outputs, write_outputs
from contextcanon.parser import parse_node
from contextcanon.sources import accept_source_candidate, review_source_candidate
from tests.test_git_transport import GitTransportTests


class SourceUpdateLoopTests(unittest.TestCase):
    def test_normal_fetch_review_accept_then_offline_build_loop(self):
        helper = GitTransportTests()
        provider, v1, v2 = helper.make_provider()
        commits = helper.git(provider, "log", "--format=%H", "--reverse").stdout.splitlines()
        accepted_ref, candidate_ref = commits
        consumer = helper.make_consumer(provider, v1)
        source_path = consumer / "CONTEXT.src.md"
        source_path.write_text(
            source_path.read_text(encoding="utf-8").replace('ref="main"', f'ref="{accepted_ref}"'),
            encoding="utf-8",
        )

        # 1. Fetch is the only network/repository-discovery step. It freezes
        # exact candidate bytes + exact Git provenance but changes no accepted
        # consumer state.
        candidate, candidate_root = fetch_git_candidate(consumer, "node-python")
        self.assertEqual(candidate.package_digest, v2.package_digest)
        provenance = load_candidate_provenance(consumer, candidate.package_digest)
        self.assertEqual(provenance["candidate_ref"], candidate_ref)
        before = Compiler(consumer).compile(consumer)
        self.assertEqual(before.source_packages[0].package_digest, v1.package_digest)

        # Simulate remote/network loss immediately after discovery. Review and
        # accept must operate only on the frozen local candidate.
        shutil.rmtree(provider)

        # 2. Review is local and non-mutating.
        diff, receipt = review_source_candidate(consumer, "node-python", candidate_root)
        self.assertFalse(diff.is_empty)
        self.assertTrue(receipt.is_file())
        after_review = Compiler(consumer).compile(consumer)
        self.assertEqual(after_review.source_packages[0].package_digest, v1.package_digest)

        # 3. Accept is also local and changes only the accepted immutable store
        # plus the exact canonical Source pin.
        accepted = accept_source_candidate(consumer, "node-python", candidate_root)
        self.assertEqual(accepted.package_digest, v2.package_digest)
        parsed = parse_node(consumer, consumer).sources[0]
        self.assertEqual(parsed.package_digest, v2.package_digest)
        self.assertEqual(parsed.transport_ref, candidate_ref)

        # Candidate/review scratch state is expendable after acceptance. The
        # normal consumer remains independently buildable/checkable offline.
        shutil.rmtree(consumer / ".context" / "candidates")
        shutil.rmtree(consumer / ".context" / "source-reviews")
        compiled = Compiler(consumer).compile(consumer)
        self.assertEqual(compiled.source_packages[0].package_digest, v2.package_digest)
        self.assertEqual(compiled.inherited_rules[0].statement, "Prefer explicit Python v2.")
        write_outputs(compiled)
        self.assertEqual(check_outputs(Compiler(consumer).compile(consumer)), [])

        # The accepted content-addressed package is the offline boundary.
        self.assertTrue(
            (consumer / ".context" / "sources" / v2.package_digest / ".context" / "package.json").is_file()
        )


if __name__ == "__main__":
    unittest.main()
