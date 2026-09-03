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

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from contextcanon.compiler import Compiler
from contextcanon.package import artifact_files


def install(target: Path, compiled) -> None:
    destination = target / ".context" / "sources" / compiled.package_digest
    for rel, content in artifact_files(compiled).items():
        path = destination / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


def parent_block(name: str, locator: str, compiled) -> str:
    return (
        f"## Parent\n\n- [{name}]({locator}) — `{compiled.metadata.version}`\n"
        f'  <!-- ctx:parent id="{compiled.metadata.id}" version="{compiled.metadata.version}" '
        f'normalized-digest="{compiled.normalized_digest}" package-digest="{compiled.package_digest}" -->\n\n'
    )


class ParentChainTests(unittest.TestCase):
    def test_subsystem_receives_only_its_complete_parent_chain(self):
        repo = Path(tempfile.mkdtemp())
        (repo / ".git").mkdir()

        workflow = repo / "library" / "workflow"
        workflow.mkdir(parents=True)
        (workflow / "docs").mkdir()
        (workflow / "docs" / "workflow.md").write_text("# Workflow\n\nReview before merge.\n", encoding="utf-8")
        (workflow / "CONTEXT.src.md").write_text(
            """# Development Workflow — Local Context Source
<!-- ctx:node id="node-workflow" version="1.0.0" -->

## Rules

### Review

- **Review before merge:** Keep coherent changes under human review before merge.
  Why: Automation does not decide product acceptance.
  <!-- ctx:rule id="WF-001" -->

## Topics

### Workflow details

When changing the development workflow:

Required:
- Resource: `docs/workflow.md`
<!-- ctx:topic id="WF-TOPIC" -->
""",
            encoding="utf-8",
        )
        workflow_compiled = Compiler(repo).compile(workflow)

        project = repo / "project"
        project.mkdir()
        (project / "docs").mkdir()
        (project / "docs" / "project.md").write_text("# Project\n\nProject-wide architecture.\n", encoding="utf-8")
        install(project, workflow_compiled)
        (project / "CONTEXT.src.md").write_text(
            f"""# AI Workstation — Local Context Source
<!-- ctx:node id="node-project" version="1.0.0" -->

## Sources

- [Development Workflow](../library/workflow) — `1.0.0`
  <!-- ctx:source id="node-workflow" version="1.0.0" normalized-digest="{workflow_compiled.normalized_digest}" package-digest="{workflow_compiled.package_digest}" -->

## Rules

### Project

- **Repository authority:** The repository is the installation specification.
  Why: Running state must not become undocumented authority.
  <!-- ctx:rule id="PROJECT-001" -->

## Topics

### Project architecture

When changing project-wide architecture:

Required:
- Resource: `docs/project.md`
<!-- ctx:topic id="PROJECT-TOPIC" -->
""",
            encoding="utf-8",
        )
        project_compiled = Compiler(repo).compile(project)

        subsystem = project / "subsystem"
        subsystem.mkdir()
        (subsystem / "docs").mkdir()
        (subsystem / "docs" / "subsystem.md").write_text("# Subsystem\n\nSubsystem-specific operations.\n", encoding="utf-8")
        install(subsystem, project_compiled)
        (subsystem / "CONTEXT.src.md").write_text(
            "# Llama Stack — Local Context Source\n"
            '<!-- ctx:node id="node-subsystem" version="1.0.0" -->\n\n'
            + parent_block("AI Workstation", "..", project_compiled)
            + """## Rules

### Subsystem

- **Keep model runtime isolated:** Runtime changes stay inside the Llama subsystem boundary.
  Why: Other workstation services must not acquire accidental runtime coupling.
  <!-- ctx:rule id="SUBSYSTEM-001" -->

## Topics

### Subsystem operations

When changing Llama subsystem operations:

Required:
- Resource: `docs/subsystem.md`
<!-- ctx:topic id="SUBSYSTEM-TOPIC" -->
""",
            encoding="utf-8",
        )
        subsystem_compiled = Compiler(repo).compile(subsystem)

        sibling = project / "unrelated-sibling"
        sibling.mkdir()
        install(sibling, project_compiled)
        (sibling / "CONTEXT.src.md").write_text(
            "# Unrelated Sibling — Local Context Source\n"
            '<!-- ctx:node id="node-sibling" version="1.0.0" -->\n\n'
            + parent_block("AI Workstation", "..", project_compiled)
            + """## Rules

### Sibling only

- **Sibling secret sauce:** This rule belongs only to the unrelated sibling subtree.
  Why: A selected subsystem must not absorb sibling context.
  <!-- ctx:rule id="SIBLING-001" -->
""",
            encoding="utf-8",
        )
        Compiler(repo).compile(sibling)

        leaf = subsystem / "tool"
        leaf.mkdir()
        install(leaf, subsystem_compiled)
        (leaf / "CONTEXT.src.md").write_text(
            "# Llama Dispatcher — Local Context Source\n"
            '<!-- ctx:node id="node-tool" version="1.0.0" -->\n\n'
            + parent_block("Llama Stack", "..", subsystem_compiled)
            + """## Rules

### Tool

- **Keep dispatch deterministic:** Routing decisions must remain reproducible.
  Why: Debugging requires stable request behavior.
  <!-- ctx:rule id="TOOL-001" -->
""",
            encoding="utf-8",
        )

        leaf_compiled = Compiler(repo).compile(leaf)
        inherited_rules = {(rule.origin_node_id, rule.id) for rule in leaf_compiled.inherited_rules}
        self.assertEqual(
            inherited_rules,
            {
                ("node-workflow", "WF-001"),
                ("node-project", "PROJECT-001"),
                ("node-subsystem", "SUBSYSTEM-001"),
            },
        )
        self.assertNotIn(("node-sibling", "SIBLING-001"), inherited_rules)
        inherited_topics = {(topic.origin_node_id, topic.id) for topic in leaf_compiled.inherited_topics}
        self.assertEqual(
            inherited_topics,
            {
                ("node-workflow", "WF-TOPIC"),
                ("node-project", "PROJECT-TOPIC"),
                ("node-subsystem", "SUBSYSTEM-TOPIC"),
            },
        )
        self.assertEqual(leaf_compiled.source_packages, [])
        self.assertEqual(leaf_compiled.parent_package.metadata.id, "node-subsystem")

        resources = leaf_compiled.resources
        self.assertEqual(
            resources["CONTEXT/references/node-workflow/library/workflow/docs/workflow.md"],
            b"# Workflow\n\nReview before merge.\n",
        )
        self.assertEqual(
            resources["CONTEXT/references/node-project/project/docs/project.md"],
            b"# Project\n\nProject-wide architecture.\n",
        )
        self.assertEqual(
            resources["CONTEXT/references/node-subsystem/project/subsystem/docs/subsystem.md"],
            b"# Subsystem\n\nSubsystem-specific operations.\n",
        )
        self.assertNotIn("node-sibling", "\n".join(resources))
        self.assertIn("Rules from Development Workflow", leaf_compiled.official_markdown)
        self.assertIn("Topics from Development Workflow", leaf_compiled.official_markdown)
        self.assertIn("Rules from AI Workstation", leaf_compiled.official_markdown)
        self.assertIn("Rules from Llama Stack", leaf_compiled.official_markdown)
        self.assertNotIn("Sibling secret sauce", leaf_compiled.official_markdown)

        # The direct Parent package is a self-contained snapshot of the whole
        # effective chain. Ordinary work in the leaf must not require live
        # ancestor/source authoring trees.
        (workflow / "CONTEXT.src.md").unlink()
        (project / "CONTEXT.src.md").unlink()
        (subsystem / "CONTEXT.src.md").unlink()
        (sibling / "CONTEXT.src.md").unlink()
        offline_leaf = Compiler(repo).compile(leaf)
        self.assertEqual(
            {(rule.origin_node_id, rule.id) for rule in offline_leaf.inherited_rules},
            inherited_rules,
        )
        self.assertEqual(
            {(topic.origin_node_id, topic.id) for topic in offline_leaf.inherited_topics},
            inherited_topics,
        )
        self.assertEqual(offline_leaf.resources, resources)


