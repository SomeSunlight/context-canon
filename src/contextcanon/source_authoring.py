"""Maintain editable source layout without changing accepted import meaning."""
from __future__ import annotations

import os
import re
import tempfile
import uuid
from pathlib import Path

from .parser import (
    ContextCanonError, RESOURCE_COMMENT_RE, RESOURCE_LINE_RE, RULE_COMMENT_RE,
    RULE_RE, SOURCE_RE, TOPIC_COMMENT_RE, _attrs, parse_node,
)
from .source_help import ALIASES, FORMATS, INTRO_END, INTRO_START, explain_source_error, format_comment, remove_help, semantic_lines


def format_source(text: str) -> str:
    """Idempotent layout/help migration; preserve identities, prose and exact pins."""
    text = remove_help(text.replace("\r\n", "\n"))
    lines = text.splitlines()
    visible = semantic_lines(text)
    headings = [(i, line[3:].strip()) for i, line in enumerate(visible) if line.startswith("## ")]
    prelude = lines[:headings[0][0]] if headings else lines
    sections: list[tuple[str, list[str]]] = []
    imports: list[list[str]] = []
    seen: set[str] = set()
    for index, (start, old_name) in enumerate(headings):
        end = headings[index + 1][0] if index + 1 < len(headings) else len(lines)
        name = ALIASES.get(old_name, old_name)
        if name in seen:
            raise ContextCanonError(f"Duplicate source section ## {name}; keep a single section before building")
        seen.add(name)
        body = lines[start + 1:end]
        if name in {"Context Imports", "Parent", "Parent Context Node"}:
            body = _explicit_imports(body, legacy_parent=name != "Context Imports")
            imports.append(body)
        else:
            sections.append((name, _trailing_placement(body)))

    node_index = next((i for i, line in enumerate(prelude) if re.search(r"<!--\s*ctx:node\b", line)), None)
    if node_index is not None:
        prelude[node_index + 1:node_index + 1] = [
            "", format_comment("Node"), "", INTRO_START,
            "Edit this local Context source; ContextCanon generates CONTEXT.md from it.",
            "Some sections use a strict syntax. The comments below show the expected format.",
            "New Rules, Topics and Resources receive IDs automatically during build; preserve existing IDs.",
            "See [the source format guide](CONTEXT-format.md) for examples and editing instructions.",
            INTRO_END, "",
        ]
    chunks = ["\n".join(prelude).strip("\n"), "## Context Imports", format_comment("Context Imports")]
    if imports:
        chunks.append("\n\n".join("\n".join(body).strip("\n") for body in imports).strip("\n"))
    for name, body in sections:
        chunks.append(f"## {name}")
        if name in FORMATS:
            chunks.append(format_comment(name))
        chunks.append("\n".join(body).strip("\n"))
    return "\n\n".join(chunk for chunk in chunks if chunk).rstrip("\n") + "\n"


def _explicit_imports(lines: list[str], *, legacy_parent: bool) -> list[str]:
    result = list(lines)
    visible = semantic_lines("\n".join(lines))
    for i, line in enumerate(visible):
        match = SOURCE_RE.match(line)
        if match and match.group("relationship") is None:
            result[i] = line.rstrip() + " — `relationship=parent`"
        if legacy_parent and "ctx:parent" in line:
            result[i] = line.replace("ctx:parent", "ctx:source")
    return result


def _trailing_placement(lines: list[str]) -> list[str]:
    result = list(lines)
    i = 0
    while i < len(result):
        if re.fullmatch(r'<!-- cc:placement-(?:overview|state|plan|unresolved)\s+.*?-->\s*', result[i]) and (i == 0 or not result[i - 1].startswith("- ")):
            next_item = i + 1
            while next_item < len(result) and not result[next_item].strip():
                next_item += 1
            if next_item < len(result) and result[next_item].startswith("- "):
                marker = result.pop(i).strip()
                result.insert(next_item, "  " + marker)
                i = next_item
        i += 1
    return result


