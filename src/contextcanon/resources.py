from __future__ import annotations

import hashlib
import json
import os
import posixpath
import re
import subprocess
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Callable, Iterable

from .compiler import discover_nodes
from .links import local_markdown_targets
from .model import CompiledPackage
from .package import load_package
from .parser import ContextCanonError, find_repo_root, parse_node


RESOURCE_LINE_RE = re.compile(r'^(?P<indent>\s*)- Resource:\s+`(?P<locator>[^`]+)`\s*$')
RESOURCE_COMMENT_RE = re.compile(r'<!--\s*ctx:resource\s+(?P<attrs>.*?)\s*-->')
RESOURCE_ID_RE = re.compile(r'\bid="(?P<id>[^"]+)"')


@dataclass(frozen=True)
class ResourceUse:
    node_root: Path
    node_id: str
    node_name: str
    topic_id: str
    topic_title: str
    intent: str
    resource_id: str | None
    locator: str

    @property
    def path(self) -> Path:
        return (self.node_root / self.locator).resolve()


@dataclass(frozen=True)
class ResourceRecord:
    node_root: Path
    node_id: str
    node_name: str
    resource_id: str | None
    locator: str
    uses: tuple[ResourceUse, ...]

    @property
    def path(self) -> Path:
        return (self.node_root / self.locator).resolve()


@dataclass(frozen=True)
class ResourceCandidate:
    path: Path
    repo_path: str
    sha256: str
    size: int
    lines: int | None


@dataclass(frozen=True)
class ResourceStatus:
    record: ResourceRecord
    state: str
    repo_path: str
    sha256: str | None
    size: int | None
    lines: int | None
    baseline_repo_path: str | None
    baseline_sha256: str | None
    baseline_size: int | None
    candidates: tuple[ResourceCandidate, ...] = ()
    closure_changed: bool = False
    closure_before: tuple[str, ...] = ()
    closure_after: tuple[str, ...] = ()


@dataclass(frozen=True)
class RegisterResult:
    node_root: Path
    added: int
    resource_ids: tuple[str, ...]


@dataclass(frozen=True)
class MoveResult:
    old_path: Path
    new_path: Path
    updated_nodes: tuple[Path, ...]
    resource_ids: tuple[str, ...]
    inbound_markdown_links: tuple[str, ...] = ()


@dataclass(frozen=True)
class _Baseline:
    package: CompiledPackage
    package_path: str
    repo_path: str
    sha256: str
    size: int
    lines: int | None
    dependencies: tuple[str, ...]


def _new_resource_id(existing: set[str]) -> str:
    for _ in range(100):
        candidate = f"RESOURCE-{uuid.uuid4().hex[:12].upper()}"
        if candidate not in existing:
            return candidate
    raise ContextCanonError("Could not allocate a fresh Resource identity")


def collect_resource_uses(repo_root: Path, node_roots: Iterable[Path]) -> tuple[ResourceUse, ...]:
    repo_root = repo_root.resolve()
    uses: list[ResourceUse] = []
    for node_root in node_roots:
        parsed = parse_node(node_root, repo_root)
        for topic in parsed.topics:
            for target in topic.targets:
                if target.kind != "resource":
                    continue
                uses.append(
                    ResourceUse(
                        node_root=parsed.root,
                        node_id=parsed.metadata.id,
                        node_name=parsed.metadata.name,
                        topic_id=topic.id,
                        topic_title=topic.title,
                        intent=target.intent,
                        resource_id=target.resource_id,
                        locator=target.locator,
                    )
                )
    return tuple(
        sorted(
            uses,
            key=lambda use: (
                use.node_root.as_posix(),
                use.resource_id or "",
                use.locator,
                use.topic_id,
                use.intent,
            ),
        )
    )


