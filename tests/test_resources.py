from __future__ import annotations

import contextlib
import io
import json
import subprocess
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from contextcanon.authoring import add_topic
from contextcanon.cli import main
from contextcanon.compiler import Compiler
from contextcanon.diff import diff_compiled
from contextcanon.outputs import check_outputs, write_outputs
from contextcanon.package import load_package
from contextcanon.parser import ContextCanonError, parse_node
from contextcanon.resources import (
    collect_resource_records,
    move_resource,
    reconcile_resource,
    register_resources,
    status_resources,
)


def init_repo() -> Path:
    repo = Path(tempfile.mkdtemp())
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    return repo


def source_text(
    *,
    node_id: str = "node-root",
    node_name: str = "Demo",
    resource: str = "table.md",
    resource_id: str | None = "RESOURCE-TABLE",
    topic_id: str = "TOPIC-TABLE",
) -> str:
    resource_meta = (
        f'  <!-- ctx:resource id="{resource_id}" -->\n'
        if resource_id is not None
        else ""
    )
    return f"""# {node_name} — Local Context Source
<!-- ctx:node id="{node_id}" name="{node_name}" version="0.1.0" -->

## Local Topics

### Table

When consulting the table:

Required:
- Resource: `{resource}`
{resource_meta}<!-- ctx:topic id="{topic_id}" -->
"""


