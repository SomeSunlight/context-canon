from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1:
        raise SystemExit(f"{label}: expected one match, found {text.count(old)}")
    return text.replace(old, new, 1)


# Source audit now links straight to the finding sheet that owns a shared Source edit.
audit_path = Path("src/contextcanon/onboarding_placement_audit.py")
audit = audit_path.read_text(encoding="utf-8")
audit = replace_once(
    audit,
    "from .onboarding_placement_review import OnboardingPlacementReview, PlacementReviewItem, PlacementReviewSourceEdit\n",
    "from .onboarding_placement_review import OnboardingPlacementReview, PlacementReviewItem, PlacementReviewSourceEdit\n"
    "from .onboarding_placement_split_review import placement_finding_filename\n",
    "audit split helper import",
)
audit = replace_once(
    audit,
    '    review_filename: str = "STEP-07-placement.md",\n',
    '    review_filename: str = "STEP-08-placement.md",\n',
    "audit default review filename",
)
audit = replace_once(
    audit,
    '        "> **Generated, read-only view.** Edit `STEP-07-placement.md`, not this file. Rerunning `contextcanon onboard placement-review ...` validates the human gate and regenerates this audit from that exact parsed review.",\n',
    '        f"> **Generated, read-only view.** Use `{review_filename}` as the STEP-08 index and edit its linked finding files, not this audit. Rerunning `contextcanon onboard placement-review ...` validates the human gate and regenerates this audit from that exact parsed review.",\n',
    "audit preamble",
)
old = '''            lines.extend([
                f"### {edit.proposal_id} — lines {edit.start_line}-{edit.end_line}",
                "",
                f"Review control: [`{edit.proposal_id}` in {review_filename}]({review_filename}#source-edit-{edit.proposal_id.lower()})",
                "",
'''
new = '''            owner_item_id = edit.linked_item_ids[0]
            proposal_item = next((item for item in proposal.items if item.id == owner_item_id), None)
            if proposal_item is None:
                raise ContextCanonError(f"Source audit edit {edit.proposal_id} references missing proposal item {owner_item_id}")
            finding_dir = Path(review_filename).with_suffix("").name
            control_target = f"{finding_dir}/{placement_finding_filename(proposal_item)}#source-edit-{edit.proposal_id.lower()}"
            lines.extend([
                f"### {edit.proposal_id} — lines {edit.start_line}-{edit.end_line}",
                "",
                f"Review control: [`{edit.proposal_id}` in `{owner_item_id}` finding]({control_target})",
                "",
'''
audit = replace_once(audit, old, new, "audit direct finding link")
audit_path.write_text(audit, encoding="utf-8", newline="\n")


