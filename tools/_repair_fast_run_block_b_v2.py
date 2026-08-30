from pathlib import Path

path = Path("tools/_fast_run_block_b.py")
text = path.read_text(encoding="utf-8")


def replace_once(old: str, new: str, label: str) -> None:
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one target, found {count}")
    text = text.replace(old, new, 1)


marker = '''# Block-B focused tests use the existing placement fixture and prove persistence,
# direct Markdown editing, stable authoring IDs, and owner-selected Source origin.
test = Path("tests/test_onboarding_placement_review.py")
'''
replace_once(
    marker,
    '''# Update the pre-existing CLI assertion to the directly editable wording line.
replace_once(
    "tests/test_onboarding_placement.py",
    '        self.assertIn("Wording origin: **exact**", workspace.placement_path.read_text(encoding="utf-8"))\\n',
    '        self.assertIn("Wording: `exact`", workspace.placement_path.read_text(encoding="utf-8"))\\n',
)

''' + marker,
    "legacy CLI assertion insertion",
)
replace_once(
    "from tests.test_onboarding_placement import OnboardingPlacementTests\n",
    "import tests.test_onboarding_placement as placement_fixture\n",
    "fixture import",
)
replace_once(
    "        helper = OnboardingPlacementTests()\n",
    "        helper = placement_fixture.OnboardingPlacementTests()\n",
    "fixture constructor",
)
replace_once(
    '''        raw = helper.placement_dict(prepared, workspace, readme, architecture, package)
        workspace.placement_proposal_path.write_text(json.dumps(raw), encoding="utf-8")
''',
    '''        raw = helper.placement_dict(prepared, workspace, readme, architecture, package)
        if owner_source:
            # Exercise explicit owner selection independently from an LLM Source match.
            raw["source_reuses"] = []
        workspace.placement_proposal_path.write_text(json.dumps(raw), encoding="utf-8")
''',
    "owner source fixture",
)
replace_once(
    '''        self.assertEqual(len(review.sources), 2)
        self.assertEqual({source.origin for source in review.sources}, {"evidence-derived", "owner-selected"})
''',
    '''        self.assertEqual(len(review.sources), 1)
        self.assertEqual(review.sources[0].origin, "owner-selected")
''',
    "owner source assertion",
)
replace_once(
    '        text = text.replace("## P-001 — Repository source of truth", "## P-001 — Canonical installation authority")\n',
    '        text = text.replace("## P-001 — Repository is the installation specification", "## P-001 — Canonical installation authority")\n',
    "editable title fixture",
)
path.write_text(text, encoding="utf-8", newline="\n")
