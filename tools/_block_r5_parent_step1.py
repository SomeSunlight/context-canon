from __future__ import annotations

import argparse
from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one match, found {count}: {old[:120]!r}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


def patch_model() -> None:
    replace_once(
        "src/contextcanon/model.py",
        '''    def has_transport(self) -> bool:
        return self.transport is not None


@dataclass(frozen=True)
class RuleModification:
''',
        '''    def has_transport(self) -> bool:
        return self.transport is not None


@dataclass(frozen=True)
class ParentRef:
    id: str
    name: str
    version: str
    locator: str
    normalized_digest: str
    package_digest: str

    @property
    def is_pinned(self) -> bool:
        return True


@dataclass(frozen=True)
class RuleModification:
''',
    )
    replace_once(
        "src/contextcanon/model.py",
        '''    normalized_digest: str
    package_digest: str


@dataclass(frozen=True)
class ParsedNode:
''',
        '''    normalized_digest: str
    package_digest: str
    parent: PackageDependency | None = None


@dataclass(frozen=True)
class ParsedNode:
''',
    )
    replace_once(
        "src/contextcanon/model.py",
        '''    sources: tuple[SourceRef, ...]
    rules: tuple[Rule, ...]
    topics: tuple[Topic, ...]
    changes: tuple[RuleChange, ...] = ()
''',
        '''    sources: tuple[SourceRef, ...]
    rules: tuple[Rule, ...]
    topics: tuple[Topic, ...]
    parent: ParentRef | None = None
    changes: tuple[RuleChange, ...] = ()
''',
    )
    replace_once(
        "src/contextcanon/model.py",
        '''    source_packages: list[CompiledPackage] = field(default_factory=list)
    inherited_rules: list[Rule] = field(default_factory=list)
''',
        '''    parent_package: CompiledPackage | None = None
    source_packages: list[CompiledPackage] = field(default_factory=list)
    inherited_rules: list[Rule] = field(default_factory=list)
''',
    )


def patch_parser() -> None:
    replace_once(
        "src/contextcanon/parser.py",
        "from .model import NodeMetadata, ParsedNode, Rule, RuleChange, SourceRef, Topic, TopicTarget\n",
        "from .model import NodeMetadata, ParentRef, ParsedNode, Rule, RuleChange, SourceRef, Topic, TopicTarget\n",
    )
    replace_once(
        "src/contextcanon/parser.py",
        "SOURCE_COMMENT_RE = re.compile(r'<!--\\s*ctx:source\\s+(?P<attrs>.*?)\\s*-->')\n",
        "SOURCE_COMMENT_RE = re.compile(r'<!--\\s*ctx:source\\s+(?P<attrs>.*?)\\s*-->')\nPARENT_COMMENT_RE = re.compile(r'<!--\\s*ctx:parent\\s+(?P<attrs>.*?)\\s*-->')\n",
    )
    replace_once(
        "src/contextcanon/parser.py",
        '''    sources = _parse_sources(lines, sections.get("Sources"), source_path)
    rules = _parse_rules(lines, sections.get("Rules"), source_path, metadata)
''',
        '''    parent = _parse_parent(lines, sections.get("Parent"), source_path)
    if parent is not None and parent.id == metadata.id:
        raise ContextCanonError(f"{source_path}: Parent cannot be the Node itself")
    sources = _parse_sources(lines, sections.get("Sources"), source_path)
    rules = _parse_rules(lines, sections.get("Rules"), source_path, metadata)
''',
    )
    old_return = '''    return ParsedNode(
        node_root,
        repo_root,
        metadata,
        tuple(sources),
        tuple(rules),
        tuple(topics),
        tuple(changes),
        overview=overview,
        state=state,
        plan=plan,
    )
'''
    new_return = '''    return ParsedNode(
        root=node_root,
        repo_root=repo_root,
        metadata=metadata,
        sources=tuple(sources),
        rules=tuple(rules),
        topics=tuple(topics),
        parent=parent,
        changes=tuple(changes),
        overview=overview,
        state=state,
        plan=plan,
    )
'''
    replace_once("src/contextcanon/parser.py", old_return, new_return)
    anchor = "\ndef _parse_sources(lines: list[str], section: tuple[int, int] | None, source_path: Path) -> list[SourceRef]:\n"
    parent_parser = r'''
def _parse_parent(lines: list[str], section: tuple[int, int] | None, source_path: Path) -> ParentRef | None:
    if not section:
        return None
    start, end = section
    entries: list[tuple[int, re.Match[str]]] = []
    for i in range(start, end):
        match = SOURCE_RE.match(lines[i])
        if match:
            entries.append((i, match))
    if len(entries) != 1:
        raise ContextCanonError(f"{source_path}: Parent section must contain exactly one Parent entry")

    i, match = entries[0]
    attrs = _find_ctx_attrs(lines, PARENT_COMMENT_RE, i + 1, min(i + 5, end))
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

    return ParentRef(
        id=attrs["id"],
        name=match.group("name"),
        version=attrs["version"],
        locator=match.group("path"),
        normalized_digest=normalized_digest,
        package_digest=package_digest,
    )
'''
    p = Path("src/contextcanon/parser.py")
    text = p.read_text(encoding="utf-8")
    if anchor not in text:
        raise SystemExit("parser Parent insertion anchor missing")
    text = text.replace(anchor, parent_parser + anchor, 1)
    p.write_text(text, encoding="utf-8")


