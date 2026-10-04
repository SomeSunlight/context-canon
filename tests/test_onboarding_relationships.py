from __future__ import annotations

import contextlib
import io
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from contextcanon.compiler import Compiler
from contextcanon.entry import main as entry_main
from contextcanon.onboarding import prepare_onboarding_evidence
from contextcanon.onboarding_placement import PLACEMENT_PROPOSAL_SCHEMA
from contextcanon.onboarding_reusable_contexts import (
    ASSIGNMENTS_START, ASSIGNMENTS_END, CATALOG_START, CATALOG_END,
    load_accepted_reusable_contexts,
)
from contextcanon.onboarding_structure import (
    STRUCTURE_PROPOSAL_SCHEMA, create_or_load_structure_markdown,
    load_onboarding_structure_proposal, load_structure_markdown,
)
from contextcanon.onboarding_workspace import open_onboarding_workspace
from contextcanon.outputs import write_outputs
from contextcanon.parser import parse_node


class OnboardingRelationshipTests(unittest.TestCase):
    def command(self, args, *, success=True):
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            result = entry_main(args)
        self.assertEqual(result, 0 if success else 2, output.getvalue())
        return output.getvalue()

    def make_case(self, *, subtree=False):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        base = Path(temporary.name)
        repo = base / "repo"
        repo.mkdir()
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        project = repo
        if subtree:
            self.provider(repo, "Enclosing", "enclosing")
            project = repo / "Project"
            project.mkdir()
        (project / "README.md").write_text("# Project\nProject with a Child.\n", encoding="utf-8")
        prepared = prepare_onboarding_evidence(project)
        workspace = open_onboarding_workspace(prepared.snapshot_root, create=True)
        evidence = [{"path": "README.md", "sha256": prepared.included[0].sha256,
                     "start_line": 1, "end_line": 2}]
        nodes = [
            {"key": "N-ROOT", "name": "Project", "parent_key": None, "suggested_path": "."},
            {"key": "N-CHILD", "name": "Child", "parent_key": "N-ROOT", "suggested_path": "child"},
        ]
        for node in nodes:
            node.update(lifecycle="current", purpose="Reviewed responsibility.",
                        rationale="Reviewed project structure.", confidence="high", evidence=evidence)
        workspace.structure_proposal_path.write_text(json.dumps({
            "schema": STRUCTURE_PROPOSAL_SCHEMA, "evidence_digest": prepared.evidence_digest,
            "nodes": nodes, "knowledge_bodies": [], "source_reuses": [],
        }), encoding="utf-8")
        create_or_load_structure_markdown(prepared.snapshot_root, workspace.structure_proposal_path, workspace.structure_path)
        proposal = load_onboarding_structure_proposal(workspace.structure_proposal_path, prepared.snapshot_root)
        structure = load_structure_markdown(workspace.structure_path, proposal)
        self.command(["onboard", "structure-materialize", str(prepared.snapshot_root)])
        catalog = base / "catalog"
        self.provider(catalog / "workflow", "Workflow", "workflow")
        self.provider(catalog / "knowledge", "Knowledge", "knowledge")
        return repo, project, prepared, workspace, structure, catalog

    def provider(self, root, name, identity):
        root.mkdir(parents=True, exist_ok=True)
        (root / "guide.md").write_text(f"# {name} guide\nUseful information.\n", encoding="utf-8")
        (root / "CONTEXT.src.md").write_text(
            f'# {name}\n<!-- ctx:node id="{identity}" name="{name}" version="1.0.0" -->\n\n'
            f'## Local Rules\n\n### Governance\n\n- **{name} rule:** Apply {name} constraints.\n'
            f'  Why: Shared governance.\n  <!-- ctx:rule id="{identity.upper()}-RULE" -->\n\n'
            f'## Local Topics\n\n### {name} guide\n\nWhen consulting {name}:\n\nRequired:\n'
            f'- Resource: `guide.md`\n  <!-- ctx:resource id="{identity.upper()}-RESOURCE" -->\n\n'
            f'<!-- ctx:topic id="{identity.upper()}-TOPIC" -->\n', encoding="utf-8")
        write_outputs(Compiler(root).compile(root))

    def accept_imports(self, case, choices):
        _, _, prepared, workspace, structure, catalog = case
        self.command(["onboard", "reusable-contexts", str(prepared.snapshot_root)])
        text = workspace.reusable_contexts_path.read_text(encoding="utf-8")
        text = text.replace(CATALOG_START + "\n" + CATALOG_END,
                            CATALOG_START + f"\n{catalog}\n" + CATALOG_END)
        assignments = ""
        for target, name, relationship in choices:
            assignments += (f"{target} ← {name} (1.0.0) [{relationship.title()}]\n"
                            f"Why: Reviewed {relationship} at this Node.\n")
        text = text.replace(ASSIGNMENTS_START + "\n```text\n```\n" + ASSIGNMENTS_END,
                            ASSIGNMENTS_START + "\n```text\n" + assignments + "```\n" + ASSIGNMENTS_END)
        text = text.replace("Decision: `pending`", "Decision: `accept`")
        workspace.reusable_contexts_path.write_text(text, encoding="utf-8")
        self.command(["onboard", "reusable-contexts", str(prepared.snapshot_root)])
        accepted = load_accepted_reusable_contexts(workspace.reusable_contexts_path,
                                                  prepared.snapshot_root, prepared.evidence_digest, structure)
        self.assertEqual([a.relationship for a in accepted.assignments], [r for _, _, r in choices])
        return accepted

    def placement(self, case):
        _, _, prepared, workspace, structure, _ = case
        self.command(["onboard", "placement-instruction", str(prepared.snapshot_root)])
        instruction = workspace.placement_instruction_path.read_text(encoding="utf-8")
        self.assertIn("onboarding-placement-proposal/v2", instruction)
        self.assertNotIn("source_reuses", instruction)
        workspace.placement_proposal_path.write_text(json.dumps({
            "schema": PLACEMENT_PROPOSAL_SCHEMA, "evidence_digest": prepared.evidence_digest,
            "structure_digest": structure.structure_digest, "items": [], "source_edits": [],
        }), encoding="utf-8")
        self.command(["onboard", "placement-validate", str(prepared.snapshot_root)])
        self.command(["onboard", "placement-review", str(prepared.snapshot_root)])
        return instruction

    def publish(self, case):
        repo, project, prepared, workspace, _, _ = case
        self.command(["onboard", "placement-preview", str(prepared.snapshot_root)])
        preview = workspace.placement_preview_path.read_text(encoding="utf-8")
        self.command(["onboard", "placement-publish", str(prepared.snapshot_root)])
        published_bytes = {(root / "CONTEXT.src.md"): (root / "CONTEXT.src.md").read_bytes()
                           for root in (project, project / "child")}
        self.command(["onboard", "placement-publish", str(prepared.snapshot_root)])
        self.assertTrue(all(path.read_bytes() == before for path, before in published_bytes.items()))
        for root in (project, project / "child"):
            source = (root / "CONTEXT.src.md").read_text(encoding="utf-8")
            self.assertEqual(source.count("## Context Imports"), 1)
            for legacy in ("## Parent Context Node", "ctx:parent", "## Sources", "contextcanon-placement-parent:start"):
                self.assertNotIn(legacy, source)
            self.assertEqual(source.count("contextcanon-placement-sources:start"), 1)
        self.command(["build", "--all", str(repo)])
        self.command(["check", "--all", str(repo)])
        self.command(["propagate", "--status", "--all", str(repo)])
        return preview

    def test_root_parent_reference_and_multiple_parents(self):
        for relationships in (("parent",), ("reference",), ("parent", "parent"), ("parent", "reference")):
            with self.subTest(relationships=relationships):
                case = self.make_case()
                choices = [("Project (.)", name, relation)
                           for name, relation in zip(("Workflow", "Knowledge"), relationships)]
                accepted = self.accept_imports(case, choices)
                instruction = self.placement(case)
                for _, name, relationship in choices:
                    self.assertIn(f"{name}** (`1.0.0`) [{relationship.title()}]", instruction)
                preview = self.publish(case)
                repo, project, prepared, _, _, _ = case
                parsed = parse_node(project, repo)
                self.assertEqual([s.relationship for s in parsed.sources], list(relationships))
                record = json.loads((prepared.snapshot_root / "placement-acceptance.json").read_text())
                self.assertEqual([s["relationship"] for s in record["sources"]], list(relationships))
                for _, name, relation in choices:
                    self.assertIn(f"**{name}** — **{relation.title()}**", preview)
                root_package = Compiler(repo).compile(project)
                child_package = Compiler(repo).compile(project / "child")
                root_rules = {r.id for r in root_package.inherited_rules}
                child_rules = {r.id for r in child_package.inherited_rules}
                for name, relation in zip(("workflow", "knowledge"), relationships):
                    self.assertEqual(f"{name.upper()}-RULE" in root_rules, relation == "parent")
                    self.assertEqual(f"{name.upper()}-RULE" in child_rules, relation == "parent")
                    child_topics = {t.id for t in child_package.inherited_topics}
                    self.assertEqual(f"{name.upper()}-TOPIC" in child_topics, relation == "parent")
                    if relation == "reference":
                        self.assertIn(f"{name.title()} guide", root_package.official_markdown)
                        self.assertNotIn(f"{name.title()} guide", child_package.official_markdown)
                # Compare actual compiler semantics with a manually authored import.
                manual = repo / "manual"
                manual.mkdir()
                (manual / "CONTEXT.src.md").write_text(
                    '# Manual\n<!-- ctx:node id="manual" name="Manual" version="1.0.0" -->\n\n'
                    '## Context Imports\n\n' + "\n".join(
                        f'- [{a.source_name}](../contextcanon.yaml) — `{a.source_version}` — `relationship={a.relationship}`\n'
                        f'  <!-- ctx:source id="{a.source_node_id}" version="{a.source_version}" '
                        f'normalized-digest="{a.source_normalized_digest}" package-digest="{a.source_package_digest}" -->'
                        for a in accepted.assignments
                    ), encoding="utf-8")
                shutil.copytree(project / ".context" / "sources", manual / ".context" / "sources")
                self.assertEqual(root_rules, {r.id for r in Compiler(repo).compile(manual).inherited_rules})

    def test_subtree_existing_parent_alone_plus_parent_or_reference(self):
        for relation in (None, "parent", "reference"):
            with self.subTest(relationship=relation):
                case = self.make_case(subtree=True)
                choices = [] if relation is None else [("Project (.)", "Workflow", relation)]
                self.accept_imports(case, choices)
                gate = case[3].reusable_contexts_path.read_text(encoding="utf-8")
                self.assertIn("Project (.) ← Enclosing (1.0.0) [Parent]", gate)
                self.placement(case)
                self.publish(case)
                repo, project, _, _, _, _ = case
                parsed = parse_node(project, repo)
                self.assertEqual(sum(s.id == "enclosing" for s in parsed.sources), 1)
                self.assertEqual(len(parsed.sources), 1 + bool(relation))
                rules = {r.id for r in Compiler(repo).compile(project / "child").inherited_rules}
                self.assertIn("ENCLOSING-RULE", rules)
                self.assertEqual("WORKFLOW-RULE" in rules, relation == "parent")

    def test_same_package_parent_at_root_reference_at_child_preserves_exact_import_identity(self):
        case = self.make_case()
        self.accept_imports(case, [("Project (.)", "Workflow", "parent"), ("Child (child)", "Workflow", "reference")])
        self.placement(case)
        self.publish(case)
        repo, project, prepared, _, _, _ = case
        child = parse_node(project / "child", repo)
        self.assertEqual(next(s.relationship for s in child.sources if s.id == "workflow"), "reference")
        entries = json.loads((prepared.snapshot_root / "placement-acceptance.json").read_text())["sources"]
        self.assertEqual({(s["target_node_key"], s["relationship"]) for s in entries},
                         {("N-ROOT", "parent"), ("N-CHILD", "reference")})

    def test_reset_from_step07_rolls_back_publication_and_can_choose_new_relationship(self):
        case = self.make_case(subtree=True)
        self.accept_imports(case, [("Project (.)", "Workflow", "reference")])
        self.placement(case)
        self.publish(case)
        repo, project, prepared, workspace, _, _ = case
        self.command(["onboard", "reset", str(prepared.snapshot_root), "--from", "8"])
        recovered = load_accepted_reusable_contexts(workspace.reusable_contexts_path, prepared.snapshot_root,
                                                   prepared.evidence_digest, case[4])
        self.assertEqual(recovered.assignments[0].relationship, "reference")
        self.placement(case)
        self.publish(case)
        self.command(["onboard", "reset", str(prepared.snapshot_root), "--from", "7"])
        self.assertTrue(prepared.snapshot_root.is_dir())
        self.assertFalse(workspace.reusable_contexts_path.exists())
        self.assertFalse((prepared.snapshot_root / "reusable-contexts.json").exists())
        self.assertEqual(parse_node(project, repo).sources, ())
        self.accept_imports(case, [("Project (.)", "Workflow", "parent")])
        self.placement(case)
        self.publish(case)
        self.assertIn("WORKFLOW-RULE", {r.id for r in Compiler(repo).compile(project / "child").inherited_rules})

    def test_step10_cannot_silently_change_step07_relationship(self):
        case = self.make_case()
        self.accept_imports(case, [("Project (.)", "Workflow", "reference")])
        self.placement(case)
        prepared, workspace = case[2], case[3]
        text = workspace.placement_path.read_text(encoding="utf-8")
        workspace.placement_path.write_text(text.replace('relationship="reference"', 'relationship="parent"'), encoding="utf-8")
        error = self.command(["onboard", "placement-preview", str(prepared.snapshot_root)], success=False)
        self.assertIn("Relationship differs", error)
        workspace.placement_path.write_text(text.replace('relationship="reference"', 'relationship="parent"')
                                            .replace("Relationship: `reference`", "Relationship: `parent`"), encoding="utf-8")
        for command in ("placement-review", "placement-preview", "placement-publish"):
            error = self.command(["onboard", command, str(prepared.snapshot_root)], success=False)
            self.assertIn("accepted STEP-07 choices", error)

    def test_new_assignments_require_explicit_choice_and_enclosing_parent_is_not_an_assignment(self):
        case = self.make_case(subtree=True)
        self.accept_imports(case, [("Project (.)", "Workflow", "parent")])
        prepared, workspace = case[2], case[3]
        text = workspace.reusable_contexts_path.read_text(encoding="utf-8")
        workspace.reusable_contexts_path.write_text(text.replace("Workflow (1.0.0) [Parent]", "Workflow (1.0.0)"), encoding="utf-8")
        self.assertIn("explicit [Parent] or [Reference]", self.command(["onboard", "reusable-contexts", str(prepared.snapshot_root)], success=False))
        parent_root = case[0]
        subprocess.run(["git", "-C", str(parent_root), "add", "CONTEXT.src.md", "CONTEXT.md", "CONTEXT", ".context/package.json", ".context/context.yaml"], check=True)
        subprocess.run(["git", "-C", str(parent_root), "-c", "user.name=Test", "-c", "user.email=test@example.org", "commit", "-qm", "Enclosing package"], check=True)
        duplicate = text.replace(str(case[5]), str(parent_root)).replace("Workflow (1.0.0)", "Enclosing (1.0.0)")
        workspace.reusable_contexts_path.write_text(duplicate, encoding="utf-8")
        self.assertIn("already the enclosing Parent", self.command(["onboard", "reusable-contexts", str(prepared.snapshot_root)], success=False))

    def test_v2_placement_cannot_invent_relationships(self):
        case = self.make_case()
        self.accept_imports(case, [])
        self.placement(case)
        path = case[3].placement_proposal_path
        raw = json.loads(path.read_text())
        raw["source_reuses"] = []
        path.write_text(json.dumps(raw), encoding="utf-8")
        self.assertIn("unknown fields: source_reuses", self.command(["onboard", "placement-validate", str(case[2].snapshot_root)], success=False))

    def test_legacy_cli_flags_cannot_bypass_accepted_step07(self):
        case = self.make_case()
        self.accept_imports(case, [("Project (.)", "Workflow", "reference")])
        error = self.command(["onboard", "placement-instruction", str(case[2].snapshot_root),
                              "--catalog-package", str(case[5] / "workflow")], success=False)
        self.assertIn("STEP 07 owns reusable Context Imports", error)
        self.placement(case)
        error = self.command(["onboard", "placement-review", str(case[2].snapshot_root),
                              "--owner-source", "N-ROOT=workflow"], success=False)
        self.assertIn("STEP 07 owns reusable Context Imports", error)
