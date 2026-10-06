"""Removable, explicit migration of one existing onboarding run.

Preview never freezes inputs or advances a review. Runtime uses authenticated
location metadata, not these receipts. Copy/verify precedes activation; retirement
only removes the exact selected old files, and immutable history is retained.
"""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path, PurePosixPath

from .onboarding import find_enclosing_context_root, project_root_from_snapshot, resolve_onboarding_scope
from .onboarding_proposal import load_evidence_snapshot
from .onboarding_storage import (
    ACTIVE_MARKER, ACTIVE_SCHEMA, RUN_MARKER, SCOPE_MARKER, _json, _normal_path,
    _scope, _write_marker, binding_from_row, run_metadata, run_path, scope_root,
    handoff_path, HANDOFF_MARKER, HANDOFF_OWNER_SCHEMA,
)
from .onboarding_workspace import (
    CHECKPOINT_START, CHECKPOINT_END, COMMANDS_START, COMMANDS_END, PLAN_MARKER,
    WORKSPACE_MARKER, OnboardingWorkspace, _checkpoint_block, _checkpoint_snapshot,
    _checkpoint_stage, _checkpoint_review_complete, _completed_steps, _exact_commands,
    _snapshot_label, ensure_onboarding_gitignore, write_utf8,
)
from .package import PACKAGE_MANIFEST_PATH, load_package, load_package_files
from .parser import ContextCanonError
from .path_budget import preflight_paths
from .version_store import package_key, store_package, library_root, version_path
from .version_store import TOKEN_LENGTHS

SCHEMA = "contextcanon/onboarding-migration/v1"
PROVENANCE = ".context/onboarding-provenance.json"
INVENTORY = ("inventory-state.json", "inventory-acceptance.json")
RUN_FILES = {"manifest.json", "run-inputs.json", "reusable-contexts.json", "enclosing-parent.json",
             "placement-acceptance.json", "onboarding-reset-journal.json"}


def _error(message):
    return ContextCanonError("Onboarding migration: " + message)


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _tree(root):
    _normal_path(root)
    if not root.exists():
        return {}
    if not root.is_dir():
        raise _error(f"not a normal directory: {root}")
    result = {}
    for path in root.rglob("*"):
        _normal_path(path)
        if path.is_file():
            result[path.relative_to(root).as_posix()] = path.read_bytes()
        elif not path.is_dir():
            raise _error(f"not a regular file: {path}")
    return result


def _directories(root):
    _tree(root)  # Prove every ancestor/descendant is a normal path first.
    return {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_dir()} if root.exists() else set()


def _package(root, binding=None, *, provenance=False, authoring=False):
    _normal_path(root)
    _normal_path(root / PACKAGE_MANIFEST_PATH)
    files = None if authoring else _tree(root)
    package = load_package(root)
    allowed = {PACKAGE_MANIFEST_PATH, *(f.path for f in package.files)}
    if provenance:
        allowed.add(PROVENANCE)
    if files is not None and set(files) - allowed:
        raise _error(f"unknown files inside immutable package: {root}")
    if authoring:
        # A live Node also owns CONTEXT.src.md, docs and harness files. Only
        # verified manifest artifacts belong to its immutable package.
        for rel in allowed:
            _normal_path(root / rel)
        files = {rel: (root / rel).read_bytes() for rel in allowed if (root / rel).is_file()}
    contents = {rel: files[rel] for rel in allowed if rel != PROVENANCE and rel in files}
    package = load_package_files(contents)
    if binding is not None and (package_key(package) != package_key(binding) or
                              package.metadata.name != binding.name or package.metadata.version != binding.version):
        raise _error(f"exact frozen package binding mismatch: {root}")
    return package, contents


def _catalog_input(project, old, row):
    from .onboarding_reusable_contexts import _catalog_provenance, _read_historical_package
    binding = binding_from_row(row)
    original = row.get("path")
    if not isinstance(original, str) or not original:
        raise _error("accepted Catalog has no original provider locator")
    original = Path(original).expanduser().absolute()
    retained = None
    for root in (old / "reusable-context-packages" / binding.package_digest,
                 version_path(project, binding), project / ".context/sources" / binding.package_digest):
        if root.exists():
            retained = _package(root, binding, provenance=True)
            for path in (root / PROVENANCE, old / "catalog-provenance" / (package_key(binding) + ".json")):
                if path.is_file():
                    return (*retained, _json(path))
            break
    _normal_path(original)
    if retained is None:
        root = version_path(original, binding)
        if root.exists():
            retained = _package(root, binding)
            path = old / "catalog-provenance" / (package_key(binding) + ".json")
            if path.is_file():
                return (*retained, _json(path))
    # Legacy reviews could bind identity before catalog bytes were frozen.
    # Reuse the existing Git reader, without creating a legacy freeze, staging
    # directory or checkout during preview. Never substitute a newer provider.
    historical = _read_historical_package(original, binding.package_digest, binding)
    if historical is not None:
        package, files, provenance = historical
        if package.metadata.name != binding.name or package.metadata.version != binding.version:
            raise _error("historical Catalog binding mismatch")
        return (*(retained or (package, files)), provenance)
    try:
        current = _package(original, binding, authoring=True)
        provenance = _catalog_provenance(original, current[0])
    except (ContextCanonError, OSError) as exc:
        raise _error(
            f"exact accepted Catalog package/provenance cannot be recovered: {binding.name} "
            f"{binding.version} (Node {binding.id}; package {binding.package_digest}). "
            "No matching frozen package with provenance or verified local Git history was found. "
            f"Original provider: {original}. Preserve/recover its historical package or Git history; "
            "do not substitute the newer provider or restart accepted review merely to migrate."
        ) from exc
    return (*(retained or current), provenance)


