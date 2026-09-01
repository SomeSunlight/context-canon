from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    (ROOT / path).write_text(text, encoding="utf-8", newline="\n")


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one match, found {count}")
    return text.replace(old, new, 1)


def fix_cli() -> None:
    path = "src/contextcanon/cli.py"
    text = read(path)
    text = once(
        text,
        "from .onboarding_workspace import open_onboarding_workspace, update_workspace_checkpoint, write_utf8",
        "from .onboarding_workspace import open_onboarding_workspace, remember_run_inputs, update_workspace_checkpoint, write_utf8",
        "CLI run-input import",
    )
    write(path, text)


def fix_workspace_migration() -> None:
    path = "src/contextcanon/onboarding_workspace.py"
    text = read(path)
    anchor = '''    owner_specs = machine_owner or _remember_first(\n        plan,\n        (\n            "- Owner-selected Source choices already recorded in the human review (do not repeat on preview/publish):",\n            "- Owner-selected Source choices already recorded in `placement.md` (do not repeat on preview/publish):",\n        ),\n    )\n\n    refreshed = _workspace_plan()\n'''
    replacement = '''    owner_specs = machine_owner or _remember_first(\n        plan,\n        (\n            "- Owner-selected Source choices already recorded in the human review (do not repeat on preview/publish):",\n            "- Owner-selected Source choices already recorded in `placement.md` (do not repeat on preview/publish):",\n        ),\n    )\n    if (catalog_inputs or owner_specs) and not (machine_catalog or machine_owner):\n        catalog_inputs, owner_specs = remember_run_inputs(\n            snapshot_root, catalog_inputs=catalog_inputs, owner_source_specs=owner_specs\n        )\n\n    refreshed = _workspace_plan()\n'''
    text = once(text, anchor, replacement, "PLAN-to-machine run-input migration")
    write(path, text)


def fix_reset_journal() -> None:
    path = "src/contextcanon/onboarding_reset.py"
    text = read(path)
    text = once(
        text,
        "from .outputs import expected_outputs\nfrom .parser import ContextCanonError, find_repo_root",
        "from .onboarding_proposal import load_evidence_snapshot\nfrom .outputs import expected_outputs\nfrom .parser import ContextCanonError, find_repo_root",
        "reset Evidence import",
    )
    text = once(
        text,
        '''def _managed_state(project_root: Path) -> dict[str, bytes | None]:\n    project = project_root.resolve()\n''',
        '''def _managed_state(project_root: Path, extra_paths: Iterable[str] = ()) -> dict[str, bytes | None]:\n    project = project_root.resolve()\n''',
        "managed state signature",
    )
    text = once(
        text,
        '''        if source_store.is_dir():\n            for path in source_store.rglob("*"):\n                if path.is_file():\n                    result[path.relative_to(project).as_posix()] = path.read_bytes()\n    return result\n''',
        '''        if source_store.is_dir():\n            for path in source_store.rglob("*"):\n                if path.is_file():\n                    result[path.relative_to(project).as_posix()] = path.read_bytes()\n    for rel in extra_paths:\n        path = project / rel\n        result[rel] = path.read_bytes() if path.is_file() else None\n    return result\n''',
        "managed Evidence state",
    )
    text = once(
        text,
        '''    project = (project_arg or find_repo_root(snapshot)).resolve()\n    before = _managed_state(project)\n    result = delegate(argv)\n    if result != 0:\n        return result\n    after = _managed_state(project)\n''',
        '''    project = (project_arg or find_repo_root(snapshot)).resolve()\n    extra_paths: tuple[str, ...] = ()\n    if argv[1] == "placement-publish":\n        extra_paths = tuple(\n            entry.path for entry in load_evidence_snapshot(snapshot).entries if entry.path.lower().endswith(".md")\n        )\n    before = _managed_state(project, extra_paths)\n    result = delegate(argv)\n    if result != 0:\n        return result\n    after = _managed_state(project, extra_paths)\n''',
        "journal source documents",
    )
    write(path, text)


def fix_tests() -> None:
    path = "tests/test_onboarding_placement_publish.py"
    text = read(path)
    text = once(
        text,
        '''        review_text = workspace.placement_path.read_text(encoding="utf-8").replace(\n            "Decision: `pending`", "Decision: `accept`"\n        )\n''',
        '''        review_text = workspace.placement_path.read_text(encoding="utf-8").replace(\n            "Decision: `pending`", "Decision: `accept`"\n        ).replace("Source edit decision: `pending`", "Source edit decision: `accept`")\n''',
        "publish accepts source edits",
    )
    write(path, text)

    path = "tests/test_onboarding_reset.py"
    text = read(path)
    old = '''    def test_machine_run_inputs_survive_missing_workspace_plan(self):\n        repo, prepared, workspace = self.make_workspace()\n        from contextcanon.onboarding_workspace import remember_run_inputs, open_onboarding_workspace\n        remember_run_inputs(\n            prepared.snapshot_root,\n            catalog_inputs=("C:/catalog/development-workflow",),\n            owner_source_specs=("N-001=c4c94726-3cc7-4df6-b779-72bbf9c06f40",),\n        )\n        workspace.plan_path.unlink()\n        reopened = open_onboarding_workspace(prepared.snapshot_root, create=False)\n'''
    new = '''    def test_machine_run_inputs_survive_missing_workspace_plan(self):\n        repo, prepared = self.make_repo()\n        workspace = open_onboarding_workspace(prepared.snapshot_root, create=True)\n        from contextcanon.onboarding_workspace import remember_run_inputs\n        remember_run_inputs(\n            prepared.snapshot_root,\n            catalog_inputs=("C:/catalog/development-workflow",),\n            owner_source_specs=("N-001=c4c94726-3cc7-4df6-b779-72bbf9c06f40",),\n        )\n        workspace.plan_path.unlink()\n        reopened = open_onboarding_workspace(prepared.snapshot_root, create=False)\n'''
    text = once(text, old, new, "run-input test fixture")
    extra = '''\n    def test_step9_journal_restores_reviewed_source_document(self):\n        repo, prepared = self.make_repo()\n        source_before = (repo / "README.md").read_bytes()\n\n        def fake_publish(_argv):\n            (repo / "README.md").write_text("# Project\\n\\nShort orientation after promotion.\\n", encoding="utf-8")\n            return 0\n\n        result = run_journaled(\n            ["onboard", "placement-publish", str(prepared.snapshot_root)],\n            fake_publish,\n        )\n        self.assertEqual(result, 0)\n        self.assertNotEqual((repo / "README.md").read_bytes(), source_before)\n        reset_onboarding(prepared.snapshot_root, from_step=9)\n        self.assertEqual((repo / "README.md").read_bytes(), source_before)\n'''
    marker = '\n\nif __name__ == "__main__":'
    if "test_step9_journal_restores_reviewed_source_document" not in text:
        text = text.replace(marker, extra + marker)
    write(path, text)


def main() -> None:
    fix_cli()
    fix_workspace_migration()
    fix_reset_journal()
    fix_tests()


if __name__ == "__main__":
    main()
