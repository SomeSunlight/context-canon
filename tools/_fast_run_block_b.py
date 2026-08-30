from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    file = Path(path)
    text = file.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one target, found {count}: {old[:90]!r}")
    file.write_text(text.replace(old, new), encoding="utf-8", newline="\n")


# Fix two small contract examples intentionally left out of the Block A meta-patch.
replace_once(
    "src/contextcanon/onboarding_placement_instruction.py",
    '        \'  "action": "move",\',\n',
    '        \'  "action": "promote",\',\n',
)
replace_once(
    "src/contextcanon/onboarding_placement_instruction.py",
    '        "All resource/document/authority paths must exist in the frozen Evidence for this v0 experiment.",\n',
    '        "All resource/document/authority paths must exist in the frozen Evidence for this v1 experiment.",\n',
)

# CLI uses the persistent editable review model rather than overwriting placement.md.
replace_once(
    "src/contextcanon/cli.py",
    'from .onboarding_placement import load_onboarding_placement_proposal, render_placement_review\n',
    'from .onboarding_placement import load_onboarding_placement_proposal\n'
    'from .onboarding_placement_review import create_or_load_placement_review\n',
)
replace_once(
    "src/contextcanon/cli.py",
    '''    onboard_placement_review.add_argument(\n        "--catalog-package",\n        action="append",\n        default=[],\n        metavar="PATH",\n        help="same exact immutable Source package catalog shown to the placement reviewer; may be repeated",\n    )\n''',
    '''    onboard_placement_review.add_argument(\n        "--catalog-package",\n        action="append",\n        default=[],\n        metavar="PATH",\n        help="same exact immutable Source package catalog shown to the placement reviewer; may be repeated",\n    )\n    onboard_placement_review.add_argument(\n        "--review",\n        metavar="PATH",\n        help="human-editable placement Markdown (default: <workspace>/placement.md)",\n    )\n    onboard_placement_review.add_argument(\n        "--owner-source",\n        action="append",\n        default=[],\n        metavar="TARGET_NODE_KEY=SOURCE_NODE_ID",\n        help="explicitly select one exact catalog Source as owner design input when creating a new review; may be repeated",\n    )\n''',
)
replace_once(
    "src/contextcanon/cli.py",
    '''                write_utf8(workspace.placement_path, render_placement_review(proposal, snapshot))\n                print(f"wrote onboarding placement review {workspace.placement_path}")\n                print(f"Placement proposal: {proposal.proposal_digest}")\n                print(f"Items: {len(proposal.items)} · Source reuses: {len(proposal.source_reuses)}")\n                return 0\n''',
    '''                review_path = Path(args.review) if args.review is not None else workspace.placement_path\n                review, created = create_or_load_placement_review(\n                    review_path,\n                    proposal,\n                    snapshot,\n                    owner_source_specs=args.owner_source,\n                )\n                verb = "created" if created else "loaded"\n                print(f"{verb} onboarding placement review {review.review_digest}")\n                print(f"Review file: {review_path}")\n                print(f"Items: {len(review.items)} · Sources: {len(review.sources)} · complete: {review.is_complete}")\n                return 0\n''',
)

