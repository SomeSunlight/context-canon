from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1:
        raise SystemExit(f"{label}: expected one match, found {text.count(old)}")
    return text.replace(old, new, 1)


# Fix the newly added reset regression to use this suite's real fixture.
reset_path = Path("tests/test_onboarding_reset.py")
reset = reset_path.read_text(encoding="utf-8")
reset = replace_once(
    reset,
    '''    def test_reset_from_step8_removes_split_review_directory(self):
        repo, prepared, workspace = self.make_project()
        split_dir = workspace.placement_dir_path
''',
    '''    def test_reset_from_step8_removes_split_review_directory(self):
        _, prepared = self.make_repo()
        workspace = open_onboarding_workspace(prepared.snapshot_root, create=True)
        split_dir = workspace.placement_dir_path
''',
    "reset regression fixture",
)
reset_path.write_text(reset, encoding="utf-8", newline="\n")


# Add a many-finding regression: the index stays compact and each finding has one sheet.
review_path = Path("tests/test_onboarding_placement_review.py")
review = review_path.read_text(encoding="utf-8")
anchor = '''    def test_missing_or_foreign_split_finding_is_rejected(self):
'''
if anchor not in review:
    raise SystemExit("split review test anchor missing")
method = '''    def test_many_findings_scale_as_index_plus_one_sheet_each(self):
        helper = placement_fixture.OnboardingPlacementTests()
        _, prepared, workspace, readme, architecture, source_root, package = helper.make_case()
        raw = helper.placement_dict(prepared, workspace, readme, architecture, package)
        template = raw["items"][1]
        raw["items"] = []
        for number in range(1, 41):
            item = json.loads(json.dumps(template))
            item["id"] = f"P-{number:03d}"
            item["title"] = f"Architecture reference {number:02d}"
            raw["items"].append(item)
        raw["source_edits"] = []
        raw["source_reuses"] = []
        workspace.placement_proposal_path.write_text(json.dumps(raw), encoding="utf-8")
        proposal = load_onboarding_placement_proposal(
            workspace.placement_proposal_path,
            prepared.snapshot_root,
            workspace.structure_proposal_path,
            workspace.structure_path,
            catalog_package_roots=[source_root],
        )
        review_gate, created = create_or_load_placement_review(
            workspace.placement_path, proposal, prepared.snapshot_root
        )
        self.assertTrue(created)
        self.assertEqual(len(review_gate.items), 40)
        review_dir = placement_review_directory(workspace.placement_path)
        self.assertEqual(len(list(review_dir.glob("*.md"))), 40)
        index = workspace.placement_path.read_text(encoding="utf-8")
        self.assertEqual(index.count("STEP-08-placement/P-"), 40)
        self.assertNotIn("### Source before — frozen Evidence", index)
        self.assertLess(len(index.splitlines()), 130)

'''
review = review.replace(anchor, method + anchor, 1)
review_path.write_text(review, encoding="utf-8", newline="\n")

print("Issue 35 reset/scaling follow-up applied")
