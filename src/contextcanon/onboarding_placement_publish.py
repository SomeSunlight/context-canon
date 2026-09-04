from __future__ import annotations

import difflib
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable

from .compiler import Compiler
from .onboarding_placement import OnboardingPlacementProposal
from .onboarding_placement_review import (OnboardingPlacementReview, PlacementReviewItem, PlacementReviewSource, PlacementReviewSourceEdit)
from .onboarding_proposal import EvidenceSnapshot, load_evidence_snapshot
from .outputs import expected_outputs, write_outputs
from .package import PACKAGE_MANIFEST_PATH, artifact_files, compiled_package, load_package
from .parser import ContextCanonError, find_repo_root, parse_node


PLACEMENT_ACCEPTANCE_SCHEMA = "contextcanon/onboarding-placement-acceptance/v1"

_MANAGED_SECTIONS = ("overview", "state", "plan", "parent", "sources", "rules", "topics")
_MARKER_START = {name: f"<!-- contextcanon-placement-{name}:start -->" for name in _MANAGED_SECTIONS}
_MARKER_END = {name: f"<!-- contextcanon-placement-{name}:end -->" for name in _MANAGED_SECTIONS}

_SKELETON_SENTENCES = (
    "This Node skeleton reserves the accepted onboarding landing point before detailed project knowledge is distributed.",
    "This area is intentionally reserved by the project owner; implementation details are not yet decided.",
    "The later placement pass will add only the Rules, Topics, Sources, or mappings reviewed for this area.",
)


@dataclass(frozen=True)
class SourceGitProvenance:
    source_node_id: str
    source_name: str
    source_version: str
    source_package_digest: str
    origin: str
    locator: str
    ref: str
    node_path: str
    package_root: Path

    def to_dict(self) -> dict[str, str]:
        return {
            "source_node_id": self.source_node_id,
            "locator": self.locator,
            "ref": self.ref,
            "node_path": self.node_path,
        }


@dataclass(frozen=True)
class PlacementNodeDelta:
    key: str
    name: str
    path: str
    node_id: str
    source_path: Path
    before: str
    after: str

    @property
    def changed(self) -> bool:
        return self.before != self.after


@dataclass(frozen=True)
class PlacementParentPin:
    child_key: str
    child_name: str
    child_path: str
    parent_key: str
    parent_name: str
    parent_path: str
    parent_node_id: str
    parent_version: str
    parent_normalized_digest: str
    parent_package_digest: str
    locator: str

    def to_dict(self) -> dict[str, str]:
        return {
            "child_key": self.child_key,
            "parent_key": self.parent_key,
            "parent_node_id": self.parent_node_id,
            "parent_version": self.parent_version,
            "parent_normalized_digest": self.parent_normalized_digest,
            "parent_package_digest": self.parent_package_digest,
            "locator": self.locator,
        }


@dataclass(frozen=True)
class PlacementDocumentDelta:
    path: str
    source_path: Path
    before: str
    after: str
    source_edit_ids: tuple[str, ...]

    @property
    def changed(self) -> bool:
        return self.before != self.after


@dataclass(frozen=True)
class PlacementPublicationPreview:
    project_root: Path
    evidence_digest: str
    structure_digest: str
    proposal_digest: str
    review_digest: str
    review_complete: bool
    pending_ids: tuple[str, ...]
    nodes: tuple[PlacementNodeDelta, ...]
    parents: tuple[PlacementParentPin, ...]
    sources: tuple[SourceGitProvenance, ...]
    followups: tuple[PlacementReviewItem, ...]
    documents: tuple[PlacementDocumentDelta, ...]


@dataclass(frozen=True)
class PlacementPublicationResult:
    acceptance_path: Path
    review_digest: str
    changed_sources: tuple[Path, ...]
    acceptance_digest: str


def _error(message: str) -> ContextCanonError:
    return ContextCanonError(f"Onboarding placement publication: {message}")


def _node_root(project_root: Path, path: str) -> Path:
    if path == ".":
        return project_root
    return project_root / Path(*PurePosixPath(path).parts)


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except OSError as exc:
        raise _error(f"could not atomically write {path}: {exc}") from exc
    finally:
        temporary.unlink(missing_ok=True)


def _apply_line_edits(original: str, edits: list[PlacementReviewSourceEdit]) -> str:
    lines = original.splitlines(keepends=True)
    for edit in sorted(edits, key=lambda item: item.start_line, reverse=True):
        segment = lines[edit.start_line - 1 : edit.end_line]
        needs_newline = bool(segment and segment[-1].endswith(("\n", "\r"))) or edit.end_line < len(lines)
        replacement = edit.replacement
        if replacement and needs_newline and not replacement.endswith("\n"):
            replacement += "\n"
        lines[edit.start_line - 1 : edit.end_line] = [replacement] if replacement else []
    return "".join(lines)


def _accepted_source_edits(review: OnboardingPlacementReview) -> dict[str, list[PlacementReviewSourceEdit]]:
    result: dict[str, list[PlacementReviewSourceEdit]] = {}
    for edit in review.source_edits:
        if edit.decision == "accept":
            result.setdefault(edit.path, []).append(edit)
    return result


def _expected_document_deltas(
    snapshot: EvidenceSnapshot, project_root: Path, review: OnboardingPlacementReview
) -> tuple[PlacementDocumentDelta, ...]:
    accepted = _accepted_source_edits(review)
    result: list[PlacementDocumentDelta] = []
    for path, edits in sorted(accepted.items()):
        entry = snapshot.by_path[path]
        frozen = (snapshot.root / "evidence" / Path(*PurePosixPath(path).parts)).read_text(encoding="utf-8")
        expected = _apply_line_edits(frozen, edits)
        live_path = project_root / Path(*PurePosixPath(path).parts)
        if not live_path.is_file():
            raise _error(f"frozen Evidence path is missing from the live project: {path}")
        live = live_path.read_text(encoding="utf-8")
        if live not in {frozen, expected}:
            raise _error(
                f"frozen Evidence changed outside the reviewed source transformation: {path}; prepare/review again rather than publishing stale placement"
            )
        result.append(PlacementDocumentDelta(path, live_path, live, expected, tuple(edit.proposal_id for edit in edits)))
    edited_paths = set(accepted)
    for entry in snapshot.entries:
        if entry.path in edited_paths:
            continue
        live = project_root / Path(*PurePosixPath(entry.path).parts)
        if not live.is_file():
            raise _error(f"frozen Evidence path is missing from the live project: {entry.path}")
        if _sha256_bytes(live.read_bytes()) != entry.sha256:
            raise _error(
                f"frozen Evidence changed after semantic review: {entry.path}; prepare a new snapshot rather than publishing stale placement"
            )
    return tuple(result)

