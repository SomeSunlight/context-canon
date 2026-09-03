from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise SystemExit(f"{path}: expected one match for {old!r}, found {text.count(old)}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


replace_once("pyproject.toml", 'version = "0.4.0"', 'version = "0.5.0"')
replace_once(
    "tests/test_walking_skeleton.py",
    '        self.assertIn("compiler_version: \\\"0.4.0\\\"", node.machine_yaml)\n',
    '        self.assertIn("compiler_version: \\\"0.5.0\\\"", node.machine_yaml)\n',
)