if __name__ == "__main__":
    unittest.main()
'''
    Path("tests/test_parent_chain.py").write_text(test, encoding="utf-8")


def patch_docs() -> None:
    anchor = "## No implicit precedence\n"
    section = '''## Parent chains define scoped context\n\nA semantic Parent chain is the normal way to work inside one project subtree without loading sibling context. Each accepted Parent package already contains its complete effective Rules, Topics and Topic Resources, including reusable Sources attached farther up the chain. A Child therefore needs only its direct accepted Parent package.\n\nFor example:\n\n```text\nDevelopment Workflow Source ──> AI Workstation\n                                 ├──> Llama Stack ──> Llama Dispatcher\n                                 └──> Unrelated Sibling\n```\n\nStarting from `Llama Dispatcher` yields the effective Development Workflow + AI Workstation + Llama Stack + Llama Dispatcher context. It does **not** include `Unrelated Sibling`. This is semantic reachability through accepted package edges, not directory recursion.\n\nBecause every direct Parent pin is a self-contained immutable package snapshot, ordinary use at the leaf remains possible even when the upstream Source/Parent authoring trees are unavailable. Updating any ancestor is still an explicit review/accept operation at the next Child edge.\n\n'''
    p = Path("nodes/library/foundation/docs/composition.md")
    text = p.read_text(encoding="utf-8")
    if anchor not in text:
        raise SystemExit("composition Parent-chain anchor missing")
    p.write_text(text.replace(anchor, section + anchor, 1), encoding="utf-8")


def complete() -> None:
    replace_once(
        "PLAN.md",
        "**Status: ACTIVE — R5 Semantic Parent relationship, step 4 of 5. Fast-run remains ACTIVE.**",
        "**Status: ACTIVE — R5 Semantic Parent relationship, step 5 of 5. Fast-run remains ACTIVE.**",
    )
    replace_once(
        "PLAN.md",
        "- [ ] 4. Prove that the Parent chain carries complete effective Rules, Topics and Resources transitively, so a reusable Development Workflow attached at the intended ancestor reaches descendants without being selected on every Node.",
        "- [x] 4. Prove that the Parent chain carries complete effective Rules, Topics and Resources transitively, so a reusable Development Workflow attached at the intended ancestor reaches descendants without being selected on every Node.",
    )
    state = Path("STATE.md")
    text = state.read_text(encoding="utf-8").rstrip() + "\n\n## Latest Block R5 step 4 Parent-chain checkpoint\n\nThe complete scoped-context chain is now regression-proven: a reusable Development Workflow Source attached at a project ancestor reaches a deep subsystem Tool through immutable Parent packages together with project/subsystem Rules, Topics and exact Resource bytes, while an unrelated sibling contributes nothing. The leaf remains compilable from its direct Parent package even after upstream Source/Parent authoring files are removed, demonstrating that the semantic chain is accepted package reachability rather than filesystem recursion. R5 now proceeds to migration/idempotency/recovery for an already-published ai-workstation-like tree.\n"
    state.write_text(text, encoding="utf-8")


def apply() -> None:
    write_test()
    patch_docs()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--complete":
        complete()
    else:
        apply()
