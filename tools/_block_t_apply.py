from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def write(rel: str, text: str) -> None:
    (ROOT / rel).write_text(text, encoding="utf-8")


def replace_once(rel: str, old: str, new: str) -> None:
    text = read(rel)
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{rel}: expected exactly one replacement target, found {count}: {old[:120]!r}")
    write(rel, text.replace(old, new, 1))


def insert_before_once(rel: str, marker: str, insertion: str) -> None:
    text = read(rel)
    count = text.count(marker)
    if count != 1:
        raise SystemExit(f"{rel}: expected exactly one insertion marker, found {count}: {marker[:120]!r}")
    write(rel, text.replace(marker, insertion + marker, 1))


# ---------------------------------------------------------------------------
# Model/package provenance: every immutable package carries a verified flattened
# list of effective imported Context Nodes. This is presentation/audit metadata
# backed by normalized semantic identity; exact package digests remain in the
# package manifest and local accepted package store.
# ---------------------------------------------------------------------------
replace_once(
    "src/contextcanon/model.py",
    """    normalized_digest: str\n    package_digest: str\n    parent: PackageDependency | None = None\n""",
    """    normalized_digest: str\n    package_digest: str\n    imports: tuple[PackageDependency, ...] = ()\n    parent: PackageDependency | None = None\n""",
)
replace_once(
    "src/contextcanon/model.py",
    """    parent_package: CompiledPackage | None = None\n    source_packages: list[CompiledPackage] = field(default_factory=list)\n    inherited_rules: list[Rule] = field(default_factory=list)\n""",
    """    parent_package: CompiledPackage | None = None\n    source_packages: list[CompiledPackage] = field(default_factory=list)\n    imported_contexts: list[PackageDependency] = field(default_factory=list)\n    inherited_rules: list[Rule] = field(default_factory=list)\n""",
)

replace_once(
    "src/contextcanon/package.py",
    """    topics: Iterable[Topic],\n    parent: PackageDependency | None = None,\n) -> dict[str, Any]:\n""",
    """    topics: Iterable[Topic],\n    parent: PackageDependency | None = None,\n    imports: Iterable[PackageDependency] = (),\n) -> dict[str, Any]:\n""",
)
insert_before_once(
    "src/contextcanon/package.py",
    "    change_items = sorted(\n",
    """    import_items = sorted(\n        (\n            {\n                \"id\": dependency.id,\n                \"version\": dependency.version,\n                \"normalized_digest\": dependency.normalized_digest,\n            }\n            for dependency in imports\n        ),\n        key=lambda item: (item[\"id\"], item[\"version\"], item[\"normalized_digest\"]),\n    )\n""",
)
replace_once(
    "src/contextcanon/package.py",
    """        \"topics\": topic_items,\n    }\n    if parent is not None:\n""",
    """        \"topics\": topic_items,\n    }\n    # Keep old package/v0 digests valid when no imports exist. Once a Node\n    # composes context, the flattened import identities become authenticated\n    # semantic provenance rather than unauthenticated manifest decoration.\n    if import_items:\n        payload[\"imports\"] = import_items\n    if parent is not None:\n""",
)
replace_once(
    "src/contextcanon/package.py",
    """    topics: Iterable[Topic],\n    parent: PackageDependency | None = None,\n) -> str:\n    payload = semantic_payload(metadata, sources, changes, rules, removed_rules, topics, parent)\n""",
    """    topics: Iterable[Topic],\n    parent: PackageDependency | None = None,\n    imports: Iterable[PackageDependency] = (),\n) -> str:\n    payload = semantic_payload(metadata, sources, changes, rules, removed_rules, topics, parent, imports)\n""",
)
replace_once(
    "src/contextcanon/package.py",
    """        (*compiled.inherited_topics, *compiled.local_topics),\n        package_parent_dependency(compiled),\n    )\n""",
    """        (*compiled.inherited_topics, *compiled.local_topics),\n        package_parent_dependency(compiled),\n        compiled.imported_contexts,\n    )\n""",
)
replace_once(
    "src/contextcanon/package.py",
    """        package_digest=compiled.package_digest,\n        parent=package_parent_dependency(compiled),\n""",
    """        package_digest=compiled.package_digest,\n        imports=tuple(compiled.imported_contexts),\n        parent=package_parent_dependency(compiled),\n""",
)
replace_once(
    "src/contextcanon/package.py",
    """        \"parent\": asdict(package.parent) if package.parent is not None else None,\n        \"sources\": [asdict(source) for source in package.sources],\n        \"changes\": [asdict(change) for change in package.changes],\n""",
    """        \"parent\": asdict(package.parent) if package.parent is not None else None,\n        \"sources\": [asdict(source) for source in package.sources],\n        \"imports\": [asdict(dependency) for dependency in package.imports],\n        \"changes\": [asdict(change) for change in package.changes],\n""",
)
replace_once(
    "src/contextcanon/package.py",
    """    sources = tuple(_parse_dependency(item, index) for index, item in enumerate(_list(root.get(\"sources\"), \"sources\")))\n    _unique((source.id for source in sources), \"package Source Node ID\")\n""",
    """    sources = tuple(_parse_dependency(item, index) for index, item in enumerate(_list(root.get(\"sources\"), \"sources\")))\n    imports = tuple(\n        _parse_import_dependency(item, index)\n        for index, item in enumerate(_list(root.get(\"imports\", []), \"imports\"))\n    )\n    _unique((source.id for source in sources), \"package Source Node ID\")\n    _unique((dependency.id for dependency in imports), \"package imported Context Node ID\")\n""",
)
replace_once(
    "src/contextcanon/package.py",
    """    actual_normalized = semantic_digest(metadata, sources, changes, rules, removed_rules, topics, parent)\n""",
    """    actual_normalized = semantic_digest(metadata, sources, changes, rules, removed_rules, topics, parent, imports)\n""",
)
replace_once(
    "src/contextcanon/package.py",
    """        package_digest=expected_package_digest,\n        parent=parent,\n""",
    """        package_digest=expected_package_digest,\n        imports=tuple(imports),\n        parent=parent,\n""",
)
insert_before_once(
    "src/contextcanon/package.py",
    "\ndef _parse_change(value: Any, index: int) -> RuleChange:\n",
    """\ndef _parse_import_dependency(value: Any, index: int) -> PackageDependency:\n    item = _dict(value, f\"imports[{index}]\")\n    return PackageDependency(\n        _string(item.get(\"id\"), f\"imports[{index}].id\"),\n        _string(item.get(\"name\"), f\"imports[{index}].name\"),\n        _string(item.get(\"version\"), f\"imports[{index}].version\"),\n        _digest(item.get(\"normalized_digest\"), f\"imports[{index}].normalized_digest\"),\n        _digest(item.get(\"package_digest\"), f\"imports[{index}].package_digest\"),\n    )\n\n""",
)