def collect_resource_records(repo_root: Path, node_roots: Iterable[Path]) -> tuple[ResourceRecord, ...]:
    grouped: dict[tuple[str, str], list[ResourceUse]] = {}
    for use in collect_resource_uses(repo_root, node_roots):
        identity = use.resource_id or f"path:{use.locator}"
        grouped.setdefault((use.node_id, identity), []).append(use)

    records: list[ResourceRecord] = []
    for _, uses in sorted(grouped.items()):
        first = uses[0]
        locators = {use.locator for use in uses}
        if len(locators) != 1:
            raise ContextCanonError(
                f"Resource identity {first.resource_id} in {first.node_name} has multiple locators: "
                + ", ".join(sorted(locators))
            )
        records.append(
            ResourceRecord(
                node_root=first.node_root,
                node_id=first.node_id,
                node_name=first.node_name,
                resource_id=first.resource_id,
                locator=first.locator,
                uses=tuple(uses),
            )
        )
    return tuple(records)


def _atomic_write(path: Path, text: str) -> None:
    path = path.resolve()
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def register_resources(node_root: Path) -> RegisterResult:
    node_root = node_root.resolve()
    parsed = parse_node(node_root)
    source_path = node_root / "CONTEXT.src.md"
    original = source_path.read_text(encoding="utf-8")
    lines = original.splitlines()

    existing_by_locator: dict[str, str] = {}
    existing_ids: set[str] = set()
    for topic in parsed.topics:
        for target in topic.targets:
            if target.kind == "resource" and target.resource_id is not None:
                existing_by_locator[target.locator] = target.resource_id
                existing_ids.add(target.resource_id)

    allocated = dict(existing_by_locator)
    added_ids: list[str] = []
    output: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        match = RESOURCE_LINE_RE.match(line)
        output.append(line)
        if not match:
            index += 1
            continue

        locator = match.group("locator")
        look = index + 1
        while look < len(lines) and not lines[look].strip():
            look += 1
        has_metadata = False
        if look < len(lines):
            comment = RESOURCE_COMMENT_RE.search(lines[look])
            if comment is not None:
                id_match = RESOURCE_ID_RE.search(comment.group("attrs"))
                if id_match is None:
                    raise ContextCanonError(
                        f"{source_path}:{look + 1}: ctx:resource needs a stable id"
                    )
                has_metadata = True
                resource_id = id_match.group("id")
                previous = allocated.get(locator)
                if previous is not None and previous != resource_id:
                    raise ContextCanonError(
                        f"{source_path}: Resource {locator!r} has conflicting stable IDs"
                    )
                allocated[locator] = resource_id
                existing_ids.add(resource_id)

        if not has_metadata:
            resource_id = allocated.get(locator)
            if resource_id is None:
                resource_id = _new_resource_id(existing_ids)
                existing_ids.add(resource_id)
                allocated[locator] = resource_id
                added_ids.append(resource_id)
            output.append(f'  <!-- ctx:resource id="{resource_id}" -->')
        index += 1

    if not added_ids:
        return RegisterResult(node_root, 0, ())

    updated = "\n".join(output).rstrip() + "\n"
    parse_node(node_root, find_repo_root(node_root), source_text=updated)
    _atomic_write(source_path, updated)
    return RegisterResult(node_root, len(added_ids), tuple(added_ids))


def _namespace(node_id: str) -> str:
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", node_id):
        return node_id
    return "sha256-" + hashlib.sha256(node_id.encode("utf-8")).hexdigest()


def _published_path(repo_root: Path, record: ResourceRecord) -> str:
    source = record.path
    try:
        repo_rel = source.relative_to(repo_root).as_posix()
    except ValueError as exc:
        raise ContextCanonError(f"Resource escapes repository: {record.locator}") from exc
    return f"CONTEXT/references/{_namespace(record.node_id)}/{repo_rel}"


def _decode_lines(content: bytes) -> int | None:
    try:
        return len(content.decode("utf-8").splitlines())
    except UnicodeDecodeError:
        return None


def _strip_namespace(package_path: str) -> str | None:
    parts = PurePosixPath(package_path).parts
    if len(parts) < 4 or parts[0:2] != ("CONTEXT", "references"):
        return None
    return PurePosixPath(*parts[3:]).as_posix()


