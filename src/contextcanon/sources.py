from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
from pathlib import Path

from .compiler import Compiler
from .diff import ContextDiff
from .model import CompiledNode, CompiledPackage, ParentRef, Rule, SourceRef
from .package import PACKAGE_MANIFEST_PATH, artifact_files, compiled_package, load_package
from .package_diff import diff_packages
from .parser import ContextCanonError, find_repo_root, parse_node

REVIEW_SCHEMA = "contextcanon/source-review/v0"
PARENT_REVIEW_SCHEMA = "contextcanon/parent-review/v0"
_ATTR_RE = re.compile(r'([A-Za-z_][A-Za-z0-9_-]*)="([^"]*)"')
_SOURCE_COMMENT_RE = re.compile(r'^(?P<indent>\s*)<!--\s*ctx:source\s+(?P<attrs>.*?)\s*-->(?P<ending>\r?\n?)$')
_PARENT_COMMENT_RE = re.compile(r'^(?P<indent>\s*)<!--\s*ctx:parent\s+(?P<attrs>.*?)\s*-->(?P<ending>\r?\n?)$')
_SOURCE_LINE_RE = re.compile(
    r'^(?P<prefix>- \[[^]]+\]\([^)]+\)\s+—\s+)`[^`]+`(?P<ending>\s*(?:\r?\n)?)$'
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
        "structural_validation": "passed",
        "diff": result.to_dict(),
    }
    path = _review_path(node_root, candidate.package_digest)
    path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write_text(path, json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    return result, path


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

    _validate_candidate_composition(compiler, compiled, index, candidate)
    _install_package(node_root, candidate_root, candidate)
    _write_source_pin(node_root, source_id, candidate)
    return candidate


def review_parent_candidate(node_root: Path) -> tuple[ContextDiff, Path]:
    """Compile the live semantic Parent explicitly and review it as an immutable candidate.

    Ordinary child builds never call this function and therefore remain bound
    to the accepted Parent package pin. Review snapshots the live Parent into a
    content-addressed candidate store without changing the accepted Child.
    """

    node_root = node_root.resolve()
    repo_root = find_repo_root(node_root)
    compiler = Compiler(repo_root)
    compiled = compiler.compile(node_root)
    parent_ref = _parent_ref(compiled)
    current = compiled.parent_package
    assert current is not None

    parent_root = compiler._resolve_source_root(node_root, parent_ref.locator)
    live_parent = Compiler(repo_root).compile(parent_root)
    candidate = compiled_package(live_parent)
    if candidate.metadata.id != parent_ref.id:
        raise ContextCanonError(
            f"Live Parent Node ID {candidate.metadata.id} does not match accepted Parent {parent_ref.name} ({parent_ref.id})"
        )

    _validate_parent_candidate_composition(compiler, compiled, candidate)
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
    path = _parent_review_path(node_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write_text(path, json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    return result, path


def accept_parent_candidate(node_root: Path) -> CompiledPackage:
    """Accept exactly the most recently reviewed semantic Parent snapshot."""

    node_root = node_root.resolve()
    receipt_path = _parent_review_path(node_root)
    if not receipt_path.is_file():
        raise ContextCanonError("Parent has no review receipt; run 'contextcanon parent review' first")
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContextCanonError(f"Invalid Parent review receipt {receipt_path}: {exc}") from exc
    if not isinstance(receipt, dict) or receipt.get("schema") != PARENT_REVIEW_SCHEMA:
        raise ContextCanonError(f"Invalid Parent review receipt schema in {receipt_path}")

    compiler = Compiler(find_repo_root(node_root))
    compiled = compiler.compile(node_root)
    parent_ref = _parent_ref(compiled)
    current = compiled.parent_package
    assert current is not None
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

    _validate_parent_candidate_composition(compiler, compiled, candidate)
    _install_package(node_root, candidate_root, candidate)
    _write_parent_pin(node_root, candidate)
    return candidate


def _parent_ref(compiled: CompiledNode) -> ParentRef:
    parent = compiled.parsed.parent
    if parent is None or compiled.parent_package is None:
        raise ContextCanonError(f"{compiled.metadata.name}: Node has no semantic Parent")
    return parent


def _validate_parent_candidate_composition(
    compiler: Compiler,
    compiled: CompiledNode,
    candidate: CompiledPackage,
) -> None:
    packages = [candidate, *compiled.source_packages]
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


def _parent_review_path(node_root: Path) -> Path:
    return node_root / ".context" / "parent-review.json"


def _write_parent_pin(node_root: Path, candidate: CompiledPackage) -> None:
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
            if not attrs:
                continue
            found += 1
            if found > 1:
                raise ContextCanonError(f"More than one semantic Parent appears in {path}")
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
        raise ContextCanonError(f"Could not find exactly one semantic Parent in {path}")
    _atomic_write_text(path, "".join(lines))


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
    packages = ([compiled.parent_package] if compiled.parent_package is not None else []) + list(compiled.source_packages)
    candidate_index = source_index + (1 if compiled.parent_package is not None else 0)
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


def _write_source_pin(node_root: Path, source_id: str, candidate: CompiledPackage) -> None:
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

            lines[index] = (
                visible.group("prefix")
                + f"`{candidate.metadata.version}`"
                + visible.group("ending")
            )

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
            lines[comment_index] = (
                f"{comment.group('indent')}<!-- ctx:source {attrs_text} -->{comment.group('ending')}"
            )
            break

    if found != 1:
        raise ContextCanonError(f"Could not find exactly one Source Node ID {source_id} in {path}")
    _atomic_write_text(path, "".join(lines))


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