class ResourceIdentityTests(unittest.TestCase):
    def make_single_resource_repo(
        self,
        *,
        resource: str = "table.md",
        resource_id: str | None = "RESOURCE-TABLE",
        content: str = "name,value\nfoo,1\n",
    ) -> Path:
        repo = init_repo()
        (repo / resource).parent.mkdir(parents=True, exist_ok=True)
        (repo / resource).write_text(content, encoding="utf-8")
        (repo / "CONTEXT.src.md").write_text(
            source_text(resource=resource, resource_id=resource_id),
            encoding="utf-8",
        )
        return repo

    def test_parser_accepts_legacy_resource_and_explicit_identity(self) -> None:
        legacy = self.make_single_resource_repo(resource_id=None)
        parsed = parse_node(legacy)
        target = parsed.topics[0].targets[0]
        self.assertEqual(target.locator, "table.md")
        self.assertIsNone(target.resource_id)

        identified = self.make_single_resource_repo()
        parsed = parse_node(identified)
        target = parsed.topics[0].targets[0]
        self.assertEqual(target.locator, "table.md")
        self.assertEqual(target.resource_id, "RESOURCE-TABLE")

    def test_resource_identity_cannot_point_to_two_paths_in_one_node(self) -> None:
        repo = self.make_single_resource_repo()
        (repo / "other.csv").write_text("name,value\nfoo,1\n", encoding="utf-8")
        path = repo / "CONTEXT.src.md"
        path.write_text(
            path.read_text(encoding="utf-8")
            + """
### Other

When consulting the other table:

Required:
- Resource: `other.csv`
  <!-- ctx:resource id="RESOURCE-TABLE" -->
<!-- ctx:topic id="TOPIC-OTHER" -->
""",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ContextCanonError, "attached to both"):
            parse_node(repo)

    def test_register_migrates_path_only_resources_explicitly_and_reuses_same_path(self) -> None:
        repo = self.make_single_resource_repo(resource_id=None)
        path = repo / "CONTEXT.src.md"
        path.write_text(
            path.read_text(encoding="utf-8")
            + """
### Same table again

When consulting the same table elsewhere:

Optional:
- Resource: `table.md`
<!-- ctx:topic id="TOPIC-SAME" -->
""",
            encoding="utf-8",
        )

        before = path.read_text(encoding="utf-8")
        self.assertNotIn("ctx:resource", before)

        result = register_resources(repo)
        self.assertEqual(result.added, 1)
        parsed = parse_node(repo)
        resource_ids = [
            target.resource_id
            for topic in parsed.topics
            for target in topic.targets
            if target.kind == "resource"
        ]
        self.assertEqual(len(resource_ids), 2)
        self.assertIsNotNone(resource_ids[0])
        self.assertEqual(resource_ids[0], resource_ids[1])

        again = register_resources(repo)
        self.assertEqual(again.added, 0)

    def test_author_topic_allocates_resource_identity(self) -> None:
        repo = init_repo()
        (repo / "CONTEXT.src.md").write_text(
            '# Demo — Local Context Source\n'
            '<!-- ctx:node id="node-root" name="Demo" version="0.1.0" -->\n',
            encoding="utf-8",
        )
        (repo / "data.csv").write_text("a,b\n1,2\n", encoding="utf-8")

        add_topic(
            repo,
            title="Data",
            condition="When consulting data:",
            required_resources=("data.csv",),
        )
        parsed = parse_node(repo)
        target = parsed.topics[0].targets[0]
        self.assertRegex(target.resource_id or "", r"^RESOURCE-[0-9A-F]{12}$")
        self.assertIn("ctx:resource", (repo / "CONTEXT.src.md").read_text(encoding="utf-8"))

    def test_package_v2_round_trip_and_path_only_v1_compatibility(self) -> None:
        identified = self.make_single_resource_repo()
        write_outputs(Compiler(identified).compile(identified))
        package = load_package(identified)
        self.assertEqual(package.topics[0].targets[0].resource_id, "RESOURCE-TABLE")
        manifest = json.loads((identified / ".context/package.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["schema"], "contextcanon/package/v2")

        legacy = self.make_single_resource_repo(resource_id=None)
        write_outputs(Compiler(legacy).compile(legacy))
        manifest_path = legacy / ".context/package.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["schema"] = "contextcanon/package/v1"
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        loaded = load_package(legacy)
        self.assertIsNone(loaded.topics[0].targets[0].resource_id)

    def test_pure_identified_move_preserves_topic_semantics_and_renders_resource_move(self) -> None:
        repo = self.make_single_resource_repo()
        before = Compiler(repo).compile(repo)

        (repo / "table.md").rename(repo / "table.csv")
        source = repo / "CONTEXT.src.md"
        source.write_text(
            source.read_text(encoding="utf-8").replace(
                "- Resource: `table.md`",
                "- Resource: `table.csv`",
            ),
            encoding="utf-8",
        )
        after = Compiler(repo).compile(repo)
        result = diff_compiled(before, after)

        topic_changes = [entry for entry in result.entries if entry.category == "topic"]
        resource_changes = [entry for entry in result.entries if entry.category == "resource"]
        self.assertEqual(topic_changes, [])
        moved = [entry for entry in resource_changes if entry.change == "moved"]
        self.assertEqual(len(moved), 1)
        self.assertEqual(moved[0].identity, "node-root#RESOURCE-TABLE")
        self.assertEqual(
            moved[0].before["path"],
            "CONTEXT/references/node-root/table.md",
        )
        self.assertEqual(
            moved[0].after["path"],
            "CONTEXT/references/node-root/table.csv",
        )
        self.assertEqual(before.normalized_digest, after.normalized_digest)
        self.assertNotEqual(before.package_digest, after.package_digest)

    def test_owner_md_to_csv_external_rename_status_and_reconcile(self) -> None:
        repo = self.make_single_resource_repo()
        write_outputs(Compiler(repo).compile(repo))

        (repo / "table.md").rename(repo / "table.csv")
        statuses = status_resources(repo, (repo,))
        self.assertEqual(len(statuses), 1)
        status = statuses[0]
        self.assertEqual(status.state, "candidate")
        self.assertEqual(status.candidates[0].repo_path, "table.csv")
        self.assertEqual(status.candidates[0].lines, 2)

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = main(["resource", "status", str(repo)])
        self.assertEqual(code, 0)
        rendered = stdout.getvalue()
        self.assertIn("R?", rendered)
        self.assertIn("table.md -> table.csv", rendered)
        self.assertIn("exact 100%", rendered)

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = main(["resource", "reconcile", str(repo), "--yes"])
        self.assertEqual(code, 0)
        self.assertIn("Reconciled", stdout.getvalue())

        parsed = parse_node(repo)
        target = parsed.topics[0].targets[0]
        self.assertEqual(target.resource_id, "RESOURCE-TABLE")
        self.assertEqual(target.locator, "table.csv")

        compiled = Compiler(repo).compile(repo)
        write_outputs(compiled)
        self.assertEqual(check_outputs(Compiler(repo).compile(repo)), [])

    def test_ambiguous_identical_candidates_remain_unresolved(self) -> None:
        repo = self.make_single_resource_repo()
        write_outputs(Compiler(repo).compile(repo))
        content = (repo / "table.md").read_bytes()
        (repo / "table.md").unlink()
        (repo / "table-a.csv").write_bytes(content)
        (repo / "table-b.csv").write_bytes(content)

        status = status_resources(repo, (repo,))[0]
        self.assertEqual(status.state, "ambiguous")
        self.assertEqual(
            [candidate.repo_path for candidate in status.candidates],
            ["table-a.csv", "table-b.csv"],
        )
        self.assertIn("table.md", (repo / "CONTEXT.src.md").read_text(encoding="utf-8"))

    def test_interactive_reconcile_resolves_ambiguous_exact_candidates_by_human_choice(self) -> None:
        repo = self.make_single_resource_repo()
        write_outputs(Compiler(repo).compile(repo))
        content = (repo / "table.md").read_bytes()
        (repo / "table.md").unlink()
        (repo / "table-a.csv").write_bytes(content)
        (repo / "table-b.csv").write_bytes(content)

        stdout = io.StringIO()
        with mock.patch("builtins.input", side_effect=["2", "y"]), contextlib.redirect_stdout(stdout):
            code = main(["resource", "reconcile", str(repo)])

        self.assertEqual(code, 0)
        rendered = stdout.getvalue()
        self.assertIn("Ambiguous external Resource rename", rendered)
        self.assertIn("1. table-a.csv", rendered)
        self.assertIn("2. table-b.csv", rendered)
        self.assertIn("Reconciled", rendered)
        target = parse_node(repo).topics[0].targets[0]
        self.assertEqual(target.locator, "table-b.csv")
        self.assertEqual(target.resource_id, "RESOURCE-TABLE")

    def test_yes_mode_never_guesses_between_ambiguous_candidates(self) -> None:
        repo = self.make_single_resource_repo()
        write_outputs(Compiler(repo).compile(repo))
        content = (repo / "table.md").read_bytes()
        (repo / "table.md").unlink()
        (repo / "table-a.csv").write_bytes(content)
        (repo / "table-b.csv").write_bytes(content)

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = main(["resource", "reconcile", str(repo), "--yes"])

        self.assertEqual(code, 0)
        self.assertIn("require a human choice", stdout.getvalue())
        self.assertEqual(parse_node(repo).topics[0].targets[0].locator, "table.md")

    def test_move_reports_inbound_project_markdown_links_without_rewriting_them(self) -> None:
        repo = self.make_single_resource_repo()
        (repo / "README.md").write_text(
            "# Demo\n\nSee [the table](table.md).\n",
            encoding="utf-8",
        )

        result = move_resource(repo, repo / "table.md", repo / "table.csv")

        self.assertEqual(result.inbound_markdown_links, ("README.md -> table.md",))
        self.assertIn("(table.md)", (repo / "README.md").read_text(encoding="utf-8"))

    def test_relative_markdown_closure_change_blocks_external_move(self) -> None:
        repo = self.make_single_resource_repo(
            resource="docs/guide.md",
            content="# Guide\n\n[Details](details.txt)\n",
        )
        (repo / "docs/details.txt").write_text("old details\n", encoding="utf-8")
        write_outputs(Compiler(repo).compile(repo))

        (repo / "moved").mkdir()
        (repo / "docs/guide.md").rename(repo / "moved/guide.md")
        status = status_resources(repo, (repo,))[0]
        self.assertEqual(status.state, "candidate-closure-changed")
        with self.assertRaisesRegex(ContextCanonError, "closure"):
            reconcile_resource(repo, repo / "docs/guide.md", repo / "moved/guide.md")

    def test_explicit_move_updates_file_and_locator_without_changing_id(self) -> None:
        repo = self.make_single_resource_repo()
        result = move_resource(repo, repo / "table.md", repo / "table.csv")
        self.assertFalse((repo / "table.md").exists())
        self.assertTrue((repo / "table.csv").is_file())
        self.assertEqual(result.resource_ids, ("RESOURCE-TABLE",))
        target = parse_node(repo).topics[0].targets[0]
        self.assertEqual(target.locator, "table.csv")
        self.assertEqual(target.resource_id, "RESOURCE-TABLE")

    def test_cross_node_physical_move_is_refused_as_rehome(self) -> None:
        repo = self.make_single_resource_repo()
        child = repo / "child"
        child.mkdir()
        (child / "CONTEXT.src.md").write_text(
            '# Child — Local Context Source\n'
            '<!-- ctx:node id="node-child" name="Child" version="0.1.0" -->\n',
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ContextCanonError, "rehome"):
            move_resource(repo, repo / "table.md", child / "table.md")
        self.assertTrue((repo / "table.md").is_file())

    def test_same_physical_file_referenced_by_two_nodes_reconciles_both_ids(self) -> None:
        repo = self.make_single_resource_repo()
        child = repo / "child"
        child.mkdir()
        (child / "CONTEXT.src.md").write_text(
            source_text(
                node_id="node-child",
                node_name="Child",
                resource="../table.md",
                resource_id="RESOURCE-CHILD",
                topic_id="TOPIC-CHILD",
            ),
            encoding="utf-8",
        )

        for node_root in (repo, child):
            write_outputs(Compiler(repo).compile(node_root))

        (repo / "table.md").rename(repo / "table.csv")
        statuses = status_resources(repo, (repo, child))
        self.assertEqual([status.state for status in statuses], ["candidate", "candidate"])

        result = reconcile_resource(repo, repo / "table.md", repo / "table.csv")
        self.assertEqual(
            set(result.resource_ids),
            {"RESOURCE-TABLE", "RESOURCE-CHILD"},
        )
        root_target = parse_node(repo).topics[0].targets[0]
        child_target = parse_node(child, repo).topics[0].targets[0]
        self.assertEqual(root_target.locator, "table.csv")
        self.assertEqual(child_target.locator, "../table.csv")
        self.assertEqual(root_target.resource_id, "RESOURCE-TABLE")
        self.assertEqual(child_target.resource_id, "RESOURCE-CHILD")

    def test_missing_registered_resource_points_to_noninteractive_status_workflow(self) -> None:
        repo = self.make_single_resource_repo()
        (repo / "table.md").unlink()
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            code = main(["check", str(repo)])
        self.assertEqual(code, 2)
        self.assertIn("contextcanon resource status", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
