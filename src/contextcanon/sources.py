from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from .compiler import Compiler
from .diff import ContextDiff, diff_compiled
from .config import CONFIG_FILENAME, config_path, upsert_local_source
from .git_transport import load_candidate_provenance
from .model import CompiledNode, CompiledPackage, ParentRef, Rule, SourceRef
from .package import PACKAGE_MANIFEST_PATH, artifact_files, compiled_package, load_package
from .package_diff import diff_packages
from .parser import ContextCanonError, find_repo_root, parse_node
from .versioning import ensure_node_version_advanced

REVIEW_SCHEMA = "contextcanon/source-review/v0"
PARENT_REVIEW_SCHEMA = "contextcanon/parent-review/v0"
_ATTR_RE = re.compile(r'([A-Za-z_][A-Za-z0-9_-]*)="([^"]*)"')
_SOURCE_COMMENT_RE = re.compile(r'^(?P<indent>\s*)<!--\s*ctx:source\s+(?P<attrs>.*?)\s*-->(?P<ending>\r?\n?)$')
_PARENT_COMMENT_RE = re.compile(r'^(?P<indent>\s*)<!--\s*ctx:parent\s+(?P<attrs>.*?)\s*-->(?P<ending>\r?\n?)$')
_SOURCE_LINE_RE = re.compile(
    r'^(?P<prefix>(?P<bullet>- )\[[^]]+\]\((?P<path>[^)]+)\)(?P<separator>\s+—\s+))`[^`]+`(?P<ending>\s*(?:\r?\n)?)$'
)


def _validate_local_adoption_checkout(package_root: Path) -> None:
    """Reject dirty Git-backed package bytes without requiring Git or a remote for pure local repositories."""
    try:
        repository_result = subprocess.run(
            ["git", "-C", str(package_root), "rev-parse", "--show-toplevel"],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False,
        )
    except (FileNotFoundError, OSError):
        return
    if repository_result.returncode != 0:
        return
    repository = Path(repository_result.stdout.strip()).resolve()
    try:
        node_path = package_root.resolve().relative_to(repository).as_posix() or "."
    except ValueError as exc:
        raise ContextCanonError(f"Source package root is not inside its Git repository: {package_root}") from exc
    status = subprocess.run(
        ["git", "-C", str(repository), "status", "--porcelain", "--untracked-files=all", "--", node_path],
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False,
    )
    if status.returncode != 0:
        detail = status.stderr.strip() or status.stdout.strip() or f"exit code {status.returncode}"
        raise ContextCanonError(f"Could not verify local Source package cleanliness: {detail}")
    if status.stdout.strip():
        raise ContextCanonError("Source package path has uncommitted changes; exact adoption bytes would be ambiguous")


def adopt_source_package(node_root: Path, package_root: Path) -> tuple[CompiledPackage, bool]:
    """Explicitly adopt one exact published local package and register local discovery centrally."""

    node_root = node_root.resolve()
    package_root = package_root.resolve()
    _validate_local_adoption_checkout(package_root)
    repo_root = find_repo_root(node_root)
    parsed = parse_node(node_root, repo_root)
    candidate = load_package(package_root)

    if candidate.metadata.id == parsed.metadata.id:
        raise ContextCanonError(f"{parsed.metadata.name}: a Node cannot adopt itself as a Source")
    if any(parent.id == candidate.metadata.id for parent in parsed.parents):
        raise ContextCanonError(
            f"{parsed.metadata.name}: Node {candidate.metadata.id} is already the semantic Parent and cannot also be a Source"
        )

    matches = [source for source in parsed.sources if source.id == candidate.metadata.id]
    if matches:
        if len(matches) != 1:
            raise ContextCanonError(f"{parsed.metadata.name}: Source Node ID {candidate.metadata.id} is not unique")
        existing = matches[0]
        if (
            existing.is_pinned
            and existing.version == candidate.metadata.version
            and existing.normalized_digest == candidate.normalized_digest
            and existing.package_digest == candidate.package_digest
        ):
            _install_package(node_root, package_root, candidate)
            upsert_local_source(repo_root, candidate.metadata.id, package_root)
            Compiler(repo_root).compile(node_root)
            return candidate, False
        raise ContextCanonError(
            f"{parsed.metadata.name}: Source {candidate.metadata.name} ({candidate.metadata.id}) already exists with a different accepted package; use 'contextcanon source update' or fetch/review/accept"
        )

    config = config_path(repo_root)
    config_before = config.read_bytes() if config.is_file() else None
    entry = _render_adopted_source(node_root, repo_root, candidate)
    source_path = node_root / "CONTEXT.src.md"
    before = source_path.read_text(encoding="utf-8")
    after = _insert_source_entry(before, entry)

    resources = {
        file.path: (package_root / file.path).read_bytes()
        for file in candidate.files
        if file.path.startswith("CONTEXT/references/")
    }
    preview = Compiler(
        repo_root,
        source_overrides={node_root: after},
        package_overrides={(node_root, candidate.package_digest): (candidate, resources)},
    )
    preview.compile(node_root)

    destination = node_root / ".context" / "sources" / candidate.package_digest
    existed = destination.exists()
    _install_package(node_root, package_root, candidate)
    try:
        upsert_local_source(repo_root, candidate.metadata.id, package_root)
        _atomic_write_text(source_path, after)
        Compiler(repo_root).compile(node_root)
    except Exception:
        _atomic_write_text(source_path, before)
        if not existed and destination.exists():
            shutil.rmtree(destination, ignore_errors=True)
        if config_before is None:
            config.unlink(missing_ok=True)
        else:
            config.write_bytes(config_before)
        raise
    return candidate, True