def patch_compiler() -> None:
    replace_once(
        "src/contextcanon/compiler.py",
        "from .model import CompiledNode, CompiledPackage, Rule, RuleChange, RuleModification, RuleRemoval, SourceRef, Topic, TopicTarget\n",
        "from .model import CompiledNode, CompiledPackage, ParentRef, Rule, RuleChange, RuleModification, RuleRemoval, SourceRef, Topic, TopicTarget\n",
    )
    replace_once("src/contextcanon/compiler.py", 'COMPILER_VERSION = "0.4.0"\n', 'COMPILER_VERSION = "0.5.0"\n')
    replace_once(
        "src/contextcanon/compiler.py",
        '''            compiled = CompiledNode(parsed=parsed)
            seen_source_ids: set[str] = set()
            source_resource_sets: list[dict[str, bytes]] = []
            for source in parsed.sources:
''',
        '''            compiled = CompiledNode(parsed=parsed)
            composition_packages: list[CompiledPackage] = []
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
''',
    )
    replace_once(
        "src/contextcanon/compiler.py",
        '''                if source.is_pinned:
                    package, package_resources = self._load_pinned_source(node_root, source)
                    compiled.source_packages.append(package)
                    source_resource_sets.append(package_resources)
                    continue
''',
        '''                if source.is_pinned:
                    package, package_resources = self._load_pinned_dependency(
                        node_root, source, relation="Source"
                    )
                    compiled.source_packages.append(package)
                    composition_packages.append(package)
                    source_resource_sets.append(package_resources)
                    continue
''',
    )
    replace_once(
        "src/contextcanon/compiler.py",
        '''                compiled.source_packages.append(compiled_package(source_node))
                source_resource_sets.append({
''',
        '''                source_package = compiled_package(source_node)
                compiled.source_packages.append(source_package)
                composition_packages.append(source_package)
                source_resource_sets.append({
''',
    )
    replace_once(
        "src/contextcanon/compiler.py",
        '''                compiled.source_packages,
                compiled.metadata.name,
            )
''',
        '''                composition_packages,
                compiled.metadata.name,
            )
''',
    )
    # The same exact two-line call shape occurs for Topic composition later.
    p = Path("src/contextcanon/compiler.py")
    text = p.read_text(encoding="utf-8")
    old = '''            compiled.inherited_topics = self._compose_inherited_topics(
                compiled.source_packages,
                compiled.metadata.name,
            )
'''
    if text.count(old) != 1:
        raise SystemExit(f"compiler Topic composition anchor count {text.count(old)}")
    text = text.replace(old, '''            compiled.inherited_topics = self._compose_inherited_topics(
                composition_packages,
                compiled.metadata.name,
            )
''', 1)
    p.write_text(text, encoding="utf-8")

    p = Path("src/contextcanon/compiler.py")
    text = p.read_text(encoding="utf-8")
    start = text.find("    def _load_pinned_source(")
    end = text.find("\n    def _resolve_source_root(", start)
    if start < 0 or end < 0:
        raise SystemExit("compiler pinned dependency function boundary missing")
    replacement = r'''    def _load_pinned_dependency(
        self,
        node_root: Path,
        dependency: SourceRef | ParentRef,
        *,
        relation: str,
    ) -> tuple[CompiledPackage, dict[str, bytes]]:
        if dependency.normalized_digest is None or dependency.package_digest is None:
            raise ContextCanonError(
                f"{node_root}: internal error: pinned {relation} {dependency.name} has incomplete digests"
            )

        package_root = node_root / ".context" / "sources" / dependency.package_digest
        if not package_root.is_dir():
            raise ContextCanonError(
                f"{node_root}: accepted {relation} package {dependency.name} is not available locally at "
                f".context/sources/{dependency.package_digest}; build does not fetch {relation} packages"
            )

        package = load_package(package_root)
        if package.metadata.id != dependency.id:
            raise ContextCanonError(
                f"{node_root}: {relation} {dependency.name} expects Node ID {dependency.id}, got {package.metadata.id}"
            )
        if package.metadata.version != dependency.version:
            raise ContextCanonError(
                f"{node_root}: {relation} {dependency.name} expects version {dependency.version}, got {package.metadata.version}"
            )
        if package.normalized_digest != dependency.normalized_digest:
            raise ContextCanonError(
                f"{node_root}: {relation} {dependency.name} normalized digest mismatch: "
                f"expected {dependency.normalized_digest}, got {package.normalized_digest}"
            )
        if package.package_digest != dependency.package_digest:
            raise ContextCanonError(
                f"{node_root}: {relation} {dependency.name} package digest mismatch: "
                f"expected {dependency.package_digest}, got {package.package_digest}"
            )
        resources = {
            file.path: (package_root / file.path).read_bytes()
            for file in package.files
            if file.path.startswith("CONTEXT/references/")
        }
        return package, resources
'''
    text = text[:start] + replacement + text[end:]
    p.write_text(text, encoding="utf-8")


