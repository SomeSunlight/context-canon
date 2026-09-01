from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "PLAN.md"
STATE = ROOT / "STATE.md"
SOURCE = ROOT / "src/contextcanon/onboarding_structure_materialize.py"
TEST = ROOT / "tests/test_onboarding_structure_materialize.py"

BLOCK = '''\n\n#### Block I — recover generated child Nodes during repeated onboarding\n\nPurpose: close the next live `ai-workstation` Step-4 restart gap: a child Node such as `bootstrap` may already have provably generated `.context`/`CONTEXT` state from an earlier onboarding run while its `CONTEXT.src.md` was removed by reset/cleanup. That is established ContextCanon state, not automatically a foreign collision.\n\n- [ ] Generalize safe authoring recovery from the project root to every accepted Node path when that Node's own generated machine/package state proves one stable identity.\n- [ ] Keep root-only acceptance-record recovery root-only; child recovery must come from the child's own generated state rather than inherited/project-root evidence.\n- [ ] Preserve strict collision safety: foreign `CONTEXT/` content or unknown child `.context` entries must still abort before mutation.\n- [ ] Add regressions for a recoverable generated child Node and a child `.context` namespace containing foreign state, then run the complete suite/build/check and normal exact-head PR CI before returning a new test SHA.\n'''


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"missing expected {label}")
    if text.count(old) != 1:
        raise SystemExit(f"expected one {label}, found {text.count(old)}")
    return text.replace(old, new, 1)