replace_once(
    "src/contextcanon/compiler.py",
    "from .model import CompiledNode, CompiledPackage, ParentRef, Rule, RuleChange, RuleModification, RuleRemoval, SourceRef, Topic, TopicTarget\n",
    "from .model import CompiledNode, CompiledPackage, PackageDependency, ParentRef, Rule, RuleChange, RuleModification, RuleRemoval, SourceRef, Topic, TopicTarget\n",
)
replace_once(
    "src/contextcanon/compiler.py",
    """            compiled.inherited_rules, compiled.removed_rules = self._compose_inherited_rule_state(\n                composition_packages,\n                compiled.metadata.name,\n            )\n""",
    """            compiled.imported_contexts = self._compose_imported_contexts(\n                composition_packages,\n                compiled.metadata.id,\n                compiled.metadata.name,\n            )\n            compiled.inherited_rules, compiled.removed_rules = self._compose_inherited_rule_state(\n                composition_packages,\n                compiled.metadata.name,\n            )\n""",
)
insert_before_once(
    "src/contextcanon/compiler.py",
    "    def _compose_inherited_rule_state(\n",
    """    def _compose_imported_contexts(\n        self,\n        packages: list[CompiledPackage],\n        node_id: str,\n        node_name: str,\n    ) -> list[PackageDependency]:\n        \"\"\"Flatten exact effective Context origins in deterministic composition order.\n\n        A direct Parent/Source package already authenticates its own transitive\n        imports. Carrying those identities forward lets a deep leaf explain its\n        complete effective composition without dereferencing any live ancestor.\n        \"\"\"\n        result: list[PackageDependency] = []\n        seen: dict[str, PackageDependency] = {}\n        for package in packages:\n            dependency = PackageDependency(\n                package.metadata.id,\n                package.metadata.name,\n                package.metadata.version,\n                package.normalized_digest,\n                package.package_digest,\n            )\n            for candidate in (*package.imports, dependency):\n                if candidate.id == node_id:\n                    raise ContextCanonError(\n                        f\"{node_name}: imported Context chain loops back to the consuming Node {node_id}\"\n                    )\n                previous = seen.get(candidate.id)\n                if previous is not None:\n                    if previous != candidate:\n                        raise ContextCanonError(\n                            f\"{node_name}: imported Context {candidate.name} ({candidate.id}) arrives through \"\n                            \"multiple composition paths with different accepted package identity\"\n                        )\n                    continue\n                seen[candidate.id] = candidate\n                result.append(candidate)\n        return result\n\n""",
)

# ---------------------------------------------------------------------------
# Human source grammar: canonical local headings + Parent Context Node, while
# retaining legacy heading aliases so old published projects remain readable.
# ---------------------------------------------------------------------------
insert_before_once(
    "src/contextcanon/parser.py",
    "\ndef parse_node(\n",
    """\ndef _section_range(\n    sections: dict[str, tuple[int, int]],\n    source_path: Path,\n    canonical: str,\n    legacy: str | None = None,\n) -> tuple[int, int] | None:\n    names = (canonical,) if legacy is None else (canonical, legacy)\n    present = [(name, sections[name]) for name in names if name in sections]\n    if len(present) > 1:\n        joined = \" and \".join(f\"## {name}\" for name, _ in present)\n        raise ContextCanonError(\n            f\"{source_path}: ambiguous duplicate section aliases ({joined}); keep only ## {canonical}\"\n        )\n    return present[0][1] if present else None\n\n""",
)
replace_once(
    "src/contextcanon/parser.py",
    """    overview = _parse_overview(lines, sections.get(\"Overview\"))\n    state = _parse_overview(lines, sections.get(\"State\"))\n    plan = _parse_overview(lines, sections.get(\"Plan\"))\n    parent = _parse_parent(lines, sections.get(\"Parent\"), source_path)\n""",
    """    overview = _parse_overview(lines, _section_range(sections, source_path, \"Local Overview\", \"Overview\"))\n    state = _parse_overview(lines, _section_range(sections, source_path, \"Local State\", \"State\"))\n    plan = _parse_overview(lines, _section_range(sections, source_path, \"Local Plan\", \"Plan\"))\n    parent = _parse_parent(lines, _section_range(sections, source_path, \"Parent Context Node\", \"Parent\"), source_path)\n""",
)
replace_once(
    "src/contextcanon/parser.py",
    """    sources = _parse_sources(lines, sections.get(\"Sources\"), source_path)\n    rules = _parse_rules(lines, sections.get(\"Rules\"), source_path, metadata)\n    topics = _parse_topics(lines, sections.get(\"Topics\"), source_path, metadata)\n""",
    """    sources = _parse_sources(lines, sections.get(\"Sources\"), source_path)\n    rules = _parse_rules(lines, _section_range(sections, source_path, \"Local Rules\", \"Rules\"), source_path, metadata)\n    topics = _parse_topics(lines, _section_range(sections, source_path, \"Local Topics\", \"Topics\"), source_path, metadata)\n""",
)

