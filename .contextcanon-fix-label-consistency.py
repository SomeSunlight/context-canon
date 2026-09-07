from __future__ import annotations

import sys
from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected one replacement target, found {count}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


def update_plan() -> None:
    path = Path("PLAN.md")
    text = path.read_text(encoding="utf-8")
    anchor = "Owner-test correction under #22: `source list` and human Source selectors must use the accepted package's canonical Node name;"
    note = (
        "Owner-test consistency follow-up under #22: accepted Source and Parent visible labels must match the canonical Node name of the accepted package. "
        "Stable ID/version/digests remain technical identity; `source list` stays diagnostic/repairable, while `contextcanon check` must report a label mismatch until acceptance or a direct source edit normalizes it.\n\n"
    )
    if note in text:
        return
    if anchor not in text:
        raise RuntimeError("active #22 owner-test checkpoint not found")
    text = text.replace(anchor, note + anchor, 1)
    path.write_text(text, encoding="utf-8")


def update_product() -> None:
    outputs = "src/contextcanon/outputs.py"
    old = '''def check_outputs(compiled: CompiledNode) -> list[str]:\n    outputs = expected_outputs(compiled)\n    root = compiled.parsed.root\n    drift: list[str] = []\n'''
    new = '''def check_outputs(compiled: CompiledNode) -> list[str]:\n    outputs = expected_outputs(compiled)\n    root = compiled.parsed.root\n    drift: list[str] = []\n\n    for relation, authored, packages in (\n        ("Source", compiled.parsed.sources, compiled.source_packages),\n        ("Parent", compiled.parsed.parents, compiled.parent_packages),\n    ):\n        canonical_names = {package.metadata.id: package.metadata.name for package in packages}\n        for dependency in authored:\n            canonical_name = canonical_names.get(dependency.id)\n            if canonical_name is not None and dependency.name != canonical_name:\n                drift.append(\n                    f"{relation} label mismatch for {dependency.id}: "\n                    f"{dependency.name!r} != accepted package name {canonical_name!r}"\n                )\n'''
    replace_once(outputs, old, new)

    tests = "tests/test_configuration_and_update_ux.py"
    replace_once(
        tests,
        "from contextcanon.outputs import write_outputs\n",
        "from contextcanon.outputs import check_outputs, write_outputs\n",
    )
    marker = '''            install_package(consumer, main_package)\n\n            listed = io.StringIO()\n'''
    inserted = '''            install_package(consumer, main_package)\n            write_outputs(Compiler(project).compile(project))\n            self.assertIn(\n                "Source label mismatch for source-id: 'stale accidental label' != accepted package name 'Shared Canonical'",\n                check_outputs(Compiler(project).compile(project)),\n            )\n\n            listed = io.StringIO()\n'''
    replace_once(tests, marker, inserted)

    marker2 = '''            self.assertIn("- [Shared Canonical]", (consumer / "CONTEXT.src.md").read_text(encoding="utf-8"))\n            self.assertNotIn("stale accidental label", (consumer / "CONTEXT.src.md").read_text(encoding="utf-8"))\n'''
    inserted2 = '''            self.assertIn("- [Shared Canonical]", (consumer / "CONTEXT.src.md").read_text(encoding="utf-8"))\n            self.assertNotIn("stale accidental label", (consumer / "CONTEXT.src.md").read_text(encoding="utf-8"))\n            write_outputs(Compiler(project).compile(project))\n            self.assertEqual(check_outputs(Compiler(project).compile(project)), [])\n'''
    replace_once(tests, marker2, inserted2)

    anchor = '''    def test_parent_propagate_updates_chain_top_down_in_one_command(self):\n'''
    new_test = '''    def test_check_reports_stale_parent_display_name(self):\n        repo = Path(tempfile.mkdtemp())\n        try:\n            (repo / ".git").mkdir()\n            parent = write_node(repo, "root", "Canonical Parent", "1.0.0", "Meaning.")\n            child_root = repo / "child"\n            child_root.mkdir()\n            source = parent_source("child", "Child", "..", parent).replace("[Canonical Parent]", "[stale parent label]")\n            (child_root / "CONTEXT.src.md").write_text(source, encoding="utf-8")\n            install_package(child_root, parent)\n            compiled = Compiler(repo).compile(child_root)\n            write_outputs(compiled)\n            self.assertIn(\n                "Parent label mismatch for root: 'stale parent label' != accepted package name 'Canonical Parent'",\n                check_outputs(Compiler(repo).compile(child_root)),\n            )\n        finally:\n            shutil.rmtree(repo, ignore_errors=True)\n\n'''
    path = Path(tests)
    text = path.read_text(encoding="utf-8")
    if "test_check_reports_stale_parent_display_name" not in text:
        if text.count(anchor) != 1:
            raise RuntimeError("parent test anchor not found")
        path.write_text(text.replace(anchor, new_test + anchor, 1), encoding="utf-8")

    doc = "nodes/library/foundation/docs/source-format.md"
    replace_once(
        doc,
        "The visible locator records where a newer Parent candidate may later be discovered. Ordinary `contextcanon build` never dereferences it.",
        "The visible label must match the canonical Node name of the accepted Parent package; the link target records where a newer Parent candidate may later be discovered. Stable ID/version/digests remain the technical identity. `contextcanon check` reports a stale or accidentally edited Parent label. Ordinary `contextcanon build` never dereferences the locator.",
    )
    replace_once(
        doc,
        "`## Sources` lists accepted Context Nodes. The visible link names the Source location; the adjacent compiler-managed comment preserves stable identity and accepted version.",
        "`## Sources` lists accepted Context Nodes. The visible link label must match the canonical Node name of the accepted Source package, while the link target is its provenance/update location. The adjacent compiler-managed comment preserves stable identity and accepted version. Stable ID/version/digests define technical identity; `contextcanon check` reports a stale or accidentally edited visible Source label.",
    )
    replace_once(
        doc,
        "`contextcanon source list` shows the canonical name from each accepted Source package, stable IDs and the resolved discovery configuration. If a consumer carries a stale visible label, the list warns about it while name-based commands still accept the canonical package name.",
        "`contextcanon source list` shows the canonical name from each accepted Source package, stable IDs and the resolved discovery configuration. If a consumer carries a stale visible label, the list warns about it while name-based commands still accept the canonical package name; `contextcanon check` reports that mismatch until the source is repaired or a successful acceptance normalizes the label.",
    )


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "plan":
        update_plan()
    elif mode == "product":
        update_product()
    else:
        raise SystemExit("usage: helper.py plan|product")
