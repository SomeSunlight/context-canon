from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

TargetKind = Literal["resource", "context-node"]
TargetIntent = Literal["required", "optional"]


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


@dataclass(frozen=True)
class Rule:
    id: str
    title: str
    statement: str
    why: str
    group: str
    origin_node_id: str
    origin_node_name: str


@dataclass(frozen=True)
class TopicTarget:
    kind: TargetKind
    locator: str
    intent: TargetIntent


@dataclass(frozen=True)
class Topic:
    id: str
    title: str
    condition: str
    targets: tuple[TopicTarget, ...]
    origin_node_id: str
    origin_node_name: str


@dataclass(frozen=True)
class ParsedNode:
    root: Path
    repo_root: Path
    metadata: NodeMetadata
    sources: tuple[SourceRef, ...]
    rules: tuple[Rule, ...]
    topics: tuple[Topic, ...]


@dataclass
class CompiledNode:
    parsed: ParsedNode
    source_nodes: list["CompiledNode"] = field(default_factory=list)
    inherited_rules: list[Rule] = field(default_factory=list)
    local_rules: list[Rule] = field(default_factory=list)
    local_topics: list[Topic] = field(default_factory=list)
    resources: dict[str, bytes] = field(default_factory=dict)
    normalized_digest: str = ""
    package_digest: str = ""
    official_markdown: str = ""
    machine_yaml: str = ""
    adapters: dict[str, str] = field(default_factory=dict)

    @property
    def metadata(self) -> NodeMetadata:
        return self.parsed.metadata
