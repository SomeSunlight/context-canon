from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    file = Path(path)
    text = file.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one target, found {count}: {old[:120]!r}")
    file.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")


# ---------------------------------------------------------------------------
# Publication safety: authored Source collisions, stale preview protection,
# exact review binding, and immutable acceptance record semantics.
# ---------------------------------------------------------------------------
replace_once(
    "src/contextcanon/onboarding_placement_publish.py",
    '''def _managed_ids_outside_blocks(text: str) -> tuple[set[str], set[str]]:\n    stripped = text\n    for name in _MANAGED_SECTIONS:\n        stripped = _strip_managed_block(stripped, name)\n    rule_ids = set(re.findall(r'ctx:rule\\s+id="([^"]+)"', stripped))\n    topic_ids = set(re.findall(r'ctx:topic\\s+id="([^"]+)"', stripped))\n    return rule_ids, topic_ids\n''',
    '''def _managed_ids_outside_blocks(text: str) -> tuple[set[str], set[str], set[str]]:\n    stripped = text\n    for name in _MANAGED_SECTIONS:\n        stripped = _strip_managed_block(stripped, name)\n    rule_ids = set(re.findall(r'ctx:rule\\s+id="([^"]+)"', stripped))\n    topic_ids = set(re.findall(r'ctx:topic\\s+id="([^"]+)"', stripped))\n    source_ids = set(re.findall(r'ctx:source\\s+id="([^"]+)"', stripped))\n    return rule_ids, topic_ids, source_ids\n''',
)
replace_once(
    "src/contextcanon/onboarding_placement_publish.py",
    '''    outside_rule_ids, outside_topic_ids = _managed_ids_outside_blocks(before)\n    for item in rules:\n        if item.authoring_id in outside_rule_ids:\n            raise _error(f"Rule authoring ID collision outside placement-managed block: {item.authoring_id}")\n    for item in topics:\n        if item.authoring_id in outside_topic_ids:\n            raise _error(f"Topic authoring ID collision outside placement-managed block: {item.authoring_id}")\n\n    text = before\n''',
    '''    outside_rule_ids, outside_topic_ids, outside_source_ids = _managed_ids_outside_blocks(before)\n    for item in rules:\n        if item.authoring_id in outside_rule_ids:\n            raise _error(f"Rule authoring ID collision outside placement-managed block: {item.authoring_id}")\n    for item in topics:\n        if item.authoring_id in outside_topic_ids:\n            raise _error(f"Topic authoring ID collision outside placement-managed block: {item.authoring_id}")\n    for source in sources:\n        if source.source_node_id in outside_source_ids:\n            raise _error(\n                f"Source Node ID collision outside placement-managed block: {source.source_node_id}; "\n                "review the existing authored Source instead of duplicating it"\n            )\n\n    text = before\n''',
)
replace_once(
    "src/contextcanon/onboarding_placement_publish.py",
    '''def publish_placement_review(\n    preview: PlacementPublicationPreview,\n    review: OnboardingPlacementReview,\n    *,\n    catalog_package_roots: Iterable[Path] = (),\n    acceptance_path: Path,\n) -> PlacementPublicationResult:\n    if not preview.review_complete:\n        raise _error("review still contains pending decisions; publication requires a complete human review")\n    project = preview.project_root\n''',
    '''def publish_placement_review(\n    preview: PlacementPublicationPreview,\n    review: OnboardingPlacementReview,\n    *,\n    snapshot_root: Path,\n    catalog_package_roots: Iterable[Path] = (),\n    acceptance_path: Path,\n) -> PlacementPublicationResult:\n    if review.review_digest != preview.review_digest:\n        raise _error("review changed after publication preview; build a fresh preview")\n    if (\n        review.evidence_digest != preview.evidence_digest\n        or review.structure_digest != preview.structure_digest\n        or review.proposal_digest != preview.proposal_digest\n    ):\n        raise _error("review identity does not match publication preview")\n    if not preview.review_complete or not review.is_complete:\n        raise _error("review still contains pending decisions; publication requires a complete human review")\n    project = preview.project_root\n    snapshot = load_evidence_snapshot(snapshot_root)\n    _verify_live_evidence(snapshot, project)\n    for delta in preview.nodes:\n        if not delta.source_path.is_file() or delta.source_path.read_text(encoding="utf-8") != delta.before:\n            raise _error(\n                f"Context Node source changed after publication preview: {delta.source_path}; build a fresh preview"\n            )\n''',
)
replace_once(
    "src/contextcanon/onboarding_placement_publish.py",
    '''        payload = _acceptance_payload(preview, review, node_digests)\n        encoded = (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\\n").encode("utf-8")\n        _atomic_write(acceptance_path, encoded)\n        digest = _sha256_bytes(encoded)\n''',
    '''        payload = _acceptance_payload(preview, review, node_digests)\n        encoded = (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\\n").encode("utf-8")\n        if acceptance_path.is_file() and acceptance_path.read_bytes() != encoded:\n            raise _error(\n                f"placement acceptance record already exists with different exact content: {acceptance_path}"\n            )\n        _atomic_write(acceptance_path, encoded)\n        digest = _sha256_bytes(encoded)\n''',
)

