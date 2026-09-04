from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

from .model import CompiledPackage
from .onboarding_structure import HumanStructurePlan
from .package import load_package
from .parser import ContextCanonError
from .onboarding_workspace import write_utf8


REUSABLE_CONTEXTS_SCHEMA = "contextcanon/onboarding-reusable-contexts/v0"
REUSABLE_CONTEXTS_STATE_SCHEMA = "contextcanon/onboarding-reusable-contexts-state/v0"
REUSABLE_CONTEXTS_STATE_NAME = "reusable-contexts.json"
CATALOG_START = "<!-- contextcanon-reusable-catalog:start -->"
CATALOG_END = "<!-- contextcanon-reusable-catalog:end -->"
ASSIGNMENTS_START = "<!-- contextcanon-reusable-assignments:start -->"
ASSIGNMENTS_END = "<!-- contextcanon-reusable-assignments:end -->"
GENERATED_PROJECT_START = "<!-- contextcanon-reusable-project-nodes:start -->"
GENERATED_PROJECT_END = "<!-- contextcanon-reusable-project-nodes:end -->"
GENERATED_CATALOG_START = "<!-- contextcanon-reusable-found-nodes:start -->"
GENERATED_CATALOG_END = "<!-- contextcanon-reusable-found-nodes:end -->"

_HEADER_RE = re.compile(
    r'<!-- contextcanon-reusable-contexts schema="(?P<schema>[^"]+)" '
    r'evidence="(?P<evidence>[0-9a-f]{64})" structure="(?P<structure>[0-9a-f]{64})" -->'
)
_ASSIGN_RE = re.compile(
    r'^- \*\*(?P<target>.+?)\*\* \(`(?P<path>[^`]+)`\) ← '
    r'\*\*(?P<source>.+?)\*\* \(`(?P<version>[^`]+)`\)$'
)


@dataclass(frozen=True)
class ReusableContextAssignment:
    target_node_key: str
    target_name: str
    target_path: str
    source_node_id: str
    source_name: str
    source_version: str
    source_normalized_digest: str
    source_package_digest: str
    why: str

    @property
    def owner_spec(self) -> str:
        return f"{self.target_node_key}={self.source_node_id}"

    def to_dict(self) -> dict[str, str]:
        return {
            "target_node_key": self.target_node_key,
            "target_name": self.target_name,
            "target_path": self.target_path,
            "source_node_id": self.source_node_id,
            "source_name": self.source_name,
            "source_version": self.source_version,
            "source_normalized_digest": self.source_normalized_digest,
            "source_package_digest": self.source_package_digest,
            "why": self.why,
        }


@dataclass(frozen=True)
class ReusableContextsPlan:
    evidence_digest: str
    structure_digest: str
    decision: str
    catalog_locations: tuple[str, ...]
    catalog_roots: tuple[Path, ...]
    catalog_packages: tuple[CompiledPackage, ...]
    assignments: tuple[ReusableContextAssignment, ...]
    review_digest: str

    @property
    def is_complete(self) -> bool:
        return self.decision == "accept"

    @property
    def catalog_package_inputs(self) -> tuple[str, ...]:
        return tuple(str(path) for path in self.catalog_roots)

    @property
    def owner_source_specs(self) -> tuple[str, ...]:
        return tuple(assignment.owner_spec for assignment in self.assignments)

    @property
    def owner_source_whys(self) -> dict[str, str]:
        return {assignment.owner_spec: assignment.why for assignment in self.assignments}


def _error(message: str) -> ContextCanonError:
    return ContextCanonError(f"Reusable Context setup: {message}")


def _between(text: str, start: str, end: str, label: str) -> str:
    if text.count(start) != 1 or text.count(end) != 1:
        raise _error(f"malformed {label} markers")
    a = text.index(start) + len(start)
    b = text.index(end, a)
    return text[a:b]


def _catalog_locations(text: str) -> tuple[str, ...]:
    body = _between(text, CATALOG_START, CATALOG_END, "Catalog locations")
    values: list[str] = []
    for raw in body.splitlines():
        line = raw.strip()
        if not line:
            continue

        # Human input is intentionally forgiving. A pasted path is the semantic
        # value; Markdown bullet/code/quote wrappers are only presentation.
        if line.startswith("- "):
            line = line[2:].strip()
        if len(line) >= 2 and (line[0], line[-1]) in {
            ("`", "`"),
            ('"', '"'),
            ("'", "'"),
        }:
            line = line[1:-1].strip()

        if not line:
            raise _error("Catalog location cannot be empty")
        if line.startswith("<!--"):
            raise _error("Catalog locations must contain paths, not machine markers")
        if line not in values:
            values.append(line)
    return tuple(values)