def _catalog_roots(catalog_package_roots: Iterable[Path]) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for raw in catalog_package_roots:
        root = Path(raw).resolve()
        package = load_package(root)
        if package.metadata.id in result:
            raise _error(f"more than one catalog package root supplied for Source {package.metadata.id}")
        result[package.metadata.id] = root
    return result


def _run_git(root: Path, *args: str) -> str:
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), *args],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise _error("Git provenance requires the 'git' executable on PATH") from exc
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or f"exit {completed.returncode}"
        raise _error(f"could not resolve reusable Source Git provenance: {detail}")
    return completed.stdout.strip()


def _git_provenance(source: PlacementReviewSource, package_root: Path) -> SourceGitProvenance:
    repository = Path(_run_git(package_root, "rev-parse", "--show-toplevel")).resolve()
    try:
        node_path = package_root.relative_to(repository).as_posix() or "."
    except ValueError as exc:
        raise _error(f"catalog package root is not inside its Git repository: {package_root}") from exc
    status = _run_git(repository, "status", "--porcelain", "--untracked-files=all", "--", node_path)
    if status:
        raise _error(
            f"accepted Source {source.source_name} has uncommitted package-path changes; exact Git provenance would be ambiguous"
        )
    ref = _run_git(repository, "rev-parse", "HEAD")
    locator = _run_git(repository, "remote", "get-url", "origin")
    if not re.fullmatch(r"[0-9a-f]{40}", ref):
        raise _error(f"Source Git HEAD is not an exact commit SHA: {ref!r}")
    if '"' in locator or '"' in node_path:
        raise _error("Source Git provenance contains unsupported quote characters")
    return SourceGitProvenance(
        source_node_id=source.source_node_id,
        source_name=source.source_name,
        source_version=source.source_version,
        source_package_digest=source.source_package_digest,
        origin=source.origin,
        locator=locator,
        ref=ref,
        node_path=node_path,
        package_root=package_root,
    )


def _source_provenance(
    review: OnboardingPlacementReview,
    proposal: OnboardingPlacementProposal,
    catalog_package_roots: Iterable[Path],
) -> tuple[SourceGitProvenance, ...]:
    roots = _catalog_roots(catalog_package_roots)
    package_by_id = {package.metadata.id: package for package in proposal.catalog_packages}
    result: list[SourceGitProvenance] = []
    for source in review.sources:
        if source.decision != "accept":
            continue
        package = package_by_id.get(source.source_node_id)
        root = roots.get(source.source_node_id)
        if package is None or root is None:
            raise _error(f"accepted Source {source.source_name} requires its exact --catalog-package root")
        if (
            package.metadata.version != source.source_version
            or package.normalized_digest != source.source_normalized_digest
            or package.package_digest != source.source_package_digest
        ):
            raise _error(f"accepted Source {source.source_name} no longer matches the reviewed exact package")
        result.append(_git_provenance(source, root))
    return tuple(result)


def _strip_managed_block(text: str, name: str) -> str:
    start = _MARKER_START[name]
    end = _MARKER_END[name]
    starts = text.count(start)
    ends = text.count(end)
    if starts != ends or starts > 1:
        raise _error(f"CONTEXT.src.md has malformed managed {name} placement block")
    if starts == 0:
        return text
    pattern = re.compile(rf"\n?{re.escape(start)}\n.*?\n{re.escape(end)}\n?", re.DOTALL)
    return pattern.sub("\n", text, count=1)


def _remove_skeleton_placeholder(text: str) -> str:
    for sentence in _SKELETON_SENTENCES:
        text = text.replace(sentence + "\n\n", "")
        text = text.replace(sentence + "\n", "")
    return text


def _replace_managed_section(
    text: str,
    section: str,
    name: str,
    body: str,
    *,
    aliases: tuple[str, ...] = (),
) -> str:
    text = _strip_managed_block(text, name)
    candidates: list[tuple[str, re.Match[str]]] = []
    for candidate in (section, *aliases):
        match = re.search(rf"(?m)^## {re.escape(candidate)}\s*$", text)
        if match is not None:
            candidates.append((candidate, match))
    if len(candidates) > 1:
        raise _error(
            f"CONTEXT.src.md contains both canonical and legacy headings for {section}: "
            + ", ".join(f"## {candidate}" for candidate, _ in candidates)
        )
    if candidates and candidates[0][0] != section:
        _, match = candidates[0]
        text = text[:match.start()] + f"## {section}" + text[match.end():]
    if not body.strip():
        return text.rstrip() + "\n"
    block = f"{_MARKER_START[name]}\n{body.rstrip()}\n{_MARKER_END[name]}"
    heading = re.search(rf"(?m)^## {re.escape(section)}\s*$", text)
    if heading is None:
        return text.rstrip() + f"\n\n## {section}\n\n{block}\n"
    next_heading = re.compile(r"(?m)^## .+$").search(text, heading.end())
    insert_at = next_heading.start() if next_heading else len(text)
    before = text[:insert_at].rstrip()
    after = text[insert_at:].lstrip("\n")
    result = before + "\n\n" + block + "\n"
    if after:
        result += "\n" + after
    return result.rstrip() + "\n"


