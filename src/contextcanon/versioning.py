from __future__ import annotations

import json
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .compiler import Compiler
from .parser import ContextCanonError, find_repo_root

_SEMVERISH_RE = re.compile(
    r"^(?P<major>0|[1-9][0-9]*)\.(?P<minor>0|[1-9][0-9]*)\.(?P<patch>0|[1-9][0-9]*)(?P<suffix>(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?)$"
)
_NODE_COMMENT_RE = re.compile(r"<!--\s*ctx:node\s+(?P<attrs>.*?)\s*-->")
_VERSION_ATTR_RE = re.compile(r'(?P<prefix>\bversion=")(?P<version>[^"]*)(?P<suffix>")')


@dataclass(frozen=True)
class VersionBump:
    node_name: str
    before: str
    after: str


def minimum_patch_bump(version: str) -> str | None:
    match = _SEMVERISH_RE.fullmatch(version)
    if match is None:
        return None
    patch = int(match.group("patch")) + 1
    return f"{match.group('major')}.{match.group('minor')}.{patch}{match.group('suffix')}"


def _previous_package_identity(node_root: Path) -> tuple[str, str, str] | None:
    manifest = node_root / ".context" / "package.json"
    if not manifest.is_file():
        return None
    try:
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        node = payload["node"]
        digests = payload["digests"]
        node_id = node["id"]
        version = node["version"]
        package_digest = digests["package"]
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError):
        return None
    if not all(isinstance(value, str) and value for value in (node_id, version, package_digest)):
        return None
    return node_id, version, package_digest


def version_reuse_problem(compiled) -> str | None:
    previous = _previous_package_identity(compiled.parsed.root)
    if previous is None:
        return None
    node_id, version, package_digest = previous
    if node_id != compiled.metadata.id:
        return None
    if version == compiled.metadata.version and package_digest != compiled.package_digest:
        suggestion = minimum_patch_bump(version)
        if suggestion is None:
            return (
                f"Context Node package changed but version {version!r} was reused; "
                "update ctx:node version manually before publishing this package"
            )
        return (
            f"Context Node package changed but version {version!r} was reused; "
            f"run contextcanon build to apply the minimum patch bump to {suggestion!r}, "
            "or set a higher minor/major version explicitly"
        )
    return None


def ensure_node_version_advanced(node_root: Path, repo_root: Path | None = None) -> VersionBump | None:
    node_root = node_root.resolve()
    repo_root = (repo_root or find_repo_root(node_root)).resolve()
    compiled = Compiler(repo_root).compile(node_root)
    previous = _previous_package_identity(node_root)
    if previous is None:
        return None
    node_id, previous_version, previous_package = previous
    if node_id != compiled.metadata.id:
        return None
    if previous_version != compiled.metadata.version or previous_package == compiled.package_digest:
        return None

    bumped = minimum_patch_bump(compiled.metadata.version)
    if bumped is None:
        raise ContextCanonError(
            f"{compiled.metadata.name}: package identity changed while version {compiled.metadata.version!r} stayed unchanged; "
            "this version cannot be patch-bumped safely, so update ctx:node version manually"
        )
    _replace_node_version(node_root / "CONTEXT.src.md", compiled.metadata.version, bumped)
    return VersionBump(compiled.metadata.name, compiled.metadata.version, bumped)


def _replace_node_version(path: Path, before: str, after: str) -> None:
    text = path.read_text(encoding="utf-8")
    matches = list(_NODE_COMMENT_RE.finditer(text))
    if len(matches) != 1:
        raise ContextCanonError(f"{path}: expected exactly one ctx:node comment for automatic version bump")
    match = matches[0]
    attrs = match.group("attrs")
    versions = list(_VERSION_ATTR_RE.finditer(attrs))
    if len(versions) != 1 or versions[0].group("version") != before:
        raise ContextCanonError(f"{path}: could not safely update ctx:node version from {before!r}")
    updated_attrs = _VERSION_ATTR_RE.sub(
        lambda item: item.group("prefix") + after + item.group("suffix"),
        attrs,
        count=1,
    )
    updated = text[: match.start("attrs")] + updated_attrs + text[match.end("attrs") :]
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(updated)
        os.replace(temporary, path)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
