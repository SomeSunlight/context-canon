from __future__ import annotations

import re
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, content: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def replace_once(path: str, old: str, new: str) -> None:
    text = read(path)
    if text.count(old) != 1:
        raise RuntimeError(f"{path}: expected exactly one replacement target, found {text.count(old)}")
    write(path, text.replace(old, new, 1))


def sub_once(path: str, pattern: str, replacement: str) -> None:
    text = read(path)
    result, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
    if count != 1:
        raise RuntimeError(f"{path}: expected exactly one regex replacement, found {count}: {pattern}")
    write(path, result)


# Package/CLI version and YAML dependency.
replace_once("pyproject.toml", 'version = "0.5.0"', 'version = "0.6.0"')
replace_once("pyproject.toml", "dependencies = []", 'dependencies = ["PyYAML>=6.0"]')

write(
    "src/contextcanon/version.py",
    '''from __future__ import annotations\n\n__version__ = "0.6.0"\n''',
)

write(
    "src/contextcanon/config.py",
    r'''from __future__ import annotations

import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse

import yaml

from .parser import ContextCanonError, find_repo_root


CONFIG_FILENAME = "contextcanon.yaml"
CONFIG_SCHEMA = "contextcanon/config/v1"


@dataclass(frozen=True)
class RepositoryConfig:
    key: str
    kind: str
    location: str
    ref: str | None = None

    def resolve_local(self, project_root: Path) -> Path:
        if self.kind != "local":
            raise ContextCanonError(f"Repository {self.key} is not local")
        path = Path(self.location).expanduser()
        if not path.is_absolute():
            path = project_root / path
        return path.resolve()


@dataclass(frozen=True)
class SourceConfig:
    source_id: str
    repository: str
    node_path: str


@dataclass(frozen=True)
class ProjectConfig:
    repositories: dict[str, RepositoryConfig]
    sources: dict[str, SourceConfig]


def config_path(project_root: Path) -> Path:
    return project_root.resolve() / CONFIG_FILENAME


def _node_path(value: object, label: str) -> str:
    text = str(value).strip()
    if not text or "\\" in text:
        raise ContextCanonError(f"{label}: invalid Source node path")
    path = PurePosixPath(text)
    if path.is_absolute() or ".." in path.parts:
        raise ContextCanonError(f"{label}: Source node path must be repository-relative")
    return path.as_posix()


def load_project_config(project_root: Path) -> ProjectConfig:
    root = project_root.resolve()
    path = config_path(root)
    if not path.is_file():
        return ProjectConfig({}, {})
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        raise ContextCanonError(f"Invalid {CONFIG_FILENAME}: {exc}") from exc
    if not isinstance(raw, dict) or raw.get("schema") != CONFIG_SCHEMA:
        raise ContextCanonError(f"{path}: expected schema {CONFIG_SCHEMA}")
    unknown = set(raw) - {"schema", "repositories", "sources"}
    if unknown:
        raise ContextCanonError(f"{path}: unsupported top-level keys: {', '.join(sorted(unknown))}")

    repositories_raw = raw.get("repositories", {})
    sources_raw = raw.get("sources", {})
    if not isinstance(repositories_raw, dict) or not isinstance(sources_raw, dict):
        raise ContextCanonError(f"{path}: repositories and sources must be YAML mappings")

    repositories: dict[str, RepositoryConfig] = {}
    for key, value in repositories_raw.items():
        if not isinstance(key, str) or not key.strip() or not isinstance(value, dict):
            raise ContextCanonError(f"{path}: invalid repository entry")
        kind = str(value.get("kind", "")).strip()
        location = str(value.get("location", "")).strip()
        ref = value.get("ref")
        if kind not in {"git", "local"}:
            raise ContextCanonError(f"{path}: repository {key} kind must be git or local")
        if not location or "\n" in location or "\r" in location:
            raise ContextCanonError(f"{path}: repository {key} location must be non-empty single-line text")
        if ref is not None:
            ref = str(ref).strip()
            if not ref or "\n" in ref or "\r" in ref:
                raise ContextCanonError(f"{path}: repository {key} ref must be non-empty single-line text")
        if kind == "local" and ref is not None:
            raise ContextCanonError(f"{path}: local repository {key} must not declare ref")
        repositories[key] = RepositoryConfig(key, kind, location, ref)

    sources: dict[str, SourceConfig] = {}
    for source_id, value in sources_raw.items():
        if not isinstance(source_id, str) or not source_id.strip() or not isinstance(value, dict):
            raise ContextCanonError(f"{path}: invalid Source entry")
        repository = str(value.get("repository", "")).strip()
        if repository not in repositories:
            raise ContextCanonError(f"{path}: Source {source_id} references unknown repository {repository!r}")
        node_path = _node_path(value.get("path", ""), f"{path}: Source {source_id}")
        sources[source_id] = SourceConfig(source_id, repository, node_path)
    return ProjectConfig(repositories, sources)


def _data(config: ProjectConfig) -> dict[str, object]:
    repositories: dict[str, object] = {}
    for key in sorted(config.repositories):
        item = config.repositories[key]
        value: dict[str, object] = {"kind": item.kind, "location": item.location}
        if item.ref is not None:
            value["ref"] = item.ref
        repositories[key] = value
    sources: dict[str, object] = {}
    for source_id in sorted(config.sources):
        item = config.sources[source_id]
        sources[source_id] = {"repository": item.repository, "path": item.node_path}
    return {"schema": CONFIG_SCHEMA, "repositories": repositories, "sources": sources}


def write_project_config(project_root: Path, config: ProjectConfig) -> Path:
    root = project_root.resolve()
    path = config_path(root)
    encoded = yaml.safe_dump(_data(config), sort_keys=False, allow_unicode=True, width=1000)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
    return path


def configured_source(project_root: Path, source_id: str) -> tuple[SourceConfig, RepositoryConfig] | None:
    config = load_project_config(project_root)
    source = config.sources.get(source_id)
    if source is None:
        return None
    return source, config.repositories[source.repository]


def _slug(location: str) -> str:
    parsed = urlparse(location)
    candidate = Path(parsed.path or location).name
    if candidate.endswith(".git"):
        candidate = candidate[:-4]
    candidate = re.sub(r"[^A-Za-z0-9._-]+", "-", candidate).strip("-._") or "repository"
    return candidate.lower()


def _repository_key(config: ProjectConfig, kind: str, location: str) -> str:
    for key, item in config.repositories.items():
        if item.kind == kind and item.location == location:
            return key
    base = _slug(location)
    key = base
    counter = 2
    while key in config.repositories:
        key = f"{base}-{counter}"
        counter += 1
    return key


def upsert_git_source(project_root: Path, source_id: str, location: str, ref: str | None, node_path: str) -> Path:
    root = project_root.resolve()
    config = load_project_config(root)
    key = _repository_key(config, "git", location)
    repositories = dict(config.repositories)
    repositories[key] = RepositoryConfig(key, "git", location, ref)
    sources = dict(config.sources)
    sources[source_id] = SourceConfig(source_id, key, _node_path(node_path, f"Source {source_id}"))
    return write_project_config(root, ProjectConfig(repositories, sources))


def _relative_location(project_root: Path, repository_root: Path) -> str:
    try:
        return Path(os.path.relpath(repository_root, project_root)).as_posix()
    except ValueError:
        return str(repository_root)


def upsert_local_mapping(
    project_root: Path,
    source_id: str,
    repository_root: Path,
    node_path: str,
) -> Path:
    root = project_root.resolve()
    repository_root = repository_root.resolve()
    location = _relative_location(root, repository_root)
    config = load_project_config(root)
    key = _repository_key(config, "local", location)
    repositories = dict(config.repositories)
    repositories[key] = RepositoryConfig(key, "local", location, None)
    sources = dict(config.sources)
    sources[source_id] = SourceConfig(source_id, key, _node_path(node_path, f"Source {source_id}"))
    return write_project_config(root, ProjectConfig(repositories, sources))


def upsert_local_source(project_root: Path, source_id: str, package_root: Path) -> Path:
    package = package_root.resolve()
    repository = find_repo_root(package)
    try:
        node_path = package.relative_to(repository).as_posix() or "."
    except ValueError:
        repository = package
        node_path = "."
    return upsert_local_mapping(project_root, source_id, repository, node_path)
''',
)

