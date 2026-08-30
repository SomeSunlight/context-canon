from pathlib import Path

path = Path("tools/_fast_run_block_b.py")
text = path.read_text(encoding="utf-8")

old = '''# Block-B focused tests use the existing placement fixture and prove persistence,\n# direct Markdown editing, stable authoring IDs, and owner-selected Source origin.\ntest = Path("tests/test_onboarding_placement_review.py")\n'''
new = '''# Update the pre-existing CLI assertion to the new directly editable wording line.\nreplace_once(\n    "tests/test_onboarding_placement.py",\n    '        self.assertIn("Wording origin: **exact**", workspace.placement_path.read_text(encoding="utf-8"))\\n',\n    '        self.assertIn("Wording: `exact`", workspace.placement_path.read_text(encoding="utf-8"))\\n',\n)\n\n# Block-B focused tests use the existing placement fixture and prove persistence,\n# direct Markdown editing, stable authoring IDs, and owner-selected Source origin.\ntest = Path("tests/test_onboarding_placement_review.py")\n'''
if text.count(old) != 1:
    raise SystemExit(f"assertion insertion target count={text.count(old)}")
text = text.replace(old, new, 1)
text = text.replace(
    'from tests.test_onboarding_placement import OnboardingPlacementTests\\n',
    'import tests.test_onboarding_placement as placement_fixture\\n',
    1,
)
text = text.replace(
    '        helper = OnboardingPlacementTests()\\n',
    '        helper = placement_fixture.OnboardingPlacementTests()\\n',
    1,
)
old = '''        raw = helper.placement_dict(prepared, workspace, readme, architecture, package)\n        workspace.placement_proposal_path.write_text(json.dumps(raw), encoding="utf-8")\n'''
new = '''        raw = helper.placement_dict(prepared, workspace, readme, architecture, package)\n        if owner_source:\n            # Exercise the explicit owner path independently of LLM-derived reuse.\n            raw["source_reuses"] = []\n        workspace.placement_proposal_path.write_text(json.dumps(raw), encoding="utf-8")\n'''
if text.count(old) != 1:
    raise SystemExit(f"owner source fixture target count={text.count(old)}")
text = text.replace(old, new, 1)
text = text.replace(
    '        self.assertEqual(len(review.sources), 2)\\n        self.assertEqual({source.origin for source in review.sources}, {"evidence-derived", "owner-selected"})\\n',
    '        self.assertEqual(len(review.sources), 1)\\n        self.assertEqual(review.sources[0].origin, "owner-selected")\\n',
    1,
)
text = text.replace(
    '        text = text.replace("## P-001 — Repository source of truth", "## P-001 — Canonical installation authority")\\n',
    '        text = text.replace("## P-001 — Repository is the installation specification", "## P-001 — Canonical installation authority")\\n',
    1,
)
path.write_text(text, encoding="utf-8", newline="\n")
