"""Source-only authoring guidance and line-preserving parser visibility."""
from __future__ import annotations

import re
from importlib.resources import files
from pathlib import Path

GUIDE_NAME = "CONTEXT-format.md"
GUIDE_MARKER = "<!-- contextcanon:generated-source-format -->"
INTRO_START = "<!-- contextcanon:source-help:intro:start -->"
INTRO_END = "<!-- contextcanon:source-help:intro:end -->"
FORMAT_PREFIX = "<!-- contextcanon:format "
FORMATS = {
    "Node": 'Node metadata follows the # title: ctx:node id="..." name="..." version="...". Preserve existing identity.',
    "Context Imports": '- [Name](location) — `version` — `relationship=parent|reference`; optional indented Why:, then ctx:source metadata. Preserve exact pins; use source list/adopt/update for package identity.',
    "Local Overview": 'Ordinary Markdown orientation, local to this Node. Any existing placement identity follows its paragraph/item; do not change it.',
    "Local State": 'Ordinary Markdown describing the current local situation. Any existing placement identity follows its paragraph/item; preserve it.',
    "Local Plan": 'Ordinary Markdown describing intended local work. Any existing placement identity follows its paragraph/item; preserve it.',
    "Local Rules": '### Group, then - **Title:** Statement, then indented Why: Rationale. build adds a missing ctx:rule ID after the entry; preserve existing IDs.',
    "Changes": '### Remove or ### Override, then - `Source name / RULE-ID` — Title, indented Why:, and ctx:change op/source-id/rule-id. Override also needs indented New rule: text; metadata follows the entry.',
    "Local Topics": '### Title, condition text, Required: and/or Optional:, then - Resource: `path` or - Context Node: `node-path`. Resource may have indented Why:. build adds missing Topic/Resource IDs after their entries; preserve existing IDs.',
}
ALIASES = {"Sources": "Context Imports", "Overview": "Local Overview", "State": "Local State",
           "Plan": "Local Plan", "Rules": "Local Rules", "Topics": "Local Topics"}


def guide_text() -> str:
    return files("contextcanon").joinpath("data/source-format.md").read_text(encoding="utf-8")


def semantic_lines(text: str) -> list[str]:
    """Mask examples/comments while retaining physical line numbers and real metadata.

    Nested comment markers occur in historical compiler-managed templates.
    Examples inside those templates must never become Rules or dependencies.
    """
    result = []
    depth = 0
    intro = False
    for line in text.splitlines():
        if line.strip() == INTRO_START:
            intro = True
        if intro:
            result.append("")
            if line.strip() == INTRO_END:
                intro = False
            continue
        stripped = line.strip()
        real_metadata = re.fullmatch(r"<!--\s*(?:ctx:[\w-]+|cc:placement-[\w-]+|contextcanon-placement-[\w-]+:[\w-]+)\b.*?-->", stripped)
        if depth == 0 and real_metadata:
            result.append(line)
            continue
        if depth or "<!--" in line:
            depth += line.count("<!--") - line.count("-->")
            depth = max(depth, 0)
            result.append("")
        else:
            result.append(line)
    return result


def remove_help(text: str) -> str:
    text = re.sub(r"(?ms)^" + re.escape(INTRO_START) + r"\n.*?^" + re.escape(INTRO_END) + r"\n*", "", text)
    return re.sub(r"(?ms)^<!-- contextcanon:format [^\n]+\n.*?^-->\n*", "", text)


def format_comment(section: str) -> str:
    return f"{FORMAT_PREFIX}{section}\nFormat: {FORMATS[section]}\nDetails: {GUIDE_NAME}\n-->"


def explain_source_error(message: str, path: Path, text: str) -> str:
    if "Source format help:" in message:
        return message
    match = re.search(re.escape(str(path)) + r":(\d+):", message)
    number = int(match.group(1)) if match else None
    if number is None:
        declared_line = re.search(r"\bline (\d+):", message)
        if declared_line:
            number = int(declared_line.group(1))
        bad_line = message.split("unsupported Topic line: ")[-1] if "unsupported Topic line: " in message else None
        if bad_line and number is None:
            number = next((i for i, line in enumerate(text.splitlines(), 1) if line.strip() == bad_line), None)
    section = "Node"
    for index, line in enumerate(semantic_lines(text), 1):
        if number is not None and index > number:
            break
        if line.startswith("## "):
            candidate = ALIASES.get(line[3:].strip(), line[3:].strip())
            if candidate in {"Parent", "Parent Context Node"}:
                candidate = "Context Imports"
            if candidate in FORMATS:
                section = candidate
    if number is None:
        section = next((name for word, name in (("Topic", "Local Topics"), ("Resource", "Local Topics"), ("Rule", "Local Rules"), ("Change", "Changes"), ("Source", "Context Imports"), ("import", "Context Imports")) if word in message), section)
    example = FORMATS[section]
    if section == "Local Topics":
        example += '\nExample: - Resource: `samples/variant-6.jsonc`\n  Why: Version 6 - VALID\nUse backticks around the path; move trailing annotations to an indented Why: line.'
    if number is not None and not match:
        message = f"{path}:{number}: {message.removeprefix(str(path) + ': ')}"
    return (message + f"\nExpected format: {example}\nSource format help: the 'contextcanon:format {section}' comment in {path} (installed/refreshed by build)."
            f"\nDetailed guide: {path.parent / GUIDE_NAME}"
            "\nDocumentation: https://github.com/SomeSunlight/context-canon/blob/main/docs/context-source-format.md"
            "\nIf authoring help/IDs are missing, run contextcanon build on this Node; check never edits the source.")