def _replace_parent_section(text: str, body: str) -> str:
    text = _strip_managed_block(text, "parent")
    matches: list[re.Match[str]] = []
    for heading in ("Parent Context Node", "Parent"):
        match = re.search(rf"(?m)^## {re.escape(heading)}\s*$", text)
        if match is not None:
            matches.append(match)
    if len(matches) > 1:
        raise _error("CONTEXT.src.md contains both ## Parent Context Node and legacy ## Parent")
    if matches:
        heading = matches[0]
        next_heading = re.compile(r"(?m)^## .+$").search(text, heading.end())
        end = next_heading.start() if next_heading else len(text)
        existing = text[heading.end():end].strip()
        if existing and "ctx:parent" not in existing:
            raise _error("Parent Context Node section contains unmanaged content; preserve it elsewhere before publication")
        text = (text[:heading.start()].rstrip() + "\n\n" + text[end:].lstrip("\n")).rstrip() + "\n"
    if not body.strip():
        return text
    block = f"{_MARKER_START['parent']}\n{body.rstrip()}\n{_MARKER_END['parent']}"
    section = f"## Parent Context Node\n\n{block}\n"
    first_local = re.search(r"(?m)^## .+$", text)
    insert_at = first_local.start() if first_local else len(text)
    before = text[:insert_at].rstrip()
    after = text[insert_at:].lstrip("\n")
    result = before + "\n\n" + section
    if after:
        result += "\n" + after
    return result.rstrip() + "\n"


def _safe_line(value: object, label: str) -> str:
    text = str(value).strip()
    if not text or "\n" in text or "\r" in text:
        raise _error(f"{label} must be non-empty single-line text for Context source publication")
    return text


def _relative_resource(project_root: Path, node_root: Path, repository_path: str) -> str:
    absolute = (project_root / Path(*PurePosixPath(repository_path).parts)).resolve()
    try:
        absolute.relative_to(project_root)
    except ValueError as exc:
        raise _error(f"resource path escapes project: {repository_path}") from exc
    return Path(os.path.relpath(absolute, node_root)).as_posix()


def _render_overviews(items: list[PlacementReviewItem]) -> str:
    lines: list[str] = []
    for item in items:
        text = _safe_line(item.payload["text"], f"item {item.proposal_id} overview")
        lines.extend([f'<!-- cc:placement-overview id="{item.authoring_id}" -->', f"- {text}", ""])
    return "\n".join(lines).rstrip()


def _render_summaries(items: list[PlacementReviewItem], kind: str) -> str:
    lines: list[str] = []
    for item in items:
        text = _safe_line(item.payload["text"], f"item {item.proposal_id} {kind}")
        lines.extend([f'<!-- cc:placement-{kind} id="{item.authoring_id}" -->', f"- {text}", ""])
    return "\n".join(lines).rstrip()


def _render_state(items: list[PlacementReviewItem]) -> str:
    lines: list[str] = []
    for item in items:
        if item.kind == "state":
            text = _safe_line(item.payload["text"], f"item {item.proposal_id} state")
            lines.extend([f'<!-- cc:placement-state id="{item.authoring_id}" -->', f"- {text}", ""])
        elif item.kind == "unresolved":
            question = _safe_line(item.payload["question"], f"item {item.proposal_id} unresolved question")
            lines.extend([f'<!-- cc:placement-unresolved id="{item.authoring_id}" -->', f"- Open question: {question}", ""])
    return "\n".join(lines).rstrip()


def _render_rules(items: list[PlacementReviewItem]) -> str:
    if not items:
        return ""
    lines = ["### Onboarding placement", ""]
    for item in items:
        title = _safe_line(item.title, f"item {item.proposal_id} title")
        statement = _safe_line(item.payload["statement"], f"item {item.proposal_id} statement")
        why = _safe_line(item.payload["why"], f"item {item.proposal_id} why")
        lines.extend(
            [
                f"- **{title}:** {statement}",
                f"  Why: {why}",
                f'  <!-- ctx:rule id="{item.authoring_id}" -->',
                "",
            ]
        )
    return "\n".join(lines).rstrip()


def _render_topics(items: list[PlacementReviewItem], project_root: Path, node_root: Path) -> str:
    lines: list[str] = []
    for item in items:
        title = _safe_line(item.title, f"item {item.proposal_id} title")
        condition = _safe_line(item.payload["condition"], f"item {item.proposal_id} condition")
        lines.extend([f"### {title}", "", condition, "", "Required:"])
        for path in item.payload["resource_paths"]:
            locator = _relative_resource(project_root, node_root, str(path))
            lines.append(f"- Resource: `{locator}`")
        lines.extend(["", f'<!-- ctx:topic id="{item.authoring_id}" -->', ""])
    return "\n".join(lines).rstrip()


def _render_sources(
    sources: list[PlacementReviewSource],
    provenance_by_id: dict[str, SourceGitProvenance],
) -> str:
    lines: list[str] = []
    for source in sources:
        provenance = provenance_by_id[source.source_node_id]
        name = _safe_line(source.source_name, f"Source {source.review_id} name")
        if any(char in name for char in "]\n\r"):
            raise _error(f"Source {source.review_id} name cannot be represented safely")
        lines.append(f"- [{name}]({provenance.locator}) — `{source.source_version}`")
        if source.relationship_why:
            lines.append(f"  Why: {_safe_line(source.relationship_why, f'Source {source.review_id} relationship Why')}")
        lines.extend(
            [
                (
                    f'  <!-- ctx:source id="{source.source_node_id}" version="{source.source_version}" '
                    f'normalized-digest="{source.source_normalized_digest}" '
                    f'package-digest="{source.source_package_digest}" transport="git" '
                    f'ref="{provenance.ref}" node-path="{provenance.node_path}" -->'
                ),
                "",
            ]
        )
    return "\n".join(lines).rstrip()


def _managed_ids_outside_blocks(text: str) -> tuple[set[str], set[str], set[str]]:
    stripped = text
    for name in _MANAGED_SECTIONS:
        stripped = _strip_managed_block(stripped, name)
    rule_ids = set(re.findall(r'ctx:rule\s+id="([^"]+)"', stripped))
    topic_ids = set(re.findall(r'ctx:topic\s+id="([^"]+)"', stripped))
    source_ids = set(re.findall(r'ctx:source\s+id="([^"]+)"', stripped))
    return rule_ids, topic_ids, source_ids