def prepare() -> None:
    plan = PLAN.read_text(encoding="utf-8")
    if "#### Block I — recover generated child Nodes" not in plan:
        PLAN.write_text(plan.rstrip() + BLOCK, encoding="utf-8", newline="\n")

    text = SOURCE.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "def _recover_root_identity(root: Path) -> _RecoveredNodeIdentity | None:\n",
        "def _recover_node_identity(root: Path, *, include_acceptance: bool) -> _RecoveredNodeIdentity | None:\n",
        "recovery function name",
    )
    text = replace_once(
        text,
        '''    accepted = root / ".context" / "onboarding" / "accepted"\n    if accepted.is_dir() and not accepted.is_symlink():\n        for path in sorted(accepted.glob("*/acceptance.json")):\n            raw = _json_object(path)\n            if raw is None or raw.get("schema") != "contextcanon/onboarding-acceptance/v0":\n                continue\n            item = _identity(raw.get("node"), path.relative_to(root).as_posix())\n            if item is not None:\n                candidates.append(item)\n''',
        '''    if include_acceptance:\n        accepted = root / ".context" / "onboarding" / "accepted"\n        if accepted.is_dir() and not accepted.is_symlink():\n            for path in sorted(accepted.glob("*/acceptance.json")):\n                raw = _json_object(path)\n                if raw is None or raw.get("schema") != "contextcanon/onboarding-acceptance/v0":\n                    continue\n                item = _identity(raw.get("node"), path.relative_to(root).as_posix())\n                if item is not None:\n                    candidates.append(item)\n''',
        "root acceptance guard",
    )
    text = text.replace("Conflicting prior ContextCanon root identities", "Conflicting prior ContextCanon Node identities")
    text = text.replace("Conflicting generated ContextCanon root name/version metadata", "Conflicting generated ContextCanon Node name/version metadata")
    text = text.replace("Prior ContextCanon acceptance records disagree on root name/version", "Prior ContextCanon acceptance records disagree on Node name/version")

    text = replace_once(
        text,
        '''    readme = context / "README.md"\n    if readme.is_file() and not readme.is_symlink():\n        try:\n            if readme.read_text(encoding="utf-8").startswith("# Generated Context package resources\\n"):\n                return True\n        except (OSError, UnicodeDecodeError):\n            pass\n    for path in files:\n        if path.is_symlink():\n            return False\n        rel = path.relative_to(root).as_posix()\n        expected = _manifest_file_hash(root, rel)\n        if expected is None or hashlib.sha256(path.read_bytes()).hexdigest() != expected:\n            return False\n    return True\n\n\ndef _framework_root_machine_namespace(root: Path) -> bool:\n''',
        '''    generated_readme = False\n    readme = context / "README.md"\n    if readme.is_file() and not readme.is_symlink():\n        try:\n            generated_readme = readme.read_text(encoding="utf-8").startswith("# Generated Context package resources\\n")\n        except (OSError, UnicodeDecodeError):\n            generated_readme = False\n    for path in files:\n        if path.is_symlink():\n            return False\n        rel = path.relative_to(root).as_posix()\n        if rel == "CONTEXT/README.md" and generated_readme:\n            continue\n        expected = _manifest_file_hash(root, rel)\n        if expected is None or hashlib.sha256(path.read_bytes()).hexdigest() != expected:\n            return False\n    return True\n\n\ndef _framework_machine_namespace(root: Path, *, allow_onboarding: bool) -> bool:\n''',
        "generated CONTEXT namespace safety",
    )
    text = replace_once(
        text,
        '''    allowed = {"onboarding", "context.yaml", "package.json", "sources"}\n''',
        '''    allowed = {"context.yaml", "package.json", "sources"}\n    if allow_onboarding:\n        allowed.add("onboarding")\n''',
        "machine namespace allowlist",
    )
    text = replace_once(
        text,
        '''    if root.resolve() != project_root.resolve():\n        raise ContextCanonError("Internal onboarding error: authoring recovery is supported only for the established project root")\n    if not _matches_generated_manifest(root, "CONTEXT.md"):\n''',
        '''    if not _matches_generated_manifest(root, "CONTEXT.md"):\n''',
        "root-only recovery restriction",
    )
    text = replace_once(
        text,
        '''    if not _framework_root_machine_namespace(root):\n        raise ContextCanonError(\n            f"Refusing to recover Context Node at {root}: .context contains non-ContextCanon-owned entries"\n        )\n''',
        '''    if not _framework_machine_namespace(\n        root,\n        allow_onboarding=root.resolve() == project_root.resolve(),\n    ):\n        raise ContextCanonError(\n            f"Refusing to recover Context Node at {root}: .context contains non-ContextCanon-owned entries"\n        )\n''',
        "machine namespace recovery check",
    )
    text = replace_once(
        text,
        '''        if node.path == ".":\n            recovered = _recover_root_identity(root)\n            if recovered is None:\n                raise ContextCanonError(\n                    "Structure-first continuation found no CONTEXT.src.md at the project root and no unambiguous prior ContextCanon root identity to recover"\n                )\n            _preflight_new_node(root, project_root=project, recovery_identity=recovered)\n            items.append(\n                StructureMaterializationItem(\n                    key=node.key,\n                    name=node.name,\n                    path=node.path,\n                    lifecycle=node.lifecycle,\n                    status="recover",\n                    existing_node_id=recovered.id,\n                    existing_node_name=recovered.name,\n                    existing_node_version=recovered.version,\n                    directory_exists=True,\n                )\n            )\n            continue\n        _preflight_new_node(root, project_root=project)\n''',
        '''        recovered = _recover_node_identity(root, include_acceptance=node.path == ".")\n        if recovered is not None:\n            _preflight_new_node(root, project_root=project, recovery_identity=recovered)\n            items.append(\n                StructureMaterializationItem(\n                    key=node.key,\n                    name=node.name,\n                    path=node.path,\n                    lifecycle=node.lifecycle,\n                    status="recover",\n                    existing_node_id=recovered.id,\n                    existing_node_name=recovered.name,\n                    existing_node_version=recovered.version,\n                    directory_exists=True,\n                )\n            )\n            continue\n        if node.path == ".":\n            raise ContextCanonError(\n                "Structure-first continuation found no CONTEXT.src.md at the project root and no unambiguous prior ContextCanon root identity to recover"\n            )\n        _preflight_new_node(root, project_root=project)\n''',
        "preview recovery branch",
    )
    SOURCE.write_text(text, encoding="utf-8", newline="\n")

    tests = TEST.read_text(encoding="utf-8")
    anchor = '''    def test_root_recovery_still_refuses_foreign_context_directory(self):\n'''
    addition = '''    def test_preview_recovers_missing_child_source_from_generated_contextcanon_state(self):\n        repo, prepared, workspace = self.make_project()\n        initial = preview_structure_materialization(\n            prepared.snapshot_root,\n            workspace.structure_proposal_path,\n            workspace.structure_path,\n        )\n        materialize_structure_skeletons(initial)\n        child = repo / "bootstrap"\n        child_id = parse_node(child, repo).metadata.id\n        (child / "CONTEXT.src.md").unlink()\n\n        preview = preview_structure_materialization(\n            prepared.snapshot_root,\n            workspace.structure_proposal_path,\n            workspace.structure_path,\n        )\n        item = next(value for value in preview.items if value.path == "bootstrap")\n        self.assertEqual(item.status, "recover")\n        self.assertEqual(item.existing_node_id, child_id)\n\n        created = materialize_structure_skeletons(preview)\n        self.assertEqual(created, (child / "CONTEXT.src.md",))\n        self.assertEqual(parse_node(child, repo).metadata.id, child_id)\n\n    def test_child_recovery_refuses_foreign_machine_namespace(self):\n        repo, prepared, workspace = self.make_project()\n        initial = preview_structure_materialization(\n            prepared.snapshot_root,\n            workspace.structure_proposal_path,\n            workspace.structure_path,\n        )\n        materialize_structure_skeletons(initial)\n        child = repo / "bootstrap"\n        (child / "CONTEXT.src.md").unlink()\n        (child / ".context" / "foreign.txt").write_text("project-owned\\n", encoding="utf-8")\n\n        with self.assertRaisesRegex(ContextCanonError, ".context contains non-ContextCanon-owned entries"):\n            preview_structure_materialization(\n                prepared.snapshot_root,\n                workspace.structure_proposal_path,\n                workspace.structure_path,\n            )\n\n'''
    if "def test_preview_recovers_missing_child_source_from_generated_contextcanon_state" not in tests:
        tests = replace_once(tests, anchor, addition + anchor, "child recovery test anchor")
        TEST.write_text(tests, encoding="utf-8", newline="\n")


