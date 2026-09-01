from __future__ import annotations

import json
import os
from pathlib import Path

from .model import CompiledNode, Rule
from .parser import ContextCanonError, parse_node


def render_official(compiled: CompiledNode, repo_root: Path) -> str:
    lines: list[str] = [
        f"# {compiled.metadata.name} — Official Context",
        "",
        "> [!CAUTION]",
        "> **GENERATED FILE — DO NOT EDIT.**",
        "> This is the compact official entry for this Context Node.",
    ]
    if compiled.resources:
        lines.append("> Together with `CONTEXT/` it forms the human/agent-facing Official Context Package.")
    lines.extend([
        ">",
        "> Edit [CONTEXT.src.md](CONTEXT.src.md) instead.",
        "",
        f"**Node:** {compiled.metadata.name}  ",
        f"**Context version:** `{compiled.metadata.version}`",
        "",
    ])

    if compiled.parsed.overview:
        lines.extend(["## Overview", "", *compiled.parsed.overview.splitlines(), ""])

    if compiled.parsed.state:
        lines.extend(["## State", "", *compiled.parsed.state.splitlines(), ""])

    if compiled.parsed.plan:
        lines.extend(["## Plan", "", *compiled.parsed.plan.splitlines(), ""])

    if compiled.inherited_rules or compiled.local_rules or compiled.local_topics:
        lines.extend(["## How to use this context", ""])
        if compiled.inherited_rules or compiled.local_rules:
            lines.extend(["Apply all Rules below to every task in this Node.", ""])
        if compiled.local_topics:
            lines.extend([
                "For the current task, evaluate each Topic condition. When one matches, read every **Required** target before continuing; read **Optional** targets only when useful.",
                "",
            ])

    seen_origins: set[str] = set()
    for rule in compiled.inherited_rules:
        if rule.origin_node_id in seen_origins:
            continue
        seen_origins.add(rule.origin_node_id)
        rules = [candidate for candidate in compiled.inherited_rules if candidate.origin_node_id == rule.origin_node_id]
        lines.extend([f"## Rules from {rule.origin_node_name}", ""])
        _append_rules(lines, rules)

    if compiled.local_rules:
        lines.extend(["## Local Rules" if compiled.source_packages else "## Rules", ""])
        _append_rules(lines, compiled.local_rules)
    elif not compiled.inherited_rules:
        lines.extend(["This Node defines no Rules.", ""])

    if compiled.local_changes:
        lines.extend(["## Changes to inherited Rules", ""])
        for change in compiled.local_changes:
            action = "Removed" if change.kind == "remove" else "Overrode"
            lines.append(
                f"- **{action}** `{change.target_node_name} / {change.target_rule_id}` — {change.why}"
            )
        lines.append("")

    if compiled.local_topics:
        lines.extend(["## Topics", ""])
        for topic in compiled.local_topics:
            lines.extend([f"### {topic.title}", "", topic.condition, ""])
            for intent in ("required", "optional"):
                targets = [target for target in topic.targets if target.intent == intent]
                if not targets:
                    continue
                lines.extend([f"**{intent.title()}**", ""])
                for target in targets:
                    display, href = _render_target(compiled, target, repo_root)
                    lines.append(f"- [{display}]({href})")
                lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _append_rules(lines: list[str], rules: list[Rule]) -> None:
    current_group = None
    for rule in rules:
        if rule.group != current_group:
            lines.extend([f"### {rule.group}", ""])
            current_group = rule.group
        lines.extend([f"#### `{rule.id}` — {rule.title}", ""])
        if rule.modifications:
            latest = rule.modifications[-1]
            lines.extend([f"> **Override:** {latest.node_name} — {latest.why}", ""])
        lines.extend([rule.statement, ""])


def _render_target(compiled: CompiledNode, target, repo_root: Path) -> tuple[str, str]:
    if target.kind == "resource":
        source = (compiled.parsed.root / target.locator).resolve()
        rel = source.relative_to(repo_root).as_posix()
        published = f"CONTEXT/references/{rel}"
        return f"`{published}`", published
    target_root = (compiled.parsed.root / target.locator).resolve()
    if target_root.name == "CONTEXT.md":
        target_root = target_root.parent
    rel = os.path.relpath(target_root / "CONTEXT.md", compiled.parsed.root).replace(os.sep, "/")
    target_node = parse_node(target_root, repo_root)
    return target_node.metadata.name, rel


def render_adapters(compiled: CompiledNode) -> dict[str, str]:
    result: dict[str, str] = {}
    if "agents" in compiled.metadata.adapters:
        state_line = " Read [STATE.md](STATE.md) when current project state or planning matters." if (compiled.parsed.root / "STATE.md").exists() else ""
        result["AGENTS.md"] = (
            "# ContextCanon Agent Entry Point\n\n"
            "> **GENERATED FILE — DO NOT EDIT.**\n"
            "> Managed by ContextCanon.\n\n"
            "Read and follow [CONTEXT.md](CONTEXT.md) before answering, analyzing, or editing files. "
            "It defines the applicable Rules and Topic-loading instructions."
            f"{state_line}\n"
        )
    if "goose" in compiled.metadata.adapters:
        state_line = " Read STATE.md when current project state or planning matters." if (compiled.parsed.root / "STATE.md").exists() else ""
        result[".goosehints"] = (
            "# GENERATED FILE — DO NOT EDIT. Managed by ContextCanon.\n\n"
            "Read and follow CONTEXT.md before answering, analyzing, or editing files. "
            "It defines the applicable Rules and Topic-loading instructions."
            f"{state_line}\n"
        )
    unknown = set(compiled.metadata.adapters) - {"agents", "goose"}
    if unknown:
        raise ContextCanonError(f"Unsupported adapter(s): {', '.join(sorted(unknown))}")
    return result