# Central discovery and local/offline candidate support.
replace_once(
    "src/contextcanon/git_transport.py",
    "from .model import CompiledPackage, SourceRef\n",
    "from .config import configured_source\nfrom .model import CompiledPackage, SourceRef\n",
)
replace_once(
    "src/contextcanon/git_transport.py",
    'CANDIDATE_PROVENANCE_SCHEMA = "contextcanon/git-candidate-provenance/v0"\n',
    'CANDIDATE_PROVENANCE_SCHEMA = "contextcanon/git-candidate-provenance/v0"\nCONFIGURED_CANDIDATE_PROVENANCE_SCHEMA = "contextcanon/source-candidate-provenance/v1"\n',
)

sub_once(
    "src/contextcanon/git_transport.py",
    r"def fetch_git_candidate\(.*?(?=\ndef _find_source)",
    r'''def fetch_git_candidate(
    node_root: Path,
    source_id: str,
    discovery_ref: str | None = None,
) -> tuple[CompiledPackage, Path]:
    """Fetch one immutable Source candidate through central or legacy transport metadata."""

    node_root = node_root.resolve()
    parsed = parse_node(node_root, find_repo_root(node_root))
    source = _find_source(parsed.sources, source_id, parsed.metadata.name)
    configured = configured_source(parsed.repo_root, source_id)

    if configured is not None:
        source_config, repository = configured
        if repository.kind == "local":
            if discovery_ref is not None:
                raise ContextCanonError("--ref cannot be used with a local ContextCanon repository")
            repository_root = repository.resolve_local(parsed.repo_root)
            candidate_root = _configured_candidate_node_root(repository_root, source_config.node_path, source.name)
            candidate = load_package(candidate_root)
            if candidate.metadata.id != source.id:
                raise ContextCanonError(
                    f"Configured Source {source.name} expects Node ID {source.id}, got {candidate.metadata.id}"
                )
            persisted = _persist_candidate(node_root, candidate_root, candidate)
            _persist_configured_candidate_provenance(
                node_root,
                source,
                candidate,
                kind="local",
                location=repository.location,
                discovery_ref="",
                candidate_ref="",
                node_path=source_config.node_path,
            )
            return candidate, persisted

        ref = discovery_ref if discovery_ref is not None else repository.ref
        checkout_parent = Path(tempfile.mkdtemp(prefix="contextcanon-git-"))
        checkout = checkout_parent / "repository"
        try:
            candidate_ref = _clone_location(repository.location, checkout, ref)
            candidate_root = _configured_candidate_node_root(checkout, source_config.node_path, source.name)
            candidate = load_package(candidate_root)
            if candidate.metadata.id != source.id:
                raise ContextCanonError(
                    f"Configured Source {source.name} expects Node ID {source.id}, got {candidate.metadata.id}"
                )
            persisted = _persist_candidate(node_root, candidate_root, candidate)
            _persist_configured_candidate_provenance(
                node_root,
                source,
                candidate,
                kind="git",
                location=repository.location,
                discovery_ref=ref or "",
                candidate_ref=candidate_ref,
                node_path=source_config.node_path,
            )
            return candidate, persisted
        finally:
            shutil.rmtree(checkout_parent, ignore_errors=True)

    _validate_git_source(source, node_root)
    checkout_parent = Path(tempfile.mkdtemp(prefix="contextcanon-git-"))
    checkout = checkout_parent / "repository"
    try:
        if discovery_ref is None:
            candidate_ref = _clone(source, checkout)
        else:
            candidate_ref = _clone_location(source.locator, checkout, discovery_ref)
        candidate_root = _candidate_node_root(checkout, source)
        candidate = load_package(candidate_root)
        if candidate.metadata.id != source.id:
            raise ContextCanonError(
                f"Git Source {source.name} expects Node ID {source.id}, got {candidate.metadata.id} "
                f"at node-path {source.node_path}"
            )
        persisted = _persist_candidate(node_root, candidate_root, candidate)
        if discovery_ref is None:
            _persist_candidate_provenance(node_root, source, candidate, candidate_ref)
        else:
            _persist_configured_candidate_provenance(
                node_root,
                source,
                candidate,
                kind="git",
                location=source.locator,
                discovery_ref=discovery_ref,
                candidate_ref=candidate_ref,
                node_path=source.node_path or ".",
            )
        return candidate, persisted
    finally:
        shutil.rmtree(checkout_parent, ignore_errors=True)
''',
)

