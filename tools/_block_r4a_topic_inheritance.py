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


def activate_plan() -> None:
    p = Path("PLAN.md")
    text = p.read_text(encoding="utf-8")
    old_status = "**Status: NEXT — Blocks R1/R2/R3 complete; continue with semantic parent composition and Source-update UX. Fast-run remains ACTIVE.**"
    new_status = """**Status: ACTIVE — Block R4a effective Topic inheritance and package-safe Resource composition. Fast-run remains ACTIVE.**

R4a purpose: make Topics package semantics just like effective Rules before adding the distinct accepted Parent relationship. Local Topic targets are compiled into portable targets; Resource materialization is namespaced by stable origin Node identity so Source packages can be merged transitively without filesystem-path collisions, while Context-Node targets carry stable target identity across package boundaries.

R4a verification: focused compiler/package/external-Source/diff regressions first, then the complete deterministic suite plus self-hosted build/check and hygiene before the clean checkpoint."""
    if old_status not in text:
        raise SystemExit("PLAN.md: R1-R3 completion marker not found")
    text = text.replace(old_status, new_status, 1)
    text = text.replace(
        "R3 verification: focused source-audit, placement-review and reset regressions first, then the complete deterministic suite plus self-hosted build/check and hygiene before the clean checkpoint.",
        "R3 verification: focused source-audit/placement-review/reset regressions passed, followed by the complete deterministic suite (167 tests), self-hosted build/check and `git diff --check`. The clean product checkpoint removed every temporary R3 harness file.",
        1,
    )
    p.write_text(text, encoding="utf-8")


def patch_model() -> None:
    replace_once(
        "src/contextcanon/model.py",
        '''@dataclass(frozen=True)
class TopicTarget:
    kind: TargetKind
    locator: str
    intent: TargetIntent
''',
        '''@dataclass(frozen=True)
class TopicTarget:
    kind: TargetKind
    locator: str
    intent: TargetIntent
    target_node_id: str | None = None
    target_node_name: str | None = None
''',
    )
    replace_once(
        "src/contextcanon/model.py",
        '''    local_changes: list[RuleChange] = field(default_factory=list)
    local_topics: list[Topic] = field(default_factory=list)
''',
        '''    local_changes: list[RuleChange] = field(default_factory=list)
    inherited_topics: list[Topic] = field(default_factory=list)
    local_topics: list[Topic] = field(default_factory=list)
''',
    )


def patch_package() -> None:
    replace_once(
        "src/contextcanon/package.py",
        '''        compiled.removed_rules,
        compiled.local_topics,
    )
''',
        '''        compiled.removed_rules,
        (*compiled.inherited_topics, *compiled.local_topics),
    )
''',
    )
    replace_once(
        "src/contextcanon/package.py",
        '''        topics=tuple(compiled.local_topics),
''',
        '''        topics=tuple((*compiled.inherited_topics, *compiled.local_topics)),
''',
    )
    replace_once(
        "src/contextcanon/package.py",
        '''def _topic_dict(topic: Topic) -> dict[str, Any]:
    item = asdict(topic)
    item["targets"] = sorted(
        item["targets"],
        key=lambda target: (target["intent"], target["kind"], target["locator"]),
    )
    return item
''',
        '''def _topic_dict(topic: Topic) -> dict[str, Any]:
    item = asdict(topic)
    targets: list[dict[str, Any]] = []
    for target in item["targets"]:
        targets.append({key: value for key, value in target.items() if value is not None})
    item["targets"] = sorted(
        targets,
        key=lambda target: (
            target["intent"], target["kind"], target["locator"],
            target.get("target_node_id", ""), target.get("target_node_name", ""),
        ),
    )
    return item
''',
    )
    replace_once(
        "src/contextcanon/package.py",
        '''    return TopicTarget(
        kind=kind,  # type: ignore[arg-type]
        locator=_string(item.get("locator"), f"{label}.locator"),
        intent=intent,  # type: ignore[arg-type]
    )
''',
        '''    target_node_id = item.get("target_node_id")
    target_node_name = item.get("target_node_name")
    if target_node_id is not None and not isinstance(target_node_id, str):
        raise ContextCanonError(f"Invalid {label}.target_node_id: expected string or null")
    if target_node_name is not None and not isinstance(target_node_name, str):
        raise ContextCanonError(f"Invalid {label}.target_node_name: expected string or null")
    if (target_node_id is None) != (target_node_name is None):
        raise ContextCanonError(f"Invalid {label}: target_node_id and target_node_name must appear together")
    return TopicTarget(
        kind=kind,  # type: ignore[arg-type]
        locator=_string(item.get("locator"), f"{label}.locator"),
        intent=intent,  # type: ignore[arg-type]
        target_node_id=target_node_id,
        target_node_name=target_node_name,
    )
''',
    )


