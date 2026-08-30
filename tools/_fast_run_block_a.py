from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    file = Path(path)
    text = file.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one replacement target, found {count}: {old[:80]!r}")
    file.write_text(text.replace(old, new), encoding="utf-8", newline="\n")


# ---------------------------------------------------------------------------
# Structure review: all Markdown is mutable by default; selected knowledge-body
# paths may be marked fixed. Existing v0 structure.md files remain readable and
# receive the proposal-derived fixed defaults in their normalized structure.
# ---------------------------------------------------------------------------
replace_once(
    "src/contextcanon/onboarding_structure.py",
    '_TREE_END = "<!-- contextcanon-node-tree:end -->"\n',
    '_TREE_END = "<!-- contextcanon-node-tree:end -->"\n'
    '_FIXED_MARKDOWN_START = "<!-- contextcanon-fixed-markdown:start -->"\n'
    '_FIXED_MARKDOWN_END = "<!-- contextcanon-fixed-markdown:end -->"\n'
    '_FIXED_MARKDOWN_LINE_RE = re.compile(r"^- `(?P<path>[^`]+)`$")\n',
)
replace_once(
    "src/contextcanon/onboarding_structure.py",
    '''@dataclass(frozen=True)\nclass HumanStructurePlan:\n    evidence_digest: str\n    proposal_digest: str\n    nodes: tuple[HumanStructureNode, ...]\n    structure_digest: str\n''',
    '''@dataclass(frozen=True)\nclass HumanStructurePlan:\n    evidence_digest: str\n    proposal_digest: str\n    nodes: tuple[HumanStructureNode, ...]\n    fixed_markdown: tuple[str, ...]\n    structure_digest: str\n''',
)
replace_once(
    "src/contextcanon/onboarding_structure.py",
    '''            if path not in snapshot.by_path:\n                raise _error(f"knowledge body path is not in evidence snapshot: {path}")\n            paths.append(path)\n''',
    '''            if path not in snapshot.by_path:\n                raise _error(f"knowledge body path is not in evidence snapshot: {path}")\n            if not path.lower().endswith(".md"):\n                raise _error(\n                    f"knowledge body path {path!r} is not supported in this experiment; "\n                    "non-Node document policy currently supports Markdown only"\n                )\n            paths.append(path)\n''',
)
replace_once(
    "src/contextcanon/onboarding_structure.py",
    '''    lines.extend(["", "## Proposed reusable Source matches", ""])\n''',
    '''    fixed_defaults = _default_fixed_markdown(proposal)\n    lines.extend(\n        [\n            "",\n            "## Fixed Markdown",\n            "",\n            "All Markdown knowledge bodies are mutable by default. List only project Markdown that must remain fixed/authoritative; the later placement pass may reference or map it but must not plan destructive cleanup of it.",\n            "",\n            _FIXED_MARKDOWN_START,\n        ]\n    )\n    if fixed_defaults:\n        for path in fixed_defaults:\n            lines.append(f"- `{path}`")\n    lines.extend([_FIXED_MARKDOWN_END, "", "## Proposed reusable Source matches", ""])\n''',
)
replace_once(
    "src/contextcanon/onboarding_structure.py",
    '''def _human_key(name: str, path: str, parent_key: str | None, lifecycle: str) -> str:\n''',
    '''def _default_fixed_markdown(proposal: OnboardingStructureProposal) -> tuple[str, ...]:\n    result: list[str] = []\n    seen: set[str] = set()\n    for body in proposal.knowledge_bodies:\n        if body.kind not in {"authoritative-reference", "imported-corpus"}:\n            continue\n        for path in body.paths:\n            if path not in seen:\n                seen.add(path)\n                result.append(path)\n    return tuple(result)\n\n\ndef _knowledge_body_markdown(proposal: OnboardingStructureProposal) -> set[str]:\n    return {path for body in proposal.knowledge_bodies for path in body.paths}\n\n\ndef _human_key(name: str, path: str, parent_key: str | None, lifecycle: str) -> str:\n''',
)
replace_once(
    "src/contextcanon/onboarding_structure.py",
    '''    normalized = {\n        "schema": STRUCTURE_MARKDOWN_SCHEMA,\n        "evidence_digest": proposal.evidence_digest,\n        "proposal_digest": proposal.proposal_digest,\n        "nodes": [node.to_dict() for node in nodes],\n    }\n    return HumanStructurePlan(\n        evidence_digest=proposal.evidence_digest,\n        proposal_digest=proposal.proposal_digest,\n        nodes=tuple(nodes),\n        structure_digest=_canonical_digest(normalized),\n    )\n''',
    '''    fixed_markdown = _default_fixed_markdown(proposal)\n    if _FIXED_MARKDOWN_START in raw_lines or _FIXED_MARKDOWN_END in raw_lines:\n        try:\n            fixed_start = raw_lines.index(_FIXED_MARKDOWN_START)\n            fixed_end = raw_lines.index(_FIXED_MARKDOWN_END)\n        except ValueError as exc:\n            raise _error("Fixed Markdown section must contain both boundary markers") from exc\n        if fixed_end < fixed_start:\n            raise _error("Fixed Markdown boundary markers are reversed")\n        allowed = _knowledge_body_markdown(proposal)\n        selected: list[str] = []\n        seen_fixed: set[str] = set()\n        for line_number, line in enumerate(raw_lines[fixed_start + 1 : fixed_end], start=fixed_start + 2):\n            if not line.strip():\n                continue\n            match = _FIXED_MARKDOWN_LINE_RE.fullmatch(line)\n            if match is None:\n                raise _error(f"Fixed Markdown line {line_number} must look like '- `docs/file.md`'")\n            path = match.group("path")\n            if path not in allowed:\n                raise _error(f"Fixed Markdown path is not a proposed knowledge-body Markdown path: {path}")\n            if path in seen_fixed:\n                raise _error(f"Fixed Markdown contains duplicate path {path}")\n            seen_fixed.add(path)\n            selected.append(path)\n        fixed_markdown = tuple(selected)\n\n    normalized = {\n        "schema": STRUCTURE_MARKDOWN_SCHEMA,\n        "evidence_digest": proposal.evidence_digest,\n        "proposal_digest": proposal.proposal_digest,\n        "nodes": [node.to_dict() for node in nodes],\n        "fixed_markdown": list(fixed_markdown),\n    }\n    return HumanStructurePlan(\n        evidence_digest=proposal.evidence_digest,\n        proposal_digest=proposal.proposal_digest,\n        nodes=tuple(nodes),\n        fixed_markdown=fixed_markdown,\n        structure_digest=_canonical_digest(normalized),\n    )\n''',
)