# The review parser validates human edits against the same semantic constraints as
# the proposal contract, but does not require the human title/wording to equal LLM output.
review_path = Path("src/contextcanon/onboarding_placement_review.py")
text = review_path.read_text(encoding="utf-8")
text = text.replace(
    'from .onboarding_placement import OnboardingPlacementProposal, PlacementItem\n',
    'from .onboarding_placement import (\n'
    '    PLACEMENT_ACTIONS,\n'
    '    PLACEMENT_KINDS,\n'
    '    WORDING_ORIGINS,\n'
    '    OnboardingPlacementProposal,\n'
    '    PlacementItem,\n'
    ')\n',
    1,
)
text = text.replace(
    'def _normalize_review(\n',
    '''def _validate_item_edit(\n    item_id: str,\n    kind: str,\n    action: str,\n    destination: str | None,\n    payload: dict[str, object],\n    proposal: OnboardingPlacementProposal,\n    snapshot: EvidenceSnapshot,\n) -> None:\n    if kind not in PLACEMENT_KINDS:\n        raise _error(f"item {item_id} has unsupported Kind {kind!r}")\n    if action not in PLACEMENT_ACTIONS:\n        raise _error(f"item {item_id} has unsupported Action {action!r}")\n    allowed_actions = {\n        "overview": {"promote"},\n        "rule": {"promote"},\n        "topic-resource": {"reference"},\n        "ordinary-documentation": {"keep"},\n        "state": {"promote"},\n        "plan": {"promote"},\n        "authority-mapping": {"map"},\n        "unresolved": {"keep"},\n    }\n    if action not in allowed_actions[kind]:\n        expected = ", ".join(sorted(allowed_actions[kind]))\n        raise _error(f"item {item_id} Kind {kind} must use Action {expected}")\n    requires_destination = kind in {"overview", "rule", "topic-resource", "state", "plan", "authority-mapping"}\n    if requires_destination and destination is None:\n        raise _error(f"item {item_id} Kind {kind} requires a Destination")\n    evidence_paths = set(snapshot.by_path)\n    if kind in {"overview", "state", "plan"}:\n        if payload.get("wording_origin") not in WORDING_ORIGINS or not str(payload.get("text", "")).strip():\n            raise _error(f"item {item_id} has invalid {kind} maintained meaning")\n    elif kind == "rule":\n        if payload.get("wording_origin") not in WORDING_ORIGINS:\n            raise _error(f"item {item_id} has invalid Rule wording origin")\n        if not str(payload.get("statement", "")).strip() or not str(payload.get("why", "")).strip():\n            raise _error(f"item {item_id} Rule requires Statement and Why")\n    elif kind == "topic-resource":\n        if not str(payload.get("condition", "")).strip():\n            raise _error(f"item {item_id} Topic requires Condition")\n        for path in payload.get("resource_paths", []):\n            if path not in evidence_paths:\n                raise _error(f"item {item_id} Resource path is not frozen Evidence: {path}")\n    elif kind == "ordinary-documentation":\n        for path in payload.get("document_paths", []):\n            if path not in evidence_paths:\n                raise _error(f"item {item_id} document path is not frozen Evidence: {path}")\n    elif kind == "authority-mapping":\n        if payload.get("wording_origin") not in WORDING_ORIGINS:\n            raise _error(f"item {item_id} has invalid mapping wording origin")\n        fixed = set(proposal.structure.fixed_markdown)\n        for path in payload.get("authority_paths", []):\n            if path not in fixed:\n                raise _error(f"item {item_id} authority is not fixed Markdown in the accepted structure: {path}")\n    elif kind == "unresolved" and not str(payload.get("question", "")).strip():\n        raise _error(f"item {item_id} unresolved finding requires Question")\n\n\ndef _normalize_review(\n''',
    1,
)
text = text.replace(
    'def load_placement_review(path: Path, proposal: OnboardingPlacementProposal) -> OnboardingPlacementReview:\n',
    'def load_placement_review(\n    path: Path, proposal: OnboardingPlacementProposal, snapshot_root: Path\n) -> OnboardingPlacementReview:\n',
    1,
)
text = text.replace(
    '    lines = text.splitlines()\n    proposal_by_id = {item.id: item for item in proposal.items}\n',
    '    snapshot = load_evidence_snapshot(snapshot_root)\n    lines = text.splitlines()\n    proposal_by_id = {item.id: item for item in proposal.items}\n',
    1,
)
old = '''        parsed_items.append(\n            PlacementReviewItem(\n                proposal_id=item_id,\n                authoring_id=attrs.group("authoring"),\n                title=heading.group("title").strip(),\n                decision=decision,\n                destination_node_key=destination,\n                kind=kind,\n                action=action,\n                payload=_payload_from_block(kind, block),\n                review_note="" if _find_line(block, "Review note: ", "Review note") == "-" else _find_line(block, "Review note: ", "Review note"),\n            )\n        )\n'''
new = '''        payload = _payload_from_block(kind, block)\n        _validate_item_edit(item_id, kind, action, destination, payload, proposal, snapshot)\n        note = _find_line(block, "Review note: ", "Review note")\n        parsed_items.append(\n            PlacementReviewItem(\n                proposal_id=item_id,\n                authoring_id=attrs.group("authoring"),\n                title=heading.group("title").strip(),\n                decision=decision,\n                destination_node_key=destination,\n                kind=kind,\n                action=action,\n                payload=payload,\n                review_note="" if note == "-" else note,\n            )\n        )\n'''
if text.count(old) != 1:
    raise SystemExit("review item parse insertion point changed")
text = text.replace(old, new, 1)
text = text.replace(
    '        return load_placement_review(path, proposal), False\n',
    '        return load_placement_review(path, proposal, snapshot_root), False\n',
    1,
)
text = text.replace(
    '    return load_placement_review(path, proposal), True\n',
    '    return load_placement_review(path, proposal, snapshot_root), True\n',
    1,
)
review_path.write_text(text, encoding="utf-8", newline="\n")

