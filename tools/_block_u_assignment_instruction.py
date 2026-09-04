from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def patch(rel: str, old: str, new: str, *, count: int = 1) -> None:
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    actual = text.count(old)
    if actual != count:
        raise SystemExit(f"{rel}: expected {count} occurrence(s), found {actual}: {old[:120]!r}")
    path.write_text(text.replace(old, new, count), encoding="utf-8", newline="\n")


# The placement LLM must see not only which reusable packages exist but which
# relationships the human already accepted in STEP 05. Otherwise it can still
# propose semantically duplicate local Rules/Source relations.
patch(
    "src/contextcanon/onboarding_placement_instruction.py",
    "from .onboarding_proposal import load_evidence_snapshot\n",
    "from .onboarding_proposal import load_evidence_snapshot\nfrom .onboarding_reusable_contexts import ReusableContextAssignment\n",
)

patch(
    "src/contextcanon/onboarding_placement_instruction.py",
    '''def _render_catalog(packages: tuple[CompiledPackage, ...]) -> list[str]:\n''',
    '''def _render_accepted_reusable_contexts(\n    assignments: tuple[ReusableContextAssignment, ...],\n) -> list[str]:\n    lines = [\n        "## Accepted reusable Context assignments — already decided",\n        "",\n    ]\n    if not assignments:\n        lines.extend([\n            "No owner-selected reusable Context relationship applies in this onboarding.",\n            "",\n        ])\n        return lines\n    lines.extend([\n        "The project owner already accepted these composition relationships in STEP 05. Treat them as fixed input for placement, not as Source suggestions to rediscover. A reusable Context attached to a project Node also reaches that Node's semantic descendants through the accepted Parent chain. Do not duplicate its generic Rules/Topics locally merely because the same project prose mentions them.",\n        "",\n    ])\n    for assignment in assignments:\n        lines.extend([\n            f"- `{assignment.target_node_key}` — **{assignment.target_name}** (`{assignment.target_path}`) ← **{assignment.source_name}** (`{assignment.source_version}`)",\n            f"  Why: {assignment.why}",\n            f"  Exact Source: `{assignment.source_node_id}` · `{assignment.source_package_digest}`",\n        ])\n    lines.extend([\n        "",\n        "Do not emit a `source_reuses` entry for one of these already accepted relationships, or for the same Source redundantly at one of its descendant Nodes. `source_reuses` is reserved for a genuinely new Evidence-derived relationship that STEP 05 did not already establish.",\n        "",\n    ])\n    return lines\n\n\ndef _render_catalog(packages: tuple[CompiledPackage, ...]) -> list[str]:\n''',
)

patch(
    "src/contextcanon/onboarding_placement_instruction.py",
    '''    *,\n    catalog_package_roots: Iterable[Path] = (),\n) -> OnboardingPlacementInstruction:\n''',
    '''    *,\n    catalog_package_roots: Iterable[Path] = (),\n    accepted_reusable_assignments: Iterable[ReusableContextAssignment] = (),\n) -> OnboardingPlacementInstruction:\n''',
)
patch(
    "src/contextcanon/onboarding_placement_instruction.py",
    '''    packages = _load_catalog(catalog_package_roots)\n\n    lines = [\n''',
    '''    packages = _load_catalog(catalog_package_roots)\n    assignments = tuple(accepted_reusable_assignments)\n\n    lines = [\n''',
)
patch(
    "src/contextcanon/onboarding_placement_instruction.py",
    '''    lines.extend(_render_structure(structure))\n    lines.extend(_render_catalog(packages))\n''',
    '''    lines.extend(_render_structure(structure))\n    lines.extend(_render_accepted_reusable_contexts(assignments))\n    lines.extend(_render_catalog(packages))\n''',
)

# The wording altered earlier in Block U is made explicit about the already
# accepted assignment set rather than only the package catalog.
patch(
    "src/contextcanon/onboarding_placement_instruction.py",
    '"14. Compare likely generic practices with every supplied reusable Source package before proposing a duplicate local Rule. Reusable Context assignments are reviewed before this pass; project-specific deltas may still remain local. Return `source_reuses` only for a genuinely new Evidence-derived relationship not already established by the human reusable-Context gate.",\n',
    '"14. Compare likely generic practices with every supplied reusable Source package and the accepted STEP-05 assignments before proposing a duplicate local Rule. A Source attached to an ancestor is already effective in its semantic descendants through Parent composition. Project-specific deltas may still remain local. Return `source_reuses` only for a genuinely new Evidence-derived relationship not already established by the human reusable-Context gate or inherited from one of its assignments.",\n',
)