# Structure-discovery instruction: clarify the intentionally small Markdown-only
# document policy without changing the existing proposal JSON shape.
replace_once(
    "src/contextcanon/onboarding_structure_instruction.py",
    '''        "6. Separate **Nodes** from larger knowledge bodies that should remain documents/corpora rather than be rewritten into Node prose. Use `project-documentation` for ordinary project-owned documentation sets, `authoritative-reference` for standards/policies/specifications whose authority should remain external to the local wording, and `imported-corpus` for large imported information sets such as exported team documentation.",\n''',
    '''        "6. Separate **Nodes** from larger knowledge bodies that should remain documents/corpora rather than be rewritten into Node prose. This experiment supports Markdown knowledge-body paths only. Use `project-documentation` for ordinary project-owned Markdown that may later be reorganized, `authoritative-reference` for Markdown whose wording/authority must remain fixed, and `imported-corpus` for fixed imported Markdown sets. Non-Markdown authorities such as PDF are deliberately unsupported for placement/cleanup in this version rather than silently converted.",\n''',
)
replace_once(
    "src/contextcanon/onboarding_structure_instruction.py",
    '''        "7. A non-Node knowledge body may suggest the Node where it is most relevant, but the body itself remains outside the Node hierarchy. The later placement pass can map or route into it.",\n''',
    '''        "7. A non-Node knowledge body may suggest the Node where it is most relevant, but the body itself remains outside the Node hierarchy. The generated human structure review treats ordinary project Markdown as mutable by default and preselects authoritative/imported Markdown as fixed; the project owner can correct that policy before placement.",\n''',
)

