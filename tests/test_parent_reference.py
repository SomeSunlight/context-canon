from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from contextcanon.compiler import Compiler
from contextcanon.outputs import check_outputs, write_outputs
from contextcanon.package import artifact_files, compiled_package, export_digest, load_package
from contextcanon.parser import parse_node
from contextcanon.sources import (
    accept_source_candidate,
    normalize_source_relationships,
    preview_source_candidate_effect,
    review_parent_candidate,
    review_source_candidate,
)
from contextcanon.parser import ContextCanonError


class ParentReferenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        (self.repo / ".git").mkdir()
        (self.repo / "docs").mkdir()
        (self.repo / "docs" / "a.md").write_text("# A guide\n", encoding="utf-8")
        (self.repo / "docs" / "r.md").write_text("# Reference guide\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _node(
        self,
        rel: str,
        node_id: str,
        name: str,
        *,
        version: str = "1.0.0",
        rule_id: str | None = None,
        statement: str = "",
        topic_id: str | None = None,
        resource: str | None = None,
        imports: str = "",
    ) -> Path:
        root = self.repo / rel
        root.mkdir(parents=True, exist_ok=True)
        parts = [
            f"# {name} — Local Context Source",
            f'<!-- ctx:node id="{node_id}" name="{name}" version="{version}" -->',
            "",
        ]
        if imports:
            parts.extend(["## Context Imports", "", imports.rstrip(), ""])
        if rule_id:
            parts.extend(
                [
                    "## Local Rules",
                    "",
                    "### General",
                    "",
                    f"- **{rule_id}:** {statement}",
                    "  Why: regression",
                    f'  <!-- ctx:rule id="{rule_id}" -->',
                    "",
                ]
            )
        if topic_id and resource:
            parts.extend(
                [
                    "## Topics",
                    "",
                    f"### {name} guide",
                    "",
                    f"When {name} background is useful:",
                    "",
                    "Required:",
                    f"- Resource: `{resource}`",
                    f'<!-- ctx:topic id="{topic_id}" -->',
                    "",
                ]
            )
        (root / "CONTEXT.src.md").write_text("\n".join(parts).rstrip() + "\n", encoding="utf-8")
        return root

    def _install(self, child: Path, compiled) -> None:
        package = compiled_package(compiled)
        target = child / ".context" / "sources" / package.package_digest
        for rel, data in artifact_files(compiled).items():
            destination = target / rel
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)

    def _pinned_parent(self, child: Path, parent_root: Path, parent) -> None:
        source = (child / "CONTEXT.src.md").read_text(encoding="utf-8")
        block = (
            "## Parent Context Node\n\n"
            f"- [{parent.metadata.name}]({os.path.relpath(parent_root, child).replace(os.sep, '/')}/) — `{parent.metadata.version}`\n"
            f'  <!-- ctx:parent id="{parent.metadata.id}" version="{parent.metadata.version}" '
            f'normalized-digest="{parent.normalized_digest}" package-digest="{parent.package_digest}" -->\n\n'
        )
        marker = "## Local Rules"
        if marker in source:
            source = source.replace(marker, block + marker, 1)
        else:
            source = source.rstrip() + "\n\n" + block
        (child / "CONTEXT.src.md").write_text(source, encoding="utf-8")

    def test_reference_is_local_non_normative_and_non_transitive(self) -> None:
        a = self._node(
            "nodes/a",
            "node-a",
            "Parent A",
            rule_id="A-1",
            statement="Apply A.",
            topic_id="A-T",
            resource="../../docs/a.md",
        )
        r = self._node(
            "nodes/r",
            "node-r",
            "Reference R",
            rule_id="R-1",
            statement="Do not apply R as a rule.",
            topic_id="R-T",
            resource="../../docs/r.md",
        )
        imports = (
            "- [Parent A](../a/) — `1.0.0` — `relationship=parent`\n"
            '  <!-- ctx:source id="node-a" version="1.0.0" -->\n\n'
            "- [Reference R](../r/) — `1.0.0` — `relationship=reference`\n"
            '  Why: useful background only\n'
            '  <!-- ctx:source id="node-r" version="1.0.0" -->'
        )
        b = self._node(
            "nodes/b",
            "node-b",
            "Node B",
            rule_id="B-1",
            statement="Apply B.",
            imports=imports,
        )

        compiled_b = Compiler(self.repo).compile(b)
        self.assertEqual({rule.id for rule in compiled_b.inherited_rules}, {"A-1"})
        self.assertNotIn("R-1", {rule.id for rule in compiled_b.inherited_rules})
        self.assertIn("## Reference Context — informational only", compiled_b.official_markdown)
        self.assertIn("Reference R", compiled_b.official_markdown)
        self.assertIn("Reference R guide", compiled_b.official_markdown)
        self.assertNotIn("Do not apply R as a rule.", compiled_b.official_markdown)
        self.assertIn('relationship: "reference"', compiled_b.machine_yaml)
        self.assertIn("references:", compiled_b.machine_yaml)

        package_b = compiled_package(compiled_b)
        self.assertEqual(
            {(source.id, source.relationship) for source in package_b.sources},
            {("node-a", "parent"), ("node-r", "reference")},
        )
        self.assertEqual({rule.id for rule in package_b.rules}, {"A-1", "B-1"})
        self.assertNotIn("R-T", {topic.id for topic in package_b.topics})
        self.assertTrue(
            any("/node-r/" in file.path for file in package_b.files),
            "Reference Resources remain available in B's local package",
        )

        c = self._node("nodes/c", "node-c", "Node C", rule_id="C-1", statement="Apply C.")
        self._install(c, compiled_b)
        self._pinned_parent(c, b, compiled_b)
        compiled_c = Compiler(self.repo).compile(c)

        self.assertEqual({rule.id for rule in compiled_c.inherited_rules}, {"A-1", "B-1"})
        self.assertNotIn("R-1", {rule.id for rule in compiled_c.inherited_rules})
        self.assertNotIn("Reference R", compiled_c.official_markdown)
        self.assertNotIn("R-T", {topic.id for topic in compiled_c.inherited_topics})
        self.assertFalse(any("/node-r/" in path for path in compiled_c.resources))

    def test_legacy_source_defaults_to_parent_and_normalizes_without_semantic_change(self) -> None:
        parent = self._node(
            "nodes/p",
            "node-p",
            "Legacy Parent",
            rule_id="P-1",
            statement="Legacy rule remains normative.",
        )
        consumer = self._node("consumer", "consumer", "Consumer")
        source = (consumer / "CONTEXT.src.md").read_text(encoding="utf-8")
        source += (
            "\n## Sources\n\n"
            "- [Legacy Parent](../nodes/p/) — `1.0.0`\n"
            '  <!-- ctx:source id="node-p" version="1.0.0" -->\n'
        )
        (consumer / "CONTEXT.src.md").write_text(source, encoding="utf-8")

        before = Compiler(self.repo).compile(consumer)
        self.assertEqual([rule.id for rule in before.inherited_rules], ["P-1"])
        self.assertEqual(parse_node(consumer, self.repo).sources[0].relationship, "parent")

        self.assertTrue(normalize_source_relationships(consumer))
        normalized_text = (consumer / "CONTEXT.src.md").read_text(encoding="utf-8")
        self.assertIn("## Context Imports", normalized_text)
        self.assertIn("`relationship=parent`", normalized_text)
        self.assertNotIn("## Sources", normalized_text)

        after = Compiler(self.repo).compile(consumer)
        self.assertEqual(before.normalized_digest, after.normalized_digest)
        self.assertEqual([rule.id for rule in after.inherited_rules], ["P-1"])
        self.assertFalse(normalize_source_relationships(consumer))

        (consumer / "CONTEXT.src.md").write_text(
            normalized_text.replace("`relationship=parent`", "`relationship=reference`"),
            encoding="utf-8",
        )
        reference = Compiler(self.repo).compile(consumer)
        self.assertEqual(reference.inherited_rules, [])
        self.assertIn("## Reference Context — informational only", reference.official_markdown)
        self.assertIn("Legacy Parent", reference.official_markdown)

    def test_v3_package_roundtrip_preserves_relationship_kind(self) -> None:
        parent = self._node("p", "p", "Parent", rule_id="P-1", statement="Parent.")
        reference = self._node("r", "r", "Reference", rule_id="R-1", statement="Reference.")
        consumer = self._node(
            "consumer",
            "consumer",
            "Consumer",
            imports=(
                "- [Parent](../p/) — `1.0.0` — `relationship=parent`\n"
                '  <!-- ctx:source id="p" version="1.0.0" -->\n\n'
                "- [Reference](../r/) — `1.0.0` — `relationship=reference`\n"
                '  <!-- ctx:source id="r" version="1.0.0" -->'
            ),
        )
        compiled = Compiler(self.repo).compile(consumer)
        artifact = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: shutil.rmtree(artifact, ignore_errors=True))
        for rel, data in artifact_files(compiled).items():
            destination = artifact / rel
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)

        loaded = load_package(artifact)
        self.assertEqual(
            {(source.id, source.relationship) for source in loaded.sources},
            {("p", "parent"), ("r", "reference")},
        )
        self.assertEqual({rule.id for rule in loaded.rules}, {"P-1"})

    def test_reference_update_reuses_package_review_without_becoming_normative(self) -> None:
        reference = self._node(
            "provider",
            "ref-node",
            "Reference Provider",
            version="1.0.0",
            rule_id="REF-RULE",
            statement="Background v1.",
            topic_id="REF-TOPIC",
            resource="../docs/r.md",
        )
        current_reference = Compiler(self.repo).compile(reference)

        consumer = self._node(
            "consumer",
            "consumer",
            "Consumer",
            rule_id="LOCAL",
            statement="Consumer rule.",
            imports=(
                f"- [Reference Provider](../provider/) — `1.0.0` — `relationship=reference`\n"
                f'  <!-- ctx:source id="ref-node" version="1.0.0" '
                f'normalized-digest="{current_reference.normalized_digest}" '
                f'package-digest="{current_reference.package_digest}" -->'
            ),
        )
        self._install(consumer, current_reference)
        write_outputs(Compiler(self.repo).compile(consumer))

        provider_source = (reference / "CONTEXT.src.md").read_text(encoding="utf-8")
        (reference / "CONTEXT.src.md").write_text(
            provider_source.replace('version="1.0.0"', 'version="1.1.0"', 1)
            .replace("Background v1.", "Background v2."),
            encoding="utf-8",
        )
        candidate_compiled = Compiler(self.repo).compile(reference)
        candidate_root = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: shutil.rmtree(candidate_root, ignore_errors=True))
        for rel, data in artifact_files(candidate_compiled).items():
            destination = candidate_root / rel
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)

        package_diff, receipt = review_source_candidate(consumer, "ref-node", candidate_root)
        self.assertTrue(receipt.is_file())
        self.assertTrue(any(entry.category == "rule" for entry in package_diff.entries))

        local_effect = preview_source_candidate_effect(consumer, "ref-node", candidate_root)
        self.assertFalse(any(entry.category == "rule" for entry in local_effect.entries))

        accept_source_candidate(consumer, "ref-node", candidate_root)
        authored = (consumer / "CONTEXT.src.md").read_text(encoding="utf-8")
        self.assertIn("`relationship=reference`", authored)
        self.assertIn('version="1.1.0"', authored)

        accepted = Compiler(self.repo).compile(consumer)
        self.assertEqual({rule.id for rule in (*accepted.inherited_rules, *accepted.local_rules)}, {"LOCAL"})
        self.assertEqual(accepted.source_packages[0].metadata.version, "1.1.0")
        self.assertIn("Background v2.", candidate_compiled.official_markdown)
        self.assertNotIn("Background v2.", accepted.official_markdown)

    def test_reference_only_parent_change_does_not_change_export_or_propagate(self) -> None:
        reference = self._node(
            "nodes/r",
            "node-r",
            "Reference R",
            version="1.0.0",
            rule_id="R-1",
            statement="Background v1.",
        )
        b = self._node(
            "nodes/b",
            "node-b",
            "Node B",
            rule_id="B-1",
            statement="Normative B.",
            imports=(
                "- [Reference R](../r/) — `1.0.0` — `relationship=reference`\n"
                '  <!-- ctx:source id="node-r" version="1.0.0" -->'
            ),
        )
        compiled_b1 = Compiler(self.repo).compile(b)
        write_outputs(compiled_b1)

        c = self._node("nodes/c", "node-c", "Node C")
        self._install(c, compiled_b1)
        self._pinned_parent(c, b, compiled_b1)
        compiled_c = Compiler(self.repo).compile(c)
        write_outputs(compiled_c)

        r_text = (reference / "CONTEXT.src.md").read_text(encoding="utf-8")
        (reference / "CONTEXT.src.md").write_text(
            r_text.replace('version="1.0.0"', 'version="1.0.1"', 1).replace("Background v1.", "Background v2."),
            encoding="utf-8",
        )
        b_text = (b / "CONTEXT.src.md").read_text(encoding="utf-8")
        (b / "CONTEXT.src.md").write_text(
            b_text.replace("Reference R](../r/) — `1.0.0`", "Reference R](../r/) — `1.0.1`")
            .replace('id="node-r" version="1.0.0"', 'id="node-r" version="1.0.1"'),
            encoding="utf-8",
        )

        compiled_b2 = Compiler(self.repo).compile(b)
        self.assertNotEqual(compiled_b1.package_digest, compiled_b2.package_digest)
        self.assertEqual(export_digest(compiled_package(compiled_b1)), export_digest(compiled_package(compiled_b2)))

        with self.assertRaisesRegex(ContextCanonError, "no changed normative export"):
            review_parent_candidate(c, "node-b")

        unchanged_c = Compiler(self.repo).compile(c)
        self.assertEqual(check_outputs(unchanged_c), [])


if __name__ == "__main__":
    unittest.main()
