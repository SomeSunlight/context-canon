from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .compiler import Compiler
from .model import CompiledPackage
from .onboarding import find_enclosing_context_root, project_root_from_snapshot, resolve_onboarding_scope
from .package import compiled_package
from .onboarding_instruction import MAX_INSTRUCTION_BYTES, _load_catalog, _render_evidence
from .onboarding_proposal import load_evidence_snapshot
from .onboarding_reusable_contexts import ReusableContextAssignment
from .onboarding_structure import HumanStructurePlan, load_onboarding_structure_proposal, load_structure_markdown
from .parser import ContextCanonError


PLACEMENT_INSTRUCTION_SCHEMA = "contextcanon/onboarding-placement-instruction/v2"


@dataclass(frozen=True)
class OnboardingPlacementInstruction:
    evidence_digest: str
    structure_digest: str
    catalog_packages: tuple[CompiledPackage, ...]
    enclosing_parent_package: CompiledPackage | None
    text: str
    instruction_digest: str


def _render_structure(structure: HumanStructurePlan) -> list[str]:
    by_key = {node.key: node for node in structure.nodes}
    depths: dict[str, int] = {}

    def depth(key: str) -> int:
        if key in depths:
            return depths[key]
        node = by_key[key]
        value = 0 if node.parent_key is None else depth(node.parent_key) + 1
        depths[key] = value
        return value

    lines = [
        "## Human-edited structure — this is the shelf map",
        "",
        f"Structure digest: `{structure.structure_digest}`",
        "",
        "The project owner has already reviewed and edited this hierarchy. **Do not redesign it in this pass.** Place knowledge into these Nodes or leave/reference it outside Node authoring as the output contract permits.",
        "",
    ]
    for node in structure.nodes:
        indent = "  " * depth(node.key)
        lifecycle = " [reserved]" if node.lifecycle == "reserved" else ""
        lines.append(f"{indent}- `{node.key}` — **{node.name}** (`{node.path}`){lifecycle}")
    lines.append("")
    lines.extend(["## Accepted Markdown document policy", ""])
    if structure.fixed_markdown:
        lines.append("Fixed Markdown — preserve its authority/wording; do not plan destructive cleanup:")
        for path in structure.fixed_markdown:
            lines.append(f"- `{path}`")
    else:
        lines.append("No proposed Markdown knowledge body is marked fixed.")
    lines.extend(
        [
            "",
            "Other project Markdown may be treated as mutable: when reviewed meaning is promoted into ContextCanon, this same placement pass may propose a concise replacement/orientation for the exact source range so the final repository does not keep two canonical copies. Structured textual bodies such as CSV/JSON/YAML are first-class Evidence/resources and may be referenced or mapped as technical authority, but they are not rewritten by `source_edits`.",
            "",
        ]
    )
    return lines


def _enclosing_parent_package(snapshot_root: Path) -> tuple[CompiledPackage, Path] | None:
    project = project_root_from_snapshot(snapshot_root)
    parent_root = find_enclosing_context_root(project)
    if parent_root is None:
        return None
    repository = resolve_onboarding_scope(project).repository_root
    return compiled_package(Compiler(repository).compile(parent_root)), parent_root


def _render_enclosing_parent_context(
    value: tuple[CompiledPackage, Path] | None,
    project_root: Path,
) -> list[str]:
    lines = ["## Enclosing Parent Context — already accepted", ""]
    if value is None:
        lines.extend([
            "This onboarding scope is not inside an existing ContextCanon Node.",
            "",
        ])
        return lines
    package, parent_root = value
    locator = Path(os.path.relpath(parent_root, project_root)).as_posix()
    lines.extend([
        f"The selected onboarding subtree lives inside **{package.metadata.name}**. Treat this as fixed inherited context for the subtree, not as project Evidence and not as a reusable Source suggestion.",
        f"- Parent locator: `{locator}`",
        f"- Node ID: `{package.metadata.id}`",
        f"- Version: `{package.metadata.version}`",
        f"- Normalized digest: `{package.normalized_digest}`",
        f"- Package digest: `{package.package_digest}`",
        "- Exact package files are available in the Semantic Handoff under `.contextcanon-handoff/enclosing-parent/`; inspect `CONTEXT.md` and relevant packaged Topic Resources when inherited detail matters.",
    ])
    if package.rules:
        lines.append("- Effective inherited Rules:")
        for rule in package.rules:
            lines.append(
                f"  - `{rule.origin_node_id}#{rule.id}` — **{rule.title}**: {rule.statement} Why: {rule.why}"
            )
    else:
        lines.append("- Effective inherited Rules: none")
    if package.topics:
        lines.append("- Effective inherited Topics:")
        for topic in package.topics:
            lines.append(f"  - `{topic.id}` — **{topic.title}**: {topic.condition}")
    else:
        lines.append("- Effective inherited Topics: none")
    lines.extend([
        "",
        "Do not recreate these inherited Rules or Topics locally merely because subtree Evidence repeats or depends on them. Add only the subtree-specific delta.",
        "",
    ])
    return lines