# ---------------------------------------------------------------------------
# Placement proposal v1: future ownership, non-overlapping action semantics,
# and Overview as a first-class kind.
# ---------------------------------------------------------------------------
replace_once(
    "src/contextcanon/onboarding_placement.py",
    'PLACEMENT_PROPOSAL_SCHEMA = "contextcanon/onboarding-placement-proposal/v0"\n',
    'PLACEMENT_PROPOSAL_SCHEMA = "contextcanon/onboarding-placement-proposal/v1"\n',
)
replace_once(
    "src/contextcanon/onboarding_placement.py",
    '''PLACEMENT_KINDS = {\n    "rule",\n''',
    '''PLACEMENT_KINDS = {\n    "overview",\n    "rule",\n''',
)
replace_once(
    "src/contextcanon/onboarding_placement.py",
    'PLACEMENT_ACTIONS = {"keep", "move", "reference", "map"}\n',
    'PLACEMENT_ACTIONS = {"keep", "promote", "reference", "map"}\n',
)
replace_once(
    "src/contextcanon/onboarding_placement.py",
    '''    if kind in {"state", "plan"}:\n        _exact_keys(payload, {"text", "wording_origin"}, label)\n''',
    '''    if kind in {"overview", "state", "plan"}:\n        _exact_keys(payload, {"text", "wording_origin"}, label)\n''',
)
replace_once(
    "src/contextcanon/onboarding_placement.py",
    '''        if kind in {"rule", "topic-resource", "state", "plan", "authority-mapping"} and destination is None:\n            raise _error(f"items[{index}] kind {kind} requires destination_node_key")\n        if kind == "authority-mapping" and action != "map":\n            raise _error(f"items[{index}] authority-mapping must use action 'map'")\n        items.append(\n            PlacementItem(\n''',
    '''        if kind in {"overview", "rule", "topic-resource", "state", "plan", "authority-mapping"} and destination is None:\n            raise _error(f"items[{index}] kind {kind} requires destination_node_key")\n        allowed_actions = {\n            "overview": {"promote"},\n            "rule": {"promote"},\n            "topic-resource": {"reference"},\n            "ordinary-documentation": {"keep"},\n            "state": {"promote"},\n            "plan": {"promote"},\n            "authority-mapping": {"map"},\n            "unresolved": {"keep"},\n        }\n        if action not in allowed_actions[str(kind)]:\n            expected = ", ".join(sorted(allowed_actions[str(kind)]))\n            raise _error(f"items[{index}] kind {kind} must use action {expected}")\n        payload = _parse_payload(str(kind), raw_item["payload"], f"items[{index}].payload", snapshot)\n        if kind == "authority-mapping":\n            fixed = set(structure.fixed_markdown)\n            for path in payload["authority_paths"]:\n                if path not in fixed:\n                    raise _error(\n                        f"items[{index}] authority path {path!r} is not marked fixed in the accepted structure"\n                    )\n        items.append(\n            PlacementItem(\n''',
)
replace_once(
    "src/contextcanon/onboarding_placement.py",
    '''                evidence=_references(raw_item["evidence"], f"items[{index}].evidence", snapshot),\n                payload=_parse_payload(str(kind), raw_item["payload"], f"items[{index}].payload", snapshot),\n''',
    '''                evidence=_references(raw_item["evidence"], f"items[{index}].evidence", snapshot),\n                payload=payload,\n''',
)