# ---------------------------------------------------------------------------
# Visible workspace artifacts for publication preview/follow-up.
# ---------------------------------------------------------------------------
replace_once(
    "src/contextcanon/onboarding_workspace.py",
    '''PLACEMENT_REVIEW_NAME = "placement.md"\n''',
    '''PLACEMENT_REVIEW_NAME = "placement.md"\nPLACEMENT_PREVIEW_NAME = "placement-preview.md"\nPLACEMENT_FOLLOWUP_NAME = "placement-followup.md"\n''',
)
replace_once(
    "src/contextcanon/onboarding_workspace.py",
    '''    def placement_path(self) -> Path:\n        return self.root / PLACEMENT_REVIEW_NAME\n\n\ndef _workspace_readme() -> str:\n''',
    '''    def placement_path(self) -> Path:\n        return self.root / PLACEMENT_REVIEW_NAME\n\n    @property\n    def placement_preview_path(self) -> Path:\n        return self.root / PLACEMENT_PREVIEW_NAME\n\n    @property\n    def placement_followup_path(self) -> Path:\n        return self.root / PLACEMENT_FOLLOWUP_NAME\n\n\ndef _workspace_readme() -> str:\n''',
)
replace_once(
    "src/contextcanon/onboarding_workspace.py",
    '''- `{PLACEMENT_REVIEW_NAME}` — readable evidence-rich placement review showing source excerpt, destination/action, and proposed canonical wording.\n\nThe structure file is the human-owned coarse map. The placement pass is not allowed to redesign it. None of these working files become canonical Context merely because they exist.\n''',
    '''- `{PLACEMENT_REVIEW_NAME}` — human-editable placement decision file. Destination and maintained meaning come first; Evidence remains visible below each finding.\n- `{PLACEMENT_PREVIEW_NAME}` — deterministic exact per-Node source delta and Source-state preview before publication.\n- `{PLACEMENT_FOLLOWUP_NAME}` — generated durable follow-up view for accepted state/plan/mapping/documentation/unresolved findings and deferred mutable-Markdown cleanup candidates.\n\nThe structure file is the human-owned coarse map. The placement pass is not allowed to redesign it. None of these working files become canonical Context merely because they exist; only explicit `placement-publish` changes reviewed Context Node authoring.\n''',
)