# Block-B focused tests use the existing placement fixture and prove persistence,
# direct Markdown editing, stable authoring IDs, and owner-selected Source origin.
test = Path("tests/test_onboarding_placement_review.py")
test.write_text(r'''from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from contextcanon.onboarding_placement import load_onboarding_placement_proposal
from contextcanon.onboarding_placement_review import create_or_load_placement_review, load_placement_review
from contextcanon.parser import ContextCanonError
from tests.test_onboarding_placement import OnboardingPlacementTests


class EditablePlacementReviewTests(unittest.TestCase):
    def make_review(self, *, owner_source: bool = True):
        helper = OnboardingPlacementTests()
        _, prepared, workspace, readme, architecture, source_root, package = helper.make_case()
        raw = helper.placement_dict(prepared, workspace, readme, architecture, package)
        workspace.placement_proposal_path.write_text(json.dumps(raw), encoding="utf-8")
        proposal = load_onboarding_placement_proposal(
            workspace.placement_proposal_path,
            prepared.snapshot_root,
            workspace.structure_proposal_path,
            workspace.structure_path,
            catalog_package_roots=[source_root],
        )
        specs = [f"N-001={package.metadata.id}"] if owner_source else []
        review, created = create_or_load_placement_review(
            workspace.placement_path,
            proposal,
            prepared.snapshot_root,
            owner_source_specs=specs,
        )
        return prepared, workspace, source_root, package, proposal, review, created

    def test_review_is_destination_first_editable_and_owner_source_is_distinct(self):
        prepared, workspace, source_root, package, proposal, review, created = self.make_review()
        self.assertTrue(created)
        text = workspace.placement_path.read_text(encoding="utf-8")
        item = text.index("## P-001")
        destination = text.index("Destination:", item)
        decision = text.index("Decision:", item)
        rationale = text.index("### Proposal rationale", item)
        self.assertLess(destination, decision)
        self.assertLess(decision, rationale)
        self.assertIn("### Maintained meaning", text)
        self.assertIn('origin="owner-selected"', text)
        self.assertEqual(len(review.sources), 2)
        self.assertEqual({source.origin for source in review.sources}, {"evidence-derived", "owner-selected"})

    def test_human_edits_round_trip_and_authoring_identity_stays_stable(self):
        prepared, workspace, source_root, package, proposal, first, _ = self.make_review(owner_source=False)
        first_id = first.items[0].authoring_id
        text = workspace.placement_path.read_text(encoding="utf-8")
        text = text.replace("## P-001 — Repository source of truth", "## P-001 — Canonical installation authority")
        text = text.replace("Decision: `pending`", "Decision: `accept`", 1)
        text = text.replace(
            "Statement: The repository is the installation specification.",
            "Statement: The repository is the canonical installation specification.",
            1,
        )
        workspace.placement_path.write_text(text, encoding="utf-8")
        second = load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)
        self.assertEqual(second.items[0].authoring_id, first_id)
        self.assertEqual(second.items[0].title, "Canonical installation authority")
        self.assertEqual(second.items[0].decision, "accept")
        self.assertEqual(
            second.items[0].payload["statement"],
            "The repository is the canonical installation specification.",
        )

    def test_existing_human_review_is_loaded_not_overwritten(self):
        prepared, workspace, source_root, package, proposal, first, _ = self.make_review(owner_source=False)
        text = workspace.placement_path.read_text(encoding="utf-8").replace("Decision: `pending`", "Decision: `reject`", 1)
        workspace.placement_path.write_text(text, encoding="utf-8")
        loaded, created = create_or_load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)
        self.assertFalse(created)
        self.assertEqual(loaded.items[0].decision, "reject")
        self.assertEqual(loaded.items[0].authoring_id, first.items[0].authoring_id)

    def test_changed_proposal_refuses_to_replace_existing_review(self):
        prepared, workspace, source_root, package, proposal, _, _ = self.make_review(owner_source=False)
        text = workspace.placement_path.read_text(encoding="utf-8")
        workspace.placement_path.write_text(text.replace(proposal.proposal_digest, "0" * 64), encoding="utf-8")
        with self.assertRaisesRegex(ContextCanonError, "new review path"):
            create_or_load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)

    def test_invalid_human_rule_reference_is_rejected(self):
        prepared, workspace, source_root, package, proposal, _, _ = self.make_review(owner_source=False)
        text = workspace.placement_path.read_text(encoding="utf-8").replace("Action: `promote`", "Action: `reference`", 1)
        workspace.placement_path.write_text(text, encoding="utf-8")
        with self.assertRaisesRegex(ContextCanonError, "Kind rule must use Action promote"):
            load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)


if __name__ == "__main__":
    unittest.main()
''', encoding="utf-8", newline="\n")

# Check off Block B only after the workflow runs all focused tests.
plan = Path("PLAN.md")
text = plan.read_text(encoding="utf-8")
for old in [
    "- [ ] Redesign `placement.md` around the reviewer:",
    "- [ ] Parse only a deliberately small editable Markdown control surface; keep Evidence/provenance rendering outside the editable contract.",
    "- [ ] Allocate canonical Rule/Topic identities once in human review state and preserve them across repeated load/preview; titles and wording remain editable presentation.",
    "- [ ] Preserve an existing human-edited placement review instead of overwriting it; fail clearly when a changed proposal requires a new candidate/review decision.",
    "- [ ] Support explicit owner-selected reusable Sources independently of LLM-derived `source_reuses`, while retaining exact immutable package identity and project-specific local deltas.",
]:
    if old not in text:
        raise SystemExit(f"PLAN Block B item missing: {old}")
    text = text.replace(old, old.replace("- [ ]", "- [x]", 1), 1)
plan.write_text(text, encoding="utf-8", newline="\n")