sub_once(
    "src/contextcanon/git_transport.py",
    r"def _clone\(source: SourceRef, destination: Path\) -> str:.*?(?=\ndef _candidate_node_root)",
    r'''def _clone(source: SourceRef, destination: Path) -> str:
    """Clone legacy discovery semantics while keeping exact accepted SHAs non-live."""
    ref = source.transport_ref
    if ref and _GIT_SHA_RE.fullmatch(ref):
        ref = None
    return _clone_location(source.locator, destination, ref)


def _clone_location(locator: str, destination: Path, ref: str | None) -> str:
    if ref and _GIT_SHA_RE.fullmatch(ref):
        command = ["git", "clone", "--quiet", "--no-checkout", locator, str(destination)]
    else:
        command = ["git", "clone", "--quiet", "--depth", "1", "--single-branch"]
        if ref:
            command.extend(["--branch", ref])
        command.extend([locator, str(destination)])
    try:
        completed = subprocess.run(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise ContextCanonError("Git Source transport requires the 'git' executable on PATH") from exc
    except OSError as exc:
        raise ContextCanonError(f"Could not start Git Source transport: {exc}") from exc
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or f"exit code {completed.returncode}"
        raise ContextCanonError(f"Git Source fetch failed for discovery ref {ref or 'remote default branch'}: {detail}")

    if ref and _GIT_SHA_RE.fullmatch(ref):
        fetch = subprocess.run(
            ["git", "-C", str(destination), "fetch", "--quiet", "--depth", "1", "origin", ref],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        if fetch.returncode != 0:
            detail = fetch.stderr.strip() or fetch.stdout.strip() or f"exit code {fetch.returncode}"
            raise ContextCanonError(f"Git Source fetch failed for exact ref {ref}: {detail}")
        checkout = subprocess.run(
            ["git", "-C", str(destination), "checkout", "--quiet", "FETCH_HEAD"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        if checkout.returncode != 0:
            detail = checkout.stderr.strip() or checkout.stdout.strip() or f"exit code {checkout.returncode}"
            raise ContextCanonError(f"Could not checkout exact Git Source ref {ref}: {detail}")

    exact = subprocess.run(
        ["git", "-C", str(destination), "rev-parse", "HEAD"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    candidate_ref = exact.stdout.strip()
    if exact.returncode != 0 or not _GIT_SHA_RE.fullmatch(candidate_ref):
        detail = exact.stderr.strip() or exact.stdout.strip() or f"exit code {exact.returncode}"
        raise ContextCanonError(f"Could not resolve exact Git Source candidate commit: {detail}")
    return candidate_ref


def _configured_candidate_node_root(repository: Path, node_path: str, source_name: str) -> Path:
    root = repository.resolve()
    path = PurePosixPath(node_path)
    candidate = root.joinpath(*path.parts).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ContextCanonError(f"Configured Source {source_name} path escapes repository: {node_path}") from exc
    if not candidate.is_dir():
        raise ContextCanonError(f"Configured Source {source_name} path does not exist: {candidate}")
    return candidate
''',
)

sub_once(
    "src/contextcanon/git_transport.py",
    r"def load_candidate_provenance\(.*?(?=\ndef _persist_candidate_provenance)",
    r'''def load_candidate_provenance(node_root: Path, package_digest: str) -> dict[str, str] | None:
    path = candidate_provenance_path(node_root, package_digest)
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContextCanonError(f"Invalid Source candidate provenance {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ContextCanonError(f"Invalid Source candidate provenance schema in {path}")
    schema = raw.get("schema")
    if schema == CANDIDATE_PROVENANCE_SCHEMA:
        required = {"schema", "source_id", "locator", "accepted_ref", "candidate_ref", "node_path", "package_digest"}
        if set(raw) != required:
            raise ContextCanonError(f"Invalid Git Source candidate provenance schema in {path}")
        values = {key: str(value) for key, value in raw.items()}
        if not _GIT_SHA_RE.fullmatch(values["candidate_ref"]):
            raise ContextCanonError(f"Invalid exact Git Source candidate commit in {path}")
    elif schema == CONFIGURED_CANDIDATE_PROVENANCE_SCHEMA:
        required = {"schema", "source_id", "kind", "location", "discovery_ref", "candidate_ref", "node_path", "package_digest"}
        if set(raw) != required or raw.get("kind") not in {"git", "local"}:
            raise ContextCanonError(f"Invalid configured Source candidate provenance schema in {path}")
        values = {key: str(value) for key, value in raw.items()}
        if values["kind"] == "git" and not _GIT_SHA_RE.fullmatch(values["candidate_ref"]):
            raise ContextCanonError(f"Invalid exact configured Git Source candidate commit in {path}")
        if values["kind"] == "local" and values["candidate_ref"]:
            raise ContextCanonError(f"Local Source candidate provenance must not invent a Git commit in {path}")
    else:
        raise ContextCanonError(f"Invalid Source candidate provenance schema in {path}")
    if values["package_digest"] != package_digest:
        raise ContextCanonError(f"Source candidate provenance digest mismatch in {path}")
    return values


def _persist_configured_candidate_provenance(
    node_root: Path,
    source: SourceRef,
    candidate: CompiledPackage,
    *,
    kind: str,
    location: str,
    discovery_ref: str,
    candidate_ref: str,
    node_path: str,
) -> Path:
    path = candidate_provenance_path(node_root, candidate.package_digest)
    payload = {
        "schema": CONFIGURED_CANDIDATE_PROVENANCE_SCHEMA,
        "source_id": source.id,
        "kind": kind,
        "location": location,
        "discovery_ref": discovery_ref,
        "candidate_ref": candidate_ref,
        "node_path": node_path,
        "package_digest": candidate.package_digest,
    }
    encoded = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(encoded, encoding="utf-8")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
    return path
''',
)

# Candidate provenance v1 is bound to central configuration rather than stale inline transport hints.
sub_once(
    "src/contextcanon/sources.py",
    r"def _validated_candidate_provenance\(.*?(?=\ndef _review_path)",
    r'''def _validated_candidate_provenance(
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
''',
)
replace_once(
    "src/contextcanon/sources.py",
    '    accepted_ref = None if transport_candidate is None else transport_candidate["candidate_ref"]\n',
    '    accepted_ref = None if transport_candidate is None else (transport_candidate.get("candidate_ref") or None)\n',
)

# Make adoption local/offline-first and put discovery configuration in contextcanon.yaml.
replace_once(
    "src/contextcanon/sources.py",
    "from .git_transport import load_candidate_provenance, resolve_git_package_provenance\n",
    "from .config import CONFIG_FILENAME, config_path, upsert_local_source\nfrom .git_transport import load_candidate_provenance\n",
)
sub_once(
    "src/contextcanon/sources.py",
    r"def adopt_source_package\(.*?(?=\ndef _render_adopted_source)",
    r'''def adopt_source_package(node_root: Path, package_root: Path) -> tuple[CompiledPackage, bool]:
    """Explicitly adopt one exact published local package and register local discovery centrally."""

    node_root = node_root.resolve()
    package_root = package_root.resolve()
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
    upsert_local_source(repo_root, candidate.metadata.id, package_root)
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
''',
)
sub_once(
    "src/contextcanon/sources.py",
    r"def _render_adopted_source\(.*?(?=\ndef _insert_source_entry)",
    r'''def _render_adopted_source(node_root: Path, repo_root: Path, candidate: CompiledPackage) -> str:
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
''',
)