# ---------------------------------------------------------------------------
# CLI: placement-preview and placement-publish use the same exact proposal,
# editable review and Source catalog. Publication always builds a fresh preview.
# ---------------------------------------------------------------------------
replace_once(
    "src/contextcanon/cli.py",
    '''from .onboarding_placement_review import create_or_load_placement_review\n''',
    '''from .onboarding_placement_review import create_or_load_placement_review, load_placement_review\nfrom .onboarding_placement_publish import (\n    build_placement_publication_preview,\n    publish_placement_review,\n    render_placement_followups,\n    render_placement_publication_preview,\n)\n''',
)
parser_anchor = '''    onboard_placement_review.add_argument(\n        "--owner-source",\n        action="append",\n        default=[],\n        metavar="TARGET_NODE_KEY=SOURCE_NODE_ID",\n        help="explicitly select one exact catalog Source as owner design input when creating a new review; may be repeated",\n    )\n\n'''
parser_insert = parser_anchor + '''    for command_name, command_help in (\n        ("placement-preview", "preview exact reviewed placement publication without changing project files"),\n        ("placement-publish", "explicitly publish one complete reviewed placement into existing Context Nodes"),\n    ):\n        command = onboard_sub.add_parser(command_name, help=command_help)\n        command.add_argument("snapshot", help="root of the prepared content-addressed evidence snapshot")\n        command.add_argument(\n            "proposal", nargs="?", help="placement proposal JSON (default: <workspace>/placement-proposal.json)"\n        )\n        _add_workspace(command)\n        _add_structure_inputs(command)\n        command.add_argument(\n            "--catalog-package",\n            action="append",\n            default=[],\n            metavar="PATH",\n            help="same exact immutable Source catalog used for placement review; may be repeated",\n        )\n        command.add_argument(\n            "--review", metavar="PATH", help="human-edited placement Markdown (default: <workspace>/placement.md)"\n        )\n        command.add_argument(\n            "--project", metavar="PATH", help="target Git repository root (default: infer from snapshot)"\n        )\n        if command_name == "placement-publish":\n            command.add_argument(\n                "--acceptance",\n                metavar="PATH",\n                help="exact machine acceptance record (default: <snapshot>/placement-acceptance.json)",\n            )\n\n'''
replace_once("src/contextcanon/cli.py", parser_anchor, parser_insert)
replace_once(
    "src/contextcanon/cli.py",
    '''            if args.onboard_command in {"placement-instruction", "placement-validate", "placement-review"}:\n''',
    '''            if args.onboard_command in {\n                "placement-instruction",\n                "placement-validate",\n                "placement-review",\n                "placement-preview",\n                "placement-publish",\n            }:\n''',
)
replace_once(
    "src/contextcanon/cli.py",
    '''                review_path = Path(args.review) if args.review is not None else workspace.placement_path\n                review, created = create_or_load_placement_review(\n                    review_path,\n                    proposal,\n                    snapshot,\n                    owner_source_specs=args.owner_source,\n                )\n                verb = "created" if created else "loaded"\n                print(f"{verb} onboarding placement review {review.review_digest}")\n                print(f"Review file: {review_path}")\n                print(f"Items: {len(review.items)} · Sources: {len(review.sources)} · complete: {review.is_complete}")\n                return 0\n''',
    '''                review_path = Path(args.review) if args.review is not None else workspace.placement_path\n                if args.onboard_command == "placement-review":\n                    review, created = create_or_load_placement_review(\n                        review_path,\n                        proposal,\n                        snapshot,\n                        owner_source_specs=args.owner_source,\n                    )\n                    verb = "created" if created else "loaded"\n                    print(f"{verb} onboarding placement review {review.review_digest}")\n                    print(f"Review file: {review_path}")\n                    print(f"Items: {len(review.items)} · Sources: {len(review.sources)} · complete: {review.is_complete}")\n                    return 0\n\n                review = load_placement_review(review_path, proposal, snapshot)\n                project = Path(args.project) if args.project is not None else None\n                preview = build_placement_publication_preview(\n                    proposal,\n                    review,\n                    snapshot,\n                    catalog_package_roots=catalog,\n                    project_root=project,\n                )\n                write_utf8(workspace.placement_preview_path, render_placement_publication_preview(preview))\n                print(f"wrote placement publication preview {workspace.placement_preview_path}")\n                print(f"Review: {preview.review_digest} · complete: {preview.review_complete}")\n                print(f"Touched Context Nodes: {len(preview.nodes)} · follow-ups: {len(preview.followups)}")\n                if args.onboard_command == "placement-preview":\n                    return 0\n\n                acceptance_path = (\n                    Path(args.acceptance) if args.acceptance is not None else snapshot / "placement-acceptance.json"\n                )\n                result = publish_placement_review(\n                    preview,\n                    review,\n                    snapshot_root=snapshot,\n                    catalog_package_roots=catalog,\n                    acceptance_path=acceptance_path,\n                )\n                write_utf8(workspace.placement_followup_path, render_placement_followups(preview))\n                print(f"published reviewed placement {result.review_digest}")\n                print(f"Acceptance record: {result.acceptance_path}")\n                print(f"Acceptance digest: {result.acceptance_digest}")\n                print(f"Changed Context sources: {len(result.changed_sources)}")\n                print(f"Follow-up: {workspace.placement_followup_path}")\n                return 0\n''',
)