def _decision(text: str) -> str:
    matches = re.findall(r"(?m)^Decision: `([^`]+)`$", text)
    if len(matches) != 1 or matches[0] not in {"pending", "accept"}:
        raise _error("Decision must appear exactly once and be `pending` or `accept`")
    return matches[0]


def _candidate_manifest_paths(location: Path) -> list[Path]:
    if (location / ".context" / "package.json").is_file():
        return [location / ".context" / "package.json"]
    if not location.is_dir():
        raise _error(f"Catalog location does not exist or is not a directory: {location}")
    result: list[Path] = []
    for manifest in location.rglob("package.json"):
        if manifest.parent.name != ".context":
            continue
        rel_parts = manifest.relative_to(location).parts
        # Ignore accepted/candidate package caches inside another Node.
        if "sources" in rel_parts and ".context" in rel_parts:
            continue
        if "candidates" in rel_parts and ".context" in rel_parts:
            continue
        result.append(manifest)
    return sorted(result)


def discover_catalog(locations: tuple[str, ...]) -> tuple[tuple[Path, ...], tuple[CompiledPackage, ...]]:
    by_id: dict[str, tuple[Path, CompiledPackage]] = {}
    for raw in locations:
        location = Path(raw).expanduser().resolve()
        manifests = _candidate_manifest_paths(location)
        if not manifests:
            raise _error(
                f"Catalog location contains no compiled Context package: {location}. "
                "Build/publish the reusable Node first or choose a directory containing compiled Nodes."
            )
        for manifest in manifests:
            root = manifest.parent.parent
            package = load_package(root)
            previous = by_id.get(package.metadata.id)
            if previous is not None:
                if previous[1].package_digest != package.package_digest:
                    raise _error(
                        f"Catalog contains more than one package version for {package.metadata.name} "
                        f"({package.metadata.id}); narrow the Catalog location before accepting the run"
                    )
                continue
            by_id[package.metadata.id] = (root, package)
    ordered = sorted(
        by_id.values(),
        key=lambda item: (item[1].metadata.name.casefold(), item[1].metadata.version, item[1].metadata.id),
    )
    return tuple(item[0] for item in ordered), tuple(item[1] for item in ordered)


def _parse_assignments(
    text: str,
    structure: HumanStructurePlan,
    packages: tuple[CompiledPackage, ...],
) -> tuple[ReusableContextAssignment, ...]:
    body = _between(text, ASSIGNMENTS_START, ASSIGNMENTS_END, "Assignments")
    target_by_label = {(node.name, node.path): node for node in structure.nodes}
    package_by_label: dict[tuple[str, str], list[CompiledPackage]] = {}
    for package in packages:
        package_by_label.setdefault((package.metadata.name, package.metadata.version), []).append(package)

    lines = body.splitlines()
    result: list[ReusableContextAssignment] = []
    seen: set[tuple[str, str]] = set()
    index = 0
    while index < len(lines):
        line = lines[index].strip()
        if not line:
            index += 1
            continue
        match = _ASSIGN_RE.fullmatch(line)
        if match is None:
            raise _error(
                "Assignments must use '- **Project Node** (`path`) ← **Reusable Context** (`version`)' "
                "followed by an indented 'Why:' line"
            )
        target = target_by_label.get((match.group("target"), match.group("path")))
        if target is None:
            raise _error(
                f"Assignment target is not an accepted project Context Node: "
                f"{match.group('target')} ({match.group('path')})"
            )
        candidates = package_by_label.get((match.group("source"), match.group("version")), [])
        if not candidates:
            raise _error(
                f"Assignment Source is not present in the current Catalog: "
                f"{match.group('source')} {match.group('version')}"
            )
        if len(candidates) != 1:
            raise _error(
                f"Catalog label is ambiguous for {match.group('source')} {match.group('version')}; "
                "narrow the Catalog location"
            )
        index += 1
        if index >= len(lines):
            raise _error("Assignment is missing its indented Why line")
        why_line = lines[index].strip()
        if not why_line.startswith("Why:"):
            raise _error("Assignment must be followed by '  Why: ...'")
        why = why_line[4:].strip()
        if not why or why == "-":
            raise _error("Every reusable Context assignment needs a real Why rationale")
        package = candidates[0]
        identity = (target.key, package.metadata.id)
        if identity in seen:
            raise _error(f"Duplicate reusable Context assignment for {target.name} and {package.metadata.name}")
        seen.add(identity)
        result.append(
            ReusableContextAssignment(
                target_node_key=target.key,
                target_name=target.name,
                target_path=target.path,
                source_node_id=package.metadata.id,
                source_name=package.metadata.name,
                source_version=package.metadata.version,
                source_normalized_digest=package.normalized_digest,
                source_package_digest=package.package_digest,
                why=why,
            )
        )
        index += 1
    return tuple(result)