def patch_compiler() -> None:
    replace_once(
        "src/contextcanon/compiler.py",
        "from dataclasses import replace\nfrom pathlib import Path\n",
        "from dataclasses import replace\nimport hashlib\nfrom pathlib import Path\nimport re\n",
    )
    replace_once(
        "src/contextcanon/compiler.py",
        "from .model import CompiledNode, CompiledPackage, Rule, RuleChange, RuleModification, RuleRemoval, SourceRef\n",
        "from .model import CompiledNode, CompiledPackage, Rule, RuleChange, RuleModification, RuleRemoval, SourceRef, Topic, TopicTarget\n",
    )
    old = '''            compiled = CompiledNode(parsed=parsed)
            seen_source_ids: set[str] = set()
            for source in parsed.sources:
                if source.id in seen_source_ids:
                    raise ContextCanonError(
                        f"{node_root}: duplicate Source Node ID {source.id}; each Source may be composed only once"
                    )
                seen_source_ids.add(source.id)

                if source.is_pinned:
                    compiled.source_packages.append(self._load_pinned_source(node_root, source))
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
            # Topics remain local for now. Inheriting Topic payloads across
            # published Source package boundaries needs an explicit package
            # locator/materialization contract.
            compiled.local_topics = list(parsed.topics)
            compiled.resources = self._collect_resources(compiled)
'''
    new = '''            compiled = CompiledNode(parsed=parsed)
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
'''
    replace_once("src/contextcanon/compiler.py", old, new)
    replace_once(
        "src/contextcanon/compiler.py",
        '''    def _load_pinned_source(self, node_root: Path, source: SourceRef) -> CompiledPackage:
''',
        '''    def _load_pinned_source(self, node_root: Path, source: SourceRef) -> tuple[CompiledPackage, dict[str, bytes]]:
''',
    )
    replace_once(
        "src/contextcanon/compiler.py",
        '''        if package.package_digest != source.package_digest:
            raise ContextCanonError(
                f"{node_root}: Source {source.name} package digest mismatch: "
                f"expected {source.package_digest}, got {package.package_digest}"
            )
        return package
''',
        '''        if package.package_digest != source.package_digest:
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
''',
    )

    start = '''    def _collect_resources(self, compiled: CompiledNode) -> dict[str, bytes]:
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

        if resources:
            resources["CONTEXT/README.md"] = CONTEXT_FOLDER_README.encode("utf-8")
        return dict(sorted(resources.items()))
'''
    replacement = '''    @staticmethod
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
'''
    replace_once("src/contextcanon/compiler.py", start, replacement)

    replace_once(
        "src/contextcanon/compiler.py",
        '''`references/` contains exact materialized copies of authored Topic resources. The path after `CONTEXT/references/` preserves the resource's repository-relative source path at build time.
''',
        '''`references/` contains exact materialized copies of effective Topic resources. The first path component after `CONTEXT/references/` is the stable origin Node identity (or a deterministic hash when that identity is not path-safe); the remaining path preserves repository-relative source location. This namespace lets inherited Topic resources from independent packages coexist without Source-order precedence.
''',
    )
    replace_once(
        "src/contextcanon/compiler.py",
        '''CONTEXT/references/nodes/internal/framework-development/docs/architecture.md
''',
        '''CONTEXT/references/<origin-node-id>/nodes/internal/framework-development/docs/architecture.md
''',
    )