def _render_node_source(
    before: str,
    project_root: Path,
    node_root: Path,
    items: list[PlacementReviewItem],
    sources: list[PlacementReviewSource],
    provenance_by_id: dict[str, SourceGitProvenance],
) -> str:
    overviews = [item for item in items if item.kind == "overview"]
    states = [item for item in items if item.kind in {"state", "unresolved"}]
    plans = [item for item in items if item.kind == "plan"]
    rules = [item for item in items if item.kind == "rule"]
    topics = [item for item in items if item.kind == "topic-resource"]
    outside_rule_ids, outside_topic_ids, outside_source_ids = _managed_ids_outside_blocks(before)
    for item in rules:
        if item.authoring_id in outside_rule_ids:
            raise _error(f"Rule authoring ID collision outside placement-managed block: {item.authoring_id}")
    for item in topics:
        if item.authoring_id in outside_topic_ids:
            raise _error(f"Topic authoring ID collision outside placement-managed block: {item.authoring_id}")
    for source in sources:
        if source.source_node_id in outside_source_ids:
            raise _error(
                f"Source Node ID collision outside placement-managed block: {source.source_node_id}; "
                "review the existing authored Source instead of duplicating it"
            )

    text = before
    if overviews or states or plans or rules or topics or sources:
        text = _remove_skeleton_placeholder(text)
    text = _replace_managed_section(text, "Local Overview", "overview", _render_overviews(overviews), aliases=("Overview",))
    text = _replace_managed_section(text, "Local State", "state", _render_state(states), aliases=("State",))
    text = _replace_managed_section(text, "Local Plan", "plan", _render_summaries(plans, "plan"), aliases=("Plan",))
    text = _replace_managed_section(text, "Sources", "sources", _render_sources(sources, provenance_by_id))
    text = _replace_managed_section(text, "Local Rules", "rules", _render_rules(rules), aliases=("Rules",))
    text = _replace_managed_section(text, "Local Topics", "topics", _render_topics(topics, project_root, node_root), aliases=("Topics",))
    return text


def _structure_order(nodes) -> list:
    by_key = {node.key: node for node in nodes}
    depths: dict[str, int] = {}
    active: set[str] = set()

    def depth(key: str) -> int:
        if key in depths:
            return depths[key]
        if key in active:
            raise _error(f"accepted semantic Parent cycle includes {key}")
        node = by_key.get(key)
        if node is None:
            raise _error(f"accepted semantic Parent references unknown Node key {key}")
        active.add(key)
        if node.parent_key is None:
            value = 0
        else:
            if node.parent_key not in by_key:
                raise _error(f"accepted semantic Parent {node.parent_key} for {key} is missing")
            value = depth(node.parent_key) + 1
        active.remove(key)
        depths[key] = value
        return value

    return sorted(nodes, key=lambda node: (depth(node.key), node.path, node.key))


def _parent_locator(child_root: Path, parent_root: Path) -> str:
    return Path(os.path.relpath(parent_root, child_root)).as_posix()


def _render_parent_body(parent, compiled_parent, child_root: Path, parent_root: Path) -> tuple[str, str]:
    locator = _parent_locator(child_root, parent_root)
    name = _safe_line(parent.name, f"Parent {parent.key} name")
    if any(char in name for char in "]\n\r"):
        raise _error(f"Parent {parent.key} name cannot be represented safely")
    body = "\n".join([
        f"- [{name}]({locator}) — `{compiled_parent.metadata.version}`",
        (
            f'  <!-- ctx:parent id="{compiled_parent.metadata.id}" version="{compiled_parent.metadata.version}" '
            f'normalized-digest="{compiled_parent.normalized_digest}" '
            f'package-digest="{compiled_parent.package_digest}" -->'
        ),
    ])
    return body, locator


def _assert_parent_block_is_framework_owned(text: str, node_name: str) -> None:
    stripped = _strip_managed_block(text, "parent")
    if re.search(r"ctx:parent\s+", stripped):
        raise _error(
            f"{node_name} already has a Parent outside the ContextCanon onboarding-managed block; "
            "refuse to replace human-authored Parent state implicitly"
        )


def _package_resource_bytes(package_root: Path, package) -> dict[str, bytes]:
    return {
        file.path: (package_root / Path(*PurePosixPath(file.path).parts)).read_bytes()
        for file in package.files
        if file.path.startswith("CONTEXT/references/")
    }


def _compiled_package_override(compiled) -> tuple[object, dict[str, bytes]]:
    package = compiled_package(compiled)
    resources = {
        path: content
        for path, content in compiled.resources.items()
        if path.startswith("CONTEXT/references/")
    }
    return package, resources


def _accepted_by_node(review: OnboardingPlacementReview) -> dict[str, list[PlacementReviewItem]]:
    result: dict[str, list[PlacementReviewItem]] = {}
    for item in review.items:
        if item.decision != "accept" or item.destination_node_key is None:
            continue
        if item.kind not in {"overview", "rule", "topic-resource", "state", "plan", "unresolved"}:
            continue
        result.setdefault(item.destination_node_key, []).append(item)
    return result


def _sources_by_node(review: OnboardingPlacementReview) -> dict[str, list[PlacementReviewSource]]:
    result: dict[str, list[PlacementReviewSource]] = {}
    for source in review.sources:
        if source.decision == "accept":
            result.setdefault(source.target_node_key, []).append(source)
    return result


def _followups(review: OnboardingPlacementReview) -> tuple[PlacementReviewItem, ...]:
    return tuple(
        item
        for item in review.items
        if item.decision == "accept" and item.kind in {"ordinary-documentation", "authority-mapping"}
    )


