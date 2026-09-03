from __future__ import annotations

from dataclasses import replace
import hashlib
from pathlib import Path
import re

from .links import local_markdown_targets
from .model import CompiledNode, CompiledPackage, Rule, RuleChange, RuleModification, RuleRemoval, SourceRef, Topic, TopicTarget
from .package import (
    compiled_package,
    load_package,
    package_content_files,
    package_digest,
    render_package_manifest,
    semantic_digest_for_node,
)
from .parser import ContextCanonError, parse_node
from .render import render_adapters, render_machine_yaml, render_official

COMPILER_VERSION = "0.4.0"

CONTEXT_FOLDER_README = """# Generated Context package resources

> [!CAUTION]
> **GENERATED DIRECTORY — DO NOT EDIT THESE FILES.**
> Start with [`../CONTEXT.md`](../CONTEXT.md), the compact Official Context entry for this Node.

This `CONTEXT/` directory exists because the Node has deeper Topic resources that should be available **without loading them into every task**.

## Why `references/` may look like duplicate documentation

`references/` contains exact materialized copies of effective Topic resources. The first path component after `CONTEXT/references/` is the stable origin Node identity (or a deterministic hash when that identity is not path-safe); the remaining path preserves repository-relative source location. This namespace lets inherited Topic resources from independent packages coexist without Source-order precedence.

For example:

```text
nodes/internal/framework-development/docs/architecture.md
        ↓ deterministic materialization
CONTEXT/references/<origin-node-id>/nodes/internal/framework-development/docs/architecture.md
```

The first path is the authored source. The second path is generated package content and is **not another maintenance surface**.

The copy is intentional: it makes the Official Context Package self-contained, so the package can later be published or consumed without needing the original authoring repository layout. In a standalone package the original source path may no longer exist; the materialized copy is what preserves the reviewed resource bytes.

`contextcanon build` refreshes generated package files. `contextcanon check` reports drift when committed generated output no longer matches the authored source and compiler.
"""


