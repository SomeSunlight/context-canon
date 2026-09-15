from pathlib import Path

p = Path(__file__).resolve().parents[1] / "tests/test_onboarding_reset.py"
text = p.read_text(encoding="utf-8")
old = '''        split_dir = workspace.placement_dir_path
        split_dir.mkdir()
        (split_dir / "P-001-example.md").write_text("human reviewed finding", encoding="utf-8")
        workspace.placement_path.write_text("owned STEP-08 index", encoding="utf-8")

        result = reset_onboarding(prepared.snapshot_root, from_step=8)

        self.assertFalse(workspace.placement_path.exists())
        self.assertFalse(split_dir.exists())
        self.assertIn("STEP-08-placement/", result["workspace_files_removed"])
'''
new = '''        split_dir = workspace.placement_dir_path
        edit_dir = workspace.placement_source_edit_dir_path
        split_dir.mkdir()
        edit_dir.mkdir()
        (split_dir / "P-001-example.md").write_text("human reviewed finding", encoding="utf-8")
        (edit_dir / "E-001-example.md").write_text("human reviewed source edit", encoding="utf-8")
        workspace.placement_path.write_text("owned STEP-08 index", encoding="utf-8")

        result = reset_onboarding(prepared.snapshot_root, from_step=8)

        self.assertFalse(workspace.placement_path.exists())
        self.assertFalse(split_dir.exists())
        self.assertFalse(edit_dir.exists())
        self.assertIn("STEP-08-placement/", result["workspace_files_removed"])
        self.assertIn("STEP-08-source-edits/", result["workspace_files_removed"])
'''
if text.count(old) != 1:
    raise RuntimeError(f"reset test anchor count: {text.count(old)}")
p.write_text(text.replace(old, new, 1), encoding="utf-8")
print("Issue #36 reset regression patched")