def patch_render() -> None:
    replace_once(
        "src/contextcanon/render.py",
        "import json\nimport os\nfrom pathlib import Path\n",
        "import hashlib\nimport json\nimport os\nfrom pathlib import Path\nimport re\n",
    )
    old = '''def render_official(compiled: CompiledNode, repo_root: Path) -> str:
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
'''
    new = '''def render_official(compiled: CompiledNode, repo_root: Path) -> str:
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
        lines.extend(["## Local Rules" if compiled.source_packages else "## Rules", ""])
        _append_rules(lines, compiled.local_rules)
    elif not compiled.inherited_rules:
        lines.extend(["This Node defines no Rules.", ""])

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
        lines.extend(["## Local Topics" if compiled.source_packages else "## Topics", ""])
        _append_topics(lines, compiled.local_topics, compiled, repo_root)
    return "\n".join(lines).rstrip() + "\n"
'''
    replace_once("src/contextcanon/render.py", old, new)

    old_target = '''def _render_target(compiled: CompiledNode, target, repo_root: Path) -> tuple[str, str]:
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
'''
    new_target = '''def _append_topics(lines: list[str], topics, compiled: CompiledNode, repo_root: Path) -> None:
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
'''
    replace_once("src/contextcanon/render.py", old_target, new_target)

    replace_once(
        "src/contextcanon/render.py",
        '''    lines.extend(["", "# Compiled Rule view with provenance plus the local Topic index.", "official:"])
''',
        '''    lines.extend(["", "# Compiled effective Rule/Topic view with provenance.", "official:"])
''',
    )
    replace_once(
        "src/contextcanon/render.py",
        '''    lines.append("  topic_ids: " + q([topic.id for topic in compiled.local_topics]))
''',
        '''    effective_topics = [*compiled.inherited_topics, *compiled.local_topics]
    lines.append("  topic_ids: " + q([topic.id for topic in effective_topics]))
''',
    )
    replace_once(
        "src/contextcanon/render.py",
        '''    targets = [(topic, target) for topic in compiled.local_topics for target in topic.targets]
''',
        '''    targets = [(topic, target) for topic in effective_topics for target in topic.targets]
''',
    )
    replace_once(
        "src/contextcanon/render.py",
        '''                f"    locator: {q(target.locator)}",
            ])
''',
        '''                f"    locator: {q(target.locator)}",
                f"    target_node_id: {q(target.target_node_id) if target.target_node_id else 'null'}",
                f"    target_node_name: {q(target.target_node_name) if target.target_node_name else 'null'}",
            ])
''',
    )
    old_resources = '''    if compiled.resources:
        lines.append("resources:")
        for published in compiled.resources:
            repo_rel = published.removeprefix("CONTEXT/references/")
            source_abs = repo_root / repo_rel
            source_rel = os.path.relpath(source_abs, compiled.parsed.root).replace(os.sep, "/")
            lines.append("  - " + q({"source": source_rel, "published": published}))
    else:
        lines.append("resources: []")
'''
    new_resources = '''    published_resources = [path for path in compiled.resources if path != "CONTEXT/README.md"]
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
'''
    replace_once("src/contextcanon/render.py", old_resources, new_resources)


def patch_diff_and_sources() -> None:
    replace_once(
        "src/contextcanon/diff.py",
        '''    for topic in compiled.local_topics:
''',
        '''    for topic in (*compiled.inherited_topics, *compiled.local_topics):
''',
    )
    replace_once(
        "src/contextcanon/sources.py",
        '''    seen: dict[str, Rule] = {}
    for rule in (*inherited, *compiled.local_rules):
        previous = seen.get(rule.id)
        if previous is not None and previous.origin_node_id != rule.origin_node_id:
            raise ContextCanonError(
                f"Visible Rule ID collision in {compiled.metadata.name}: {rule.id} comes from multiple Nodes"
            )
        seen[rule.id] = rule
''',
        '''    seen: dict[str, Rule] = {}
    for rule in (*inherited, *compiled.local_rules):
        previous = seen.get(rule.id)
        if previous is not None and previous.origin_node_id != rule.origin_node_id:
            raise ContextCanonError(
                f"Visible Rule ID collision in {compiled.metadata.name}: {rule.id} comes from multiple Nodes"
            )
        seen[rule.id] = rule

    inherited_topics = compiler._compose_inherited_topics(packages, compiled.metadata.name)
    compiler._validate_visible_topic_ids(inherited_topics, compiled.local_topics, compiled.metadata.name)
''',
    )