replace_once(
    "src/contextcanon/authoring.py",
    """def _section_bounds(lines: list[str], name: str) -> tuple[int, int] | None:\n    heading = f\"## {name}\"\n    try:\n        heading_index = lines.index(heading)\n    except ValueError:\n        return None\n    end = len(lines)\n    for index in range(heading_index + 1, len(lines)):\n        if lines[index].startswith(\"## \"):\n            end = index\n            break\n    return heading_index, end\n""",
    """def _section_bounds(lines: list[str], *names: str) -> tuple[int, int] | None:\n    matches = [(name, lines.index(f\"## {name}\")) for name in names if f\"## {name}\" in lines]\n    if len(matches) > 1:\n        raise ContextCanonError(\n            \"Ambiguous local section aliases: \" + \", \".join(f\"## {name}\" for name, _ in matches)\n        )\n    if not matches:\n        return None\n    _, heading_index = matches[0]\n    end = len(lines)\n    for index in range(heading_index + 1, len(lines)):\n        if lines[index].startswith(\"## \"):\n            end = index\n            break\n    return heading_index, end\n""",
)
replace_once(
    "src/contextcanon/authoring.py",
    """    bounds = _section_bounds(lines, \"Rules\")\n    if bounds is None:\n        lines = _trim_insert(lines, len(lines), [\"## Rules\", \"\", f\"### {group}\", \"\"] + rule_block)\n""",
    """    bounds = _section_bounds(lines, \"Local Rules\", \"Rules\")\n    if bounds is None:\n        lines = _trim_insert(lines, len(lines), [\"## Local Rules\", \"\", f\"### {group}\", \"\"] + rule_block)\n""",
)
replace_once(
    "src/contextcanon/authoring.py",
    """    bounds = _section_bounds(lines, \"Topics\")\n    if bounds is None:\n        lines = _trim_insert(lines, len(lines), [\"## Topics\", \"\"] + block)\n""",
    """    bounds = _section_bounds(lines, \"Local Topics\", \"Topics\")\n    if bounds is None:\n        lines = _trim_insert(lines, len(lines), [\"## Local Topics\", \"\"] + block)\n""",
)