def allocate_missing_ids(text: str) -> str:
    """Only absent IDs are allocated; invalid existing metadata is never repaired."""
    lines = text.splitlines()
    visible = semantic_lines(text)
    identity_comments = {"rule": RULE_COMMENT_RE, "topic": TOPIC_COMMENT_RE, "resource": RESOURCE_COMMENT_RE}
    for number, line in enumerate(visible, 1):
        for kind, pattern in identity_comments.items():
            if re.search(rf"ctx:{kind}\b", line):
                match = pattern.search(line)
                attrs = _attrs(match.group("attrs")) if match else {}
                if not attrs.get("id", "").strip():
                    raise ContextCanonError(f"line {number}: invalid existing ctx:{kind} metadata; preserve or restore its stable ID")
    existing = {value for line in visible for key, value in _attrs(line).items() if key == "id"}
    additions: dict[int, list[str]] = {}

    def fresh(prefix: str) -> str:
        while True:
            value = f"{prefix}-{uuid.uuid4().hex[:12].upper()}"
            if value not in existing:
                existing.add(value)
                return value

    def resource_end(start: int, end: int) -> int:
        i = start + 1
        while i < end and (not visible[i].strip() or (visible[i][:1].isspace() and visible[i].strip().startswith("Why:"))):
            i += 1
        return i

    # Reuse a locator's already established identity across Topics.
    resource_ids: dict[str, str] = {}
    section = ""
    for i, line in enumerate(visible):
        if line.startswith("## "):
            section = ALIASES.get(line[3:].strip(), line[3:].strip())
        match = RESOURCE_LINE_RE.match(line) if section == "Local Topics" else None
        if match:
            end = resource_end(i, len(lines))
            comment = RESOURCE_COMMENT_RE.search(visible[end]) if end < len(lines) else None
            if comment and _attrs(comment.group("attrs")).get("id"):
                resource_ids.setdefault(match.group("locator"), _attrs(comment.group("attrs"))["id"])

    starts = [(i, ALIASES.get(line[3:].strip(), line[3:].strip())) for i, line in enumerate(visible) if line.startswith("## ")]
    for index, (start, name) in enumerate(starts):
        end = starts[index + 1][0] if index + 1 < len(starts) else len(lines)
        if name == "Local Rules":
            for i in range(start + 1, end):
                if not RULE_RE.match(visible[i]):
                    continue
                block_end = next((j for j in range(i + 1, end) if visible[j].startswith(("- ", "### "))), end)
                if not any(RULE_COMMENT_RE.search(line) for line in visible[i + 1:block_end]):
                    insert = block_end
                    while insert > i + 1 and not lines[insert - 1].strip():
                        insert -= 1
                    additions.setdefault(insert, []).append(f'  <!-- ctx:rule id="{fresh("RULE")}" -->')
        elif name == "Local Topics":
            topics = [i for i in range(start + 1, end) if visible[i].startswith("### ")]
            for number, i in enumerate(topics):
                block_end = topics[number + 1] if number + 1 < len(topics) else end
                for j in range(i + 1, block_end):
                    match = RESOURCE_LINE_RE.match(visible[j])
                    if not match:
                        continue
                    insert = resource_end(j, block_end)
                    if insert < block_end and RESOURCE_COMMENT_RE.search(visible[insert]):
                        continue
                    while insert > j + 1 and not lines[insert - 1].strip():
                        insert -= 1
                    locator = match.group("locator")
                    if locator not in resource_ids:
                        resource_ids[locator] = fresh("RESOURCE")
                    additions.setdefault(insert, []).append(f'  <!-- ctx:resource id="{resource_ids[locator]}" -->')
                if not any(TOPIC_COMMENT_RE.search(line) for line in visible[i + 1:block_end]):
                    insert = block_end
                    while insert > i + 1 and not lines[insert - 1].strip():
                        insert -= 1
                    additions.setdefault(insert, []).append(f'<!-- ctx:topic id="{fresh("TOPIC")}" -->')
    for index in sorted(additions, reverse=True):
        lines[index:index] = additions[index]
    return "\n".join(lines).rstrip("\n") + "\n"


def _replace_bytes(path: Path, content: bytes) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=".contextcanon-source-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
        os.chmod(temporary, path.stat().st_mode)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def migrate_sources(repo_root: Path, node_roots: list[Path]) -> list[Path]:
    """Validate every candidate before atomically replacing any selected source."""
    from .compiler import Compiler
    from .outputs import expected_outputs
    from .path_budget import preflight_paths
    originals: dict[Path, bytes] = {}
    candidates: dict[Path, str] = {}
    encoded: dict[Path, bytes] = {}
    for root in node_roots:
        root = root.resolve()
        path = root / "CONTEXT.src.md"
        if path.is_symlink():
            raise ContextCanonError(f"{path}: refusing to migrate a symlink source")
        original = path.read_bytes()
        text = original.decode("utf-8-sig")
        try:
            allocated = allocate_missing_ids(text)
            try:
                parse_node(root, repo_root, source_text=allocated)
            except ContextCanonError as exc:
                # Candidate-only IDs must not make diagnostics point beyond the
                # still unchanged source that the user is about to edit.
                message = str(exc)
                match = re.search(re.escape(str(path)) + r":(\d+):", message)
                if match:
                    bad = allocated.splitlines()[int(match.group(1)) - 1]
                    original_line = next((i for i, line in enumerate(text.splitlines(), 1) if line == bad), None)
                    if original_line is not None:
                        message = message[:match.start(1)] + str(original_line) + message[match.end(1):]
                raise ContextCanonError(message) from exc
            candidate = format_source(allocated)
        except ContextCanonError as exc:
            raise ContextCanonError(explain_source_error(str(exc), path, text)) from exc
        parse_node(root, repo_root, source_text=candidate)
        newline = "\r\n" if b"\r\n" in original else "\n"
        content = candidate.replace("\n", newline).encode("utf-8")
        if original.startswith(b"\xef\xbb\xbf"):
            content = b"\xef\xbb\xbf" + content
        originals[root] = original
        candidates[root] = candidate
        encoded[root] = content
    compiler = Compiler(repo_root, source_overrides=candidates)
    for root in candidates:
        outputs = expected_outputs(compiler.compile(root))
        preflight_paths(root, ["CONTEXT.src.md", *outputs], action="Source authoring migration and output publication")
    changed: list[Path] = []
    try:
        for root, original in originals.items():
            path = root / "CONTEXT.src.md"
            if path.read_bytes() != original:
                raise ContextCanonError(f"{path}: source changed during build preparation; rerun build")
            if encoded[root] != original:
                _replace_bytes(path, encoded[root])
                changed.append(root)
    except Exception as exc:
        for root in reversed(changed):
            _replace_bytes(root / "CONTEXT.src.md", originals[root])
        if isinstance(exc, OSError):
            raise ContextCanonError(f"Source migration could not be written; previous sources restored: {exc}") from exc
        raise
    return changed
