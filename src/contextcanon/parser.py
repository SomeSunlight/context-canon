from __future__ import annotations

import re
from pathlib import Path

from .model import NodeMetadata, ParsedNode, Rule, RuleChange, SourceRef, Topic, TopicTarget

NODE_COMMENT_RE = re.compile(r'<!--\s*ctx:node\s+(?P<attrs>.*?)\s*-->')
RULE_COMMENT_RE = re.compile(r'<!--\s*ctx:rule\s+(?P<attrs>.*?)\s*-->')
TOPIC_COMMENT_RE = re.compile(r'<!--\s*ctx:topic\s+(?P<attrs>.*?)\s*-->')
SOURCE_COMMENT_RE = re.compile(r'<!--\s*ctx:source\s+(?P<attrs>.*?)\s*-->')
CHANGE_COMMENT_RE = re.compile(r'<!--\s*ctx:change\s+(?P<attrs>.*?)\s*-->')
ATTR_RE = re.compile(r'([A-Za-z_][A-Za-z0-9_-]*)="([^"]*)"')
DIGEST_RE = re.compile(r'^[0-9a-f]{64}$')
H1_RE = re.compile(r'^#\s+(.+?)\s+—\s+Local Context Source\s*$')
SOURCE_RE = re.compile(r'^- \[(?P<name>[^]]+)\]\((?P<path>[^)]+)\)\s+—\s+`(?P<version>[^`]+)`\s*$')
RULE_RE = re.compile(r'^- \*\*(?P<title>.+?):\*\*\s+(?P<statement>.+?)\s*$')
CHANGE_TARGET_RE = re.compile(r'^- `(?P<source>.+?) / (?P<rule_id>[^`]+)`(?:\s+—\s+.*)?\s*$')
TARGET_RE = re.compile(r'^- (?P<label>Resource|Context Node):\s+`(?P<path>[^`]+)`\s*$')


class ContextCanonError(ValueError):
    pass


def _attrs(text: str) -> dict[str, str]:
    return dict(ATTR_RE.findall(text))


def _find_ctx_attrs(lines: list[str], regex: re.Pattern[str], start: int = 0, end: int | None = None) -> dict[str, str] | None:
    end = len(lines) if end is None else end
    for line in lines[start:end]:
        match = regex.search(line)
        if match:
            return _attrs(match.group("attrs"))
    return None


def find_repo_root(node_root: Path) -> Path:
    current = node_root.resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    return current


def parse_node(node_root: Path, repo_root: Path | None = None) -> ParsedNode:
    node_root = node_root.resolve()
    source_path = node_root / "CONTEXT.src.md"
    if not source_path.is_file():
        raise ContextCanonError(f"Not a Context Node root: {node_root} (missing CONTEXT.src.md)")

    repo_root = (repo_root or find_repo_root(node_root)).resolve()
    text = source_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    name = None
    for line in lines:
        match = H1_RE.match(line)
        if match:
            name = match.group(1).strip()
            break
    if not name:
        raise ContextCanonError(f"{source_path}: first H1 must end with '— Local Context Source'")

    node_attrs = _find_ctx_attrs(lines, NODE_COMMENT_RE)
    if not node_attrs or not node_attrs.get("id") or not node_attrs.get("version"):
        raise ContextCanonError(f"{source_path}: missing compiler-managed ctx:node id/version metadata")
    adapters = tuple(filter(None, (part.strip() for part in node_attrs.get("adapters", "").split(","))))
    metadata = NodeMetadata(node_attrs["id"], name, node_attrs["version"], adapters)

    sections = _section_ranges(lines)
    sources = _parse_sources(lines, sections.get("Sources"), source_path)
    rules = _parse_rules(lines, sections.get("Rules"), source_path, metadata)
    topics = _parse_topics(lines, sections.get("Topics"), source_path, metadata)
    changes = _parse_changes(lines, sections.get("Changes"), source_path)

    _ensure_unique([rule.id for rule in rules], f"{source_path}: duplicate Rule ID")
    _ensure_unique([topic.id for topic in topics], f"{source_path}: duplicate Topic ID")
    _ensure_unique(
        [f"{change.target_node_id}#{change.target_rule_id}" for change in changes],
        f"{source_path}: duplicate Change target",
    )
    return ParsedNode(node_root, repo_root, metadata, tuple(sources), tuple(rules), tuple(topics), tuple(changes))


