from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one replacement target, found {count}: {old[:120]!r}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


replace_once("pyproject.toml", 'version = "0.7.1"', 'version = "0.7.2"')

replace_once(
    "src/contextcanon/package_diff.py",
    '''        parent.id: {
            "version": parent.version,''',
    '''        parent.id: {
            "name": parent.name,
            "version": parent.version,''',
)
replace_once(
    "src/contextcanon/package_diff.py",
    '''        source.id: {
            "version": source.version,''',
    '''        source.id: {
            "name": source.name,
            "version": source.version,''',
)

replace_once(
    "tests/test_configuration_and_update_ux.py",
    'self.assertEqual(out.getvalue().strip(), "contextcanon 0.7.1")',
    'self.assertEqual(out.getvalue().strip(), "contextcanon 0.7.2")',
)
replace_once(
    "tests/test_configuration_and_update_ux.py",
    'self.assertIn("Propagation review complete: accepted 2 changed Parent edge(s).", out.getvalue())',
    'self.assertIn("Propagation review complete: applied 2 changed Parent/Child update(s).", out.getvalue())',
)
replace_once(
    "tests/test_propagation_review_ux.py",
    'self.assertIn("Applies here?", out.getvalue())',
    'self.assertIn("Should these Parent changes apply to Child?", out.getvalue())',
)
