from pathlib import Path

path = Path(__file__).with_name("apply_issue27_source_story.py")
text = path.read_text(encoding="utf-8")

# The embedded regression contains its own triple-quoted source fixture; use the
# opposite delimiter for the outer applicator string.
text = text.replace(
    "new_test = '''    def test_source_update_explains_downstream_parent_child_review_and_guided_command",
    "new_test = \"\"\"    def test_source_update_explains_downstream_parent_child_review_and_guided_command",
    1,
)
text = text.replace(
    "            shutil.rmtree(provider, ignore_errors=True)\n\n'''\nreplace_once(\"tests/test_configuration_and_update_ux.py\", test_insert, new_test + test_insert)",
    "            shutil.rmtree(provider, ignore_errors=True)\n\n\"\"\"\nreplace_once(\"tests/test_configuration_and_update_ux.py\", test_insert, new_test + test_insert)",
    1,
)

# Keep the old legacy-discovery regression, but align its wording with the new
# human-facing narrative independently of the larger narrative assertion block.
marker = "# Update the established tests to the new temporal vocabulary and narrative.\n"
extra = '''replace_once(
    "tests/test_configuration_and_update_ux.py",
    'self.assertIn("Migrated legacy Source discovery", out.getvalue())',
    'self.assertIn("Discovery setup note:", out.getvalue())\\n            self.assertIn("Legacy Source lookup settings were moved to", out.getvalue())',
)
replace_once(
    "tests/test_configuration_and_update_ux.py",
    'self.assertIn("This migration only changes where future Source candidates are discovered.", out.getvalue())',
    'self.assertIn("This command is offering an update to Consumer; its Context has not changed yet.", out.getvalue())',
)
'''
if text.count(marker) != 1:
    raise SystemExit("source-story test-update marker missing")
text = text.replace(marker, marker + extra, 1)
path.write_text(text, encoding="utf-8")