def _section_ranges(lines: list[str]) -> dict[str, tuple[int, int]]:
    starts: list[tuple[str, int]] = []
    for i, line in enumerate(lines):
        if line.startswith("## "):
            starts.append((line[3:].strip(), i + 1))
    result: dict[str, tuple[int, int]] = {}
    for idx, (name, start) in enumerate(starts):
        end = starts[idx + 1][1] - 1 if idx + 1 < len(starts) else len(lines)
        result[name] = (start, end)
    return result


def _parse_sources(lines: list[str], section: tuple[int, int] | None, source_path: Path) -> list[SourceRef]:
    if not section:
        return []
    start, end = section
    result: list[SourceRef] = []
    i = start
    while i < end:
        match = SOURCE_RE.match(lines[i])
        if not match:
            i += 1
            continue
        attrs = _find_ctx_attrs(lines, SOURCE_COMMENT_RE, i + 1, min(i + 5, end))
        if not attrs or not attrs.get("id") or not attrs.get("version"):
            raise ContextCanonError(f"{source_path}:{i+1}: Source needs ctx:source id/version metadata")
        if attrs["version"] != match.group("version"):
            raise ContextCanonError(f"{source_path}:{i+1}: Source display version and ctx:source version differ")

        has_normalized = "normalized-digest" in attrs
        has_package = "package-digest" in attrs
        if has_normalized != has_package:
            raise ContextCanonError(
                f"{source_path}:{i+1}: immutable Source needs both normalized-digest and package-digest"
            )
        normalized_digest = attrs.get("normalized-digest")
        package_digest = attrs.get("package-digest")
        if has_normalized:
            if not DIGEST_RE.fullmatch(normalized_digest or ""):
                raise ContextCanonError(f"{source_path}:{i+1}: invalid Source normalized-digest")
            if not DIGEST_RE.fullmatch(package_digest or ""):
                raise ContextCanonError(f"{source_path}:{i+1}: invalid Source package-digest")

        result.append(
            SourceRef(
                attrs["id"],
                match.group("name"),
                attrs["version"],
                match.group("path"),
                normalized_digest,
                package_digest,
            )
        )
        i += 1
    return result


def _parse_rules(lines: list[str], section: tuple[int, int] | None, source_path: Path, metadata: NodeMetadata) -> list[Rule]:
    if not section:
        return []
    start, end = section
    result: list[Rule] = []
    group = "Rules"
    i = start
    while i < end:
        line = lines[i]
        if line.startswith("### "):
            group = line[4:].strip()
            i += 1
            continue
        match = RULE_RE.match(line)
        if not match:
            i += 1
            continue
        block_end = i + 1
        while block_end < end and not lines[block_end].startswith("- **") and not lines[block_end].startswith("### "):
            block_end += 1
        why = None
        attrs = None
        for detail in lines[i + 1:block_end]:
            stripped = detail.strip()
            if stripped.startswith("Why:"):
                why = stripped[4:].strip()
            comment = RULE_COMMENT_RE.search(detail)
            if comment:
                attrs = _attrs(comment.group("attrs"))
        if not why:
            raise ContextCanonError(f"{source_path}:{i+1}: Rule needs an indented Why: rationale")
        if not attrs or not attrs.get("id"):
            raise ContextCanonError(f"{source_path}:{i+1}: Rule needs compiler-managed ctx:rule ID")
        result.append(Rule(attrs["id"], match.group("title").strip(), match.group("statement").strip(), why, group, metadata.id, metadata.name))
        i = block_end
    return result