def _render_accepted_reusable_contexts(
    assignments: tuple[ReusableContextAssignment, ...],
) -> list[str]:
    lines = [
        "## Accepted reusable Context assignments — already decided",
        "",
    ]
    if not assignments:
        lines.extend([
            "No owner-selected reusable Context relationship applies in this onboarding.",
            "",
        ])
        return lines
    lines.extend([
        "The project owner already accepted these Context Import relationships in STEP 07. Treat both the package identity and the Parent/Reference relationship as fixed input for placement; this pass must not reclassify them.",
        "",
        "**Parent** is normative: its Rules apply at the target and its effective Context propagates through semantic Children. **Reference** is informational: its Rules do not apply and the relationship does not propagate. Do not treat a Reference as inherited governance.",
        "",
    ])
    for assignment in assignments:
        lines.extend([
            f"- `{assignment.target_node_key}` — **{assignment.target_name}** (`{assignment.target_path}`) ← **{assignment.source_name}** (`{assignment.source_version}`) [{assignment.relationship.title()}]",
            f"  Why: {assignment.why}",
            f"  Exact package: `{assignment.source_node_id}` · `{assignment.source_package_digest}`",
        ])
    lines.extend([
        "",
        "STEP 07 is the reusable-relationship human gate. Do not emit or invent an additional reusable relationship in this pass. Parent inheritance may suppress duplicate generic guidance in descendants; Reference does not.",
        "",
    ])
    return lines


def _render_catalog(packages: tuple[CompiledPackage, ...]) -> list[str]:
    lines = ["## Available reusable ContextCanon Source catalog", ""]
    if not packages:
        lines.extend(
            [
                "No reusable Source packages were supplied for this placement run.",
                "Return empty `source_edits` and `source_reuses` arrays when neither applies. Do not invent reusable Source identities.",
                "",
            ]
        )
        return lines
    lines.extend(
        [
            "These verified reusable packages were prepared before placement. Compare generic-looking project guidance with them before proposing a duplicate local Rule. Reusable Context assignment itself is a separate human gate; do not invent or re-decide owner-selected relationships in this LLM pass.",
            "",
        ]
    )
    for package in packages:
        lines.extend(
            [
                f"### {package.metadata.name}",
                "",
                f"- Node ID: `{package.metadata.id}`",
                f"- Version: `{package.metadata.version}`",
                f"- Normalized digest: `{package.normalized_digest}`",
                f"- Package digest: `{package.package_digest}`",
            ]
        )
        if package.rules:
            lines.append("- Effective Rules:")
            for rule in package.rules:
                lines.append(
                    f"  - `{rule.origin_node_id}#{rule.id}` — **{rule.title}**: {rule.statement} Why: {rule.why}"
                )
        else:
            lines.append("- Effective Rules: none")
        if package.topics:
            lines.append("- Published Topics:")
            for topic in package.topics:
                lines.append(f"  - `{topic.id}` — **{topic.title}**: {topic.condition}")
        else:
            lines.append("- Published Topics: none")
        lines.append("")
    return lines


