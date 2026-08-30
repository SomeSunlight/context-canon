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
from .onboarding_placement_review import OnboardingPlacementReview, PlacementReviewItem, PlacementReviewSource
from .onboarding_proposal import EvidenceSnapshot, load_evidence_snapshot
from .outputs import expected_outputs, write_outputs
from .package import PACKAGE_MANIFEST_PATH, load_package
from .parser import ContextCanonError, find_repo_root, parse_node


PLACEMENT_ACCEPTANCE_SCHEMA = "contextcanon/onboarding-placement-acceptance/v1"

_MANAGED_SECTIONS = ("overview", "sources", "rules", "topics")
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
class PlacementPublicationPreview:
    project_root: Path
    evidence_digest: str
    structure_digest: str
    proposal_digest: str
    review_digest: str
    review_complete: bool
    pending_ids: tuple[str, ...]
    nodes: tuple[PlacementNodeDelta, ...]
    sources: tuple[SourceGitProvenance, ...]
    followups: tuple[PlacementReviewItem, ...]
    mutable_cleanup_candidates: tuple[dict[str, object], ...]


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


def _verify_live_evidence(snapshot: EvidenceSnapshot, project_root: Path) -> None:
    for entry in snapshot.entries:
        live = project_root / Path(*PurePosixPath(entry.path).parts)
        if not live.is_file():
            raise _error(f"frozen Evidence path is missing from the live project: {entry.path}")
        if _sha256_bytes(live.read_bytes()) != entry.sha256:
            raise _error(
                f"frozen Evidence changed after semantic review: {entry.path}; prepare a new snapshot rather than publishing stale placement"
            )


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
    return SourceGitProvenance(source.source_node_id, locator, ref, node_path, package_root)


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


def _replace_managed_section(text: str, section: str, name: str, body: str) -> str:
    text = _strip_managed_block(text, name)
    if not body.strip():
        return text.rstrip() + "\n"
    block = f"{_MARKER_START[name]}\n{body.rstrip()}\n{_MARKER_END[name]}"
    heading_pattern = re.compile(rf"(?m)^## {re.escape(section)}\s*$")
    heading = heading_pattern.search(text)
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
        lines.extend([f'<!-- cc:placement-overview id="{item.authoring_id}" -->', text, ""])
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
        lines.extend(
            [
                f"- [{name}]({provenance.locator}) — `{source.source_version}`",
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
    if overviews or rules or topics or sources:
        text = _remove_skeleton_placeholder(text)
    text = _replace_managed_section(text, "Overview", "overview", _render_overviews(overviews))
    text = _replace_managed_section(text, "Sources", "sources", _render_sources(sources, provenance_by_id))
    text = _replace_managed_section(text, "Rules", "rules", _render_rules(rules))
    text = _replace_managed_section(text, "Topics", "topics", _render_topics(topics, project_root, node_root))
    return text


def _accepted_by_node(review: OnboardingPlacementReview) -> dict[str, list[PlacementReviewItem]]:
    result: dict[str, list[PlacementReviewItem]] = {}
    for item in review.items:
        if item.decision != "accept" or item.destination_node_key is None:
            continue
        if item.kind not in {"overview", "rule", "topic-resource"}:
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
        if item.decision == "accept" and item.kind in {"state", "plan", "ordinary-documentation", "authority-mapping", "unresolved"}
    )


def _mutable_cleanup_candidates(
    review: OnboardingPlacementReview, proposal: OnboardingPlacementProposal
) -> tuple[dict[str, object], ...]:
    fixed = set(proposal.structure.fixed_markdown)
    proposal_by_id = {item.id: item for item in proposal.items}
    result: list[dict[str, object]] = []
    for item in review.items:
        if item.decision != "accept" or item.action != "promote":
            continue
        original = proposal_by_id[item.proposal_id]
        paths = sorted({reference.path for reference in original.evidence if reference.path.endswith(".md") and reference.path not in fixed})
        if not paths:
            continue
        result.append(
            {
                "proposal_id": item.proposal_id,
                "authoring_id": item.authoring_id,
                "title": item.title,
                "paths": paths,
                "note": "Potential duplicate cleanup only; no Markdown cleanup is performed by placement publication.",
            }
        )
    return tuple(result)


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
    _verify_live_evidence(snapshot, project)
    provenance = _source_provenance(review, proposal, catalog_package_roots)
    provenance_by_id = {item.source_node_id: item for item in provenance}
    items_by_node = _accepted_by_node(review)
    sources_by_node = _sources_by_node(review)
    node_by_key = {node.key: node for node in proposal.structure.nodes}
    touched_keys = sorted(set(items_by_node) | set(sources_by_node), key=lambda key: node_by_key[key].path)

    deltas: list[PlacementNodeDelta] = []
    for key in touched_keys:
        node = node_by_key[key]
        root = _node_root(project, node.path)
        source_path = root / "CONTEXT.src.md"
        if not source_path.is_file():
            raise _error(f"accepted destination Node is not materialized: {node.name} ({node.path})")
        parsed = parse_node(root, project)
        before = source_path.read_text(encoding="utf-8")
        after = _render_node_source(
            before,
            project,
            root,
            items_by_node.get(key, []),
            sources_by_node.get(key, []),
            provenance_by_id,
        )
        deltas.append(PlacementNodeDelta(key, node.name, node.path, parsed.metadata.id, source_path, before, after))

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
        nodes=tuple(deltas),
        sources=provenance,
        followups=_followups(review),
        mutable_cleanup_candidates=_mutable_cleanup_candidates(review, proposal),
    )