# CLI: version, readable Source selectors/list/update, explicit ref, config visibility and top-down propagation.
replace_once(
    "src/contextcanon/cli.py",
    "from .authoring import add_rule, add_topic\n",
    "from .authoring import add_rule, add_topic\nfrom .config import CONFIG_FILENAME, configured_source, config_path, load_project_config\nfrom .version import __version__\n",
)
replace_once(
    "src/contextcanon/cli.py",
    "from .parser import ContextCanonError, find_repo_root\n",
    "from .parser import ContextCanonError, find_repo_root, parse_node\n",
)

insert_marker = '''def _add_structure_inputs(parser: argparse.ArgumentParser) -> None:\n    parser.add_argument(\n        "--structure-proposal",\n        metavar="PATH",\n        help="validated structure proposal (default: <workspace>/STEP-02b-structure-proposal.json)",\n    )\n    parser.add_argument(\n        "--structure",\n        metavar="PATH",\n        help="human-edited structure Markdown (default: <workspace>/STEP-03-structure.md)",\n    )\n\n\n'''
helpers = r'''def _resolve_source_id(node_root: Path, selector: str) -> str:
    parsed = parse_node(node_root, find_repo_root(node_root))
    for source in parsed.sources:
        if source.id == selector:
            return source.id
    matches = [source for source in parsed.sources if source.name.casefold() == selector.casefold()]
    if len(matches) == 1:
        return matches[0].id
    choices = ", ".join(f"{source.name} ({source.id})" for source in parsed.sources) or "none"
    if len(matches) > 1:
        raise ContextCanonError(f"Source name {selector!r} is ambiguous; available Sources: {choices}")
    raise ContextCanonError(f"No Source named or identified by {selector!r}; available Sources: {choices}")


def _confirm(prompt: str) -> bool:
    try:
        answer = input(f"{prompt} [y/N] ").strip().casefold()
    except EOFError:
        return False
    return answer in {"y", "yes"}


def _parent_edges(repo_root: Path):
    compiler = Compiler(repo_root)
    roots = [root.resolve() for root in discover_nodes(repo_root)]
    parsed = {root: parse_node(root, repo_root) for root in roots}
    parent_roots: dict[Path, list[tuple[object, Path]]] = {}
    for child_root, node in parsed.items():
        for parent in node.parents:
            parent_root = compiler._resolve_source_root(child_root, parent.locator).resolve()
            if parent_root not in parsed:
                raise ContextCanonError(
                    f"{node.metadata.name}: Parent {parent.name} is outside the repository-wide propagation set; update that edge explicitly"
                )
            parent_roots.setdefault(child_root, []).append((parent, parent_root))

    depths: dict[Path, int] = {}
    active: set[Path] = set()

    def depth(root: Path) -> int:
        if root in depths:
            return depths[root]
        if root in active:
            raise ContextCanonError("Semantic Parent cycle prevents top-down propagation")
        active.add(root)
        parents = parent_roots.get(root, [])
        value = 0 if not parents else 1 + max(depth(parent_root) for _, parent_root in parents)
        active.remove(root)
        depths[root] = value
        return value

    edges = [
        (child_root, parent, parent_root)
        for child_root, items in parent_roots.items()
        for parent, parent_root in items
    ]
    return sorted(
        edges,
        key=lambda item: (
            depth(item[0]),
            item[0].relative_to(repo_root).as_posix(),
            item[1].id,
        ),
    )


'''
replace_once("src/contextcanon/cli.py", insert_marker, insert_marker + helpers)
replace_once(
    "src/contextcanon/cli.py",
    '    parser = argparse.ArgumentParser(prog="contextcanon", description="Deterministic ContextCanon compiler")\n    sub = parser.add_subparsers(dest="command", required=True)\n',
    '    parser = argparse.ArgumentParser(prog="contextcanon", description="Deterministic ContextCanon compiler")\n    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")\n    sub = parser.add_subparsers(dest="command", required=True)\n',
)
replace_once(
    "src/contextcanon/cli.py",
    '''    parent_accept = parent_sub.add_parser("accept", help="accept exactly the reviewed snapshot for one Parent")\n    parent_accept.add_argument("parent_id", nargs="?", help="Parent Node ID; optional when the Child has exactly one Parent")\n    parent_accept.add_argument("--node", default=".", help="child Context Node root (default: current directory)")\n\n    source_parser = sub.add_parser("source", help="fetch, review, and explicitly accept immutable Source packages")\n''',
    '''    parent_accept = parent_sub.add_parser("accept", help="accept exactly the reviewed snapshot for one Parent")\n    parent_accept.add_argument("parent_id", nargs="?", help="Parent Node ID; optional when the Child has exactly one Parent")\n    parent_accept.add_argument("--node", default=".", help="child Context Node root (default: current directory)")\n    parent_propagate = parent_sub.add_parser("propagate", help="review and accept stale Parent edges top-down across a repository")\n    parent_propagate.add_argument("path", nargs="?", default=".", help="repository root or path inside it (default: current directory)")\n    parent_propagate.add_argument("--yes", action="store_true", help="accept each displayed Parent diff without interactive confirmation")\n\n    source_parser = sub.add_parser("source", help="discover, review, and explicitly accept immutable Source packages")\n''',
)
replace_once(
    "src/contextcanon/cli.py",
    '''    source_adopt = source_sub.add_parser("adopt", help="explicitly adopt one exact published Git package as a new Source")\n    source_adopt.add_argument("package", help="local root of the exact published Source package Node")\n    source_adopt.add_argument("--node", default=".", help="consumer Context Node root (default: current directory)")\n    source_fetch = source_sub.add_parser("fetch", help="fetch a Source candidate through its declared transport")\n    source_fetch.add_argument("source_id", help="stable Node ID of the Source in CONTEXT.src.md")\n    source_fetch.add_argument("--node", default=".", help="consumer Context Node root (default: current directory)")\n    source_review = source_sub.add_parser("review", help="diff and structurally validate a Source candidate")\n    source_review.add_argument("source_id", help="stable Node ID of the Source in CONTEXT.src.md")\n    source_review.add_argument("candidate", help="local root of the candidate immutable package")\n    source_review.add_argument("--node", default=".", help="consumer Context Node root (default: current directory)")\n    source_accept = source_sub.add_parser("accept", help="accept exactly a previously reviewed Source candidate")\n    source_accept.add_argument("source_id", help="stable Node ID of the Source in CONTEXT.src.md")\n    source_accept.add_argument("candidate", help="local root of the reviewed immutable package")\n    source_accept.add_argument("--node", default=".", help="consumer Context Node root (default: current directory)")\n\n    args = parser.parse_args(argv)\n''',
    '''    source_list = source_sub.add_parser("list", help="list Sources by human name, stable ID and discovery configuration")\n    source_list.add_argument("--node", default=".", help="consumer Context Node root (default: current directory)")\n    source_adopt = source_sub.add_parser("adopt", help="adopt one exact local package and register its local repository centrally")\n    source_adopt.add_argument("package", help="local root of the exact published Source package Node")\n    source_adopt.add_argument("--node", default=".", help="consumer Context Node root (default: current directory)")\n    source_fetch = source_sub.add_parser("fetch", help="fetch a Source candidate from central configuration or legacy inline transport")\n    source_fetch.add_argument("source", help="Source name or stable Node ID")\n    source_fetch.add_argument("--node", default=".", help="consumer Context Node root (default: current directory)")\n    source_fetch.add_argument("--ref", help="one-off Git discovery ref/branch/commit; does not rewrite accepted or central configuration")\n    source_update = source_sub.add_parser("update", help="fetch, review and optionally accept one Source in a single human-scale flow")\n    source_update.add_argument("source", help="Source name or stable Node ID")\n    source_update.add_argument("--node", default=".", help="consumer Context Node root (default: current directory)")\n    source_update.add_argument("--ref", help="one-off Git discovery ref/branch/commit")\n    source_update.add_argument("--yes", action="store_true", help="accept the displayed Source diff without interactive confirmation")\n    source_review = source_sub.add_parser("review", help="diff and structurally validate a Source candidate")\n    source_review.add_argument("source", help="Source name or stable Node ID")\n    source_review.add_argument("candidate", help="local root of the candidate immutable package")\n    source_review.add_argument("--node", default=".", help="consumer Context Node root (default: current directory)")\n    source_accept = source_sub.add_parser("accept", help="accept exactly a previously reviewed Source candidate")\n    source_accept.add_argument("source", help="Source name or stable Node ID")\n    source_accept.add_argument("candidate", help="local root of the reviewed immutable package")\n    source_accept.add_argument("--node", default=".", help="consumer Context Node root (default: current directory)")\n\n    config_parser = sub.add_parser("config", help=f"inspect the central {CONFIG_FILENAME} operational configuration")\n    config_sub = config_parser.add_subparsers(dest="config_command", required=True)\n    config_show = config_sub.add_parser("show", help="validate and print the central project configuration")\n    config_show.add_argument("path", nargs="?", default=".", help="repository root or path inside it")\n\n    args = parser.parse_args(argv)\n''',
)

