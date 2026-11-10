from __future__ import annotations

import json
import re
import subprocess
import tomllib
from importlib.metadata import PackageNotFoundError, distribution, version as distribution_version
from pathlib import Path


_DISTRIBUTION_NAME = "contextcanon"


def _project_root(start: Path | None = None) -> Path | None:
    current = (start or Path(__file__)).resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        pyproject = candidate / "pyproject.toml"
        if not pyproject.is_file():
            continue
        try:
            project = tomllib.loads(pyproject.read_text(encoding="utf-8")).get("project", {})
        except (OSError, tomllib.TOMLDecodeError):
            continue
        if project.get("name") == _DISTRIBUTION_NAME:
            return candidate
    return None


def _pyproject_version(root: Path) -> str | None:
    try:
        project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8")).get("project", {})
    except (OSError, tomllib.TOMLDecodeError):
        return None
    value = project.get("version")
    return value if isinstance(value, str) and value else None


def release_version(project_root: Path | None = None) -> str:
    """Return the canonical release version.

    A source/editable checkout reads the value directly from pyproject.toml so a
    pulled release-version change is visible without reinstalling the tool.
    Installed artifacts fall back to Python distribution metadata.
    """

    root = project_root or _project_root()
    if root is not None:
        value = _pyproject_version(root)
        if value is not None:
            return value
    try:
        return distribution_version(_DISTRIBUTION_NAME)
    except PackageNotFoundError:
        return "unknown"


def _git(root: Path, *args: str) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), *args],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=2,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout.strip()


def git_provenance(project_root: Path | None = None) -> str | None:
    """Return human-readable Git checkout provenance when available."""

    root = project_root or _project_root()
    if root is None or not (root / ".git").exists():
        return None

    commit = _git(root, "rev-parse", "--short=7", "HEAD")
    if not commit:
        return None

    branch = _git(root, "symbolic-ref", "--quiet", "--short", "HEAD") or "detached"
    status = _git(root, "status", "--porcelain", "--untracked-files=normal")

    result = f"{branch}@{commit}"
    if status:
        result += ", dirty"
    return result


def installed_git_origin() -> tuple[str, str, str | None] | None:
    """Return (repository URL, resolved commit, requested revision) from PEP 610.

    A uv/pip Git-URL tool installation has no .git checkout, but direct_url.json
    identifies the immutable installed commit. Do not consult the current CWD.
    """
    try:
        data = distribution(_DISTRIBUTION_NAME).read_text("direct_url.json")
    except (PackageNotFoundError, OSError):
        return None
    if not data:
        return None
    try:
        record = json.loads(data)
        info = record["vcs_info"]
        if info["vcs"] != "git":
            return None
        url = record["url"]
        commit = info["commit_id"]
        if not isinstance(url, str) or not url or not isinstance(commit, str):
            return None
        if not re.fullmatch(r"[a-fA-F0-9]{40}|[a-fA-F0-9]{64}", commit):
            return None
        requested = info.get("requested_revision")
        if requested is not None and (not isinstance(requested, str) or
                                      any(c in requested for c in "\r\n\t")):
            return None
        return url, commit.lower(), requested or None
    except (ValueError, TypeError, KeyError, AttributeError):
        return None


def installed_git_provenance() -> str | None:
    """Display installed Git-URL identity using the resolved, not requested, SHA."""
    origin = installed_git_origin()
    if origin is None:
        return None
    _, commit, requested = origin
    label = (requested or "git").removeprefix("refs/heads/").removeprefix("refs/tags/")
    if not label or re.fullmatch(r"[a-fA-F0-9]{7,64}", label):
        label = "detached"
    return f"{label}@{commit[:7]}"


def display_version(project_root: Path | None = None) -> str:
    release = release_version(project_root)
    provenance = git_provenance(project_root)
    if provenance is None and project_root is None:
        provenance = installed_git_provenance()
    return f"{release} ({provenance})" if provenance else release


__version__ = release_version()