def patch_tests() -> None:
    p = Path("tests/test_walking_skeleton.py")
    text = p.read_text(encoding="utf-8")
    old = '''        self.assertEqual([topic.id for topic in node.local_topics], ["D-ARCH"])
        self.assertEqual(
            list(node.resources),
            [
                "CONTEXT/README.md",
                "CONTEXT/references/docs/architecture.md",
                "CONTEXT/references/docs/authoring.md",
                "CONTEXT/references/docs/details.md",
            ],
        )
'''
    new = '''        self.assertEqual([topic.id for topic in node.inherited_topics], ["F-AUTH"])
        self.assertEqual([topic.id for topic in node.local_topics], ["D-ARCH"])
        self.assertEqual(
            list(node.resources),
            [
                "CONTEXT/README.md",
                "CONTEXT/references/node-development/docs/architecture.md",
                "CONTEXT/references/node-development/docs/authoring.md",
                "CONTEXT/references/node-development/docs/details.md",
                "CONTEXT/references/node-foundation/docs/authoring.md",
                "CONTEXT/references/node-foundation/docs/details.md",
            ],
        )
'''
    if old not in text:
        raise SystemExit("walking skeleton compile expectation anchor missing")
    text = text.replace(old, new, 1)
    text = text.replace(
        '        self.assertIn("Rules from Demo Foundation", node.official_markdown)\n',
        '        self.assertIn("Rules from Demo Foundation", node.official_markdown)\n        self.assertIn("Topics from Demo Foundation", node.official_markdown)\n        self.assertIn("CONTEXT/references/node-foundation/docs/authoring.md", node.official_markdown)\n',
        1,
    )
    text = text.replace(
        '''        self.assertEqual([removal.rule_id for removal in node.removed_rules], ["F-002"])
        self.assertIn("## Rules from Demo Foundation", node.official_markdown)
''',
        '''        self.assertEqual([removal.rule_id for removal in node.removed_rules], ["F-002"])
        self.assertEqual([topic.id for topic in node.inherited_topics], ["F-AUTH", "D-ARCH"])
        self.assertIn("## Rules from Demo Foundation", node.official_markdown)
        self.assertIn("## Topics from Demo Foundation", node.official_markdown)
        self.assertIn("## Topics from Demo Development", node.official_markdown)
''',
        1,
    )
    text = text.replace(
        '''        node = Compiler(repo).compile(consumer)
        self.assertEqual([rule.id for rule in node.inherited_rules], ["F-001", "F-002"])
''',
        '''        node = Compiler(repo).compile(consumer)
        self.assertEqual([rule.id for rule in node.inherited_rules], ["F-001", "F-002"])
        self.assertEqual([topic.id for topic in node.inherited_topics], ["F-AUTH"])
''',
        1,
    )
    collision_test = r'''
    def test_visible_topic_id_collision_from_different_origins_fails(self):
        repo = self.make_repo()
        for name in ("left", "right"):
            node = repo / f"nodes/internal/{name}"
            node.mkdir(parents=True)
            (node / "CONTEXT.src.md").write_text(
                f'''# Demo {name.title()} — Local Context Source
<!-- ctx:node id="node-{name}" version="0.1.0" -->

## Topics

### Shared label

When testing {name}:

Required:
- Resource: `../../../docs/authoring.md`
<!-- ctx:topic id="SHARED-TOPIC" -->
''',
                encoding="utf-8",
            )
        consumer = repo / "nodes/internal/topic-consumer"
        consumer.mkdir(parents=True)
        (consumer / "CONTEXT.src.md").write_text(
            '''# Topic Consumer — Local Context Source
<!-- ctx:node id="node-topic-consumer" version="0.1.0" -->

## Sources

- [Left](../left/) — `0.1.0`
  <!-- ctx:source id="node-left" version="0.1.0" -->
- [Right](../right/) — `0.1.0`
  <!-- ctx:source id="node-right" version="0.1.0" -->
