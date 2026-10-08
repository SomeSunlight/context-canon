from __future__ import annotations

import contextlib
import io
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from contextcanon.cli import main
from contextcanon.compiler import Compiler
from contextcanon.package import artifact_files, compiled_package
from contextcanon.parser import ContextCanonError, parse_node
from contextcanon.source_authoring import format_source, migrate_sources
from contextcanon.source_help import GUIDE_MARKER, GUIDE_NAME, guide_text


class SourceAuthoringTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.repo = Path(self.temporary.name).resolve()
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)

    def node(self, name="Demo", body=""):
        root = self.repo / name
        root.mkdir(parents=True)
        (root / "CONTEXT.src.md").write_text(
            f'# {name}\n<!-- ctx:node id="node-{name}" name="{name}" version="1.0.0" -->\n\n' + body,
            encoding="utf-8",
        )
        (root / "payload sample.jsonc").write_text("// illustrative\n{}\n", encoding="utf-8")
        return root

    def run_cli(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            result = main(list(args))
        return result, out.getvalue(), err.getvalue()

    def topic(self, *, identified=True):
        return ('## Local Topics\n\n### Payloads\n\nWhen comparing payloads:\n\nRequired:\n'
                '- Resource: `payload sample.jsonc`\n  Why: Version 6 - VALID\n'
                + ('  <!-- ctx:resource id="RESOURCE-PAYLOAD" -->\n<!-- ctx:topic id="TOPIC-PAYLOAD" -->\n' if identified else ""))

    def test_build_all_migrates_existing_nested_sources_and_is_idempotent(self):
        roots = [self.node("01 Project", '## Local Overview\n\nOrdinary orientation.\n\n## Sources\n'),
                 self.node("01 Project/02 Subproject", self.topic())]
        result, _, err = self.run_cli("build", "--all", str(self.repo))
        self.assertEqual(result, 0, err)
        originals = {}
        for root in roots:
            text = (root / "CONTEXT.src.md").read_text(encoding="utf-8")
            self.assertEqual(next(line for line in text.splitlines() if line.startswith("## ")), "## Context Imports")
            self.assertIn('[the source format guide](CONTEXT-format.md)', text)
            self.assertIn("contextcanon:format Node", text)
            self.assertTrue((root / GUIDE_NAME).is_file())
            originals[root] = (root / "CONTEXT.src.md").read_bytes()
            compiled = Compiler(self.repo).compile(root)
            self.assertNotIn("contextcanon:format", compiled.official_markdown)
            self.assertNotIn("New Rules, Topics", compiled.machine_yaml)
            self.assertNotIn(GUIDE_NAME, artifact_files(compiled))
        self.assertEqual(self.run_cli("build", "--all", str(self.repo))[0], 0)
        self.assertEqual({root: (root / "CONTEXT.src.md").read_bytes() for root in roots}, originals)
        self.assertEqual(self.run_cli("check", "--all", str(self.repo))[0], 0)

    def test_help_only_preserves_compiled_package_identity(self):
        root = self.node(body='## Local Overview\n\n  Indented orientation.\n\n' + self.topic())
        before = Compiler(self.repo).compile(root)
        self.assertEqual(migrate_sources(self.repo, [root]), [root])
        after = Compiler(self.repo).compile(root)
        self.assertEqual((before.normalized_digest, before.package_digest), (after.normalized_digest, after.package_digest))
        self.assertEqual(artifact_files(before), artifact_files(after))
        self.assertIn("  Indented orientation.", (root / "CONTEXT.src.md").read_text(encoding="utf-8"))

    def test_build_adds_new_rule_topic_and_shared_resource_ids_once(self):
        root = self.node(body='## Local Rules\n\n### Security\n\n- **Keep secrets out:** Do not commit credentials.\n  Why: Git is not a secret store.\n\n'
                         + self.topic(identified=False) + '\n### Old samples\n\nWhen comparing old payloads:\n\nOptional:\n- Resource: `payload sample.jsonc`\n  Why: OBSOLETE\n')
        self.assertEqual(self.run_cli("build", str(root))[0], 0)
        parsed = parse_node(root)
        self.assertTrue(parsed.rules[0].id.startswith("RULE-"))
        self.assertTrue(all(topic.id.startswith("TOPIC-") for topic in parsed.topics))
        targets = [topic.targets[0] for topic in parsed.topics]
        self.assertEqual(targets[0].resource_id, targets[1].resource_id)
        self.assertTrue(targets[0].resource_id.startswith("RESOURCE-"))
        source = (root / "CONTEXT.src.md").read_bytes()
        self.assertEqual(self.run_cli("build", str(root))[0], 0)
        self.assertEqual((root / "CONTEXT.src.md").read_bytes(), source)

    def test_new_target_reuses_later_existing_resource_identity(self):
        root = self.node(body=self.topic(identified=False) + '\n### Existing\n\nWhen needed:\nRequired:\n- Resource: `payload sample.jsonc`\n  <!-- ctx:resource id="RESOURCE-EXISTING" -->\n<!-- ctx:topic id="TOPIC-EXISTING" -->\n')
        migrate_sources(self.repo, [root])
        self.assertEqual({target.resource_id for topic in parse_node(root).topics for target in topic.targets}, {"RESOURCE-EXISTING"})

    def test_placement_identity_moves_after_correct_item_and_stays_there(self):
        root = self.node(body='## Local State\n\n<!-- cc:placement-state id="STATE-A" -->\n- Current state A.\n\n<!-- cc:placement-state id="STATE-B" -->\n- Current state B.\n\n## Local Plan\n\n<!-- cc:placement-plan id="PLAN-A" -->\n- Planned work.\n')
        migrate_sources(self.repo, [root])
        text = (root / "CONTEXT.src.md").read_text(encoding="utf-8")
        self.assertIn('- Current state A.\n  <!-- cc:placement-state id="STATE-A" -->', text)
        self.assertIn('- Current state B.\n  <!-- cc:placement-state id="STATE-B" -->', text)
        self.assertIn('- Planned work.\n  <!-- cc:placement-plan id="PLAN-A" -->', text)
        self.assertEqual(format_source(text), text)

    def test_imports_first_preserve_parent_reference_pins_and_offline_packages(self):
        provider = self.node("Provider", self.topic())
        compiled = Compiler(self.repo).compile(provider)
        package = compiled_package(compiled)
        roots = []
        for relationship in ("parent", "reference"):
            root = self.node(relationship, '## Local Overview\n\nLocal description.\n\n## Context Imports\n\n'
                             f'- [Provider](../gone/) — `1.0.0` — `relationship={relationship}`\n  Why: Preserve my choice.\n'
                             f'  <!-- ctx:source id="node-Provider" version="1.0.0" normalized-digest="{package.normalized_digest}" package-digest="{package.package_digest}" -->\n')
            for path, content in artifact_files(compiled).items():
                destination = root / ".context" / "sources" / package.package_digest / path
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(content)
            roots.append(root)
        migrate_sources(self.repo, roots)
        for root, relationship in zip(roots, ("parent", "reference")):
            ref = parse_node(root).sources[0]
            self.assertEqual((ref.relationship, ref.normalized_digest, ref.package_digest, ref.why),
                             (relationship, package.normalized_digest, package.package_digest, "Preserve my choice."))
            self.assertEqual(len(Compiler(self.repo).compile(root).inherited_topics), 1 if relationship == "parent" else 0)

    def test_legacy_parent_and_sources_consolidate_without_changing_pins(self):
        provider = self.node("Provider")
        compiled = Compiler(self.repo).compile(provider)
        package = compiled_package(compiled)
        root = self.node(body='## Local Overview\n\nLocal.\n\n## Parent Context Node\n\n'
                         '- [Provider](../Provider/) — `1.0.0`\n'
                         f'  <!-- ctx:parent id="node-Provider" version="1.0.0" normalized-digest="{package.normalized_digest}" package-digest="{package.package_digest}" -->\n')
        self.assertEqual(self.run_cli("build", str(provider))[0], 0)
        self.assertEqual(self.run_cli("build", str(root))[0], 0)
        text = (root / "CONTEXT.src.md").read_text(encoding="utf-8")
        self.assertNotIn("ctx:parent", text)
        self.assertEqual(parse_node(root).sources[0].package_digest, package.package_digest)
        self.assertIn("`relationship=parent`", text)

    def test_check_is_read_only_even_when_help_and_ids_are_missing(self):
        root = self.node(body=self.topic(identified=False))
        original = (root / "CONTEXT.src.md").read_bytes()
        result, _, error = self.run_cli("check", str(root))
        self.assertEqual(result, 2)
        self.assertIn("run contextcanon build", error)
        self.assertEqual((root / "CONTEXT.src.md").read_bytes(), original)
        self.assertFalse((root / GUIDE_NAME).exists())
        self.assertFalse((self.repo / ".context").exists())

    def test_invalid_resource_reports_original_line_example_and_both_help_locations(self):
        root = self.node(body=self.topic(identified=False).replace('`payload sample.jsonc`', 'samples/variant-6.jsonc (Version 6 - VALID)'))
        original = (root / "CONTEXT.src.md").read_bytes()
        bad_number = next(i for i, line in enumerate(original.decode().splitlines(), 1) if line.startswith("- Resource:"))
        for command in ("check", "build"):
            result, _, error = self.run_cli(command, str(root))
            self.assertEqual(result, 2)
            if command == "build":
                self.assertIn(f'CONTEXT.src.md:{bad_number}:', error)
                self.assertIn('Example: - Resource: `samples/variant-6.jsonc`', error)
                self.assertIn("move trailing annotations", error)
            self.assertIn("contextcanon:format Local Topics", error)
            self.assertIn("CONTEXT-format.md", error)
            self.assertIn("docs/context-source-format.md", error)
            self.assertEqual((root / "CONTEXT.src.md").read_bytes(), original)

    def test_invalid_rules_are_not_silently_dropped_or_repaired(self):
        for body in ('- Wrong rule form\n', '- **Title:** Statement\n  Why: \n', '- **Title:** Statement\nWhy: Unindented\n', '- **Title:** Statement\n  Why: A\n  Why: B\n', '- **Title:** Statement\n  Why: A\n  <!-- ctx:rule id="" -->\n'):
            with self.subTest(body=body):
                root = self.node(str(len(list(self.repo.iterdir()))), '## Local Rules\n\n### Rules\n\n' + body)
                original = (root / "CONTEXT.src.md").read_bytes()
                result, _, error = self.run_cli("build", str(root))
                self.assertEqual(result, 2)
                self.assertIn("contextcanon:format Local Rules", error)
                self.assertIn("- **Title:** Statement", error)
                self.assertEqual((root / "CONTEXT.src.md").read_bytes(), original)

    def test_all_sources_are_validated_before_any_write(self):
        good = self.node("A", self.topic(identified=False))
        bad = self.node("B", '## Local Rules\n\n- invalid\n')
        originals = {root: (root / "CONTEXT.src.md").read_bytes() for root in (good, bad)}
        self.assertEqual(self.run_cli("build", "--all", str(self.repo))[0], 2)
        self.assertEqual({root: (root / "CONTEXT.src.md").read_bytes() for root in originals}, originals)

    def test_missing_resource_fails_compile_without_writing_candidate_ids(self):
        root = self.node(body=self.topic(identified=False))
        (root / "payload sample.jsonc").unlink()
        original = (root / "CONTEXT.src.md").read_bytes()
        self.assertEqual(self.run_cli("build", str(root))[0], 2)
        self.assertEqual((root / "CONTEXT.src.md").read_bytes(), original)

    def test_invalid_topic_and_corrupt_identity_are_not_repaired(self):
        for body in (self.topic(identified=False).replace('When comparing payloads:\n', ''),
                     self.topic(identified=False).replace('Required:\n', ''),
                     self.topic(identified=False).replace('### Payloads', 'Payloads'),
                     self.topic().replace('id="TOPIC-PAYLOAD"', 'id=""'),
                     self.topic().replace('ctx:resource id="RESOURCE-PAYLOAD"', 'ctx:resource'),
                     self.topic() + '<!-- ctx:topic id="DUPLICATE" -->\n'):
            with self.subTest(body=body):
                root = self.node(str(len(list(self.repo.iterdir()))), body)
                original = (root / "CONTEXT.src.md").read_bytes()
                result, _, error = self.run_cli("build", str(root))
                self.assertEqual(result, 2)
                self.assertIn("contextcanon:format Local Topics", error)
                self.assertEqual((root / "CONTEXT.src.md").read_bytes(), original)

    def test_implicit_legacy_source_default_becomes_explicit_parent(self):
        provider = self.node("Provider")
        root = self.node(body='## Local Overview\n\nHere.\n\n## Sources\n\n- [Provider](../Provider/) — `1.0.0`\n  <!-- ctx:source id="node-Provider" version="1.0.0" -->\n')
        migrate_sources(self.repo, [root])
        source = parse_node(root).sources[0]
        self.assertEqual((source.relationship, source.version, source.id), ("parent", "1.0.0", "node-Provider"))
        text = (root / "CONTEXT.src.md").read_text(encoding="utf-8")
        self.assertIn('`relationship=parent`', text)
        self.assertNotIn('## Sources\n', text)

    def test_owned_guide_with_windows_newlines_can_be_refreshed(self):
        root = self.node()
        (root / GUIDE_NAME).write_bytes((GUIDE_MARKER + "\r\nOld help\r\n").encode("utf-8"))
        self.assertEqual(self.run_cli("build", str(root))[0], 0)
        self.assertEqual((root / GUIDE_NAME).read_text(encoding="utf-8"), guide_text())

    def test_contradictory_legacy_parent_kind_fails_without_reclassification(self):
        root = self.node(body='## Parent Context Node\n\n- [Provider](../Provider/) — `1.0.0` — `relationship=reference`\n'
                         '  <!-- ctx:parent id="provider" version="1.0.0" normalized-digest="' + '1' * 64 + '" package-digest="' + '2' * 64 + '" -->\n')
        original = (root / "CONTEXT.src.md").read_bytes()
        result, _, error = self.run_cli("build", str(root))
        self.assertEqual(result, 2)
        self.assertIn("contextcanon:format Context Imports", error)
        self.assertEqual((root / "CONTEXT.src.md").read_bytes(), original)

    def test_mid_write_failure_restores_previous_sources(self):
        from contextcanon import source_authoring
        roots = [self.node("A"), self.node("B")]
        originals = {root: (root / "CONTEXT.src.md").read_bytes() for root in roots}
        replace = source_authoring._replace_bytes
        failed = False
        def fail_second(path, content):
            nonlocal failed
            if path.parent == roots[1] and not failed:
                failed = True
                raise OSError("simulated write failure")
            replace(path, content)
        with patch.object(source_authoring, "_replace_bytes", side_effect=fail_second):
            with self.assertRaisesRegex(ContextCanonError, "previous sources restored"):
                migrate_sources(self.repo, roots)
        self.assertEqual({root: (root / "CONTEXT.src.md").read_bytes() for root in roots}, originals)

    def test_concurrent_edit_is_preserved_and_earlier_write_rolled_back(self):
        from contextcanon import source_authoring
        roots = [self.node("A"), self.node("B")]
        original = (roots[0] / "CONTEXT.src.md").read_bytes()
        edited = (roots[1] / "CONTEXT.src.md").read_bytes() + b"\nConcurrent edit.\n"
        replace = source_authoring._replace_bytes
        def edit_second(path, content):
            replace(path, content)
            if path.parent == roots[0] and b"source-help" in content:
                (roots[1] / "CONTEXT.src.md").write_bytes(edited)
        with patch.object(source_authoring, "_replace_bytes", side_effect=edit_second):
            with self.assertRaisesRegex(ContextCanonError, "source changed during build"):
                migrate_sources(self.repo, roots)
        self.assertEqual((roots[0] / "CONTEXT.src.md").read_bytes(), original)
        self.assertEqual((roots[1] / "CONTEXT.src.md").read_bytes(), edited)

    def test_unowned_guide_is_not_overwritten_and_no_source_is_migrated(self):
        root = self.node()
        (root / GUIDE_NAME).write_text("My document\n", encoding="utf-8")
        original = (root / "CONTEXT.src.md").read_bytes()
        result, _, error = self.run_cli("build", str(root))
        self.assertEqual(result, 2)
        self.assertIn("not ContextCanon-owned", error)
        self.assertEqual((root / GUIDE_NAME).read_text(encoding="utf-8"), "My document\n")
        self.assertEqual((root / "CONTEXT.src.md").read_bytes(), original)

    def test_crlf_bom_non_ascii_and_spaces_survive_migration(self):
        root = self.node("Übungsprojekt mit Raum", '## Local Overview\n\nÄnderungen für die Zukunft.\n')
        source = root / "CONTEXT.src.md"
        original = source.read_bytes()
        source.write_bytes(b"\xef\xbb\xbf" + original.replace(b"\n", b"\r\n"))
        migrate_sources(self.repo, [root])
        result = source.read_bytes()
        self.assertTrue(result.startswith(b"\xef\xbb\xbf"))
        self.assertNotIn(b"\n", result.replace(b"\r\n", b""))
        self.assertIn("Änderungen für die Zukunft.", result.decode("utf-8-sig"))
        self.assertEqual(migrate_sources(self.repo, [root]), [])

    def test_nested_comment_examples_never_become_machine_semantics(self):
        root = self.node(body='## Local Rules\n\n<!-- Example only\n### Example\n- **Wrong:** Do not import this example.\n  Why: Not a Rule.\n  <!-- ctx:rule id="EXAMPLE" -->\n-->\n\n'
                         + self.topic() + '\n<!-- Example only\n## Local Topics\n### Wrong\nWhen never:\nRequired:\n- Resource: `missing.json`\n<!-- ctx:topic id="EXAMPLE" -->\n-->\n')
        parsed = parse_node(root)
        self.assertEqual(parsed.rules, ())
        self.assertEqual(len(parsed.topics), 1)
        migrate_sources(self.repo, [root])
        self.assertEqual(len(parse_node(root).topics), 1)
        self.assertNotIn("missing.json", Compiler(self.repo).compile(root).official_markdown)

    def test_help_refresh_keeps_guide_out_of_frozen_packages(self):
        root = self.node(body=self.topic())
        self.assertEqual(self.run_cli("build", str(root))[0], 0)
        frozen = {path: path.read_bytes() for path in (self.repo / ".context" / "versions").rglob("*") if path.is_file()}
        (root / GUIDE_NAME).write_text(GUIDE_MARKER + "\nOld help\n", encoding="utf-8")
        self.assertEqual(self.run_cli("build", str(root))[0], 0)
        self.assertEqual((root / GUIDE_NAME).read_text(encoding="utf-8"), guide_text())
        self.assertEqual({path: path.read_bytes() for path in frozen}, frozen)


if __name__ == "__main__":
    unittest.main()