# ---------------------------------------------------------------------------
# Placement publication canonicalizes its managed authoring surface and moves
# Parent Context Node before all local semantic sections.
# ---------------------------------------------------------------------------
replace_once(
    "src/contextcanon/onboarding_placement_publish.py",
    """def _replace_managed_section(text: str, section: str, name: str, body: str) -> str:\n    text = _strip_managed_block(text, name)\n    if not body.strip():\n        return text.rstrip() + \"\\n\"\n    block = f\"{_MARKER_START[name]}\\n{body.rstrip()}\\n{_MARKER_END[name]}\"\n    heading_pattern = re.compile(rf\"(?m)^## {re.escape(section)}\\s*$\")\n    heading = heading_pattern.search(text)\n    if heading is None:\n        return text.rstrip() + f\"\\n\\n## {section}\\n\\n{block}\\n\"\n    next_heading = re.compile(r\"(?m)^## .+$\").search(text, heading.end())\n    insert_at = next_heading.start() if next_heading else len(text)\n    before = text[:insert_at].rstrip()\n    after = text[insert_at:].lstrip(\"\\n\")\n    result = before + \"\\n\\n\" + block + \"\\n\"\n    if after:\n        result += \"\\n\" + after\n    return result.rstrip() + \"\\n\"\n""",
    """def _replace_managed_section(\n    text: str,\n    section: str,\n    name: str,\n    body: str,\n    *,\n    aliases: tuple[str, ...] = (),\n) -> str:\n    text = _strip_managed_block(text, name)\n    candidates: list[tuple[str, re.Match[str]]] = []\n    for candidate in (section, *aliases):\n        match = re.search(rf\"(?m)^## {re.escape(candidate)}\\s*$\", text)\n        if match is not None:\n            candidates.append((candidate, match))\n    if len(candidates) > 1:\n        raise _error(\n            f\"CONTEXT.src.md contains both canonical and legacy headings for {section}: \"\n            + \", \".join(f\"## {candidate}\" for candidate, _ in candidates)\n        )\n    if candidates and candidates[0][0] != section:\n        _, match = candidates[0]\n        text = text[:match.start()] + f\"## {section}\" + text[match.end():]\n    if not body.strip():\n        return text.rstrip() + \"\\n\"\n    block = f\"{_MARKER_START[name]}\\n{body.rstrip()}\\n{_MARKER_END[name]}\"\n    heading = re.search(rf\"(?m)^## {re.escape(section)}\\s*$\", text)\n    if heading is None:\n        return text.rstrip() + f\"\\n\\n## {section}\\n\\n{block}\\n\"\n    next_heading = re.compile(r\"(?m)^## .+$\").search(text, heading.end())\n    insert_at = next_heading.start() if next_heading else len(text)\n    before = text[:insert_at].rstrip()\n    after = text[insert_at:].lstrip(\"\\n\")\n    result = before + \"\\n\\n\" + block + \"\\n\"\n    if after:\n        result += \"\\n\" + after\n    return result.rstrip() + \"\\n\"\n\n\ndef _replace_parent_section(text: str, body: str) -> str:\n    text = _strip_managed_block(text, \"parent\")\n    matches: list[re.Match[str]] = []\n    for heading in (\"Parent Context Node\", \"Parent\"):\n        match = re.search(rf\"(?m)^## {re.escape(heading)}\\s*$\", text)\n        if match is not None:\n            matches.append(match)\n    if len(matches) > 1:\n        raise _error(\"CONTEXT.src.md contains both ## Parent Context Node and legacy ## Parent\")\n    if matches:\n        heading = matches[0]\n        next_heading = re.compile(r\"(?m)^## .+$\").search(text, heading.end())\n        end = next_heading.start() if next_heading else len(text)\n        existing = text[heading.end():end].strip()\n        if existing and \"ctx:parent\" not in existing:\n            raise _error(\"Parent Context Node section contains unmanaged content; preserve it elsewhere before publication\")\n        text = (text[:heading.start()].rstrip() + \"\\n\\n\" + text[end:].lstrip(\"\\n\")).rstrip() + \"\\n\"\n    if not body.strip():\n        return text\n    block = f\"{_MARKER_START['parent']}\\n{body.rstrip()}\\n{_MARKER_END['parent']}\"\n    section = f\"## Parent Context Node\\n\\n{block}\\n\"\n    first_local = re.search(r\"(?m)^## .+$\", text)\n    insert_at = first_local.start() if first_local else len(text)\n    before = text[:insert_at].rstrip()\n    after = text[insert_at:].lstrip(\"\\n\")\n    result = before + \"\\n\\n\" + section\n    if after:\n        result += \"\\n\" + after\n    return result.rstrip() + \"\\n\"\n""",
)
replace_once(
    "src/contextcanon/onboarding_placement_publish.py",
    """    text = _replace_managed_section(text, \"Overview\", \"overview\", _render_overviews(overviews))\n    text = _replace_managed_section(text, \"State\", \"state\", _render_state(states))\n    text = _replace_managed_section(text, \"Plan\", \"plan\", _render_summaries(plans, \"plan\"))\n    text = _replace_managed_section(text, \"Sources\", \"sources\", _render_sources(sources, provenance_by_id))\n    text = _replace_managed_section(text, \"Rules\", \"rules\", _render_rules(rules))\n    text = _replace_managed_section(text, \"Topics\", \"topics\", _render_topics(topics, project_root, node_root))\n""",
    """    text = _replace_managed_section(text, \"Local Overview\", \"overview\", _render_overviews(overviews), aliases=(\"Overview\",))\n    text = _replace_managed_section(text, \"Local State\", \"state\", _render_state(states), aliases=(\"State\",))\n    text = _replace_managed_section(text, \"Local Plan\", \"plan\", _render_summaries(plans, \"plan\"), aliases=(\"Plan\",))\n    text = _replace_managed_section(text, \"Sources\", \"sources\", _render_sources(sources, provenance_by_id))\n    text = _replace_managed_section(text, \"Local Rules\", \"rules\", _render_rules(rules), aliases=(\"Rules\",))\n    text = _replace_managed_section(text, \"Local Topics\", \"topics\", _render_topics(topics, project_root, node_root), aliases=(\"Topics\",))\n""",
)
replace_once(
    "src/contextcanon/onboarding_placement_publish.py",
    """            source_overrides[root] = _replace_managed_section(\n                source_overrides[root], \"Parent\", \"parent\", \"\"\n            )\n""",
    """            source_overrides[root] = _replace_parent_section(source_overrides[root], \"\")\n""",
)
replace_once(
    "src/contextcanon/onboarding_placement_publish.py",
    """            source_overrides[root] = _replace_managed_section(\n                source_overrides[root], \"Parent\", \"parent\", body\n            )\n""",
    """            source_overrides[root] = _replace_parent_section(source_overrides[root], body)\n""",
)

replace_once(
    "src/contextcanon/onboarding_structure_materialize.py",
    '        "## Overview\\n\\n"\n',
    '        "## Local Overview\\n\\n"\n',
)

# Canonicalize ContextCanon's own authoring sources; generated copies are never
# touched as authoring truth.
heading_map = {
    "## Overview": "## Local Overview",
    "## State": "## Local State",
    "## Plan": "## Local Plan",
    "## Parent": "## Parent Context Node",
    "## Rules": "## Local Rules",
    "## Topics": "## Local Topics",
}
for source in ROOT.rglob("CONTEXT.src.md"):
    rel = source.relative_to(ROOT)
    if "CONTEXT" in rel.parts[:-1]:
        continue
    text = source.read_text(encoding="utf-8")
    lines = [heading_map.get(line, line) for line in text.splitlines()]
    source.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