# Placement instruction: ownership and document policy are explicit; reference
# cannot carry maintained copied meaning because only Topic/Resource uses it.
replace_once(
    "src/contextcanon/onboarding_placement_instruction.py",
    '''    lines.append("")\n    return lines\n\n\ndef _render_catalog''',
    '''    lines.append("")\n    lines.extend(["## Accepted Markdown document policy", ""])\n    if structure.fixed_markdown:\n        lines.append("Fixed Markdown — preserve its authority/wording; do not plan destructive cleanup:")\n        for path in structure.fixed_markdown:\n            lines.append(f"- `{path}`")\n    else:\n        lines.append("No proposed Markdown knowledge body is marked fixed.")\n    lines.extend(\n        [\n            "",\n            "Other project Markdown may be treated as mutable: ownership may move into ContextCanon and a later, separate cleanup may shorten/remove redundant prose after human review. Non-Markdown document authorities are unsupported in this placement version.",\n            "",\n        ]\n    )\n    return lines\n\n\ndef _render_catalog''',
)
replace_once(
    "src/contextcanon/onboarding_placement_instruction.py",
    '''        "This is the **second onboarding pass: place the books onto the already accepted shelves**. Read every frozen Evidence file, then identify durable pieces of project knowledge and propose where each one belongs. The structure is fixed for this pass.",\n''',
    '''        "This is the **second onboarding pass: place the books onto the already accepted shelves**. Read every frozen Evidence file, then decide where each durable piece of project knowledge should be **maintained in the future**, not merely where it happens to be written today. The accepted Node hierarchy and Markdown fixed/mutable policy are fixed inputs for this pass.",\n''',
)
replace_once(
    "src/contextcanon/onboarding_placement_instruction.py",
    '''        "3. The primary question is **where does this information live?**, not how can it be made more abstract. Do not beautify terminology merely because you can.",\n        "4. Use action `move` when project-owned canonical governance or state is currently buried in an accidental location and should become canonical at the destination Node. A later cleanup pass may replace the old duplicate text with a reference; do not perform that cleanup now.",\n        "5. Use action `reference` when a document/resource is already in a natural authoritative or task-oriented location and the destination Node should route to it rather than copy it.",\n        "6. Use action `keep` for ordinary documentation or unresolved information that should remain where it is and does not need canonical Node authoring merely to justify its existence.",\n        "7. Use action `map` only for `authority-mapping`: preserve the authoritative text and describe the relationship from project context to that authority rather than rewriting the authority as local truth.",\n''',
    '''        "3. The primary question is **where should this meaning be maintained from now on?** Minimize future redundancy. Do not preserve a poor current file boundary merely because the text happens to live there, and do not beautify terminology merely because you can.",\n        "4. Use kind `overview` plus action `promote` for short durable orientation about what one Node owns or is responsible for. Overview is stable local presentation, not temporary project `state` and not inherited governance.",\n        "5. Use action `promote` when project-owned canonical Overview, Rule, State, or Plan meaning should be maintained at the destination ContextCanon surface. Promotion does not delete the old prose now; a later cleanup preview may remove a true duplicate only for mutable Markdown.",\n        "6. Use action `reference` only for `topic-resource`: the referenced Markdown remains maintained at its natural location. The Node stores the routing condition/path, not a second maintained copy of the referenced prose.",\n        "7. Use action `keep` only for ordinary documentation or unresolved information that intentionally stays outside canonical Node authoring.",\n        "8. Use action `map` only for `authority-mapping`: the fixed Markdown remains authoritative, while the destination Node may state a clear local interpretation of what that authority means here. Do not rewrite the authority itself.",\n''',
)
replace_once(
    "src/contextcanon/onboarding_placement_instruction.py",
    '''        "8. Do not split or rename Nodes, add future architecture, or move a finding to a Node that does not exist in the supplied structure. If the structure is insufficient, return an `unresolved` item explaining the problem instead of redesigning it.",\n        "9. Treat README, CONTRIBUTING, architecture notes, implementation/configuration, CI, tests, security policy, state/planning text, and imported documentation according to their actual semantic role. Conventional files can be stale; prefer direct implementation/configuration/CI/test evidence for current behavior when it clearly conflicts with prose.",\n        "10. Preserve project state and planning findings explicitly. Do not let reviewed state/plan semantics disappear merely because they are not Rules.",\n        "11. Compare likely generic practices with every supplied reusable Source package before proposing a duplicate local Rule. A Source reuse is a separate proposal entry, bound to the exact immutable package; do not rewrite its inherited Rules locally.",\n        "12. A Source may be useful even when it is independent of other Sources. Do not infer Foundation or any other transitive dependency unless it is actually present in the supplied package semantics.",\n        "13. Use only frozen Evidence as evidence about this project. Do not use the live repository, web search, chat history, or model memory to fill project gaps.",\n        "14. Every placement item and Source reuse must cite exact Evidence path/hash/line ranges supporting the proposal.",\n        "15. Do not create, edit, move, or delete project files. Return a proposal only. ContextCanon will render an evidence-rich review before any canonical placement or cleanup is designed.",\n''',
    '''        "9. Do not split or rename Nodes, add future architecture, or place a finding at a Node that does not exist in the supplied structure. If the structure is insufficient, return an `unresolved` item explaining the problem instead of redesigning it.",\n        "10. Treat README as first-contact orientation/navigation rather than the default store for volatile state, future plan, detailed architecture, or every implementation invariant. Use `state` for current local situation, `plan` for future work, `overview` for stable Node responsibility, Rules for durable governance, and Topics/Resources for deeper task material.",\n        "11. Treat CONTRIBUTING, architecture notes, implementation/configuration, CI, tests, security policy, state/planning text, and imported documentation according to their actual semantic role. Conventional files can be stale; prefer direct implementation/configuration/CI/test evidence for current behavior when it clearly conflicts with prose.",\n        "12. Preserve project state, planning, important local development constraints, and unresolved contradictions explicitly. Before returning, check that the better structure did not silently drop high-value semantics visible elsewhere in the same frozen Evidence.",\n        "13. Compare likely generic practices with every supplied reusable Source package before proposing a duplicate local Rule. A Source reuse is a separate Evidence-derived proposal entry; project-specific deltas may still remain local.",\n        "14. A Source may be useful even when it is independent of other Sources. Do not infer Foundation or any other transitive dependency unless it is actually present in the supplied package semantics.",\n        "15. Use only frozen Evidence as evidence about this project. Do not use the live repository, web search, chat history, or model memory to fill project gaps. An explicit owner-selected Source, when supplied later by the human review workflow, is design input and is deliberately not something you must pretend to derive from Evidence.",\n        "16. Every placement item and Evidence-derived Source reuse must cite exact Evidence path/hash/line ranges supporting the proposal.",\n        "17. Do not create, edit, move, or delete project files. Return a proposal only. ContextCanon will render an evidence-rich review before any canonical placement or cleanup is designed.",\n''',
)
replace_once(
    "src/contextcanon/onboarding_placement_instruction.py",
    '''        '  "schema": "contextcanon/onboarding-placement-proposal/v0",',\n''',
    '''        '  "schema": "contextcanon/onboarding-placement-proposal/v1",',\n''',
)
replace_once(
    "src/contextcanon/onboarding_placement_instruction.py",
    '''        '`kind` is exactly one of `rule`, `topic-resource`, `ordinary-documentation`, `state`, `plan`, `authority-mapping`, `unresolved`. `action` is exactly one of `keep`, `move`, `reference`, `map`. `confidence` is exactly `high`, `medium`, or `low`.',\n''',
    '''        '`kind` is exactly one of `overview`, `rule`, `topic-resource`, `ordinary-documentation`, `state`, `plan`, `authority-mapping`, `unresolved`. `action` is exactly one of `keep`, `promote`, `reference`, `map`. `confidence` is exactly `high`, `medium`, or `low`.',\n''',
)
replace_once(
    "src/contextcanon/onboarding_placement_instruction.py",
    '''        "`destination_node_key` must be one key from the human-edited structure. It is required for `rule`, `topic-resource`, `state`, `plan`, and `authority-mapping`; it may be `null` for ordinary documentation or unresolved information that stays outside Node authoring.",\n''',
    '''        "`destination_node_key` must be one key from the human-edited structure. It is required for `overview`, `rule`, `topic-resource`, `state`, `plan`, and `authority-mapping`; it may be `null` for ordinary documentation or unresolved information that stays outside Node authoring.",\n''',
)
replace_once(
    "src/contextcanon/onboarding_placement_instruction.py",
    '''        '- `rule`: `{"statement": "...", "why": "...", "wording_origin": "exact|lightly-edited|synthesized"}`',\n''',
    '''        '- `overview`: `{"text": "...", "wording_origin": "exact|lightly-edited|synthesized"}` and action must be `promote`',\n        '- `rule`: `{"statement": "...", "why": "...", "wording_origin": "exact|lightly-edited|synthesized"}` and action must be `promote`',\n''',
)
replace_once(
    "src/contextcanon/onboarding_placement_instruction.py",
    '''        '- `topic-resource`: `{"condition": "...", "resource_paths": ["docs/file.md"]}`',\n        '- `ordinary-documentation`: `{"document_paths": ["README.md"], "reason": "..."}`',\n        '- `state`: `{"text": "...", "wording_origin": "exact|lightly-edited|synthesized"}`',\n        '- `plan`: `{"text": "...", "wording_origin": "exact|lightly-edited|synthesized"}`',\n''',
    '''        '- `topic-resource`: `{"condition": "...", "resource_paths": ["docs/file.md"]}` and action must be `reference`',\n        '- `ordinary-documentation`: `{"document_paths": ["README.md"], "reason": "..."}` and action must be `keep`',\n        '- `state`: `{"text": "...", "wording_origin": "exact|lightly-edited|synthesized"}` and action must be `promote`',\n        '- `plan`: `{"text": "...", "wording_origin": "exact|lightly-edited|synthesized"}` and action must be `promote`',\n''',
)
replace_once(
    "src/contextcanon/onboarding_placement_instruction.py",
    '''        '- `unresolved`: `{"question": "..."}`',\n''',
    '''        '- `unresolved`: `{"question": "..."}` and action must be `keep`',\n''',
)

