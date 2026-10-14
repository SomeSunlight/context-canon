from __future__ import annotations

import contextlib
import io
import shutil
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from contextcanon.cli import main as cli_main
from contextcanon.compiler import Compiler
from contextcanon.outputs import write_outputs
from contextcanon.package import artifact_files


def write_node(repo: Path, root: Path, node_id: str, name: str, version: str, statement: str):
    root.mkdir(parents=True, exist_ok=True)
    root.joinpath("CONTEXT.src.md").write_text(
        f'''# {name} — Local Context Source\n<!-- ctx:node id="{node_id}" name="{name}" version="{version}" -->\n\n## Local Rules\n\n### General\n\n- **Policy:** {statement}\n  Why: Test.\n  <!-- ctx:rule id="RULE-1" -->\n''',
        encoding="utf-8",
    )
    compiled = Compiler(repo).compile(root)
    write_outputs(compiled)
    return Compiler(repo).compile(root)


def install_package(child: Path, compiled) -> None:
    destination = child / ".context" / "sources" / compiled.package_digest
    for rel, content in artifact_files(compiled).items():
        target = destination / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)


def write_child(repo: Path, root: Path, node_id: str, name: str, parent_path: str, parent):
    root.mkdir(parents=True, exist_ok=True)
    root.joinpath("CONTEXT.src.md").write_text(
        f'''# {name} — Local Context Source\n<!-- ctx:node id="{node_id}" name="{name}" version="0.1.0" -->\n\n## Parent Context Node\n\n- [{parent.metadata.name}]({parent_path}) — `{parent.metadata.version}`\n  <!-- ctx:parent id="{parent.metadata.id}" version="{parent.metadata.version}" normalized-digest="{parent.normalized_digest}" package-digest="{parent.package_digest}" -->\n''',
        encoding="utf-8",
    )
    install_package(root, parent)
    compiled = Compiler(repo).compile(root)
    write_outputs(compiled)
    return Compiler(repo).compile(root)

def write_resource_root(repo: Path, *, version: str, filename: str = "troubleshooting.md",
                        content: bytes = b"Old WSL recovery guidance.\n"):
    (repo / "docs").mkdir(exist_ok=True)
    (repo / "docs" / filename).write_bytes(content)
    repo.joinpath("CONTEXT.src.md").write_text(
        f'''# Root — Local Context Source
<!-- ctx:node id="root-id" name="Root" version="{version}" -->

## Local Topics

### Troubleshooting guide

When diagnosing WSL installation issues, read this guide.

Required:
- Resource: `docs/{filename}`
  <!-- ctx:resource id="RESOURCE-TROUBLESHOOT" -->
<!-- ctx:topic id="TOPIC-TROUBLESHOOT" -->
''',
        encoding="utf-8",
    )
    compiled = Compiler(repo).compile(repo)
    write_outputs(compiled)
    return Compiler(repo).compile(repo)