# ---------------------------------------------------------------------------
# Official rendering: visible direct Parent, flattened effective composition,
# local-vs-inherited headings, and machine-readable imports.
# ---------------------------------------------------------------------------
replace_once(
    "src/contextcanon/render.py",
    "from .model import CompiledNode, Rule\n",
    "from .model import CompiledNode, CompiledPackage, PackageDependency, Rule, SourceRef\n",
)
replace_once(
    "src/contextcanon/render.py",
    """    if compiled.parent_package is not None:\n        lines.extend([\n            f\"**Parent:** {compiled.parent_package.metadata.name} (`{compiled.parent_package.metadata.id}`)  \",\n            f\"**Accepted Parent package:** `{compiled.parent_package.package_digest}`\",\n            \"\",\n        ])\n\n    if compiled.parsed.overview:\n        lines.extend([\"## Overview\", \"\", *compiled.parsed.overview.splitlines(), \"\"])\n    if compiled.parsed.state:\n        lines.extend([\"## State\", \"\", *compiled.parsed.state.splitlines(), \"\"])\n    if compiled.parsed.plan:\n        lines.extend([\"## Plan\", \"\", *compiled.parsed.plan.splitlines(), \"\"])\n""",
    """    if compiled.parent_package is not None:\n        parent_link = _accepted_package_link(compiled.parent_package)\n        lines.extend([\n            f\"**Parent Context Node:** [{compiled.parent_package.metadata.name}]({parent_link}) — `{compiled.parent_package.metadata.version}`  \",\n            f\"**Accepted Parent package:** `{compiled.parent_package.package_digest}`\",\n            \"\",\n        ])\n\n    if compiled.imported_contexts:\n        lines.extend([\"**Resulting imported Contexts:**\", \"\"])\n        for dependency in compiled.imported_contexts:\n            relation, link = _import_carrier(compiled, dependency)\n            lines.append(\n                f\"- **{dependency.name}** — `{dependency.version}` — {relation} — \"\n                f\"[inspect accepted carrier]({link})\"\n            )\n        lines.append(\"\")\n\n    if compiled.parsed.overview:\n        lines.extend([\"## Local Overview\", \"\", *compiled.parsed.overview.splitlines(), \"\"])\n    if compiled.parsed.state:\n        lines.extend([\"## Local State\", \"\", *compiled.parsed.state.splitlines(), \"\"])\n    if compiled.parsed.plan:\n        lines.extend([\"## Local Plan\", \"\", *compiled.parsed.plan.splitlines(), \"\"])\n""",
)
replace_once(
    "src/contextcanon/render.py",
    """    if compiled.local_rules:\n        lines.extend([\"## Local Rules\" if (compiled.parent_package or compiled.source_packages) else \"## Rules\", \"\"])\n        _append_rules(lines, compiled.local_rules)\n    elif not compiled.inherited_rules:\n        lines.extend([\"This Node defines no Rules.\", \"\"])\n""",
    """    if compiled.local_rules:\n        lines.extend([\"## Local Rules\", \"\"])\n        _append_rules(lines, compiled.local_rules)\n    elif not compiled.inherited_rules:\n        lines.extend([\"This Node defines no Local Rules.\", \"\"])\n""",
)
replace_once(
    "src/contextcanon/render.py",
    """    if compiled.local_topics:\n        lines.extend([\"## Local Topics\" if (compiled.parent_package or compiled.source_packages) else \"## Topics\", \"\"])\n        _append_topics(lines, compiled.local_topics, compiled, repo_root)\n    return \"\\n\".join(lines).rstrip() + \"\\n\"\n\ndef _append_rules""",
    """    if compiled.local_topics:\n        lines.extend([\"## Local Topics\", \"\"])\n        _append_topics(lines, compiled.local_topics, compiled, repo_root)\n    return \"\\n\".join(lines).rstrip() + \"\\n\"\n\n\ndef _accepted_package_link(package: CompiledPackage) -> str:\n    return f\".context/sources/{package.package_digest}/CONTEXT.md\"\n\n\ndef _source_carrier_link(compiled: CompiledNode, ref: SourceRef, package: CompiledPackage) -> str:\n    if ref.is_pinned:\n        return _accepted_package_link(package)\n    target = (compiled.parsed.root / ref.locator).resolve()\n    if target.name != \"CONTEXT.md\":\n        target = target / \"CONTEXT.md\"\n    return os.path.relpath(target, compiled.parsed.root).replace(os.sep, \"/\")\n\n\ndef _import_carrier(compiled: CompiledNode, dependency: PackageDependency) -> tuple[str, str]:\n    parent = compiled.parent_package\n    if parent is not None:\n        link = _accepted_package_link(parent)\n        if dependency.id == parent.metadata.id:\n            return \"direct Parent Context Node\", link\n        if any(item.id == dependency.id for item in parent.imports):\n            return f\"via Parent Context Node **{parent.metadata.name}**\", link\n\n    for ref, package in zip(compiled.parsed.sources, compiled.source_packages):\n        link = _source_carrier_link(compiled, ref, package)\n        if dependency.id == package.metadata.id:\n            return \"direct Source\", link\n        if any(item.id == dependency.id for item in package.imports):\n            return f\"via Source **{package.metadata.name}**\", link\n    raise ContextCanonError(\n        f\"{compiled.metadata.name}: no direct accepted carrier found for imported Context {dependency.name}\"\n    )\n\n\ndef render_node_readme(compiled: CompiledNode) -> str:\n    return (\n        \"<!-- contextcanon:generated-node-readme -->\\n\"\n        f\"# {compiled.metadata.name} — ContextCanon Node\\n\\n\"\n        \"> [!NOTE]\\n\"\n        \"> **GENERATED ORIENTATION — DO NOT EDIT.**\\n\"\n        \"> ContextCanon creates this doorplate only when this Node directory has no project-owned `README.md`.\\n\\n\"\n        \"Start with [**CONTEXT.md**](CONTEXT.md): it is the generated Official Context that actually applies in this Node, including inherited Contexts and their provenance.\\n\\n\"\n        \"Edit [**CONTEXT.src.md**](CONTEXT.src.md) for this Node's local authored context. `Local` means authored here; inherited Rule overrides/removals are explicit separate Changes.\\n\\n\"\n        \"ContextCanon project and documentation: https://github.com/SomeSunlight/context-canon\\n\"\n    )\n\n\ndef _append_rules""",
)