# ---------------------------------------------------------------------------
# Focused vertical publication regression.
# ---------------------------------------------------------------------------
test = Path("tests/test_onboarding_placement_publish.py")
test.write_text(r'''from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from contextcanon.cli import main
from contextcanon.compiler import Compiler
from contextcanon.onboarding_placement import load_onboarding_placement_proposal
from contextcanon.onboarding_placement_publish import (
    build_placement_publication_preview,
    publish_placement_review,
    render_placement_publication_preview,
)
from contextcanon.onboarding_placement_review import create_or_load_placement_review, load_placement_review
from contextcanon.outputs import write_outputs
from contextcanon.parser import ContextCanonError, parse_node
from tests.test_onboarding_placement import OnboardingPlacementTests


class PlacementPublicationTests(unittest.TestCase):
    def make_case(self):
        helper = OnboardingPlacementTests()
        repo, prepared, workspace, readme, architecture, source_root, package = helper.make_case()

        structure_text = workspace.structure_path.read_text(encoding="utf-8")
        structure_text = structure_text.replace(
            "<!-- contextcanon-fixed-markdown:start -->\n<!-- contextcanon-fixed-markdown:end -->",
            "<!-- contextcanon-fixed-markdown:start -->\n- `README.md`\n<!-- contextcanon-fixed-markdown:end -->",
        )
        workspace.structure_path.write_text(structure_text, encoding="utf-8")

        (repo / "CONTEXT.src.md").write_text(
            "# AI Workstation — Local Context Source\n"
            '<!-- ctx:node id="aea56adf-2a26-43f0-b712-3bbeab7a3097" version="0.1.0" -->\n\n'
            "## Overview\n\n"
            "Existing authored root orientation that placement must preserve.\n",
            encoding="utf-8",
        )
        goose = repo / "compose" / "goose"
        goose.mkdir(parents=True)
        (goose / "CONTEXT.src.md").write_text(
            "# Goose — Local Context Source\n"
            '<!-- ctx:node id="11111111-2222-4333-8444-555555555555" version="0.1.0-draft" -->\n\n'
            "## Overview\n\n"
            "Existing authored Goose orientation.\n",
            encoding="utf-8",
        )
        write_outputs(Compiler(repo).compile(repo))
        write_outputs(Compiler(repo).compile(goose))

        raw = helper.placement_dict(prepared, workspace, readme, architecture, package)
        raw["items"][1]["destination_node_key"] = "N-002"
        raw["items"].extend(
            [
                {
                    "id": "P-003",
                    "title": "Goose changes stay reviewed",
                    "kind": "rule",
                    "action": "promote",
                    "destination_node_key": "N-002",
                    "rationale": "This is local durable Goose development governance.",
                    "confidence": "high",
                    "evidence": [{"path": "README.md", "sha256": readme.sha256, "start_line": 4, "end_line": 4}],
                    "payload": {
                        "statement": "Goose changes are developed through reviewed pull requests.",
                        "why": "Keep local Goose changes reviewable.",
                        "wording_origin": "exact",
                    },
                },
                {
                    "id": "P-004",
                    "title": "Root responsibility",
                    "kind": "overview",
                    "action": "promote",
                    "destination_node_key": "N-001",
                    "rationale": "Stable project orientation belongs at the root Node.",
                    "confidence": "high",
                    "evidence": [{"path": "README.md", "sha256": readme.sha256, "start_line": 1, "end_line": 2}],
                    "payload": {"text": "AI Workstation owns reproducible workstation setup.", "wording_origin": "synthesized"},
                },
                {
                    "id": "P-005",
                    "title": "Current migration state",
                    "kind": "state",
                    "action": "promote",
                    "destination_node_key": "N-001",
                    "rationale": "State is reviewed but not forced into current Context source grammar.",
                    "confidence": "medium",
                    "evidence": [{"path": "README.md", "sha256": readme.sha256, "start_line": 1, "end_line": 1}],
                    "payload": {"text": "Migration is in progress.", "wording_origin": "synthesized"},
                },
                {
                    "id": "P-006",
                    "title": "README authority mapping",
                    "kind": "authority-mapping",
                    "action": "map",
                    "destination_node_key": "N-001",
                    "rationale": "Fixed Markdown remains authoritative.",
                    "confidence": "high",
                    "evidence": [{"path": "README.md", "sha256": readme.sha256, "start_line": 1, "end_line": 2}],
                    "payload": {
                        "authority_paths": ["README.md"],
                        "mapping": "README remains the fixed first-contact authority for this test.",
                        "wording_origin": "synthesized",
                    },
                },
            ]
        )
        workspace.placement_proposal_path.write_text(json.dumps(raw, indent=2), encoding="utf-8")
        proposal = load_onboarding_placement_proposal(
            workspace.placement_proposal_path,
            prepared.snapshot_root,
            workspace.structure_proposal_path,
            workspace.structure_path,
            catalog_package_roots=[source_root],
        )
        review, created = create_or_load_placement_review(
            workspace.placement_path, proposal, prepared.snapshot_root
        )
        self.assertTrue(created)
        review_text = workspace.placement_path.read_text(encoding="utf-8").replace(
            "Decision: `pending`", "Decision: `accept`"
        )
        workspace.placement_path.write_text(review_text, encoding="utf-8")
        review = load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)
        self.assertTrue(review.is_complete)

        subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@example.test"], check=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.name", "ContextCanon Test"], check=True)
        subprocess.run(
            ["git", "-C", str(repo), "remote", "add", "origin", "https://example.test/context-canon.git"], check=True
        )
        subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-qm", "test baseline"], check=True)
        head = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"], check=True, text=True, capture_output=True
        ).stdout.strip()
        return repo, prepared, workspace, source_root, proposal, review, head

    def test_preview_is_non_mutating_destination_aware_and_keeps_followups(self):
        repo, prepared, workspace, source_root, proposal, review, head = self.make_case()
        root_before = (repo / "CONTEXT.src.md").read_bytes()
        child_before = (repo / "compose" / "goose" / "CONTEXT.src.md").read_bytes()
        preview = build_placement_publication_preview(
            proposal,
            review,
            prepared.snapshot_root,
            catalog_package_roots=[source_root],
            project_root=repo,
        )
        text = render_placement_publication_preview(preview)
        self.assertTrue(preview.review_complete)
        self.assertEqual((repo / "CONTEXT.src.md").read_bytes(), root_before)
        self.assertEqual((repo / "compose" / "goose" / "CONTEXT.src.md").read_bytes(), child_before)
        self.assertEqual({delta.key for delta in preview.nodes}, {"N-001", "N-002"})
        child = next(delta for delta in preview.nodes if delta.key == "N-002")
        self.assertIn("Resource: `../../docs/architecture.md`", child.after)
        self.assertIn("Existing authored Goose orientation.", child.after)
        self.assertEqual({item.kind for item in preview.followups}, {"state", "authority-mapping"})
        self.assertIn(head, text)
        self.assertTrue(preview.mutable_cleanup_candidates)

    def test_publish_preserves_node_identity_and_project_markdown_then_is_idempotent(self):
        repo, prepared, workspace, source_root, proposal, review, head = self.make_case()
        readme_before = (repo / "README.md").read_bytes()
        architecture_before = (repo / "docs" / "architecture.md").read_bytes()
        root_id = parse_node(repo, repo).metadata.id
        child_root = repo / "compose" / "goose"
        child_id = parse_node(child_root, repo).metadata.id
        preview = build_placement_publication_preview(
            proposal, review, prepared.snapshot_root, catalog_package_roots=[source_root], project_root=repo
        )
        acceptance = prepared.snapshot_root / "placement-acceptance.json"
        result = publish_placement_review(
            preview,
            review,
            snapshot_root=prepared.snapshot_root,
            catalog_package_roots=[source_root],
            acceptance_path=acceptance,
        )
        self.assertTrue(acceptance.is_file())
        self.assertEqual((repo / "README.md").read_bytes(), readme_before)
        self.assertEqual((repo / "docs" / "architecture.md").read_bytes(), architecture_before)
        self.assertEqual(parse_node(repo, repo).metadata.id, root_id)
        self.assertEqual(parse_node(child_root, repo).metadata.id, child_id)
        root_text = (repo / "CONTEXT.src.md").read_text(encoding="utf-8")
        child_text = (child_root / "CONTEXT.src.md").read_text(encoding="utf-8")
        self.assertIn("Existing authored root orientation that placement must preserve.", root_text)
        self.assertIn("contextcanon-placement-rules:start", root_text)
        self.assertIn('transport="git"', root_text)
        self.assertIn(f'ref="{head}"', root_text)
        self.assertIn("../../docs/architecture.md", child_text)
        Compiler(repo).compile(repo)
        Compiler(repo).compile(child_root)
        payload = json.loads(acceptance.read_text(encoding="utf-8"))
        self.assertEqual({item["kind"] for item in payload["followups"]}, {"state", "authority-mapping"})

        second = build_placement_publication_preview(
            proposal, review, prepared.snapshot_root, catalog_package_roots=[source_root], project_root=repo
        )
        self.assertTrue(all(not delta.changed for delta in second.nodes))
        second_result = publish_placement_review(
            second,
            review,
            snapshot_root=prepared.snapshot_root,
            catalog_package_roots=[source_root],
            acceptance_path=acceptance,
        )
        self.assertEqual(second_result.acceptance_digest, result.acceptance_digest)
        self.assertEqual(second_result.changed_sources, ())

    def test_publish_rejects_stale_node_source_after_preview(self):
        repo, prepared, workspace, source_root, proposal, review, _ = self.make_case()
        preview = build_placement_publication_preview(
            proposal, review, prepared.snapshot_root, catalog_package_roots=[source_root], project_root=repo
        )
        root_source = repo / "CONTEXT.src.md"
        root_source.write_text(root_source.read_text(encoding="utf-8") + "\nHuman edit after preview.\n", encoding="utf-8")
        with self.assertRaisesRegex(ContextCanonError, "changed after publication preview"):
            publish_placement_review(
                preview,
                review,
                snapshot_root=prepared.snapshot_root,
                catalog_package_roots=[source_root],
                acceptance_path=prepared.snapshot_root / "placement-acceptance.json",
            )

    def test_cli_preview_and_publish_use_visible_workspace_artifacts(self):
        repo, prepared, workspace, source_root, proposal, review, _ = self.make_case()
        args = [
            "onboard", "placement-preview", str(prepared.snapshot_root),
            "--catalog-package", str(source_root), "--project", str(repo),
        ]
        self.assertEqual(main(args), 0)
        self.assertTrue(workspace.placement_preview_path.is_file())
        self.assertFalse((prepared.snapshot_root / "placement-acceptance.json").exists())
        args[1] = "placement-publish"
        self.assertEqual(main(args), 0)
        self.assertTrue((prepared.snapshot_root / "placement-acceptance.json").is_file())
        self.assertTrue(workspace.placement_followup_path.is_file())


if __name__ == "__main__":
    unittest.main()
''', encoding="utf-8", newline="\n")

# PLAN checkpoint is committed only if the workflow's focused test gate succeeds.
plan = Path("PLAN.md")
text = plan.read_text(encoding="utf-8")
for old in [
    "- [ ] Add deterministic `placement-preview` that shows exact per-Node `CONTEXT.src.md` deltas, Source install/pin changes, and findings that intentionally remain outside Node authoring before mutation.",
    "- [ ] Materialize accepted Overview, local Rules, Topics/Resources and Source state without replacing Node identity or unrelated authored content; repeated preview/publication must be safe.",
    "- [ ] Carry accepted `state`, `plan`, `ordinary-documentation`, authority mappings and unresolved findings durably even when they are not automatically spliced into arbitrary repository prose.",
    "- [ ] Keep existing mutable Markdown untouched during initial placement publication. A later cleanup preview may propose removing duplicate promoted text and leaving orientation/references, but that remains a distinct operation.",
    "- [ ] Preserve exact Source package identity plus durable Git provenance/update metadata without writing a transient developer checkout path into project truth.",
]:
    if old not in text:
        raise SystemExit(f"PLAN Block C item missing: {old}")
    text = text.replace(old, old.replace("- [ ]", "- [x]", 1), 1)
plan.write_text(text, encoding="utf-8", newline="\n")