def _relative(repository, path):
    try:
        return path.relative_to(repository).as_posix()
    except ValueError as exc:
        raise _error("migration workspace must be inside this Git repository; external custom workspaces remain usable without migration") from exc


def _path(repository, value):
    if not isinstance(value, str) or not value or PurePosixPath(value).is_absolute() or "\\" in value or ":" in value or any(part in {"", ".", ".."} for part in value.split("/")):
        raise _error("unsafe receipt locator")
    result = repository / value
    _normal_path(result)
    return result


def _receipt_path(project):
    repository, _, key = _scope(project)
    return repository / ".context/onboarding-migrations" / (key[:16] + ".json")


def _owned_workspace(root, old):
    files = _tree(root)
    if not files:
        return files
    if WORKSPACE_MARKER not in files.get("README.md", b"").decode("utf-8"):
        raise _error(f"unowned workspace: {root}")
    plan = files.get("PLAN.md", b"").decode("utf-8")
    checkpoint = _checkpoint_block(plan, root / "PLAN.md")
    if PLAN_MARKER not in plan or _checkpoint_snapshot(checkpoint) != _snapshot_label(old):
        raise _error("workspace PLAN is not bound to the selected old snapshot")
    # Unknown files are not claimed merely because a README marker exists.
    from .onboarding_workspace import LEGACY_ARTIFACT_NAMES, LEGACY_DIRECTORY_NAMES
    from .onboarding_reset import _ARTIFACT_STEPS
    names = set(_ARTIFACT_STEPS) | set(LEGACY_ARTIFACT_NAMES) | set(LEGACY_DIRECTORY_NAMES)
    names |= {"README.md", "PLAN.md", "STEP-02-inventory.csv", "STEP-02-inventory-guide.md", "handoffs"}
    unknown = sorted({rel.split("/")[0] for rel in [*files, *_directories(root)]
                      if rel.split("/")[0] not in names})
    if unknown:
        entries = "\n".join(f"  - {name}{'/' if (root / name).is_dir() else ''}" for name in unknown)
        raise _error(
            f"unknown files or directories in workspace: {root}\n"
            f"Unrecognized entries (relative to this workspace):\n{entries}\n"
            "No files were changed. The selected snapshot passed the workspace binding check; "
            "changing --snapshot does not resolve these unrecognized entries. "
            "If these are ContextCanon artifacts, report their names. Otherwise, preserve them "
            "outside the onboarding workspace and retry; do not delete them."
        )
    return files


def _plan_bytes(data, project, old, new, workspace, run_inputs):
    text = data.decode("utf-8")
    checkpoint = _checkpoint_block(text, workspace / "PLAN.md")
    if _checkpoint_snapshot(checkpoint) != _snapshot_label(old):
        raise _error("workspace checkpoint changed while planning")
    block = _exact_commands(OnboardingWorkspace(workspace), new,
                            tuple(run_inputs.get("catalog_package_inputs", [])),
                            tuple(run_inputs.get("owner_source_specs", [])),
                            completed=_completed_steps(_checkpoint_stage(checkpoint) or "evidence prepared",
                                                       _checkpoint_review_complete(checkpoint)), project_root=project,
                            evidence_digest=load_evidence_snapshot(old).evidence_digest, central_handoffs=True)
    if "\r\n" in text:
        block = block.replace("\n", "\r\n")
    if text.count(COMMANDS_START) != 1 or text.count(COMMANDS_END) != 1:
        raise _error("workspace PLAN has no unique managed commands block")
    start, end = text.index(COMMANDS_START), text.index(COMMANDS_END) + len(COMMANDS_END)
    text = text[:start] + block + text[end:]
    # Only the owned locator lines change; rationale, stage and reviewed hashes do not.
    old_label, new_label = _snapshot_label(old), _snapshot_label(new, project)
    for label in ("Snapshot", "Evidence snapshot"):
        checkpoint = checkpoint.replace(f"- {label}: `{old_label}`", f"- {label}: `{new_label}`")
    start, end = text.index(CHECKPOINT_START), text.index(CHECKPOINT_END) + len(CHECKPOINT_END)
    return (text[:start] + checkpoint + text[end:]).encode("utf-8")