def patch_package() -> None:
    anchor = '''def package_content_files(compiled: CompiledNode) -> dict[str, bytes]:
'''
    helper = '''def package_parent_dependency(compiled: CompiledNode) -> PackageDependency | None:
    parent = compiled.parent_package
    if parent is None:
        return None
    return PackageDependency(
        id=parent.metadata.id,
        name=parent.metadata.name,
        version=parent.metadata.version,
        normalized_digest=parent.normalized_digest,
        package_digest=parent.package_digest,
    )


'''
    p = Path("src/contextcanon/package.py")
    text = p.read_text(encoding="utf-8")
    if anchor not in text:
        raise SystemExit("package parent dependency insertion anchor missing")
    text = text.replace(anchor, helper + anchor, 1)
    p.write_text(text, encoding="utf-8")

    replace_once(
        "src/contextcanon/package.py",
        '''    topics: Iterable[Topic],
) -> dict[str, Any]:
''',
        '''    topics: Iterable[Topic],
    parent: PackageDependency | None = None,
) -> dict[str, Any]:
''',
    )
    old_return = '''    return {
        "node": {
            "id": metadata.id,
            "name": metadata.name,
            "version": metadata.version,
        },
        "sources": source_items,
        "changes": change_items,
        "rules": rule_items,
        "removed_rules": removal_items,
        "topics": topic_items,
    }
'''
    new_return = '''    payload: dict[str, Any] = {
        "node": {
            "id": metadata.id,
            "name": metadata.name,
            "version": metadata.version,
        },
        "sources": source_items,
        "changes": change_items,
        "rules": rule_items,
        "removed_rules": removal_items,
        "topics": topic_items,
    }
    if parent is not None:
        payload["parent"] = {
            "id": parent.id,
            "version": parent.version,
            "normalized_digest": parent.normalized_digest,
        }
    return payload
'''
    replace_once("src/contextcanon/package.py", old_return, new_return)
    replace_once(
        "src/contextcanon/package.py",
        '''    topics: Iterable[Topic],
) -> str:
    payload = semantic_payload(metadata, sources, changes, rules, removed_rules, topics)
''',
        '''    topics: Iterable[Topic],
    parent: PackageDependency | None = None,
) -> str:
    payload = semantic_payload(metadata, sources, changes, rules, removed_rules, topics, parent)
''',
    )
    replace_once(
        "src/contextcanon/package.py",
        '''        (*compiled.inherited_topics, *compiled.local_topics),
    )
''',
        '''        (*compiled.inherited_topics, *compiled.local_topics),
        package_parent_dependency(compiled),
    )
''',
    )
    replace_once(
        "src/contextcanon/package.py",
        '''        normalized_digest=compiled.normalized_digest,
        package_digest=compiled.package_digest,
    )
''',
        '''        normalized_digest=compiled.normalized_digest,
        package_digest=compiled.package_digest,
        parent=package_parent_dependency(compiled),
    )
''',
    )
    replace_once(
        "src/contextcanon/package.py",
        '''        "sources": [asdict(source) for source in package.sources],
        "changes": [asdict(change) for change in package.changes],
''',
        '''        "parent": asdict(package.parent) if package.parent is not None else None,
        "sources": [asdict(source) for source in package.sources],
        "changes": [asdict(change) for change in package.changes],
''',
    )
    replace_once(
        "src/contextcanon/package.py",
        '''    sources = tuple(_parse_dependency(item, index) for index, item in enumerate(_list(root.get("sources"), "sources")))
    _unique((source.id for source in sources), "package Source Node ID")
    changes = tuple(_parse_change(item, index) for index, item in enumerate(_list(root.get("changes"), "changes")))
''',
        '''    parent_raw = root.get("parent")
    parent = _parse_parent_dependency(parent_raw) if parent_raw is not None else None
    sources = tuple(_parse_dependency(item, index) for index, item in enumerate(_list(root.get("sources"), "sources")))
    _unique((source.id for source in sources), "package Source Node ID")
    if parent is not None and any(source.id == parent.id for source in sources):
        raise ContextCanonError("Context package cannot use the same Node as Parent and ordinary Source")
    changes = tuple(_parse_change(item, index) for index, item in enumerate(_list(root.get("changes"), "changes")))
''',
    )
    replace_once(
        "src/contextcanon/package.py",
        '''    actual_normalized = semantic_digest(metadata, sources, changes, rules, removed_rules, topics)
''',
        '''    actual_normalized = semantic_digest(metadata, sources, changes, rules, removed_rules, topics, parent)
''',
    )
    replace_once(
        "src/contextcanon/package.py",
        '''        normalized_digest=normalized_digest,
        package_digest=expected_package_digest,
    )
''',
        '''        normalized_digest=normalized_digest,
        package_digest=expected_package_digest,
        parent=parent,
    )
''',
    )
    anchor = "\ndef _parse_dependency(value: Any, index: int) -> PackageDependency:\n"
    parent_parse = '''
def _parse_parent_dependency(value: Any) -> PackageDependency:
    item = _dict(value, "parent")
    return PackageDependency(
        _string(item.get("id"), "parent.id"),
        _string(item.get("name"), "parent.name"),
        _string(item.get("version"), "parent.version"),
        _digest(item.get("normalized_digest"), "parent.normalized_digest"),
        _digest(item.get("package_digest"), "parent.package_digest"),
    )

'''
    p = Path("src/contextcanon/package.py")
    text = p.read_text(encoding="utf-8")
    if anchor not in text:
        raise SystemExit("package parent parse insertion anchor missing")
    text = text.replace(anchor, parent_parse + anchor, 1)
    p.write_text(text, encoding="utf-8")