# Preserve the accepted assignment set through the placement CLI group.
patch(
    "src/contextcanon/cli.py",
    '''                owner_source_whys: dict[str, str] = {}\n                preaccepted_owner_sources = False\n\n                structure_proposal = load_onboarding_structure_proposal(structure_proposal_path, snapshot)\n''',
    '''                owner_source_whys: dict[str, str] = {}\n                preaccepted_owner_sources = False\n                accepted_reusable_assignments = ()\n\n                structure_proposal = load_onboarding_structure_proposal(structure_proposal_path, snapshot)\n''',
)
patch(
    "src/contextcanon/cli.py",
    '''                    owner_source_whys = reusable.owner_source_whys\n                    preaccepted_owner_sources = True\n''',
    '''                    owner_source_whys = reusable.owner_source_whys\n                    accepted_reusable_assignments = reusable.assignments\n                    preaccepted_owner_sources = True\n''',
)
patch(
    "src/contextcanon/cli.py",
    '''                        structure_path,\n                        catalog_package_roots=catalog,\n                    )\n''',
    '''                        structure_path,\n                        catalog_package_roots=catalog,\n                        accepted_reusable_assignments=accepted_reusable_assignments,\n                    )\n''',
)

# Redundant Source proposals are suppressed not only for the exact STEP-05
# target, but also below that target where Parent inheritance already delivers
# the same Source.
patch(
    "src/contextcanon/onboarding_placement_review.py",
    '''    owner_pairs: dict[tuple[str, str], tuple[str, CompiledPackage]] = {}\n''',
    '''    owner_pairs: dict[tuple[str, str], tuple[str, CompiledPackage]] = {}\n    nodes_by_key = {node.key: node for node in proposal.structure.nodes}\n\n    def is_same_or_descendant(candidate_key: str, ancestor_key: str) -> bool:\n        current = candidate_key\n        seen_keys: set[str] = set()\n        while current is not None and current not in seen_keys:\n            if current == ancestor_key:\n                return True\n            seen_keys.add(current)\n            node = nodes_by_key.get(current)\n            current = None if node is None else node.parent_key\n        return False\n''',
)
patch(
    "src/contextcanon/onboarding_placement_review.py",
    '''    for reuse in proposal.source_reuses:\n        pair = (reuse.target_node_key, reuse.source_node_id)\n        if pair in owner_pairs:\n            continue\n''',
    '''    for reuse in proposal.source_reuses:\n        pair = (reuse.target_node_key, reuse.source_node_id)\n        if any(\n            source_id == reuse.source_node_id and is_same_or_descendant(reuse.target_node_key, owner_target)\n            for owner_target, source_id in owner_pairs\n        ):\n            continue\n''',
)

# Permanent focused regression for instruction visibility + descendant duplicate
# suppression. Add it to the test module generated earlier in this block.
path = ROOT / "tests" / "test_onboarding_reusable_contexts.py"
text = path.read_text(encoding="utf-8")
text = text.replace(
    "from contextcanon.outputs import write_outputs\n",
    "from contextcanon.outputs import write_outputs\nfrom contextcanon.onboarding_placement_instruction import _render_accepted_reusable_contexts\n",
    1,
)
needle = '''    def test_source_why_is_parsed_from_authored_source(self) -> None:\n'''
insert = '''    def test_accepted_assignment_is_explicit_placement_reasoning_input(self) -> None:\n        from contextcanon.onboarding_reusable_contexts import ReusableContextAssignment\n\n        assignment = ReusableContextAssignment(\n            target_node_key="N-001",\n            target_name="AI Workstation",\n            target_path=".",\n            source_node_id="workflow-node",\n            source_name="Development Workflow",\n            source_version="0.2.0-draft",\n            source_normalized_digest="1" * 64,\n            source_package_digest="2" * 64,\n            why="Shared development workflow applies to the whole project.",\n        )\n        rendered = "\\n".join(_render_accepted_reusable_contexts((assignment,)))\n        self.assertIn("already accepted", rendered)\n        self.assertIn("AI Workstation", rendered)\n        self.assertIn("Development Workflow", rendered)\n        self.assertIn("semantic descendants", rendered)\n        self.assertIn("Why: Shared development workflow applies to the whole project.", rendered)\n        self.assertIn("Do not emit a `source_reuses` entry", rendered)\n\n'''
if text.count(needle) != 1:
    raise SystemExit("test insertion point not found exactly once")
text = text.replace(needle, insert + needle, 1)
path.write_text(text, encoding="utf-8", newline="\n")