''',
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ContextCanonError, "Visible Topic ID collision"):
            Compiler(repo).compile(consumer)

'''
    anchor = "    def test_conflicting_diamond_rule_fails_without_source_precedence(self):\n"
    if collision_test.strip() not in text:
        if anchor not in text:
            raise SystemExit("walking skeleton collision insertion anchor missing")
        text = text.replace(anchor, collision_test + anchor, 1)
    p.write_text(text, encoding="utf-8")

    p = Path("tests/test_package.py")
    text = p.read_text(encoding="utf-8")
    text = text.replace(
        '        self.assertIn("CONTEXT/references/docs/team-guide.md", [file.path for file in loaded.files])\n',
        '        self.assertIn("CONTEXT/references/node-team/docs/team-guide.md", [file.path for file in loaded.files])\n',
        1,
    )
    text = text.replace(
        '        (artifact / "CONTEXT/references/docs/team-guide.md").unlink()\n',
        '        (artifact / "CONTEXT/references/node-team/docs/team-guide.md").unlink()\n',
        1,
    )
    p.write_text(text, encoding="utf-8")

    p = Path("tests/test_external_sources.py")
    text = p.read_text(encoding="utf-8")
    text = text.replace(
        '''- **Use explicit Python:** Prefer explicit, deterministic Python over hidden magic.
  Why: Consumers need predictable implementation behavior.
  <!-- ctx:rule id="PY-001" -->
''',
        '''- **Use explicit Python:** Prefer explicit, deterministic Python over hidden magic.
  Why: Consumers need predictable implementation behavior.
  <!-- ctx:rule id="PY-001" -->

## Topics

### Python guide

When changing Python implementation details:

Required:
- Resource: `guide.md`
<!-- ctx:topic id="PY-GUIDE" -->
''',
        1,
    )
    text = text.replace(
        '        (root / "CONTEXT.src.md").write_text(SOURCE, encoding="utf-8")\n',
        '        (root / "CONTEXT.src.md").write_text(SOURCE, encoding="utf-8")\n        (root / "guide.md").write_text("# Python Guide\\n\\nKeep implementation explicit.\\n", encoding="utf-8")\n',
        1,
    )
    text = text.replace(
        '''        self.assertIn("Rules from Shared Python Development", compiled.official_markdown)
''',
        '''        self.assertEqual([topic.id for topic in compiled.inherited_topics], ["PY-GUIDE"])
        self.assertIn("CONTEXT/references/node-python/guide.md", compiled.resources)
        self.assertEqual(compiled.resources["CONTEXT/references/node-python/guide.md"], b"# Python Guide\n\nKeep implementation explicit.\n")
        self.assertIn("Rules from Shared Python Development", compiled.official_markdown)
        self.assertIn("Topics from Shared Python Development", compiled.official_markdown)
''',
        1,
    )
    p.write_text(text, encoding="utf-8")


def patch_docs() -> None:
    replace_once(
        "nodes/library/foundation/docs/source-format.md",
        '''`Resource` targets are materialized into the generated `CONTEXT/` package. `Context Node` targets point to another node root and remain navigation rather than Source composition.
''',
        '''`Resource` targets are materialized into the generated `CONTEXT/` package. Compiled Resource targets use an origin-Node namespace under `CONTEXT/references/`, so effective Topics can cross Source package boundaries without unrelated repositories colliding on paths. `Context Node` targets remain navigation rather than Source composition; compiled packages carry the stable target Node identity so inherited navigation remains meaningful even when the original repository-relative link is unavailable.

Topics compose transitively through accepted Sources just like effective Rules. A consuming Node renders inherited and local Topics together, while State/Plan/Overview remain local-only. Resource bytes from multiple Source paths are deduplicated only when the same origin-qualified package path has identical content; different bytes at that stable path are a structural conflict rather than Source-order precedence.
''',
    )
    replace_once(
        "nodes/library/foundation/docs/composition.md",
        '''## Navigation is not composition
''',
        '''## Topics and Resources compose transitively

A Source package carries its complete effective Topic set, not only the Topics authored directly in that Source. Resource targets are compiled to package-safe paths namespaced by the Topic's stable origin Node identity. Descendants therefore inherit both Topic conditions and the exact materialized Resource closure without consulting the Source repository.

When the same inherited Topic identity reaches a Node through several Source paths, equivalent Topic definitions are deduplicated. If their effective definitions differ, compilation fails. Origin-qualified Resource paths behave the same way: identical bytes deduplicate, while different bytes at the same stable inherited path are a structural conflict.

`Context Node` Topic targets remain navigation rather than composition. Packages preserve the stable target Node ID/name so an inherited Topic can still explain where it points; a consumer does not invent a local link when that target Node is not materialized in the consumer package.

## Navigation is not composition
''',
    )
    replace_once(
        "nodes/internal/framework-development/docs/compiler.md",
        '''- transitive Rule composition, Remove/Override, provenance, dangling diagnostics, and diamond conflicts;
- Required/Optional Topics and materialized Resource closure;
''',
        '''- transitive Rule composition, Remove/Override, provenance, dangling diagnostics, and diamond conflicts;
- transitive Topic composition with stable origin identity, package-safe Context-Node target identity, and deterministic diamond conflict handling;
- Required/Optional Topics and origin-namespaced materialized Resource closure across Source package boundaries;
''',
    )
    replace_once(
        "nodes/internal/framework-development/docs/compiler.md",
        '''- Topic composition/materialization across Source package boundaries;
- protected Rules and authorized exceptions;
''',
        '''- protected Rules and authorized exceptions;
''',
    )
    replace_once(
        "nodes/internal/framework-development/docs/architecture.md",
        '''Other later deterministic capabilities include protected Rules and authorized exceptions, Topic composition/materialization across Source package boundaries, richer resource-collision policy, and broader repository-boundary diagnostics.
''',
        '''Other later deterministic capabilities include protected Rules and authorized exceptions, richer resource-collision policy beyond the current stable-origin exact-byte rule, and broader repository-boundary diagnostics. Effective Topics and their Resource closures now compose across Source package boundaries without parsing generated Markdown.
''',
    )


