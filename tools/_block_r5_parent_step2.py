from __future__ import annotations

import argparse
from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one match, found {count}: {old[:120]!r}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


def replace_function(path: str, start_marker: str, end_marker: str, replacement: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    start = text.find(start_marker)
    end = text.find(end_marker, start)
    if start < 0 or end < 0:
        raise SystemExit(f"{path}: function boundary not found for {start_marker.strip()}")
    p.write_text(text[:start] + replacement.rstrip() + "\n\n" + text[end + 1 :], encoding="utf-8")


def patch_parser() -> None:
    replace_once(
        "src/contextcanon/parser.py",
        '''def parse_node(node_root: Path, repo_root: Path | None = None) -> ParsedNode:
    node_root = node_root.resolve()
    source_path = node_root / "CONTEXT.src.md"
    if not source_path.is_file():
        raise ContextCanonError(f"Not a Context Node root: {node_root} (missing CONTEXT.src.md)")

    repo_root = (repo_root or find_repo_root(node_root)).resolve()
    text = source_path.read_text(encoding="utf-8")
''',
        '''def parse_node(
    node_root: Path,
    repo_root: Path | None = None,
    *,
    source_text: str | None = None,
) -> ParsedNode:
    node_root = node_root.resolve()
    source_path = node_root / "CONTEXT.src.md"
    if not source_path.is_file():
        raise ContextCanonError(f"Not a Context Node root: {node_root} (missing CONTEXT.src.md)")

    repo_root = (repo_root or find_repo_root(node_root)).resolve()
    text = source_text if source_text is not None else source_path.read_text(encoding="utf-8")
''',
    )


def patch_compiler() -> None:
    replace_once(
        "src/contextcanon/compiler.py",
        '''class Compiler:
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root.resolve()
        self._cache: dict[Path, CompiledNode] = {}
        self._active: list[Path] = []
        self._node_ids: dict[str, Path] = {}
''',
        '''class Compiler:
    def __init__(
        self,
        repo_root: Path,
        *,
        source_overrides: dict[Path, str] | None = None,
        file_overrides: dict[Path, bytes] | None = None,
        package_overrides: dict[tuple[Path, str], tuple[CompiledPackage, dict[str, bytes]]] | None = None,
    ):
        self.repo_root = repo_root.resolve()
        self._cache: dict[Path, CompiledNode] = {}
        self._active: list[Path] = []
        self._node_ids: dict[str, Path] = {}
        self._source_overrides = {
            path.resolve(): text for path, text in (source_overrides or {}).items()
        }
        self._file_overrides = {
            path.resolve(): content for path, content in (file_overrides or {}).items()
        }
        self._package_overrides = {
            (root.resolve(), digest): value
            for (root, digest), value in (package_overrides or {}).items()
        }
''',
    )
    replace_once(
        "src/contextcanon/compiler.py",
        '''            parsed = parse_node(node_root, self.repo_root)
''',
        '''            parsed = parse_node(
                node_root,
                self.repo_root,
                source_text=self._source_overrides.get(node_root),
            )
''',
    )
    replace_once(
        "src/contextcanon/compiler.py",
        '''        package_root = node_root / ".context" / "sources" / dependency.package_digest
        if not package_root.is_dir():
            raise ContextCanonError(
                f"{node_root}: accepted {relation} package {dependency.name} is not available locally at "
                f".context/sources/{dependency.package_digest}; build does not fetch {relation} packages"
            )

        package = load_package(package_root)
''',
        '''        override = self._package_overrides.get((node_root.resolve(), dependency.package_digest))
        if override is not None:
            package, resources = override
        else:
            package_root = node_root / ".context" / "sources" / dependency.package_digest
            if not package_root.is_dir():
                raise ContextCanonError(
                    f"{node_root}: accepted {relation} package {dependency.name} is not available locally at "
                    f".context/sources/{dependency.package_digest}; build does not fetch {relation} packages"
                )
            package = load_package(package_root)
            resources = {
                file.path: (package_root / file.path).read_bytes()
                for file in package.files
                if file.path.startswith("CONTEXT/references/")
            }
''',
    )
    replace_once(
        "src/contextcanon/compiler.py",
        '''        resources = {
            file.path: (package_root / file.path).read_bytes()
            for file in package.files
            if file.path.startswith("CONTEXT/references/")
        }
        return package, resources
''',
        '''        return package, resources
''',
    )
    replace_once(
        "src/contextcanon/compiler.py",
        '''            content = source.read_bytes()
            if source.suffix.lower() != ".md":
''',
        '''            content = self._file_overrides.get(source, source.read_bytes())
            if source.suffix.lower() != ".md":
''',
    )
    replace_once(
        "src/contextcanon/compiler.py",
        '''                        content = source.read_bytes()
                        previous = resources.get(published)
''',
        '''                        content = self._file_overrides.get(source, source.read_bytes())
                        previous = resources.get(published)
''',
    )
    replace_once(
        "src/contextcanon/compiler.py",
        '''                target_node = parse_node(target_root, self.repo_root)
''',
        '''                target_node = parse_node(
                    target_root,
                    self.repo_root,
                    source_text=self._source_overrides.get(target_root),
                )
''',
    )


def patch_publication_model_and_helpers() -> None:
    replace_once(
        "src/contextcanon/onboarding_placement_publish.py",
        '''from .package import PACKAGE_MANIFEST_PATH, load_package
''',
        '''from .package import PACKAGE_MANIFEST_PATH, artifact_files, compiled_package, load_package
''',
    )
    replace_once(
        "src/contextcanon/onboarding_placement_publish.py",
        '''_MANAGED_SECTIONS = ("overview", "state", "plan", "sources", "rules", "topics")
''',
        '''_MANAGED_SECTIONS = ("overview", "state", "plan", "parent", "sources", "rules", "topics")
''',
    )
    anchor = '''@dataclass(frozen=True)
class PlacementDocumentDelta:
'''
    parent_dataclass = '''@dataclass(frozen=True)
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


'''
    replace_once("src/contextcanon/onboarding_placement_publish.py", anchor, parent_dataclass + anchor)
    replace_once(
        "src/contextcanon/onboarding_placement_publish.py",
        '''    nodes: tuple[PlacementNodeDelta, ...]
    sources: tuple[SourceGitProvenance, ...]
    followups: tuple[PlacementReviewItem, ...]
''',
        '''    nodes: tuple[PlacementNodeDelta, ...]
    parents: tuple[PlacementParentPin, ...]
    sources: tuple[SourceGitProvenance, ...]
    followups: tuple[PlacementReviewItem, ...]
''',
    )
    anchor = '''def _accepted_by_node(review: OnboardingPlacementReview) -> dict[str, list[PlacementReviewItem]]:
'''
    helpers = r'''def _structure_order(nodes) -> list:
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


'''
    replace_once("src/contextcanon/onboarding_placement_publish.py", anchor, helpers + anchor)


def patch_preview() -> None:
    replacement = r'''def build_placement_publication_preview(
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
            source_overrides[root] = _replace_managed_section(
                source_overrides[root], "Parent", "parent", ""
            )
        else:
            parent = node_by_key[node.parent_key]
            compiled_parent = compiled_by_key.get(parent.key)
            if compiled_parent is None:
                raise _error(f"internal error: Parent {parent.key} was not compiled before Child {node.key}")
            parent_root = _node_root(project, parent.path).resolve()
            body, locator = _render_parent_body(parent, compiled_parent, root, parent_root)
            source_overrides[root] = _replace_managed_section(
                source_overrides[root], "Parent", "parent", body
            )
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
'''
    replace_function(
        "src/contextcanon/onboarding_placement_publish.py",
        "def build_placement_publication_preview(\n",
        "\ndef render_placement_publication_preview(preview: PlacementPublicationPreview) -> str:\n",
        replacement,
    )
    replace_once(
        "src/contextcanon/onboarding_placement_publish.py",
        '''    lines.extend(["## Accepted reusable Source state", ""])
''',
        '''    lines.extend(["## Accepted semantic Parent chain", ""])
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
''',
    )
    replace_once(
        "src/contextcanon/onboarding_placement_publish.py",
        '''        lines.extend(["No accepted Overview, State/open-question, Plan, Rule, Topic/Resource or Source changes currently touch a Context Node.", ""])
''',
        '''        lines.extend(["No accepted placement or semantic Parent changes currently touch a Context Node.", ""])
''',
    )


def patch_package_copy_and_acceptance() -> None:
    anchor = '''def _snapshot_files(root: Path, rels: Iterable[str]) -> dict[str, bytes | None]:
'''
    helper = r'''def _copy_compiled_package(compiled, target_root: Path) -> bool:
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


'''
    replace_once("src/contextcanon/onboarding_placement_publish.py", anchor, helper + anchor)
    replace_once(
        "src/contextcanon/onboarding_placement_publish.py",
        '''        "nodes": node_digests,
        "sources": accepted_sources,
''',
        '''        "nodes": node_digests,
        "parents": [parent.to_dict() for parent in preview.parents],
        "sources": accepted_sources,
''',
    )


def patch_publish() -> None:
    replacement = r'''def publish_placement_review(
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
'''
    path = Path("src/contextcanon/onboarding_placement_publish.py")
    text = path.read_text(encoding="utf-8")
    start = text.find("def publish_placement_review(\n")
    if start < 0:
        raise SystemExit("publish_placement_review start not found")
    path.write_text(text[:start] + replacement.rstrip() + "\n", encoding="utf-8")


def patch_tests_and_docs() -> None:
    p = Path("tests/test_onboarding_placement_publish.py")
    text = p.read_text(encoding="utf-8")
    old = '''        self.assertEqual({delta.key for delta in preview.nodes}, {"N-001", "N-002"})
        child = next(delta for delta in preview.nodes if delta.key == "N-002")
        self.assertIn("Resource: `../../docs/architecture.md`", child.after)
        self.assertIn("Existing authored Goose orientation.", child.after)
'''
    new = '''        self.assertEqual({delta.key for delta in preview.nodes}, {"N-001", "N-002"})
        self.assertEqual(len(preview.parents), 1)
        parent = preview.parents[0]
        self.assertEqual((parent.child_key, parent.parent_key), ("N-002", "N-001"))
        child = next(delta for delta in preview.nodes if delta.key == "N-002")
        self.assertIn("## Parent", child.after)
        self.assertIn('ctx:parent id="aea56adf-2a26-43f0-b712-3bbeab7a3097"', child.after)
        self.assertIn(parent.parent_package_digest, child.after)
        self.assertIn("Resource: `../../docs/architecture.md`", child.after)
        self.assertIn("Existing authored Goose orientation.", child.after)
        self.assertFalse((repo / "compose" / "goose" / ".context" / "sources" / parent.parent_package_digest).exists())
'''
    if old not in text:
        raise SystemExit("placement preview parent assertion anchor missing")
    text = text.replace(old, new, 1)
    old = '''        self.assertIn("../../docs/architecture.md", child_text)
        Compiler(repo).compile(repo)
        Compiler(repo).compile(child_root)
        payload = json.loads(acceptance.read_text(encoding="utf-8"))
'''
    new = '''        self.assertIn("../../docs/architecture.md", child_text)
        parsed_child = parse_node(child_root, repo)
        self.assertIsNotNone(parsed_child.parent)
        self.assertEqual(parsed_child.parent.id, root_id)
        parent_store = child_root / ".context" / "sources" / parsed_child.parent.package_digest
        self.assertTrue(parent_store.is_dir())
        accepted_parent = load_package(parent_store)
        self.assertEqual(accepted_parent.metadata.id, root_id)
        compiled_root = Compiler(repo).compile(repo)
        compiled_child = Compiler(repo).compile(child_root)
        self.assertEqual(compiled_child.parent_package.package_digest, compiled_root.package_digest)
        self.assertIn(
            "The repository is the installation specification.",
            [rule.statement for rule in compiled_child.inherited_rules],
        )
        payload = json.loads(acceptance.read_text(encoding="utf-8"))
        self.assertEqual(len(payload["parents"]), 1)
        self.assertEqual(payload["parents"][0]["parent_package_digest"], compiled_root.package_digest)
        self.assertEqual(payload["nodes"]["N-002"]["parent_package_digest"], compiled_root.package_digest)
'''
    if old not in text:
        raise SystemExit("placement publication parent assertion anchor missing")
    text = text.replace(old, new, 1)
    p.write_text(text, encoding="utf-8")

    p = Path("nodes/internal/framework-development/docs/onboarding-reference.md")
    text = p.read_text(encoding="utf-8")
    needle = '''The human review is explicit. It participates only after the proposal is structurally/provenance-valid and before canonical publication.
'''
    addition = '''The human review is explicit. It participates only after the proposal is structurally/provenance-valid and before canonical publication.

For structure-first placement publication, the accepted Step-03 Parent hierarchy is also published deterministically. Preview computes the future Parent packages in semantic parent-to-child order using a read-only compiler overlay for reviewed `CONTEXT.src.md`, Source-After Resource bytes and exact catalog packages. Every non-root Child therefore receives an explicit `## Parent` pin to the exact final Parent package that the same publication will create. Publication installs that immutable Parent package locally before compiling the Child; repository nesting itself still carries no inheritance meaning.
'''
    if needle not in text:
        raise SystemExit("onboarding reference Parent publication anchor missing")
    text = text.replace(needle, addition, 1)
    p.write_text(text, encoding="utf-8")


def complete() -> None:
    p = Path("PLAN.md")
    text = p.read_text(encoding="utf-8")
    text = text.replace(
        "**Status: ACTIVE — R5 Semantic Parent relationship, step 2 of 5. Fast-run remains ACTIVE.**",
        "**Status: ACTIVE — R5 Semantic Parent relationship, step 3 of 5. Fast-run remains ACTIVE.**",
        1,
    )
    text = text.replace(
        "- [ ] 2. Persist every non-root accepted Step-03 parent into onboarding publication and pin the exact accepted Parent package locally in the Child.",
        "- [x] 2. Persist every non-root accepted Step-03 parent into onboarding publication and pin the exact accepted Parent package locally in the Child.",
        1,
    )
    p.write_text(text, encoding="utf-8")

    state = Path("STATE.md")
    current = state.read_text(encoding="utf-8").rstrip()
    block = '''

## Latest Block R5 step-2 onboarding-Parent publication checkpoint

Structure-first placement publication now preserves the owner-accepted Step-03 hierarchy as exact semantic Parent pins. Preview evaluates every accepted structure Node parent-to-child with the normal compiler behind a read-only overlay: reviewed future `CONTEXT.src.md` text, accepted Source-After Resource bytes and exact catalog packages are visible to compilation without mutating the project. The Child pin therefore names the exact final Parent package from the same reviewed publication, including any Parent meaning or Resource bytes being changed in that publication.

Publication writes the reviewed source/document deltas transactionally, installs direct reusable Source packages, then walks the semantic Parent chain from roots to leaves. Each final Parent artifact is installed into the Child's local immutable `.context/sources/<package-digest>/` store before the Child is compiled. Acceptance records preserve the Parent edge and exact package identity; rerunning the same reviewed publication is idempotent.

R5 step 3 is next: give Parent updates the same non-live candidate/review/accept safety as reusable Source updates. PR #13 remains draft and unmerged; fast-run remains active.
'''
    state.write_text(current + block.rstrip() + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--complete", action="store_true")
    args = parser.parse_args()
    if args.complete:
        complete()
        return
    patch_parser()
    patch_compiler()
    patch_publication_model_and_helpers()
    patch_preview()
    patch_package_copy_and_acceptance()
    patch_publish()
    patch_tests_and_docs()


if __name__ == "__main__":
    main()
