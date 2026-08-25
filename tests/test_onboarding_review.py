from __future__ import annotations

import contextlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import contextcanon.onboarding_review as onboarding_review_module
from contextcanon.cli import main
from contextcanon.compiler import Compiler
from contextcanon.onboarding import prepare_onboarding_evidence
from contextcanon.onboarding_proposal import load_evidence_snapshot, load_onboarding_proposal
from contextcanon.onboarding_review import (
    accept_onboarding_review,
    create_or_load_onboarding_review,
    load_onboarding_review,
    render_onboarding_review,
)
from contextcanon.outputs import check_outputs, write_outputs
from contextcanon.parser import ContextCanonError


class OnboardingReviewTests(unittest.TestCase):
    def make_project(self):
        repo = Path(tempfile.mkdtemp())
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        (repo / "README.md").write_text(
            "# Demo Project\n\nRun tests before merging.\nThe migration target is still undecided.\n",
            encoding="utf-8",
        )
        (repo / "docs").mkdir()
        (repo / "docs" / "architecture.md").write_text(
            "# Architecture\n\nThe service boundary is intentionally narrow.\n",
            encoding="utf-8",
        )
        return repo, prepare_onboarding_evidence(repo)

    def evidence_ref(self, prepared, path: str, start: int, end: int):
        snapshot = load_evidence_snapshot(prepared.snapshot_root)
        entry = snapshot.by_path[path]
        return {
            "path": path,
            "sha256": entry.sha256,
            "start_line": start,
            "end_line": end,
        }

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

    def local_rule(self, prepared):
        return {
            "id": "TEST-001",
            "kind": "local-rule",
            "title": "Run tests before merging",
            "rationale": "The README states this as the project merge discipline.",
            "confidence": "high",
            "evidence": [self.evidence_ref(prepared, "README.md", 3, 3)],
            "payload": {
                "group": "Development",
                "statement": "Run the configured test suite before merging changes.",
                "why": "Merges should not knowingly introduce failing tests.",
            },
        }

    def topic(self, prepared):
        return {
            "id": "ARCH",
            "kind": "topic-resource",
            "title": "Architecture",
            "rationale": "Architecture detail is useful only for architecture-sensitive work.",
            "confidence": "high",
            "evidence": [self.evidence_ref(prepared, "docs/architecture.md", 1, 3)],
            "payload": {
                "condition": "When changing service boundaries or architecture:",
                "resource_paths": ["docs/architecture.md"],
            },
        }

    def reusable_candidate(self, prepared):
        return {
            "id": "GENERIC-TESTING",
            "kind": "candidate-reusable-node",
            "title": "Reusable testing discipline",
            "rationale": "The practice may apply across repositories.",
            "confidence": "medium",
            "evidence": [self.evidence_ref(prepared, "README.md", 3, 3)],
            "payload": {
                "suggested_name": "Testing Discipline",
                "scope": "Cross-project test-before-merge guidance.",
                "why_reusable": "The rule is not intrinsically project-specific.",
            },
        }

    def unresolved(self, prepared):
        return {
            "id": "MIGRATION-QUESTION",
            "kind": "unresolved-question",
            "title": "Migration target",
            "rationale": "The repository explicitly says the target is undecided.",
            "confidence": "high",
            "evidence": [self.evidence_ref(prepared, "README.md", 4, 4)],
            "payload": {
                "question": "Which migration target should become the project plan?",
                "why_unresolved": "The frozen evidence says the target is still undecided.",
            },
        }

    def existing_source(self, prepared, package):
        return {
            "id": "USE-SHARED-PYTHON",
            "kind": "existing-source",
            "title": "Use shared Python development",
            "rationale": "The supplied reusable Node already covers the practice.",
            "confidence": "high",
            "evidence": [self.evidence_ref(prepared, "README.md", 3, 3)],
            "payload": {
                "source_node_id": package.metadata.id,
                "source_name": package.metadata.name,
                "source_version": package.metadata.version,
                "source_normalized_digest": package.normalized_digest,
                "source_package_digest": package.package_digest,
                "reason": "Reuse the shared test discipline instead of copying it locally.",
            },
        }

    def set_decisions(self, review_path: Path, values: dict[str, str]) -> None:
        data = json.loads(review_path.read_text(encoding="utf-8"))
        for decision in data["decisions"]:
            if decision["id"] in values:
                decision["decision"] = values[decision["id"]]
        review_path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def make_package(
        self,
        node_id: str = "shared-python",
        *,
        version: str = "1.2.0",
        statement: str = "Run the configured test suite before merging changes.",
    ) -> Path:
        repo = Path(tempfile.mkdtemp())
        (repo / ".git").mkdir()
        (repo / "CONTEXT.src.md").write_text(
            f'''# Shared Python Development — Local Context Source
<!-- ctx:node id="{node_id}" version="{version}" -->

## Rules

### Development

- **Run tests:** {statement}
  Why: Shared testing discipline catches regressions before merge.
  <!-- ctx:rule id="PY-TEST" -->
''',
            encoding="utf-8",
        )
        compiled = Compiler(repo).compile(repo)
        write_outputs(compiled)
        return repo

    def test_review_template_is_pending_and_renders_exact_evidence(self):
        repo, prepared = self.make_project()
        proposal_path = self.write_proposal(repo, prepared, [self.local_rule(prepared)])
        review_path = repo / "review.json"

        review, proposal, snapshot, created = create_or_load_onboarding_review(
            prepared.snapshot_root,
            proposal_path,
            review_path,
            node_name="Demo Context",
        )

        self.assertTrue(created)
        self.assertEqual(review.decisions[0].decision, "pending")
        self.assertEqual(review.proposal_digest, proposal.proposal_digest)
        report = render_onboarding_review(review, proposal, snapshot)
        self.assertIn("[PENDING] TEST-001", report)
        self.assertIn("3: Run tests before merging.", report)
        self.assertIn("Edit the review JSON", report)

        loaded, _, _, created_again = create_or_load_onboarding_review(
            prepared.snapshot_root,
            proposal_path,
            review_path,
        )
        self.assertFalse(created_again)
        self.assertEqual(loaded.review_digest, review.review_digest)

    def test_proposal_change_invalidates_existing_review(self):
        repo, prepared = self.make_project()
        item = self.local_rule(prepared)
        proposal_path = self.write_proposal(repo, prepared, [item])
        review_path = repo / "review.json"
        create_or_load_onboarding_review(
            prepared.snapshot_root,
            proposal_path,
            review_path,
            node_name="Demo Context",
        )

        item["title"] = "Changed semantic finding"
        self.write_proposal(repo, prepared, [item])
        changed = load_onboarding_proposal(proposal_path, prepared.snapshot_root)
        with self.assertRaisesRegex(ContextCanonError, "proposal changed after review creation"):
            load_onboarding_review(review_path, changed)

    def test_accept_requires_all_decisions_and_unchanged_live_evidence(self):
        repo, prepared = self.make_project()
        proposal_path = self.write_proposal(repo, prepared, [self.local_rule(prepared)])
        review_path = repo / "review.json"
        create_or_load_onboarding_review(
            prepared.snapshot_root,
            proposal_path,
            review_path,
            node_name="Demo Context",
        )

        with self.assertRaisesRegex(ContextCanonError, "pending decisions"):
            accept_onboarding_review(prepared.snapshot_root, proposal_path, review_path, repo)

        self.set_decisions(review_path, {"TEST-001": "accept"})
        (repo / "README.md").write_text("# changed after review\n", encoding="utf-8")
        with self.assertRaisesRegex(ContextCanonError, "Project evidence changed after onboarding review"):
            accept_onboarding_review(prepared.snapshot_root, proposal_path, review_path, repo)
        self.assertFalse((repo / "CONTEXT.src.md").exists())

    def test_accept_publishes_reviewed_context_and_preserves_follow_up_findings(self):
        repo, prepared = self.make_project()
        original_readme = (repo / "README.md").read_bytes()
        items = [
            self.local_rule(prepared),
            self.topic(prepared),
            self.reusable_candidate(prepared),
            self.unresolved(prepared),
        ]
        proposal_path = self.write_proposal(repo, prepared, items)
        review_path = repo / "review.json"
        create_or_load_onboarding_review(
            prepared.snapshot_root,
            proposal_path,
            review_path,
            node_name="Demo Context",
            node_id="demo-context",
        )
        self.set_decisions(review_path, {item["id"]: "accept" for item in items})

        accepted = accept_onboarding_review(prepared.snapshot_root, proposal_path, review_path, repo)

        source = (repo / "CONTEXT.src.md").read_text(encoding="utf-8")
        self.assertIn('ctx:node id="demo-context" version="0.1.0"', source)
        self.assertIn('ctx:rule id="TEST-001"', source)
        self.assertIn('ctx:topic id="ARCH"', source)
        self.assertEqual((repo / "README.md").read_bytes(), original_readme)
        self.assertTrue((accepted.acceptance_path.parent / "reusable-candidates.json").is_file())
        self.assertTrue((accepted.acceptance_path.parent / "unresolved.json").is_file())
        compiled = Compiler(repo).compile(repo)
        self.assertEqual(check_outputs(compiled), [])
        receipt = json.loads(accepted.acceptance_path.read_text(encoding="utf-8"))
        self.assertEqual(receipt["schema"], "contextcanon/onboarding-acceptance/v0")
        self.assertEqual(receipt["canonical"]["package_digest"], compiled.package_digest)

    def test_accept_existing_source_requires_exact_package_and_locator_and_builds_offline(self):
        repo, prepared = self.make_project()
        package_root = self.make_package()
        package = Compiler(package_root).compile(package_root)
        item = self.existing_source(prepared, package)
        proposal_path = self.write_proposal(repo, prepared, [item])
        review_path = repo / "review.json"
        create_or_load_onboarding_review(
            prepared.snapshot_root,
            proposal_path,
            review_path,
            node_name="Demo Context",
            node_id="demo-context",
        )
        self.set_decisions(review_path, {item["id"]: "accept"})

        with self.assertRaisesRegex(ContextCanonError, "requires --catalog-package"):
            accept_onboarding_review(prepared.snapshot_root, proposal_path, review_path, repo)
        with self.assertRaisesRegex(ContextCanonError, "requires --source-locator"):
            accept_onboarding_review(
                prepared.snapshot_root,
                proposal_path,
                review_path,
                repo,
                catalog_package_roots=[package_root],
            )

        accepted = accept_onboarding_review(
            prepared.snapshot_root,
            proposal_path,
            review_path,
            repo,
            catalog_package_roots=[package_root],
            source_locators={item["id"]: "https://example.invalid/shared-python.git"},
        )
        source = (repo / "CONTEXT.src.md").read_text(encoding="utf-8")
        self.assertIn(package.package_digest, source)
        self.assertIn("https://example.invalid/shared-python.git", source)
        shutil.rmtree(package_root)
        compiled = Compiler(repo).compile(repo)
        self.assertEqual(compiled.package_digest, accepted.package_digest)
        self.assertEqual(check_outputs(compiled), [])

    def test_legacy_existing_source_proposal_validates_but_cannot_be_accepted_unbound(self):
        repo, prepared = self.make_project()
        package_root = self.make_package()
        package = Compiler(package_root).compile(package_root)
        item = self.existing_source(prepared, package)
        for field in ("source_version", "source_normalized_digest", "source_package_digest"):
            del item["payload"][field]
        proposal_path = self.write_proposal(repo, prepared, [item])
        review_path = repo / "review.json"
        create_or_load_onboarding_review(
            prepared.snapshot_root,
            proposal_path,
            review_path,
            node_name="Demo Context",
        )
        self.set_decisions(review_path, {item["id"]: "accept"})

        with self.assertRaisesRegex(ContextCanonError, "not bound to an exact catalog package"):
            accept_onboarding_review(
                prepared.snapshot_root,
                proposal_path,
                review_path,
                repo,
                catalog_package_roots=[package_root],
                source_locators={item["id"]: "https://example.invalid/shared-python.git"},
            )

    def test_existing_source_acceptance_requires_same_exact_package_seen_by_reviewer(self):
        repo, prepared = self.make_project()
        reviewed_root = self.make_package(version="1.2.0")
        reviewed = Compiler(reviewed_root).compile(reviewed_root)
        different_root = self.make_package(
            version="1.3.0",
            statement="Run tests and the integration suite before merging changes.",
        )
        item = self.existing_source(prepared, reviewed)
        proposal_path = self.write_proposal(repo, prepared, [item])
        review_path = repo / "review.json"
        create_or_load_onboarding_review(
            prepared.snapshot_root,
            proposal_path,
            review_path,
            node_name="Demo Context",
        )
        self.set_decisions(review_path, {item["id"]: "accept"})

        with self.assertRaisesRegex(ContextCanonError, "exact package identity does not match supplied package"):
            accept_onboarding_review(
                prepared.snapshot_root,
                proposal_path,
                review_path,
                repo,
                catalog_package_roots=[different_root],
                source_locators={item["id"]: "https://example.invalid/shared-python.git"},
            )
        self.assertFalse((repo / "CONTEXT.src.md").exists())

    def test_accept_refuses_destructive_replacement(self):
        repo, prepared = self.make_project()
        proposal_path = self.write_proposal(repo, prepared, [self.local_rule(prepared)])
        review_path = repo / "review.json"
        create_or_load_onboarding_review(
            prepared.snapshot_root,
            proposal_path,
            review_path,
            node_name="Demo Context",
        )
        self.set_decisions(review_path, {"TEST-001": "accept"})
        (repo / "CONTEXT.src.md").write_text(
            '# Existing — Local Context Source\n<!-- ctx:node id="existing" version="1.0.0" -->\n',
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ContextCanonError, "will not replace an existing CONTEXT.src.md"):
            accept_onboarding_review(prepared.snapshot_root, proposal_path, review_path, repo)

    def test_first_adoption_refuses_preexisting_generated_output_paths(self):
        for relative_path in ("CONTEXT.md", "CONTEXT/legacy.md", "AGENTS.md"):
            with self.subTest(relative_path=relative_path):
                repo, prepared = self.make_project()
                proposal_path = self.write_proposal(repo, prepared, [self.local_rule(prepared)])
                review_path = repo / "review.json"
                create_or_load_onboarding_review(
                    prepared.snapshot_root,
                    proposal_path,
                    review_path,
                    node_name="Demo Context",
                )
                self.set_decisions(review_path, {"TEST-001": "accept"})
                collision = repo / relative_path
                collision.parent.mkdir(parents=True, exist_ok=True)
                original = b"project-owned file\n"
                collision.write_bytes(original)

                with self.assertRaisesRegex(ContextCanonError, "will not replace"):
                    accept_onboarding_review(prepared.snapshot_root, proposal_path, review_path, repo)
                self.assertEqual(collision.read_bytes(), original)
                self.assertFalse((repo / "CONTEXT.src.md").exists())

    def test_failed_acceptance_record_publication_rolls_back_first_adoption(self):
        repo, prepared = self.make_project()
        original_readme = (repo / "README.md").read_bytes()
        proposal_path = self.write_proposal(repo, prepared, [self.local_rule(prepared)])
        review_path = repo / "review.json"
        create_or_load_onboarding_review(
            prepared.snapshot_root,
            proposal_path,
            review_path,
            node_name="Demo Context",
        )
        self.set_decisions(review_path, {"TEST-001": "accept"})
        original_write = onboarding_review_module._atomic_write_text

        def fail_acceptance_record(path: Path, content: str) -> None:
            if path.name == "acceptance.json":
                raise ContextCanonError("simulated acceptance record publication failure")
            original_write(path, content)

        with mock.patch.object(
            onboarding_review_module,
            "_atomic_write_text",
            side_effect=fail_acceptance_record,
        ):
            with self.assertRaisesRegex(ContextCanonError, "simulated acceptance record publication failure"):
                accept_onboarding_review(prepared.snapshot_root, proposal_path, review_path, repo)

        self.assertEqual((repo / "README.md").read_bytes(), original_readme)
        for relative_path in (
            "CONTEXT.src.md",
            "CONTEXT.md",
            "AGENTS.md",
            ".goosehints",
            ".context/context.yaml",
            ".context/package.json",
        ):
            self.assertFalse((repo / relative_path).exists(), relative_path)
        accepted_parent = repo / ".context" / "onboarding" / "accepted"
        self.assertFalse(any(accepted_parent.iterdir()) if accepted_parent.exists() else False)

    def test_cli_review_creates_human_file_and_prints_report(self):
        repo, prepared = self.make_project()
        proposal_path = self.write_proposal(repo, prepared, [self.local_rule(prepared)])
        review_path = repo / "review.json"
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            result = main(
                [
                    "onboard",
                    "review",
                    str(prepared.snapshot_root),
                    str(proposal_path),
                    str(review_path),
                    "--node-name",
                    "Demo Context",
                ]
            )
        self.assertEqual(result, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertTrue(review_path.is_file())
        self.assertIn("created onboarding review", stdout.getvalue())
        self.assertIn("[PENDING] TEST-001", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
