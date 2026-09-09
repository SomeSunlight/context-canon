from pathlib import Path

path = Path(__file__).with_name("apply_issue27_source_story.py")
text = path.read_text(encoding="utf-8")
text = text.replace("new_test = '''    def test_source_update_explains_downstream_parent_child_review_and_guided_command", "new_test = \"\"\"    def test_source_update_explains_downstream_parent_child_review_and_guided_command", 1)
text = text.replace("            shutil.rmtree(provider, ignore_errors=True)\n\n'''\nreplace_once(\"tests/test_configuration_and_update_ux.py\", test_insert, new_test + test_insert)", "            shutil.rmtree(provider, ignore_errors=True)\n\n\"\"\"\nreplace_once(\"tests/test_configuration_and_update_ux.py\", test_insert, new_test + test_insert)", 1)
path.write_text(text, encoding="utf-8")