def build_placement_publication_preview(
    proposal: OnboardingPlacementProposal,
    review: OnboardingPlacementReview,
    snapshot_root: Path,
    *,
    catalog_package_roots: Iterable[Path] = (),
    project_root: Path | None = None,
) -> PlacementPublicationPreview:
    snapshot = load_evidence_snapshot(snapshot_root)
    project = (project_root or find_repo_root(snapshot_root)).resolve()
    if not (project / ".git").exists():
        raise _error(f"target project root is not a Git repository: {project}")
    documents = _expected_document_deltas(snapshot, project, review)
    provenance = _source_provenance(review, proposal, catalog_package_roots)
    provenance_by_id = {item.source_node_id: item for item in provenance}
    items_by_node = _accepted_by_node(review)
    sources_by_node = _sources_by_node(review)
    node_by_key = {node.key: node for node in proposal.structure.nodes}
    ordered_nodes = _structure_order(proposal.structure.nodes)

    source_overrides: dict[Path, str] = {}
    node_before: dict[str, str] = {}
    node_ids: dict[str, str] = {}
    for node in ordered_nodes:
        root = _node_root(project, node.path)
        source_path = root / "CONTEXT.src.md"
        if not source_path.is_file():
            raise _error(f"accepted destination Node is not materialized: {node.name} ({node.path})")
        parsed = parse_node(root, project)
        before = source_path.read_text(encoding="utf-8")
        _assert_parent_block_is_framework_owned(before, node.name)
        if node.key in items_by_node or node.key in sources_by_node:
            after = _render_node_source(
                before,
                project,
                root,
                items_by_node.get(node.key, []),
                sources_by_node.get(node.key, []),
                provenance_by_id,
            )
        else:
            after = before
        node_before[node.key] = before
        node_ids[node.key] = parsed.metadata.id
        source_overrides[root] = after

    file_overrides = {
        document.source_path.resolve(): document.after.encode("utf-8")
        for document in documents
    }
    roots = _catalog_roots(catalog_package_roots)
    package_overrides: dict[tuple[Path, str], tuple[object, dict[str, bytes]]] = {}
    for source in review.sources:
        if source.decision != "accept":
            continue
        target = node_by_key[source.target_node_key]
        target_root = _node_root(project, target.path)
        package_root = roots.get(source.source_node_id)
        if package_root is None:
            raise _error(f"accepted Source {source.source_name} requires exact catalog package root")
        package = load_package(package_root)
        package_overrides[(target_root.resolve(), source.source_package_digest)] = (
            package,
            _package_resource_bytes(package_root, package),
        )

    compiled_by_key: dict[str, object] = {}
    parent_pins: list[PlacementParentPin] = []
    for node in ordered_nodes:
        root = _node_root(project, node.path).resolve()
        if node.parent_key is None:
            source_overrides[root] = _replace_parent_section(source_overrides[root], "")
        else:
            parent = node_by_key[node.parent_key]
            compiled_parent = compiled_by_key.get(parent.key)
            if compiled_parent is None:
                raise _error(f"internal error: Parent {parent.key} was not compiled before Child {node.key}")
            parent_root = _node_root(project, parent.path).resolve()
            body, locator = _render_parent_body(parent, compiled_parent, root, parent_root)
            source_overrides[root] = _replace_parent_section(source_overrides[root], body)
            package_overrides[(root, compiled_parent.package_digest)] = _compiled_package_override(compiled_parent)
            parent_pins.append(
                PlacementParentPin(
                    child_key=node.key,
                    child_name=node.name,
                    child_path=node.path,
                    parent_key=parent.key,
                    parent_name=parent.name,
                    parent_path=parent.path,
                    parent_node_id=compiled_parent.metadata.id,
                    parent_version=compiled_parent.metadata.version,
                    parent_normalized_digest=compiled_parent.normalized_digest,
                    parent_package_digest=compiled_parent.package_digest,
                    locator=locator,
                )
            )

        compiled = Compiler(
            project,
            source_overrides=source_overrides,
            file_overrides=file_overrides,
            package_overrides=package_overrides,
        ).compile(root)
        if compiled.metadata.id != node_ids[node.key]:
            raise _error(f"semantic Parent preview changed stable Node identity for {node.name}")
        compiled_by_key[node.key] = compiled

    deltas = tuple(
        PlacementNodeDelta(
            node.key,
            node.name,
            node.path,
            node_ids[node.key],
            _node_root(project, node.path) / "CONTEXT.src.md",
            node_before[node.key],
            source_overrides[_node_root(project, node.path).resolve()],
        )
        for node in ordered_nodes
    )

    pending = tuple(
        [item.proposal_id for item in review.items if item.decision == "pending"]
        + [f"Source:{source.review_id}" for source in review.sources if source.decision == "pending"]
    )
    return PlacementPublicationPreview(
        project_root=project,
        evidence_digest=proposal.evidence_digest,
        structure_digest=proposal.structure_digest,
        proposal_digest=proposal.proposal_digest,
        review_digest=review.review_digest,
        review_complete=review.is_complete,
        pending_ids=pending,
        nodes=deltas,
        parents=tuple(parent_pins),
        sources=provenance,
        followups=_followups(review),
        documents=documents,
    )