def _verify_handoff(root, payload, evidence, zip_path):
    """Verify portable frozen inputs before claiming/copying a disposable task."""
    import zipfile
    from .onboarding_handoff import handoff_spec
    files = _tree(root)
    control = ".contextcanon-handoff/"
    expected = {control + name for name in ("PLAN.md", "INSTRUCTION.md", "manifest.json")}
    if _sha(files.get(control + "INSTRUCTION.md", b"")) != payload.get("instruction_sha256"):
        raise _error("frozen handoff instruction changed")
    for row in payload.get("evidence", []):
        rel = row.get("path")
        original = evidence.by_path.get(rel)
        data = files.get(rel)
        if original is None or data is None or row.get("sha256") != original.sha256 or row.get("size") != original.size or _sha(data) != original.sha256 or len(data) != original.size:
            raise _error("frozen handoff Evidence changed")
        expected.add(rel)
    parent = payload.get("enclosing_parent")
    if parent is not None:
        binding = binding_from_row({**parent, "id": parent.get("node_id")})
        if parent.get("root") != control + "enclosing-parent":
            raise _error("unsafe handoff Parent locator")
        _, packaged = _package(root / parent["root"], binding)
        rows = parent.get("files")
        if not isinstance(rows, list) or {r.get("path"): (r.get("sha256"), r.get("size")) for r in rows} != {rel: (_sha(data), len(data)) for rel, data in packaged.items()}:
            raise _error("frozen handoff Parent files changed")
        expected.update(parent["root"] + "/" + rel for rel in packaged)
    missing = sorted(expected - set(files))
    unknown = sorted(set(files) - expected - {control + "RESULT.json"})
    if missing or unknown:
        details = []
        if unknown:
            details.append("Unrecognized files (relative to this handoff):\n" +
                           "\n".join(f"  - {rel}" for rel in unknown))
        if missing:
            details.append("Missing required files (relative to this handoff):\n" +
                           "\n".join(f"  - {rel}" for rel in missing))
        guidance = ["No files were changed. Keep the handoff and its RESULT.json."]
        if unknown:
            guidance.append("If unrecognized files are ContextCanon artifacts, report their names. "
                            "Otherwise, preserve them outside this handoff and retry; do not delete them.")
        if missing:
            guidance.append("Restore missing files from the original handoff ZIP or a backup. "
                            "Do not regenerate frozen inputs from the current project or a newer Parent.")
        raise _error(f"STEP {payload['step']:02d} handoff has unrecognized or missing files: {root}\n" +
                     "\n".join([*details, *guidance]))
    if zip_path.exists():
        try:
            with zipfile.ZipFile(zip_path) as archive:
                prefix = handoff_spec(payload["step"]).directory_name + "/"
                names = {prefix + rel for rel in expected}
                if len(archive.namelist()) != len(names) or set(archive.namelist()) != names or any(archive.read(prefix + rel) != files[rel] for rel in expected):
                    raise _error("frozen handoff ZIP differs from its verified inputs")
        except (OSError, zipfile.BadZipFile) as exc:
            raise _error("frozen handoff ZIP is unreadable") from exc


def _parent_input(project, old, workspace, packages):
    record = old / "enclosing-parent.json"
    if record.exists():
        value = _json(record)
        if value.get("schema") != "contextcanon/onboarding-enclosing-parent/v1":
            raise _error("unsupported enclosing Parent record")
        if value.get("binding") is None:
            if set(value) != {"schema", "binding"}:
                raise _error("invalid enclosing Parent record")
            return value
        binding = binding_from_row(value["binding"])
        root = version_path(project, binding)
        if not root.exists():
            root = project / ".context/sources" / binding.package_digest
        package, files = _package(root, binding)
        packages[package_key(package)] = (package, files)
        node = value.get("node_path")
        _path(resolve_onboarding_scope(project).repository_root, node) if node != "." else None
        return value
    parent = find_enclosing_context_root(project)
    retained = []
    for manifest in workspace.glob("handoffs/*/.contextcanon-handoff/manifest.json"):
        payload = _json(manifest)
        if payload.get("evidence_digest") != load_evidence_snapshot(old).evidence_digest:
            raise _error("handoff belongs to another Evidence snapshot")
        row = payload.get("enclosing_parent")
        if row is None:
            continue
        binding = binding_from_row({**row, "id": row.get("node_id")})
        root_rel = row.get("root")
        if root_rel != ".contextcanon-handoff/enclosing-parent":
            raise _error("unsafe enclosing Parent handoff locator")
        root = manifest.parent.parent / root_rel
        package, files = _package(root, binding)
        expected = row.get("files")
        if not isinstance(expected, list) or {r.get("path"): (r.get("sha256"), r.get("size")) for r in expected} != {p: (_sha(b), len(b)) for p, b in files.items()}:
            raise _error("frozen enclosing Parent handoff file set changed")
        retained.append((package, files))
    if not retained and parent is None:
        return {"schema": "contextcanon/onboarding-enclosing-parent/v1", "binding": None}
    if not retained or len({package_key(p) for p, _ in retained}) != 1:
        raise _error("exact old enclosing Parent is unavailable/ambiguous; retain its frozen handoff or restart before STEP 04; a newer live Parent is not a substitute")
    package, files = retained[0]
    # The enclosing scope supplies a locator, never replacement package bytes.
    from .parser import parse_node
    repository = resolve_onboarding_scope(project).repository_root
    matches = []
    for ancestor in project.parents:
        if not ancestor.is_relative_to(repository):
            break
        source = ancestor / "CONTEXT.src.md"
        if source.is_file():
            identity = parse_node(ancestor, repository).metadata.id
        elif (ancestor / PACKAGE_MANIFEST_PATH).is_file():
            identity = load_package(ancestor).metadata.id
        else:
            continue
        if identity == package.metadata.id:
            matches.append(ancestor)
    if len(matches) != 1:
        raise _error("cannot prove the old enclosing Parent authoring locator")
    parent = matches[0]
    packages[package_key(package)] = (package, files)
    return {"schema": "contextcanon/onboarding-enclosing-parent/v1",
            "node_path": parent.relative_to(resolve_onboarding_scope(project).repository_root).as_posix(),
            "binding": {"id": package.metadata.id, "name": package.metadata.name, "version": package.metadata.version,
                        "normalized_digest": package.normalized_digest, "package_digest": package.package_digest}}


