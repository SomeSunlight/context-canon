from pathlib import Path
import sys


def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    Path(path).write_text(text, encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1:
        raise RuntimeError(f"{label}: expected exactly one anchor, got {text.count(old)}")
    return text.replace(old, new, 1)


def plan() -> None:
    path = "PLAN.md"
    text = read(path).rstrip()
    marker = "#### Block L — parse multiple shared Source After edits per finding"
    if marker in text:
        return
    text += """

#### Block L — parse multiple shared Source After edits per finding

Purpose: close the live `ai-workstation` Step-7 failure where one promoted finding owns more than one reviewed Source After edit. The renderer already shows each edit once, but the review parser must stop each editable Source-edit block at the next Source-edit boundary rather than consuming all later edits under the same finding.

- [ ] Bound Source-edit parsing by the next Source-edit metadata marker as well as the next placement/Source heading.
- [ ] Add a regression with two non-overlapping Source After edits owned by the same promoted finding and verify both round-trip independently.
- [ ] Run the focused placement-review tests, complete deterministic suite, build/check, diff-check, cleanup, and exact-head PR CI before returning a new test SHA.
"""
    write(path, text.rstrip() + "\n")


def apply() -> None:
    path = "src/contextcanon/onboarding_placement_review.py"
    text = read(path)
    old = '''        next_item = next(\n            (i for i in range(index + 1, len(lines)) if _ITEM_HEADING_RE.match(lines[i]) or _SOURCE_HEADING_RE.match(lines[i])),\n            len(lines),\n        )\n'''
    new = '''        next_item = next(\n            (\n                i\n                for i in range(index + 1, len(lines))\n                if _SOURCE_EDIT_COMMENT_RE.match(lines[i])\n                or _ITEM_HEADING_RE.match(lines[i])\n                or _SOURCE_HEADING_RE.match(lines[i])\n            ),\n            len(lines),\n        )\n'''
    text = replace_once(text, old, new, "source-edit block boundary")
    write(path, text)

    path = "tests/test_onboarding_placement_review.py"
    text = read(path)
    marker = '\n\nif __name__ == "__main__":'
    test = r'''
    def test_multiple_source_edits_owned_by_one_finding_parse_independently(self):
        helper = placement_fixture.OnboardingPlacementTests()
        _, prepared, workspace, readme, architecture, source_root, package = helper.make_case()
        raw = helper.placement_dict(prepared, workspace, readme, architecture, package)
        # Let P-001 justify two adjacent but non-overlapping architecture edits.
        raw["items"][0]["evidence"][0]["start_line"] = 1
        raw["source_edits"].append(
            {
                "id": "E-002",
                "path": "docs/architecture.md",
                "sha256": architecture.sha256,
                "start_line": 1,
                "end_line": 1,
                "linked_item_ids": ["P-001"],
                "replacement": "# Architecture gateway",
                "rationale": "Keep a compact architecture gateway beside the promoted canonical rule.",
                "confidence": "high",
            }
        )
        workspace.placement_proposal_path.write_text(json.dumps(raw), encoding="utf-8")
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
        rendered = workspace.placement_path.read_text(encoding="utf-8")
        self.assertEqual(rendered.count("Source edit note:"), 2)
        loaded = load_placement_review(workspace.placement_path, proposal, prepared.snapshot_root)
        self.assertEqual([edit.proposal_id for edit in loaded.source_edits], ["E-001", "E-002"])
        self.assertEqual(
            [edit.replacement for edit in loaded.source_edits],
            [
                "Installation authority is maintained in [AI Workstation Context](../CONTEXT.md).",
                "# Architecture gateway",
            ],
        )
'''
    if "test_multiple_source_edits_owned_by_one_finding_parse_independently" not in text:
        text = text.replace(marker, "\n" + test + marker)
    write(path, text)


def finalize() -> None:
    path = "PLAN.md"
    text = read(path)
    start = text.index("#### Block L — parse multiple shared Source After edits per finding")
    block = text[start:]
    block = block.replace("- [ ] ", "- [x] ")
    checkpoint = """

Shared Source-edit parser checkpoint: the live `ai-workstation` proposal contains several legitimate cases where one promoted finding owns multiple non-overlapping Source After transformations. Review parsing now treats the next `cc:source-edit` marker as an explicit block boundary, so each edit keeps exactly one decision, note and editable replacement even when two edits are rendered under the same P-item. A focused regression reproduces that shape; the complete deterministic suite and repository build/check are green.
"""
    text = text[:start] + block.rstrip() + checkpoint
    write(path, text.rstrip() + "\n")

    path = "STATE.md"
    state = read(path).rstrip()
    section = "## Latest shared Source-edit parsing correction"
    if section not in state:
        state += """

## Latest shared Source-edit parsing correction

The real `ai-workstation` Step-7 review exposed a parser boundary bug when one promoted finding owns more than one Source After edit. The renderer correctly materialized each Source edit once, but the parser previously scanned from one Source-edit marker until the next placement item/Source heading, so a sibling Source edit under the same finding contributed a second `Source edit note:` and caused validation to fail. Source-edit parsing now stops at the next Source-edit marker as well; multiple non-overlapping edits under one finding round-trip independently.
"""
    write(path, state.rstrip() + "\n")


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "apply"
    {"plan": plan, "apply": apply, "finalize": finalize}[command]()