def patch_render() -> None:
    replace_once(
        "src/contextcanon/render.py",
        '''        f"**Context version:** `{compiled.metadata.version}`",
        "",
    ])

    if compiled.parsed.overview:
''',
        '''        f"**Context version:** `{compiled.metadata.version}`",
        "",
    ])
    if compiled.parent_package is not None:
        lines.extend([
            f"**Parent:** {compiled.parent_package.metadata.name} (`{compiled.parent_package.metadata.id}`)  ",
            f"**Accepted Parent package:** `{compiled.parent_package.package_digest}`",
            "",
        ])

    if compiled.parsed.overview:
''',
    )
    replace_once(
        "src/contextcanon/render.py",
        '''        lines.extend(["## Local Rules" if compiled.source_packages else "## Rules", ""])
''',
        '''        lines.extend(["## Local Rules" if (compiled.parent_package or compiled.source_packages) else "## Rules", ""])
''',
    )
    replace_once(
        "src/contextcanon/render.py",
        '''        lines.extend(["## Local Topics" if compiled.source_packages else "## Topics", ""])
''',
        '''        lines.extend(["## Local Topics" if (compiled.parent_package or compiled.source_packages) else "## Topics", ""])
''',
    )
    replace_once(
        "src/contextcanon/render.py",
        '''        "# Accepted Source packages used by this build. Both digests are exact pins.",
    ]
    if compiled.source_packages:
''',
        '''        "# Accepted semantic Parent package. The locator is discovery metadata; build uses only the exact pin.",
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
''',
    )