# ---------------------------------------------------------------------------
# Focused tests: update existing contract expectations and add the concrete
# semantic boundaries discovered by the real AI Workstation placement.
# ---------------------------------------------------------------------------
replace_once(
    "tests/test_onboarding_placement.py",
    '"action": "move",\n',
    '"action": "promote",\n',
)
replace_once(
    "tests/test_onboarding_placement.py",
    'self.assertIn("action: `move`", review)\n',
    'self.assertIn("action: `promote`", review)\n',
)
replace_once(
    "tests/test_onboarding_placement.py",
    '''        self.assertIn("place the books onto the already accepted shelves", instruction.text)\n        self.assertIn("Do not redesign it in this pass", instruction.text)\n''',
    '''        self.assertIn("place the books onto the already accepted shelves", instruction.text)\n        self.assertIn("where each durable piece of project knowledge should be **maintained in the future**", instruction.text)\n        self.assertIn("README as first-contact orientation/navigation", instruction.text)\n        self.assertIn("Use action `reference` only for `topic-resource`", instruction.text)\n        self.assertIn("Do not redesign it in this pass", instruction.text)\n''',
)
# Add two focused tests before the CLI test.
replace_once(
    "tests/test_onboarding_placement.py",
    '''    def test_cli_writes_instruction_validates_and_renders_review_without_redirects(self):\n''',
    '''    def test_overview_is_distinct_from_state_and_rule_reference_is_rejected(self):\n        _, prepared, workspace, readme, architecture, source_root, package = self.make_case()\n        raw = self.placement_dict(prepared, workspace, readme, architecture, package)\n        raw["items"].insert(0, {\n            "id": "P-000",\n            "title": "Stable root responsibility",\n            "kind": "overview",\n            "action": "promote",\n            "destination_node_key": "N-001",\n            "rationale": "This is stable orientation, not temporary project state.",\n            "confidence": "high",\n            "evidence": [{"path": "README.md", "sha256": readme.sha256, "start_line": 1, "end_line": 1}],\n            "payload": {"text": "AI Workstation owns reproducible workstation setup.", "wording_origin": "synthesized"},\n        })\n        workspace.placement_proposal_path.write_text(json.dumps(raw), encoding="utf-8")\n        proposal = load_onboarding_placement_proposal(\n            workspace.placement_proposal_path, prepared.snapshot_root, workspace.structure_proposal_path,\n            workspace.structure_path, catalog_package_roots=[source_root],\n        )\n        self.assertEqual(proposal.items[0].kind, "overview")\n\n        raw["items"][1]["action"] = "reference"\n        workspace.placement_proposal_path.write_text(json.dumps(raw), encoding="utf-8")\n        with self.assertRaisesRegex(ContextCanonError, "kind rule must use action promote"):\n            load_onboarding_placement_proposal(\n                workspace.placement_proposal_path, prepared.snapshot_root, workspace.structure_proposal_path,\n                workspace.structure_path, catalog_package_roots=[source_root],\n            )\n\n    def test_cli_writes_instruction_validates_and_renders_review_without_redirects(self):\n''',
)