class PropagationReviewUXTests(unittest.TestCase):
    def test_propagation_review_tells_parent_change_and_effective_child_story_before_ids(self):
        repo = Path(tempfile.mkdtemp())
        try:
            (repo / ".git").mkdir()
            root = write_node(repo, repo, "root-id", "Root", "1.0.0", "Root old.")
            write_child(repo, repo / "child", "child-id", "Child", "..", root)
            write_node(repo, repo, "root-id", "Root", "1.1.0", "Root new.")

            out = io.StringIO()
            with contextlib.redirect_stdout(out), mock.patch("builtins.input", return_value="n"):
                rc = cli_main(["propagate", str(repo)])
            self.assertEqual(rc, 0, out.getvalue())
            text = out.getvalue()
            self.assertIn("[1/1] Child (child)", text)
            self.assertIn("Parent: Root 1.0.0 -> 1.1.0", text)
            self.assertIn("Change: 1 rule changed", text)
            self.assertIn("Rules:", text)
            self.assertIn("RULE-1 — Policy", text)
            self.assertIn("before: Root old.", text)
            self.assertIn("after:  Root new.", text)
            self.assertIn("Effect here if accepted: 1 rule changed.", text)
            self.assertNotIn("Technical details:", text)
            self.assertNotIn("Review guidance:", text)
            self.assertLess(text.index("Parent: Root"), text.index("Effect here if accepted:"))
            self.assertNotIn("Review receipt:", text)
            self.assertNotIn("Parent Node ID:", text)
            self.assertIn('No Parent update applied to Child "Child".', text)
        finally:
            shutil.rmtree(repo, ignore_errors=True)

    def test_propagation_rerun_skips_already_current_steps_and_resumes_at_stale_child(self):
        repo = Path(tempfile.mkdtemp())
        try:
            (repo / ".git").mkdir()
            root = write_node(repo, repo, "root", "Root", "1.0.0", "Root old.")
            child = write_child(repo, repo / "child", "child", "Child", "..", root)
            write_child(repo, repo / "child" / "grand", "grand", "Grand", "..", child)
            write_node(repo, repo, "root", "Root", "1.1.0", "Root new.")

            first = io.StringIO()
            with contextlib.redirect_stdout(first), mock.patch("builtins.input", side_effect=["y", "n"]):
                rc = cli_main(["propagate", str(repo)])
            self.assertEqual(rc, 0, first.getvalue())
            self.assertIn('Applied Parent update to Child "Child"', first.getvalue())
            self.assertIn('No Parent update applied to Child "Grand".', first.getvalue())

            second = io.StringIO()
            with contextlib.redirect_stdout(second), mock.patch("builtins.input", return_value="n") as prompt:
                rc = cli_main(["propagate", str(repo)])
            self.assertEqual(rc, 0, second.getvalue())
            text = second.getvalue()
            self.assertIn("Propagation: reviewing 2 Parent/Child relationship(s)", text)
            self.assertIn("[1/2] Child (child)", text)
            self.assertIn("Already current: Root 1.1.0.", text)
            self.assertIn("[2/2] Grand (child/grand)", text)
            self.assertEqual(prompt.call_count, 1)
            self.assertIn('Accept the new Parent for "Grand"?', prompt.call_args.args[0])
        finally:
            shutil.rmtree(repo, ignore_errors=True)

    def test_top_level_propagate_scopes_from_current_node_and_all_broadens_scope(self):
        repo = Path(tempfile.mkdtemp())
        try:
            (repo / ".git").mkdir()
            root = write_node(repo, repo, "root", "Root", "1.0.0", "Root old.")
            child = write_child(repo, repo / "child", "child", "Child", "..", root)
            write_child(repo, repo / "child" / "grand", "grand", "Grand", "..", child)

            other = write_node(repo, repo / "other", "other", "Other", "1.0.0", "Other old.")
            other_leaf = write_child(repo, repo / "other" / "leaf", "other-leaf", "Other Leaf", "..", other)

            write_node(repo, repo, "root", "Root", "1.1.0", "Root new.")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                rc = cli_main(["propagate", str(repo), "--yes"])
            self.assertEqual(rc, 0, out.getvalue())
            self.assertIn("Propagation: reviewing", out.getvalue())
            self.assertIn("Effect here if accepted:", out.getvalue())
            self.assertNotIn("Technical details:", out.getvalue())
            grand = Compiler(repo).compile(repo / "child" / "grand")
            self.assertIn("Root new.", [rule.statement for rule in grand.inherited_rules])
            unchanged_other = Compiler(repo).compile(repo / "other" / "leaf").parent_packages[0]
            self.assertEqual(unchanged_other.package_digest, other_leaf.parent_packages[0].package_digest)

            write_node(repo, repo / "other", "other", "Other", "1.1.0", "Other new.")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                rc = cli_main(["propagate", str(repo), "--all", "--yes"])
            self.assertEqual(rc, 0, out.getvalue())
            updated_other = Compiler(repo).compile(repo / "other" / "leaf")
            self.assertIn("Other new.", [rule.statement for rule in updated_other.inherited_rules])
        finally:
            shutil.rmtree(repo, ignore_errors=True)

    def test_resource_review_shows_authored_path_topic_and_exact_change_not_only_id(self):
        repo = Path(tempfile.mkdtemp())
        try:
            (repo / ".git").mkdir()
            root = write_resource_root(repo, version="1.0.0")
            write_child(repo, repo / "child", "child-id", "Child", "..", root)
            write_resource_root(repo, version="1.1.0", content=b"New WSL recovery guidance.\n")
            out = io.StringIO()
            with contextlib.redirect_stdout(out), mock.patch("builtins.input", return_value="n"):
                rc = cli_main(["propagate", str(repo)])
            self.assertEqual(rc, 0, out.getvalue())
            text = out.getvalue()
            for expected in (
                "Changed Resources:", "docs/troubleshooting.md — content changed",
                "Topic: Troubleshooting guide", "Origin: Root",
                "-Old WSL recovery guidance.", "+New WSL recovery guidance.",
                "Change: 1 resource changed", "Effect here if accepted: 1 resource changed",
                "Parent: Root 1.0.0 -> 1.1.0",
            ):
                self.assertIn(expected, text)
            self.assertNotIn("Technical details:", text)
            self.assertIn("No Parent update applied", text)
        finally:
            shutil.rmtree(repo, ignore_errors=True)

    def test_same_upstream_resource_change_recognized_in_grandchild(self):
        repo = Path(tempfile.mkdtemp())
        try:
            (repo / ".git").mkdir()
            root = write_resource_root(repo, version="1.0.0")
            child = write_child(repo, repo / "child", "child-id", "Child", "..", root)
            write_child(repo, repo / "child" / "grand", "grand-id", "Grand", "..", child)
            write_resource_root(repo, version="1.1.0", content=b"New WSL recovery guidance.\n")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                rc = cli_main(["propagate", str(repo), "--yes"])
            self.assertEqual(rc, 0, out.getvalue())
            text = out.getvalue()
            self.assertIn("Same upstream change as review 1", text)
            self.assertEqual(text.count("+New WSL recovery guidance."), 1)
            self.assertEqual(text.count("Applied Parent update to Child"), 2)
        finally:
            shutil.rmtree(repo, ignore_errors=True)

    def test_binary_resource_change_warns_without_fake_text_diff(self):
        repo = Path(tempfile.mkdtemp())
        try:
            (repo / ".git").mkdir()
            root = write_resource_root(repo, version="1.0.0", content=b"binary\x00old")
            write_child(repo, repo / "child", "child-id", "Child", "..", root)
            write_resource_root(repo, version="1.1.0", content=b"binary\x00new")
            out = io.StringIO()
            with contextlib.redirect_stdout(out), mock.patch("builtins.input", return_value="n"):
                rc = cli_main(["propagate", str(repo)])
            self.assertEqual(rc, 0, out.getvalue())
            self.assertIn("Binary content changed; a text diff is not applicable.", out.getvalue())
        finally:
            shutil.rmtree(repo, ignore_errors=True)

    def test_resource_move_shows_old_and_new_locations(self):
        repo = Path(tempfile.mkdtemp())
        try:
            (repo / ".git").mkdir()
            root = write_resource_root(repo, version="1.0.0")
            write_child(repo, repo / "child", "child-id", "Child", "..", root)
            (repo / "docs" / "troubleshooting.md").unlink()
            write_resource_root(
                repo, version="1.1.0", filename="recovery.md",
                content=b"Old WSL recovery guidance.\n",
            )
            out = io.StringIO()
            with contextlib.redirect_stdout(out), mock.patch("builtins.input", return_value="n"):
                rc = cli_main(["propagate", str(repo)])
            self.assertEqual(rc, 0, out.getvalue())
            text = out.getvalue()
            self.assertIn("docs/recovery.md — moved (same content)", text)
            self.assertIn("Moved from: docs/troubleshooting.md", text)
            self.assertIn("Document bytes are identical", text)
            self.assertNotIn("Old accepted snapshot:", text)
        finally:
            shutil.rmtree(repo, ignore_errors=True)

    def test_details_key_discloses_provenance_without_approving(self):
        repo = Path(tempfile.mkdtemp())
        try:
            (repo / ".git").mkdir()
            root = write_resource_root(repo, version="1.0.0")
            write_child(repo, repo / "child", "child-id", "Child", "..", root)
            write_resource_root(repo, version="1.1.0", content=b"New WSL recovery guidance.\n")
            before = (repo / "child" / "CONTEXT.src.md").read_bytes()

            out = io.StringIO()
            with contextlib.redirect_stdout(out), mock.patch(
                "builtins.input", side_effect=["d", "n"]
            ) as prompt:
                rc = cli_main(["propagate", str(repo)])
            self.assertEqual(rc, 0, out.getvalue())
            text = out.getvalue()
            self.assertEqual(prompt.call_count, 2)
            self.assertIn("Detailed Parent review", text)
            self.assertIn("Old accepted snapshot:", text)
            self.assertIn("New authored source: docs/troubleshooting.md", text)
            self.assertIn("Parent Node ID: root-id", text)
            self.assertIn("Parent normalized digest:", text)
            self.assertIn("Review receipt:", text)
            self.assertIn("Review guidance:", text)
            self.assertIn('No Parent update applied to Child "Child".', text)
            self.assertEqual((repo / "child" / "CONTEXT.src.md").read_bytes(), before)
        finally:
            shutil.rmtree(repo, ignore_errors=True)

    def test_verbose_option_and_compatibility_parent_alias_expose_details(self):
        repo = Path(tempfile.mkdtemp())
        try:
            (repo / ".git").mkdir()
            root = write_resource_root(repo, version="1.0.0")
            write_child(repo, repo / "child", "child-id", "Child", "..", root)
            write_resource_root(repo, version="1.1.0", content=b"New WSL recovery guidance.\n")
            for command in (["propagate", str(repo), "--verbose"],
                            ["parent", "propagate", str(repo), "--verbose"]):
                out = io.StringIO()
                with contextlib.redirect_stdout(out), mock.patch("builtins.input", return_value="n"):
                    rc = cli_main(command)
                self.assertEqual(rc, 0, out.getvalue())
                self.assertIn("Detailed Parent review", out.getvalue())
                self.assertIn("Technical details:", out.getvalue())
        finally:
            shutil.rmtree(repo, ignore_errors=True)

    def test_bad_choice_reprompts_and_empty_choice_rejects(self):
        repo = Path(tempfile.mkdtemp())
        try:
            (repo / ".git").mkdir()
            root = write_node(repo, repo, "root", "Root", "1.0.0", "Before")
            write_child(repo, repo / "child", "child", "Child", "..", root)
            write_node(repo, repo, "root", "Root", "1.1.0", "After")
            out = io.StringIO()
            with contextlib.redirect_stdout(out), mock.patch("builtins.input", side_effect=["maybe", ""]):
                rc = cli_main(["propagate", str(repo)])
            self.assertEqual(rc, 0, out.getvalue())
            self.assertIn("Choose y to accept", out.getvalue())
            self.assertEqual(Compiler(repo).compile(repo / "child").parent_packages[0].metadata.version, "1.0.0")
        finally:
            shutil.rmtree(repo, ignore_errors=True)



if __name__ == "__main__":
    unittest.main()