def patch_diffs_and_source_validation() -> None:
    for path in ("src/contextcanon/diff.py", "src/contextcanon/package_diff.py"):
        replace_once(
            path,
            '''_CATEGORY_ORDER = {
    "node": 0,
    "source": 1,
    "change": 2,
    "rule": 3,
    "topic": 4,
    "resource": 5,
}
''',
            '''_CATEGORY_ORDER = {
    "node": 0,
    "parent": 1,
    "source": 2,
    "change": 3,
    "rule": 4,
    "topic": 5,
    "resource": 6,
}
''',
        )
        replace_once(
            path,
            '''    entries.extend(_diff_maps("node", _node_snapshot(before), _node_snapshot(after)))
    entries.extend(_diff_maps("source", _source_snapshot(before), _source_snapshot(after)))
''',
            '''    entries.extend(_diff_maps("node", _node_snapshot(before), _node_snapshot(after)))
    entries.extend(_diff_maps("parent", _parent_snapshot(before), _parent_snapshot(after)))
    entries.extend(_diff_maps("source", _source_snapshot(before), _source_snapshot(after)))
''',
        )

    anchor = "\ndef _source_snapshot(compiled: CompiledNode) -> dict[str, dict[str, Any]]:\n"
    helper = '''
def _parent_snapshot(compiled: CompiledNode) -> dict[str, dict[str, Any]]:
    parent = compiled.parent_package
    if parent is None:
        return {}
    return {
        parent.metadata.id: {
            "version": parent.metadata.version,
            "normalized_digest": parent.normalized_digest,
            "package_digest": parent.package_digest,
        }
    }

'''
    p = Path("src/contextcanon/diff.py")
    text = p.read_text(encoding="utf-8")
    if anchor not in text:
        raise SystemExit("diff parent snapshot anchor missing")
    text = text.replace(anchor, helper + anchor, 1)
    p.write_text(text, encoding="utf-8")

    anchor = "\ndef _source_snapshot(package: CompiledPackage) -> dict[str, dict[str, Any]]:\n"
    helper = '''
def _parent_snapshot(package: CompiledPackage) -> dict[str, dict[str, Any]]:
    parent = package.parent
    if parent is None:
        return {}
    return {
        parent.id: {
            "version": parent.version,
            "normalized_digest": parent.normalized_digest,
            "package_digest": parent.package_digest,
        }
    }

'''
    p = Path("src/contextcanon/package_diff.py")
    text = p.read_text(encoding="utf-8")
    if anchor not in text:
        raise SystemExit("package_diff parent snapshot anchor missing")
    text = text.replace(anchor, helper + anchor, 1)
    p.write_text(text, encoding="utf-8")

    replace_once(
        "src/contextcanon/sources.py",
        '''    packages = list(compiled.source_packages)
    packages[source_index] = candidate
''',
        '''    packages = ([compiled.parent_package] if compiled.parent_package is not None else []) + list(compiled.source_packages)
    candidate_index = source_index + (1 if compiled.parent_package is not None else 0)
    packages[candidate_index] = candidate
''',
    )