def render_placement_publication_preview(preview: PlacementPublicationPreview) -> str:
    lines = [
        "# ContextCanon placement publication preview",
        "",
        f"Review: `{preview.review_digest}`",
        f"Review complete: **{'yes' if preview.review_complete else 'no'}**",
        "",
        "No project file was changed by this preview. Existing README, architecture, CONTRIBUTING and other mutable Markdown remain untouched; possible duplicate cleanup is a separate later review.",
        "",
    ]
    if preview.pending_ids:
        lines.extend(["## Pending review decisions", ""])
        for item_id in preview.pending_ids:
            lines.append(f"- `{item_id}`")
        lines.append("")

    lines.extend(["## Context Node source deltas", ""])
    if not preview.nodes:
        lines.extend(["No accepted Overview, Rule, Topic/Resource or Source changes currently touch a Context Node.", ""])
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

    lines.extend(["## Accepted reusable Source state", ""])
    if not preview.sources:
        lines.extend(["No reusable Source is accepted in the current review.", ""])
    for source in preview.sources:
        lines.extend(
            [
                f"- `{source.source_node_id}` from `{source.locator}`",
                f"  - ref: `{source.ref}`",
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

    lines.extend(["## Mutable Markdown cleanup candidates — deferred", ""])
    if not preview.mutable_cleanup_candidates:
        lines.extend(["None.", ""])
    else:
        for candidate in preview.mutable_cleanup_candidates:
            paths = ", ".join(f"`{path}`" for path in candidate["paths"])
            lines.append(f"- `{candidate['proposal_id']}` — {paths}: {candidate['note']}")
        lines.append("")
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
        "sources": accepted_sources,
        "followups": [item.to_dict() for item in preview.followups],
        "mutable_cleanup_candidates": list(preview.mutable_cleanup_candidates),
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
    groups = (("state", "State"), ("plan", "Plan"), ("authority-mapping", "Fixed-authority mappings"), ("ordinary-documentation", "Ordinary documentation"), ("unresolved", "Unresolved"))
    for kind, title in groups:
        items = [item for item in preview.followups if item.kind == kind]
        if not items:
            continue
        lines.extend([f"## {title}", ""])
        for item in items:
            lines.extend([f"### {item.proposal_id} — {item.title}", "", "```json", json.dumps(item.payload, ensure_ascii=False, indent=2, sort_keys=True), "```", ""])
    lines.extend(["## Mutable Markdown cleanup candidates — not applied", ""])
    if not preview.mutable_cleanup_candidates:
        lines.append("None.")
    else:
        for candidate in preview.mutable_cleanup_candidates:
            paths = ", ".join(f"`{path}`" for path in candidate["paths"])
            lines.append(f"- `{candidate['proposal_id']}` — {paths}")
    return "\n".join(lines).rstrip() + "\n"


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
    _verify_live_evidence(snapshot, project)
    for delta in preview.nodes:
        if not delta.source_path.is_file() or delta.source_path.read_text(encoding="utf-8") != delta.before:
            raise _error(
                f"Context Node source changed after publication preview: {delta.source_path}; build a fresh preview"
            )
    roots = _catalog_roots(catalog_package_roots)
    delta_by_key = {delta.key: delta for delta in preview.nodes}
    node_by_path = {delta.source_path.parent: delta for delta in preview.nodes}
    original_sources = {delta.source_path: delta.before.encode("utf-8") for delta in preview.nodes}
    new_package_dirs: list[Path] = []
    generated_snapshots: dict[Path, dict[str, bytes | None]] = {}
    generated_new_rels: dict[Path, set[str]] = {}
    acceptance_before = acceptance_path.read_bytes() if acceptance_path.is_file() else None

    try:
        # Publish reviewed source text and exact local Source package state first; compile all touched Nodes before any generated output is written.
        for delta in preview.nodes:
            if delta.changed:
                _atomic_write(delta.source_path, delta.after.encode("utf-8"))

        accepted_sources_by_node = _sources_by_node(review)
        provenance_by_id = {source.source_node_id: source for source in preview.sources}
        for key, sources in accepted_sources_by_node.items():
            node = next(node for node in review.items if False) if False else None
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

        compiler = Compiler(project)
        compiled_nodes = []
        for root in node_by_path:
            compiled_nodes.append(compiler.compile(root))

        # Snapshot all current/new compiler-owned paths before write_outputs can remove or replace them.
        for compiled in compiled_nodes:
            root = compiled.parsed.root
            current_compiler = Compiler(project).compile(root)
            current_rels = set(expected_outputs(current_compiler)) | _existing_context_files(root)
            new_rels = set(expected_outputs(compiled)) | _existing_context_files(root)
            generated_snapshots[root] = _snapshot_files(root, current_rels | new_rels)
            generated_new_rels[root] = new_rels

        for compiled in compiled_nodes:
            write_outputs(compiled)

        # Verify the exact resulting package state after generated outputs are materialized.
        verifier = Compiler(project)
        node_digests: dict[str, dict[str, str]] = {}
        for delta in preview.nodes:
            compiled = verifier.compile(delta.source_path.parent)
            node_digests[delta.key] = {
                "node_id": compiled.metadata.id,
                "path": delta.path,
                "normalized_digest": compiled.normalized_digest,
                "package_digest": compiled.package_digest,
                "source_sha256": _sha256_bytes(delta.source_path.read_bytes()),
            }

        payload = _acceptance_payload(preview, review, node_digests)
        encoded = (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
        if acceptance_path.is_file() and acceptance_path.read_bytes() != encoded:
            raise _error(
                f"placement acceptance record already exists with different exact content: {acceptance_path}"
            )
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
        for directory in reversed(new_package_dirs):
            if directory.exists():
                shutil.rmtree(directory, ignore_errors=True)
        if acceptance_before is None:
            acceptance_path.unlink(missing_ok=True)
        else:
            _atomic_write(acceptance_path, acceptance_before)
        raise
