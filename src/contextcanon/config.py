from __future__ import annotations

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