def patch_docs() -> None:
    parent_section = '''## Parent

A Context Node may have **one semantic Parent**. Parent is an explicit accepted relationship, not a filesystem convention. A directory above the Node, or a Node whose path contains this Node, does not become Parent automatically.

Parent is always an exact immutable package pin:

```markdown
## Parent

- [Project Context](../) — `0.1.0`
  <!-- ctx:parent id="<stable-parent-node-id>" version="0.1.0" normalized-digest="<sha256>" package-digest="<sha256>" -->
```

The visible locator records where a newer Parent candidate may later be discovered. Ordinary `contextcanon build` never dereferences it. Build loads only the accepted Parent artifact from the Child's local `.context/sources/<package-digest>/` store and verifies Node ID, version, both digests and package files.

Parent and ordinary Sources are intentionally different roles. Parent expresses the human-accepted semantic hierarchy; Sources express independent reusable composition. Both feed the same immutable package-composition engine, so inherited Rules, Topics and Resources use the same deterministic conflict rules without creating a second inheritance implementation.

Changing the Parent's live repository files therefore does not silently change the Child. The Child continues using its accepted Parent package until an explicit update is reviewed and accepted.

'''
    replace_once(
        "nodes/library/foundation/docs/source-format.md",
        "## Sources\n\n`## Sources` lists accepted Context Nodes.",
        parent_section + "## Sources\n\n`## Sources` lists accepted Context Nodes.",
    )
    replace_once(
        "nodes/library/foundation/docs/composition.md",
        '''# Context Composition

ContextCanon combines independent context Sources instead of relying on a single inheritance tree.
''',
        '''# Context Composition

ContextCanon combines one optional explicit semantic Parent with any number of independent reusable Sources. Filesystem nesting never creates either relationship implicitly.
''',
    )
    replace_once(
        "nodes/library/foundation/docs/composition.md",
        '''A Source is an accepted published package from another Context Node. Sources may live in the same Git repository or in independent repositories. Filesystem containment does not create inheritance.

Local development Sources can be resolved directly from another Node in the same repository. Accepted external Sources are immutable packages pinned by Node/version identity plus exact semantic and package digests.

## No implicit precedence
''',
        '''A Source is an accepted published package from another Context Node. Sources may live in the same Git repository or in independent repositories. A Parent is also an accepted package, but its role is the owner-reviewed semantic hierarchy rather than reusable cross-cutting composition.

Local development Sources can be resolved directly from another Node in the same repository. Accepted external Sources and every semantic Parent are immutable packages pinned by Node/version identity plus exact semantic and package digests.

## Semantic Parent

A Node has at most one Parent. The relationship must be written explicitly in `CONTEXT.src.md`; repository directories are only locations and do not imply Parent/Child composition.

Parent and Sources are composed through the same `CompiledPackage` boundary. This means no special "parent text merge" exists: the Child consumes the Parent's complete effective Rules, Topics, removals, overrides and materialized Topic Resources exactly as an immutable package. The Parent role remains separately visible in human output, machine state, package metadata and deterministic diff.

The accepted Parent pin is intentionally non-live. Editing or rebuilding the Parent Node elsewhere does not change an ordinary Child build. A Parent update is a later candidate/review/accept operation, not implicit inheritance from current filesystem bytes.

## No implicit precedence
''',
    )
    replace_once(
        "nodes/library/foundation/docs/composition.md",
        '''Compiler 0.4 supports local unpinned Sources and immutable pinned external Sources. Both become `CompiledPackage` before Rule composition, so the same transitive composition and conflict rules apply regardless of Source transport.
''',
        '''Compiler 0.5 supports one immutable semantic Parent, local unpinned Sources and immutable pinned external Sources. All become `CompiledPackage` before Rule/Topic composition, so the same transitive composition and conflict rules apply while Parent remains a distinct relationship role.
''',
    )


def write_tests() -> None:
    test = r'''from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from contextcanon.compiler import Compiler
from contextcanon.diff import diff_compiled
from contextcanon.package import artifact_files, load_package
from contextcanon.parser import ContextCanonError, parse_node


PARENT_SOURCE = ''' + "'''" + r'''# Shared Parent — Local Context Source
<!-- ctx:node id="node-parent" version="1.0.0" -->

## Rules

### Parent policy

- **Carry parent policy:** Parent policy must reach accepted descendants.
  Why: The semantic hierarchy should carry durable higher-level context.
  <!-- ctx:rule id="PARENT-001" -->

## Topics

### Parent guide

When changing inherited parent behavior:

Required:
- Resource: `guide.md`
<!-- ctx:topic id="PARENT-GUIDE" -->
''' + "'''" + r'''


def child_source(normalized: str, package: str, relation: str = "Parent") -> str:
    if relation == "Parent":
        return f'''# Child — Local Context Source
