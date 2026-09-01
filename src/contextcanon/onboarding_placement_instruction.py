from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .model import CompiledPackage
from .onboarding_instruction import MAX_INSTRUCTION_BYTES, _load_catalog, _render_evidence
from .onboarding_proposal import load_evidence_snapshot
from .onboarding_structure import HumanStructurePlan, load_onboarding_structure_proposal, load_structure_markdown
from .parser import ContextCanonError


PLACEMENT_INSTRUCTION_SCHEMA = "contextcanon/onboarding-placement-instruction/v1"


@dataclass(frozen=True)
class OnboardingPlacementInstruction:
    evidence_digest: str
    structure_digest: str
    catalog_packages: tuple[CompiledPackage, ...]
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
            "Other project Markdown may be treated as mutable: when reviewed meaning is promoted into ContextCanon, this same placement pass may propose a concise replacement/orientation for the exact source range so the final repository does not keep two canonical copies. Non-Markdown document authorities are not rewritten by source edits.",
            "",
        ]
    )
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
            "Compare generic-looking project guidance with every verified immutable package below before proposing a duplicate local Rule. Use `source_reuses` only when one exact package materially covers evidence-backed guidance for one accepted Node. Copy the exact package identity.",
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
        "1. For meaning that moves into a Node, preserve the source's precise language whenever it is already clear. Facts, constraints and Rules should normally move with minimal wording change. Overview is a condensation task, but still use the project's ordinary vocabulary: prefer short concrete language over abstract academic/corporate phrases such as 'provides provisioning and operation' when the source simply says what the thing is and does.",
        "2. The primary question is **where should this meaning be maintained from now on?** Minimize future redundancy. Every durable meaning should have one canonical maintenance surface: promotion must leave a single canonical maintenance surface for that meaning. Do not preserve a poor current file boundary merely because the text happens to live there.",
        "3. Use kind `overview` plus action `promote` for short durable orientation about what one Node owns or is responsible for. Consolidate closely related overview statements for the same Node when one clean overview says the job better; split only independently maintainable responsibilities. Avoid semicolon/comma-heavy snake sentences.",
        "4. Use action `promote` when project-owned canonical Overview, Rule, State, or Plan meaning belongs at the destination. Overview, Rule, State and Plan promotions are published into the destination Node's `CONTEXT.src.md`; Topic/Resource references are published there as routing. The Node authoring becomes the canonical maintenance surface for promoted meaning. State describes the current local situation and Plan describes future intended work; do not leave accepted State/Plan as migration follow-up.",
        "5. When promoted meaning came from mutable Markdown and leaving the original full prose would create duplicate maintenance, propose a `source_edits` entry in this same semantic pass. It names one exact frozen source range and the promoted item IDs that justify replacing it. The replacement is **orientation, not a second canonical copy**: prefer concise human orientation plus a link/reference to the owning `CONTEXT.md` when that helps. When the meaning is unambiguous, rewrite freely for readability and a light human touch is welcome; when anything is uncertain, stay close to the original wording and do not invent. If no safe Source After edit is proposed or accepted, a temporary duplicate may exist during migration, but it remains migration debt. Do not plan to maintain the same full rule or explanation in both places. Do not create a source edit merely to change style.",
        "6. If several promoted findings jointly remove or reorganize one source passage, create **one shared source edit** linked to all of them. Never emit overlapping source edits for the same file. History such as CHANGELOG/patch records normally remains history, fixed Markdown remains untouched, and configuration/CI/manifests remain authoritative technical sources rather than targets for prose cleanup.",
        "7. Use action `reference` only for `topic-resource`: the referenced Markdown remains maintained at its natural location. The Node stores the routing condition/path, not a second maintained copy of the referenced prose.",
        "8. Use action `keep` only for ordinary documentation or unresolved information that intentionally stays outside canonical Node authoring.",
        "9. Use action `map` only for `authority-mapping`: the fixed Markdown remains authoritative, while the destination Node may state a clear local interpretation of what that authority means here. Do not rewrite the authority itself.",
        "10. Do not split or rename Nodes, add future architecture, or place a finding at a Node that does not exist in the supplied structure. If the structure is insufficient, return an `unresolved` item explaining the problem instead of redesigning it.",
        "11. Treat README as first-contact orientation/navigation rather than the default store for volatile state, future plan, detailed architecture, or every implementation invariant. Its durable project summary should be short and human-facing; exact supported versions/platforms normally belong in root `state` or a narrower Node. Use `state` for current local situation, `plan` for future work, `overview` for stable Node responsibility, Rules for durable governance, and Topics/Resources for genuinely useful deeper task material.",
        "12. Treat CONTRIBUTING, architecture notes, implementation/configuration, CI, tests, security policy, state/planning text, and imported documentation according to their actual semantic role. In particular, do **not** keep `architecture.md` as a Topic/Resource merely because its filename says architecture: promote its durable responsibilities/invariants into the owning Nodes when that is the better maintenance surface. It is acceptable for a later reviewed cleanup to reduce such a document to a short orientation/reference or remove it when no independent procedural, explanatory, diagrammatic, or authority value remains. Conventional files can be stale; prefer direct implementation/configuration/CI/test evidence for current behavior when it clearly conflicts with prose.",
        "13. Preserve project state, planning, important local development constraints, and unresolved contradictions explicitly. Before returning, check that the better structure did not silently drop high-value semantics visible elsewhere in the same frozen Evidence.",
        "14. Compare likely generic practices with every supplied reusable Source package before proposing a duplicate local Rule. A Source reuse is a separate Evidence-derived proposal entry; project-specific deltas may still remain local.",
        "15. A Source may be useful even when it is independent of other Sources. Do not infer Foundation or any other transitive dependency unless it is actually present in the supplied package semantics.",
        "16. Use only frozen Evidence as evidence about this project. Do not use the live repository, web search, chat history, or model memory to fill project gaps. An explicit owner-selected Source, when supplied later by the human review workflow, is design input and is deliberately not something you must pretend to derive from Evidence.",
        "17. Every placement item and Evidence-derived Source reuse must cite exact Evidence path/hash/line ranges supporting the proposal. Those exact excerpts are also the deterministic basis for a future duplicate-cleanup review: semantic cleanup may propose shorter orientation wording, but ContextCanon must never guess which original bytes were reviewed.",
        "18. Do not create, edit, move, or delete project files. Return a proposal only. ContextCanon will render an evidence-rich review before any canonical placement or cleanup is designed.",
        "",
        "## Output contract",
        "",
        "Return **only one JSON object**, with no Markdown fence and no prose before or after it.",
        "",
        "Top level exactly:",
        "",
        "```json",
        "{",
        '  "schema": "contextcanon/onboarding-placement-proposal/v1",',
        f'  "evidence_digest": "{evidence_digest}",',
        f'  "structure_digest": "{structure_digest}",',
        '  "items": [],',
        '  "source_edits": [],',
        '  "source_reuses": []',
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
        "`destination_node_key` must be one key from the human-edited structure. It is required for `overview`, `rule`, `topic-resource`, `state`, `plan`, and `authority-mapping`; it may be `null` for ordinary documentation or unresolved information that stays outside Node authoring.",
        "",
        "Payloads are kind-specific and exact:",
        "",
        '- `overview`: `{"text": "...", "wording_origin": "exact|lightly-edited|synthesized"}` and action must be `promote`',
        '- `rule`: `{"statement": "...", "why": "...", "wording_origin": "exact|lightly-edited|synthesized"}` and action must be `promote`',
        '- `topic-resource`: `{"condition": "...", "resource_paths": ["docs/file.md"]}` and action must be `reference`',
        '- `ordinary-documentation`: `{"document_paths": ["README.md"], "reason": "..."}` and action must be `keep`',
        '- `state`: `{"text": "...", "wording_origin": "exact|lightly-edited|synthesized"}` and action must be `promote`',
        '- `plan`: `{"text": "...", "wording_origin": "exact|lightly-edited|synthesized"}` and action must be `promote`',
        '- `authority-mapping`: `{"authority_paths": ["policy.md"], "mapping": "...", "wording_origin": "exact|lightly-edited|synthesized"}` and action must be `map`',
        '- `unresolved`: `{"question": "..."}` and action must be `keep`',
        "",
        "All resource/document/authority paths must exist in the frozen Evidence for this v1 experiment.",
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
        '  "replacement": "Short, plain first-contact orientation\n\nFor maintained detail, see [Project Context](CONTEXT.md).",',
        '  "rationale": "Why replacing this exact mutable-Markdown range removes duplicate maintenance without losing useful orientation",',
        '  "confidence": "high"',
        "}",
        "```",
        "",
        "`source_edits` is the proposed A → A′ side of promotion. Use only mutable `.md` Evidence that is not listed as fixed Markdown. Every edited line must be covered by Evidence cited by the linked promoted items; linked IDs must all be `promote` items. One source range may be linked to several findings, but source edits in one file must never overlap. `replacement` may be empty only when removing the range entirely is clearly better than leaving orientation. If no promoted mutable prose needs cleanup, return an empty array.",
        "",
        "Every `source_reuses` entry contains exactly:",
        "",
        "```json",
        "{",
        '  "id": "S-001",',
        '  "target_node_key": "N-001",',
        '  "source_node_id": "<exact catalog Node ID>",',
        '  "source_name": "<exact catalog name>",',
        '  "source_version": "<exact catalog version>",',
        '  "source_normalized_digest": "<exact catalog digest>",',
        '  "source_package_digest": "<exact catalog digest>",',
        '  "reason": "Why this package replaces duplicated local guidance at this Node",',
        '  "confidence": "high",',
        '  "evidence": [{"path": "CONTRIBUTING.md", "sha256": "...", "start_line": 1, "end_line": 5}]',
        "}",
        "```",
        "",
        "If no supplied Source package is a justified match, return an empty `source_reuses` array. Do not invent one.",
        "",
    ]


def build_onboarding_placement_instruction(
    snapshot_root: Path,
    structure_proposal_path: Path,
    structure_path: Path,
    *,
    catalog_package_roots: Iterable[Path] = (),
) -> OnboardingPlacementInstruction:
    snapshot = load_evidence_snapshot(snapshot_root)
    structure_proposal = load_onboarding_structure_proposal(structure_proposal_path, snapshot_root)
    structure = load_structure_markdown(structure_path, structure_proposal)
    packages = _load_catalog(catalog_package_roots)

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
        text=text,
        instruction_digest=hashlib.sha256(encoded).hexdigest(),
    )
