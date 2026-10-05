from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterable

from .model import (
    CompiledNode,
    CompiledPackage,
    NodeMetadata,
    PackageDependency,
    PackageFile,
    Rule,
    RuleChange,
    RuleModification,
    RuleRemoval,
    ResourceOrigin,
    Topic,
    TopicTarget,
)
from .parser import ContextCanonError
from .resource_layout import ORIGINS_PATH, ORIGINS_SCHEMA, legacy_namespace

PACKAGE_SCHEMA = "contextcanon/package/v4"
RELATIONSHIP_PACKAGE_SCHEMA = "contextcanon/package/v3"
PREVIOUS_PACKAGE_SCHEMA = "contextcanon/package/v2"
OLDER_PACKAGE_SCHEMA = "contextcanon/package/v1"
LEGACY_PACKAGE_SCHEMA = "contextcanon/package/v0"
PACKAGE_MANIFEST_PATH = ".context/package.json"


def package_dependencies(compiled: CompiledNode) -> tuple[PackageDependency, ...]:
    return tuple(
        sorted(
            (
                PackageDependency(
                    id=package.metadata.id,
                    name=package.metadata.name,
                    version=package.metadata.version,
                    normalized_digest=package.normalized_digest,
                    package_digest=package.package_digest,
                    relationship=ref.relationship,
                )
                for ref, package in zip(compiled.parsed.sources, compiled.source_packages)
            ),
            key=lambda source: (
                source.id,
                source.version,
                source.normalized_digest,
                source.package_digest,
                source.relationship or "",
            ),
        )
    )


def package_parent_dependencies(compiled: CompiledNode) -> tuple[PackageDependency, ...]:
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

def package_content_files(compiled: CompiledNode) -> dict[str, bytes]:
    return {
        "CONTEXT.md": compiled.official_markdown.encode("utf-8"),
        **compiled.resources,
    }


def package_digest(files: dict[str, bytes]) -> str:
    digest = hashlib.sha256()
    for path, content in sorted(files.items()):
        digest.update(path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(content).digest())
        digest.update(b"\0")
    return digest.hexdigest()


def package_file_metadata(files: dict[str, bytes]) -> tuple[PackageFile, ...]:
    return tuple(
        PackageFile(path, hashlib.sha256(content).hexdigest(), len(content))
        for path, content in sorted(files.items())
    )


def semantic_payload(
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
                **({"relationship": source.relationship} if source.relationship else {}),
            }
            for source in sources
        ),
        key=lambda item: (
            item["id"],
            item["version"],
            item["normalized_digest"],
            item.get("relationship", ""),
        ),
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
    topic_items = [_semantic_topic_dict(topic) for topic in topics]
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