<!-- ctx:node id="node-child" version="0.1.0" -->

## Parent

- [Shared Parent](../parent) — `1.0.0`
  <!-- ctx:parent id="node-parent" version="1.0.0" normalized-digest="{normalized}" package-digest="{package}" -->
'''
    return f'''# Child — Local Context Source
<!-- ctx:node id="node-child" version="0.1.0" -->

## Sources

- [Shared Parent](../parent) — `1.0.0`
  <!-- ctx:source id="node-parent" version="1.0.0" normalized-digest="{normalized}" package-digest="{package}" -->
'''


class ParentRelationshipTests(unittest.TestCase):
    def make_parent(self):
        root = Path(tempfile.mkdtemp())
        (root / ".git").mkdir()
        (root / "CONTEXT.src.md").write_text(PARENT_SOURCE, encoding="utf-8")
        (root / "guide.md").write_text("# Parent Guide\n\nExact inherited bytes.\n", encoding="utf-8")
        return root, Compiler(root).compile(root)

    def make_child(self, normalized: str, package: str, relation: str = "Parent") -> Path:
        root = Path(tempfile.mkdtemp())
        (root / ".git").mkdir()
        (root / "CONTEXT.src.md").write_text(child_source(normalized, package, relation), encoding="utf-8")
        return root

    def install(self, child: Path, compiled) -> None:
        destination = child / ".context" / "sources" / compiled.package_digest
        for rel, content in artifact_files(compiled).items():
            path = destination / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)

    def package_roundtrip(self, compiled):
        root = Path(tempfile.mkdtemp())
        for rel, content in artifact_files(compiled).items():
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        return load_package(root)

    def test_pinned_parent_composes_offline_and_remains_distinct_from_sources(self):
        provider, parent = self.make_parent()
        child = self.make_child(parent.normalized_digest, parent.package_digest)
        self.install(child, parent)

        shutil.rmtree(provider)
        compiled = Compiler(child).compile(child)

        self.assertIsNotNone(compiled.parsed.parent)
        self.assertIsNotNone(compiled.parent_package)
        self.assertEqual(compiled.parent_package.metadata.id, "node-parent")
        self.assertEqual(compiled.source_packages, [])
        self.assertEqual([rule.id for rule in compiled.inherited_rules], ["PARENT-001"])
        self.assertEqual([topic.id for topic in compiled.inherited_topics], ["PARENT-GUIDE"])
        self.assertEqual(
            compiled.resources["CONTEXT/references/node-parent/guide.md"],
            b"# Parent Guide\n\nExact inherited bytes.\n",
        )
        self.assertIn("**Parent:** Shared Parent", compiled.official_markdown)
        self.assertIn("parent:\n", compiled.machine_yaml)

        package = self.package_roundtrip(compiled)
        self.assertIsNotNone(package.parent)
        self.assertEqual(package.parent.id, "node-parent")
        self.assertEqual(package.sources, ())

    def test_parent_role_is_semantic_not_just_a_source_label(self):
        _, parent = self.make_parent()
        child_as_parent = self.make_child(parent.normalized_digest, parent.package_digest, "Parent")
        child_as_source = self.make_child(parent.normalized_digest, parent.package_digest, "Source")
        self.install(child_as_parent, parent)
        self.install(child_as_source, parent)

        compiled_parent = Compiler(child_as_parent).compile(child_as_parent)
        compiled_source = Compiler(child_as_source).compile(child_as_source)
        self.assertEqual(
            [rule.statement for rule in compiled_parent.inherited_rules],
            [rule.statement for rule in compiled_source.inherited_rules],
        )
        self.assertNotEqual(compiled_parent.normalized_digest, compiled_source.normalized_digest)

    def test_parent_requires_both_exact_digests(self):
        root = Path(tempfile.mkdtemp())
        (root / ".git").mkdir()
        (root / "CONTEXT.src.md").write_text(
            '''# Child — Local Context Source
