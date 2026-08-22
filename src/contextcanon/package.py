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
    Topic,
    TopicTarget,
)
from .parser import ContextCanonError

PACKAGE_SCHEMA = "contextcanon/package/v0"
PACKAGE_MANIFEST_PATH = ".context/package.json"


def package_dependencies(compiled: CompiledNode) -> tuple[PackageDependency, ...]:
    return tuple(
        sorted(
            (
                PackageDependency(
                    id=source.metadata.id,
                    name=source.metadata.name,
                    version=source.metadata.version,
                    normalized_digest=source.normalized_digest,
                    package_digest=source.package_digest,
                )
                for source in compiled.source_nodes
            ),
            key=lambda source: (source.id, source.version, source.normalized_digest, source.package_digest),
        )
    )


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
) -> dict[str, Any]:
    """Return the canonical semantic payload used for normalized_digest.

    Exact Source package bytes are deliberately not semantic input. A Source's
    normalized digest identifies the accepted semantic dependency; its package
    digest is tracked separately for exact human/agent package identity.
    """

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

    return {
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


def semantic_digest(
    metadata: NodeMetadata,
    sources: Iterable[PackageDependency],
    changes: Iterable[RuleChange],
    rules: Iterable[Rule],
    removed_rules: Iterable[RuleRemoval],
    topics: Iterable[Topic],
) -> str:
    payload = semantic_payload(metadata, sources, changes, rules, removed_rules, topics)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def semantic_digest_for_node(compiled: CompiledNode) -> str:
    return semantic_digest(
        compiled.metadata,
        package_dependencies(compiled),
        compiled.local_changes,
        (*compiled.inherited_rules, *compiled.local_rules),
        compiled.removed_rules,
        compiled.local_topics,
    )


def compiled_package(compiled: CompiledNode) -> CompiledPackage:
    files = package_content_files(compiled)
    return CompiledPackage(
        metadata=NodeMetadata(compiled.metadata.id, compiled.metadata.name, compiled.metadata.version),
        sources=package_dependencies(compiled),
        changes=tuple(compiled.local_changes),
        rules=tuple(sorted(
            (*compiled.inherited_rules, *compiled.local_rules),
            key=lambda rule: (rule.origin_node_id, rule.id),
        )),
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
        topics=tuple(sorted(compiled.local_topics, key=lambda topic: (topic.origin_node_id, topic.id))),
        files=package_file_metadata(files),
        normalized_digest=compiled.normalized_digest,
        package_digest=compiled.package_digest,
    )


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
        "sources": [asdict(source) for source in package.sources],
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
    if root.get("schema") != PACKAGE_SCHEMA:
        raise ContextCanonError(
            f"Unsupported Context package schema in {manifest_path}: {root.get('schema')!r}"
        )

    node = _dict(root.get("node"), "node")
    metadata = NodeMetadata(
        _string(node.get("id"), "node.id"),
        _string(node.get("name"), "node.name"),
        _string(node.get("version"), "node.version"),
    )

    sources = tuple(_parse_dependency(item, index) for index, item in enumerate(_list(root.get("sources"), "sources")))
    _unique((source.id for source in sources), "package Source Node ID")
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

    actual_normalized = semantic_digest(metadata, sources, changes, rules, removed_rules, topics)
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
        changes=tuple(sorted(changes, key=lambda change: (change.target_node_id, change.target_rule_id, change.kind))),
        rules=tuple(sorted(rules, key=lambda rule: (rule.origin_node_id, rule.id))),
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
        topics=tuple(sorted(topics, key=lambda topic: (topic.origin_node_id, topic.id))),
        files=tuple(sorted(files, key=lambda file: file.path)),
        normalized_digest=normalized_digest,
        package_digest=expected_package_digest,
    )


def artifact_files(compiled: CompiledNode) -> dict[str, bytes]:
    """Return the complete immutable package artifact without authoring or harness files."""

    return {
        **package_content_files(compiled),
        PACKAGE_MANIFEST_PATH: compiled.package_manifest.encode("utf-8"),
    }


def _topic_dict(topic: Topic) -> dict[str, Any]:
    item = asdict(topic)
    item["targets"] = sorted(
        item["targets"],
        key=lambda target: (target["intent"], target["kind"], target["locator"]),
    )
    return item


def _read_and_verify_files(package_root: Path, expected: tuple[PackageFile, ...]) -> dict[str, bytes]:
    expected_by_path = {file.path: file for file in expected}
    actual_paths: set[str] = set()
    if (package_root / "CONTEXT.md").is_file():
        actual_paths.add("CONTEXT.md")
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


def _parse_dependency(value: Any, index: int) -> PackageDependency:
    item = _dict(value, f"sources[{index}]")
    return PackageDependency(
        _string(item.get("id"), f"sources[{index}].id"),
        _string(item.get("name"), f"sources[{index}].name"),
        _string(item.get("version"), f"sources[{index}].version"),
        _digest(item.get("normalized_digest"), f"sources[{index}].normalized_digest"),
        _digest(item.get("package_digest"), f"sources[{index}].package_digest"),
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
    return TopicTarget(
        kind=kind,  # type: ignore[arg-type]
        locator=_string(item.get("locator"), f"{label}.locator"),
        intent=intent,  # type: ignore[arg-type]
    )


def _parse_file(value: Any, index: int) -> PackageFile:
    item = _dict(value, f"files[{index}]")
    path = _string(item.get("path"), f"files[{index}].path")
    if path != "CONTEXT.md" and not path.startswith("CONTEXT/"):
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