def _normalized_payload(
    evidence_digest: str,
    structure_digest: str,
    decision: str,
    locations: tuple[str, ...],
    roots: tuple[Path, ...],
    packages: tuple[CompiledPackage, ...],
    assignments: tuple[ReusableContextAssignment, ...],
) -> dict[str, object]:
    return {
        "schema": REUSABLE_CONTEXTS_STATE_SCHEMA,
        "evidence_digest": evidence_digest,
        "structure_digest": structure_digest,
        "decision": decision,
        "catalog_locations": list(locations),
        "catalog_packages": [
            {
                "path": str(root),
                "id": package.metadata.id,
                "name": package.metadata.name,
                "version": package.metadata.version,
                "normalized_digest": package.normalized_digest,
                "package_digest": package.package_digest,
            }
            for root, package in zip(roots, packages)
        ],
        "assignments": [assignment.to_dict() for assignment in assignments],
    }


def _digest(payload: dict[str, object]) -> str:
    data = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def render_reusable_contexts(
    evidence_digest: str,
    structure: HumanStructurePlan,
    decision: str,
    locations: tuple[str, ...],
    packages: tuple[CompiledPackage, ...],
    assignments: tuple[ReusableContextAssignment, ...],
) -> str:
    lines = [
        "# STEP 05 — Reusable Contexts",
        f'<!-- contextcanon-reusable-contexts schema="{REUSABLE_CONTEXTS_SCHEMA}" evidence="{evidence_digest}" structure="{structure.structure_digest}" -->',
        "",
        "This step says **which reusable Context Nodes are available and where they apply in this project**. It happens after the project's own Context Node structure is accepted and before the placement LLM distributes project knowledge.",
        "",
        "Edit only the Catalog locations, the sparse Assignments, and `Decision`. ContextCanon owns IDs, package digests and the generated lists. Run the same `contextcanon onboard reusable-contexts ...` command again after every edit.",
        "",
        "## Catalog locations",
        "",
        "Add one directory containing reusable compiled Context Nodes per line. A location may itself be one Context Node or a directory containing several Nodes.",
        "",
        "Paste a path normally. Markdown bullets, backticks, or quotes are optional input conveniences; ContextCanon rewrites accepted input into one canonical Markdown form on the next run.",
        "",
        r"Example: `C:\Users\you\PycharmProjects\context-canon\nodes\library`",
        "",
        "> ✏️ Editable Catalog locations start below.",
        "",
        CATALOG_START,
    ]
    lines.extend(f"- `{value}`" for value in locations)
    lines.extend(
        [
            CATALOG_END,
            "",
            "> End editable Catalog locations.",
            "",
            "## Assignments",
            "",
            "Only list relationships that should actually exist; there is deliberately no project-node × catalog-node matrix. Copy the human-readable names/path/version from the generated lists below. Every relationship needs a durable `Why`.",
            "",
            "Example syntax:",
            "",
            "```text",
            "- **AI Workstation** (`.`) ← **Development Workflow** (`0.2.0-draft`)",
            "  Why: Shared development workflow applies to the whole project.",
            "```",
            "",
            "> ✏️ Editable reusable-Context assignment controls start below.",
            "",
            f"Decision: `{decision}`",
            "",
            ASSIGNMENTS_START,
        ]
    )
    for assignment in assignments:
        lines.extend(
            [
                f"- **{assignment.target_name}** (`{assignment.target_path}`) ← **{assignment.source_name}** (`{assignment.source_version}`)",
                f"  Why: {assignment.why}",
            ]
        )
    lines.extend(
        [
            ASSIGNMENTS_END,
            "",
            "> End editable reusable-Context assignment controls.",
            "",
            "Set `Decision` to `accept` when the Catalog and assignments are the intended reusable-context composition for this onboarding. An empty assignment list is valid when no reusable Context applies.",
            "",
            "## Available project Context Nodes — generated",
            "",
            GENERATED_PROJECT_START,
        ]
    )
    for node in structure.nodes:
        lines.append(f"- **{node.name}** (`{node.path}`)")
    lines.extend([GENERATED_PROJECT_END, "", "## Available reusable Context Nodes — generated", "", GENERATED_CATALOG_START])
    if packages:
        for package in packages:
            lines.append(
                f"- **{package.metadata.name}** (`{package.metadata.version}`) — exact package `{package.package_digest}`"
            )
    elif locations:
        lines.append("No verified reusable Context Nodes found.")
    else:
        lines.append("No Catalog locations yet. Add one or more above and run this step again.")
    lines.extend(
        [
            GENERATED_CATALOG_END,
            "",
            "The generated package identities are review information. Do not copy their IDs or digests into Assignments; ContextCanon resolves and remembers them for subsequent steps.",
            "",
        ]
    )
    return "\n".join(lines)