# Audit tests edit the owning finding sheet rather than the index.
test_audit_path = Path("tests/test_onboarding_placement_audit.py")
test_audit = test_audit_path.read_text(encoding="utf-8")
test_audit = replace_once(
    test_audit,
    "from contextcanon.onboarding_placement_review import create_or_load_placement_review, load_placement_review\n",
    "from contextcanon.onboarding_placement_review import create_or_load_placement_review, load_placement_review\n"
    "from contextcanon.onboarding_placement_split_review import placement_finding_path\n",
    "audit test split import",
)
test_audit = test_audit.replace(
    '''        text = workspace.placement_path.read_text(encoding="utf-8")
        text = text.replace("Decision: `pending`", "Decision: `accept`", 1)
        text = text.replace("Source edit decision: `pending`", "Source edit decision: `accept`", 1)
        workspace.placement_path.write_text(text, encoding="utf-8")
''',
    '''        finding_path = placement_finding_path(workspace.placement_path, proposal.items[0])
        text = finding_path.read_text(encoding="utf-8")
        text = text.replace("Decision: `pending`", "Decision: `accept`", 1)
        text = text.replace("Source edit decision: `pending`", "Source edit decision: `accept`", 1)
        finding_path.write_text(text, encoding="utf-8")
''',
    1,
)
test_audit = test_audit.replace(
    '''        text = workspace.placement_path.read_text(encoding="utf-8")
        text = text.replace("Source edit decision: `pending`", "Source edit decision: `reject`", 1)
        workspace.placement_path.write_text(text, encoding="utf-8")
''',
    '''        finding_path = placement_finding_path(workspace.placement_path, proposal.items[0])
        text = finding_path.read_text(encoding="utf-8")
        text = text.replace("Source edit decision: `pending`", "Source edit decision: `reject`", 1)
        finding_path.write_text(text, encoding="utf-8")
''',
    1,
)
test_audit = replace_once(
    test_audit,
    '''        review_text = workspace.placement_path.read_text(encoding="utf-8")
        review_text = review_text.replace("Decision: `pending`", "Decision: `accept`", 1)
        review_text = review_text.replace("Source edit decision: `pending`", "Source edit decision: `accept`", 1)
        workspace.placement_path.write_text(review_text, encoding="utf-8")
''',
    '''        proposal = load_onboarding_placement_proposal(
            workspace.placement_proposal_path,
            prepared.snapshot_root,
            workspace.structure_proposal_path,
            workspace.structure_path,
            catalog_package_roots=[source_root],
        )
        finding_path = placement_finding_path(workspace.placement_path, proposal.items[0])
        review_text = finding_path.read_text(encoding="utf-8")
        review_text = review_text.replace("Decision: `pending`", "Decision: `accept`", 1)
        review_text = review_text.replace("Source edit decision: `pending`", "Source edit decision: `accept`", 1)
        finding_path.write_text(review_text, encoding="utf-8")
''',
    "audit CLI edit finding",
)
test_audit = replace_once(
    test_audit,
    '        self.assertIn("Why: Running state must not become undocumented authority.", audit)\n',
    '        self.assertIn("Why: Running state must not become undocumented authority.", audit)\n'
    '        self.assertIn("STEP-08-placement/P-001-repository-is-the-installation-specification.md#source-edit-e-001", audit)\n',
    "audit direct link assertion",
)
test_audit_path.write_text(test_audit, encoding="utf-8", newline="\n")


# The historical real-tree migration test accepts all split findings explicitly.
ai_path = Path("tests/test_ai_workstation_parent_migration.py")
ai = ai_path.read_text(encoding="utf-8")
ai = replace_once(
    ai,
    "from contextcanon.onboarding_placement_review import create_or_load_placement_review, load_placement_review\n",
    "from contextcanon.onboarding_placement_review import create_or_load_placement_review, load_placement_review\n"
    "from contextcanon.onboarding_placement_split_review import placement_finding_path\n",
    "ai migration split import",
)
ai = replace_once(
    ai,
    '''        workspace.placement_path.write_text(
            workspace.placement_path.read_text(encoding="utf-8").replace(
                "Decision: `pending`", "Decision: `accept`"
            ),
            encoding="utf-8",
        )
''',
    '''        for item in proposal.items:
            finding_path = placement_finding_path(workspace.placement_path, item)
            finding_path.write_text(
                finding_path.read_text(encoding="utf-8").replace(
                    "Decision: `pending`", "Decision: `accept`"
                ),
                encoding="utf-8",
            )
''',
    "ai migration accept split findings",
)
ai_path.write_text(ai, encoding="utf-8", newline="\n")


# Add explicit reset coverage for the STEP-08 split directory.
reset_test_path = Path("tests/test_onboarding_reset.py")
reset_test = reset_test_path.read_text(encoding="utf-8")
anchor = '''    def test_reset_from_step8_removes_generated_source_audit(self):
'''
if anchor not in reset_test:
    raise SystemExit("reset test anchor missing")
method = '''    def test_reset_from_step8_removes_split_review_directory(self):
        repo, prepared, workspace = self.make_project()
        split_dir = workspace.placement_dir_path
        split_dir.mkdir()
        (split_dir / "P-001-example.md").write_text("human reviewed finding", encoding="utf-8")
        workspace.placement_path.write_text("owned STEP-08 index", encoding="utf-8")

        result = reset_onboarding(prepared.snapshot_root, from_step=8)

        self.assertFalse(workspace.placement_path.exists())
        self.assertFalse(split_dir.exists())
        self.assertIn("STEP-08-placement/", result["workspace_files_removed"])

'''
reset_test = reset_test.replace(anchor, method + anchor, 1)
reset_test_path.write_text(reset_test, encoding="utf-8", newline="\n")

print("Issue 35 remaining integration patch applied")
