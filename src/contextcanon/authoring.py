from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path

from .parser import ContextCanonError, parse_node


@dataclass(frozen=True)
class AuthoringResult:
    element_id: str
    source_path: Path


def _one_line(value: str, label: str) -> str:
    result = " ".join(value.splitlines()).strip()
    if not result:
        raise ContextCanonError(f"{label} must not be empty")
    return result


def _fresh_id(prefix: str, existing: set[str]) -> str:
    for _ in range(100):
        candidate = f"{prefix}-{uuid.uuid4().hex[:12].upper()}"
        if candidate not in existing:
            return candidate
    raise ContextCanonError(f"Could not allocate a fresh {prefix} identity")


def _section_bounds(lines: list[str], name: str) -> tuple[int, int] | None:
    heading = f"## {name}"
    try:
        heading_index = lines.index(heading)
    except ValueError:
        return None
    end = len(lines)
    for index in range(heading_index + 1, len(lines)):
        if lines[index].startswith("## "):
            end = index
            break
    return heading_index, end


def _trim_insert(lines: list[str], index: int, block: list[str]) -> list[str]:
    before = list(lines[:index])
    after = list(lines[index:])
    while before and not before[-1].strip():
        before.pop()
    while after and not after[0].strip():
        after.pop(0)
    result = before + [""] + block
    if after:
        result += [""] + after
    return result


def _write_validated(node_root: Path, original: str, lines: list[str], expected_kind: str, element_id: str) -> AuthoringResult:
    source_path = node_root / "CONTEXT.src.md"
    source_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    try:
        parsed = parse_node(node_root)
        ids = {item.id for item in (parsed.rules if expected_kind == "rule" else parsed.topics)}
        if element_id not in ids:
            raise ContextCanonError(f"New {expected_kind} {element_id} was not readable after authoring")
    except Exception:
        source_path.write_text(original, encoding="utf-8")
        raise
    return AuthoringResult(element_id, source_path)


def add_rule(
    node_root: Path,
    *,
    title: str,
    statement: str,
    why: str,
    group: str = "General",
) -> AuthoringResult:
    node_root = node_root.resolve()
    parsed = parse_node(node_root)
    title = _one_line(title, "Rule title")
    statement = _one_line(statement, "Rule statement")
    why = _one_line(why, "Rule rationale")
    group = _one_line(group, "Rule group")
    element_id = _fresh_id("RULE", {rule.id for rule in parsed.rules})
    source_path = node_root / "CONTEXT.src.md"
    original = source_path.read_text(encoding="utf-8")
    lines = original.splitlines()
    rule_block = [
        f"- **{title}:** {statement}",
        f"  Why: {why}",
        f'  <!-- ctx:rule id="{element_id}" -->',
    ]

    bounds = _section_bounds(lines, "Rules")
    if bounds is None:
        lines = _trim_insert(lines, len(lines), ["## Rules", "", f"### {group}", ""] + rule_block)
    else:
        start, end = bounds
        group_heading = f"### {group}"
        group_index = next((i for i in range(start + 1, end) if lines[i] == group_heading), None)
        if group_index is None:
            lines = _trim_insert(lines, end, [group_heading, ""] + rule_block)
        else:
            group_end = end
            for i in range(group_index + 1, end):
                if lines[i].startswith("### "):
                    group_end = i
                    break
            lines = _trim_insert(lines, group_end, rule_block)
    return _write_validated(node_root, original, lines, "rule", element_id)


def add_topic(
    node_root: Path,
    *,
    title: str,
    condition: str,
    required_resources: tuple[str, ...] = (),
    optional_resources: tuple[str, ...] = (),
    required_nodes: tuple[str, ...] = (),
    optional_nodes: tuple[str, ...] = (),
) -> AuthoringResult:
    node_root = node_root.resolve()
    parsed = parse_node(node_root)
    title = _one_line(title, "Topic title")
    condition = _one_line(condition, "Topic condition")
    targets = required_resources or optional_resources or required_nodes or optional_nodes
    if not targets:
        raise ContextCanonError("Topic needs at least one --required-resource, --optional-resource, --required-node, or --optional-node target")
    element_id = _fresh_id("TOPIC", {topic.id for topic in parsed.topics})
    source_path = node_root / "CONTEXT.src.md"
    original = source_path.read_text(encoding="utf-8")
    lines = original.splitlines()
    block = [f"### {title}", "", condition, ""]
    if required_resources or required_nodes:
        block += ["Required:"]
        block += [f"- Resource: `{_one_line(value, 'Resource target')}`" for value in required_resources]
        block += [f"- Context Node: `{_one_line(value, 'Context Node target')}`" for value in required_nodes]
        block += [""]
    if optional_resources or optional_nodes:
        block += ["Optional:"]
        block += [f"- Resource: `{_one_line(value, 'Resource target')}`" for value in optional_resources]
        block += [f"- Context Node: `{_one_line(value, 'Context Node target')}`" for value in optional_nodes]
        block += [""]
    block += [f'<!-- ctx:topic id="{element_id}" -->']

    bounds = _section_bounds(lines, "Topics")
    if bounds is None:
        lines = _trim_insert(lines, len(lines), ["## Topics", ""] + block)
    else:
        _, end = bounds
        lines = _trim_insert(lines, end, block)
    return _write_validated(node_root, original, lines, "topic", element_id)