class Compiler:
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root.resolve()
        self._cache: dict[Path, CompiledNode] = {}
        self._active: list[Path] = []
        self._node_ids: dict[str, Path] = {}

    def compile(self, node_root: Path) -> CompiledNode:
        node_root = node_root.resolve()
        if node_root in self._cache:
            return self._cache[node_root]
        if node_root in self._active:
            cycle = " -> ".join(str(path) for path in (*self._active, node_root))
            raise ContextCanonError(f"Source dependency cycle: {cycle}")
        self._active.append(node_root)
        try:
            parsed = parse_node(node_root, self.repo_root)
            previous = self._node_ids.get(parsed.metadata.id)
            if previous is not None and previous != node_root:
                raise ContextCanonError(f"Node ID {parsed.metadata.id} is used by both {previous} and {node_root}")
            self._node_ids[parsed.metadata.id] = node_root

            compiled = CompiledNode(parsed=parsed)
            seen_source_ids: set[str] = set()
            source_resource_sets: list[dict[str, bytes]] = []
            for source in parsed.sources:
                if source.id in seen_source_ids:
                    raise ContextCanonError(
                        f"{node_root}: duplicate Source Node ID {source.id}; each Source may be composed only once"
                    )
                seen_source_ids.add(source.id)

                if source.is_pinned:
                    package, package_resources = self._load_pinned_source(node_root, source)
                    compiled.source_packages.append(package)
                    source_resource_sets.append(package_resources)
                    continue

                source_root = self._resolve_source_root(node_root, source.locator)
                source_node = self.compile(source_root)
                if source_node.metadata.id != source.id:
                    raise ContextCanonError(
                        f"{node_root}: Source {source.name} expects Node ID {source.id}, got {source_node.metadata.id}"
                    )
                if source_node.metadata.version != source.version:
                    raise ContextCanonError(
                        f"{node_root}: Source {source.name} expects version {source.version}, got {source_node.metadata.version}"
                    )
                compiled.source_packages.append(compiled_package(source_node))
                source_resource_sets.append({
                    path: content
                    for path, content in source_node.resources.items()
                    if path.startswith("CONTEXT/references/")
                })

            compiled.inherited_rules, compiled.removed_rules = self._compose_inherited_rule_state(
                compiled.source_packages,
                compiled.metadata.name,
            )
            compiled.local_changes = list(parsed.changes)
            compiled.inherited_rules, compiled.removed_rules = self._apply_rule_changes(
                compiled.inherited_rules,
                compiled.removed_rules,
                compiled.local_changes,
                compiled.metadata.id,
                compiled.metadata.name,
            )
            compiled.local_rules = list(parsed.rules)
            self._validate_visible_rule_ids(compiled)

            compiled.inherited_topics = self._compose_inherited_topics(
                compiled.source_packages,
                compiled.metadata.name,
            )
            compiled.local_topics, local_resources = self._compile_local_topics(compiled)
            self._validate_visible_topic_ids(
                compiled.inherited_topics,
                compiled.local_topics,
                compiled.metadata.name,
            )
            compiled.resources = self._collect_resources(
                compiled.metadata.name,
                local_resources,
                source_resource_sets,
            )
            compiled.normalized_digest = semantic_digest_for_node(compiled)
            compiled.official_markdown = render_official(compiled, self.repo_root)
            compiled.package_digest = package_digest(package_content_files(compiled))
            compiled.package_manifest = render_package_manifest(compiled, COMPILER_VERSION)
            compiled.adapters = render_adapters(compiled)
            compiled.machine_yaml = render_machine_yaml(compiled, self.repo_root, COMPILER_VERSION)
            self._cache[node_root] = compiled
            return compiled
        finally:
            self._active.pop()

    def _load_pinned_source(self, node_root: Path, source: SourceRef) -> tuple[CompiledPackage, dict[str, bytes]]:
        if source.normalized_digest is None or source.package_digest is None:
            raise ContextCanonError(f"{node_root}: internal error: pinned Source {source.name} has incomplete digests")

        package_root = node_root / ".context" / "sources" / source.package_digest
        if not package_root.is_dir():
            raise ContextCanonError(
                f"{node_root}: accepted Source package {source.name} is not available locally at "
                f".context/sources/{source.package_digest}; build does not fetch Source packages"
            )

        package = load_package(package_root)
        if package.metadata.id != source.id:
            raise ContextCanonError(
                f"{node_root}: Source {source.name} expects Node ID {source.id}, got {package.metadata.id}"
            )
        if package.metadata.version != source.version:
            raise ContextCanonError(
                f"{node_root}: Source {source.name} expects version {source.version}, got {package.metadata.version}"
            )
        if package.normalized_digest != source.normalized_digest:
            raise ContextCanonError(
                f"{node_root}: Source {source.name} normalized digest mismatch: "
                f"expected {source.normalized_digest}, got {package.normalized_digest}"
            )
        if package.package_digest != source.package_digest:
            raise ContextCanonError(
                f"{node_root}: Source {source.name} package digest mismatch: "
                f"expected {source.package_digest}, got {package.package_digest}"
            )
        resources = {
            file.path: (package_root / file.path).read_bytes()
            for file in package.files
            if file.path.startswith("CONTEXT/references/")
        }
        return package, resources

    def _resolve_source_root(self, node_root: Path, locator: str) -> Path:
        path = (node_root / locator).resolve()
        if path.name == "CONTEXT.md":
            path = path.parent
        if not self._is_within_repo(path):
            raise ContextCanonError(f"Source locator escapes repository: {locator}")
        if not (path / "CONTEXT.src.md").is_file():
            raise ContextCanonError(f"Source locator is not a Context Node root: {locator}")
        return path

    def _compose_inherited_rule_state(
        self,
        source_packages: list[CompiledPackage],
        node_name: str,
    ) -> tuple[list[Rule], list[RuleRemoval]]:
        rules: list[Rule] = []
        removals: list[RuleRemoval] = []
        rules_by_identity: dict[tuple[str, str], Rule] = {}
        removals_by_identity: dict[tuple[str, str], list[RuleRemoval]] = {}

        for source in source_packages:
            for rule in source.rules:
                identity = (rule.origin_node_id, rule.id)
                if identity in removals_by_identity:
                    raise ContextCanonError(
                        f"{node_name}: conflicting inherited Rule {rule.origin_node_name} / {rule.id} "
                        f"({rule.origin_node_id}#{rule.id}) is present through one Source and removed through another"
                    )
                previous = rules_by_identity.get(identity)
                if previous is not None:
                    if previous != rule:
                        raise ContextCanonError(
                            f"{node_name}: conflicting inherited Rule {rule.origin_node_name} / {rule.id} "
                            f"({rule.origin_node_id}#{rule.id}) arrives through multiple Sources with "
                            "different effective definitions or provenance"
                        )
                    continue
                rules_by_identity[identity] = rule
                rules.append(rule)

            for removal in source.removed_rules:
                identity = (removal.origin_node_id, removal.rule_id)
                if identity in rules_by_identity:
                    raise ContextCanonError(
                        f"{node_name}: conflicting inherited Rule {removal.origin_node_name} / {removal.rule_id} "
                        f"({removal.origin_node_id}#{removal.rule_id}) is present through one Source and removed through another"
                    )
                bucket = removals_by_identity.setdefault(identity, [])
                if removal not in bucket:
                    bucket.append(removal)
                    removals.append(removal)

        removals.sort(
            key=lambda removal: (
                removal.origin_node_id,
                removal.rule_id,
                removal.removed_by_node_id,
                removal.removed_by_node_name,
                removal.why,
            )
        )
        return rules, removals

    def _apply_rule_changes(
        self,
        inherited_rules: list[Rule],
        inherited_removals: list[RuleRemoval],
        changes: list[RuleChange],
        node_id: str,
        node_name: str,
    ) -> tuple[list[Rule], list[RuleRemoval]]:
        rules = list(inherited_rules)
        removals = list(inherited_removals)
        for change in changes:
            identity = (change.target_node_id, change.target_rule_id)
            index = next(
                (
                    i
                    for i, rule in enumerate(rules)
                    if (rule.origin_node_id, rule.id) == identity
                ),
                None,
            )
            if index is None:
                raise ContextCanonError(
                    f"{node_name}: {change.kind.title()} targets missing inherited Rule "
                    f"{change.target_node_name} / {change.target_rule_id} "
                    f"({change.target_node_id}#{change.target_rule_id})"
                )
            target = rules[index]
            if change.kind == "remove":
                rules.pop(index)
                removals.append(
                    RuleRemoval(
                        origin_node_id=target.origin_node_id,
                        origin_node_name=target.origin_node_name,
                        rule_id=target.id,
                        removed_by_node_id=node_id,
                        removed_by_node_name=node_name,
                        why=change.why,
                    )
                )
                continue

            if change.statement is None:
                raise ContextCanonError(
                    f"{node_name}: Override for {change.target_node_name} / {change.target_rule_id} "
                    "has no replacement statement"
                )
            modification = RuleModification("override", node_id, node_name, change.why)
            rules[index] = replace(
                target,
                statement=change.statement,
                modifications=(*target.modifications, modification),
            )
        return rules, removals

    def _validate_visible_rule_ids(self, compiled: CompiledNode) -> None:
        seen: dict[str, Rule] = {}
        for rule in (*compiled.inherited_rules, *compiled.local_rules):
            if rule.id in seen and seen[rule.id].origin_node_id != rule.origin_node_id:
                raise ContextCanonError(
                    f"Visible Rule ID collision in {compiled.metadata.name}: {rule.id} comes from multiple Nodes"
                )
            seen[rule.id] = rule

    @staticmethod
    def _topic_target_key(target: TopicTarget) -> tuple[str, str, str, str, str]:
        return (
            target.intent,
            target.kind,
            target.locator,
            target.target_node_id or "",
            target.target_node_name or "",
        )

    def _topics_equivalent(self, left: Topic, right: Topic) -> bool:
        return (
            left.id == right.id
            and left.title == right.title
            and left.condition == right.condition
            and left.origin_node_id == right.origin_node_id
            and left.origin_node_name == right.origin_node_name
            and sorted(left.targets, key=self._topic_target_key)
            == sorted(right.targets, key=self._topic_target_key)
        )

    def _validate_package_topics(self, package: CompiledPackage, node_name: str) -> None:
        package_files = {file.path for file in package.files}
        for topic in package.topics:
            for target in topic.targets:
                if target.kind == "resource":
                    if not target.locator.startswith("CONTEXT/references/") or target.locator not in package_files:
                        raise ContextCanonError(
                            f"{node_name}: Source package {package.metadata.name} Topic {topic.id} uses a legacy/non-portable Resource target {target.locator!r}; republish that Source with package-safe Topic targets before inheritance"
                        )
                    continue
                if not target.target_node_id or not target.target_node_name:
                    raise ContextCanonError(
                        f"{node_name}: Source package {package.metadata.name} Topic {topic.id} lacks stable Context Node target identity; republish that Source before Topic inheritance"
                    )

    def _validate_inherited_resource_files(self, source_packages: list[CompiledPackage], node_name: str) -> None:
        seen: dict[str, tuple[str, int, str]] = {}
        for package in source_packages:
            for file in package.files:
                if not file.path.startswith("CONTEXT/references/"):
                    continue
                current = (file.sha256, file.size, package.metadata.name)
                previous = seen.get(file.path)
                if previous is None:
                    seen[file.path] = current
                    continue
                if previous[:2] != current[:2]:
                    raise ContextCanonError(
                        f"{node_name}: conflicting inherited Topic Resource {file.path} arrives through {previous[2]} and {package.metadata.name} with different exact bytes"
                    )

    def _compose_inherited_topics(self, source_packages: list[CompiledPackage], node_name: str) -> list[Topic]:
        self._validate_inherited_resource_files(source_packages, node_name)
        result: list[Topic] = []
        by_identity: dict[tuple[str, str], Topic] = {}
        for package in source_packages:
            self._validate_package_topics(package, node_name)
            for topic in package.topics:
                identity = (topic.origin_node_id, topic.id)
                previous = by_identity.get(identity)
                if previous is not None:
                    if not self._topics_equivalent(previous, topic):
                        raise ContextCanonError(
                            f"{node_name}: conflicting inherited Topic {topic.origin_node_name} / {topic.id} ({topic.origin_node_id}#{topic.id}) arrives through multiple Sources with different effective definitions"
                        )
                    continue
                by_identity[identity] = topic
                result.append(topic)
        return result

    def _validate_visible_topic_ids(self, inherited: list[Topic], local: list[Topic], node_name: str) -> None:
        seen: dict[str, Topic] = {}
        for topic in (*inherited, *local):
            previous = seen.get(topic.id)
            if previous is not None and previous.origin_node_id != topic.origin_node_id:
                raise ContextCanonError(
                    f"Visible Topic ID collision in {node_name}: {topic.id} comes from multiple Nodes"
                )
            seen[topic.id] = topic

    @staticmethod
    def _resource_namespace(node_id: str) -> str:
        if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", node_id):
            return node_id
        return "sha256-" + hashlib.sha256(node_id.encode("utf-8")).hexdigest()

    def _resource_closure(self, seed: Path, node_name: str, topic_id: str, locator: str) -> list[Path]:
        self._validate_resource(seed, node_name, topic_id, locator)
        queue = [seed.resolve()]
        visited: set[Path] = set()
        result: list[Path] = []
        while queue:
            source = queue.pop(0).resolve()
            if source in visited:
                continue
            visited.add(source)
            result.append(source)
            content = source.read_bytes()
            if source.suffix.lower() != ".md":
                continue
            text = content.decode("utf-8")
            rel = source.relative_to(self.repo_root).as_posix()
            for linked_locator in local_markdown_targets(text):
                linked = (source.parent / linked_locator).resolve()
                if linked.is_dir():
                    continue
                self._validate_resource(linked, node_name, f"closure:{rel}", linked_locator)
                if linked not in visited:
                    queue.append(linked)
        return result

    def _compile_local_topics(self, compiled: CompiledNode) -> tuple[list[Topic], dict[str, bytes]]:
        effective: list[Topic] = []
        resources: dict[str, bytes] = {}
        namespace = self._resource_namespace(compiled.metadata.id)
        for topic in compiled.parsed.topics:
            targets: list[TopicTarget] = []
            for target in topic.targets:
                if target.kind == "resource":
                    seed = (compiled.parsed.root / target.locator).resolve()
                    closure = self._resource_closure(seed, compiled.metadata.name, topic.id, target.locator)
                    for source in closure:
                        rel = source.relative_to(self.repo_root).as_posix()
                        published = f"CONTEXT/references/{namespace}/{rel}"
                        content = source.read_bytes()
                        previous = resources.get(published)
                        if previous is not None and previous != content:
                            raise ContextCanonError(
                                f"{compiled.metadata.name}: local Topic Resource collision at {published}"
                            )
                        resources[published] = content
                    seed_rel = seed.relative_to(self.repo_root).as_posix()
                    targets.append(
                        TopicTarget(
                            kind="resource",
                            locator=f"CONTEXT/references/{namespace}/{seed_rel}",
                            intent=target.intent,
                        )
                    )
                    continue

                target_root = (compiled.parsed.root / target.locator).resolve()
                if target_root.name == "CONTEXT.md":
                    target_root = target_root.parent
                if not self._is_within_repo(target_root) or not (target_root / "CONTEXT.src.md").is_file():
                    raise ContextCanonError(
                        f"{compiled.metadata.name} Topic {topic.id}: invalid Context Node target {target.locator}"
                    )
                target_node = parse_node(target_root, self.repo_root)
                targets.append(
                    TopicTarget(
                        kind="context-node",
                        locator=target.locator,
                        intent=target.intent,
                        target_node_id=target_node.metadata.id,
                        target_node_name=target_node.metadata.name,
                    )
                )
            effective.append(replace(topic, targets=tuple(targets)))
        return effective, resources

    def _collect_resources(
        self,
        node_name: str,
        local_resources: dict[str, bytes],
        source_resource_sets: list[dict[str, bytes]],
    ) -> dict[str, bytes]:
        resources = dict(local_resources)
        for inherited in source_resource_sets:
            for path, content in inherited.items():
                previous = resources.get(path)
                if previous is not None and previous != content:
                    raise ContextCanonError(
                        f"{node_name}: conflicting inherited Topic Resource bytes at {path}"
                    )
                resources[path] = content
        if resources:
            resources["CONTEXT/README.md"] = CONTEXT_FOLDER_README.encode("utf-8")
        return dict(sorted(resources.items()))

    def _validate_resource(self, source: Path, node_name: str, topic_id: str, locator: str) -> None:
        if not self._is_within_repo(source):
            raise ContextCanonError(
                f"{node_name} Topic {topic_id}: resource escapes repository: {locator}"
            )
        if not source.is_file():
            raise ContextCanonError(
                f"{node_name} Topic {topic_id}: missing resource: {locator}"
            )

    def _is_within_repo(self, path: Path) -> bool:
        try:
            path.resolve().relative_to(self.repo_root)
            return True
        except ValueError:
            return False


def discover_nodes(repo_root: Path) -> list[Path]:
    repo_root = repo_root.resolve()
    result: list[Path] = []
    for source in repo_root.rglob("CONTEXT.src.md"):
        if any(part in {".git", ".context", "CONTEXT"} for part in source.relative_to(repo_root).parts):
            continue
        result.append(source.parent)
    return sorted(result, key=lambda path: path.relative_to(repo_root).as_posix())