def _package_dependencies(
    package_root: Path,
    package: CompiledPackage,
    root_package_path: str,
) -> tuple[str, ...]:
    files = {file.path for file in package.files}
    if PurePosixPath(root_package_path).suffix.lower() != ".md":
        return ()
    queue = [root_package_path]
    seen: set[str] = set()
    dependencies: set[str] = set()
    while queue:
        current = queue.pop(0)
        if current in seen or current not in files:
            continue
        seen.add(current)
        path = package_root / current
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if PurePosixPath(current).suffix.lower() != ".md":
            continue
        for locator in local_markdown_targets(text):
            target = posixpath.normpath(posixpath.join(posixpath.dirname(current), locator))
            if target not in files:
                continue
            if target != root_package_path:
                repo_path = _strip_namespace(target)
                if repo_path is not None:
                    dependencies.add(repo_path)
            if target not in seen and PurePosixPath(target).suffix.lower() == ".md":
                queue.append(target)
    return tuple(sorted(dependencies))


def _baseline_for_record(repo_root: Path, record: ResourceRecord) -> _Baseline | None:
    manifest = record.node_root / ".context" / "package.json"
    if not manifest.is_file():
        return None
    try:
        package = load_package(record.node_root)
    except ContextCanonError:
        return None

    package_path: str | None = None
    if record.resource_id is not None:
        for topic in package.topics:
            if topic.origin_node_id != record.node_id:
                continue
            for target in topic.targets:
                if target.kind == "resource" and target.resource_id == record.resource_id:
                    package_path = target.locator
                    break
            if package_path is not None:
                break

    if package_path is None:
        candidate = _published_path(repo_root, record)
        if any(file.path == candidate for file in package.files):
            package_path = candidate

    if package_path is None:
        return None

    file = next((item for item in package.files if item.path == package_path), None)
    if file is None:
        return None
    content_path = record.node_root / package_path
    if not content_path.is_file():
        return None
    content = content_path.read_bytes()
    repo_path = _strip_namespace(package_path)
    if repo_path is None:
        return None
    return _Baseline(
        package=package,
        package_path=package_path,
        repo_path=repo_path,
        sha256=file.sha256,
        size=file.size,
        lines=_decode_lines(content),
        dependencies=_package_dependencies(record.node_root, package, package_path),
    )


