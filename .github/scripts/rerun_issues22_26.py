from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
finalizer = ROOT / ".github/scripts/finalize_issues22_26.py"
text = finalizer.read_text(encoding="utf-8")

old = '''    new = old.replace('            print(f"Next: contextcanon build {node_root}")\\n', '            _report_version_bump(ensure_node_version_advanced(node_root))\\n            print(f"Next: contextcanon build {node_root}")\\n')\n'''
new = '''    new = old\n'''
if old not in text:
    raise RuntimeError("Could not locate premature authoring version bump in finalizer")
text = text.replace(old, new, 1)

marker = '''def update_cli() -> None:\n'''
helper = '''def harden_parent_review_api() -> None:\n    path = ROOT / "src/contextcanon/sources.py"\n    source = path.read_text(encoding="utf-8")\n    import_line = "from .parser import ContextCanonError, find_repo_root, parse_node\\n"\n    if "from .versioning import ensure_node_version_advanced\\n" not in source:\n        if import_line not in source:\n            raise RuntimeError("Could not locate sources.py parser import")\n        source = source.replace(import_line, import_line + "from .versioning import ensure_node_version_advanced\\n", 1)\n    old_block = "    parent_root = compiler._resolve_source_root(node_root, parent_ref.locator)\\n    live_parent = Compiler(repo_root).compile(parent_root)\\n"\n    new_block = "    parent_root = compiler._resolve_source_root(node_root, parent_ref.locator)\\n    ensure_node_version_advanced(parent_root, repo_root)\\n    live_parent = Compiler(repo_root).compile(parent_root)\\n"\n    if new_block not in source:\n        if old_block not in source:\n            raise RuntimeError("Could not locate Parent live compile block")\n        source = source.replace(old_block, new_block, 1)\n    path.write_text(source, encoding="utf-8")\n\n\n'''
if "def harden_parent_review_api()" not in text:
    if marker not in text:
        raise RuntimeError("Could not locate update_cli in finalizer")
    text = text.replace(marker, helper + marker, 1)

old_call = '''    update_sources_validation()\n    update_cli()\n'''
new_call = '''    update_sources_validation()\n    harden_parent_review_api()\n    update_cli()\n'''
if new_call not in text:
    if old_call not in text:
        raise RuntimeError("Could not locate finalizer product-call sequence")
    text = text.replace(old_call, new_call, 1)

old_cleanup = '''        ".github/workflows/issues22-26-finalizer.yml",\n'''
new_cleanup = '''        ".github/workflows/issues22-26-finalizer.yml",\n        ".github/scripts/rerun_issues22_26.py",\n        ".github/workflows/rerun-issues22-26.yml",\n'''
if ".github/scripts/rerun_issues22_26.py" not in text:
    if old_cleanup not in text:
        raise RuntimeError("Could not locate finalizer cleanup list")
    text = text.replace(old_cleanup, new_cleanup, 1)

finalizer.write_text(text, encoding="utf-8")
subprocess.run([sys.executable, str(finalizer)], cwd=ROOT, check=True)
