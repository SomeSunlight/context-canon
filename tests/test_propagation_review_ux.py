from __future__ import annotations

import contextlib
import io
import shutil
import tempfile
import unittest
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


class PropagationReviewUXTests(unittest.TestCase):
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
            self.assertIn("Propagation review", out.getvalue())
            self.assertIn("Applies here?", out.getvalue())
            self.assertIn("Import order is never precedence", out.getvalue())
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


if __name__ == "__main__":
    unittest.main()