replace_once(
    "src/contextcanon/render.py",
    """    lines.extend([\"\", \"# Accepted reusable Source packages used by this build. Both digests are exact pins.\"])\n""",
    """    lines.extend([\"\", \"# Accepted reusable Source packages used by this build. Both digests are exact pins.\"])\n""",
)
# Insert effective import machine state immediately before local authoring state.
replace_once(
    "src/contextcanon/render.py",
    """    lines.extend([\"\", \"# Elements authored in this Node's CONTEXT.src.md.\", \"local:\"])\n""",
    """    lines.extend([\"\", \"# Effective imported Context origins, flattened through accepted Parent/Source packages.\"])\n    if compiled.imported_contexts:\n        lines.append(\"imports:\")\n        for dependency in compiled.imported_contexts:\n            lines.extend([\n                f\"  - id: {q(dependency.id)}\",\n                f\"    name: {q(dependency.name)}\",\n                f\"    version: {q(dependency.version)}\",\n                f\"    normalized_digest: {q(dependency.normalized_digest)}\",\n                f\"    package_digest: {q(dependency.package_digest)}\",\n            ])\n    else:\n        lines.append(\"imports: []\")\n\n    lines.extend([\"\", \"# Elements authored in this Node's CONTEXT.src.md.\", \"local:\"])\n""",
)

# ---------------------------------------------------------------------------
# Node README doorplate is a generated repository orientation artifact, not part
# of the immutable Context package. Existing/foreign README always wins.
# ---------------------------------------------------------------------------
replace_once(
    "src/contextcanon/outputs.py",
    "from .package import PACKAGE_MANIFEST_PATH\n",
    "from .package import PACKAGE_MANIFEST_PATH\nfrom .render import render_node_readme\n",
)
replace_once(
    "src/contextcanon/outputs.py",
    """    outputs.update({path: content for path, content in compiled.resources.items()})\n    outputs.update({path: content.encode(\"utf-8\") for path, content in compiled.adapters.items()})\n    return outputs\n""",
    """    outputs.update({path: content for path, content in compiled.resources.items()})\n    outputs.update({path: content.encode(\"utf-8\") for path, content in compiled.adapters.items()})\n    readme = compiled.parsed.root / \"README.md\"\n    manage_readme = not readme.exists()\n    if readme.is_file() and not readme.is_symlink():\n        try:\n            manage_readme = readme.read_text(encoding=\"utf-8\").startswith(\"<!-- contextcanon:generated-node-readme -->\\n\")\n        except (OSError, UnicodeDecodeError):\n            manage_readme = False\n    if manage_readme:\n        outputs[\"README.md\"] = render_node_readme(compiled).encode(\"utf-8\")\n    return outputs\n""",
)

# ---------------------------------------------------------------------------
# Documentation: canonical terminology, concise composition audit, doorplates,
# and the observed semantic-index side effect of the placement pass.
# ---------------------------------------------------------------------------
source_format = read("nodes/library/foundation/docs/source-format.md")
for old, new in (
    ("## Overview", "## Local Overview"),
    ("## Parent", "## Parent Context Node"),
    ("## Rules", "## Local Rules"),
    ("## Topics", "## Local Topics"),
):
    source_format = source_format.replace(old, new)
source_format = source_format.replace(
    "The format is deliberately constrained Markdown: readable without special tooling, but structured enough for deterministic parsing.\n",
    "The format is deliberately constrained Markdown: readable without special tooling, but structured enough for deterministic parsing. Canonical local sections are named `Local Overview`, `Local State`, `Local Plan`, `Local Rules`, and `Local Topics`; `Local` means authored in this Node, not an implicit override. The relationship heading is `Parent Context Node`. Compiler 0.5 continues to accept the older `Overview`/`State`/`Plan`/`Rules`/`Topics`/`Parent` headings as migration aliases, but a source must not contain both forms for the same section.\n",
)
source_format = source_format.replace(
    "`## Local Overview` is an optional short orientation block for the Node itself",
    "`## Local Overview` is an optional short orientation block for the Node itself",
)
source_format = source_format.replace(
    "`## Local Rules` contains the Node's local Rules.",
    "`## Local Rules` contains the Node's local Rules. The explicit label keeps authored-here Rules visually distinct from generated `Rules from …` sections; it does not mean those Rules override inherited identities.",
)
write("nodes/library/foundation/docs/source-format.md", source_format)

