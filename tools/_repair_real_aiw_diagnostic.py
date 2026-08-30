from pathlib import Path

path = Path("tools/_real_aiw_review.py")
text = path.read_text(encoding="utf-8")
old = '''def run(*args: str, cwd: Path | None = None) -> str:\n    return subprocess.run(args, cwd=cwd, check=True, text=True, capture_output=True).stdout.strip()\n'''
new = '''def run(*args: str, cwd: Path | None = None) -> str:\n    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True)\n    if result.returncode != 0:\n        raise RuntimeError(\n            f"command failed ({result.returncode}): {' '.join(args)}\\nSTDOUT:\\n{result.stdout}\\nSTDERR:\\n{result.stderr}"\n        )\n    return result.stdout.strip()\n'''
if text.count(old) != 1:
    raise SystemExit(f"run helper target count={text.count(old)}")
path.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")