# Structure tests: the human-editable document-policy section is part of the
# accepted structure digest and can mark proposed Markdown fixed.
replace_once(
    "tests/test_onboarding_structure.py",
    '''        self.assertIn("## Proposal details", text)\n''',
    '''        self.assertIn("## Fixed Markdown", text)\n        self.assertIn("<!-- contextcanon-fixed-markdown:start -->", text)\n        self.assertIn("## Proposal details", text)\n''',
)
replace_once(
    "tests/test_onboarding_structure.py",
    '''        changed = load_structure_markdown(structure_path, proposal)\n\n        self.assertEqual(len(changed.nodes), 5)\n''',
    '''        edited = edited.replace(\n            "<!-- contextcanon-fixed-markdown:start -->\\n<!-- contextcanon-fixed-markdown:end -->",\n            "<!-- contextcanon-fixed-markdown:start -->\\n- `README.md`\\n<!-- contextcanon-fixed-markdown:end -->",\n        )\n        structure_path.write_text(edited, encoding="utf-8")\n        changed = load_structure_markdown(structure_path, proposal)\n\n        self.assertEqual(changed.fixed_markdown, ("README.md",))\n        self.assertEqual(len(changed.nodes), 5)\n''',
)
replace_once(
    "tests/test_onboarding_structure.py",
    '''        self.assertIn("authoritative-reference", first.text)\n''',
    '''        self.assertIn("authoritative-reference", first.text)\n        self.assertIn("Markdown knowledge-body paths only", first.text)\n        self.assertIn("Non-Markdown authorities such as PDF", first.text)\n''',
)

# Check off Block A implementation items in PLAN after focused tests succeed; the
# workflow that runs this script performs the tests before committing.
plan = Path("PLAN.md")
text = plan.read_text(encoding="utf-8")
for old in [
    "- [ ] Evolve the experimental placement contract from current-location sorting to future ownership:",
    "- [ ] Make the placement instruction explicitly minimize future redundancy, distinguish README/state/plan/architecture responsibilities, and forbid `reference` from becoming maintained text duplication.",
    "- [ ] Add Markdown document policy (`mutable` / `fixed`) to the structure discovery/review boundary and reject unsupported non-Markdown knowledge bodies in this v1 experiment instead of inventing conversion semantics.",
    "- [ ] Tell the semantic pass to preserve high-value Evidence findings across the two-pass split and surface unresolved contradictions rather than allowing a better hierarchy to become semantically poorer.",
    "- [ ] Cover the real `ai-workstation` patterns in focused regression tests:",
]:
    if old not in text:
        raise SystemExit(f"PLAN item missing: {old}")
    text = text.replace(old, old.replace("- [ ]", "- [x]", 1), 1)
plan.write_text(text, encoding="utf-8", newline="\n")