def _render_contract(evidence_digest: str, structure_digest: str) -> list[str]:
    return [
        "## Required semantic work",
        "",
        "This is the **second onboarding pass: place the books onto the already accepted shelves**. Read every frozen Evidence file, then decide where each durable piece of project knowledge should be **maintained in the future**, not merely where it happens to be written today. The accepted Node hierarchy and Markdown fixed/mutable policy are fixed inputs for this pass.",
        "",
        "1. For meaning that moves into a Node, preserve the source's precise language whenever it is already clear. Facts, constraints and Rules should normally move with minimal wording change. Overview is a condensation task, but still use the project's ordinary vocabulary: prefer short concrete language over abstract academic/corporate phrases such as 'provides provisioning and operation' when the source simply says what the thing is and does. A stable Overview must not repeat volatile exact versions, compatibility numbers or current-phase details when those facts can be represented as State. If one source sentence mixes durable identity with volatile compatibility, split it into a short versionless Overview plus separate State finding(s). **Splitting is not permission to drop facts:** the State finding(s) must cite the original mixed source range as Evidence so any Source After edit can link the exact promoted destinations that carry those removed details.",
        "2. The primary question is **where should this meaning be maintained from now on?** Minimize future redundancy. Every durable meaning should have one canonical maintenance surface: promotion must leave a single canonical maintenance surface for that meaning. Do not preserve a poor current file boundary merely because the text happens to live there.",
        "3. Use kind `overview` plus action `promote` for short durable orientation about what one Node owns or is responsible for. One `overview`, `state`, or `plan` placement item becomes one bullet in the final Node: make each item one bullet-sized fact. When a source block is a list or matrix of independently readable facts, emit several short findings instead of compressing them into one comma/semicolon snake sentence. If one candidate sentence contains three or more independently maintainable claims, split it. Do not evade this by writing `includes A, B, C` or by joining several facts with semicolons. Consolidate only when one genuinely atomic sentence says the job better.",
        "4. Use action `promote` when project-owned canonical Overview, Rule, State, or Plan meaning belongs at the destination. Overview, Rule, State and Plan promotions are published into the destination Node's `CONTEXT.src.md`; Topic/Resource references are published there as routing. The Node authoring becomes the canonical maintenance surface for promoted meaning. State describes the current local situation and Plan describes future intended work; do not leave accepted State/Plan as migration follow-up.",
        "5. When promoted meaning came from mutable Markdown and leaving the original full prose would create duplicate maintenance, propose a `source_edits` entry in this same semantic pass. It names one exact frozen source range and the promoted item IDs that justify replacing it. The replacement is the useful A′ left behind after A moves into the Node. Treat A′ as **structure-preserving reduction, not generic prose summarization**: remove duplicated canonical detail while preserving the source shape that makes the remaining orientation easy to understand. If the source uses an informative table, normally leave a shorter/simpler table rather than flattening it into prose. If it explains an ordered process, keep an ordered list. If a diagram or ASCII structure communicates relationships better than prose, preserve or simplify that visual structure. If a concrete example materially makes an abstract concept intuitive, keep at least one representative example. Do not turn several independently readable claims into one comma/semicolon snake sentence; use short paragraphs, bullets, steps, or a compact table instead. Write a real plain-language gist of what the removed block said, then add the link/reference to the owning `CONTEXT.md`. When a replacement contains a repository-local Markdown link, keep the real repository path as the meaning but percent-encode the link destination as a URI path (for example, a space becomes `%20`) so valid filenames do not create renderer-dependent links. A reader should learn the gist without following the link. Pointer-only replacements such as 'The maintained details are in Project Context' are not acceptable when the old location still has first-contact, safety, architecture, contribution, or operating value. Keep only enough substance to orient the reader without recreating a second canonical copy. When meaning is unambiguous, rewrite freely for readability and a light human touch is welcome; when anything is uncertain, stay close to the original wording and do not invent. If no safe Source After edit is proposed or accepted, a temporary duplicate may exist during migration, but it remains migration debt. Do not create a source edit merely to change style.",
        "6. If several promoted findings jointly remove or reorganize one source passage, create **one shared source edit** linked to all of them. Never emit overlapping source edits for the same file. History such as CHANGELOG/patch records normally remains history, fixed Markdown remains untouched, and configuration/CI/manifests remain authoritative technical sources rather than targets for prose cleanup. Likewise, Markdown retained as a `topic-resource` remains its own maintenance surface and normally must not receive a Source After cleanup merely because one fact from it was promoted elsewhere.",
        "7. Use action `reference` only for `topic-resource`: the referenced resource remains maintained at its natural location. It may be Markdown or structured textual data such as CSV/JSON/YAML. The Node stores the routing condition/path, not a second maintained copy of the resource.",
        "8. Use action `keep` only for ordinary documentation that intentionally stays outside canonical Node authoring. An `unresolved` finding is different: it is a valuable open project question discovered by onboarding. Give it the most relevant destination Node and action `promote`; ContextCanon will carry it as a local open question in that Node's State. Do not answer the question merely to finish onboarding, and do not let investigation block the migration.",
        "9. Use action `map` only for `authority-mapping`. An authority path may be owner-accepted fixed Markdown or frozen non-Markdown technical Evidence such as a manifest/configuration file. Mutable Markdown does not become authoritative merely because the model says so: Markdown authority paths must already be marked fixed in the accepted structure. The destination Node may state a clear local interpretation of the authority, but do not rewrite the authority itself.",
        "10. Do not split or rename Nodes, add future architecture, or place a finding at a Node that does not exist in the supplied structure. If the structure is insufficient, return an `unresolved` item explaining the problem instead of redesigning it.",
        "11. Treat `README.md` as human/customer first-contact orientation and navigation rather than the default store for volatile state, future plan, detailed architecture, or every implementation invariant. Its durable project summary should be short and human-facing, but short does not mean prose-only: preserve a compact table, small diagram, list, or example when that is the clearest first-contact explanation. Exact supported versions/platforms normally belong in root `state` or a narrower Node. If the existing README identity line mixes the durable project idea with exact OS/runtime versions, normally keep a simpler versionless first-contact sentence in README and maintain the exact compatibility matrix as State. Use `state` for current local situation, `plan` for future work, `overview` for stable Node responsibility, Rules for durable governance, and Topics/Resources for genuinely useful deeper task material.",
        "12. Treat familiar filenames as role hints, not semantic authorities. `CONTRIBUTING.md` should primarily serve humans who want to contribute: motivation, coarse contribution areas, contribution process, and other genuinely contributor-facing orientation may remain there, while project-wide technical implementation rules and detailed specifications should normally move to the owning Context Nodes instead of remaining as a second canonical specification. Architecture notes, implementation/configuration, CI, tests, security policy, state/planning text, and imported documentation likewise follow their actual semantic role. In particular, do **not** keep `architecture.md` as a Topic/Resource merely because its filename says architecture: promote its durable responsibilities/invariants into the owning Nodes when that is the better maintenance surface. Harness-specific files such as `.goosehints`, `AGENTS.md`, `CLAUDE.md`, and similar files are adapter/projection surfaces, not semantic ownership boundaries: inspect them for project-wide meaning, promote harness-independent meaning into canonical Context Nodes, and retain only genuinely harness-specific mechanics or representation at the edge. Make such adapters as thin as the harness safely allows. A non-Markdown harness adapter is not rewritten by `source_edits`; classify/promote its general meaning correctly without inventing an unsupported rewrite. It is acceptable for a later reviewed cleanup to reduce a conventional document to a short orientation/reference or remove it when no independent procedural, explanatory, diagrammatic, or authority value remains. Conventional files can be stale; prefer direct implementation/configuration/CI/test evidence for current behavior when it clearly conflicts with prose.",
        "13. Preserve project state, planning, important local development constraints, and unresolved contradictions explicitly. A volatile version/value supported only by release history or other historical prose is not proven current merely because it is the newest historical mention: phrase it as `last documented ...` or emit an unresolved question when currentness matters. Before returning, check that the better structure did not silently drop high-value semantics visible elsewhere in the same frozen Evidence.",
        "14. Compare likely generic practices with every supplied reusable Context package and the accepted STEP-07 imports before proposing a duplicate local Rule. An accepted **Parent** at an ancestor is normative in semantic descendants; an accepted **Reference** is informational only at its direct target and must not suppress descendant Rules as inherited governance. Project-specific deltas may still remain local. STEP 07 is the only reusable-relationship gate in a new onboarding run, so do not propose additional reusable imports here.",
        "15. A Source may be useful even when it is independent of other Sources. Do not infer Foundation or any other transitive dependency unless it is actually present in the supplied package semantics.",
        "16. Use only frozen Evidence as evidence about this project. Do not use the live repository, web search, chat history, or model memory to fill project gaps. Explicit owner-selected Context Imports from STEP 07 are design input and are deliberately not something you must pretend to derive from Evidence.",
        "17. Every placement item must cite exact Evidence path/hash/line ranges supporting the proposal. Those exact excerpts are also the deterministic basis for a future duplicate-cleanup review: semantic cleanup may propose shorter orientation wording, but ContextCanon must never guess which original bytes were reviewed.",
        "18. Before returning, run two final audits. **Readability/redundancy:** every Overview/State/Plan item is one bullet-sized fact; stable Overview does not repeat volatile versions already represented as State; every Source After replacement at a still-useful human location carries a real gist plus its Context link rather than a pointer-only sentence; useful presentation structure has not been needlessly flattened (tables stay tabular when the matrix helps, ordered flows stay ordered, diagrams stay visual when that is clearer, and an explanatory example survives when it materially aids comprehension); no Source After replacement hides several independent claims inside a snake sentence; and every shared edit names all promoted findings whose meaning it summarizes. **Zero semantic loss per Source edit:** enumerate the substantive facts in that exact frozen `start_line..end_line`. Every fact removed from A must either still be present in A′ or be represented by one or more `linked_item_ids` whose Evidence cites the relevant removed source range. Do not rely on the same fact happening to occur elsewhere in another document or duplicate passage.",
        "19. Do not create, edit, move, or delete project files. Return a proposal only. ContextCanon will render an evidence-rich review before any canonical placement or cleanup is designed.",
        "",
        "## Output contract",
        "",
        "Return **only one valid JSON object**, with no Markdown fence and no prose before or after it. JSON strings must escape embedded double quotes as `\\\"`; never place a raw unescaped `\"` inside an already quoted JSON string.",
        "",
        "Top level exactly:",
        "",
        "```json",
        "{",
        '  "schema": "contextcanon/onboarding-placement-proposal/v2",',
        f'  "evidence_digest": "{evidence_digest}",',
        f'  "structure_digest": "{structure_digest}",',
        '  "items": [],',
        '  "source_edits": []',
        "}",
        "```",
        "",
        "Every `items` entry contains exactly:",
        "",
        "```json",
        "{",
        '  "id": "P-001",',
        '  "title": "Human-readable finding title",',
        '  "kind": "rule",',
        '  "action": "promote",',
        '  "destination_node_key": "N-001",',
        '  "rationale": "Why this information belongs here and why this action is appropriate",',
        '  "confidence": "high",',
        '  "evidence": [{"path": "README.md", "sha256": "...", "start_line": 1, "end_line": 3}],',
        '  "payload": {}',
        "}",
        "```",
        "",
        "`kind` is exactly one of `overview`, `rule`, `topic-resource`, `ordinary-documentation`, `state`, `plan`, `authority-mapping`, `unresolved`. `action` is exactly one of `keep`, `promote`, `reference`, `map`. `confidence` is exactly `high`, `medium`, or `low`.",
        "",
        "`destination_node_key` must be one key from the human-edited structure. It is required for `overview`, `rule`, `topic-resource`, `state`, `plan`, `authority-mapping`, and `unresolved`; it may be `null` only for ordinary documentation that stays outside Node authoring.",
        "",
        "Payloads are kind-specific and exact:",
        "",
        '- `overview`: `{"text": "...", "wording_origin": "exact|lightly-edited|synthesized"}` and action must be `promote`',
        '- `rule`: `{"statement": "...", "why": "...", "wording_origin": "exact|lightly-edited|synthesized"}` and action must be `promote`',
        '- `topic-resource`: `{"condition": "...", "resource_paths": ["docs/file.md"]}` and action must be `reference`',
        '- `ordinary-documentation`: `{"document_paths": ["README.md"], "reason": "..."}` and action must be `keep`',
        '- `state`: `{"text": "...", "wording_origin": "exact|lightly-edited|synthesized"}` and action must be `promote`',
        '- `plan`: `{"text": "...", "wording_origin": "exact|lightly-edited|synthesized"}` and action must be `promote`',
        '- `authority-mapping`: `{"authority_paths": ["pyproject.toml"], "mapping": "...", "wording_origin": "exact|lightly-edited|synthesized"}` and action must be `map`',
        '- `unresolved`: `{"question": "..."}` and action must be `promote`; give it the Node that should carry the open question until it is resolved',
        "",
        "All resource/document/authority paths must exist in the frozen Evidence for this v1 experiment. Markdown `authority_paths` must additionally be listed as fixed Markdown in the accepted structure; frozen non-Markdown technical authority paths may be mapped directly and are never source-edit targets.",
        "",
        "Every `source_edits` entry contains exactly:",
        "",
        "```json",
        "{",
        '  "id": "E-001",',
        '  "path": "README.md",',
        '  "sha256": "<exact frozen file hash>",',
        '  "start_line": 3,',
        '  "end_line": 8,',
        '  "linked_item_ids": ["P-001", "P-003"],',
        '  "replacement": "AI Workstation runs on Windows with WSL/Linux. Exact supported versions and current compatibility are maintained in [Project Context](CONTEXT.md).",',
        '  "rationale": "Why replacing this exact mutable-Markdown range removes duplicate maintenance without losing useful orientation",',
        '  "confidence": "high"',
        "}",
        "```",
        "",
        "`source_edits` is the proposed A → A′ side of promotion. Use only mutable `.md` Evidence that is not listed as fixed Markdown. Every **non-blank** edited line must be covered by Evidence cited by the linked promoted items; blank Markdown separator lines may sit inside one contiguous edit range without their own Evidence citation. Linked IDs must all be `promote` items and must not be `unresolved` findings, because an unanswered question cannot justify deleting uncertain source meaning. One source range may be linked to several findings, but source edits in one file must never overlap. `replacement` may be empty only when removing the range entirely is clearly better than leaving orientation. If no promoted mutable prose needs cleanup, return an empty array.",
        "",
        "Reusable Context relationships are not part of the STEP-08 output contract. They were already decided in STEP 07; preserve those accepted Parent/Reference semantics as fixed design input.",
        "",
    ]