def _git_repository_paths(repo_root: Path) -> tuple[str, ...]:
    try:
        completed = subprocess.run(
            ["git", "-C", str(repo_root), "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ContextCanonError(f"Could not list repository files with Git: {exc}") from exc
    return tuple(
        item.decode("utf-8")
        for item in completed.stdout.split(b"\0")
        if item
    )


def _compiler_owned_paths(repo_root: Path) -> tuple[Path, ...]:
    owned: list[Path] = []
    for node_root in discover_nodes(repo_root):
        owned.extend(
            [
                (node_root / "CONTEXT").resolve(),
                (node_root / ".context").resolve(),
                (node_root / "CONTEXT.md").resolve(),
                (node_root / "AGENTS.md").resolve(),
                (node_root / ".goosehints").resolve(),
            ]
        )
    return tuple(owned)


def _is_compiler_owned(path: Path, owned: tuple[Path, ...]) -> bool:
    resolved = path.resolve()
    for candidate in owned:
        if resolved == candidate:
            return True
        if candidate.is_dir():
            try:
                resolved.relative_to(candidate)
                return True
            except ValueError:
                pass
    return False


def _exact_candidates(
    repo_root: Path,
    baseline: _Baseline,
    *,
    exclude: set[Path] | None = None,
) -> tuple[ResourceCandidate, ...]:
    exclude = {path.resolve() for path in (exclude or set())}
    owned = _compiler_owned_paths(repo_root)
    result: list[ResourceCandidate] = []
    for rel in _git_repository_paths(repo_root):
        path = (repo_root / rel).resolve()
        if path in exclude or not path.is_file() or path.is_symlink():
            continue
        if _is_compiler_owned(path, owned):
            continue
        try:
            if path.stat().st_size != baseline.size:
                continue
            content = path.read_bytes()
        except OSError:
            continue
        digest = hashlib.sha256(content).hexdigest()
        if digest != baseline.sha256:
            continue
        result.append(
            ResourceCandidate(
                path=path,
                repo_path=path.relative_to(repo_root).as_posix(),
                sha256=digest,
                size=len(content),
                lines=_decode_lines(content),
            )
        )
    return tuple(sorted(result, key=lambda item: item.repo_path))


def _live_dependencies(
    repo_root: Path,
    root: Path,
    *,
    root_content: bytes | None = None,
) -> tuple[str, ...]:
    root = root.resolve()
    content_override = {root: root_content} if root_content is not None else {}
    if root.suffix.lower() != ".md":
        return ()
    queue = [root]
    seen: set[Path] = set()
    dependencies: set[str] = set()
    while queue:
        current = queue.pop(0).resolve()
        if current in seen:
            continue
        seen.add(current)
        if current == root and root_content is not None:
            content = root_content
        else:
            if not current.is_file():
                raise ContextCanonError(
                    f"Resource Markdown closure would contain missing file: {current}"
                )
            content = current.read_bytes()
        if current.suffix.lower() != ".md":
            continue
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ContextCanonError(f"Markdown Resource is not valid UTF-8: {current}") from exc
        for locator in local_markdown_targets(text):
            linked = (current.parent / locator).resolve()
            try:
                repo_rel = linked.relative_to(repo_root).as_posix()
            except ValueError as exc:
                raise ContextCanonError(
                    f"Resource Markdown closure escapes repository from {current}: {locator}"
                ) from exc
            if linked != root:
                dependencies.add(repo_rel)
            if linked.is_dir():
                continue
            if linked not in seen and linked.suffix.lower() == ".md":
                queue.append(linked)
            elif not linked.exists():
                raise ContextCanonError(
                    f"Resource Markdown closure would contain missing file: {repo_rel}"
                )
    return tuple(sorted(dependencies))


def status_resources(repo_root: Path, node_roots: Iterable[Path]) -> tuple[ResourceStatus, ...]:
    repo_root = repo_root.resolve()
    result: list[ResourceStatus] = []
    for record in collect_resource_records(repo_root, node_roots):
        repo_path = record.path.relative_to(repo_root).as_posix()
        if record.resource_id is None:
            result.append(
                ResourceStatus(
                    record=record,
                    state="unregistered",
                    repo_path=repo_path,
                    sha256=None,
                    size=None,
                    lines=None,
                    baseline_repo_path=None,
                    baseline_sha256=None,
                    baseline_size=None,
                )
            )
            continue

        baseline = _baseline_for_record(repo_root, record)
        if record.path.is_file():
            content = record.path.read_bytes()
            digest = hashlib.sha256(content).hexdigest()
            size = len(content)
            lines = _decode_lines(content)
            if baseline is None:
                state = "unbuilt"
            elif baseline.repo_path != repo_path:
                state = "moved" if digest == baseline.sha256 else "moved-modified"
            elif digest != baseline.sha256:
                state = "modified"
            else:
                state = "clean"
            result.append(
                ResourceStatus(
                    record=record,
                    state=state,
                    repo_path=repo_path,
                    sha256=digest,
                    size=size,
                    lines=lines,
                    baseline_repo_path=baseline.repo_path if baseline else None,
                    baseline_sha256=baseline.sha256 if baseline else None,
                    baseline_size=baseline.size if baseline else None,
                )
            )
            continue

        if baseline is None:
            result.append(
                ResourceStatus(
                    record=record,
                    state="missing-unbuilt",
                    repo_path=repo_path,
                    sha256=None,
                    size=None,
                    lines=None,
                    baseline_repo_path=None,
                    baseline_sha256=None,
                    baseline_size=None,
                )
            )
            continue

        candidates = _exact_candidates(repo_root, baseline, exclude={record.path})
        state = "missing"
        closure_changed = False
        closure_before = baseline.dependencies
        closure_after: tuple[str, ...] = ()
        if len(candidates) == 1:
            state = "candidate"
            try:
                closure_after = _live_dependencies(repo_root, candidates[0].path)
                closure_changed = closure_before != closure_after
            except ContextCanonError:
                closure_changed = True
            if closure_changed:
                state = "candidate-closure-changed"
        elif len(candidates) > 1:
            state = "ambiguous"

        result.append(
            ResourceStatus(
                record=record,
                state=state,
                repo_path=repo_path,
                sha256=None,
                size=None,
                lines=None,
                baseline_repo_path=baseline.repo_path,
                baseline_sha256=baseline.sha256,
                baseline_size=baseline.size,
                candidates=candidates,
                closure_changed=closure_changed,
                closure_before=closure_before,
                closure_after=closure_after,
            )
        )
    return tuple(result)


def _inbound_markdown_links(repo_root: Path, target_path: Path) -> tuple[str, ...]:
    """Return project-authored Markdown files whose local links resolve to target_path.

    These links are reported, never rewritten. Generated ContextCanon Markdown
    is excluded because build owns that surface.
    """

    target = target_path.resolve()
    owned = _compiler_owned_paths(repo_root)
    hits: list[str] = []
    for rel in _git_repository_paths(repo_root):
        if not rel.lower().endswith(".md"):
            continue
        path = (repo_root / rel).resolve()
        if not path.is_file() or path.is_symlink() or _is_compiler_owned(path, owned):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for locator in local_markdown_targets(text):
            linked = (path.parent / locator).resolve()
            if linked == target:
                hits.append(f"{rel} -> {locator}")
    return tuple(sorted(set(hits)))


def _containing_node(repo_root: Path, path: Path) -> Path | None:
    resolved = path.resolve()
    candidates: list[Path] = []
    for node_root in discover_nodes(repo_root):
        try:
            resolved.relative_to(node_root.resolve())
        except ValueError:
            continue
        candidates.append(node_root.resolve())
    if not candidates:
        return None
    return max(candidates, key=lambda item: len(item.parts))


def _all_uses_for_path(repo_root: Path, path: Path) -> tuple[ResourceUse, ...]:
    target = path.resolve()
    return tuple(
        use
        for use in collect_resource_uses(repo_root, discover_nodes(repo_root))
        if use.path == target
    )


def _rewrite_node_source(
    repo_root: Path,
    node_root: Path,
    old_path: Path,
    new_path: Path,
) -> tuple[str, str] | None:
    source_path = node_root / "CONTEXT.src.md"
    original = source_path.read_text(encoding="utf-8")
    lines = original.splitlines()
    changed = False
    output: list[str] = []
    for line in lines:
        match = RESOURCE_LINE_RE.match(line)
        if match is None:
            output.append(line)
            continue
        locator = match.group("locator")
        current = (node_root / locator).resolve()
        if current != old_path.resolve():
            output.append(line)
            continue
        replacement = os.path.relpath(new_path.resolve(), start=node_root.resolve()).replace("\\", "/")
        output.append(f"{match.group('indent')}- Resource: `{replacement}`")
        changed = True
    if not changed:
        return None
    updated = "\n".join(output).rstrip() + "\n"
    parse_node(node_root, repo_root, source_text=updated)
    return original, updated


def _apply_locator_rewrite(
    repo_root: Path,
    old_path: Path,
    new_path: Path,
    uses: tuple[ResourceUse, ...],
) -> tuple[Path, ...]:
    node_roots = tuple(sorted({use.node_root.resolve() for use in uses}, key=lambda item: item.as_posix()))
    staged: dict[Path, tuple[str, str]] = {}
    for node_root in node_roots:
        rewrite = _rewrite_node_source(repo_root, node_root, old_path, new_path)
        if rewrite is None:
            raise ContextCanonError(
                f"Could not find Resource locator for {old_path} in {node_root / 'CONTEXT.src.md'}"
            )
        staged[node_root] = rewrite

    written: list[Path] = []
    try:
        for node_root in node_roots:
            original, updated = staged[node_root]
            _atomic_write(node_root / "CONTEXT.src.md", updated)
            written.append(node_root)
    except BaseException:
        for node_root in reversed(written):
            original, _ = staged[node_root]
            _atomic_write(node_root / "CONTEXT.src.md", original)
        raise
    return node_roots


def _validate_same_physical_node(repo_root: Path, old_path: Path, new_path: Path) -> None:
    old_owner = _containing_node(repo_root, old_path)
    new_owner = _containing_node(repo_root, new_path)
    if old_owner != new_owner:
        old_label = old_owner.relative_to(repo_root).as_posix() if old_owner else "<none>"
        new_label = new_owner.relative_to(repo_root).as_posix() if new_owner else "<none>"
        raise ContextCanonError(
            "Resource move crosses Context Node physical boundaries "
            f"({old_label or '.'} -> {new_label or '.'}); explicit Resource rehome is not supported yet"
        )


def move_resource(repo_root: Path, old_path: Path, new_path: Path) -> MoveResult:
    repo_root = repo_root.resolve()
    old_path = old_path.resolve()
    new_path = new_path.resolve()
    if not old_path.is_file():
        raise ContextCanonError(f"Resource move source does not exist: {old_path}")
    if new_path.exists():
        raise ContextCanonError(f"Resource move destination already exists: {new_path}")
    try:
        old_path.relative_to(repo_root)
        new_path.relative_to(repo_root)
    except ValueError as exc:
        raise ContextCanonError("Resource move must stay inside the Git repository") from exc
    if not new_path.parent.is_dir():
        raise ContextCanonError(f"Resource move destination directory does not exist: {new_path.parent}")

    uses = _all_uses_for_path(repo_root, old_path)
    if not uses:
        raise ContextCanonError(f"No Topic Resource references {old_path.relative_to(repo_root).as_posix()}")
    unregistered = [use for use in uses if use.resource_id is None]
    if unregistered:
        raise ContextCanonError(
            "Resource move requires stable IDs for every affected ContextCanon reference; "
            "run 'contextcanon resource register --all .' first"
        )
    _validate_same_physical_node(repo_root, old_path, new_path)

    content = old_path.read_bytes()
    before = _live_dependencies(repo_root, old_path)
    after = _live_dependencies(repo_root, new_path, root_content=content)
    if before != after:
        raise ContextCanonError(
            "Resource move would change relative Markdown closure; adjust the Resource/links first or treat this as a semantic change. "
            f"Before: {list(before)}; after: {list(after)}"
        )

    inbound_links = _inbound_markdown_links(repo_root, old_path)
    staged_nodes = tuple(sorted({use.node_root.resolve() for use in uses}, key=lambda item: item.as_posix()))
    staged_sources: dict[Path, tuple[str, str]] = {}
    for node_root in staged_nodes:
        rewrite = _rewrite_node_source(repo_root, node_root, old_path, new_path)
        if rewrite is None:
            raise ContextCanonError(f"Could not stage Resource locator update for {node_root}")
        staged_sources[node_root] = rewrite

    old_path.rename(new_path)
    written: list[Path] = []
    try:
        for node_root in staged_nodes:
            _, updated = staged_sources[node_root]
            _atomic_write(node_root / "CONTEXT.src.md", updated)
            written.append(node_root)
    except BaseException:
        for node_root in reversed(written):
            original, _ = staged_sources[node_root]
            _atomic_write(node_root / "CONTEXT.src.md", original)
        new_path.rename(old_path)
        raise

    return MoveResult(
        old_path=old_path,
        new_path=new_path,
        updated_nodes=staged_nodes,
        resource_ids=tuple(sorted({use.resource_id for use in uses if use.resource_id is not None})),
        inbound_markdown_links=inbound_links,
    )


def reconcile_resource(
    repo_root: Path,
    old_path: Path,
    new_path: Path,
) -> MoveResult:
    repo_root = repo_root.resolve()
    old_path = old_path.resolve()
    new_path = new_path.resolve()
    if old_path.exists():
        raise ContextCanonError(f"Reconcile expects the old Resource path to be missing: {old_path}")
    if not new_path.is_file():
        raise ContextCanonError(f"Reconcile candidate does not exist: {new_path}")
    try:
        old_path.relative_to(repo_root)
        new_path.relative_to(repo_root)
    except ValueError as exc:
        raise ContextCanonError("Resource reconciliation must stay inside the Git repository") from exc

    uses = _all_uses_for_path(repo_root, old_path)
    if not uses:
        raise ContextCanonError(f"No Topic Resource references missing path {old_path}")
    if any(use.resource_id is None for use in uses):
        raise ContextCanonError(
            "Resource reconciliation requires stable IDs for every affected ContextCanon reference; "
            "restore/register the Resource before moving it"
        )
    _validate_same_physical_node(repo_root, old_path, new_path)

    # Every semantic owner must agree that this exact candidate matches its
    # last built Resource bytes and relative Markdown closure.
    for use in uses:
        record = ResourceRecord(
            node_root=use.node_root,
            node_id=use.node_id,
            node_name=use.node_name,
            resource_id=use.resource_id,
            locator=use.locator,
            uses=tuple(item for item in uses if item.node_id == use.node_id and item.resource_id == use.resource_id),
        )
        baseline = _baseline_for_record(repo_root, record)
        if baseline is None:
            raise ContextCanonError(
                f"Resource {use.resource_id} has no verifiable previous built package; build once before external rename reconciliation"
            )
        content = new_path.read_bytes()
        digest = hashlib.sha256(content).hexdigest()
        if digest != baseline.sha256 or len(content) != baseline.size:
            raise ContextCanonError(
                f"Candidate {new_path.relative_to(repo_root).as_posix()} does not exactly match previous bytes for Resource {use.resource_id}"
            )
        after = _live_dependencies(repo_root, new_path)
        if baseline.dependencies != after:
            raise ContextCanonError(
                f"Candidate move for Resource {use.resource_id} changes relative Markdown closure; "
                f"before={list(baseline.dependencies)}, after={list(after)}"
            )

    inbound_links = _inbound_markdown_links(repo_root, old_path)
    updated_nodes = _apply_locator_rewrite(repo_root, old_path, new_path, uses)
    return MoveResult(
        old_path=old_path,
        new_path=new_path,
        updated_nodes=updated_nodes,
        resource_ids=tuple(sorted({use.resource_id for use in uses if use.resource_id is not None})),
        inbound_markdown_links=inbound_links,
    )


def resource_records_json(repo_root: Path, records: Iterable[ResourceRecord]) -> str:
    values = []
    for record in records:
        values.append(
            {
                "node_id": record.node_id,
                "node_name": record.node_name,
                "resource_id": record.resource_id,
                "path": record.path.relative_to(repo_root).as_posix(),
                "node_locator": record.locator,
                "used_by": [
                    {
                        "topic_id": use.topic_id,
                        "topic_title": use.topic_title,
                        "intent": use.intent,
                    }
                    for use in record.uses
                ],
            }
        )
    return json.dumps({"schema": "contextcanon/resource-list/v1", "resources": values}, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def resource_status_json(repo_root: Path, statuses: Iterable[ResourceStatus]) -> str:
    values = []
    for status in statuses:
        values.append(
            {
                "node_id": status.record.node_id,
                "node_name": status.record.node_name,
                "resource_id": status.record.resource_id,
                "state": status.state,
                "path": status.repo_path,
                "sha256": status.sha256,
                "size": status.size,
                "lines": status.lines,
                "baseline_path": status.baseline_repo_path,
                "baseline_sha256": status.baseline_sha256,
                "baseline_size": status.baseline_size,
                "closure_changed": status.closure_changed,
                "closure_before": list(status.closure_before),
                "closure_after": list(status.closure_after),
                "candidates": [
                    {
                        "path": candidate.repo_path,
                        "sha256": candidate.sha256,
                        "size": candidate.size,
                        "lines": candidate.lines,
                        "similarity": 100,
                    }
                    for candidate in status.candidates
                ],
            }
        )
    return json.dumps({"schema": "contextcanon/resource-status/v1", "resources": values}, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