# Dispatch config before author/parent/source.
replace_once(
    "src/contextcanon/cli.py",
    '''        if args.command == "author":\n''',
    '''        if args.command == "config":\n            root = find_repo_root(_node_root(Path(args.path)))\n            load_project_config(root)\n            path = config_path(root)\n            if not path.is_file():\n                print(f"No {CONFIG_FILENAME} exists at {path}")\n            else:\n                print(path.read_text(encoding="utf-8"), end="")\n            return 0\n\n        if args.command == "author":\n''',
)

sub_once(
    "src/contextcanon/cli.py",
    r'''        if args\.command == "parent":.*?(?=\n        if args\.command == "source":)''',
    r'''        if args.command == "parent":
            if args.parent_command == "propagate":
                repo_root = find_repo_root(Path(args.path).resolve())
                edges = _parent_edges(repo_root)
                if not edges:
                    print("No semantic Parent edges found.")
                    return 0
                accepted_count = 0
                for child_root, parent, _ in edges:
                    child = parse_node(child_root, repo_root)
                    child_label = child_root.relative_to(repo_root).as_posix() or "."
                    print(f"\n=== {child.metadata.name} ({child_label}) ← {parent.name} ===")
                    result, receipt = review_parent_candidate(child_root, parent.id)
                    print(render_diff(result), end="")
                    if not args.yes and not _confirm(f"Accept this reviewed Parent update for {child.metadata.name}?"):
                        print("Stopped before acceptance; the reviewed receipt remains available for explicit acceptance.")
                        return 0
                    accepted = accept_parent_candidate(child_root, parent.id)
                    accepted_count += 1
                    print(f"accepted Parent {accepted.metadata.name} {accepted.metadata.version} ({accepted.package_digest})")
                print(f"Propagated {accepted_count} Parent edge(s) top-down.")
                print(f"Next: contextcanon build --all {repo_root}")
                print(f"Then: contextcanon check --all {repo_root}")
                return 0

            node_root = _node_root(Path(args.node))
            if args.parent_command == "review":
                result, receipt = review_parent_candidate(node_root, args.parent_id)
                print(render_diff(result), end="")
                try:
                    label = receipt.relative_to(node_root).as_posix()
                except ValueError:
                    label = str(receipt)
                print(f"Parent review receipt: {label}")
                print("Accepted Parent pin is unchanged until 'contextcanon parent accept'.")
                return 0
            accepted = accept_parent_candidate(node_root, args.parent_id)
            print(f"accepted Parent {accepted.metadata.name} {accepted.metadata.version} ({accepted.package_digest})")
            print(f"Next: contextcanon build {node_root}")
            print(f"Then: contextcanon check {node_root}")
            return 0
''',
)

