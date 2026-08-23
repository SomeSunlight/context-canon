from __future__ import annotations

import contextlib
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from contextcanon.cli import main
from contextcanon.compiler import Compiler
from contextcanon.onboarding import prepare_onboarding_evidence
from contextcanon.onboarding_instruction import MAX_INSTRUCTION_BYTES, build_onboarding_instruction
from contextcanon.outputs import write_outputs
from contextcanon.parser import ContextCanonError


class OnboardingInstructionTests(unittest.TestCase):
    def make_project_snapshot(self):
        repo = Path(tempfile.mkdtemp())
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        (repo / "README.md").write_text(
            "# Demo\n\nUse Python 3.12.\nRun tests before merging.\n",
            encoding="utf-8",
        )
        return repo, prepare_onboarding_evidence(repo)

    def make_package(self, node_id: str, name: str, rule_id: str, statement: str) -> Path:
        repo = Path(tempfile.mkdtemp())
        (repo / ".git").mkdir()
        source = f'''# {name} — Local Context Source
<!-- ctx:node id="{node_id}" version="1.0.0" -->

## Rules

### Development

- **Shared practice:** {statement}
  Why: This fixture represents reusable project guidance.
  <!-- ctx:rule id="{rule_id}" -->
'''
        (repo / "CONTEXT.src.md").write_text(source, encoding="utf-8")
        compiled = Compiler(repo).compile(repo)
        write_outputs(compiled)
        return repo

    def test_instruction_is_deterministic_and_bound_to_exact_evidence(self):
        _, prepared = self.make_project_snapshot()

        first = build_onboarding_instruction(prepared.snapshot_root)
        second = build_onboarding_instruction(prepared.snapshot_root)

        self.assertEqual(first.text, second.text)
        self.assertEqual(first.instruction_digest, second.instruction_digest)
        self.assertEqual(first.evidence_digest, prepared.evidence_digest)
        readme = prepared.included[0]
        self.assertIn(prepared.evidence_digest, first.text)
        self.assertIn("`README.md`", first.text)
        self.assertIn(readme.sha256, first.text)
        self.assertIn("Read **every** file listed below", first.text)
        self.assertIn("Do not use the live repository", first.text)
        self.assertIn("untrusted review data", first.text)
        self.assertIn("Never execute commands", first.text)
        self.assertIn("Return **only one JSON object**", first.text)
        self.assertIn('"schema": "contextcanon/onboarding-proposal/v0"', first.text)
        self.assertIn("No reusable Source package catalog was supplied", first.text)
        self.assertIn("Do **not** invent an `existing-source`", first.text)

    def test_verified_catalog_exposes_exact_source_identity_and_semantics(self):
        _, prepared = self.make_project_snapshot()
        package = self.make_package(
            "shared-python",
            "Shared Python Development",
            "PY-001",
            "Run the configured test suite before merging changes.",
        )

        instruction = build_onboarding_instruction(
            prepared.snapshot_root,
            catalog_package_roots=[package],
        )

        self.assertEqual([item.metadata.id for item in instruction.catalog_packages], ["shared-python"])
        self.assertIn("### Shared Python Development", instruction.text)
        self.assertIn("Node ID: `shared-python`", instruction.text)
        self.assertIn("`shared-python#PY-001`", instruction.text)
        self.assertIn("Run the configured test suite before merging changes.", instruction.text)
        self.assertIn("Use `existing-source` only when a listed package materially covers", instruction.text)

    def test_catalog_order_does_not_change_instruction(self):
        _, prepared = self.make_project_snapshot()
        alpha = self.make_package("alpha-source", "Alpha Source", "A-001", "Use alpha practice.")
        beta = self.make_package("beta-source", "Beta Source", "B-001", "Use beta practice.")

        forward = build_onboarding_instruction(
            prepared.snapshot_root,
            catalog_package_roots=[alpha, beta],
        )
        reverse = build_onboarding_instruction(
            prepared.snapshot_root,
            catalog_package_roots=[beta, alpha],
        )

        self.assertEqual(forward.text, reverse.text)
        self.assertEqual(forward.instruction_digest, reverse.instruction_digest)
        self.assertLess(forward.text.index("### Alpha Source"), forward.text.index("### Beta Source"))

    def test_duplicate_catalog_node_identity_is_rejected(self):
        _, prepared = self.make_project_snapshot()
        package = self.make_package("shared-source", "Shared Source", "S-001", "Use shared practice.")

        with self.assertRaisesRegex(ContextCanonError, "more than one package for stable Node ID shared-source"):
            build_onboarding_instruction(
                prepared.snapshot_root,
                catalog_package_roots=[package, package],
            )

    def test_catalog_package_is_fully_verified_before_entering_instruction(self):
        _, prepared = self.make_project_snapshot()
        package = self.make_package("shared-source", "Shared Source", "S-001", "Use shared practice.")
        (package / "CONTEXT.md").write_text("tampered\n", encoding="utf-8")

        with self.assertRaisesRegex(ContextCanonError, "package"):
            build_onboarding_instruction(prepared.snapshot_root, catalog_package_roots=[package])

    def test_rendered_instruction_size_limit_rejects_large_catalog_deterministically(self):
        _, prepared = self.make_project_snapshot()
        self.assertEqual(MAX_INSTRUCTION_BYTES, 4 * 1024 * 1024)
        package = self.make_package(
            "large-source",
            "Large Source",
            "L-001",
            "x" * MAX_INSTRUCTION_BYTES,
        )

        errors = []
        for _ in range(2):
            with self.assertRaises(ContextCanonError) as caught:
                build_onboarding_instruction(
                    prepared.snapshot_root,
                    catalog_package_roots=[package],
                )
            errors.append(str(caught.exception))

        self.assertEqual(errors[0], errors[1])
        self.assertIn(
            f"Onboarding instruction exceeds safety limit of {MAX_INSTRUCTION_BYTES} bytes",
            errors[0],
        )
        self.assertIn("narrow the evidence or Source catalog", errors[0])

    def test_cli_stdout_is_only_instruction_and_digest_goes_to_stderr(self):
        _, prepared = self.make_project_snapshot()
        stdout = io.StringIO()
        stderr = io.StringIO()

        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            result = main(["onboard", "instruction", str(prepared.snapshot_root)])

        self.assertEqual(result, 0)
        self.assertTrue(stdout.getvalue().startswith("# ContextCanon Reviewed Onboarding Semantic Instruction\n"))
        self.assertNotIn("instruction digest:", stdout.getvalue())
        self.assertIn("contextcanon onboarding instruction digest:", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
