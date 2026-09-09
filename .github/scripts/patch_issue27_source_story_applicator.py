from pathlib import Path

path = Path(__file__).with_name("apply_issue27_source_story.py")
text = path.read_text(encoding="utf-8")
text = text.replace("new_test = '''    def test_source_update_explains_downstream_parent_child_review_and_guided_command", "new_test = \"\"\"    def test_source_update_explains_downstream_parent_child_review_and_guided_command", 1)
text = text.replace("            shutil.rmtree(provider, ignore_errors=True)\n\n'''\nreplace_once(\"tests/test_configuration_and_update_ux.py\", test_insert, new_test + test_insert)", "            shutil.rmtree(provider, ignore_errors=True)\n\n\"\"\"\nreplace_once(\"tests/test_configuration_and_update_ux.py\", test_insert, new_test + test_insert)", 1)
text = text.replace(
    "    'self.assertIn(\"It does not change the accepted Source; acceptance happens only after this review.\", out.getvalue())\\n            self.assertIn(\"Candidate: Shared 1.1.0\", out.getvalue())',",
    "    'self.assertIn(\"Migrated legacy Source discovery\", out.getvalue())\\n            self.assertIn(\"It does not change the accepted Source; acceptance happens only after this review.\", out.getvalue())\\n            self.assertIn(\"Candidate: Shared 1.1.0\", out.getvalue())',",
    1,
)
text = text.replace(
    "    'self.assertIn(\"That only changes where future candidates are found; it does not apply this Source update.\", out.getvalue())\\n            self.assertIn(\"Current local Source:\", out.getvalue())",
    "    'self.assertIn(\"Discovery setup note:\", out.getvalue())\\n            self.assertIn(\"Legacy Source lookup settings were moved to\", out.getvalue())\\n            self.assertIn(\"That only changes where future candidates are found; it does not apply this Source update.\", out.getvalue())\\n            self.assertIn(\"Current local Source:\", out.getvalue())",
    1,
)
path.write_text(text, encoding="utf-8")