def _initial_text(evidence_digest: str, structure: HumanStructurePlan) -> str:
    return render_reusable_contexts(evidence_digest, structure, "pending", (), (), ())


def _parse_bound_text(path: Path, evidence_digest: str, structure: HumanStructurePlan) -> tuple[str, tuple[str, ...]]:
    text = path.read_text(encoding="utf-8")
    header = _HEADER_RE.search(text)
    if header is None:
        raise _error(f"{path} is missing its ContextCanon binding header")
    if header.group("schema") != REUSABLE_CONTEXTS_SCHEMA:
        raise _error(f"unsupported schema {header.group('schema')!r}")
    if header.group("evidence") != evidence_digest:
        raise _error("Evidence digest differs from this onboarding snapshot")
    if header.group("structure") != structure.structure_digest:
        raise _error(
            "Accepted project Context structure changed; recreate/review STEP-05-reusable-contexts.md against the new structure"
        )
    return text, _catalog_locations(text)


def refresh_reusable_contexts(
    path: Path,
    snapshot_root: Path,
    evidence_digest: str,
    structure: HumanStructurePlan,
) -> tuple[ReusableContextsPlan, bool]:
    path = path.resolve()
    created = False
    if not path.exists():
        write_utf8(path, _initial_text(evidence_digest, structure))
        created = True
    text, locations = _parse_bound_text(path, evidence_digest, structure)
    decision = _decision(text)
    roots, packages = discover_catalog(locations) if locations else ((), ())
    assignments = _parse_assignments(text, structure, packages)
    canonical = render_reusable_contexts(
        evidence_digest,
        structure,
        decision,
        locations,
        packages,
        assignments,
    )
    write_utf8(path, canonical)
    payload = _normalized_payload(
        evidence_digest,
        structure.structure_digest,
        decision,
        locations,
        roots,
        packages,
        assignments,
    )
    review_digest = _digest(payload)
    payload["review_digest"] = review_digest
    payload["human_file_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    write_utf8(
        snapshot_root.resolve() / REUSABLE_CONTEXTS_STATE_NAME,
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    return ReusableContextsPlan(
        evidence_digest,
        structure.structure_digest,
        decision,
        locations,
        roots,
        packages,
        assignments,
        review_digest,
    ), created


def load_accepted_reusable_contexts(
    path: Path,
    snapshot_root: Path,
    evidence_digest: str,
    structure: HumanStructurePlan,
) -> ReusableContextsPlan:
    state_path = snapshot_root.resolve() / REUSABLE_CONTEXTS_STATE_NAME
    if not state_path.is_file():
        raise _error("STEP 05 has not been validated yet; run `contextcanon onboard reusable-contexts` first")
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise _error(f"machine state is unreadable: {state_path}") from exc
    if state.get("schema") != REUSABLE_CONTEXTS_STATE_SCHEMA:
        raise _error("unsupported reusable Context machine state")
    if state.get("evidence_digest") != evidence_digest or state.get("structure_digest") != structure.structure_digest:
        raise _error("reusable Context machine state does not match this Evidence/Structure")
    if state.get("decision") != "accept":
        raise _error("STEP 05 is still pending; set Decision to `accept` and rerun the step")
    if not path.is_file():
        raise _error(f"missing human reusable Context review: {path}")
    current_sha = hashlib.sha256(path.read_bytes()).hexdigest()
    if current_sha != state.get("human_file_sha256"):
        raise _error("STEP-05-reusable-contexts.md changed after validation; rerun `contextcanon onboard reusable-contexts`")

    text, locations = _parse_bound_text(path, evidence_digest, structure)
    roots, packages = discover_catalog(locations) if locations else ((), ())
    assignments = _parse_assignments(text, structure, packages)
    payload = _normalized_payload(
        evidence_digest,
        structure.structure_digest,
        "accept",
        locations,
        roots,
        packages,
        assignments,
    )
    review_digest = _digest(payload)
    if review_digest != state.get("review_digest"):
        raise _error(
            "Reusable Context Catalog/package identity changed after STEP 05 acceptance; rerun the step and review the change"
        )
    return ReusableContextsPlan(
        evidence_digest,
        structure.structure_digest,
        "accept",
        locations,
        roots,
        packages,
        assignments,
        review_digest,
    )