def complete() -> None:
    p = Path("PLAN.md")
    text = p.read_text(encoding="utf-8")
    active = "**Status: ACTIVE — Block R4a effective Topic inheritance and package-safe Resource composition. Fast-run remains ACTIVE.**"
    done = "**Status: NEXT — Blocks R1-R4a complete; next persist the accepted Step-03 Parent relationship as an exact package edge. Fast-run remains ACTIVE.**"
    if active not in text:
        raise SystemExit("PLAN.md: active R4a marker missing")
    text = text.replace(active, done, 1)
    text = text.replace(
        "R4a verification: focused compiler/package/external-Source/diff regressions first, then the complete deterministic suite plus self-hosted build/check and hygiene before the clean checkpoint.",
        "R4a verification: focused compiler/package/external-Source/diff regressions passed, followed by the complete deterministic suite, self-hosted build/check and `git diff --check`. Effective Topics now survive immutable package round-trips and pinned offline Source composition together with exact origin-namespaced Resource bytes.",
        1,
    )
    text = text.replace(
        "- [ ] Extend compiled inheritance from Rules to Topics. Today Rules compose transitively, while Topics are intentionally local-only; define package locator/resource semantics so accepted Parent/Source Topics and their Resources can be rendered safely in the Child.",
        "- [x] Extend compiled inheritance from Rules to Topics. Today Rules compose transitively, while Topics are intentionally local-only; define package locator/resource semantics so accepted Parent/Source Topics and their Resources can be rendered safely in the Child.",
        1,
    )
    text = text.replace(
        "- [ ] Render each Node's `CONTEXT.md` as the complete effective working context: all effective inherited + local Rules and all effective inherited + local Topics, with provenance and accepted-package boundaries preserved.",
        "- [x] Render each Node's `CONTEXT.md` as the complete effective working context: all effective inherited + local Rules and all effective inherited + local Topics, with provenance and accepted-package boundaries preserved.",
        1,
    )
    p.write_text(text, encoding="utf-8")

    state = Path("STATE.md")
    current = state.read_text(encoding="utf-8").rstrip()
    block = '''

## Latest Block R4a effective-Topic package checkpoint

Topics are now effective transitive package semantics rather than local-only presentation. The compiler turns local Resource targets into origin-Node-namespaced package paths and carries stable Context-Node target identity in compiled Topic targets. `CompiledPackage.topics` therefore contains inherited plus local Topics, and descendants can compose them without parsing generated `CONTEXT.md` or consulting the Source repository.

Inherited Resource trees use `CONTEXT/references/<origin-node-id>/...` (with deterministic hashing only for path-unsafe IDs). This makes the collision rule structural and Source-order-free: the same stable origin path with identical bytes deduplicates through diamonds; different bytes at that path fail compilation/review. Pinned external Source packages can now provide Topics and Resources entirely offline. Official `CONTEXT.md` renders inherited Topics grouped by origin alongside local Topics; inherited Context-Node navigation shows the stable target identity when no consumer-local link can safely be promised.

This deliberately precedes the Parent relationship itself. The next Block R slice can now model an accepted semantic Parent as a distinct exact package edge while reusing the already-general Rule/Topic composition machinery. Fast-run remains active; PR #13 remains draft and unmerged.
'''
    state.write_text(current + block.rstrip() + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--complete", action="store_true")
    args = parser.parse_args()
    if args.complete:
        complete()
        return
    activate_plan()
    patch_model()
    patch_package()
    patch_compiler()
    patch_render()
    patch_diff_and_sources()
    patch_tests()
    patch_docs()


if __name__ == "__main__":
    main()
