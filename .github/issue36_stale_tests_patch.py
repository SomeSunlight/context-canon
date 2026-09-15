from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def patch(path, old, new, label):
    p = ROOT / path
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one anchor, found {count}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


patch(
    "tests/test_onboarding_placement.py",
    '''        self.assertIn("cc:placement-review-layout: split-v1", index_text)
        finding_path = next(workspace.placement_dir_path.glob("P-001-*.md"))
        finding_text = finding_path.read_text(encoding="utf-8")
        self.assertIn("Wording: `exact`", finding_text)
        self.assertIn("### Into Node — editable", finding_text)
        self.assertIn("### Source before — frozen Evidence", finding_text)
        self.assertIn("### Source after promotion", finding_text)
        self.assertNotIn("```text", finding_text)
''',
    '''        self.assertIn("cc:placement-review-layout: split-v2", index_text)
        self.assertTrue(workspace.placement_source_edit_dir_path.is_dir())
        finding_path = next(workspace.placement_dir_path.glob("P-001-*.md"))
        finding_text = finding_path.read_text(encoding="utf-8")
        self.assertIn("- Wording: `exact`", finding_text)
        self.assertIn("## Into Node N-001 — AI Workstation", finding_text)
        self.assertIn("### Evidence 1", finding_text)
        self.assertNotIn("Source edit decision:", finding_text)
        edit_path = next(workspace.placement_source_edit_dir_path.glob("E-001-*.md"))
        edit_text = edit_path.read_text(encoding="utf-8")
        self.assertIn("## Before — frozen source", edit_text)
        self.assertIn("## After — editable replacement", edit_text)
        self.assertNotIn("```text", edit_text)
''',
    "placement CLI split-v2 assertions",
)

patch(
    "tests/test_onboarding_placement_publish.py",
    'from contextcanon.onboarding_placement_split_review import placement_finding_path',
    'from contextcanon.onboarding_placement_split_review import placement_finding_path, placement_source_edit_path',
    "publication split import",
)
patch(
    "tests/test_onboarding_placement_publish.py",
    '''        for item in proposal.items:
            finding_path = placement_finding_path(workspace.placement_path, item)
            review_text = finding_path.read_text(encoding="utf-8").replace(
                "Decision: `pending`", "Decision: `accept`"
            ).replace("Source edit decision: `pending`", "Source edit decision: `accept`")
            finding_path.write_text(review_text, encoding="utf-8")
        index_text = workspace.placement_path.read_text(encoding="utf-8").replace(
            "Decision: `pending`", "Decision: `accept`"
        )
''',
    '''        for item in proposal.items:
            finding_path = placement_finding_path(workspace.placement_path, item)
            review_text = finding_path.read_text(encoding="utf-8").replace(
                "Decision: `pending`", "Decision: `accept`"
            )
            finding_path.write_text(review_text, encoding="utf-8")
        for source_edit in review.source_edits:
            edit_path = placement_source_edit_path(workspace.placement_path, source_edit)
            edit_text = edit_path.read_text(encoding="utf-8").replace(
                "Source edit decision: `pending`", "Source edit decision: `accept`"
            )
            edit_path.write_text(edit_text, encoding="utf-8")
        index_text = workspace.placement_path.read_text(encoding="utf-8").replace(
            "Decision: `pending`", "Decision: `accept`"
        )
''',
    "publication fixture E acceptance",
)

print("Remaining Issue #36 stale tests patched")