def render_placement_publication_preview(preview: PlacementPublicationPreview) -> str:
    lines = [
        "# ContextCanon placement publication preview",
        "",
        f"Review: `{preview.review_digest}`",
        f"Review complete: **{'yes' if preview.review_complete else 'no'}**",
        "",
        "No project file was changed by this preview. Accepted mutable-Markdown Source After edits are shown below and will be published transactionally with the reviewed Context changes.",
        "",
    ]
    if preview.pending_ids:
        lines.extend(["## Pending review decisions", ""])
        for item_id in preview.pending_ids:
            lines.append(f"- `{item_id}`")
        lines.append("")

    lines.extend(["## Context Node source deltas", ""])
    if not preview.nodes:
        lines.extend(["No accepted placement or semantic Parent changes currently touch a Context Node.", ""])
    for node in preview.nodes:
        lines.extend(
            [
                f"### {node.name} (`{node.path}`)",
                "",
                f"Existing Node ID: `{node.node_id}`",
                f"Source: `{node.source_path.relative_to(preview.project_root).as_posix() or 'CONTEXT.src.md'}`",
                "",
            ]
        )
        diff = list(
            difflib.unified_diff(
                node.before.splitlines(),
                node.after.splitlines(),
                fromfile="current/CONTEXT.src.md",
                tofile="reviewed/CONTEXT.src.md",
                lineterm="",
            )
        )
        if diff:
            lines.extend(["```diff", *diff, "```", ""])
        else:
            lines.extend(["No source delta; the reviewed placement is already materialized.", ""])

    lines.extend(["## Accepted semantic Parent chain", ""])
    if not preview.parents:
        lines.extend(["No non-root Context Node is present in the accepted structure.", ""])
    else:
        for parent in preview.parents:
            lines.extend([
                f"- **{parent.child_name}** (`{parent.child_path}`) → **{parent.parent_name}** (`{parent.parent_path}`)",
                f"  - Parent Node: `{parent.parent_node_id}`",
                f"  - accepted package: `{parent.parent_package_digest}`",
                f"  - locator: `{parent.locator}` (discovery/navigation metadata; ordinary build uses the exact local pin)",
            ])
        lines.append("")

    lines.extend(["## Accepted reusable Source state", ""])
    if not preview.sources:
        lines.extend(["No reusable Source is accepted in the current review.", ""])
    for source in preview.sources:
        lines.extend(
            [
                f"- **{source.source_name}** — origin: `{source.origin}`",
                f"  - Source Node: `{source.source_node_id}`",
                f"  - version: `{source.source_version}`",
                f"  - package: `{source.source_package_digest}`",
                f"  - Git: `{source.locator}` @ `{source.ref}`",
                f"  - node-path: `{source.node_path}`",
                "  - the exact reviewed immutable package will be copied into the consumer Node's local `.context/sources/` store",
            ]
        )
    if preview.sources:
        lines.append("")

    lines.extend(["## Accepted findings kept durably outside current Node authoring", ""])
    if not preview.followups:
        lines.extend(["None.", ""])
    else:
        for item in preview.followups:
            lines.append(
                f"- `{item.proposal_id}` · `{item.kind}` · **{item.title}** — retained in the exact placement acceptance/follow-up state; not spliced into arbitrary prose files"
            )
        lines.append("")

    lines.extend(["## Reviewed source-document deltas", ""])
    if not preview.documents:
        lines.extend(["No Source After edits are accepted in the current review.", ""])
    for document in preview.documents:
        lines.extend([f"### `{document.path}`", "", f"Source edits: {', '.join(f'`{item}`' for item in document.source_edit_ids)}", ""])
        diff = list(
            difflib.unified_diff(
                document.before.splitlines(), document.after.splitlines(),
                fromfile=f"current/{document.path}", tofile=f"reviewed/{document.path}", lineterm="",
            )
        )
        if diff:
            lines.extend(["```diff", *diff, "```", ""])
        else:
            lines.extend(["No document delta; this reviewed Source After transformation is already materialized.", ""])
    return "\n".join(lines).rstrip() + "\n"