def semantic_digest(
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

def semantic_digest_for_node(compiled: CompiledNode) -> str:
    return semantic_digest(
        compiled.metadata,
        package_dependencies(compiled),
        compiled.local_changes,
        (*compiled.inherited_rules, *compiled.local_rules),
        compiled.removed_rules,
        (*compiled.inherited_topics, *compiled.local_topics),
        None,
        compiled.imported_contexts,
        parents=package_parent_dependencies(compiled),
    )


def compiled_package(compiled: CompiledNode) -> CompiledPackage:
    files = package_content_files(compiled)
    return CompiledPackage(
        metadata=NodeMetadata(compiled.metadata.id, compiled.metadata.name, compiled.metadata.version),
        sources=package_dependencies(compiled),
        changes=tuple(compiled.local_changes),
        # Preserve effective presentation order. semantic_digest canonicalizes
        # Rule order independently where order has no semantic meaning.
        rules=tuple((*compiled.inherited_rules, *compiled.local_rules)),
        removed_rules=tuple(sorted(
            compiled.removed_rules,
            key=lambda removal: (
                removal.origin_node_id,
                removal.rule_id,
                removal.removed_by_node_id,
                removal.removed_by_node_name,
                removal.why,
            ),
        )),
        topics=tuple((*compiled.inherited_topics, *compiled.local_topics)),
        files=package_file_metadata(files),
        normalized_digest=compiled.normalized_digest,
        package_digest=compiled.package_digest,
        imports=tuple(compiled.imported_contexts),
        parents=package_parent_dependencies(compiled),
        resource_origins=tuple(compiled.resource_origins[path] for path in sorted(compiled.resource_origins)),
    )


def _dependency_dict(dependency: PackageDependency) -> dict[str, Any]:
    item = asdict(dependency)
    if dependency.relationship is None:
        item.pop("relationship", None)
    return item


def render_package_manifest(compiled: CompiledNode, compiler_version: str) -> str:
    package = compiled_package(compiled)
    payload = {
        "schema": PACKAGE_SCHEMA,
        "compiler_version": compiler_version,
        "node": {
            "id": package.metadata.id,
            "name": package.metadata.name,
            "version": package.metadata.version,
        },
        "parents": [_dependency_dict(parent) for parent in package.parents],
        "sources": [_dependency_dict(source) for source in package.sources],
        "imports": [_dependency_dict(dependency) for dependency in package.imports],
        "changes": [asdict(change) for change in package.changes],
        "rules": [asdict(rule) for rule in package.rules],
        "removed_rules": [asdict(removal) for removal in package.removed_rules],
        "topics": [_topic_dict(topic) for topic in package.topics],
        "files": [asdict(file) for file in package.files],
        "digests": {
            "normalized": package.normalized_digest,
            "package": package.package_digest,
        },
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def load_package(package_root: Path) -> CompiledPackage:
    """Load and fully verify an immutable compiled Context package.

    The loader needs only the package root: CONTEXT.md, optional CONTEXT/
    resources, and .context/package.json. No CONTEXT.src.md or Source
    repository is consulted.
    """

    package_root = package_root.resolve()
    manifest_path = package_root / PACKAGE_MANIFEST_PATH
    if not manifest_path.is_file():
        raise ContextCanonError(f"Not a compiled Context package: {package_root} (missing {PACKAGE_MANIFEST_PATH})")

    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContextCanonError(f"Invalid Context package manifest {manifest_path}: {exc}") from exc

    root = _dict(raw, "manifest")
    schema = root.get("schema")
    if schema not in {PACKAGE_SCHEMA, RELATIONSHIP_PACKAGE_SCHEMA, PREVIOUS_PACKAGE_SCHEMA, OLDER_PACKAGE_SCHEMA, LEGACY_PACKAGE_SCHEMA}:
        raise ContextCanonError(
            f"Unsupported Context package schema in {manifest_path}: {schema!r}"
        )

    node = _dict(root.get("node"), "node")
    metadata = NodeMetadata(
        _string(node.get("id"), "node.id"),
        _string(node.get("name"), "node.name"),
        _string(node.get("version"), "node.version"),
    )

    if schema == LEGACY_PACKAGE_SCHEMA:
        parent_raw = root.get("parent")
        parents = (() if parent_raw is None else (_parse_parent_dependency(parent_raw, "parent"),))
    else:
        parents = tuple(
            _parse_parent_dependency(item, f"parents[{index}]")
            for index, item in enumerate(_list(root.get("parents", []), "parents"))
        )
    _unique((parent.id for parent in parents), "package Parent Node ID")
    sources = tuple(
        _parse_dependency(item, index, require_relationship=(schema in {PACKAGE_SCHEMA, RELATIONSHIP_PACKAGE_SCHEMA}))
        for index, item in enumerate(_list(root.get("sources"), "sources"))
    )
    imports = tuple(
        _parse_import_dependency(item, index)
        for index, item in enumerate(_list(root.get("imports", []), "imports"))
    )
    _unique((source.id for source in sources), "package Source Node ID")
    _unique((dependency.id for dependency in imports), "package imported Context Node ID")
    parent_ids = {parent.id for parent in parents}
    if any(source.id in parent_ids for source in sources):
        raise ContextCanonError("Context package cannot use the same Node as Parent and ordinary Source")
    changes = tuple(_parse_change(item, index) for index, item in enumerate(_list(root.get("changes"), "changes")))
    rules = tuple(_parse_rule(item, index) for index, item in enumerate(_list(root.get("rules"), "rules")))
    removed_rules = tuple(
        _parse_removal(item, index) for index, item in enumerate(_list(root.get("removed_rules"), "removed_rules"))
    )
    topics = tuple(_parse_topic(item, index) for index, item in enumerate(_list(root.get("topics"), "topics")))
    files = tuple(_parse_file(item, index) for index, item in enumerate(_list(root.get("files"), "files")))
    _unique((file.path for file in files), "package file path")

    digests = _dict(root.get("digests"), "digests")
    normalized_digest = _digest(digests.get("normalized"), "digests.normalized")
    expected_package_digest = _digest(digests.get("package"), "digests.package")

    if schema == LEGACY_PACKAGE_SCHEMA:
        legacy_parent = parents[0] if parents else None
        actual_normalized = semantic_digest(metadata, sources, changes, rules, removed_rules, topics, legacy_parent, imports)
    else:
        actual_normalized = semantic_digest(metadata, sources, changes, rules, removed_rules, topics, None, imports, parents=parents)
    if actual_normalized != normalized_digest:
        raise ContextCanonError(
            f"Context package normalized digest mismatch in {manifest_path}: "
            f"expected {normalized_digest}, computed {actual_normalized}"
        )

    actual_files = _read_and_verify_files(package_root, files)
    actual_package_digest = package_digest(actual_files)
    if actual_package_digest != expected_package_digest:
        raise ContextCanonError(
            f"Context package digest mismatch in {manifest_path}: "
            f"expected {expected_package_digest}, computed {actual_package_digest}"
        )

    return CompiledPackage(
        metadata=metadata,
        sources=tuple(sorted(sources, key=lambda source: (source.id, source.version, source.normalized_digest, source.package_digest))),
        changes=tuple(changes),
        # Preserve manifest order for presentation-equivalent downstream
        # composition. Semantic verification above remains order-insensitive.
        rules=tuple(rules),
        removed_rules=tuple(sorted(
            removed_rules,
            key=lambda removal: (
                removal.origin_node_id,
                removal.rule_id,
                removal.removed_by_node_id,
                removal.removed_by_node_name,
                removal.why,
            ),
        )),
        topics=tuple(topics),
        files=tuple(sorted(files, key=lambda file: file.path)),
        normalized_digest=normalized_digest,
        package_digest=expected_package_digest,
        imports=tuple(imports),
        parents=tuple(sorted(parents, key=lambda parent: (parent.id, parent.version, parent.normalized_digest, parent.package_digest))),
        resource_origins=_load_resource_origins(actual_files, topics, metadata, sources, imports, schema),
    )


def _load_resource_origins(files, topics, metadata, sources, imports, schema) -> tuple[ResourceOrigin, ...]:
    resource_paths = {path for path in files if path.startswith("CONTEXT/references/")}
    if ORIGINS_PATH in files:
        try:
            raw = json.loads(files[ORIGINS_PATH])
        except (ValueError, UnicodeDecodeError) as exc:
            raise ContextCanonError(f"Invalid authenticated Resource origin mapping: {exc}") from exc
        if not isinstance(raw, dict) or raw.get("schema") != ORIGINS_SCHEMA:
            raise ContextCanonError("Invalid Resource origin mapping schema")
        origins = []
        for item in _list(raw.get("resources"), "Resource origins"):
            entry = _dict(item, "Resource origin")
            path = _string(entry.get("path"), "Resource origin.path")
            repo_path = _string(entry.get("repo_path"), "Resource origin.repo_path")
            if path not in resource_paths or Path(repo_path).is_absolute() or ".." in Path(repo_path).parts:
                raise ContextCanonError(f"Invalid Resource origin path: {path}")
            origins.append(ResourceOrigin(path, _string(entry.get("node_id"), "Resource origin.node_id"), repo_path))
        _unique((origin.path for origin in origins), "Resource origin path")
        if {origin.path for origin in origins} != resource_paths:
            raise ContextCanonError("Resource origin mapping does not match package Resource files")
        return tuple(sorted(origins, key=lambda item: item.path))
    if resource_paths and schema == PACKAGE_SCHEMA:
        raise ContextCanonError("Package v4 Resource files require authenticated origin mapping")
    # Old packages preserve repository-relative paths. Decode their namespace
    # without rewriting accepted bytes or their legacy semantic normalization.
    known_ids = {metadata.id, *(topic.origin_node_id for topic in topics),
                 *(item.id for item in sources), *(item.id for item in imports)}
    namespaces = {legacy_namespace(node_id): node_id for node_id in known_ids}
    return tuple(ResourceOrigin(path, namespaces.get(path.split("/")[2], path.split("/")[2]),
                                "/".join(path.split("/")[3:])) for path in sorted(resource_paths))


def artifact_files(compiled: CompiledNode) -> dict[str, bytes]:
    """Return the complete immutable package artifact without authoring or harness files."""

    return {
        **package_content_files(compiled),
        PACKAGE_MANIFEST_PATH: compiled.package_manifest.encode("utf-8"),
    }


def _semantic_topic_dict(topic: Topic) -> dict[str, Any]:
    """Canonical Topic payload for normalized identity.

    An identified Resource is represented by its stable Resource ID rather
    than by its current package locator. Legacy path-only Resources retain
    their locator so existing package digests remain verifiable.
    """

    item = asdict(topic)
    targets: list[dict[str, Any]] = []
    for target in item["targets"]:
        if target["kind"] == "resource" and target.get("resource_id"):
            targets.append(
                {
                    "kind": target["kind"],
                    "intent": target["intent"],
                    "resource_id": target["resource_id"],
                }
            )
        else:
            targets.append({key: value for key, value in target.items() if value is not None})
    item["targets"] = sorted(
        targets,
        key=lambda target: (
            target["intent"],
            target["kind"],
            target.get("resource_id", ""),
            target.get("locator", ""),
            target.get("target_node_id", ""),
            target.get("target_node_name", ""),
        ),
    )
    return item


def _topic_dict(topic: Topic) -> dict[str, Any]:
    item = asdict(topic)
    targets: list[dict[str, Any]] = []
    for target in item["targets"]:
        targets.append({key: value for key, value in target.items() if value is not None})
    item["targets"] = sorted(
        targets,
        key=lambda target: (
            target["intent"], target["kind"], target["locator"],
            target.get("resource_id", ""),
            target.get("target_node_id", ""), target.get("target_node_name", ""),
        ),
    )
    return item


def exported_resource_files(package: CompiledPackage) -> tuple[PackageFile, ...]:
    """Return only Topic Resource files that belong to the normative export.

    The owning package may also carry Resource bytes used only by its direct
    informational References. Those bytes remain useful locally but are not
    inherited when this package is consumed as a semantic Parent.
    """

    prefixes: set[str] = set()
    for topic in package.topics:
        for target in topic.targets:
            if target.kind != "resource" or not target.locator.startswith("CONTEXT/references/"):
                continue
            parts = target.locator.split("/")
            if len(parts) >= 3:
                prefixes.add("/".join(parts[:3]) + "/")
    return tuple(
        file
        for file in package.files
        if any(file.path.startswith(prefix) for prefix in prefixes)
    )


def export_digest(package: CompiledPackage) -> str:
    """Digest the normative Context this package exports to semantic Children.

    Presentation, the Node's release version and direct Reference carriers are
    deliberately excluded. Effective ancestry identities, Rules, removals,
    Topics and their exact Resource bytes define what a Child can inherit.
    """

    imports = sorted(
        (
            {
                "id": dependency.id,
                "name": dependency.name,
                **({"why": dependency.why} if dependency.why else {}),
            }
            for dependency in package.imports
        ),
        key=lambda item: (item["id"], item["name"], item.get("why", "")),
    )
    rules = sorted(
        (asdict(rule) for rule in package.rules),
        key=lambda item: (item["origin_node_id"], item["id"]),
    )
    removals = sorted(
        (asdict(removal) for removal in package.removed_rules),
        key=lambda item: (
            item["origin_node_id"],
            item["rule_id"],
            item["removed_by_node_id"],
            item["removed_by_node_name"],
            item["why"],
        ),
    )
    topics = [_topic_dict(topic) for topic in package.topics]
    topics.sort(key=lambda item: (item["origin_node_id"], item["id"]))
    files = [asdict(file) for file in exported_resource_files(package)]
    payload = {
        "node": {"id": package.metadata.id, "name": package.metadata.name},
        "imports": imports,
        "rules": rules,
        "removed_rules": removals,
        "topics": topics,
        "files": files,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _read_and_verify_files(package_root: Path, expected: tuple[PackageFile, ...]) -> dict[str, bytes]:
    expected_by_path = {file.path: file for file in expected}
    actual_paths: set[str] = set()
    if (package_root / "CONTEXT.md").is_file():
        actual_paths.add("CONTEXT.md")
    if ORIGINS_PATH in expected_by_path and (package_root / ORIGINS_PATH).is_file():
        actual_paths.add(ORIGINS_PATH)
    context_dir = package_root / "CONTEXT"
    if context_dir.exists():
        actual_paths.update(
            path.relative_to(package_root).as_posix()
            for path in context_dir.rglob("*")
            if path.is_file()
        )

    if actual_paths != set(expected_by_path):
        missing = sorted(set(expected_by_path) - actual_paths)
        extra = sorted(actual_paths - set(expected_by_path))
        details = []
        if missing:
            details.append("missing " + ", ".join(missing))
        if extra:
            details.append("extra " + ", ".join(extra))
        raise ContextCanonError(f"Context package file set mismatch in {package_root}: {'; '.join(details)}")

    contents: dict[str, bytes] = {}
    for path in sorted(actual_paths):
        expected_file = expected_by_path[path]
        content = (package_root / path).read_bytes()
        actual_hash = hashlib.sha256(content).hexdigest()
        if actual_hash != expected_file.sha256 or len(content) != expected_file.size:
            raise ContextCanonError(
                f"Context package file mismatch: {path} expected sha256={expected_file.sha256} "
                f"size={expected_file.size}, got sha256={actual_hash} size={len(content)}"
            )
        contents[path] = content
    return contents


def _parse_parent_dependency(value: Any, label: str = "parent") -> PackageDependency:
    item = _dict(value, label)
    return PackageDependency(
        _string(item.get("id"), f"{label}.id"),
        _string(item.get("name"), f"{label}.name"),
        _string(item.get("version"), f"{label}.version"),
        _digest(item.get("normalized_digest"), f"{label}.normalized_digest"),
        _digest(item.get("package_digest"), f"{label}.package_digest"),
    )

def _parse_dependency(value: Any, index: int, *, require_relationship: bool = False) -> PackageDependency:
    item = _dict(value, f"sources[{index}]")
    raw_relationship = item.get("relationship")
    if raw_relationship is None:
        if require_relationship:
            raise ContextCanonError(
                f"Invalid sources[{index}].relationship: v3 packages require parent or reference"
            )
        relationship = None
    else:
        relationship = _string(raw_relationship, f"sources[{index}].relationship")
        if relationship not in {"parent", "reference"}:
            raise ContextCanonError(
                f"Invalid sources[{index}].relationship: expected parent or reference"
            )
    return PackageDependency(
        _string(item.get("id"), f"sources[{index}].id"),
        _string(item.get("name"), f"sources[{index}].name"),
        _string(item.get("version"), f"sources[{index}].version"),
        _digest(item.get("normalized_digest"), f"sources[{index}].normalized_digest"),
        _digest(item.get("package_digest"), f"sources[{index}].package_digest"),
        relationship=relationship,  # type: ignore[arg-type]
    )


def _parse_import_dependency(value: Any, index: int) -> PackageDependency:
    item = _dict(value, f"imports[{index}]")
    return PackageDependency(
        _string(item.get("id"), f"imports[{index}].id"),
        _string(item.get("name"), f"imports[{index}].name"),
        _string(item.get("version"), f"imports[{index}].version"),
        _digest(item.get("normalized_digest"), f"imports[{index}].normalized_digest"),
        _digest(item.get("package_digest"), f"imports[{index}].package_digest"),
        None if item.get("why") is None else _string(item.get("why"), f"imports[{index}].why"),
    )


def _parse_change(value: Any, index: int) -> RuleChange:
    item = _dict(value, f"changes[{index}]")
    kind = _string(item.get("kind"), f"changes[{index}].kind")
    if kind not in {"remove", "override"}:
        raise ContextCanonError(f"Invalid changes[{index}].kind: {kind!r}")
    statement = item.get("statement")
    if statement is not None and not isinstance(statement, str):
        raise ContextCanonError(f"Invalid changes[{index}].statement: expected string or null")
    return RuleChange(
        kind=kind,  # type: ignore[arg-type]
        target_node_id=_string(item.get("target_node_id"), f"changes[{index}].target_node_id"),
        target_node_name=_string(item.get("target_node_name"), f"changes[{index}].target_node_name"),
        target_rule_id=_string(item.get("target_rule_id"), f"changes[{index}].target_rule_id"),
        statement=statement,
        why=_string(item.get("why"), f"changes[{index}].why"),
    )


def _parse_rule(value: Any, index: int) -> Rule:
    item = _dict(value, f"rules[{index}]")
    modifications = tuple(
        _parse_modification(modification, index, mod_index)
        for mod_index, modification in enumerate(_list(item.get("modifications"), f"rules[{index}].modifications"))
    )
    return Rule(
        id=_string(item.get("id"), f"rules[{index}].id"),
        title=_string(item.get("title"), f"rules[{index}].title"),
        statement=_string(item.get("statement"), f"rules[{index}].statement"),
        why=_string(item.get("why"), f"rules[{index}].why"),
        group=_string(item.get("group"), f"rules[{index}].group"),
        origin_node_id=_string(item.get("origin_node_id"), f"rules[{index}].origin_node_id"),
        origin_node_name=_string(item.get("origin_node_name"), f"rules[{index}].origin_node_name"),
        modifications=modifications,
    )


def _parse_modification(value: Any, rule_index: int, mod_index: int) -> RuleModification:
    label = f"rules[{rule_index}].modifications[{mod_index}]"
    item = _dict(value, label)
    kind = _string(item.get("kind"), f"{label}.kind")
    if kind != "override":
        raise ContextCanonError(f"Invalid {label}.kind: {kind!r}")
    return RuleModification(
        kind="override",
        node_id=_string(item.get("node_id"), f"{label}.node_id"),
        node_name=_string(item.get("node_name"), f"{label}.node_name"),
        why=_string(item.get("why"), f"{label}.why"),
    )


def _parse_removal(value: Any, index: int) -> RuleRemoval:
    item = _dict(value, f"removed_rules[{index}]")
    return RuleRemoval(
        origin_node_id=_string(item.get("origin_node_id"), f"removed_rules[{index}].origin_node_id"),
        origin_node_name=_string(item.get("origin_node_name"), f"removed_rules[{index}].origin_node_name"),
        rule_id=_string(item.get("rule_id"), f"removed_rules[{index}].rule_id"),
        removed_by_node_id=_string(item.get("removed_by_node_id"), f"removed_rules[{index}].removed_by_node_id"),
        removed_by_node_name=_string(item.get("removed_by_node_name"), f"removed_rules[{index}].removed_by_node_name"),
        why=_string(item.get("why"), f"removed_rules[{index}].why"),
    )


def _parse_topic(value: Any, index: int) -> Topic:
    item = _dict(value, f"topics[{index}]")
    targets = tuple(
        _parse_target(target, index, target_index)
        for target_index, target in enumerate(_list(item.get("targets"), f"topics[{index}].targets"))
    )
    return Topic(
        id=_string(item.get("id"), f"topics[{index}].id"),
        title=_string(item.get("title"), f"topics[{index}].title"),
        condition=_string(item.get("condition"), f"topics[{index}].condition"),
        targets=targets,
        origin_node_id=_string(item.get("origin_node_id"), f"topics[{index}].origin_node_id"),
        origin_node_name=_string(item.get("origin_node_name"), f"topics[{index}].origin_node_name"),
    )


def _parse_target(value: Any, topic_index: int, target_index: int) -> TopicTarget:
    label = f"topics[{topic_index}].targets[{target_index}]"
    item = _dict(value, label)
    kind = _string(item.get("kind"), f"{label}.kind")
    intent = _string(item.get("intent"), f"{label}.intent")
    if kind not in {"resource", "context-node"}:
        raise ContextCanonError(f"Invalid {label}.kind: {kind!r}")
    if intent not in {"required", "optional"}:
        raise ContextCanonError(f"Invalid {label}.intent: {intent!r}")
    target_node_id = item.get("target_node_id")
    target_node_name = item.get("target_node_name")
    resource_id = item.get("resource_id")
    if target_node_id is not None and not isinstance(target_node_id, str):
        raise ContextCanonError(f"Invalid {label}.target_node_id: expected string or null")
    if target_node_name is not None and not isinstance(target_node_name, str):
        raise ContextCanonError(f"Invalid {label}.target_node_name: expected string or null")
    if resource_id is not None and not isinstance(resource_id, str):
        raise ContextCanonError(f"Invalid {label}.resource_id: expected string or null")
    if (target_node_id is None) != (target_node_name is None):
        raise ContextCanonError(f"Invalid {label}: target_node_id and target_node_name must appear together")
    if kind == "context-node" and resource_id is not None:
        raise ContextCanonError(f"Invalid {label}: Context Node targets cannot carry resource_id")
    return TopicTarget(
        kind=kind,  # type: ignore[arg-type]
        locator=_string(item.get("locator"), f"{label}.locator"),
        intent=intent,  # type: ignore[arg-type]
        target_node_id=target_node_id,
        target_node_name=target_node_name,
        resource_id=resource_id,
    )


def _parse_file(value: Any, index: int) -> PackageFile:
    item = _dict(value, f"files[{index}]")
    path = _string(item.get("path"), f"files[{index}].path")
    if path not in {"CONTEXT.md", ORIGINS_PATH} and not path.startswith("CONTEXT/"):
        raise ContextCanonError(f"Invalid package file path {path!r}; expected CONTEXT.md or CONTEXT/*")
    if ".." in Path(path).parts or Path(path).is_absolute():
        raise ContextCanonError(f"Invalid package file path {path!r}")
    size = item.get("size")
    if not isinstance(size, int) or isinstance(size, bool) or size < 0:
        raise ContextCanonError(f"Invalid files[{index}].size: expected non-negative integer")
    return PackageFile(path, _digest(item.get("sha256"), f"files[{index}].sha256"), size)


def _dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContextCanonError(f"Invalid Context package {label}: expected object")
    return value


def _list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ContextCanonError(f"Invalid Context package {label}: expected array")
    return value


def _string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ContextCanonError(f"Invalid Context package {label}: expected non-empty string")
    return value


def _digest(value: Any, label: str) -> str:
    text = _string(value, label)
    if len(text) != 64 or any(char not in "0123456789abcdef" for char in text):
        raise ContextCanonError(f"Invalid Context package {label}: expected lowercase SHA-256 hex")
    return text


def _unique(values: Iterable[str], label: str) -> None:
    seen: set[str] = set()
    for value in values:
        if value in seen:
            raise ContextCanonError(f"Duplicate {label}: {value}")
        seen.add(value)