def build_onboarding_placement_instruction(
    snapshot_root: Path,
    structure_proposal_path: Path,
    structure_path: Path,
    *,
    catalog_package_roots: Iterable[Path] = (),
    accepted_reusable_assignments: Iterable[ReusableContextAssignment] = (),
) -> OnboardingPlacementInstruction:
    snapshot = load_evidence_snapshot(snapshot_root)
    structure_proposal = load_onboarding_structure_proposal(structure_proposal_path, snapshot_root)
    structure = load_structure_markdown(structure_path, structure_proposal)
    packages = _load_catalog(catalog_package_roots)
    assignments = tuple(accepted_reusable_assignments)
    enclosing_parent = _enclosing_parent_package(snapshot_root)
    project_root = project_root_from_snapshot(snapshot_root)

    lines = [
        "# ContextCanon Onboarding Placement Instruction",
        "",
        f"Instruction schema: `{PLACEMENT_INSTRUCTION_SCHEMA}`",
        "",
        "ContextCanon has frozen the project evidence and the project owner has edited the coarse structure. You are the semantic reviewer for content placement only.",
        "",
    ]
    lines.extend(_render_evidence(snapshot))
    lines.extend(_render_structure(structure))
    lines.extend(_render_enclosing_parent_context(enclosing_parent, project_root))
    lines.extend(_render_accepted_reusable_contexts(assignments))
    lines.extend(_render_catalog(packages))
    lines.extend(_render_contract(snapshot.evidence_digest, structure.structure_digest))
    text = "\n".join(lines)
    encoded = text.encode("utf-8")
    if len(encoded) > MAX_INSTRUCTION_BYTES:
        raise ContextCanonError(
            "Onboarding placement instruction exceeds safety limit "
            f"of {MAX_INSTRUCTION_BYTES} bytes ({len(encoded)} bytes); narrow the Evidence or Source catalog"
        )
    return OnboardingPlacementInstruction(
        evidence_digest=snapshot.evidence_digest,
        structure_digest=structure.structure_digest,
        catalog_packages=packages,
        enclosing_parent_package=enclosing_parent[0] if enclosing_parent is not None else None,
        text=text,
        instruction_digest=hashlib.sha256(encoded).hexdigest(),
    )