def _journal(data, project, old, packages):
    from .onboarding_reset import RESET_JOURNAL_SCHEMA, _change_path, _unb64
    value = json.loads(data)
    if value.get("schema") != RESET_JOURNAL_SCHEMA or not isinstance(value.get("records"), list):
        raise _error("invalid legacy reset journal")
    acceptance = (old / "placement-acceptance.json").relative_to(project).as_posix()
    installations = {}
    for record in value["records"]:
        kept = []
        for change in record.get("changes", []):
            _change_path(project, change, old)
            rel = change["path"]
            if rel == acceptance:
                change["path"] = "@run/placement-acceptance.json"
            elif ".context/sources/" in rel:
                # Immutable new installations are retained outside reset ownership.
                parts = PurePosixPath(rel).parts
                index = parts.index(".context")
                if len(parts) <= index + 3 or parts[index + 1] != "sources":
                    raise _error("unrecognized package installation journal path")
                root = project.joinpath(*parts[:index + 3])
                if root not in installations:
                    if root.exists():
                        installations[root] = _package(root)
                    else:
                        # Normal versions migration may already have retired
                        # this wrapper. Its journaled manifest hash proves the
                        # full old identity in the shared library, offline.
                        manifest_rel = root.relative_to(project).as_posix() + "/" + PACKAGE_MANIFEST_PATH
                        manifests = [c for c in record.get("changes", []) if c.get("path") == manifest_rel and c.get("before") is None and c.get("after_exists")]
                        matches = []
                        if len(manifests) == 1:
                            for candidate in library_root(project).glob("*/.context/package.json"):
                                if _sha(candidate.read_bytes()) == manifests[0].get("after_sha256"):
                                    p, content = _package(candidate.parent.parent)
                                    if p.package_digest == root.name:
                                        matches.append((p, content))
                        if len(matches) != 1:
                            raise _error("legacy installation is unavailable and its exact journaled manifest cannot be proved in shared history")
                        installations[root] = matches[0]
                package, files = installations[root]
                inner = PurePosixPath(*parts[index + 3:]).as_posix()
                if change.get("before") is not None or not change.get("after_exists") or inner not in files or _sha(files[inner]) != change.get("after_sha256"):
                    raise _error("legacy package journal is not a verified new immutable installation; retain the old run until reviewed recovery")
                packages[package_key(package)] = (package, files)
                continue
            else:
                _unb64(change.get("before"))
            kept.append(change)
        record["changes"] = kept
    return _bytes(value)


