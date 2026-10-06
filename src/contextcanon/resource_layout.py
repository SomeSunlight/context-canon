"""Compact Node-oriented Resource locations; complete origin stays metadata."""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict

from .model import ResourceOrigin
from .parser import ContextCanonError

ORIGINS_PATH = ".context/resource-origins.json"
ORIGINS_SCHEMA = "contextcanon/resource-origins/v1"


def resource_namespace(node_id: str) -> str:
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,15}", node_id):
        return node_id
    return "n" + hashlib.sha256(node_id.encode("utf-8")).hexdigest()[:15]


def legacy_namespace(node_id: str) -> str:
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", node_id):
        return node_id
    return "sha256-" + hashlib.sha256(node_id.encode("utf-8")).hexdigest()


def render_origins(origins: dict[str, ResourceOrigin]) -> bytes:
    namespaces: dict[str, str] = {}
    for origin in origins.values():
        namespace = origin.path.split("/")[2]
        previous = namespaces.setdefault(namespace, origin.node_id)
        if previous != origin.node_id:
            raise ContextCanonError(f"Resource origin token collision: {previous} and {origin.node_id}")
    payload = {"schema": ORIGINS_SCHEMA, "resources": [asdict(origins[path]) for path in sorted(origins)]}
    return (json.dumps(payload, sort_keys=True, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