def finalize() -> None:
    plan = PLAN.read_text(encoding="utf-8")
    if "#### Block I — recover generated child Nodes" not in plan:
        raise SystemExit("Block I missing from PLAN")
    start = plan.index("#### Block I — recover generated child Nodes")
    prefix, block = plan[:start], plan[start:]
    block = block.replace("- [ ] ", "- [x] ")
    if "Child-node recovery checkpoint:" not in block:
        block = block.rstrip() + "\n\nChild-node recovery checkpoint: the live `bootstrap` failure proved that restart recovery must be Node-local rather than root-special. Any accepted Node path can now recover a missing `CONTEXT.src.md` only when its own generated package/machine state proves one unambiguous stable Node identity; root acceptance records remain root-only evidence. Foreign child `.context` entries and unverified `CONTEXT/` bytes still abort before mutation. The focused additions raise the deterministic suite from 144 to 146 tests.\n"
    PLAN.write_text(prefix + block, encoding="utf-8", newline="\n")

    state = STATE.read_text(encoding="utf-8")
    note = '''\n\n## Latest child-node restart recovery\n\nThe next live `ai-workstation` Step-4 run exposed `bootstrap` with a missing `CONTEXT.src.md` but existing `.context` machine state. Recovery is now Node-local: every accepted Node may recover its authoring skeleton only from its own verifiable generated identity/state; only the project root may additionally use prior onboarding acceptance records. This preserves stable child IDs across reset/retest cycles without weakening foreign-path collision protection. Focused regressions cover both successful child recovery and refusal of unknown child `.context` entries.\n'''
    if "## Latest child-node restart recovery" not in state:
        STATE.write_text(state.rstrip() + note, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in {"prepare", "finalize"}:
        raise SystemExit("usage: _apply_child_node_recovery_fix.py prepare|finalize")
    if sys.argv[1] == "prepare":
        prepare()
    else:
        finalize()