official = read("nodes/library/foundation/docs/official-context.md")
official = official.replace("## Overview: what is this place?", "## Local Overview: what is this place?")
official = official.replace("short local `Overview`", "short `Local Overview`")
official = official.replace("An Overview is deliberately", "A Local Overview is deliberately")
official = official.replace("the Overview", "the Local Overview")
official = official.replace("a concise Overview", "a concise Local Overview")
official = official.replace(
    "`.context/` is different. It contains compiler bookkeeping, accepted Source snapshots, provenance, hashes, package metadata, and other machine state. Humans normally do not need it to understand what applies.\n",
    "`.context/` is different. It contains compiler bookkeeping, accepted Source/Parent snapshots, provenance, hashes, package metadata, and other machine state. Humans normally do not browse it directly, but the compact composition summary at the top of `CONTEXT.md` links to the exact accepted local carrier packages when provenance needs inspection.\n",
)
official = official.replace(
    "## Why not put everything in `CONTEXT.md`?\n",
    "## Effective composition must be visible\n\nWhen a Node composes a Parent Context Node or reusable Sources, `CONTEXT.md` names the direct Parent and lists the resulting effective imported Context Nodes with their accepted versions. Transitive imports are flattened from authenticated immutable package metadata, so a deep Node can explain why a rule applies without dereferencing live ancestors or the network. Each list item links to the exact direct accepted carrier package (or the local development Source) that supplied that context. Unrelated sibling Nodes never appear merely because they share filesystem ancestry.\n\nThe list is deliberately compact provenance, not a second rule surface: the actual effective Rules and Topics remain grouped below by origin. Exact low-level machine state and digests remain available in `.context/context.yaml` and package manifests.\n\n## Why not put everything in `CONTEXT.md`?\n",
)
official = official.replace(
    "It should not expose normal readers to package digests, provenance event lists, dependency internals, or every resource in the package.",
    "It should expose only the small composition audit needed to understand what applies — imported Node names, accepted versions, relation/provenance, and local carrier links — rather than provenance event logs, dependency internals, or every resource in the package.",
)
official += """

## Node-directory README doorplate

A Context Node directory may have a project-owned `README.md`; ContextCanon never overwrites or adopts it. When no README exists, generated output may add a tiny marker-owned `README.md` doorplate so GitHub and filesystem browsers explain the special files immediately. It links to `CONTEXT.md` as Official Context, `CONTEXT.src.md` as local authoring truth, and the ContextCanon project documentation. It deliberately contains no duplicate project Rules, State, or other canonical meaning. If a project later replaces the generated doorplate with its own README (removing the ownership marker), ContextCanon stops managing that path.
"""
write("nodes/library/foundation/docs/official-context.md", official)

onboarding = read("docs/onboarding.md")
needle = "At this point **the shelves exist, but the books have not been distributed yet**.\n"
addition = needle + "\nA useful side effect appears during the later book-placement pass: forcing every maintained statement onto an explicit semantic shelf often surfaces responsibilities, boundaries, duplicates, and unresolved questions that were previously scattered through prose. Even before opening the detailed Evidence, the concise placement finding titles become a surprisingly useful project index. Treat that as review value, not as permission for the LLM to invent answers: unresolved questions remain explicit local State until the project resolves them.\n"
if needle not in onboarding:
    raise SystemExit("docs/onboarding.md: insertion anchor missing")
onboarding = onboarding.replace(needle, addition, 1)
write("docs/onboarding.md", onboarding)

# ---------------------------------------------------------------------------
# Focused regressions.
# ---------------------------------------------------------------------------
publication_test = r'''from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from contextcanon.compiler import Compiler
from contextcanon.outputs import check_outputs, write_outputs
from contextcanon.parser import ContextCanonError, parse_node


class PublicationReadabilityTests(unittest.TestCase):
    def _repo(self) -> Path:
        repo = Path(tempfile.mkdtemp())
        (repo / ".git").mkdir()
        return repo

    def test_canonical_local_headings_parse_and_legacy_aliases_remain_compatible(self):
        repo = self._repo()
        source = repo / "CONTEXT.src.md"
        source.write_text(
            """# Example — Local Context Source
<!-- ctx:node id="example" version="1.0.0" -->

## Local Overview

Local orientation.

## Local State

- Current state.

## Local Plan

- Future plan.

## Local Rules

### General

- **Stay local:** This rule is authored here.
  Why: The heading must not imply an override.
  <!-- ctx:rule id="RULE-1" -->

## Local Topics

### Details

When details matter:

Required:
- Resource: `detail.md`
<!-- ctx:topic id="TOPIC-1" -->
""",
            encoding="utf-8",
        )
        (repo / "detail.md").write_text("# Detail\n", encoding="utf-8")
        parsed = parse_node(repo, repo)
        self.assertEqual(parsed.overview, "Local orientation.")
        self.assertEqual(len(parsed.rules), 1)
        self.assertEqual(len(parsed.topics), 1)

        legacy = source.read_text(encoding="utf-8")
        for canonical, old in (
            ("## Local Overview", "## Overview"),
            ("## Local State", "## State"),
            ("## Local Plan", "## Plan"),
            ("## Local Rules", "## Rules"),
            ("## Local Topics", "## Topics"),
        ):
            legacy = legacy.replace(canonical, old)
        source.write_text(legacy, encoding="utf-8")
        self.assertEqual(parse_node(repo, repo).overview, "Local orientation.")

        source.write_text(legacy + "\n## Local Rules\n", encoding="utf-8")
        with self.assertRaisesRegex(ContextCanonError, "ambiguous duplicate section aliases"):
            parse_node(repo, repo)

    def test_generated_node_readme_is_owned_only_by_marker(self):
        repo = self._repo()
        (repo / "CONTEXT.src.md").write_text(
            """# Example — Local Context Source
<!-- ctx:node id="example" version="1.0.0" -->

## Local Overview

A small Node.
""",
            encoding="utf-8",
        )
        compiled = Compiler(repo).compile(repo)
        self.assertIn("missing README.md", check_outputs(compiled))
        write_outputs(compiled)
        readme = (repo / "README.md").read_text(encoding="utf-8")
        self.assertTrue(readme.startswith("<!-- contextcanon:generated-node-readme -->\n"))
        self.assertIn("CONTEXT.md", readme)
        self.assertIn("CONTEXT.src.md", readme)
        self.assertEqual(check_outputs(Compiler(repo).compile(repo)), [])

        foreign = "# Project-owned README\n\nKeep me.\n"
        (repo / "README.md").write_text(foreign, encoding="utf-8")
        compiled = Compiler(repo).compile(repo)
        self.assertNotIn("README.md", "\n".join(check_outputs(compiled)))
        write_outputs(compiled)
        self.assertEqual((repo / "README.md").read_text(encoding="utf-8"), foreign)

    def test_official_local_headings_are_explicit(self):
        repo = self._repo()
        (repo / "CONTEXT.src.md").write_text(
            """# Example — Local Context Source
<!-- ctx:node id="example" version="1.0.0" -->

## Local Overview

Orientation.

## Local State

- State.

## Local Plan

- Plan.

## Local Rules

### General

- **Rule:** Statement.
  Why: Rationale.
  <!-- ctx:rule id="RULE-1" -->
""",
            encoding="utf-8",
        )
        official = Compiler(repo).compile(repo).official_markdown
        self.assertIn("## Local Overview", official)
        self.assertIn("## Local State", official)
        self.assertIn("## Local Plan", official)
        self.assertIn("## Local Rules", official)
        self.assertNotIn("\n## Rules\n", official)


if __name__ == "__main__":
    unittest.main()
'''
write("tests/test_publication_readability.py", publication_test)

