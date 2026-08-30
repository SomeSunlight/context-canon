from pathlib import Path

path = Path("tests/test_onboarding_placement_publish.py")
text = path.read_text(encoding="utf-8")
text = text.replace(
    'from contextcanon.onboarding_placement_review import create_or_load_placement_review, load_placement_review\n',
    'from contextcanon.onboarding_placement_review import create_or_load_placement_review, load_placement_review\n'
    'from contextcanon.onboarding_structure import create_or_load_structure_markdown\n',
    1,
)
old = '''        structure_text = workspace.structure_path.read_text(encoding="utf-8")\n        structure_text = structure_text.replace(\n            "<!-- contextcanon-fixed-markdown:start -->\\n<!-- contextcanon-fixed-markdown:end -->",\n            "<!-- contextcanon-fixed-markdown:start -->\\n- `README.md`\\n<!-- contextcanon-fixed-markdown:end -->",\n        )\n        workspace.structure_path.write_text(structure_text, encoding="utf-8")\n'''
new = '''        structure_raw = json.loads(workspace.structure_proposal_path.read_text(encoding="utf-8"))\n        structure_raw["knowledge_bodies"] = [\n            {\n                "key": "K-001",\n                "kind": "authoritative-reference",\n                "name": "README authority",\n                "suggested_node_key": "N-001",\n                "paths": ["README.md"],\n                "purpose": "Exercise fixed Markdown authority handling in placement publication.",\n                "rationale": "The test intentionally treats README as fixed only after Pass 1 proposed it as a knowledge body.",\n                "confidence": "high",\n                "evidence": [\n                    {\n                        "path": "README.md",\n                        "sha256": readme.sha256,\n                        "start_line": 1,\n                        "end_line": 2,\n                    }\n                ],\n            }\n        ]\n        workspace.structure_proposal_path.write_text(json.dumps(structure_raw, indent=2), encoding="utf-8")\n        workspace.structure_path.unlink()\n        create_or_load_structure_markdown(\n            prepared.snapshot_root, workspace.structure_proposal_path, workspace.structure_path\n        )\n        structure_text = workspace.structure_path.read_text(encoding="utf-8")\n        structure_text = structure_text.replace(\n            "<!-- contextcanon-fixed-markdown:start -->\\n<!-- contextcanon-fixed-markdown:end -->",\n            "<!-- contextcanon-fixed-markdown:start -->\\n- `README.md`\\n<!-- contextcanon-fixed-markdown:end -->",\n        )\n        workspace.structure_path.write_text(structure_text, encoding="utf-8")\n'''
if text.count(old) != 1:
    raise SystemExit(f"fixture target count={text.count(old)}")
path.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")
