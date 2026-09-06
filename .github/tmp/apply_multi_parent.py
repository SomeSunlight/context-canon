from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    (ROOT / path).write_text(text, encoding="utf-8")


def exact(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one anchor, found {count}")
    return text.replace(old, new)


def between(text: str, start: str, end: str, replacement: str, label: str) -> str:
    a = text.find(start)
    if a < 0:
        raise RuntimeError(f"{label}: start anchor missing")
    b = text.find(end, a)
    if b < 0:
        raise RuntimeError(f"{label}: end anchor missing")
    return text[:a] + replacement.rstrip() + "\n\n" + text[b:]


# ---------------------------------------------------------------------------
# Core model: plural Parents with singleton compatibility accessors.
# ---------------------------------------------------------------------------
path = "src/contextcanon/model.py"
t = read(path)
t = exact(t, "    parent: ParentRef | None = None\n", "    parents: tuple[ParentRef, ...] = ()\n", "model ParsedNode parents")
t = exact(
    t,
    "    parent_package: CompiledPackage | None = None\n",
    "    parent_packages: list[CompiledPackage] = field(default_factory=list)\n",
    "model CompiledNode parents",
)
t = exact(t, "    parent: PackageDependency | None = None\n", "    parents: tuple[PackageDependency, ...] = ()\n", "model CompiledPackage parents")
# Inject compatibility properties before the next dataclass/class boundaries.
t = exact(
    t,
    "    plan: str = \"\"\n\n\n@dataclass\nclass CompiledNode:",
    "    plan: str = \"\"\n\n    @property\n    def parent(self) -> ParentRef | None:\n        if len(self.parents) > 1:\n            raise ValueError(\"Node has multiple semantic Parents; use .parents\")\n        return self.parents[0] if self.parents else None\n\n\n@dataclass\nclass CompiledNode:",
    "model ParsedNode compatibility",
)
t = exact(
    t,
    "    machine_yaml: str = \"\"\n\n\n@dataclass(frozen=True)\nclass PackageDependency:",
    "    machine_yaml: str = \"\"\n\n    @property\n    def parent_package(self) -> CompiledPackage | None:\n        if len(self.parent_packages) > 1:\n            raise ValueError(\"Node has multiple semantic Parents; use .parent_packages\")\n        return self.parent_packages[0] if self.parent_packages else None\n\n\n@dataclass(frozen=True)\nclass PackageDependency:",
    "model CompiledNode compatibility",
)
t = exact(
    t,
    "    parents: tuple[PackageDependency, ...] = ()\n",
    "    parents: tuple[PackageDependency, ...] = ()\n\n    @property\n    def parent(self) -> PackageDependency | None:\n        if len(self.parents) > 1:\n            raise ValueError(\"Package has multiple semantic Parents; use .parents\")\n        return self.parents[0] if self.parents else None\n",
    "model CompiledPackage compatibility",
)
write(path, t)


# ---------------------------------------------------------------------------
# Parser.
# ---------------------------------------------------------------------------
path = "src/contextcanon/parser.py"
t = read(path)
t = exact(
    t,
    '    parent = _parse_parent(lines, _section_range(sections, source_path, "Parent Context Node", "Parent"), source_path)\n    if parent is not None and parent.id == metadata.id:\n        raise ContextCanonError(f"{source_path}: Parent cannot be the Node itself")\n',
    '    parents = _parse_parents(lines, _section_range(sections, source_path, "Parent Context Node", "Parent"), source_path)\n    for parent in parents:\n        if parent.id == metadata.id:\n            raise ContextCanonError(f"{source_path}: Parent cannot be the Node itself")\n    _ensure_unique([parent.id for parent in parents], f"{source_path}: duplicate Parent Node ID")\n',
    "parser parse parents",
)
t = exact(t, "        parent=parent,\n", "        parents=tuple(parents),\n", "parser ParsedNode parents")
new_parent_parser = '''def _parse_parents(lines: list[str], section: tuple[int, int] | None, source_path: Path) -> list[ParentRef]:
    if not section:
        return []
    start, end = section
    entries: list[tuple[int, re.Match[str]]] = []
    for i in range(start, end):
        match = SOURCE_RE.match(lines[i])
        if match:
            entries.append((i, match))
    if not entries:
        raise ContextCanonError(f"{source_path}: Parent section must contain at least one Parent entry")

    result: list[ParentRef] = []
    for index, (i, match) in enumerate(entries):
        block_end = entries[index + 1][0] if index + 1 < len(entries) else end
        attrs = _find_ctx_attrs(lines, PARENT_COMMENT_RE, i + 1, block_end)
        if not attrs or not attrs.get("id") or not attrs.get("version"):
            raise ContextCanonError(f"{source_path}:{i+1}: Parent needs ctx:parent id/version metadata")
        if attrs["version"] != match.group("version"):
            raise ContextCanonError(f"{source_path}:{i+1}: Parent display version and ctx:parent version differ")

        normalized_digest = attrs.get("normalized-digest")
        package_digest = attrs.get("package-digest")
        if not normalized_digest or not package_digest:
            raise ContextCanonError(
                f"{source_path}:{i+1}: Parent must pin both normalized-digest and package-digest"
            )
        if not DIGEST_RE.fullmatch(normalized_digest):
            raise ContextCanonError(f"{source_path}:{i+1}: invalid Parent normalized-digest")
        if not DIGEST_RE.fullmatch(package_digest):
            raise ContextCanonError(f"{source_path}:{i+1}: invalid Parent package-digest")
        if {"transport", "ref", "node-path"}.intersection(attrs):
            raise ContextCanonError(
                f"{source_path}:{i+1}: Parent transport metadata is not supported yet; the locator is candidate-discovery metadata only"
            )
        result.append(
            ParentRef(
                id=attrs["id"],
                name=match.group("name"),
                version=attrs["version"],
                locator=match.group("path"),
                normalized_digest=normalized_digest,
                package_digest=package_digest,
            )
        )
    return sorted(result, key=lambda parent: (parent.id, parent.version, parent.normalized_digest, parent.package_digest))
'''
t = between(t, "def _parse_parent(", "def _parse_sources(", new_parent_parser, "parser parent function")
write(path, t)


# ---------------------------------------------------------------------------
# Compiler: all Parent packages enter the existing order-independent composer.
# ---------------------------------------------------------------------------
path = "src/contextcanon/compiler.py"
t = read(path)
t = exact(t, 'COMPILER_VERSION = "0.5.0"', 'COMPILER_VERSION = "0.6.0"', "compiler version")
old = '''            composition_packages: list[CompiledPackage] = []
            source_resource_sets: list[dict[str, bytes]] = []
            parent_id: str | None = None
            if parsed.parent is not None:
                parent_package, parent_resources = self._load_pinned_dependency(
                    node_root, parsed.parent, relation="Parent"
                )
                if parent_package.metadata.id == compiled.metadata.id:
                    raise ContextCanonError(f"{node_root}: Parent cannot be the Node itself")
                compiled.parent_package = parent_package
                composition_packages.append(parent_package)
                source_resource_sets.append(parent_resources)
                parent_id = parsed.parent.id

            seen_source_ids: set[str] = set()
            for source in parsed.sources:
                if parent_id is not None and source.id == parent_id:
                    raise ContextCanonError(
                        f"{node_root}: Node {source.id} cannot be both semantic Parent and ordinary Source"
                    )
'''
new = '''            composition_packages: list[CompiledPackage] = []
            source_resource_sets: list[dict[str, bytes]] = []
            parent_ids: set[str] = set()
            for parent in parsed.parents:
                parent_package, parent_resources = self._load_pinned_dependency(
                    node_root, parent, relation="Parent"
                )
                if parent_package.metadata.id == compiled.metadata.id:
                    raise ContextCanonError(f"{node_root}: Parent cannot be the Node itself")
                compiled.parent_packages.append(parent_package)
                composition_packages.append(parent_package)
                source_resource_sets.append(parent_resources)
                parent_ids.add(parent.id)

            seen_source_ids: set[str] = set()
            for source in parsed.sources:
                if source.id in parent_ids:
                    raise ContextCanonError(
                        f"{node_root}: Node {source.id} cannot be both semantic Parent and ordinary Source"
                    )
'''
t = exact(t, old, new, "compiler parent composition")
write(path, t)


# ---------------------------------------------------------------------------
# Package schema and normalized semantics. One-parent semantic digests remain
# compatible; multi-parent state is canonicalized without order/precedence.
# ---------------------------------------------------------------------------
path = "src/contextcanon/package.py"
t = read(path)
t = exact(
    t,
    'PACKAGE_SCHEMA = "contextcanon/package/v0"\nPACKAGE_MANIFEST_PATH',
    'PACKAGE_SCHEMA = "contextcanon/package/v1"\nLEGACY_PACKAGE_SCHEMA = "contextcanon/package/v0"\nPACKAGE_MANIFEST_PATH',
    "package schema",
)
new_parent_dependencies = '''def package_parent_dependencies(compiled: CompiledNode) -> tuple[PackageDependency, ...]:
    return tuple(
        sorted(
            (
                PackageDependency(
                    id=parent.metadata.id,
                    name=parent.metadata.name,
                    version=parent.metadata.version,
                    normalized_digest=parent.normalized_digest,
                    package_digest=parent.package_digest,
                )
                for parent in compiled.parent_packages
            ),
            key=lambda parent: (parent.id, parent.version, parent.normalized_digest, parent.package_digest),
        )
    )


def package_parent_dependency(compiled: CompiledNode) -> PackageDependency | None:
    parents = package_parent_dependencies(compiled)
    if len(parents) > 1:
        raise ValueError("Node has multiple semantic Parents; use package_parent_dependencies")
    return parents[0] if parents else None
'''
t = between(t, "def package_parent_dependency(", "def package_content_files(", new_parent_dependencies, "package parent dependencies")
new_semantic_payload = '''def semantic_payload(
    metadata: NodeMetadata,
    sources: Iterable[PackageDependency],
    changes: Iterable[RuleChange],
    rules: Iterable[Rule],
    removed_rules: Iterable[RuleRemoval],
    topics: Iterable[Topic],
    parent: PackageDependency | None = None,
    imports: Iterable[PackageDependency] = (),
    *,
    parents: Iterable[PackageDependency] = (),
) -> dict[str, Any]:
    """Return the canonical semantic payload used for normalized_digest."""

    parent_values = tuple(parents)
    if parent is not None:
        if parent_values:
            raise ValueError("Pass parent or parents, not both")
        parent_values = (parent,)
    parent_items = sorted(
        (
            {
                "id": item.id,
                "version": item.version,
                "normalized_digest": item.normalized_digest,
            }
            for item in parent_values
        ),
        key=lambda item: (item["id"], item["version"], item["normalized_digest"]),
    )
    source_items = sorted(
        (
            {
                "id": source.id,
                "version": source.version,
                "normalized_digest": source.normalized_digest,
            }
            for source in sources
        ),
        key=lambda item: (item["id"], item["version"], item["normalized_digest"]),
    )
    import_items = sorted(
        (
            {
                **{
                    "id": dependency.id,
                    "version": dependency.version,
                    "normalized_digest": dependency.normalized_digest,
                },
                **({"why": dependency.why} if dependency.why else {}),
            }
            for dependency in imports
        ),
        key=lambda item: (item["id"], item["version"], item["normalized_digest"]),
    )
    change_items = sorted(
        (asdict(change) for change in changes),
        key=lambda item: (item["target_node_id"], item["target_rule_id"], item["kind"]),
    )
    rule_items = sorted(
        (asdict(rule) for rule in rules),
        key=lambda item: (item["origin_node_id"], item["id"]),
    )
    removal_items = sorted(
        (asdict(removal) for removal in removed_rules),
        key=lambda item: (
            item["origin_node_id"],
            item["rule_id"],
            item["removed_by_node_id"],
            item["removed_by_node_name"],
            item["why"],
        ),
    )
    topic_items = [_topic_dict(topic) for topic in topics]
    topic_items.sort(key=lambda item: (item["origin_node_id"], item["id"]))

    payload: dict[str, Any] = {
        "node": {"id": metadata.id, "name": metadata.name, "version": metadata.version},
        "sources": source_items,
        "changes": change_items,
        "rules": rule_items,
        "removed_rules": removal_items,
        "topics": topic_items,
    }
    if import_items:
        payload["imports"] = import_items
    # Keep the normalized digest of the already-shipped zero/one-Parent model
    # stable. Only the genuinely new multi-Parent state needs a plural payload.
    if len(parent_items) == 1:
        payload["parent"] = parent_items[0]
    elif parent_items:
        payload["parents"] = parent_items
    return payload
'''
t = between(t, "def semantic_payload(", "def semantic_digest(", new_semantic_payload, "semantic payload")
new_semantic_digest = '''def semantic_digest(
    metadata: NodeMetadata,
    sources: Iterable[PackageDependency],
    changes: Iterable[RuleChange],
    rules: Iterable[Rule],
    removed_rules: Iterable[RuleRemoval],
    topics: Iterable[Topic],
    parent: PackageDependency | None = None,
    imports: Iterable[PackageDependency] = (),
    *,
    parents: Iterable[PackageDependency] = (),
) -> str:
    payload = semantic_payload(
        metadata, sources, changes, rules, removed_rules, topics, parent, imports, parents=parents
    )
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
'''
t = between(t, "def semantic_digest(", "def semantic_digest_for_node(", new_semantic_digest, "semantic digest")
t = exact(
    t,
    "        package_parent_dependency(compiled),\n        compiled.imported_contexts,\n",
    "        None,\n        compiled.imported_contexts,\n        parents=package_parent_dependencies(compiled),\n",
    "semantic digest for node",
)
t = exact(t, "        parent=package_parent_dependency(compiled),\n", "        parents=package_parent_dependencies(compiled),\n", "compiled package parents")
t = exact(
    t,
    '        "parent": asdict(package.parent) if package.parent is not None else None,\n',
    '        "parents": [asdict(parent) for parent in package.parents],\n',
    "package manifest parents",
)
t = exact(
    t,
    '    if root.get("schema") != PACKAGE_SCHEMA:\n        raise ContextCanonError(\n            f"Unsupported Context package schema in {manifest_path}: {root.get(\'schema\')!r}"\n        )\n',
    '    schema = root.get("schema")\n    if schema not in {PACKAGE_SCHEMA, LEGACY_PACKAGE_SCHEMA}:\n        raise ContextCanonError(\n            f"Unsupported Context package schema in {manifest_path}: {schema!r}"\n        )\n',
    "package loader schemas",
)
t = exact(
    t,
    '    parent_raw = root.get("parent")\n    parent = _parse_parent_dependency(parent_raw) if parent_raw is not None else None\n',
    '    if schema == LEGACY_PACKAGE_SCHEMA:\n        parent_raw = root.get("parent")\n        parents = (() if parent_raw is None else (_parse_parent_dependency(parent_raw, "parent"),))\n    else:\n        parents = tuple(\n            _parse_parent_dependency(item, f"parents[{index}]")\n            for index, item in enumerate(_list(root.get("parents", []), "parents"))\n        )\n    _unique((parent.id for parent in parents), "package Parent Node ID")\n',
    "package loader parents",
)
t = exact(
    t,
    '    if parent is not None and any(source.id == parent.id for source in sources):\n        raise ContextCanonError("Context package cannot use the same Node as Parent and ordinary Source")\n',
    '    parent_ids = {parent.id for parent in parents}\n    if any(source.id in parent_ids for source in sources):\n        raise ContextCanonError("Context package cannot use the same Node as Parent and ordinary Source")\n',
    "package overlap",
)
t = exact(
    t,
    '    actual_normalized = semantic_digest(metadata, sources, changes, rules, removed_rules, topics, parent, imports)\n',
    '    if schema == LEGACY_PACKAGE_SCHEMA:\n        legacy_parent = parents[0] if parents else None\n        actual_normalized = semantic_digest(metadata, sources, changes, rules, removed_rules, topics, legacy_parent, imports)\n    else:\n        actual_normalized = semantic_digest(metadata, sources, changes, rules, removed_rules, topics, None, imports, parents=parents)\n',
    "package normalized verify",
)
t = exact(t, "        parent=parent,\n", "        parents=tuple(sorted(parents, key=lambda parent: (parent.id, parent.version, parent.normalized_digest, parent.package_digest))),\n", "package load return parents")
new_parse_parent = '''def _parse_parent_dependency(value: Any, label: str = "parent") -> PackageDependency:
    item = _dict(value, label)
    return PackageDependency(
        _string(item.get("id"), f"{label}.id"),
        _string(item.get("name"), f"{label}.name"),
        _string(item.get("version"), f"{label}.version"),
        _digest(item.get("normalized_digest"), f"{label}.normalized_digest"),
        _digest(item.get("package_digest"), f"{label}.package_digest"),
    )
'''
t = between(t, "def _parse_parent_dependency(", "def _parse_dependency(", new_parse_parent, "package parse parent")
write(path, t)


# ---------------------------------------------------------------------------
# Diff snapshots.
# ---------------------------------------------------------------------------
path = "src/contextcanon/diff.py"
t = read(path)
new = '''def _parent_snapshot(compiled: CompiledNode) -> dict[str, dict[str, Any]]:
    return {
        parent.metadata.id: {
            "version": parent.metadata.version,
            "normalized_digest": parent.normalized_digest,
            "package_digest": parent.package_digest,
        }
        for parent in compiled.parent_packages
    }
'''
t = between(t, "def _parent_snapshot(", "def _source_snapshot(", new, "compiled parent diff")
write(path, t)

path = "src/contextcanon/package_diff.py"
t = read(path)
new = '''def _parent_snapshot(package: CompiledPackage) -> dict[str, dict[str, Any]]:
    return {
        parent.id: {
            "version": parent.version,
            "normalized_digest": parent.normalized_digest,
            "package_digest": parent.package_digest,
        }
        for parent in package.parents
    }
'''
t = between(t, "def _parent_snapshot(", "def _source_snapshot(", new, "package parent diff")
write(path, t)


# ---------------------------------------------------------------------------
# Rendering.
# ---------------------------------------------------------------------------
path = "src/contextcanon/render.py"
t = read(path)
old = '''    if compiled.parent_package is not None:
        parent_link = _accepted_package_link(compiled.parent_package)
        lines.extend([
            f"**Parent Context Node:** [{compiled.parent_package.metadata.name}]({parent_link}) — `{compiled.parent_package.metadata.version}`  ",
            f"**Accepted Parent package:** `{compiled.parent_package.package_digest}`",
            "",
        ])
'''
new = '''    if len(compiled.parent_packages) == 1:
        parent = compiled.parent_packages[0]
        parent_link = _accepted_package_link(parent)
        lines.extend([
            f"**Parent Context Node:** [{parent.metadata.name}]({parent_link}) — `{parent.metadata.version}`  ",
            f"**Accepted Parent package:** `{parent.package_digest}`",
            "",
        ])
    elif compiled.parent_packages:
        lines.extend(["**Parent Context Nodes:**", ""])
        for parent in compiled.parent_packages:
            parent_link = _accepted_package_link(parent)
            lines.append(
                f"- [{parent.metadata.name}]({parent_link}) — `{parent.metadata.version}` — package `{parent.package_digest}`"
            )
        lines.append("")
'''
t = exact(t, old, new, "official direct parents")
old_loop = '''        for dependency in compiled.imported_contexts:
            relation, link = _import_carrier(compiled, dependency)
            why = f" — Why: {dependency.why}" if dependency.why else ""
            lines.append(
                f"- **{dependency.name}** — `{dependency.version}` — {relation}{why} — "
                f"[inspect accepted carrier]({link})"
            )
'''
new_loop = '''        for dependency in compiled.imported_contexts:
            carriers = _import_carriers(compiled, dependency)
            why = f" — Why: {dependency.why}" if dependency.why else ""
            if len(carriers) == 1:
                relation, link = carriers[0]
                lines.append(
                    f"- **{dependency.name}** — `{dependency.version}` — {relation}{why} — "
                    f"[inspect accepted carrier]({link})"
                )
            else:
                rendered = "; ".join(f"{relation} [inspect]({link})" for relation, link in carriers)
                lines.append(f"- **{dependency.name}** — `{dependency.version}` — {rendered}{why}")
'''
t = exact(t, old_loop, new_loop, "official imported carriers")
new_carriers = '''def _import_carriers(compiled: CompiledNode, dependency: PackageDependency) -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    for parent in compiled.parent_packages:
        link = _accepted_package_link(parent)
        if dependency.id == parent.metadata.id:
            result.append(("direct Parent Context Node", link))
        elif any(item.id == dependency.id for item in parent.imports):
            result.append((f"via Parent Context Node **{parent.metadata.name}**", link))

    for ref, package in zip(compiled.parsed.sources, compiled.source_packages):
        link = _source_carrier_link(compiled, ref, package)
        if dependency.id == package.metadata.id:
            result.append(("direct Source", link))
        elif any(item.id == dependency.id for item in package.imports):
            result.append((f"via Source **{package.metadata.name}**", link))
    if not result:
        raise ContextCanonError(
            f"{compiled.metadata.name}: no direct accepted carrier found for imported Context {dependency.name}"
        )
    return result
'''
t = between(t, "def _import_carrier(", "def render_node_readme(", new_carriers, "import carriers")
old_yaml = '''        "# Accepted semantic Parent package. The locator is discovery metadata; build uses only the exact pin.",
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
'''
new_yaml = '''        "# Accepted semantic Parent packages. Locators are discovery metadata; build uses only exact pins.",
    ]
    if compiled.parent_packages:
        lines.append("parents:")
        for parent_ref, parent_package in zip(compiled.parsed.parents, compiled.parent_packages):
            lines.extend([
                f"  - id: {q(parent_package.metadata.id)}",
                f"    name: {q(parent_package.metadata.name)}",
                f"    version: {q(parent_package.metadata.version)}",
                f"    locator: {q(parent_ref.locator)}",
                f"    normalized_digest: {q(parent_package.normalized_digest)}",
                f"    package_digest: {q(parent_package.package_digest)}",
            ])
    else:
        lines.append("parents: []")
'''
t = exact(t, old_yaml, new_yaml, "machine parents")
write(path, t)


# ---------------------------------------------------------------------------
# Parent update UX and source composition validation.
# ---------------------------------------------------------------------------
path = "src/contextcanon/sources.py"
t = read(path)
t = exact(
    t,
    '    if parsed.parent is not None and parsed.parent.id == candidate.metadata.id:\n',
    '    if any(parent.id == candidate.metadata.id for parent in parsed.parents):\n',
    "source adoption parent overlap",
)
new_parent_workflow = '''def review_parent_candidate(node_root: Path, parent_id: str | None = None) -> tuple[ContextDiff, Path]:
    """Review one live semantic Parent as an immutable candidate."""

    node_root = node_root.resolve()
    repo_root = find_repo_root(node_root)
    compiler = Compiler(repo_root)
    compiled = compiler.compile(node_root)
    parent_index, parent_ref = _parent_index(compiled, parent_id)
    current = compiled.parent_packages[parent_index]

    parent_root = compiler._resolve_source_root(node_root, parent_ref.locator)
    live_parent = Compiler(repo_root).compile(parent_root)
    candidate = compiled_package(live_parent)
    if candidate.metadata.id != parent_ref.id:
        raise ContextCanonError(
            f"Live Parent Node ID {candidate.metadata.id} does not match accepted Parent {parent_ref.name} ({parent_ref.id})"
        )

    _validate_parent_candidate_composition(compiler, compiled, parent_index, candidate)
    candidate_root = _store_parent_candidate(node_root, live_parent)
    result = diff_packages(current, candidate)
    receipt = {
        "schema": PARENT_REVIEW_SCHEMA,
        "parent_id": parent_ref.id,
        "consumer_node_id": compiled.metadata.id,
        "source_file_sha256": _source_hash(node_root),
        "before": {
            "version": current.metadata.version,
            "normalized_digest": current.normalized_digest,
            "package_digest": current.package_digest,
        },
        "candidate": {
            "version": candidate.metadata.version,
            "normalized_digest": candidate.normalized_digest,
            "package_digest": candidate.package_digest,
        },
        "candidate_path": candidate_root.relative_to(node_root).as_posix(),
        "structural_validation": "passed",
        "diff": result.to_dict(),
    }
    path = _parent_review_path(node_root, parent_ref.id)
    path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write_text(path, json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    return result, path


def accept_parent_candidate(node_root: Path, parent_id: str | None = None) -> CompiledPackage:
    """Accept exactly the reviewed candidate for one semantic Parent."""

    node_root = node_root.resolve()
    compiler = Compiler(find_repo_root(node_root))
    compiled = compiler.compile(node_root)
    parent_index, parent_ref = _parent_index(compiled, parent_id)
    current = compiled.parent_packages[parent_index]
    receipt_path = _parent_review_path(node_root, parent_ref.id)
    if not receipt_path.is_file():
        raise ContextCanonError(
            f"Parent {parent_ref.id} has no review receipt; run 'contextcanon parent review {parent_ref.id}' first"
        )
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContextCanonError(f"Invalid Parent review receipt {receipt_path}: {exc}") from exc
    if not isinstance(receipt, dict) or receipt.get("schema") != PARENT_REVIEW_SCHEMA:
        raise ContextCanonError(f"Invalid Parent review receipt schema in {receipt_path}")
    if receipt.get("parent_id") != parent_ref.id:
        raise ContextCanonError("Parent review receipt belongs to a different Parent")
    if receipt.get("consumer_node_id") != compiled.metadata.id:
        raise ContextCanonError("Parent review receipt belongs to a different consumer Node")
    if receipt.get("source_file_sha256") != _source_hash(node_root):
        raise ContextCanonError("CONTEXT.src.md changed after Parent review; review the Parent candidate again")

    before = receipt.get("before")
    candidate_receipt = receipt.get("candidate")
    if not isinstance(before, dict) or not isinstance(candidate_receipt, dict):
        raise ContextCanonError(f"Invalid Parent review receipt state in {receipt_path}")
    if (
        before.get("version") != current.metadata.version
        or before.get("normalized_digest") != current.normalized_digest
        or before.get("package_digest") != current.package_digest
    ):
        raise ContextCanonError("Accepted Parent state changed after review; review the Parent candidate again")

    candidate_digest = candidate_receipt.get("package_digest")
    if not isinstance(candidate_digest, str):
        raise ContextCanonError(f"Invalid Parent candidate digest in {receipt_path}")
    candidate_root = node_root / ".context" / "parent-candidates" / candidate_digest
    candidate = load_package(candidate_root)
    if candidate.metadata.id != parent_ref.id:
        raise ContextCanonError("Reviewed Parent candidate belongs to a different Node")
    if (
        candidate_receipt.get("version") != candidate.metadata.version
        or candidate_receipt.get("normalized_digest") != candidate.normalized_digest
        or candidate_receipt.get("package_digest") != candidate.package_digest
    ):
        raise ContextCanonError("Parent candidate package differs from the reviewed candidate")
    if receipt.get("structural_validation") != "passed":
        raise ContextCanonError("Parent candidate review did not pass structural validation")

    _validate_parent_candidate_composition(compiler, compiled, parent_index, candidate)
    _install_package(node_root, candidate_root, candidate)
    _write_parent_pin(node_root, parent_ref.id, candidate)
    return candidate


def _parent_index(compiled: CompiledNode, parent_id: str | None) -> tuple[int, ParentRef]:
    if not compiled.parsed.parents:
        raise ContextCanonError(f"{compiled.metadata.name}: Node has no semantic Parent")
    if parent_id is None:
        if len(compiled.parsed.parents) != 1:
            ids = ", ".join(parent.id for parent in compiled.parsed.parents)
            raise ContextCanonError(
                f"{compiled.metadata.name}: Node has multiple semantic Parents ({ids}); specify the Parent Node ID"
            )
        return 0, compiled.parsed.parents[0]
    matches = [(index, parent) for index, parent in enumerate(compiled.parsed.parents) if parent.id == parent_id]
    if not matches:
        raise ContextCanonError(f"{compiled.metadata.name}: no semantic Parent with Node ID {parent_id}")
    return matches[0]
'''
t = between(t, "def review_parent_candidate(", "def _validate_parent_candidate_composition(", new_parent_workflow, "parent review workflow")
new_validate_parent = '''def _validate_parent_candidate_composition(
    compiler: Compiler,
    compiled: CompiledNode,
    parent_index: int,
    candidate: CompiledPackage,
) -> None:
    packages = [*compiled.parent_packages, *compiled.source_packages]
    packages[parent_index] = candidate
    inherited, removals = compiler._compose_inherited_rule_state(packages, compiled.metadata.name)
    inherited, removals = compiler._apply_rule_changes(
        inherited,
        removals,
        compiled.local_changes,
        compiled.metadata.id,
        compiled.metadata.name,
    )
    seen: dict[str, Rule] = {}
    for rule in (*inherited, *compiled.local_rules):
        previous = seen.get(rule.id)
        if previous is not None and previous.origin_node_id != rule.origin_node_id:
            raise ContextCanonError(
                f"Visible Rule ID collision in {compiled.metadata.name}: {rule.id} comes from multiple Nodes"
            )
        seen[rule.id] = rule
    inherited_topics = compiler._compose_inherited_topics(packages, compiled.metadata.name)
    compiler._validate_visible_topic_ids(inherited_topics, compiled.local_topics, compiled.metadata.name)
'''
t = between(t, "def _validate_parent_candidate_composition(", "def _store_parent_candidate(", new_validate_parent, "parent candidate composition")
new_review_path = '''def _parent_review_path(node_root: Path, parent_id: str) -> Path:
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", parent_id):
        token = parent_id
    else:
        token = "sha256-" + hashlib.sha256(parent_id.encode("utf-8")).hexdigest()
    return node_root / ".context" / "parent-reviews" / f"{token}.json"
'''
t = between(t, "def _parent_review_path(", "def _write_parent_pin(", new_review_path, "parent review path")
new_write_parent = '''def _write_parent_pin(node_root: Path, parent_id: str, candidate: CompiledPackage) -> None:
    path = node_root / "CONTEXT.src.md"
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    found = 0
    for index, line in enumerate(lines):
        visible = _SOURCE_LINE_RE.match(line)
        if not visible:
            continue
        search_end = min(index + 5, len(lines))
        for comment_index in range(index + 1, search_end):
            comment = _PARENT_COMMENT_RE.match(lines[comment_index])
            if not comment:
                continue
            attrs = _ATTR_RE.findall(comment.group("attrs"))
            if not attrs or dict(attrs).get("id") != parent_id:
                continue
            found += 1
            lines[index] = visible.group("prefix") + f"`{candidate.metadata.version}`" + visible.group("ending")
            updated: list[tuple[str, str]] = []
            seen_version = False
            for key, value in attrs:
                if key == "version":
                    updated.append((key, candidate.metadata.version))
                    seen_version = True
                elif key not in {"normalized-digest", "package-digest"}:
                    updated.append((key, value))
            if not seen_version:
                updated.append(("version", candidate.metadata.version))
            updated.extend([
                ("normalized-digest", candidate.normalized_digest),
                ("package-digest", candidate.package_digest),
            ])
            attrs_text = " ".join(f'{key}="{value}"' for key, value in updated)
            lines[comment_index] = f"{comment.group('indent')}<!-- ctx:parent {attrs_text} -->{comment.group('ending')}"
            break
    if found != 1:
        raise ContextCanonError(f"Could not find exactly one semantic Parent Node ID {parent_id} in {path}")
    _atomic_write_text(path, "".join(lines))
'''
t = between(t, "def _write_parent_pin(", "def install_source_package(", new_write_parent, "write parent pin")
t = exact(
    t,
    "    packages = ([compiled.parent_package] if compiled.parent_package is not None else []) + list(compiled.source_packages)\n    candidate_index = source_index + (1 if compiled.parent_package is not None else 0)\n",
    "    packages = [*compiled.parent_packages, *compiled.source_packages]\n    candidate_index = source_index + len(compiled.parent_packages)\n",
    "source candidate with parents",
)
write(path, t)


# ---------------------------------------------------------------------------
# CLI: Parent ID optional for singleton compatibility, required only when a
# Child actually has several Parents.
# ---------------------------------------------------------------------------
path = "src/contextcanon/cli.py"
t = read(path)
t = exact(
    t,
    '    parent_review = parent_sub.add_parser("review", help="compile the live Parent explicitly and review its immutable candidate snapshot")\n    parent_review.add_argument("--node", default=".", help="child Context Node root (default: current directory)")\n    parent_accept = parent_sub.add_parser("accept", help="accept exactly the most recently reviewed Parent snapshot")\n    parent_accept.add_argument("--node", default=".", help="child Context Node root (default: current directory)")\n',
    '    parent_review = parent_sub.add_parser("review", help="compile one live Parent explicitly and review its immutable candidate snapshot")\n    parent_review.add_argument("parent_id", nargs="?", help="Parent Node ID; optional when the Child has exactly one Parent")\n    parent_review.add_argument("--node", default=".", help="child Context Node root (default: current directory)")\n    parent_accept = parent_sub.add_parser("accept", help="accept exactly the reviewed snapshot for one Parent")\n    parent_accept.add_argument("parent_id", nargs="?", help="Parent Node ID; optional when the Child has exactly one Parent")\n    parent_accept.add_argument("--node", default=".", help="child Context Node root (default: current directory)")\n',
    "parent cli arguments",
)
t = exact(t, "                result, receipt = review_parent_candidate(node_root)\n", "                result, receipt = review_parent_candidate(node_root, args.parent_id)\n", "parent cli review")
t = exact(t, "            accepted = accept_parent_candidate(node_root)\n", "            accepted = accept_parent_candidate(node_root, args.parent_id)\n", "parent cli accept")
write(path, t)


# ---------------------------------------------------------------------------
# Foundation rules: short and always-readable.
# ---------------------------------------------------------------------------
path = "nodes/library/foundation/CONTEXT.src.md"
t = read(path)
t = exact(
    t,
    '### Composition\n\n- **No implicit Source precedence:** Context Sources are composed without implicit precedence; conflicts are resolved explicitly through local changes rather than Source order.\n  Why: Hidden first-source-wins behavior would make composed context difficult to reason about and unsafe to maintain.\n  <!-- ctx:rule id="CC-004" -->\n',
    '### Composition\n\n- **No implicit Source precedence:** Context Sources are composed without implicit precedence; conflicts are resolved explicitly through local changes rather than Source order.\n  Why: Hidden first-source-wins behavior would make composed context difficult to reason about and unsafe to maintain.\n  <!-- ctx:rule id="CC-004" -->\n\n- **Parents are unordered:** A Node may compose several semantic Parents. Parent order has no precedence; non-orthogonal conflicts must be resolved explicitly.\n  Why: Orthogonal context commonly meets at one Node; ordering must never hide a contradiction.\n  <!-- ctx:rule id="CC-013" -->\n',
    "Foundation parent rule",
)
t = exact(
    t,
    '### Repository conventions\n\n- **Keep familiar repository documents useful:**',
    '### Repository conventions\n\n- **Align Node roots with governed files:** Prefer Node roots that contain the files they primarily govern; keep the existing directory structure when it already fits.\n  Why: Humans and agents should encounter the applicable Context naturally from the files they change.\n  <!-- ctx:rule id="CC-012" -->\n\n- **Keep familiar repository documents useful:**',
    "Foundation layout rule",
)
write(path, t)


# ---------------------------------------------------------------------------
# Development Workflow rules.
# ---------------------------------------------------------------------------
path = "nodes/library/development-workflow/CONTEXT.src.md"
t = read(path)
t = exact(
    t,
    '### Recoverable planning\n\n- **Plan a coherent change block before editing:**',
    '### Recoverable planning\n\n- **Back every change with an Issue:** Before implementation, framework-context, or substantial documentation changes, ensure an Issue records why the change exists; it may be brief.\n  Why: Repository history should show the reason without reconstructing chat history.\n  <!-- ctx:rule id="CCW-010" -->\n\n- **Plan a coherent change block before editing:**',
    "workflow issue rule",
)
t = exact(
    t,
    '### Human review gate\n\n- **Do not merge without explicit project-owner approval:**',
    '### Human review gate\n\n- **Expand change scope explicitly:** Applicable Context constrains a task; it does not silently expand its writable scope.\n  Why: A local task must not acquire wider impact merely because broader Context was loaded.\n  <!-- ctx:rule id="CCW-011" -->\n\n- **Do not merge without explicit project-owner approval:**',
    "workflow scope rule",
)
write(path, t)


# ---------------------------------------------------------------------------
# Human docs: keep explanation just deep enough.
# ---------------------------------------------------------------------------
path = "nodes/library/development-workflow/docs/change-workflow.md"
t = read(path)
t = exact(
    t,
    'Before changing implementation, context structure, or substantial documentation:\n\n1. add a short subsection to the active area of `PLAN.md` (or the project\'s equivalent durable planning surface);\n2. state why the block exists;\n3. list concrete checkboxes that are small enough to show meaningful progress.\n',
    'Before changing implementation, context structure, or substantial documentation:\n\n1. ensure an Issue records why the change exists;\n2. add a short subsection to `PLAN.md` (or the equivalent) and reference the Issue;\n3. list concrete checkboxes that are small enough to show meaningful progress.\n\nThe planned scope is the writable scope. Reading inherited or shared Context does not add it; expand the plan explicitly before editing broader areas.\n',
    "change workflow opening",
)
write(path, t)

path = "nodes/library/foundation/docs/source-format.md"
t = read(path)
t = exact(
    t,
    'A Context Node may have **one semantic Parent**. Parent is an explicit accepted relationship, not a filesystem convention. A directory above the Node, or a Node whose path contains this Node, does not become Parent automatically.\n',
    'A Context Node may have zero, one, or several semantic Parents. Parents are explicit accepted relationships; filesystem nesting creates none. Parent order has no precedence.\n',
    "source format parent cardinality",
)
t = exact(
    t,
    'Parent is always an exact immutable package pin:\n',
    'Each Parent is an exact immutable package pin:\n',
    "source format parent pin",
)
t = exact(
    t,
    'Changing the Parent\'s live repository files therefore does not silently change the Child. The Child continues using its accepted Parent package until an explicit update is reviewed and accepted.\n',
    'Changing a Parent\'s live files does not silently change the Child. Each Parent advances only through explicit review and acceptance.\n',
    "source format parent update",
)
write(path, t)

path = "nodes/library/foundation/docs/composition.md"
t = read(path)
t = exact(
    t,
    'ContextCanon combines one optional explicit semantic Parent with any number of independent reusable Sources. Filesystem nesting never creates either relationship implicitly.\n',
    'ContextCanon combines zero or more explicit semantic Parents with any number of independent reusable Sources. Filesystem nesting creates neither relationship.\n',
    "composition opening",
)
t = exact(
    t,
    'A Node has at most one Parent. The relationship must be written explicitly in `CONTEXT.src.md`; repository directories are only locations and do not imply Parent/Child composition.\n',
    'A Node may have several Parents. Every relationship is explicit, and Parent order has no precedence. Repository directories remain locations only.\n\nParents should normally represent orthogonal context. The compiler catches structural conflicts for the same stable identity; broader natural-language contradictions remain a human review responsibility for now.\n',
    "composition semantic parent",
)
t = exact(
    t,
    'A semantic Parent chain is the normal way to work inside one project subtree without loading sibling context. Each accepted Parent package already contains its complete effective Rules, Topics and Topic Resources, including reusable Sources attached farther up the chain. A Child therefore needs only its direct accepted Parent package.\n',
    'Semantic Parent paths scope context without loading unrelated siblings. Each accepted Parent package already carries its complete effective Rules, Topics, Resources, and transitive imports.\n',
    "composition parent chains",
)
t = exact(
    t,
    'Compiler 0.5 supports one immutable semantic Parent, local unpinned Sources and immutable pinned external Sources. All become `CompiledPackage` before Rule/Topic composition, so the same transitive composition and conflict rules apply while Parent remains a distinct relationship role.\n',
    'Compiler 0.6 supports multiple immutable semantic Parents plus local and pinned Sources. All become `CompiledPackage` before composition, with no Parent or Source-order precedence.\n',
    "composition compiler contract",
)
t = exact(
    t,
    'This matters in repositories containing several Nodes: filesystem structure can organize them clearly without creating hidden context relationships.\n\nThe same principle applies to Git transport.',
    'This matters in repositories containing several Nodes: filesystem structure can organize them clearly without creating hidden context relationships. Prefer a Node root that contains the files it chiefly governs; when several semantic Parents apply, choose one clear physical home for navigation.\n\nThe same principle applies to Git transport.',
    "composition layout guidance",
)
write(path, t)

path = "nodes/library/foundation/docs/official-context.md"
t = read(path)
t = t.replace("a Parent Context Node or reusable Sources", "Parent Context Nodes or reusable Sources")
t = t.replace("names the direct Parent and lists", "names the direct Parents and lists")
write(path, t)


# ---------------------------------------------------------------------------
# Structure onboarding: filesystem is a strong prior, not semantic authority.
# ---------------------------------------------------------------------------
path = "src/contextcanon/onboarding_structure_instruction.py"
t = read(path)
t = exact(
    t,
    '        "3. Prefer the project\'s apparent mental model over both an abstract taxonomy and a mechanical copy of the current directory tree. Existing paths are useful clues, not structural authority. A later human review may rename, move, split, merge, add, or remove proposed Nodes.",\n        "4. A non-root Node may use an existing repository directory **or a new repository-relative directory that does not exist yet**. Propose a new directory when that is the clearest durable landing point for the semantic area. This is especially important for document-heavy repositories where many unrelated documents currently share one folder. ContextCanon materialization can create an accepted missing Node directory later; do not force distinct shelves into one Node merely because no matching directory exists today.",\n',
    '        "3. Treat the existing directory tree as the default when it already matches the project\'s semantic work areas; depart from it only for a clear reason.",\n        "4. Prefer a Node root that contains the files it primarily governs. If a proposed Node would leave its primary implementation elsewhere, mention that layout mismatch briefly in `rationale` for human review. New repository-relative directories remain allowed when they make the semantic structure clearer.",\n',
    "structure layout bias",
)
t = exact(
    t,
    '        "- choose `suggested_path` for durable semantic navigation rather than merely mirroring where today\'s evidence files happen to live;",\n',
    '        "- keep an existing path when it already fits; otherwise choose `suggested_path` for clearer durable semantic navigation;",\n',
    "structure suggested path rule",
)
write(path, t)


# ---------------------------------------------------------------------------
# CLI docs/source wording for multi-parent commands.
# ---------------------------------------------------------------------------
path = "nodes/library/foundation/docs/composition.md"
t = read(path)
t = t.replace("contextcanon parent review --node <child-node>", "contextcanon parent review [<parent-node-id>] --node <child-node>")
t = t.replace("contextcanon parent accept --node <child-node>", "contextcanon parent accept [<parent-node-id>] --node <child-node>")
t = t.replace("`parent review` is the only step that consults the live Parent locator.", "`parent review` is the only step that consults a live Parent locator. When several Parents exist, name the Parent Node ID; the ID may be omitted for a singleton Parent.")
write(path, t)


# ---------------------------------------------------------------------------
# Future semantic audit is explicitly later work, not current behavior.
# ---------------------------------------------------------------------------
path = "PLAN.md"
t = read(path)
if "### Later semantic contradiction audit" not in t:
    t += '''\n### Later semantic contradiction audit\n\n- [ ] When optional LLM semantic analysis is introduced, flag likely contradictions between inherited Contexts/Parents for human review; never infer precedence automatically.\n'''
write(path, t)


# ---------------------------------------------------------------------------
# Focused regression for two orthogonal Parents, order independence and update
# disambiguation.
# ---------------------------------------------------------------------------
path = ROOT / "tests/test_multi_parent.py"
path.write_text(r'''from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from contextcanon.compiler import Compiler
from contextcanon.package import artifact_files, compiled_package
from contextcanon.parser import ContextCanonError
from contextcanon.sources import review_parent_candidate


class MultiParentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        (self.repo / ".git").mkdir()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _node(self, rel: str, node_id: str, name: str, rule_id: str, statement: str) -> Path:
        root = self.repo / rel
        root.mkdir(parents=True, exist_ok=True)
        (root / "CONTEXT.src.md").write_text(
            f'''# {name} — Local Context Source
<!-- ctx:node id="{node_id}" version="1.0.0" -->

## Local Rules

### General

- **{rule_id}:** {statement}
  Why: regression
  <!-- ctx:rule id="{rule_id}" -->
''',
            encoding="utf-8",
        )
        return root

    def _install(self, child: Path, compiled) -> None:
        package = compiled_package(compiled)
        target = child / ".context" / "sources" / package.package_digest
        for rel, content in artifact_files(compiled).items():
            dest = target / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(content)

    def test_two_parents_compose_without_order_precedence(self) -> None:
        a = self._node("a", "node-a", "Parent A", "A-1", "Rule from A")
        b = self._node("b", "node-b", "Parent B", "B-1", "Rule from B")
        compiled_a = Compiler(self.repo).compile(a)
        compiled_b = Compiler(self.repo).compile(b)
        child = self._node("child", "node-child", "Child", "C-1", "Local rule")
        self._install(child, compiled_a)
        self._install(child, compiled_b)

        refs = []
        for rel, compiled in (("../b", compiled_b), ("../a", compiled_a)):
            refs.append(
                f'- [{compiled.metadata.name}]({rel}) — `{compiled.metadata.version}`\n'
                f'  <!-- ctx:parent id="{compiled.metadata.id}" version="{compiled.metadata.version}" '
                f'normalized-digest="{compiled.normalized_digest}" package-digest="{compiled.package_digest}" -->'
            )
        source = (child / "CONTEXT.src.md").read_text(encoding="utf-8")
        source = source.replace("\n## Local Rules", "\n## Parent Context Node\n\n" + "\n".join(refs) + "\n\n## Local Rules")
        (child / "CONTEXT.src.md").write_text(source, encoding="utf-8")

        compiled = Compiler(self.repo).compile(child)
        self.assertEqual([p.metadata.id for p in compiled.parent_packages], ["node-a", "node-b"])
        self.assertEqual({rule.id for rule in compiled.inherited_rules}, {"A-1", "B-1"})
        self.assertIn("**Parent Context Nodes:**", compiled.official_markdown)
        self.assertEqual([p.id for p in compiled_package(compiled).parents], ["node-a", "node-b"])

        # Reversing authoring order cannot create semantic precedence.
        reversed_source = source.replace("\n".join(refs), "\n".join(reversed(refs)))
        (child / "CONTEXT.src.md").write_text(reversed_source, encoding="utf-8")
        reversed_compiled = Compiler(self.repo).compile(child)
        self.assertEqual(reversed_compiled.normalized_digest, compiled.normalized_digest)

        with self.assertRaisesRegex(ContextCanonError, "multiple semantic Parents"):
            review_parent_candidate(child)


if __name__ == "__main__":
    unittest.main()
''', encoding="utf-8")