def _parse_changes(lines: list[str], section: tuple[int, int] | None, source_path: Path) -> list[RuleChange]:
    if not section:
        return []
    start, end = section
    result: list[RuleChange] = []
    kind: str | None = None
    i = start
    while i < end:
        line = lines[i]
        stripped_line = line.strip()
        if not stripped_line or stripped_line.startswith("<!--"):
            i += 1
            continue
        if line.startswith("### "):
            heading = line[4:].strip()
            if heading not in {"Remove", "Override"}:
                raise ContextCanonError(f"{source_path}:{i+1}: unsupported Changes heading: {heading}")
            kind = heading.lower()
            i += 1
            continue

        match = CHANGE_TARGET_RE.match(line)
        if not match:
            raise ContextCanonError(f"{source_path}:{i+1}: unsupported Changes line: {stripped_line}")
        if kind is None:
            raise ContextCanonError(f"{source_path}:{i+1}: Change appears before ### Remove or ### Override")

        block_end = i + 1
        while block_end < end and not lines[block_end].startswith("- `") and not lines[block_end].startswith("### "):
            block_end += 1

        why = None
        statement = None
        attrs = None
        for detail in lines[i + 1:block_end]:
            stripped = detail.strip()
            if not stripped:
                continue
            if stripped.startswith("Why:"):
                why = stripped[4:].strip()
                continue
            if stripped.startswith("New rule:"):
                statement = stripped[len("New rule:"):].strip()
                continue
            comment = CHANGE_COMMENT_RE.search(detail)
            if comment:
                attrs = _attrs(comment.group("attrs"))
                continue
            if stripped.startswith("<!--"):
                continue
            raise ContextCanonError(f"{source_path}:{i+1}: unsupported Change detail: {stripped}")

        if not why:
            raise ContextCanonError(f"{source_path}:{i+1}: Change needs an indented Why: rationale")
        if not attrs or not attrs.get("op") or not attrs.get("source-id") or not attrs.get("rule-id"):
            raise ContextCanonError(
                f"{source_path}:{i+1}: Change needs ctx:change op/source-id/rule-id metadata"
            )
        if attrs["op"] != kind:
            raise ContextCanonError(f"{source_path}:{i+1}: Change heading and ctx:change op differ")
        if attrs["rule-id"] != match.group("rule_id"):
            raise ContextCanonError(f"{source_path}:{i+1}: visible Rule ID and ctx:change rule-id differ")
        if kind == "override" and not statement:
            raise ContextCanonError(f"{source_path}:{i+1}: Override needs an indented New rule: statement")
        if kind == "remove" and statement:
            raise ContextCanonError(f"{source_path}:{i+1}: Remove must not define New rule:")

        result.append(
            RuleChange(
                kind=kind,  # type: ignore[arg-type]
                target_node_id=attrs["source-id"],
                target_node_name=match.group("source").strip(),
                target_rule_id=attrs["rule-id"],
                statement=statement,
                why=why,
            )
        )
        i = block_end
    return result


def _parse_topics(lines: list[str], section: tuple[int, int] | None, source_path: Path, metadata: NodeMetadata) -> list[Topic]:
    if not section:
        return []
    start, end = section
    topic_starts = [i for i in range(start, end) if lines[i].startswith("### ")]
    result: list[Topic] = []
    for index, topic_start in enumerate(topic_starts):
        topic_end = topic_starts[index + 1] if index + 1 < len(topic_starts) else end
        title = lines[topic_start][4:].strip()
        block = lines[topic_start + 1:topic_end]
        attrs = _find_ctx_attrs(block, TOPIC_COMMENT_RE)
        if not attrs or not attrs.get("id"):
            raise ContextCanonError(f"{source_path}:{topic_start+1}: Topic needs compiler-managed ctx:topic ID")

        condition_lines: list[str] = []
        targets: list[TopicTarget] = []
        intent = None
        for raw in block:
            stripped = raw.strip()
            if not stripped or stripped.startswith("<!--"):
                continue
            if stripped == "Required:":
                intent = "required"
                continue
            if stripped == "Optional:":
                intent = "optional"
                continue
            target_match = TARGET_RE.match(stripped)
            if target_match:
                if intent is None:
                    raise ContextCanonError(f"{source_path}: Topic target appears before Required:/Optional:")
                kind = "resource" if target_match.group("label") == "Resource" else "context-node"
                targets.append(TopicTarget(kind, target_match.group("path"), intent))
                continue
            if intent is None:
                condition_lines.append(stripped)
            else:
                raise ContextCanonError(f"{source_path}: unsupported Topic line: {stripped}")
        if not condition_lines:
            raise ContextCanonError(f"{source_path}:{topic_start+1}: Topic needs a condition")
        if not targets:
            raise ContextCanonError(f"{source_path}:{topic_start+1}: Topic needs at least one target")
        result.append(Topic(attrs["id"], title, " ".join(condition_lines), tuple(targets), metadata.id, metadata.name))
    return result


def _ensure_unique(values: list[str], prefix: str) -> None:
    seen: set[str] = set()
    for value in values:
        if value in seen:
            raise ContextCanonError(f"{prefix}: {value}")
        seen.add(value)