def _copy_exact_package(package_root: Path, target_root: Path, expected_digest: str) -> bool:
    destination = target_root / ".context" / "sources" / expected_digest
    if destination.exists():
        package = load_package(destination)
        if package.package_digest != expected_digest:
            raise _error(f"accepted Source store path contains different package: {destination}")
        return False
    package = load_package(package_root)
    if package.package_digest != expected_digest:
        raise _error(f"catalog package digest changed before publication: {package_root}")
    staging = Path(tempfile.mkdtemp(prefix=f".{expected_digest[:12]}-", dir=(target_root / ".context" / "sources").parent if (target_root / ".context" / "sources").parent.exists() else target_root))
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        manifest_target = staging / PACKAGE_MANIFEST_PATH
        manifest_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(package_root / PACKAGE_MANIFEST_PATH, manifest_target)
        for file in package.files:
            source = package_root / Path(*PurePosixPath(file.path).parts)
            target = staging / Path(*PurePosixPath(file.path).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        staged = load_package(staging)
        if staged.package_digest != package.package_digest or staged.normalized_digest != package.normalized_digest:
            raise _error("Source package identity changed while staging publication")
        os.replace(staging, destination)
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
    return True


def _copy_compiled_package(compiled, target_root: Path) -> bool:
    expected_digest = compiled.package_digest
    destination = target_root / ".context" / "sources" / expected_digest
    if destination.exists():
        package = load_package(destination)
        if (
            package.metadata.id != compiled.metadata.id
            or package.normalized_digest != compiled.normalized_digest
            or package.package_digest != expected_digest
        ):
            raise _error(f"accepted Parent store path contains different package: {destination}")
        return False

    store = destination.parent
    store.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{expected_digest[:12]}-", dir=store))
    try:
        for rel, content in artifact_files(compiled).items():
            target = staging / Path(*PurePosixPath(rel).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        staged = load_package(staging)
        if (
            staged.metadata.id != compiled.metadata.id
            or staged.normalized_digest != compiled.normalized_digest
            or staged.package_digest != expected_digest
        ):
            raise _error("Parent package identity changed while staging publication")
        os.replace(staging, destination)
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
    return True


def _publication_order(preview: PlacementPublicationPreview) -> list[PlacementNodeDelta]:
    by_key = {delta.key: delta for delta in preview.nodes}
    parent_by_child = {parent.child_key: parent.parent_key for parent in preview.parents}
    depths: dict[str, int] = {}
    active: set[str] = set()

    def depth(key: str) -> int:
        if key in depths:
            return depths[key]
        if key in active:
            raise _error(f"semantic Parent cycle in publication preview includes {key}")
        if key not in by_key:
            raise _error(f"publication preview Parent references missing Child {key}")
        active.add(key)
        parent_key = parent_by_child.get(key)
        if parent_key is None:
            value = 0
        else:
            if parent_key not in by_key:
                raise _error(f"publication preview Parent {parent_key} is missing")
            value = depth(parent_key) + 1
        active.remove(key)
        depths[key] = value
        return value

    return sorted(preview.nodes, key=lambda delta: (depth(delta.key), delta.path, delta.key))


def _snapshot_files(root: Path, rels: Iterable[str]) -> dict[str, bytes | None]:
    result: dict[str, bytes | None] = {}
    for rel in set(rels):
        path = root / Path(*PurePosixPath(rel).parts)
        result[rel] = path.read_bytes() if path.is_file() else None
    return result


def _existing_context_files(root: Path) -> set[str]:
    context = root / "CONTEXT"
    if not context.is_dir():
        return set()
    return {path.relative_to(root).as_posix() for path in context.rglob("*") if path.is_file()}


def _restore_files(root: Path, snapshot: dict[str, bytes | None], extra_rels: Iterable[str] = ()) -> None:
    for rel in set(snapshot) | set(extra_rels):
        path = root / Path(*PurePosixPath(rel).parts)
        before = snapshot.get(rel)
        if before is None:
            if path.is_file() or path.is_symlink():
                path.unlink(missing_ok=True)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(before)
    context = root / "CONTEXT"
    if context.is_dir():
        for directory in sorted((path for path in context.rglob("*") if path.is_dir()), key=lambda p: len(p.parts), reverse=True):
            try:
                directory.rmdir()
            except OSError:
                pass
        try:
            context.rmdir()
        except OSError:
            pass


def _acceptance_payload(
    preview: PlacementPublicationPreview,
    review: OnboardingPlacementReview,
    node_digests: dict[str, dict[str, str]],
) -> dict[str, object]:
    source_by_id = {source.source_node_id: source for source in preview.sources}
    accepted_sources = []
    for source in review.sources:
        if source.decision != "accept":
            continue
        provenance = source_by_id[source.source_node_id]
        accepted_sources.append(
            {
                **source.to_dict(),
                "git": provenance.to_dict(),
            }
        )
    return {
        "schema": PLACEMENT_ACCEPTANCE_SCHEMA,
        "evidence_digest": preview.evidence_digest,
        "structure_digest": preview.structure_digest,
        "proposal_digest": preview.proposal_digest,
        "review_digest": preview.review_digest,
        "nodes": node_digests,
        "parents": [parent.to_dict() for parent in preview.parents],
        "sources": accepted_sources,
        "followups": [item.to_dict() for item in preview.followups],
        "source_edits": [edit.to_dict() for edit in review.source_edits if edit.decision == "accept"],
        "documents": [
            {
                "path": document.path,
                "source_edit_ids": list(document.source_edit_ids),
                "after_sha256": _sha256_bytes(document.after.encode("utf-8")),
            }
            for document in preview.documents
        ],
    }


def render_placement_followups(preview: PlacementPublicationPreview) -> str:
    lines = [
        "# ContextCanon placement follow-up",
        "",
        f"Reviewed placement: `{preview.review_digest}`",
        "",
        "These accepted findings intentionally were not forced into today's `CONTEXT.src.md` grammar or into arbitrary project prose. They remain bound to the exact reviewed placement and are work for explicit later handling.",
        "",
    ]
    groups = (("authority-mapping", "Fixed-authority mappings"), ("ordinary-documentation", "Ordinary documentation"))
    for kind, title in groups:
        items = [item for item in preview.followups if item.kind == kind]
        if not items:
            continue
        lines.extend([f"## {title}", ""])
        for item in items:
            lines.extend([f"### {item.proposal_id} — {item.title}", "", "```json", json.dumps(item.payload, ensure_ascii=False, indent=2, sort_keys=True), "```", ""])
    lines.extend(["## Reviewed mutable-Markdown transformations", ""])
    if not preview.documents:
        lines.append("None.")
    else:
        for document in preview.documents:
            state = "changed" if document.changed else "already materialized"
            lines.append(f"- `{document.path}` — {state}; Source edits: {', '.join(document.source_edit_ids)}")
    return "\n".join(lines).rstrip() + "\n"


def _legacy_parent_acceptance_upgrade(
    content: bytes | None,
    preview: PlacementPublicationPreview,
) -> bool:
    """Recognize the one safe in-place upgrade from pre-Parent placement acceptance.

    The legacy acceptance must be the exact same reviewed placement and every
    Node source byte it certified must still be current. This is deliberately
    narrower than general acceptance replacement: post-publication human edits
    require a fresh explicit workflow rather than being swept into migration.
    """

    if content is None:
        return False
    try:
        raw = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return False
    if not isinstance(raw, dict) or "parents" in raw:
        return False
    identity = {
        "evidence_digest": preview.evidence_digest,
        "structure_digest": preview.structure_digest,
        "proposal_digest": preview.proposal_digest,
        "review_digest": preview.review_digest,
    }
    if any(raw.get(key) != value for key, value in identity.items()):
        return False
    if raw.get("schema") != PLACEMENT_ACCEPTANCE_SCHEMA:
        return False

    nodes = raw.get("nodes")
    if not isinstance(nodes, dict):
        raise _error("legacy placement acceptance has no verifiable Node state for Parent migration")
    by_key = {delta.key: delta for delta in preview.nodes}
    missing = sorted(set(by_key) - set(nodes))
    if missing:
        raise _error(
            "legacy placement acceptance does not cover every accepted structure Node needed for automatic Parent migration: "
            + ", ".join(missing)
        )
    for key, delta in by_key.items():
        state = nodes.get(key)
        if not isinstance(state, dict):
            raise _error(f"legacy placement acceptance Node state is invalid for {key}")
        expected_source = state.get("source_sha256")
        current_source = _sha256_bytes(delta.before.encode("utf-8"))
        if state.get("node_id") != delta.node_id or state.get("path") != delta.path:
            raise _error(f"legacy placement acceptance Node identity changed for {key}; refuse automatic Parent migration")
        if expected_source != current_source:
            raise _error(
                f"{delta.name} changed after the legacy placement acceptance; refuse automatic Parent migration and review the current Node explicitly"
            )
    return True


def publish_placement_review(
    preview: PlacementPublicationPreview,
    review: OnboardingPlacementReview,
    *,
    snapshot_root: Path,
    catalog_package_roots: Iterable[Path] = (),
    acceptance_path: Path,
) -> PlacementPublicationResult:
    if review.review_digest != preview.review_digest:
        raise _error("review changed after publication preview; build a fresh preview")
    if (
        review.evidence_digest != preview.evidence_digest
        or review.structure_digest != preview.structure_digest
        or review.proposal_digest != preview.proposal_digest
    ):
        raise _error("review identity does not match publication preview")
    if not preview.review_complete or not review.is_complete:
        raise _error("review still contains pending decisions; publication requires a complete human review")
    project = preview.project_root
    snapshot = load_evidence_snapshot(snapshot_root)
    expected_documents = _expected_document_deltas(snapshot, project, review)
    if expected_documents != preview.documents:
        raise _error("reviewed source documents changed after publication preview; build a fresh preview")
    for delta in preview.nodes:
        if not delta.source_path.is_file() or delta.source_path.read_text(encoding="utf-8") != delta.before:
            raise _error(
                f"Context Node source changed after publication preview: {delta.source_path}; build a fresh preview"
            )
    for document in preview.documents:
        if not document.source_path.is_file() or document.source_path.read_text(encoding="utf-8") != document.before:
            raise _error(f"Source document changed after publication preview: {document.path}; build a fresh preview")

    roots = _catalog_roots(catalog_package_roots)
    delta_by_key = {delta.key: delta for delta in preview.nodes}
    original_sources = {delta.source_path: delta.before.encode("utf-8") for delta in preview.nodes}
    original_documents = {document.source_path: document.before.encode("utf-8") for document in preview.documents}
    new_package_dirs: list[Path] = []
    generated_snapshots: dict[Path, dict[str, bytes | None]] = {}
    generated_new_rels: dict[Path, set[str]] = {}
    acceptance_before = acceptance_path.read_bytes() if acceptance_path.is_file() else None
    legacy_parent_upgrade = _legacy_parent_acceptance_upgrade(acceptance_before, preview)

    try:
        for delta in preview.nodes:
            if delta.changed:
                _atomic_write(delta.source_path, delta.after.encode("utf-8"))
        for document in preview.documents:
            if document.changed:
                _atomic_write(document.source_path, document.after.encode("utf-8"))

        accepted_sources_by_node = _sources_by_node(review)
        provenance_by_id = {source.source_node_id: source for source in preview.sources}
        for key, sources in accepted_sources_by_node.items():
            delta = delta_by_key.get(key)
            if delta is None:
                raise _error(f"internal error: accepted Source target {key} has no publication delta")
            target_root = delta.source_path.parent
            for source in sources:
                provenance = provenance_by_id[source.source_node_id]
                root = roots.get(source.source_node_id)
                if root is None:
                    raise _error(f"accepted Source {source.source_name} requires exact catalog package root")
                destination = target_root / ".context" / "sources" / source.source_package_digest
                if _copy_exact_package(root, target_root, source.source_package_digest):
                    new_package_dirs.append(destination)

        parent_by_child = {parent.child_key: parent for parent in preview.parents}
        compiled_by_key: dict[str, object] = {}
        compiled_nodes = []
        for delta in _publication_order(preview):
            parent_pin = parent_by_child.get(delta.key)
            if parent_pin is not None:
                compiled_parent = compiled_by_key.get(parent_pin.parent_key)
                if compiled_parent is None:
                    raise _error(
                        f"internal error: Parent {parent_pin.parent_key} was not compiled before Child {delta.key}"
                    )
                if (
                    compiled_parent.metadata.id != parent_pin.parent_node_id
                    or compiled_parent.metadata.version != parent_pin.parent_version
                    or compiled_parent.normalized_digest != parent_pin.parent_normalized_digest
                    or compiled_parent.package_digest != parent_pin.parent_package_digest
                ):
                    raise _error(
                        f"Parent {parent_pin.parent_name} changed between publication preview and publication"
                    )
                destination = delta.source_path.parent / ".context" / "sources" / compiled_parent.package_digest
                if _copy_compiled_package(compiled_parent, delta.source_path.parent):
                    new_package_dirs.append(destination)

            compiled = Compiler(project).compile(delta.source_path.parent)
            if compiled.metadata.id != delta.node_id:
                raise _error(f"publication changed stable Node identity for {delta.name}")
            if parent_pin is not None:
                if compiled.parent_package is None or compiled.parent_package.package_digest != parent_pin.parent_package_digest:
                    raise _error(f"published Parent pin for {delta.name} does not match reviewed preview")
            compiled_by_key[delta.key] = compiled
            compiled_nodes.append(compiled)

        for compiled in compiled_nodes:
            root = compiled.parsed.root
            current_rels = set(expected_outputs(compiled)) | _existing_context_files(root)
            generated_snapshots[root] = _snapshot_files(root, current_rels)
            generated_new_rels[root] = set(expected_outputs(compiled))

        for compiled in compiled_nodes:
            write_outputs(compiled)

        verifier = Compiler(project)
        node_digests: dict[str, dict[str, str]] = {}
        for delta in preview.nodes:
            compiled = verifier.compile(delta.source_path.parent)
            state = {
                "node_id": compiled.metadata.id,
                "path": delta.path,
                "normalized_digest": compiled.normalized_digest,
                "package_digest": compiled.package_digest,
                "source_sha256": _sha256_bytes(delta.source_path.read_bytes()),
            }
            if compiled.parent_package is not None:
                state["parent_node_id"] = compiled.parent_package.metadata.id
                state["parent_package_digest"] = compiled.parent_package.package_digest
            node_digests[delta.key] = state

        payload = _acceptance_payload(preview, review, node_digests)
        encoded = (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
        if acceptance_path.is_file() and acceptance_path.read_bytes() != encoded and not legacy_parent_upgrade:
            raise _error(
                f"placement acceptance record already exists with different exact content: {acceptance_path}"
            )
        if not acceptance_path.is_file() or acceptance_path.read_bytes() != encoded:
            _atomic_write(acceptance_path, encoded)
        digest = _sha256_bytes(encoded)
        return PlacementPublicationResult(
            acceptance_path=acceptance_path,
            review_digest=preview.review_digest,
            changed_sources=tuple(delta.source_path for delta in preview.nodes if delta.changed),
            acceptance_digest=digest,
        )
    except BaseException:
        for root, snapshot in generated_snapshots.items():
            _restore_files(root, snapshot, generated_new_rels.get(root, set()))
        for path, content in original_sources.items():
            _atomic_write(path, content)
        for path, content in original_documents.items():
            _atomic_write(path, content)
        for directory in reversed(new_package_dirs):
            if directory.exists():
                shutil.rmtree(directory, ignore_errors=True)
        if acceptance_before is None:
            acceptance_path.unlink(missing_ok=True)
        else:
            _atomic_write(acceptance_path, acceptance_before)
        raise