def _render_adopted_source(node_root: Path, repo_root: Path, candidate: CompiledPackage) -> str:
    name = candidate.metadata.name
    if any(char in name for char in "]\n\r"):
        raise ContextCanonError(f"Source name cannot be represented safely: {name!r}")
    locator = Path(os.path.relpath(repo_root / CONFIG_FILENAME, node_root)).as_posix()
    return "\n".join(
        [
            f"- [{name}]({locator}) — `{candidate.metadata.version}`",
            (
                f'  <!-- ctx:source id="{candidate.metadata.id}" version="{candidate.metadata.version}" '
                f'normalized-digest="{candidate.normalized_digest}" '
                f'package-digest="{candidate.package_digest}" -->'
            ),
        ]
    )

def _insert_source_entry(text: str, entry: str) -> str:
    heading = re.search(r"(?m)^## Sources\s*$", text)
    if heading is None:
        return text.rstrip() + "\n\n## Sources\n\n" + entry.rstrip() + "\n"
    next_heading = re.compile(r"(?m)^## .+$").search(text, heading.end())
    insert_at = next_heading.start() if next_heading else len(text)
    before = text[:insert_at].rstrip()
    after = text[insert_at:].lstrip("\n")
    result = before + "\n\n" + entry.rstrip() + "\n"
    if after:
        result += "\n" + after
    return result.rstrip() + "\n"


def _require_candidate_version_advance(current: CompiledPackage, candidate: CompiledPackage, relation: str) -> None:
    if current.package_digest != candidate.package_digest and current.metadata.version == candidate.metadata.version:
        raise ContextCanonError(
            f"{relation} candidate {candidate.metadata.name} changed package identity but reused version "
            f"{candidate.metadata.version!r}; advance the provider Node version before accepting this candidate"
        )