sub_once(
    "src/contextcanon/cli.py",
    r'''        if args\.command == "source":.*?(?=\n        repo_root, node_roots = _targets)''',
    r'''        if args.command == "source":
            node_root = _node_root(Path(args.node))
            repo_root = find_repo_root(node_root)
            if args.source_command == "list":
                parsed = parse_node(node_root, repo_root)
                if not parsed.sources:
                    print(f"{parsed.metadata.name}: no Sources")
                    return 0
                for source in parsed.sources:
                    configured = configured_source(repo_root, source.id)
                    if configured is None:
                        discovery = (
                            f"legacy git {source.locator} ({source.transport_ref or 'default'})"
                            if source.transport == "git"
                            else "no central discovery configuration"
                        )
                    else:
                        source_config, repository = configured
                        if repository.kind == "git":
                            discovery = f"git {repository.location} @ {repository.ref or 'default'} :: {source_config.node_path}"
                        else:
                            discovery = f"local {repository.location} :: {source_config.node_path}"
                    print(f"{source.name} | {source.id} | accepted {source.version} | {discovery}")
                return 0

            if args.source_command == "adopt":
                adopted, changed = adopt_source_package(node_root, Path(args.package))
                verb = "adopted" if changed else "already adopted"
                print(f"{verb} Source {adopted.metadata.name} {adopted.metadata.version} ({adopted.package_digest})")
                print(f"Discovery configuration: {config_path(repo_root)}")
                print(f"Next: contextcanon build {node_root}")
                print(f"Then: contextcanon check {node_root}")
                return 0

            source_id = _resolve_source_id(node_root, args.source)
            if args.source_command in {"fetch", "update"}:
                candidate, location = fetch_git_candidate(node_root, source_id, discovery_ref=args.ref)
                try:
                    label = location.relative_to(node_root).as_posix()
                except ValueError:
                    label = str(location)
                print(f"fetched candidate {candidate.metadata.name} {candidate.metadata.version} ({candidate.package_digest})")
                provenance = load_candidate_provenance(node_root, candidate.package_digest)
                if provenance is not None and provenance.get("candidate_ref"):
                    print(f"Candidate Git commit: {provenance['candidate_ref']}")
                elif provenance is not None and provenance.get("kind") == "local":
                    print(f"Candidate local repository: {provenance['location']}")
                print(f"Candidate package: {label}")
                parsed = parse_node(node_root, repo_root)
                current = next(source for source in parsed.sources if source.id == source_id)
                if current.package_digest == candidate.package_digest:
                    print("Accepted Source is already this exact package.")
                    return 0
                if args.source_command == "fetch":
                    print("Accepted Source pin is unchanged until explicit review and accept.")
                    return 0
                result, receipt = review_source_candidate(node_root, source_id, location)
                print(render_diff(result), end="")
                if not args.yes and not _confirm(f"Accept this reviewed Source update for {current.name}?"):
                    print(f"Stopped before acceptance. Review receipt: {receipt}")
                    return 0
                accepted = accept_source_candidate(node_root, source_id, location)
                print(f"accepted Source {accepted.metadata.name} {accepted.metadata.version} ({accepted.package_digest})")
                print("If this Node has descendants, run 'contextcanon parent propagate --all' from the repository root.")
                return 0

            candidate = Path(args.candidate).resolve()
            if args.source_command == "review":
                result, receipt = review_source_candidate(node_root, source_id, candidate)
                print(render_diff(result), end="")
                try:
                    label = receipt.relative_to(node_root).as_posix()
                except ValueError:
                    label = str(receipt)
                print(f"Review receipt: {label}")
                return 0

            accepted = accept_source_candidate(node_root, source_id, candidate)
            print(f"accepted {accepted.metadata.name} {accepted.metadata.version} ({accepted.package_digest})")
            return 0
''',
)

# Onboarding publishes central discovery config and no longer hides transport parameters in each Source comment.
replace_once(
    "src/contextcanon/onboarding_placement_publish.py",
    "from .compiler import Compiler\n",
    "from .compiler import Compiler\nfrom .config import CONFIG_FILENAME, config_path, upsert_git_source, upsert_local_mapping\n",
)
replace_once(
    "src/contextcanon/onboarding_placement_publish.py",
    "    package_root: Path\n",
    "    package_root: Path\n    kind: str = \"git\"\n    discovery_ref: str = \"\"\n",
)
# Replace provenance resolver with Git-or-local behavior.
sub_once(
    "src/contextcanon/onboarding_placement_publish.py",
    r"def _git_provenance\(.*?(?=\ndef _source_provenance)",
    r'''def _try_git(root: Path, *args: str) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), *args],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
    except (FileNotFoundError, OSError):
        return None
    return completed.stdout.strip() if completed.returncode == 0 else None


def _git_provenance(source: PlacementReviewSource, package_root: Path) -> SourceGitProvenance:
    repository_text = _try_git(package_root, "rev-parse", "--show-toplevel")
    if repository_text is None:
        return SourceGitProvenance(
            source_node_id=source.source_node_id,
            source_name=source.source_name,
            source_version=source.source_version,
            source_package_digest=source.source_package_digest,
            origin=source.origin,
            locator=str(package_root.resolve()),
            ref="",
            node_path=".",
            package_root=package_root,
            kind="local",
            discovery_ref="",
        )

    repository = Path(repository_text).resolve()
    try:
        node_path = package_root.relative_to(repository).as_posix() or "."
    except ValueError as exc:
        raise _error(f"catalog package root is not inside its repository: {package_root}") from exc
    status = _try_git(repository, "status", "--porcelain", "--untracked-files=all", "--", node_path)
    if status:
        raise _error(
            f"accepted Source {source.source_name} has uncommitted package-path changes; exact package provenance would be ambiguous"
        )
    exact = _try_git(repository, "rev-parse", "HEAD")
    origin = _try_git(repository, "remote", "get-url", "origin")
    branch = _try_git(repository, "branch", "--show-current") or ""
    if origin and exact and re.fullmatch(r"[0-9a-f]{40}", exact):
        if '"' in origin or '"' in node_path:
            raise _error("Source Git provenance contains unsupported quote characters")
        return SourceGitProvenance(
            source_node_id=source.source_node_id,
            source_name=source.source_name,
            source_version=source.source_version,
            source_package_digest=source.source_package_digest,
            origin=source.origin,
            locator=origin,
            ref=exact,
            node_path=node_path,
            package_root=package_root,
            kind="git",
            discovery_ref=branch or exact,
        )
    return SourceGitProvenance(
        source_node_id=source.source_node_id,
        source_name=source.source_name,
        source_version=source.source_version,
        source_package_digest=source.source_package_digest,
        origin=source.origin,
        locator=str(repository),
        ref=exact or "",
        node_path=node_path,
        package_root=package_root,
        kind="local",
        discovery_ref="",
    )
''',
)

# Central config link in newly published Source declarations.
sub_once(
    "src/contextcanon/onboarding_placement_publish.py",
    r"def _render_sources\(.*?(?=\ndef _managed_ids_outside_blocks)",
    r'''def _render_sources(
    sources: list[PlacementReviewSource],
    provenance_by_id: dict[str, SourceGitProvenance],
    config_locator: str,
) -> str:
    lines: list[str] = []
    for source in sources:
        name = _safe_line(source.source_name, f"Source {source.review_id} name")
        if any(char in name for char in "]\n\r"):
            raise _error(f"Source {source.review_id} name cannot be represented safely")
        lines.append(f"- [{name}]({config_locator}) — `{source.source_version}`")
        if source.relationship_why:
            lines.append(f"  Why: {_safe_line(source.relationship_why, f'Source {source.review_id} relationship Why')}")
        lines.extend(
            [
                (
                    f'  <!-- ctx:source id="{source.source_node_id}" version="{source.source_version}" '
                    f'normalized-digest="{source.source_normalized_digest}" '
                    f'package-digest="{source.source_package_digest}" -->'
                ),
                "",
            ]
        )
    return "\n".join(lines).rstrip()
''',
)
replace_once(
    "src/contextcanon/onboarding_placement_publish.py",
    '    text = _replace_managed_section(text, "Sources", "sources", _render_sources(sources, provenance_by_id))\n',
    '    config_locator = Path(os.path.relpath(project_root / CONFIG_FILENAME, node_root)).as_posix()\n    text = _replace_managed_section(text, "Sources", "sources", _render_sources(sources, provenance_by_id, config_locator))\n',
)
replace_once(
    "src/contextcanon/onboarding_placement_publish.py",
    '                f"  - Git: `{source.locator}` @ `{source.ref}`",\n                f"  - node-path: `{source.node_path}`",\n',
    '                f"  - discovery: `{source.kind}` `{source.locator}`" + (f" @ `{source.discovery_ref}`" if source.discovery_ref else ""),\n                f"  - node-path: `{source.node_path}`",\n                f"  - central project configuration: `{CONFIG_FILENAME}`",\n',
)

