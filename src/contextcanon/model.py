from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

TargetKind = Literal["resource", "context-node"]
TargetIntent = Literal["required", "optional"]
ChangeKind = Literal["remove", "override"]


@dataclass(frozen=True)
class NodeMetadata:
    id: str
    name: str
    version: str
    adapters: tuple[str, ...] = ()


@dataclass(frozen=True)
class SourceRef:
    id: str
    name: str
    version: str
    locator: str
    normalized_digest: str | None = None
    package_digest: str | None = None
    transport: str | None = None
    transport_ref: str | None = None
    node_path: str | None = None
    why: str | None = None

    @property
    def is_pinned(self) -> bool:
        return self.normalized_digest is not None and self.package_digest is not None

    @property
    def has_transport(self) -> bool:
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
    kind: Literal["override"]
    node_id: str
    node_name: str
    why: str


@dataclass(frozen=True)
class Rule:
    id: str
    title: str
    statement: str
    why: str
    group: str
    origin_node_id: str
    origin_node_name: str
    modifications: tuple[RuleModification, ...] = ()


@dataclass(frozen=True)
class RuleRemoval:
    origin_node_id: str
    origin_node_name: str
    rule_id: str
    removed_by_node_id: str
    removed_by_node_name: str
    why: str


@dataclass(frozen=True)
class RuleChange:
    kind: ChangeKind
    target_node_id: str
    target_node_name: str
    target_rule_id: str
    statement: str | None
    why: str


@dataclass(frozen=True)
class TopicTarget:
    kind: TargetKind
    locator: str
    intent: TargetIntent
    target_node_id: str | None = None
    target_node_name: str | None = None


@dataclass(frozen=True)
class Topic:
    id: str
    title: str
    condition: str
    targets: tuple[TopicTarget, ...]
    origin_node_id: str
    origin_node_name: str


@dataclass(frozen=True)
class PackageDependency:
    id: str
    name: str
    version: str
    normalized_digest: str
    package_digest: str
    why: str | None = None


@dataclass(frozen=True)
class PackageFile:
    path: str
    sha256: str
    size: int


@dataclass(frozen=True)
class CompiledPackage:
    """Portable, immutable compiled Context state used across repository boundaries."""

    metadata: NodeMetadata
    sources: tuple[PackageDependency, ...]
    changes: tuple[RuleChange, ...]
    rules: tuple[Rule, ...]
    removed_rules: tuple[RuleRemoval, ...]
    topics: tuple[Topic, ...]
    files: tuple[PackageFile, ...]
    normalized_digest: str
    package_digest: str
    imports: tuple[PackageDependency, ...] = ()
    parent: PackageDependency | None = None


@dataclass(frozen=True)
class ParsedNode:
    root: Path
    repo_root: Path
    metadata: NodeMetadata
    sources: tuple[SourceRef, ...]
    rules: tuple[Rule, ...]
    topics: tuple[Topic, ...]
    parent: ParentRef | None = None
    changes: tuple[RuleChange, ...] = ()
    overview: str = ""
    state: str = ""
    plan: str = ""


@dataclass
class CompiledNode:
    parsed: ParsedNode
    # All composition semantics consume immutable compiled packages. Local
    # Source Nodes are compiled first and immediately projected to this same
    # boundary; pinned external Sources are loaded directly into it.
    parent_package: CompiledPackage | None = None
    source_packages: list[CompiledPackage] = field(default_factory=list)
    imported_contexts: list[PackageDependency] = field(default_factory=list)
    inherited_rules: list[Rule] = field(default_factory=list)
    removed_rules: list[RuleRemoval] = field(default_factory=list)
    local_rules: list[Rule] = field(default_factory=list)
    local_changes: list[RuleChange] = field(default_factory=list)
    inherited_topics: list[Topic] = field(default_factory=list)
    local_topics: list[Topic] = field(default_factory=list)
    resources: dict[str, bytes] = field(default_factory=dict)
    normalized_digest: str = ""
    package_digest: str = ""
    official_markdown: str = ""
    package_manifest: str = ""
    machine_yaml: str = ""
    adapters: dict[str, str] = field(default_factory=dict)

    @property
    def metadata(self) -> NodeMetadata:
        return self.parsed.metadata