<!-- ctx:node id="node-child" version="0.1.0" -->

## Parent

- [Shared Parent](../parent) — `1.0.0`
  <!-- ctx:parent id="node-parent" version="1.0.0" normalized-digest="''' + ("0" * 64) + '''" -->
''',
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ContextCanonError, "Parent must pin both"):
            parse_node(root, root)

    def test_same_node_cannot_be_parent_and_source(self):
        _, parent = self.make_parent()
        child = self.make_child(parent.normalized_digest, parent.package_digest)
        with (child / "CONTEXT.src.md").open("a", encoding="utf-8") as handle:
            handle.write(f'''\n## Sources\n\n- [Shared Parent](../parent) — `1.0.0`\n  <!-- ctx:source id="node-parent" version="1.0.0" normalized-digest="{parent.normalized_digest}" package-digest="{parent.package_digest}" -->\n''')
        self.install(child, parent)
        with self.assertRaisesRegex(ContextCanonError, "both semantic Parent and ordinary Source"):
            Compiler(child).compile(child)

    def test_diff_reports_parent_as_parent(self):
        _, parent = self.make_parent()
        before_root = self.make_child(parent.normalized_digest, parent.package_digest, "Source")
        after_root = self.make_child(parent.normalized_digest, parent.package_digest, "Parent")
        self.install(before_root, parent)
        self.install(after_root, parent)
        before = Compiler(before_root).compile(before_root)
        after = Compiler(after_root).compile(after_root)
        diff = diff_compiled(before, after)
        categories = {(entry.category, entry.identity, entry.change) for entry in diff.entries}
        self.assertIn(("source", "node-parent", "removed"), categories)
        self.assertIn(("parent", "node-parent", "added"), categories)


if __name__ == "__main__":
    unittest.main()
'''
    Path("tests/test_parent_relationship.py").write_text(test, encoding="utf-8")


def complete() -> None:
    p = Path("PLAN.md")
    text = p.read_text(encoding="utf-8")
    text = text.replace(
        "**Status: ACTIVE — R5 Semantic Parent relationship, step 1 of 5. Fast-run remains ACTIVE.**",
        "**Status: ACTIVE — R5 Semantic Parent relationship, step 2 of 5. Fast-run remains ACTIVE.**",
        1,
    )
    text = text.replace(
        "- [ ] 1. Add an explicit `Parent` relationship to the authoring grammar/model/compiler/package/rendering boundary, distinct from ordinary reusable Sources but reusing the same immutable package-composition machinery.",
        "- [x] 1. Add an explicit `Parent` relationship to the authoring grammar/model/compiler/package/rendering boundary, distinct from ordinary reusable Sources but reusing the same immutable package-composition machinery.",
        1,
    )
    p.write_text(text, encoding="utf-8")

    state = Path("STATE.md")
    current = state.read_text(encoding="utf-8").rstrip()
    block = '''

## Latest Block R5 step-1 semantic-Parent checkpoint

ContextCanon now has an explicit `## Parent` authoring relationship. Parent is always an exact immutable package pin and remains distinct from ordinary reusable Sources in parsed state, compiled state, human rendering, machine YAML, package metadata and deterministic diff. Filesystem nesting still carries no composition meaning.

The compiler composes the accepted Parent package through the same Rule/Topic/Resource conflict machinery as Sources, while the normalized semantic digest records the Parent role separately. Existing packages without Parent metadata remain valid because the optional Parent semantic field is absent when no Parent exists. Normal builds load the Parent only from the Child's local immutable package store and never dereference the Parent locator.

R5 step 2 is next: persist the owner-accepted Step-03 hierarchy during onboarding publication and install the exact resulting Parent package into each Child. PR #13 remains draft and unmerged; fast-run remains active.
'''
    state.write_text(current + block.rstrip() + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--complete", action="store_true")
    args = parser.parse_args()
    if args.complete:
        complete()
        return
    patch_model()
    patch_parser()
    patch_compiler()
    patch_package()
    patch_render()
    patch_diffs_and_source_validation()
    patch_docs()
    write_tests()


if __name__ == "__main__":
    main()