def review_source_candidate(
    node_root: Path,
    source_id: str,
    candidate_root: Path,
) -> tuple[ContextDiff, Path]:
    """Review one candidate against the consumer's currently accepted Source.

    The function performs exact package diff plus the consumer's structural
    composition checks, then writes a receipt bound to the current
    CONTEXT.src.md bytes. It does not modify accepted pins or packages.
    """

    node_root = node_root.resolve()
    candidate = load_package(candidate_root.resolve())
    compiler = Compiler(find_repo_root(node_root))
    compiled = compiler.compile(node_root)
    index, source_ref = _source_index(compiled, source_id)
    current = compiled.source_packages[index]

    if candidate.metadata.id != source_ref.id:
        raise ContextCanonError(
            f"Candidate Node ID {candidate.metadata.id} does not match Source {source_ref.name} ({source_ref.id})"
        )
    _require_candidate_version_advance(current, candidate, "Source")

    transport_candidate = _validated_candidate_provenance(node_root, source_ref, candidate)
    _validate_candidate_composition(compiler, compiled, index, candidate)
    result = diff_packages(current, candidate)

    source_hash = _source_hash(node_root)
    receipt = {
        "schema": REVIEW_SCHEMA,
        "source_id": source_id,
        "consumer_node_id": compiled.metadata.id,
        "source_file_sha256": source_hash,
        "before": {
            "version": current.metadata.version,
            "normalized_digest": current.normalized_digest,
            "package_digest": current.package_digest,
        },
        "candidate": {
            "version": candidate.metadata.version,
            "normalized_digest": candidate.normalized_digest,
            "package_digest": candidate.package_digest,
        },
        "transport_candidate": transport_candidate,
        "structural_validation": "passed",
        "diff": result.to_dict(),
    }
    path = _review_path(node_root, candidate.package_digest)
    path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write_text(path, json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    return result, path


def preview_source_candidate_effect(
    node_root: Path,
    source_id: str,
    candidate_root: Path,
) -> ContextDiff:
    """Preview the consumer's effective compiled Context with one candidate Source pin.

    No accepted package or authored source is changed. Existing local
    Overrides/Removes and all other imported Context are applied by the normal
    compiler, so this diff describes what would actually become effective in
    the consumer if the candidate were accepted.
    """

    node_root = node_root.resolve()
    candidate_root = candidate_root.resolve()
    repo_root = find_repo_root(node_root)
    candidate = load_package(candidate_root)
    current_compiled = Compiler(repo_root).compile(node_root)
    source_index, source_ref = _source_index(current_compiled, source_id)
    current = current_compiled.source_packages[source_index]

    if candidate.metadata.id != source_ref.id:
        raise ContextCanonError(
            f"Candidate Node ID {candidate.metadata.id} does not match Source {source_ref.name} ({source_ref.id})"
        )
    _require_candidate_version_advance(current, candidate, "Source")
    _validate_candidate_composition(Compiler(repo_root), current_compiled, source_index, candidate)

    candidate_resources = {
        file.path: (candidate_root / file.path).read_bytes()
        for file in candidate.files
        if file.path.startswith("CONTEXT/references/")
    }
    preview_source = _render_source_pin_text(node_root, source_id, candidate)
    preview_compiled = Compiler(
        repo_root,
        source_overrides={node_root: preview_source},
        package_overrides={(node_root, candidate.package_digest): (candidate, candidate_resources)},
    ).compile(node_root)
    return diff_compiled(current_compiled, preview_compiled)


def accept_source_candidate(node_root: Path, source_id: str, candidate_root: Path) -> CompiledPackage:
    """Accept exactly a previously reviewed candidate package.

    Acceptance installs the immutable artifact first and then updates only the
    matching Source's visible version plus compiler-managed exact pins.
    """

    node_root = node_root.resolve()
    candidate_root = candidate_root.resolve()
    candidate = load_package(candidate_root)
    receipt_path = _review_path(node_root, candidate.package_digest)
    if not receipt_path.is_file():
        raise ContextCanonError(
            f"Source candidate {candidate.package_digest} has no review receipt; run 'contextcanon source review' first"
        )

    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContextCanonError(f"Invalid Source review receipt {receipt_path}: {exc}") from exc
    if not isinstance(receipt, dict) or receipt.get("schema") != REVIEW_SCHEMA:
        raise ContextCanonError(f"Invalid Source review receipt schema in {receipt_path}")
    if receipt.get("source_id") != source_id:
        raise ContextCanonError(f"Source review receipt {receipt_path} belongs to a different Source")

    compiler = Compiler(find_repo_root(node_root))
    compiled = compiler.compile(node_root)
    index, source_ref = _source_index(compiled, source_id)
    current = compiled.source_packages[index]

    if candidate.metadata.id != source_ref.id:
        raise ContextCanonError(
            f"Candidate Node ID {candidate.metadata.id} does not match Source {source_ref.name} ({source_ref.id})"
        )
    if receipt.get("consumer_node_id") != compiled.metadata.id:
        raise ContextCanonError(f"Source review receipt {receipt_path} belongs to a different consumer Node")
    if receipt.get("source_file_sha256") != _source_hash(node_root):
        raise ContextCanonError(
            f"CONTEXT.src.md changed after Source review; review candidate {candidate.package_digest} again"
        )

    before = receipt.get("before")
    candidate_receipt = receipt.get("candidate")
    if not isinstance(before, dict) or not isinstance(candidate_receipt, dict):
        raise ContextCanonError(f"Invalid Source review receipt state in {receipt_path}")
    if (
        before.get("version") != current.metadata.version
        or before.get("normalized_digest") != current.normalized_digest
        or before.get("package_digest") != current.package_digest
    ):
        raise ContextCanonError("Accepted Source state changed after review; review the candidate again")
    if (
        candidate_receipt.get("version") != candidate.metadata.version
        or candidate_receipt.get("normalized_digest") != candidate.normalized_digest
        or candidate_receipt.get("package_digest") != candidate.package_digest
    ):
        raise ContextCanonError("Candidate package differs from the reviewed Source candidate")
    if receipt.get("structural_validation") != "passed":
        raise ContextCanonError("Source candidate review did not pass structural validation")

    transport_candidate = _validated_candidate_provenance(node_root, source_ref, candidate)
    if receipt.get("transport_candidate") != transport_candidate:
        raise ContextCanonError("Git Source candidate provenance differs from the reviewed candidate")

    _validate_candidate_composition(compiler, compiled, index, candidate)
    _install_package(node_root, candidate_root, candidate)
    accepted_ref = None if transport_candidate is None else (transport_candidate.get("candidate_ref") or None)
    _write_source_pin(node_root, source_id, candidate, accepted_ref=accepted_ref)
    return candidate


def review_parent_candidate(node_root: Path, parent_id: str | None = None) -> tuple[ContextDiff, Path]:
    """Review one live semantic Parent as an immutable candidate."""

    node_root = node_root.resolve()
    repo_root = find_repo_root(node_root)
    compiler = Compiler(repo_root)
    compiled = compiler.compile(node_root)
    parent_index, parent_ref = _parent_index(compiled, parent_id)
    current = compiled.parent_packages[parent_index]

    parent_root = compiler._resolve_source_root(node_root, parent_ref.locator)
    ensure_node_version_advanced(parent_root, repo_root)
    live_parent = Compiler(repo_root).compile(parent_root)
    candidate = compiled_package(live_parent)
    if candidate.metadata.id != parent_ref.id:
        raise ContextCanonError(
            f"Live Parent Node ID {candidate.metadata.id} does not match accepted Parent {parent_ref.name} ({parent_ref.id})"
        )
    _require_candidate_version_advance(current, candidate, "Parent")

    _validate_parent_candidate_composition(compiler, compiled, parent_index, candidate)
    candidate_root = _store_parent_candidate(node_root, live_parent)
    result = diff_packages(current, candidate)
    receipt = {
        "schema": PARENT_REVIEW_SCHEMA,
        "parent_id": parent_ref.id,
        "consumer_node_id": compiled.metadata.id,
        "source_file_sha256": _source_hash(node_root),
        "before": {
            "version": current.metadata.version,
            "normalized_digest": current.normalized_digest,
            "package_digest": current.package_digest,
        },
        "candidate": {
            "version": candidate.metadata.version,
            "normalized_digest": candidate.normalized_digest,
            "package_digest": candidate.package_digest,
        },
        "candidate_path": candidate_root.relative_to(node_root).as_posix(),
        "structural_validation": "passed",
        "diff": result.to_dict(),
    }
    path = _parent_review_path(node_root, parent_ref.id)
    path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write_text(path, json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    return result, path


def preview_parent_candidate_effect(node_root: Path, parent_id: str | None = None) -> ContextDiff:
    """Preview the Child's effective Context with the current live Parent candidate.

    The Child's accepted Parent pin and authored source remain unchanged. Local
    Overrides/Removes, local Rules, other Parents and Sources are applied by
    the normal compiler so the returned diff describes the effective result of
    accepting this Parent update for this Child.
    """

    node_root = node_root.resolve()
    repo_root = find_repo_root(node_root)
    compiler = Compiler(repo_root)
    current_compiled = compiler.compile(node_root)
    parent_index, parent_ref = _parent_index(current_compiled, parent_id)
    current = current_compiled.parent_packages[parent_index]

    parent_root = compiler._resolve_source_root(node_root, parent_ref.locator)
    ensure_node_version_advanced(parent_root, repo_root)
    live_parent = Compiler(repo_root).compile(parent_root)
    candidate = compiled_package(live_parent)
    if candidate.metadata.id != parent_ref.id:
        raise ContextCanonError(
            f"Live Parent Node ID {candidate.metadata.id} does not match accepted Parent {parent_ref.name} ({parent_ref.id})"
        )
    _require_candidate_version_advance(current, candidate, "Parent")
    _validate_parent_candidate_composition(compiler, current_compiled, parent_index, candidate)

    candidate_root = _store_parent_candidate(node_root, live_parent)
    candidate_resources = {
        file.path: (candidate_root / file.path).read_bytes()
        for file in candidate.files
        if file.path.startswith("CONTEXT/references/")
    }
    preview_source = _render_parent_pin_text(node_root, parent_ref.id, candidate)
    preview_compiled = Compiler(
        repo_root,
        source_overrides={node_root: preview_source},
        package_overrides={(node_root, candidate.package_digest): (candidate, candidate_resources)},
    ).compile(node_root)
    return diff_compiled(current_compiled, preview_compiled)


def accept_parent_candidate(node_root: Path, parent_id: str | None = None) -> CompiledPackage:
    """Accept exactly the reviewed candidate for one semantic Parent."""

    node_root = node_root.resolve()
    compiler = Compiler(find_repo_root(node_root))
    compiled = compiler.compile(node_root)
    parent_index, parent_ref = _parent_index(compiled, parent_id)
    current = compiled.parent_packages[parent_index]
    receipt_path = _parent_review_path(node_root, parent_ref.id)
    if not receipt_path.is_file():
        raise ContextCanonError(
            f"Parent {parent_ref.id} has no review receipt; run 'contextcanon parent review {parent_ref.id}' first"
        )
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContextCanonError(f"Invalid Parent review receipt {receipt_path}: {exc}") from exc
    if not isinstance(receipt, dict) or receipt.get("schema") != PARENT_REVIEW_SCHEMA:
        raise ContextCanonError(f"Invalid Parent review receipt schema in {receipt_path}")
    if receipt.get("parent_id") != parent_ref.id:
        raise ContextCanonError("Parent review receipt belongs to a different Parent")
    if receipt.get("consumer_node_id") != compiled.metadata.id:
        raise ContextCanonError("Parent review receipt belongs to a different consumer Node")
    if receipt.get("source_file_sha256") != _source_hash(node_root):
        raise ContextCanonError("CONTEXT.src.md changed after Parent review; review the Parent candidate again")

    before = receipt.get("before")
    candidate_receipt = receipt.get("candidate")
    if not isinstance(before, dict) or not isinstance(candidate_receipt, dict):
        raise ContextCanonError(f"Invalid Parent review receipt state in {receipt_path}")
    if (
        before.get("version") != current.metadata.version
        or before.get("normalized_digest") != current.normalized_digest
        or before.get("package_digest") != current.package_digest
    ):
        raise ContextCanonError("Accepted Parent state changed after review; review the Parent candidate again")

    candidate_digest = candidate_receipt.get("package_digest")
    if not isinstance(candidate_digest, str):
        raise ContextCanonError(f"Invalid Parent candidate digest in {receipt_path}")
    candidate_root = node_root / ".context" / "parent-candidates" / candidate_digest
    candidate = load_package(candidate_root)
    if candidate.metadata.id != parent_ref.id:
        raise ContextCanonError("Reviewed Parent candidate belongs to a different Node")
    if (
        candidate_receipt.get("version") != candidate.metadata.version
        or candidate_receipt.get("normalized_digest") != candidate.normalized_digest
        or candidate_receipt.get("package_digest") != candidate.package_digest
    ):
        raise ContextCanonError("Parent candidate package differs from the reviewed candidate")
    if receipt.get("structural_validation") != "passed":
        raise ContextCanonError("Parent candidate review did not pass structural validation")

    _validate_parent_candidate_composition(compiler, compiled, parent_index, candidate)
    _install_package(node_root, candidate_root, candidate)
    _write_parent_pin(node_root, parent_ref.id, candidate)
    return candidate


def _parent_index(compiled: CompiledNode, parent_id: str | None) -> tuple[int, ParentRef]:
    if not compiled.parsed.parents:
        raise ContextCanonError(f"{compiled.metadata.name}: Node has no semantic Parent")
    if parent_id is None:
        if len(compiled.parsed.parents) != 1:
            ids = ", ".join(parent.id for parent in compiled.parsed.parents)
            raise ContextCanonError(
                f"{compiled.metadata.name}: Node has multiple semantic Parents ({ids}); specify the Parent Node ID"
            )
        return 0, compiled.parsed.parents[0]
    matches = [(index, parent) for index, parent in enumerate(compiled.parsed.parents) if parent.id == parent_id]
    if not matches:
        raise ContextCanonError(f"{compiled.metadata.name}: no semantic Parent with Node ID {parent_id}")
    return matches[0]

def _validate_parent_candidate_composition(
    compiler: Compiler,
    compiled: CompiledNode,
    parent_index: int,
    candidate: CompiledPackage,
) -> None:
    packages = [*compiled.parent_packages, *compiled.source_packages]
    packages[parent_index] = candidate
    inherited, removals = compiler._compose_inherited_rule_state(packages, compiled.metadata.name)
    inherited, removals = compiler._apply_rule_changes(
        inherited,
        removals,
        compiled.local_changes,
        compiled.metadata.id,
        compiled.metadata.name,
    )
    seen: dict[str, Rule] = {}
    for rule in (*inherited, *compiled.local_rules):
        previous = seen.get(rule.id)
        if previous is not None and previous.origin_node_id != rule.origin_node_id:
            raise ContextCanonError(
                f"Visible Rule ID collision in {compiled.metadata.name}: {rule.id} comes from multiple Nodes"
            )
        seen[rule.id] = rule
    inherited_topics = compiler._compose_inherited_topics(packages, compiled.metadata.name)
    compiler._validate_visible_topic_ids(inherited_topics, compiled.local_topics, compiled.metadata.name)

def _store_parent_candidate(node_root: Path, compiled_parent: CompiledNode) -> Path:
    package = compiled_package(compiled_parent)
    store = node_root / ".context" / "parent-candidates"
    store.mkdir(parents=True, exist_ok=True)
    destination = store / package.package_digest
    if destination.exists():
        existing = load_package(destination)
        if (
            existing.metadata.id == package.metadata.id
            and existing.normalized_digest == package.normalized_digest
            and existing.package_digest == package.package_digest
        ):
            return destination
        raise ContextCanonError(f"Parent candidate store path exists with different content: {destination}")

    temporary = Path(tempfile.mkdtemp(prefix=f".{package.package_digest[:12]}-", dir=store))
    try:
        for rel, content in artifact_files(compiled_parent).items():
            target = temporary / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        staged = load_package(temporary)
        if staged.normalized_digest != package.normalized_digest or staged.package_digest != package.package_digest:
            raise ContextCanonError("Staged Parent candidate identity changed during review")
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    return destination


def _parent_review_path(node_root: Path, parent_id: str) -> Path:
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", parent_id):
        token = parent_id
    else:
        token = "sha256-" + hashlib.sha256(parent_id.encode("utf-8")).hexdigest()
    return node_root / ".context" / "parent-reviews" / f"{token}.json"

def _render_parent_pin_text(node_root: Path, parent_id: str, candidate: CompiledPackage) -> str:
    path = node_root / "CONTEXT.src.md"
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    found = 0
    for index, line in enumerate(lines):
        visible = _SOURCE_LINE_RE.match(line)
        if not visible:
            continue
        search_end = min(index + 5, len(lines))
        for comment_index in range(index + 1, search_end):
            comment = _PARENT_COMMENT_RE.match(lines[comment_index])
            if not comment:
                continue
            attrs = _ATTR_RE.findall(comment.group("attrs"))
            if not attrs or dict(attrs).get("id") != parent_id:
                continue
            found += 1
            lines[index] = visible.group("prefix") + f"`{candidate.metadata.version}`" + visible.group("ending")
            updated: list[tuple[str, str]] = []
            seen_version = False
            for key, value in attrs:
                if key == "version":
                    updated.append((key, candidate.metadata.version))
                    seen_version = True
                elif key not in {"normalized-digest", "package-digest"}:
                    updated.append((key, value))
            if not seen_version:
                updated.append(("version", candidate.metadata.version))
            updated.extend([
                ("normalized-digest", candidate.normalized_digest),
                ("package-digest", candidate.package_digest),
            ])
            attrs_text = " ".join(f'{key}="{value}"' for key, value in updated)
            lines[comment_index] = f"{comment.group('indent')}<!-- ctx:parent {attrs_text} -->{comment.group('ending')}"
            break
    if found != 1:
        raise ContextCanonError(f"Could not find exactly one semantic Parent Node ID {parent_id} in {path}")
    return "".join(lines)


def _write_parent_pin(node_root: Path, parent_id: str, candidate: CompiledPackage) -> None:
    path = node_root / "CONTEXT.src.md"
    _atomic_write_text(path, _render_parent_pin_text(node_root, parent_id, candidate))


def install_source_package(node_root: Path, package_root: Path) -> CompiledPackage:
    """Verify and install one immutable Source package without changing pins.

    This is shared by onboarding acceptance, where the canonical Source entry
    does not exist until the reviewed onboarding source is published.
    """

    node_root = node_root.resolve()
    package_root = package_root.resolve()
    package = load_package(package_root)
    _install_package(node_root, package_root, package)
    return package


def _source_index(compiled: CompiledNode, source_id: str) -> tuple[int, SourceRef]:
    matches = [(index, source) for index, source in enumerate(compiled.parsed.sources) if source.id == source_id]
    if not matches:
        raise ContextCanonError(f"{compiled.metadata.name}: no Source with Node ID {source_id}")
    if len(matches) != 1:
        raise ContextCanonError(f"{compiled.metadata.name}: Source Node ID {source_id} is not unique")
    return matches[0]


def _validate_candidate_composition(
    compiler: Compiler,
    compiled: CompiledNode,
    source_index: int,
    candidate: CompiledPackage,
) -> None:
    packages = [*compiled.parent_packages, *compiled.source_packages]
    candidate_index = source_index + len(compiled.parent_packages)
    packages[candidate_index] = candidate
    inherited, removals = compiler._compose_inherited_rule_state(packages, compiled.metadata.name)
    inherited, removals = compiler._apply_rule_changes(
        inherited,
        removals,
        compiled.local_changes,
        compiled.metadata.id,
        compiled.metadata.name,
    )

    seen: dict[str, Rule] = {}
    for rule in (*inherited, *compiled.local_rules):
        previous = seen.get(rule.id)
        if previous is not None and previous.origin_node_id != rule.origin_node_id:
            raise ContextCanonError(
                f"Visible Rule ID collision in {compiled.metadata.name}: {rule.id} comes from multiple Nodes"
            )
        seen[rule.id] = rule

    inherited_topics = compiler._compose_inherited_topics(packages, compiled.metadata.name)
    compiler._validate_visible_topic_ids(inherited_topics, compiled.local_topics, compiled.metadata.name)


def _validated_candidate_provenance(
    node_root: Path,
    source_ref: SourceRef,
    candidate: CompiledPackage,
) -> dict[str, str] | None:
    provenance = load_candidate_provenance(node_root, candidate.package_digest)
    if provenance is None:
        return None
    if provenance["source_id"] != source_ref.id:
        raise ContextCanonError("Source candidate provenance belongs to a different Source")
    if provenance["package_digest"] != candidate.package_digest:
        raise ContextCanonError("Source candidate provenance package digest mismatch")
    if provenance.get("schema") == "contextcanon/source-candidate-provenance/v1":
        return provenance
    if provenance["locator"] != source_ref.locator:
        raise ContextCanonError("Git Source candidate provenance locator differs from the accepted Source")
    if provenance["node_path"] != (source_ref.node_path or "."):
        raise ContextCanonError("Git Source candidate provenance node-path differs from the accepted Source")
    if provenance["accepted_ref"] != (source_ref.transport_ref or ""):
        raise ContextCanonError(
            "Accepted Git Source ref changed after candidate discovery; fetch the candidate again before review"
        )
    return provenance

def _review_path(node_root: Path, candidate_package_digest: str) -> Path:
    return node_root / ".context" / "source-reviews" / f"{candidate_package_digest}.json"


def _source_hash(node_root: Path) -> str:
    path = node_root / "CONTEXT.src.md"
    if not path.is_file():
        raise ContextCanonError(f"Not a Context Node root: {node_root} (missing CONTEXT.src.md)")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _install_package(node_root: Path, candidate_root: Path, candidate: CompiledPackage) -> None:
    store = node_root / ".context" / "sources"
    store.mkdir(parents=True, exist_ok=True)
    destination = store / candidate.package_digest

    if destination.exists():
        existing = load_package(destination)
        if (
            existing.metadata.id == candidate.metadata.id
            and existing.normalized_digest == candidate.normalized_digest
            and existing.package_digest == candidate.package_digest
        ):
            return
        raise ContextCanonError(f"Accepted Source store path exists with different content: {destination}")

    temporary = Path(tempfile.mkdtemp(prefix=f".{candidate.package_digest[:12]}-", dir=store))
    try:
        manifest_source = candidate_root / PACKAGE_MANIFEST_PATH
        manifest_destination = temporary / PACKAGE_MANIFEST_PATH
        manifest_destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(manifest_source, manifest_destination)
        for file in candidate.files:
            source = candidate_root / file.path
            target = temporary / file.path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)

        staged = load_package(temporary)
        if staged.normalized_digest != candidate.normalized_digest or staged.package_digest != candidate.package_digest:
            raise ContextCanonError("Staged Source package identity changed during acceptance")
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)