def render_machine_yaml(compiled: CompiledNode, repo_root: Path, compiler_version: str) -> str:
    q = lambda value: json.dumps(value, ensure_ascii=False)
    lines = [
        f"# GENERATED ContextCanon machine state for {compiled.metadata.name}.",
        "# Humans normally read CONTEXT.src.md or CONTEXT.md instead.",
        "# This file is deterministic compiler output and must not be edited manually.",
        "",
        "schema: contextcanon/v0",
        f"compiler_version: {q(compiler_version)}",
        "",
        "# Stable logical Node identity. The filesystem path is deliberately not identity.",
        "node:",
        f"  id: {q(compiled.metadata.id)}",
        f"  name: {q(compiled.metadata.name)}",
        f"  version: {q(compiled.metadata.version)}",
        "",
        "# Accepted Source packages used by this build. Both digests are exact pins.",
    ]
    if compiled.source_packages:
        lines.append("sources:")
        for source_ref, source_package in zip(compiled.parsed.sources, compiled.source_packages):
            lines.extend([
                f"  - id: {q(source_package.metadata.id)}",
                f"    name: {q(source_package.metadata.name)}",
                f"    version: {q(source_package.metadata.version)}",
                f"    locator: {q(source_ref.locator)}",
                f"    normalized_digest: {q(source_package.normalized_digest)}",
                f"    package_digest: {q(source_package.package_digest)}",
            ])
    else:
        lines.append("sources: []")

    lines.extend(["", "# Elements authored in this Node's CONTEXT.src.md.", "local:"])
    lines.append("  state: " + (q(compiled.parsed.state) if compiled.parsed.state else "null"))
    lines.append("  plan: " + (q(compiled.parsed.plan) if compiled.parsed.plan else "null"))
    if compiled.local_rules:
        lines.append("  rules:")
        for rule in compiled.local_rules:
            lines.append("    - " + q({"id": rule.id, "title": rule.title, "group": rule.group}))
    else:
        lines.append("  rules: []")
    if compiled.local_changes:
        lines.append("  changes:")
        for change in compiled.local_changes:
            lines.append("    - " + q({
                "kind": change.kind,
                "target_node_id": change.target_node_id,
                "target_node_name": change.target_node_name,
                "target_rule_id": change.target_rule_id,
                "statement": change.statement,
                "why": change.why,
            }))
    else:
        lines.append("  changes: []")
    if compiled.local_topics:
        lines.append("  topics:")
        for topic in compiled.local_topics:
            lines.append("    - " + q({"id": topic.id, "title": topic.title}))
    else:
        lines.append("  topics: []")

    lines.extend(["", "# Compiled Rule view with provenance plus the local Topic index.", "official:"])
    all_rules = [*compiled.inherited_rules, *compiled.local_rules]
    if all_rules:
        lines.append("  rules:")
        local_identities = {(rule.origin_node_id, rule.id) for rule in compiled.local_rules}
        for rule in all_rules:
            lines.append("    - " + q({
                "id": rule.id,
                "title": rule.title,
                "origin_node_id": rule.origin_node_id,
                "origin_node_name": rule.origin_node_name,
                "local": (rule.origin_node_id, rule.id) in local_identities,
                "overrides": [
                    {
                        "node_id": modification.node_id,
                        "node_name": modification.node_name,
                        "why": modification.why,
                    }
                    for modification in rule.modifications
                ],
            }))
    else:
        lines.append("  rules: []")
    if compiled.removed_rules:
        lines.append("  removed_rules:")
        for removal in compiled.removed_rules:
            lines.append("    - " + q({
                "origin_node_id": removal.origin_node_id,
                "origin_node_name": removal.origin_node_name,
                "rule_id": removal.rule_id,
                "removed_by_node_id": removal.removed_by_node_id,
                "removed_by_node_name": removal.removed_by_node_name,
                "why": removal.why,
            }))
    else:
        lines.append("  removed_rules: []")
    lines.append("  topic_ids: " + q([topic.id for topic in compiled.local_topics]))
    lines.append("  resource_root: " + (q("CONTEXT/") if compiled.resources else "null"))

    lines.extend(["", "# Topic edges are explicit: kind is resource or context-node; intent is required or optional."])
    targets = [(topic, target) for topic in compiled.local_topics for target in topic.targets]
    if targets:
        lines.append("targets:")
        for topic, target in targets:
            lines.extend([
                f"  - topic: {q(topic.id)}",
                f"    intent: {q(target.intent)}",
                f"    kind: {q(target.kind)}",
                f"    locator: {q(target.locator)}",
            ])
    else:
        lines.append("targets: []")

    lines.extend(["", "# Mapping from author-facing Resource paths to generated package paths."])
    if compiled.resources:
        lines.append("resources:")
        for published in compiled.resources:
            repo_rel = published.removeprefix("CONTEXT/references/")
            source_abs = repo_root / repo_rel
            source_rel = os.path.relpath(source_abs, compiled.parsed.root).replace(os.sep, "/")
            lines.append("  - " + q({"source": source_rel, "published": published}))
    else:
        lines.append("resources: []")

    lines.extend([
        "",
        "# Exact deterministic identities. package_digest covers CONTEXT.md plus CONTEXT/ resources.",
        "package:",
        f"  normalized_digest: {q(compiled.normalized_digest)}",
        f"  package_digest: {q(compiled.package_digest)}",
    ])
    return "\n".join(lines) + "\n"