# Publication transaction includes contextcanon.yaml and maps every accepted reusable Source once.
replace_once(
    "src/contextcanon/onboarding_placement_publish.py",
    '    acceptance_before = acceptance_path.read_bytes() if acceptance_path.is_file() else None\n    legacy_parent_upgrade = _legacy_parent_acceptance_upgrade(acceptance_before, preview)\n',
    '    acceptance_before = acceptance_path.read_bytes() if acceptance_path.is_file() else None\n    project_config_path = config_path(project)\n    project_config_before = project_config_path.read_bytes() if project_config_path.is_file() else None\n    legacy_parent_upgrade = _legacy_parent_acceptance_upgrade(acceptance_before, preview)\n',
)
replace_once(
    "src/contextcanon/onboarding_placement_publish.py",
    '        payload = _acceptance_payload(preview, review, node_digests)\n',
    '        for source in preview.sources:\n            if source.kind == "git":\n                upsert_git_source(project, source.source_node_id, source.locator, source.discovery_ref or None, source.node_path)\n            else:\n                repository_root = Path(source.locator).resolve()\n                upsert_local_mapping(project, source.source_node_id, repository_root, source.node_path)\n\n        payload = _acceptance_payload(preview, review, node_digests)\n',
)
replace_once(
    "src/contextcanon/onboarding_placement_publish.py",
    '        if acceptance_before is None:\n            acceptance_path.unlink(missing_ok=True)\n        else:\n            _atomic_write(acceptance_path, acceptance_before)\n        raise\n',
    '        if acceptance_before is None:\n            acceptance_path.unlink(missing_ok=True)\n        else:\n            _atomic_write(acceptance_path, acceptance_before)\n        if project_config_before is None:\n            project_config_path.unlink(missing_ok=True)\n        else:\n            _atomic_write(project_config_path, project_config_before)\n        raise\n',
)

# Acceptance payload keeps old Git traceability when available and adds generic discovery provenance.
replace_once(
    "src/contextcanon/onboarding_placement_publish.py",
    '        accepted_sources.append(\n            {\n                **source.to_dict(),\n                "git": provenance.to_dict(),\n            }\n        )\n',
    '        entry = {**source.to_dict(), "discovery": {**provenance.to_dict(), "kind": provenance.kind, "discovery_ref": provenance.discovery_ref}}\n        if provenance.kind == "git":\n            entry["git"] = provenance.to_dict()\n        accepted_sources.append(entry)\n',
)

# Documentation: central operational config, local/offline mode, explicit ref and human-scale propagation.
source_format = read("nodes/library/foundation/docs/source-format.md")
old_transport = '''### Git update transport\n\nA pinned Source may additionally describe how candidate updates are retrieved:\n'''
new_transport = '''### Central Source discovery configuration\n\nOperational Source discovery belongs in one repository-visible `contextcanon.yaml`, not duplicated across consuming Nodes. A pinned Source declaration keeps only accepted immutable identity (version plus both digests); its visible link may point to the central configuration. Existing inline `transport`/`ref`/`node-path` metadata remains readable as a compatibility fallback.\n\nThe v1 YAML configuration separates reusable Source identity from repository discovery:\n\n```yaml\nschema: contextcanon/config/v1\nrepositories:\n  context-canon:\n    kind: git\n    location: https://github.com/SomeSunlight/context-canon.git\n    ref: main\nsources:\n  c4c94726-3cc7-4df6-b779-72bbf9c06f40:\n    repository: context-canon\n    path: nodes/library/development-workflow\n```\n\nThe same Source can be made completely local/offline by changing the repository once:\n\n```yaml\nrepositories:\n  context-canon:\n    kind: local\n    location: ../context-canon\n```\n\nLocal paths may be relative to the consuming project root or absolute. They require no network access. Accepted package pins remain unchanged until explicit review/accept; changing discovery configuration never silently changes effective Context. The YAML file is deliberately the project-level operational configuration surface so later non-semantic ContextCanon settings can be added under a future schema version instead of inventing one file per setting.\n\n`contextcanon source list` shows human names, stable IDs and the resolved discovery configuration. `contextcanon source update "Development Workflow"` performs fetch + exact diff + explicit acceptance as one guided flow. `--ref <branch|tag|commit>` is a one-off Git candidate override and never rewrites the central configuration or accepted pin.\n\nAfter an ancestor Source is accepted, `contextcanon parent propagate --all` walks semantic Parent edges top-down, shows each exact diff, and asks before accepting that edge. `--yes` is available for an already-reviewed scripted run. This removes UUID/path archaeology without turning Parent updates into live inheritance.\n\n### Legacy inline Git update transport\n\nA pinned Source may additionally describe how candidate updates are retrieved when no central Source mapping exists:\n'''
if old_transport not in source_format:
    raise RuntimeError("source-format transport heading not found")
write("nodes/library/foundation/docs/source-format.md", source_format.replace(old_transport, new_transport, 1))

composition = read("nodes/library/foundation/docs/composition.md")
needle = '''## Source updates are change requests\n\nConsumers remain pinned to an accepted immutable Source package. A newly published Source version is an update candidate, not live inheritance.\n'''
replacement = '''## Source updates are change requests\n\nConsumers remain pinned to an accepted immutable Source package. A newly published Source version is an update candidate, not live inheritance. Repository/discovery parameters live centrally in `contextcanon.yaml`; changing a Git ref or switching the same repository to a local/offline checkout changes only where candidates are discovered, never the currently accepted package. Existing inline Git transport metadata remains a compatibility fallback for older projects.\n\nHuman operators may address a Source by its unique visible name instead of copying its stable UUID. `contextcanon source list` exposes both. `contextcanon source update <name-or-id>` combines fetch, deterministic review and explicit acceptance, while `contextcanon parent propagate --all` then advances descendant Parent pins top-down with a diff/confirmation at each edge.\n'''
if needle not in composition:
    raise RuntimeError("composition update section not found")
write("nodes/library/foundation/docs/composition.md", composition.replace(needle, replacement, 1))

