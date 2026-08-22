from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, replace
from pathlib import Path

from .links import local_markdown_targets
from .model import CompiledNode, Rule, RuleChange, RuleModification, RuleRemoval
from .parser import ContextCanonError, parse_node
from .render import render_adapters, render_machine_yaml, render_official

COMPILER_VERSION = "0.3.0"


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
            for source in parsed.sources:
                if source.id in seen_source_ids:
                    raise ContextCanonError(
                        f"{node_root}: duplicate Source Node ID {source.id}; each Source may be composed only once"
                    )
                seen_source_ids.add(source.id)
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
                compiled.source_nodes.append(source_node)

            compiled.inherited_rules, compiled.removed_rules = self._compose_inherited_rule_state(
                compiled.source_nodes,
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
            # Topics remain local for now. Inheriting Topic payloads across
            # published Source package boundaries needs an explicit package
            # locator/materialization contract.
            compiled.local_topics = list(parsed.topics)
            compiled.resources = self._collect_resources(compiled)
            compiled.normalized_digest = self._semantic_digest(compiled)
            compiled.official_markdown = render_official(compiled, self.repo_root)
            compiled.package_digest = self._package_digest(compiled.official_markdown, compiled.resources)
            compiled.adapters = render_adapters(compiled)
            compiled.machine_yaml = render_machine_yaml(compiled, self.repo_root, COMPILER_VERSION)
            self._cache[node_root] = compiled
            return compiled
        finally:
            self._active.pop()

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
        source_nodes: list[CompiledNode],
        node_name: str,
    ) -> tuple[list[Rule], list[RuleRemoval]]:
        rules: list[Rule] = []
        removals: list[RuleRemoval] = []
        rules_by_identity: dict[tuple[str, str], Rule] = {}
        removals_by_identity: dict[tuple[str, str], list[RuleRemoval]] = {}

        for source in source_nodes:
            for rule in (*source.inherited_rules, *source.local_rules):
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

    def _collect_resources(self, compiled: CompiledNode) -> dict[str, bytes]:
        seeds: list[Path] = []
        for topic in compiled.local_topics:
            for target in topic.targets:
                if target.kind == "context-node":
                    target_root = (compiled.parsed.root / target.locator).resolve()
                    if target_root.name == "CONTEXT.md":
                        target_root = target_root.parent
                    if not self._is_within_repo(target_root) or not (target_root / "CONTEXT.src.md").is_file():
                        raise ContextCanonError(
                            f"{compiled.metadata.name} Topic {topic.id}: invalid Context Node target {target.locator}"
                        )
                    continue
                source = (compiled.parsed.root / target.locator).resolve()
                self._validate_resource(source, compiled.metadata.name, topic.id, target.locator)
                seeds.append(source)

        resources: dict[str, bytes] = {}
        queue = list(dict.fromkeys(seeds))
        visited: set[Path] = set()
        while queue:
            source = queue.pop(0).resolve()
            if source in visited:
                continue
            visited.add(source)
            rel = source.relative_to(self.repo_root).as_posix()
            published = f"CONTEXT/references/{rel}"
            content = source.read_bytes()
            resources[published] = content

            if source.suffix.lower() == ".md":
                text = content.decode("utf-8")
                for locator in local_markdown_targets(text):
                    linked = (source.parent / locator).resolve()
                    if linked.is_dir():
                        continue
                    self._validate_resource(linked, compiled.metadata.name, f"closure:{rel}", locator)
                    if linked not in visited:
                        queue.append(linked)
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

    def _semantic_digest(self, compiled: CompiledNode) -> str:
        sources = sorted(
            (
                {
                    "id": source.metadata.id,
                    "version": source.metadata.version,
                    "package_digest": source.package_digest,
                }
                for source in compiled.source_nodes
            ),
            key=lambda item: (item["id"], item["version"], item["package_digest"]),
        )
        changes = sorted(
            (asdict(change) for change in compiled.local_changes),
            key=lambda item: (item["target_node_id"], item["target_rule_id"], item["kind"]),
        )
        rules = sorted(
            (asdict(rule) for rule in (*compiled.inherited_rules, *compiled.local_rules)),
            key=lambda item: (item["origin_node_id"], item["id"]),
        )
        removed_rules = sorted(
            (asdict(removal) for removal in compiled.removed_rules),
            key=lambda item: (
                item["origin_node_id"],
                item["rule_id"],
                item["removed_by_node_id"],
                item["removed_by_node_name"],
                item["why"],
            ),
        )
        topics: list[dict] = []
        for topic in compiled.local_topics:
            item = asdict(topic)
            item["targets"] = sorted(
                item["targets"],
                key=lambda target: (target["intent"], target["kind"], target["locator"]),
            )
            topics.append(item)
        topics.sort(key=lambda item: (item["origin_node_id"], item["id"]))

        payload = {
            "node": {
                "id": compiled.metadata.id,
                "name": compiled.metadata.name,
                "version": compiled.metadata.version,
            },
            "sources": sources,
            "changes": changes,
            "rules": rules,
            "removed_rules": removed_rules,
            "topics": topics,
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def _is_within_repo(self, path: Path) -> bool:
        try:
            path.resolve().relative_to(self.repo_root)
            return True
        except ValueError:
            return False

    def _package_digest(self, official: str, resources: dict[str, bytes]) -> str:
        files: dict[str, bytes] = {"CONTEXT.md": official.encode("utf-8"), **resources}
        digest = hashlib.sha256()
        for path, content in sorted(files.items()):
            digest.update(path.encode("utf-8"))
            digest.update(b"\0")
            digest.update(hashlib.sha256(content).digest())
            digest.update(b"\0")
        return digest.hexdigest()


def discover_nodes(repo_root: Path) -> list[Path]:
    repo_root = repo_root.resolve()
    result: list[Path] = []
    for source in repo_root.rglob("CONTEXT.src.md"):
        if any(part in {".git", ".context", "CONTEXT"} for part in source.relative_to(repo_root).parts):
            continue
        result.append(source.parent)
    return sorted(result, key=lambda path: path.relative_to(repo_root).as_posix())
