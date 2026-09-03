from __future__ import annotations

import sys
from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one match, found {count}: {old[:120]!r}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


def write_test() -> None:
    test = r'''from __future__ import annotations

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
'''
    Path("tests/test_source_update_loop.py").write_text(test, encoding="utf-8")


def patch_docs() -> None:
    anchor = "## Atomic publication and interrupted operations\n"
    section = '''## Normal daily update loop — KISS\n\nUpdating a reusable Git-backed Source is intentionally boring. Only the first command needs the Source repository/network; everything after it uses frozen local candidate bytes.\n\n```text\n# 1. Explicitly look for a newer published package.\ncontextcanon source fetch <source-node-id> --node <consumer-node>\n\n# The command prints the content-addressed Candidate package path. Use that path below.\n\n# 2. Review the exact frozen candidate against the currently accepted Source.\ncontextcanon source review <source-node-id> <candidate-package> --node <consumer-node>\n\n# 3. Accept exactly that reviewed candidate when the diff is wanted.\ncontextcanon source accept <source-node-id> <candidate-package> --node <consumer-node>\n\n# 4. Regenerate/verify the consumer as usual.\ncontextcanon build <consumer-node>\ncontextcanon check <consumer-node>\n```\n\nThe important mental model is:\n\n```text\nremote moving state ──fetch once──> frozen candidate ──review──> reviewed snapshot ──accept──> accepted local package\n                                           │                                              │\n                                           └── never used by normal build                 └── normal/offline build uses this\n```\n\nNo package digest needs to be invented or looked up by the operator: `fetch` discovers the package and prints its exact local candidate path. If the Source repository disappears immediately afterwards, review and accept still work from that path. After acceptance, `.context/candidates/` and `.context/source-reviews/` are scratch/review state; the durable offline boundary is `.context/sources/<accepted-package-digest>/` plus the exact pin in `CONTEXT.src.md`.\n\nIf no update is desired, do nothing. A newer remote commit has zero effect on `build` or `check` until this explicit loop reaches `accept`.\n\n'''
    p = Path("nodes/internal/framework-development/docs/external-sources.md")
    text = p.read_text(encoding="utf-8")
    if anchor not in text:
        raise SystemExit("external Sources daily-loop insertion anchor missing")
    p.write_text(text.replace(anchor, section + anchor, 1), encoding="utf-8")


def complete() -> None:
    replace_once(
        "PLAN.md",
        "**Status: ACTIVE — R6 reusable Source update discovery UX, step 3 of 3. Fast-run remains ACTIVE.**",
        "**Status: COMPLETE — R1-R6 first-production-use work complete. Fast-run CLOSED.**",
    )
    replace_once(
        "PLAN.md",
        "- [ ] 3. Document and test the normal update loop, including offline use of the last accepted package.",
        "- [x] 3. Document and test the normal update loop, including offline use of the last accepted package.",
    )
    marker = "- [x] 3. Document and test the normal update loop, including offline use of the last accepted package."
    replace_once(
        "PLAN.md",
        marker,
        marker + "\n\nCheckpoint: R6 is complete. Explicit fetch discovers and freezes a newer Git package plus exact candidate commit; review/accept remains bound to that local snapshot even if the remote moves or disappears; the accepted exact commit advances only on acceptance; and normal build/check continues fully offline from the last accepted package.",
    )
    replace_once("PLAN.md", "#### Fast-run status — ACTIVE", "#### Fast-run status — CLOSED")
    fast_scope = "- **Scope:** corrections discovered while vertically reviewing the real `ai-workstation` onboarding placement, through the next coherent owner-review candidate."
    replace_once(
        "PLAN.md",
        fast_scope,
        fast_scope + "\n- **Closed at Block R completion:** R1-R6 now form that coherent owner-review candidate. Further framework changes return to ordinary review cadence; the next useful activity is real owner testing/migration of the published `ai-workstation` tree.",
    )
    state = Path("STATE.md")
    state.write_text(
        state.read_text(encoding="utf-8").rstrip()
        + "\n\n## Latest Block R complete first-production-use checkpoint\n\nBlock R is complete and the owner-approved fast-run is CLOSED. ContextCanon now has human-readable onboarding review surfaces, simple normal Rule/Topic authoring, source-first migration audit, transitive package-safe Topics/Resources, explicit immutable semantic Parent chains with safe update/migration/recovery, and a complete reusable-Source fetch/review/accept loop whose normal builds remain offline on accepted packages. The next useful validation is the real published `ai-workstation` tree: migrate its reviewed Step-03 hierarchy to Parent pins and exercise work from a subsystem Node. PR #13 remains draft/unmerged pending explicit owner approval.\n",
        encoding="utf-8",
    )


def apply() -> None:
    write_test()
    patch_docs()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--complete":
        complete()
    else:
        apply()