def plan_migration(target: Path, *, snapshot: Path | None = None, workspace: Path | None = None):
    scope = resolve_onboarding_scope(target)
    project, repository = scope.project_root, scope.repository_root
    old_scope = project / ".context/onboarding"
    if snapshot is None:
        acceptance = old_scope / "inventory-acceptance.json"
        if acceptance.exists():
            digest = _json(acceptance).get("evidence_digest")
            if not isinstance(digest, str) or len(digest) != 64:
                raise _error("inventory acceptance has no exact Evidence identity")
            snapshot = old_scope / digest
        else:
            candidates = [p for p in old_scope.glob("*/manifest.json")]
            if len(candidates) != 1:
                raise _error("select the active legacy Evidence snapshot with --snapshot; historical runs are never chosen arbitrarily")
            snapshot = candidates[0].parent
    old = snapshot.absolute()
    _normal_path(old)
    old = old.resolve()  # Windows 8.3 aliases must share canonical scope ownership.
    if old.parent != old_scope or project_root_from_snapshot(old) != project:
        raise _error("snapshot is not a project-local legacy run owned by this project")
    evidence = load_evidence_snapshot(old)
    if old.name != evidence.evidence_digest:
        raise _error("legacy locator does not match its full Evidence identity")
    new = run_path(project, evidence.evidence_digest, central=True, create=False)
    old_workspace = (workspace or project / "contextcanon-onboarding").absolute()
    _normal_path(old_workspace)
    old_workspace = old_workspace.resolve()
    _relative(repository, old_workspace)
    new_workspace = old_workspace
    if old_workspace == project / "contextcanon-onboarding" and project != repository:
        new_workspace = repository / ("contextcanon-onboarding-" + new.parent.name)
    workspace_files = _owned_workspace(old_workspace, old)
    old_files = _tree(old)
    if any(rel.split("/")[0] not in RUN_FILES | {"evidence", "reusable-context-packages", "catalog-provenance"} for rel in [*old_files, *_directories(old)]):
        raise _error("unknown files in selected legacy run; migration did not change anything")
    packages = {}
    copied = {rel: data for rel, data in old_files.items() if not rel.startswith("reusable-context-packages/")}
    state = _json(old / "reusable-contexts.json") if (old / "reusable-contexts.json").exists() else None
    if state is not None:
        rows = state.get("catalog_packages")
        if state.get("schema") not in {"contextcanon/onboarding-reusable-contexts-state/v0", "contextcanon/onboarding-reusable-contexts-state/v1"} or not isinstance(rows, list):
            raise _error("unsupported reusable Context state")
        frozen_rows = []
        for row in rows:
            binding = binding_from_row(row)
            package, files, provenance = _catalog_input(project, old, row)
            if provenance.get("schema") != "contextcanon/onboarding-reusable-package-provenance/v0" or provenance.get("package_digest") != package.package_digest:
                raise _error("invalid frozen Catalog provenance")
            provenance.update(node_id=package.metadata.id, normalized_digest=package.normalized_digest)
            packages[package_key(package)] = (package, files)
            copied["catalog-provenance/" + package_key(package) + ".json"] = _bytes(provenance)
            frozen_rows.append({"id": package.metadata.id, "normalized_digest": package.normalized_digest,
                                "package_digest": package.package_digest, "path": str(version_path(project, package))})
        state["frozen_catalog_packages"] = frozen_rows
        copied["reusable-contexts.json"] = _bytes(state)
    # All old frozen package files must correspond to a reviewed Catalog entry.
    expected_packages = {r["package_digest"] for r in state.get("catalog_packages", [])} if state else set()
    if any(rel.split("/")[1] not in expected_packages for rel in old_files if rel.startswith("reusable-context-packages/")):
        raise _error("unreviewed frozen package directory in selected run")
    copied["enclosing-parent.json"] = _bytes(_parent_input(project, old, old_workspace, packages))
    if "onboarding-reset-journal.json" in copied:
        copied["onboarding-reset-journal.json"] = _journal(copied["onboarding-reset-journal.json"], project, old, packages)
    copied[RUN_MARKER] = _bytes(run_metadata(project, evidence.evidence_digest))
    if "PLAN.md" in workspace_files:
        inputs = _json(old / "run-inputs.json") if (old / "run-inputs.json").exists() else {}
        workspace_files["PLAN.md"] = _plan_bytes(workspace_files["PLAN.md"], project, old, new, new_workspace, inputs)
    writes = {new / rel: data for rel, data in copied.items()}
    handoffs = []
    handoff_dirs = []
    legacy_handoff_files = {}
    legacy_handoff_dirs = []
    from .onboarding_handoff import handoff_relative_paths
    for step in (4, 8):
        relative_dir, relative_zip = handoff_relative_paths(step)
        legacy_dir, legacy_zip = old_workspace / relative_dir, old_workspace / relative_zip
        if not legacy_dir.exists():
            continue
        payload = _json(legacy_dir / ".contextcanon-handoff/manifest.json")
        if payload.get("schema") != "contextcanon/semantic-handoff/v1" or payload.get("step") != step or payload.get("evidence_digest") != evidence.evidence_digest:
            raise _error("legacy handoff is not bound to the selected run")
        _verify_handoff(legacy_dir, payload, evidence, legacy_zip)
        handoff = handoff_path(project, evidence.evidence_digest, step)
        handoff_files = _tree(legacy_dir)
        legacy_handoff_files.update({legacy_dir / rel: data for rel, data in handoff_files.items()})
        legacy_handoff_dirs.extend([legacy_dir, *(legacy_dir / rel for rel in _directories(legacy_dir))])
        actual = _tree(handoff)
        owner = {"schema": HANDOFF_OWNER_SCHEMA, "project_path": project.relative_to(repository).as_posix(),
                 "evidence_digest": evidence.evidence_digest, "step": step}
        for rel, data in actual.items():
            if rel != HANDOFF_MARKER and handoff_files.get(rel) != data:
                raise _error("foreign/changed central handoff")
        writes.update({handoff / rel: data for rel, data in handoff_files.items()})
        writes[handoff / HANDOFF_MARKER] = actual.get(HANDOFF_MARKER, (json.dumps(owner, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8"))
        if legacy_zip.exists():
            writes[handoff.with_suffix(".zip")] = legacy_zip.read_bytes()
            legacy_handoff_files[legacy_zip] = legacy_zip.read_bytes()
        handoffs.append({"step": step, "root": _relative(repository, handoff), "zip": _relative(repository, handoff.with_suffix(".zip"))})
        handoff_dirs.extend(_relative(repository, handoff / rel) for rel in _directories(legacy_dir))
        workspace_files = {rel: data for rel, data in workspace_files.items() if not rel.startswith(relative_dir + "/") and rel != relative_zip}
    writes.update({new_workspace / rel: data for rel, data in workspace_files.items()})
    inventory = {}
    for name in INVENTORY:
        source = old_scope / name
        if not source.exists():
            continue
        value = _json(source)
        if name == "inventory-acceptance.json" and value.get("evidence_digest") != evidence.evidence_digest:
            raise _error("selected run is not the accepted inventory run; preserve its scope routing")
        field = "csv_path" if name == "inventory-state.json" else "inventory_path"
        if isinstance(value.get(field), str):
            known = value[field]
            resolved = Path(known) if Path(known).is_absolute() else project / known
            if resolved.resolve() != old_workspace / "STEP-02-inventory.csv":
                raise _error("inventory locator is not bound to the selected owned workspace")
            value[field] = str(new_workspace / "STEP-02-inventory.csv")
        inventory[source] = source.read_bytes()
        writes[new.parent / name] = _bytes(value)
    # Fail before any receipt/destination is created on a foreign or changed target.
    for root, expected in ((new, copied), (new_workspace, workspace_files)):
        if root == old_workspace:
            continue
        actual = _tree(root)
        if any(rel not in expected or data != expected[rel] for rel, data in actual.items()):
            raise _error(f"foreign/changed destination: {root}")
    for path, data in writes.items():
        _normal_path(path)
        preflight_paths(path.parent, [path.name, ".tmp-xxxxxxxx"], action="onboarding migration publication", node_root=project)
        if path.exists() and path not in {old_workspace / "PLAN.md"} and path.read_bytes() != data:
            raise _error(f"destination changed: {path}")
    for package, files in packages.values():
        preflight_paths(version_path(project, package), files, action="onboarding migration immutable package", node_root=project)
    _, expected_scope, _ = _scope(project)
    activation = {"schema": ACTIVE_SCHEMA, "project_path": expected_scope["project_path"],
                  "workspace_path": _relative(repository, new_workspace)}
    retire = {old / rel: data for rel, data in old_files.items()}
    retire.update(inventory)
    retire.update(legacy_handoff_files)
    if new_workspace != old_workspace:
        retire.update({old_workspace / rel: data for rel, data in _tree(old_workspace).items()})
    receipt = {"schema": SCHEMA, "project_path": expected_scope["project_path"], "evidence_digest": evidence.evidence_digest,
               "old_run": _relative(repository, old), "new_run": _relative(repository, new),
               "old_workspace": _relative(repository, old_workspace), "new_workspace": _relative(repository, new_workspace),
               "phase": "copy", "packages_ready": False, "activation": activation,
               "packages": [{"id": p.metadata.id, "name": p.metadata.name, "version": p.metadata.version,
                             "normalized_digest": p.normalized_digest, "package_digest": p.package_digest} for p, _ in packages.values()],
               "sources": [{"path": _relative(repository, p), "sha256": _sha(data)} for p, data in
                           {**{old / rel: data for rel, data in old_files.items()},
                            **{old_workspace / rel: data for rel, data in _tree(old_workspace).items()}, **inventory}.items()],
               "writes": [{"path": _relative(repository, p), "sha256": _sha(data), "data": base64.b64encode(data).decode("ascii")} for p, data in writes.items()],
               "retire": [{"path": _relative(repository, p), "sha256": _sha(data)} for p, data in retire.items()],
               "original_records": {rel: base64.b64encode(old_files[rel]).decode("ascii") for rel in RUN_FILES if rel in old_files and copied.get(rel) != old_files[rel]}}
    receipt["handoffs"] = handoffs
    receipt["directories"] = handoff_dirs + [_relative(repository, new_workspace / rel) for rel in sorted(_directories(old_workspace)) if not rel.startswith("handoffs")]
    receipt["retire_directories"] = [_relative(repository, old / rel) for rel in sorted(_directories(old))]
    receipt["retire_directories"] += [_relative(repository, directory) for directory in legacy_handoff_dirs]
    if new_workspace != old_workspace:
        receipt["retire_directories"] += [_relative(repository, old_workspace / rel) for rel in sorted(_directories(old_workspace))]
    return project, repository, receipt, packages


def _validate_receipt(project, repository, receipt):
    _, expected, _ = _scope(project)
    if receipt.get("schema") != SCHEMA or receipt.get("project_path") != expected["project_path"] or receipt.get("phase") not in {"copy", "retire", "complete"}:
        raise _error("invalid/foreign recovery receipt")
    old, new = (_path(repository, receipt[k]) for k in ("old_run", "new_run"))
    if old.parent != project / ".context/onboarding" or old.name != receipt.get("evidence_digest") or new.parent != scope_root(project, legacy=False) or len(new.name) not in TOKEN_LENGTHS or not old.name.startswith(new.name):
        raise _error("receipt run ownership mismatch")
    ow, nw = (_path(repository, receipt[k]) for k in ("old_workspace", "new_workspace"))
    allowed_new = {new, nw}
    allowed_old = {old, ow} if ow != nw else {old}
    if ow == nw:
        allowed_old.add(ow / "handoffs")
    handoff_zips = set()
    for row in receipt.get("handoffs", []):
        handoff = _path(repository, row["root"])
        # The exact token is authenticated by metadata once installed; before
        # copying, the receipt's full project/Evidence/step binds allocation.
        owner = {"schema": HANDOFF_OWNER_SCHEMA, "project_path": expected["project_path"],
                 "evidence_digest": old.name, "step": row["step"]}
        key = hashlib.sha256(json.dumps(owner, sort_keys=True).encode("utf-8")).hexdigest()
        if row["step"] not in {4, 8} or handoff.parent != repository / ".context/handoffs" or len(handoff.name) not in TOKEN_LENGTHS or not key.startswith(handoff.name):
            raise _error("receipt handoff ownership mismatch")
        if (handoff / HANDOFF_MARKER).exists() and _json(handoff / HANDOFF_MARKER) != owner:
            raise _error("receipt handoff owner changed")
        if row["zip"] != _relative(repository, handoff.with_suffix(".zip")):
            raise _error("receipt handoff ZIP ownership mismatch")
        allowed_new.add(handoff)
        handoff_zips.add(handoff.with_suffix(".zip"))
    for record in receipt.get("writes", []):
        path = _path(repository, record.get("path"))
        if not any(path.is_relative_to(root) for root in allowed_new) and path not in {new.parent / n for n in INVENTORY} | handoff_zips:
            raise _error("receipt write escapes selected run/workspace")
        if receipt["phase"] != "complete":
            data = base64.b64decode(record["data"], validate=True)
            if _sha(data) != record.get("sha256"):
                raise _error("receipt copied bytes changed")
    for record in [*receipt.get("retire", []), *receipt.get("sources", [])]:
        path = _path(repository, record.get("path"))
        roots = {old, ow} if record in receipt.get("sources", []) else allowed_old
        if not any(path.is_relative_to(root) for root in roots) and path not in {old.parent / n for n in INVENTORY}:
            raise _error("receipt retirement escapes selected run/workspace")
    for key, roots in (("directories", allowed_new), ("retire_directories", allowed_old)):
        for relative in receipt.get(key, []):
            path = _path(repository, relative)
            if not any(path.is_relative_to(root) for root in roots):
                raise _error("receipt directory escapes selected run/workspace")
    if receipt.get("activation") != {"schema": ACTIVE_SCHEMA, "project_path": expected["project_path"], "workspace_path": receipt["new_workspace"]}:
        raise _error("receipt activation ownership mismatch")
    return old, new, ow, nw


def _verify_copy_sources(repository, receipt):
    writes = {r["path"]: r for r in receipt["writes"]}
    for record in receipt["sources"]:
        path = _path(repository, record["path"])
        digest = _sha(path.read_bytes()) if path.is_file() else None
        if digest != record["sha256"]:
            # Only the framework-owned in-place PLAN may already be rebound.
            written = writes.get(record["path"])
            if path.name != "PLAN.md" or written is None or digest != written["sha256"]:
                raise _error(f"migration inputs changed; no human files overwritten: {path}")


def _save(path, receipt):
    write_utf8(path, _bytes(receipt).decode("utf-8"))


def _copy_binary(path, data):
    import os
    import tempfile
    path.parent.mkdir(parents=True, exist_ok=True)
    preflight_paths(path.parent, [path.name, ".tmp-xxxxxxxx"], action="onboarding migration copy")
    fd, name = tempfile.mkstemp(prefix=".tmp-", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        from .onboarding_workspace import _replace_file_with_retry
        _replace_file_with_retry(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _retire_file(path, digest):
    if not path.exists():
        return
    if not path.is_file() or _sha(path.read_bytes()) != digest:
        raise _error(f"legacy file changed; new run remains usable, retirement paused: {path}")
    path.unlink()


def migrate_onboarding(target: Path, *, snapshot: Path | None = None, workspace: Path | None = None, apply=False):
    scope = resolve_onboarding_scope(target)
    project, repository = scope.project_root, scope.repository_root
    receipt_path = _receipt_path(project)
    _normal_path(receipt_path)
    if receipt_path.exists():
        receipt = _json(receipt_path)
        old, new, ow, nw = _validate_receipt(project, repository, receipt)
        if snapshot is not None:
            _normal_path(snapshot.absolute())
            if snapshot.resolve() not in {old, new}:
                raise _error("existing migration receipt belongs to a different run")
        packages = {}
        if receipt["phase"] == "copy":
            # Sources still exist. Re-plan read-only to prove frozen packages and
            # current mutable inputs; never trust a receipt to overwrite edits.
            _verify_copy_sources(repository, receipt)
            if not receipt["packages_ready"]:
                _, _, current, packages = plan_migration(project, snapshot=old, workspace=ow)
                if current != receipt:
                    raise _error("migration inputs changed since preview/apply; no files overwritten")
            else:
                for row in receipt["packages"]:
                    binding = binding_from_row(row)
                    _package(version_path(project, binding), binding)
    else:
        if scope_root(project) != project / ".context/onboarding":
            return {"status": "already central", "project": str(project), "workspace": str(workspace) if workspace else None}
        project, repository, receipt, packages = plan_migration(project, snapshot=snapshot, workspace=workspace)
        old, new, ow, nw = _validate_receipt(project, repository, receipt)
    result = {"status": receipt["phase"], "project": str(project), "old_snapshot": str(old),
              "snapshot": str(new), "workspace": str(nw), "apply": apply,
              "files_to_copy": len(receipt["writes"]), "legacy_files_to_retire": len(receipt["retire"]),
              "receipt": str(receipt_path)}
    if not apply or receipt["phase"] == "complete":
        return result
    if not receipt_path.exists():
        _save(receipt_path, receipt)
    if receipt["phase"] == "copy":
        scope_root(project, create=True, legacy=False)
        for package, files in packages.values():
            store_package(library_root(project), package, files, action="onboarding migration frozen version", node_root=project)
        if not receipt["packages_ready"]:
            receipt["packages_ready"] = True
            _save(receipt_path, receipt)
        # Mark allocated handoffs before copying nested inputs, so runtime and
        # interrupted migration resolve the same complete ownership identity.
        for record in receipt["writes"]:
            if _path(repository, record["path"]).name == HANDOFF_MARKER:
                _write_marker(_path(repository, record["path"]), json.loads(base64.b64decode(record["data"])))
        for relative in receipt["directories"]:
            _path(repository, relative).mkdir(parents=True, exist_ok=True)
        expected = {r["path"]: r["sha256"] for r in receipt["writes"]}
        sources = {r["path"]: r["sha256"] for r in receipt["sources"]}
        retiring = {r["path"]: r["sha256"] for r in receipt["retire"]}
        for root in (new, nw, *(_path(repository, row["root"]) for row in receipt["handoffs"])):
            for rel, data in _tree(root).items():
                key = _relative(repository, root / rel)
                if key not in expected and retiring.get(key) == _sha(data):
                    continue
                if key not in expected or _sha(data) not in {expected[key], sources.get(key)}:
                    raise _error(f"foreign/changed destination during recovery: {root / rel}")
        for record in receipt["writes"]:
            path = _path(repository, record["path"])
            data = base64.b64decode(record["data"])
            if not path.exists() or path.read_bytes() != data:
                _copy_binary(path, data)
        _verify_copy_sources(repository, receipt)
        load_evidence_snapshot(new)
        ensure_onboarding_gitignore(project, nw)
        # Record verified copy completion before activation. Retry can safely
        # finish activation without consulting retired source/package wrappers.
        receipt["phase"] = "retire"
        _save(receipt_path, receipt)
    _write_marker(new.parent / ACTIVE_MARKER, receipt["activation"])
    load_evidence_snapshot(new)
    retire_paths = {r["path"] for r in receipt["retire"]}
    retirement_roots = (old, ow) if ow != nw else (old, ow / "handoffs")
    for root in retirement_roots:
        for relative in _tree(root):
            if _relative(repository, root / relative) not in retire_paths:
                raise _error("unknown file appeared in legacy storage; new run remains usable")
        for relative in _directories(root):
            if _relative(repository, root / relative) not in receipt["retire_directories"]:
                raise _error("unknown directory appeared in legacy storage; new run remains usable")
    for record in receipt["retire"]:
        _retire_file(_path(repository, record["path"]), record["sha256"])
    for root in retirement_roots:
        if root.exists():
            for directory in sorted((p for p in root.rglob("*") if p.is_dir()), key=lambda p: len(p.parts), reverse=True):
                directory.rmdir()
            root.rmdir()
    receipt["phase"] = "complete"
    # Large frozen bytes now live in their authoritative destinations. Keep
    # hashes and original transformed records, not another full Evidence copy.
    for record in receipt["writes"]:
        record.pop("data", None)
    _save(receipt_path, receipt)
    result["status"] = "complete"
    return result
