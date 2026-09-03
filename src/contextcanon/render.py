from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re

from .model import CompiledNode, CompiledPackage, PackageDependency, Rule, SourceRef
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
    if compiled.parent_package is not None:
        parent_link = _accepted_package_link(compiled.parent_package)
        lines.extend([
            f"**Parent Context Node:** [{compiled.parent_package.metadata.name}]({parent_link}) — `{compiled.parent_package.metadata.version}`  ",
            f"**Accepted Parent package:** `{compiled.parent_package.package_digest}`",
            "",
        ])

    if compiled.imported_contexts:
        lines.extend(["**Resulting imported Contexts:**", ""])
        for dependency in compiled.imported_contexts:
            relation, link = _import_carrier(compiled, dependency)
            lines.append(
                f"- **{dependency.name}** — `{dependency.version}` — {relation} — "
                f"[inspect accepted carrier]({link})"
            )
        lines.append("")

    if compiled.parsed.overview:
        lines.extend(["## Local Overview", "", *compiled.parsed.overview.splitlines(), ""])
    if compiled.parsed.state:
        lines.extend(["## Local State", "", *compiled.parsed.state.splitlines(), ""])
    if compiled.parsed.plan:
        lines.extend(["## Local Plan", "", *compiled.parsed.plan.splitlines(), ""])

    effective_topics = [*compiled.inherited_topics, *compiled.local_topics]
    if compiled.inherited_rules or compiled.local_rules or effective_topics:
        lines.extend(["## How to use this context", ""])
        if compiled.inherited_rules or compiled.local_rules:
            lines.extend(["Apply all Rules below to every task in this Node.", ""])
        if effective_topics:
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
        lines.extend(["## Local Rules", ""])
        _append_rules(lines, compiled.local_rules)
    elif not compiled.inherited_rules:
        lines.extend(["This Node defines no Local Rules.", ""])

    if compiled.local_changes:
        lines.extend(["## Changes to inherited Rules", ""])
        for change in compiled.local_changes:
            action = "Removed" if change.kind == "remove" else "Overrode"
            lines.append(f"- **{action}** `{change.target_node_name} / {change.target_rule_id}` — {change.why}")
        lines.append("")

    seen_topic_origins: set[str] = set()
    for topic in compiled.inherited_topics:
        if topic.origin_node_id in seen_topic_origins:
            continue
        seen_topic_origins.add(topic.origin_node_id)
        topics = [candidate for candidate in compiled.inherited_topics if candidate.origin_node_id == topic.origin_node_id]
        lines.extend([f"## Topics from {topic.origin_node_name}", ""])
        _append_topics(lines, topics, compiled, repo_root)

    if compiled.local_topics:
        lines.extend(["## Local Topics", ""])
        _append_topics(lines, compiled.local_topics, compiled, repo_root)
    return "\n".join(lines).rstrip() + "\n"


def _accepted_package_link(package: CompiledPackage) -> str:
    return f".context/sources/{package.package_digest}/CONTEXT.md"


def _source_carrier_link(compiled: CompiledNode, ref: SourceRef, package: CompiledPackage) -> str:
    if ref.is_pinned:
        return _accepted_package_link(package)
    target = (compiled.parsed.root / ref.locator).resolve()
    if target.name != "CONTEXT.md":
        target = target / "CONTEXT.md"
    return os.path.relpath(target, compiled.parsed.root).replace(os.sep, "/")


def _import_carrier(compiled: CompiledNode, dependency: PackageDependency) -> tuple[str, str]:
    parent = compiled.parent_package
    if parent is not None:
        link = _accepted_package_link(parent)
        if dependency.id == parent.metadata.id:
            return "direct Parent Context Node", link
        if any(item.id == dependency.id for item in parent.imports):
            return f"via Parent Context Node **{parent.metadata.name}**", link

    for ref, package in zip(compiled.parsed.sources, compiled.source_packages):
        link = _source_carrier_link(compiled, ref, package)
        if dependency.id == package.metadata.id:
            return "direct Source", link
        if any(item.id == dependency.id for item in package.imports):
            return f"via Source **{package.metadata.name}**", link
    raise ContextCanonError(
        f"{compiled.metadata.name}: no direct accepted carrier found for imported Context {dependency.name}"
    )


def render_node_readme(compiled: CompiledNode) -> str:
    return (
        "<!-- contextcanon:generated-node-readme -->\n"
        f"# {compiled.metadata.name} — ContextCanon Node\n\n"
        "> [!NOTE]\n"
        "> **GENERATED ORIENTATION — DO NOT EDIT.**\n"
        "> ContextCanon creates this doorplate only when this Node directory has no project-owned `README.md`.\n\n"
        "Start with [**CONTEXT.md**](CONTEXT.md): it is the generated Official Context that actually applies in this Node, including inherited Contexts and their provenance.\n\n"
        "Edit [**CONTEXT.src.md**](CONTEXT.src.md) for this Node's local authored context. `Local` means authored here; inherited Rule overrides/removals are explicit separate Changes.\n\n"
        "ContextCanon project and documentation: https://github.com/SomeSunlight/context-canon\n"
    )


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