# Focused regression tests.
write(
    "tests/test_configuration_and_update_ux.py",
    r'''from __future__ import annotations

import contextlib
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from contextcanon.cli import main as cli_main
from contextcanon.compiler import Compiler
from contextcanon.config import configured_source, load_project_config, upsert_git_source, upsert_local_mapping
from contextcanon.git_transport import fetch_git_candidate
from contextcanon.outputs import write_outputs
from contextcanon.package import artifact_files
from contextcanon.parser import parse_node
from contextcanon.sources import accept_parent_candidate, review_parent_candidate


def write_node(root: Path, node_id: str, name: str, version: str, statement: str) -> object:
    root.mkdir(parents=True, exist_ok=True)
    (root / "CONTEXT.src.md").write_text(
        f'''# {name} — Local Context Source\n<!-- ctx:node id="{node_id}" version="{version}" -->\n\n## Local Rules\n\n### General\n\n- **Policy:** {statement}\n  Why: Test policy.\n  <!-- ctx:rule id="RULE-1" -->\n''',
        encoding="utf-8",
    )
    compiled = Compiler(root if (root / ".git").exists() else root.parent).compile(root)
    write_outputs(compiled)
    return Compiler(root if (root / ".git").exists() else root.parent).compile(root)


def install_package(child: Path, compiled) -> None:
    destination = child / ".context" / "sources" / compiled.package_digest
    for rel, content in artifact_files(compiled).items():
        path = destination / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


def parent_source(child_id: str, child_name: str, parent_path: str, parent) -> str:
    return f'''# {child_name} — Local Context Source\n<!-- ctx:node id="{child_id}" version="0.1.0" -->\n\n## Parent Context Node\n\n- [{parent.metadata.name}]({parent_path}) — `{parent.metadata.version}`\n  <!-- ctx:parent id="{parent.metadata.id}" version="{parent.metadata.version}" normalized-digest="{parent.normalized_digest}" package-digest="{parent.package_digest}" -->\n'''


class ConfigurationAndUpdateUXTests(unittest.TestCase):
    def test_cli_version_is_available(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), self.assertRaises(SystemExit) as raised:
            cli_main(["--version"])
        self.assertEqual(raised.exception.code, 0)
        self.assertEqual(out.getvalue().strip(), "contextcanon 0.6.0")

    def test_central_yaml_can_switch_same_source_to_pure_local_discovery(self):
        project = Path(tempfile.mkdtemp())
        source_repo = Path(tempfile.mkdtemp())
        try:
            (project / ".git").mkdir()
            (source_repo / ".git").mkdir()
            source = write_node(source_repo, "source-id", "Shared", "1.0.0", "Old meaning.")
            consumer = project
            (consumer / "CONTEXT.src.md").write_text(
                f'''# Consumer — Local Context Source\n<!-- ctx:node id="consumer" version="0.1.0" -->\n\n## Sources\n\n- [Shared](contextcanon.yaml) — `1.0.0`\n  <!-- ctx:source id="source-id" version="1.0.0" normalized-digest="{source.normalized_digest}" package-digest="{source.package_digest}" -->\n''',
                encoding="utf-8",
            )
            install_package(consumer, source)
            upsert_local_mapping(project, "source-id", source_repo, ".")
            config = load_project_config(project)
            self.assertEqual(config.repositories[config.sources["source-id"].repository].kind, "local")
            candidate, _ = fetch_git_candidate(consumer, "source-id")
            self.assertEqual(candidate.package_digest, source.package_digest)
        finally:
            shutil.rmtree(project, ignore_errors=True)
            shutil.rmtree(source_repo, ignore_errors=True)

    def test_explicit_ref_fetches_unmerged_git_candidate_without_rewriting_config(self):
        project = Path(tempfile.mkdtemp())
        provider = Path(tempfile.mkdtemp())
        try:
            (project / ".git").mkdir()
            subprocess.run(["git", "init", "-q", "-b", "main", str(provider)], check=True)
            subprocess.run(["git", "-C", str(provider), "config", "user.email", "test@example.com"], check=True)
            subprocess.run(["git", "-C", str(provider), "config", "user.name", "Test"], check=True)
            main_package = write_node(provider, "source-id", "Shared", "1.0.0", "Main meaning.")
            subprocess.run(["git", "-C", str(provider), "add", "."], check=True)
            subprocess.run(["git", "-C", str(provider), "commit", "-qm", "main"], check=True)
            subprocess.run(["git", "-C", str(provider), "checkout", "-qb", "feature"], check=True)
            feature_package = write_node(provider, "source-id", "Shared", "1.1.0", "Feature meaning.")
            subprocess.run(["git", "-C", str(provider), "add", "."], check=True)
            subprocess.run(["git", "-C", str(provider), "commit", "-qm", "feature"], check=True)

            consumer = project
            (consumer / "CONTEXT.src.md").write_text(
                f'''# Consumer — Local Context Source\n<!-- ctx:node id="consumer" version="0.1.0" -->\n\n## Sources\n\n- [Shared](contextcanon.yaml) — `1.0.0`\n  <!-- ctx:source id="source-id" version="1.0.0" normalized-digest="{main_package.normalized_digest}" package-digest="{main_package.package_digest}" -->\n''',
                encoding="utf-8",
            )
            install_package(consumer, main_package)
            upsert_git_source(project, "source-id", str(provider), "main", ".")
            candidate, _ = fetch_git_candidate(consumer, "source-id", discovery_ref="feature")
            self.assertEqual(candidate.package_digest, feature_package.package_digest)
            source_cfg, repo_cfg = configured_source(project, "source-id")
            self.assertEqual(repo_cfg.ref, "main")
        finally:
            shutil.rmtree(project, ignore_errors=True)
            shutil.rmtree(provider, ignore_errors=True)

    def test_parent_propagate_updates_chain_top_down_in_one_command(self):
        repo = Path(tempfile.mkdtemp())
        try:
            (repo / ".git").mkdir()
            parent = write_node(repo, "root", "Root", "1.0.0", "Initial meaning.")
            child_root = repo / "child"
            child_root.mkdir()
            (child_root / "CONTEXT.src.md").write_text(parent_source("child", "Child", "..", parent), encoding="utf-8")
            install_package(child_root, parent)
            child = Compiler(repo).compile(child_root)
            write_outputs(child)

            grand_root = child_root / "grand"
            grand_root.mkdir()
            (grand_root / "CONTEXT.src.md").write_text(parent_source("grand", "Grand", "..", child), encoding="utf-8")
            install_package(grand_root, child)
            write_outputs(Compiler(repo).compile(grand_root))

            write_node(repo, "root", "Root", "1.1.0", "Updated meaning.")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                rc = cli_main(["parent", "propagate", str(repo), "--yes"])
            self.assertEqual(rc, 0, out.getvalue())
            grand = Compiler(repo).compile(grand_root)
            self.assertEqual([rule.statement for rule in grand.inherited_rules], ["Updated meaning."])
            self.assertIn("Propagated 2 Parent edge(s) top-down.", out.getvalue())
        finally:
            shutil.rmtree(repo, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
''',
)

print("Issues #21-#24 product edits prepared")
