from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise SystemExit(f"expected one match in {path}, found {text.count(old)}")
    target.write_text(text.replace(old, new), encoding="utf-8")


def append_once(path: str, marker: str, addition: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    if marker in text:
        return
    target.write_text(text.rstrip() + "\n\n" + addition.strip() + "\n", encoding="utf-8")


def apply() -> None:
    replace_once(
        "src/contextcanon/cli.py",
        '''def _catalog_labels(packages) -> tuple[str, ...]:\n    return tuple(\n        f"{package.metadata.id} · {package.metadata.name} · {package.metadata.version} · {package.package_digest}"\n        for package in packages\n    )\n\n\ndef _add_workspace(parser: argparse.ArgumentParser) -> None:\n''',
        '''def _catalog_labels(packages) -> tuple[str, ...]:\n    return tuple(\n        f"{package.metadata.id} · {package.metadata.name} · {package.metadata.version} · {package.package_digest}"\n        for package in packages\n    )\n\n\ndef _owner_specs_for_review(\n    review_path: Path, explicit: tuple[str, ...], remembered: tuple[str, ...]\n) -> tuple[str, ...]:\n    if explicit:\n        return explicit\n    return remembered if not review_path.exists() else ()\n\n\ndef _add_workspace(parser: argparse.ArgumentParser) -> None:\n''',
    )
    replace_once(
        "src/contextcanon/cli.py",
        '''                remembered_catalog, remembered_owner = remember_run_inputs(\n                    snapshot,\n                    catalog_inputs=catalog_inputs,\n                    owner_source_specs=tuple(args.owner_source) if hasattr(args, "owner_source") else (),\n                )\n''',
        '''                explicit_owner = tuple(args.owner_source) if hasattr(args, "owner_source") else ()\n                remembered_catalog, remembered_owner = remember_run_inputs(\n                    snapshot,\n                    catalog_inputs=catalog_inputs,\n                    owner_source_specs=explicit_owner,\n                )\n''',
    )
    replace_once(
        "src/contextcanon/cli.py",
        '''                if args.onboard_command == "placement-review":\n                    review, created = create_or_load_placement_review(\n                        review_path,\n                        proposal,\n                        snapshot,\n                        owner_source_specs=args.owner_source,\n                    )\n''',
        '''                if args.onboard_command == "placement-review":\n                    owner_for_review = _owner_specs_for_review(review_path, explicit_owner, remembered_owner)\n                    review, created = create_or_load_placement_review(\n                        review_path,\n                        proposal,\n                        snapshot,\n                        owner_source_specs=owner_for_review,\n                    )\n''',
    )
    replace_once(
        "src/contextcanon/cli.py",
        '''                        source_catalog_inputs=catalog_inputs,\n                        owner_source_specs=tuple(args.owner_source),\n                        next_action=next_action,\n''',
        '''                        source_catalog_inputs=catalog_inputs,\n                        owner_source_specs=explicit_owner or remembered_owner,\n                        next_action=next_action,\n''',
    )
    replace_once(
        "tests/test_onboarding_reset.py",
        '''from contextcanon.compiler import Compiler\n''',
        '''from contextcanon.cli import _owner_specs_for_review\nfrom contextcanon.compiler import Compiler\n''',
    )
    replace_once(
        "tests/test_onboarding_reset.py",
        '''    def test_step9_journal_restores_reviewed_source_document(self):\n''',
        '''    def test_remembered_owner_source_is_reused_only_when_review_is_created(self):\n        root = Path(tempfile.mkdtemp())\n        review = root / "STEP-07-placement.md"\n        remembered = ("N-001=c4c94726-3cc7-4df6-b779-72bbf9c06f40",)\n        self.assertEqual(_owner_specs_for_review(review, (), remembered), remembered)\n        review.write_text("existing human review\\n", encoding="utf-8")\n        self.assertEqual(_owner_specs_for_review(review, (), remembered), ())\n        explicit = ("N-002=11111111-1111-4111-8111-111111111111",)\n        self.assertEqual(_owner_specs_for_review(review, explicit, remembered), explicit)\n\n    def test_step9_journal_restores_reviewed_source_document(self):\n''',
    )


def finalize() -> None:
    append_once(
        "PLAN.md",
        "#### Block P — reuse persisted owner-selected Source when Step 7 is recreated",
        '''#### Block P — reuse persisted owner-selected Source when Step 7 is recreated\n\nPurpose: fix the live `ai-workstation` production-onboarding gate where snapshot-owned `run-inputs.json` correctly remembers the Development Workflow owner Source, but `placement-review` read that remembered value without using it to recreate `STEP-07-placement.md`.\n\n- [x] Reuse remembered owner Source specs when Step 7 is created and no explicit `--owner-source` was supplied.\n- [x] Preserve the existing one-time owner-choice contract: once STEP-07 exists, rerunning placement-review without the flag validates the human file; explicitly supplying `--owner-source` to an existing review remains an error.\n- [x] Keep the remembered owner choice in generated PLAN/checkpoint commands instead of replacing it with an empty CLI argument list.\n- [x] Add a focused regression for missing-vs-existing review behavior and run the complete deterministic/build/check/diff gate.\n\nOwner-Source recovery checkpoint: Step 7 recreation now actually consumes the owner Source already persisted in machine run state. This closes the gap between 'remembered' and 'used' and lets reset-from-7 reproduce the same owner-selected Development Workflow without asking the operator to reconstruct IDs.''',
    )
    append_once(
        "STATE.md",
        "## Latest remembered owner-Source recreation correction",
        '''## Latest remembered owner-Source recreation correction\n\nThe real `ai-workstation` production review exposed that `placement-review` loaded persisted owner Source specs from snapshot-owned `run-inputs.json` but still passed only the current CLI `--owner-source` arguments into review creation. As a result, a reset/recreated Step 7 could silently lose the previously selected Development Workflow Source even though machine state still remembered it. Review creation now uses the remembered owner choice when the review file is absent, while repeated validation of an existing human review keeps the one-time owner-selection boundary unchanged.''',
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2 or sys.argv[1] not in {"apply", "finalize"}:
        raise SystemExit("usage: _restore_remembered_owner_source.py apply|finalize")
    globals()[sys.argv[1]]()