# Extend the existing end-to-end Parent chain proof with effective import
# metadata/version/audit-link assertions and offline stability.
replace_once(
    "tests/test_parent_chain.py",
    """        self.assertEqual(leaf_compiled.source_packages, [])\n        self.assertEqual(leaf_compiled.parent_package.metadata.id, \"node-subsystem\")\n\n        resources = leaf_compiled.resources\n""",
    """        self.assertEqual(leaf_compiled.source_packages, [])\n        self.assertEqual(leaf_compiled.parent_package.metadata.id, \"node-subsystem\")\n        self.assertEqual(\n            [(item.id, item.version) for item in leaf_compiled.imported_contexts],\n            [(\"node-workflow\", \"1.0.0\"), (\"node-project\", \"1.0.0\"), (\"node-subsystem\", \"1.0.0\")],\n        )\n        self.assertIn(\"**Parent Context Node:**\", leaf_compiled.official_markdown)\n        self.assertIn(\"**Resulting imported Contexts:**\", leaf_compiled.official_markdown)\n        self.assertIn(\"Development Workflow** — `1.0.0`\", leaf_compiled.official_markdown)\n        self.assertIn(\"AI Workstation** — `1.0.0`\", leaf_compiled.official_markdown)\n        self.assertIn(\"Llama Stack** — `1.0.0`\", leaf_compiled.official_markdown)\n        self.assertIn(\"via Parent Context Node **Llama Stack**\", leaf_compiled.official_markdown)\n        self.assertNotIn(\"Unrelated Sibling** —\", leaf_compiled.official_markdown)\n\n        resources = leaf_compiled.resources\n""",
)
replace_once(
    "tests/test_parent_chain.py",
    """        self.assertEqual(offline_leaf.resources, resources)\n""",
    """        self.assertEqual(offline_leaf.resources, resources)\n        self.assertEqual(offline_leaf.imported_contexts, leaf_compiled.imported_contexts)\n        self.assertIn(\"**Resulting imported Contexts:**\", offline_leaf.official_markdown)\n""",
)

# Update PLAN only on the successful candidate tree; if the workflow fails,
# none of these edits are committed/pushed.
plan = read("PLAN.md")
plan = plan.replace("**Status: ACTIVE — final pre-publication polish.**", "**Status: ACTIVE — implementation complete; owner readability acceptance pending.**")
for number in range(1, 7):
    plan = plan.replace(f"- [ ] {number}.", f"- [x] {number}.", 1)
plan = plan.replace(
    "- [ ] Document the observed onboarding effect that book placement itself surfaces previously hidden responsibilities, boundaries and unresolved questions; concise finding titles become a useful project index before the reader even opens the deeper material.",
    "- [x] Document the observed onboarding effect that book placement itself surfaces previously hidden responsibilities, boundaries and unresolved questions; concise finding titles become a useful project index before the reader even opens the deeper material.",
)
write("PLAN.md", plan)

state = read("STATE.md")
checkpoint = """

## Block T publication-readability candidate

The final pre-publication polish is implemented for owner acceptance. Canonical authoring now says `Parent Context Node` and `Local Overview` / `Local State` / `Local Plan` / `Local Rules` / `Local Topics`; the parser keeps the old headings as migration aliases but rejects mixed duplicate aliases. Placement publication moves the Parent Context Node relationship before local semantic sections.

Immutable packages now authenticate a flattened list of effective imported Context origins. A deep generated `CONTEXT.md` therefore shows the direct Parent plus every effective imported Context Node with accepted version, relation/provenance and an offline local carrier-package link, while existing Parent/Source pins remain non-live and sibling isolation is unchanged. Machine YAML and package manifests expose the same exact imported identities.

Node directories without a project-owned README receive a tiny marker-owned generated README doorplate linking Official Context, local authoring truth and the ContextCanon project. A foreign/project README is never overwritten or adopted. The doorplate is repository orientation only and is deliberately excluded from immutable package identity.

The remaining owner gate is a final readability inspection on the real `ai-workstation` root, Goose and Ansible. PR #13 remains draft/unmerged; the project owner will perform the final GitHub merge explicitly after the exact clean head passes its merge gate.
"""
if "## Block T publication-readability candidate" not in state:
    state = state.rstrip() + checkpoint + "\n"
write("STATE.md", state)