def _render_source_pin_text(
    node_root: Path,
    source_id: str,
    candidate: CompiledPackage,
    *,
    accepted_ref: str | None = None,
) -> str:
    path = node_root / "CONTEXT.src.md"
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    found = 0

    for index, line in enumerate(lines):
        visible = _SOURCE_LINE_RE.match(line)
        if not visible:
            continue
        search_end = min(index + 5, len(lines))
        for comment_index in range(index + 1, search_end):
            comment = _SOURCE_COMMENT_RE.match(lines[comment_index])
            if not comment:
                continue
            attrs = _ATTR_RE.findall(comment.group("attrs"))
            if not attrs or dict(attrs).get("id") != source_id:
                continue

            found += 1
            if found > 1:
                raise ContextCanonError(f"Source Node ID {source_id} appears more than once in {path}")

            if any(char in candidate.metadata.name for char in "]\n\r"):
                raise ContextCanonError(f"Source name cannot be represented safely: {candidate.metadata.name!r}")
            lines[index] = (
                visible.group("bullet")
                + f"[{candidate.metadata.name}]({visible.group('path')})"
                + visible.group("separator")
                + f"`{candidate.metadata.version}`"
                + visible.group("ending")
            )

            updated: list[tuple[str, str]] = []
            seen_version = False
            for key, value in attrs:
                if key == "version":
                    updated.append((key, candidate.metadata.version))
                    seen_version = True
                elif key == "ref" and accepted_ref is not None and re.fullmatch(r"[0-9a-f]{40}", value):
                    updated.append((key, accepted_ref))
                elif key not in {"normalized-digest", "package-digest"}:
                    updated.append((key, value))
            if not seen_version:
                updated.append(("version", candidate.metadata.version))
            updated.extend([
                ("normalized-digest", candidate.normalized_digest),
                ("package-digest", candidate.package_digest),
            ])
            attrs_text = " ".join(f'{key}="{value}"' for key, value in updated)
            lines[comment_index] = (
                f"{comment.group('indent')}<!-- ctx:source {attrs_text} -->{comment.group('ending')}"
            )
            break

    if found != 1:
        raise ContextCanonError(f"Could not find exactly one Source Node ID {source_id} in {path}")
    return "".join(lines)


def _write_source_pin(node_root: Path, source_id: str, candidate: CompiledPackage, *, accepted_ref: str | None = None) -> None:
    path = node_root / "CONTEXT.src.md"
    _atomic_write_text(
        path,
        _render_source_pin_text(node_root, source_id, candidate, accepted_ref=accepted_ref),
    )


def _atomic_write_text(path: Path, content: str) -> None:
    """Replace one text file atomically from a sibling temporary file.

    A failed final replace leaves the previous canonical file intact. The
    temporary file is flushed and fsynced before publication and removed on
    every failed path.
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except OSError as exc:
        raise ContextCanonError(f"Could not atomically write {path}: {exc}") from exc
    finally:
        if temporary.exists():
            temporary.unlink()