def _append_topics(lines: list[str], topics, compiled: CompiledNode, repo_root: Path) -> None:
    for topic in topics:
        lines.extend([f"### {topic.title}", "", topic.condition, ""])
        for intent in ("required", "optional"):
            targets = [target for target in topic.targets if target.intent == intent]
            if not targets:
                continue
            lines.extend([f"**{intent.title()}**", ""])
            for target in targets:
                lines.append(_render_target_line(compiled, topic, target, repo_root))
            lines.append("")


def _render_target_line(compiled: CompiledNode, topic, target, repo_root: Path) -> str:
    if target.kind == "resource":
        return f"- [`{target.locator}`]({target.locator})"
    if topic.origin_node_id == compiled.metadata.id:
        target_root = (compiled.parsed.root / target.locator).resolve()
        if target_root.name == "CONTEXT.md":
            target_root = target_root.parent
        rel = os.path.relpath(target_root / "CONTEXT.md", compiled.parsed.root).replace(os.sep, "/")
        target_node = parse_node(target_root, repo_root)
        return f"- [{target_node.metadata.name}]({rel})"
    name = target.target_node_name or "Context Node"
    node_id = target.target_node_id or target.locator
    return f"- **Context Node:** {name} (`{node_id}`) — inherited navigation target; not materialized into this package"


def _resource_namespace(node_id: str) -> str:
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", node_id):
        return node_id
    return "sha256-" + hashlib.sha256(node_id.encode("utf-8")).hexdigest()

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
        "# Accepted semantic Parent package. The locator is discovery metadata; build uses only the exact pin.",
    ]
    if compiled.parent_package is not None and compiled.parsed.parent is not None:
        lines.extend([
            "parent:",
            f"  id: {q(compiled.parent_package.metadata.id)}",
            f"  name: {q(compiled.parent_package.metadata.name)}",
            f"  version: {q(compiled.parent_package.metadata.version)}",
            f"  locator: {q(compiled.parsed.parent.locator)}",
            f"  normalized_digest: {q(compiled.parent_package.normalized_digest)}",
            f"  package_digest: {q(compiled.parent_package.package_digest)}",
        ])
    else:
        lines.append("parent: null")

    lines.extend(["", "# Accepted reusable Source packages used by this build. Both digests are exact pins."])
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

    lines.extend(["", "# Effective imported Context origins, flattened through accepted Parent/Source packages."])
    if compiled.imported_contexts:
        lines.append("imports:")
        for dependency in compiled.imported_contexts:
            lines.extend([
                f"  - id: {q(dependency.id)}",
                f"    name: {q(dependency.name)}",
                f"    version: {q(dependency.version)}",
                f"    normalized_digest: {q(dependency.normalized_digest)}",
                f"    package_digest: {q(dependency.package_digest)}",
            ])
    else:
        lines.append("imports: []")

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

    lines.extend(["", "# Compiled effective Rule/Topic view with provenance.", "official:"])
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
    effective_topics = [*compiled.inherited_topics, *compiled.local_topics]
    lines.append("  topic_ids: " + q([topic.id for topic in effective_topics]))
    lines.append("  resource_root: " + (q("CONTEXT/") if compiled.resources else "null"))

    lines.extend(["", "# Topic edges are explicit: kind is resource or context-node; intent is required or optional."])
    targets = [(topic, target) for topic in effective_topics for target in topic.targets]
    if targets:
        lines.append("targets:")
        for topic, target in targets:
            lines.extend([
                f"  - topic: {q(topic.id)}",
                f"    intent: {q(target.intent)}",
                f"    kind: {q(target.kind)}",
                f"    locator: {q(target.locator)}",
                f"    target_node_id: {q(target.target_node_id) if target.target_node_id else 'null'}",
                f"    target_node_name: {q(target.target_node_name) if target.target_node_name else 'null'}",
            ])
    else:
        lines.append("targets: []")

    lines.extend(["", "# Mapping from author-facing Resource paths to generated package paths."])
    published_resources = [path for path in compiled.resources if path != "CONTEXT/README.md"]
    if published_resources:
        lines.append("resources:")
        local_prefix = f"CONTEXT/references/{_resource_namespace(compiled.metadata.id)}/"
        for published in published_resources:
            source_rel = None
            if published.startswith(local_prefix):
                repo_rel = published[len(local_prefix):]
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
