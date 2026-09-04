from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def write(rel: str, text: str) -> None:
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def replace_once(rel: str, old: str, new: str) -> None:
    text = read(rel)
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{rel}: expected one occurrence, found {count}: {old[:120]!r}")
    write(rel, text.replace(old, new, 1))


def replace_function(rel: str, name: str, new: str) -> None:
    text = read(rel)
    pattern = re.compile(rf"(?ms)^def {re.escape(name)}\(.*?(?=^def |\Z)")
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise SystemExit(f"{rel}: expected one function {name}, found {len(matches)}")
    match = matches[0]
    write(rel, text[:match.start()] + new.rstrip() + "\n\n" + text[match.end():])


# ---------------------------------------------------------------------------
# New human gate: reusable Context setup before placement.
# ---------------------------------------------------------------------------
write(
    "src/contextcanon/onboarding_reusable_contexts.py",
    r'''from __future__ import annotations

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
        match = re.fullmatch(r"- `(.+)`", line)
        if match is None:
            raise _error("Catalog locations must contain only '- `PATH`' lines")
        value = match.group(1).strip()
        if value not in values:
            values.append(value)
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
        "## Catalog locations — editable",
        "",
        "Add one directory containing reusable compiled Context Nodes per line. A location may itself be one Context Node or a directory containing several Nodes.",
        "",
        CATALOG_START,
    ]
    lines.extend(f"- `{value}`" for value in locations)
    lines.extend(
        [
            CATALOG_END,
            "",
            "## Assignments — editable",
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
            "Set `Decision: `accept`` when the Catalog and assignments are the intended reusable-context composition for this onboarding. An empty assignment list is valid when no reusable Context applies.",
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
'''
)


# ---------------------------------------------------------------------------
# Human-facing workspace: insert STEP 05 and renumber placement artifacts.
# ---------------------------------------------------------------------------
replace_once(
    "src/contextcanon/onboarding_workspace.py",
    '''PLACEMENT_INSTRUCTION_NAME = "STEP-05a-placement-instruction.md"\nPLACEMENT_PROPOSAL_NAME = "STEP-05b-placement-proposal.json"\nPLACEMENT_REVIEW_NAME = "STEP-07-placement.md"\nPLACEMENT_AUDIT_NAME = "STEP-07a-source-audit.md"\nPLACEMENT_PREVIEW_NAME = "STEP-08-placement-preview.md"\nPLACEMENT_FOLLOWUP_NAME = "STEP-09-placement-followup.md"\n''',
    '''REUSABLE_CONTEXTS_NAME = "STEP-05-reusable-contexts.md"\nPLACEMENT_INSTRUCTION_NAME = "STEP-06a-placement-instruction.md"\nPLACEMENT_PROPOSAL_NAME = "STEP-06b-placement-proposal.json"\nPLACEMENT_REVIEW_NAME = "STEP-08-placement.md"\nPLACEMENT_AUDIT_NAME = "STEP-08a-source-audit.md"\nPLACEMENT_PREVIEW_NAME = "STEP-09-placement-preview.md"\nPLACEMENT_FOLLOWUP_NAME = "STEP-10-placement-followup.md"\n''',
)
replace_once(
    "src/contextcanon/onboarding_workspace.py",
    '''    "placement-instruction.md": PLACEMENT_INSTRUCTION_NAME,\n    "placement-proposal.json": PLACEMENT_PROPOSAL_NAME,\n    "placement.md": PLACEMENT_REVIEW_NAME,\n    "placement-preview.md": PLACEMENT_PREVIEW_NAME,\n    "placement-followup.md": PLACEMENT_FOLLOWUP_NAME,\n''',
    '''    "placement-instruction.md": PLACEMENT_INSTRUCTION_NAME,\n    "placement-proposal.json": PLACEMENT_PROPOSAL_NAME,\n    "placement.md": PLACEMENT_REVIEW_NAME,\n    "placement-preview.md": PLACEMENT_PREVIEW_NAME,\n    "placement-followup.md": PLACEMENT_FOLLOWUP_NAME,\n    "STEP-05a-placement-instruction.md": PLACEMENT_INSTRUCTION_NAME,\n    "STEP-05b-placement-proposal.json": PLACEMENT_PROPOSAL_NAME,\n    "STEP-07-placement.md": PLACEMENT_REVIEW_NAME,\n    "STEP-07a-source-audit.md": PLACEMENT_AUDIT_NAME,\n    "STEP-08-placement-preview.md": PLACEMENT_PREVIEW_NAME,\n    "STEP-09-placement-followup.md": PLACEMENT_FOLLOWUP_NAME,\n''',
)
replace_once(
    "src/contextcanon/onboarding_workspace.py",
    '''    @property\n    def placement_instruction_path(self) -> Path:\n        return self.root / PLACEMENT_INSTRUCTION_NAME\n''',
    '''    @property\n    def reusable_contexts_path(self) -> Path:\n        return self.root / REUSABLE_CONTEXTS_NAME\n\n    @property\n    def placement_instruction_path(self) -> Path:\n        return self.root / PLACEMENT_INSTRUCTION_NAME\n''',
)

replace_function(
    "src/contextcanon/onboarding_workspace.py",
    "_workspace_plan",
    r'''def _workspace_plan() -> str:
    return f"""# ContextCanon onboarding plan
{PLAN_MARKER}

This is the **operator console** for the current onboarding. Work from top to bottom. Each step keeps its explanation, completion checkbox, exact command and produced artifact together so you do not have to scroll between a checklist and a separate command manual.

## Onboarding steps

{COMMANDS_START}
The exact snapshot-bound steps appear here after ContextCanon opens this workspace.
{COMMANDS_END}

## Current checkpoint

{CHECKPOINT_START}
No ContextCanon structure-first command has recorded a checkpoint in this workspace yet.
{CHECKPOINT_END}

The checkpoint is the **last state ContextCanon validated**, not a file watcher. After editing a human gate, rerun that same step before advancing.

## Human gates

- **LLM handoff 1:** `STEP-02a-structure-instruction.md` + only the frozen `evidence/` tree → `STEP-02b-structure-proposal.json`.
- **Human gate 1:** review/edit `STEP-03-structure.md`.
- **Reusable Context gate:** review/edit `STEP-05-reusable-contexts.md`; this owns Catalog locations, Source assignments and their Why rationale.
- **LLM handoff 2:** `STEP-06a-placement-instruction.md` + only the same frozen `evidence/` tree → `STEP-06b-placement-proposal.json`.
- **Human gate 2:** review/edit `STEP-08-placement.md`.

Normal onboarding commands deliberately do not require you to reconstruct Source Node IDs, package digests or repeated `--catalog-package`/`--owner-source` options. Those identities are resolved and retained by ContextCanon from STEP 05. The legacy CLI options remain available for scripting/backward compatibility.
"""
'''
)

replace_function(
    "src/contextcanon/onboarding_workspace.py",
    "_exact_commands",
    r'''def _exact_commands(
    workspace: OnboardingWorkspace,
    snapshot_root: Path,
    catalog_inputs: tuple[str, ...],
    owner_source_specs: tuple[str, ...],
    completed: set[int] | None = None,
) -> str:
    completed = completed or set()
    snapshot = _snapshot_label(snapshot_root)
    workspace_args = _workspace_option(workspace, snapshot_root)
    snapshot_literal = _quote_cli(snapshot)
    if os.name == "nt":
        snapshot_assignment = f"$SNAPSHOT = {snapshot_literal}"
        snapshot_token = "$SNAPSHOT"
        shell = "powershell"
    else:
        snapshot_assignment = f"SNAPSHOT={snapshot_literal}"
        snapshot_token = '"$SNAPSHOT"'
        shell = "sh"

    def render(parts: list[str]) -> str:
        command = _render_command(parts)
        return command.replace(snapshot_literal, snapshot_token, 1)

    def cmd(name: str) -> str:
        return render(["contextcanon", "onboard", name, snapshot, *workspace_args])

    def mark(step: int) -> str:
        return "x" if step in completed else " "

    lines = [
        COMMANDS_START,
        "These commands are for **this exact Evidence snapshot**. ContextCanon carries forward machine identities and accepted human inputs; copy the short command shown in the current step.",
        "",
        "Set this run variable once in your terminal:",
        "",
        f"```{shell}",
        snapshot_assignment,
        "```",
        "",
        "### STEP 01 — Freeze Evidence",
        f"- [{mark(1)}] **Done**",
        "",
        "ContextCanon freezes the exact project files used as onboarding Evidence so every later LLM/human decision refers to the same bytes. Reuse the current snapshot unless you intentionally want new Evidence.",
        "",
        "```text",
        "contextcanon onboard prepare .",
        "```",
        "",
        "### STEP 02 — Structure proposal",
        f"- [{mark(2)}] **Done**",
        "",
        "A reasoning LLM proposes the project's **semantic Context Node structure** — the responsibility shelves, not merely the existing directory tree.",
        "",
        "Generate `STEP-02a-structure-instruction.md`:",
        "",
        "```text",
        cmd("structure-instruction"),
        "```",
        "",
        "Give that instruction plus only the frozen `evidence/` tree to the LLM and save its JSON exactly as `STEP-02b-structure-proposal.json`. Then validate:",
        "",
        "```text",
        cmd("structure-validate"),
        "```",
        "",
        "### STEP 03 — Structure review",
        f"- [{mark(3)}] **Done**",
        "",
        "You review the proposed project Context Node hierarchy: which semantic shelves exist, their names, paths and parent/child grouping.",
        "",
        "```text",
        cmd("structure-review"),
        "```",
        "",
        "Edit `STEP-03-structure.md` as needed, then run the same command again to validate the human gate.",
        "",
        "### STEP 04 — Materialize shelves",
        f"- [{mark(4)}] **Done**",
        "",
        "ContextCanon previews and then creates only the missing accepted Context Node directories/skeletons. No project knowledge is placed yet.",
        "",
        "```text",
        cmd("structure-preview"),
        cmd("structure-materialize"),
        "```",
        "",
        "Review `STEP-04-structure-preview.md` between the two commands.",
        "",
        "### STEP 05 — Reusable Contexts",
        f"- [{mark(5)}] **Done**",
        "",
        "You tell ContextCanon **where reusable external Context Nodes can be found, which accepted project Nodes they apply to, and why**. This prepares the foreign shelves before the placement LLM distributes project knowledge.",
        "",
        "```text",
        cmd("reusable-contexts"),
        "```",
        "",
        "The first run creates `STEP-05-reusable-contexts.md`. Edit its Catalog locations and sparse Assignments, set `Decision: `accept`` when correct, and rerun the same command after every edit. You work with names/path/version; ContextCanon owns IDs and digests.",
        "",
        "### STEP 06 — Placement proposal",
        f"- [{mark(6)}] **Done**",
        "",
        "A reasoning LLM now places the project's frozen knowledge onto the already accepted own/reusable Context shelves and proposes any reviewed source-document cleanup.",
        "",
        "Generate `STEP-06a-placement-instruction.md`:",
        "",
        "```text",
        cmd("placement-instruction"),
        "```",
        "",
        "Give that instruction plus only the frozen `evidence/` tree to the LLM and save its JSON exactly as `STEP-06b-placement-proposal.json`.",
        "",
        "### STEP 07 — Placement validate",
        f"- [{mark(7)}] **Done**",
        "",
        "ContextCanon checks the LLM proposal against the frozen Evidence, accepted project structure and exact reusable Context packages. This is machine validation; there is no separate STEP-07 artifact.",
        "",
        "```text",
        cmd("placement-validate"),
        "```",
        "",
        "### STEP 08 — Placement review",
        f"- [{mark(8)}] **Done**",
        "",
        "You review **which project knowledge goes into which Context Node**. Reusable Context assignments from STEP 05 are already decided and appear only as compact traceability, not as a giant selection matrix.",
        "",
        "```text",
        cmd("placement-review"),
        "```",
        "",
        "Edit `STEP-08-placement.md` as needed and rerun the same command to validate it. Every successful run regenerates read-only `STEP-08a-source-audit.md` for source-file-first semantic-loss checking.",
        "",
        "### STEP 09 — Publication preview",
        f"- [{mark(9)}] **Done**",
        "",
        "ContextCanon shows the exact Context/source-document changes that publication would make, including semantic Parent pins and reusable Source installation.",
        "",
        "```text",
        cmd("placement-preview"),
        "```",
        "",
        "Review `STEP-09-placement-preview.md` before publishing.",
        "",
        "### STEP 10 — Publish placement",
        f"- [{mark(10)}] **Done**",
        "",
        "ContextCanon transactionally publishes the fully reviewed Context Node authoring and produces the durable follow-up report.",
        "",
        "```text",
        cmd("placement-publish"),
        "```",
        "",
        "Inspect `STEP-10-placement-followup.md` afterwards.",
        "",
        "## Reset commands for testing",
        "",
        "Frozen Evidence is preserved. Restart from the semantic step you want to retest:",
        "",
        "```text",
    ]
    for step in range(2, 11):
        lines.append(render(["contextcanon", "onboard", "reset", snapshot, "--from", str(step), *workspace_args]))
    lines.extend(["```", COMMANDS_END])
    return "\n".join(lines)
'''
)

replace_function(
    "src/contextcanon/onboarding_workspace.py",
    "_completed_steps",
    r'''def _completed_steps(stage: str, placement_review_complete: bool | None) -> set[int]:
    reset = re.fullmatch(r"reset before step (\d+)", stage)
    if reset is not None:
        target = int(reset.group(1))
        return set(range(1, max(1, target)))

    rank = {
        "structure instruction ready": 1,
        "structure proposal validated": 2,
        "human structure validated": 3,
        "structure previewed": 3,
        "structure materialized": 4,
        "reusable contexts review": 4,
        "reusable contexts accepted": 5,
        "placement instruction ready": 5,
        "placement proposal validated": 7,
        "human placement review": 7,
        "placement publication previewed": 9,
        "placement published": 10,
    }.get(stage, 1)
    completed = set(range(1, rank + 1))
    if stage == "human placement review" and placement_review_complete is True:
        completed.add(8)
    return completed
'''
)

# Old separate checklist is gone; keep the function as a compatibility no-op.
replace_function(
    "src/contextcanon/onboarding_workspace.py",
    "_rewrite_checklist",
    r'''def _rewrite_checklist(text: str, completed: set[int], path: Path) -> str:
    return text
'''
)

replace_function(
    "src/contextcanon/onboarding_workspace.py",
    "_replace_commands",
    r'''def _replace_commands(
    text: str,
    workspace: OnboardingWorkspace,
    snapshot_root: Path,
    catalog_inputs: tuple[str, ...],
    owner_source_specs: tuple[str, ...],
    completed: set[int] | None = None,
) -> str:
    block = _exact_commands(
        workspace,
        snapshot_root,
        catalog_inputs,
        owner_source_specs,
        completed=completed,
    )
    if COMMANDS_START not in text or COMMANDS_END not in text:
        anchor = "## Current checkpoint"
        if anchor not in text:
            raise ContextCanonError(f"Malformed onboarding plan; missing {anchor}")
        return text.replace(anchor, block + "\n\n" + anchor, 1)
    start = text.index(COMMANDS_START)
    end = text.index(COMMANDS_END, start) + len(COMMANDS_END)
    return text[:start] + block + text[end:]
'''
)

replace_once(
    "src/contextcanon/onboarding_workspace.py",
    '''    text = _rewrite_checklist(text, _completed_steps(stage, placement_review_complete), workspace.plan_path)\n    text = _replace_commands(text, workspace, snapshot_root, catalog_inputs, owner_specs)\n''',
    '''    completed = _completed_steps(stage, placement_review_complete)\n    text = _replace_commands(text, workspace, snapshot_root, catalog_inputs, owner_specs, completed=completed)\n''',
)
# Keep machine inputs, but stop using PLAN as a configuration dump.
replace_once(
    "src/contextcanon/onboarding_workspace.py",
    '''    if source_catalog:\n        lines.append("- Exact reusable Source catalog:")\n        lines.extend(f"  - `{item}`" for item in source_catalog)\n    if catalog_inputs:\n        lines.append("- Reuse these exact `--catalog-package` inputs for copy/paste commands:")\n        lines.extend(f"  - `{item}`" for item in catalog_inputs)\n    if owner_specs:\n        lines.append("- Owner-selected Source choices already recorded in the human review (do not repeat on preview/publish):")\n        lines.extend(f"  - `{item}`" for item in owner_specs)\n''',
    '''    # Catalog paths, package identities and Source assignments are domain inputs owned by\n    # STEP-05-reusable-contexts.md / machine state, not by this orchestration PLAN.\n''',
)

# Refresh the stable workspace README wording/artifact list.
replace_once(
    "src/contextcanon/onboarding_workspace.py",
    '''- `{PLACEMENT_INSTRUCTION_NAME}` — generated instruction for the placement reasoning pass.\n- `{PLACEMENT_PROPOSAL_NAME}` — LLM JSON describing where existing meaning belongs.\n- Step 06 is validation-only and therefore intentionally has no separate artifact.\n- `{PLACEMENT_REVIEW_NAME}` — human-owned placement decisions.\n- `{PLACEMENT_AUDIT_NAME}` — generated read-only source-file-first audit of the currently validated placement review.\n- `{PLACEMENT_PREVIEW_NAME}` — exact deterministic publication preview.\n- `{PLACEMENT_FOLLOWUP_NAME}` — durable follow-up after placement publication.\n''',
    '''- `{REUSABLE_CONTEXTS_NAME}` — human-owned reusable Context Catalog locations, sparse assignments, and Why rationale.\n- `{PLACEMENT_INSTRUCTION_NAME}` — generated instruction for the placement reasoning pass.\n- `{PLACEMENT_PROPOSAL_NAME}` — LLM JSON describing where existing meaning belongs.\n- Step 07 is validation-only and therefore intentionally has no separate artifact.\n- `{PLACEMENT_REVIEW_NAME}` — human-owned placement decisions.\n- `{PLACEMENT_AUDIT_NAME}` — generated read-only source-file-first audit of the currently validated placement review.\n- `{PLACEMENT_PREVIEW_NAME}` — exact deterministic publication preview.\n- `{PLACEMENT_FOLLOWUP_NAME}` — durable follow-up after placement publication.\n''',
)

# ---------------------------------------------------------------------------
# CLI: add the new gate, auto-load accepted Catalog/assignments, renumber copy.
# ---------------------------------------------------------------------------
replace_once(
    "src/contextcanon/cli.py",
    '''from .onboarding_placement_review import create_or_load_placement_review, load_placement_review\n''',
    '''from .onboarding_placement_review import create_or_load_placement_review, load_placement_review\nfrom .onboarding_reusable_contexts import load_accepted_reusable_contexts, refresh_reusable_contexts\n''',
)
replace_once(
    "src/contextcanon/cli.py",
    '''from .onboarding_structure import (\n    create_or_load_structure_markdown,\n    load_onboarding_structure_proposal,\n)\n''',
    '''from .onboarding_structure import (\n    create_or_load_structure_markdown,\n    load_onboarding_structure_proposal,\n    load_structure_markdown,\n)\n''',
)

# Insert parser after structure-materialize parser.
replace_once(
    "src/contextcanon/cli.py",
    '''    onboard_structure_materialize.add_argument("--project", metavar="PATH", help="target Git repository root (default: infer from snapshot)")\n\n    onboard_placement_instruction = onboard_sub.add_parser(\n''',
    '''    onboard_structure_materialize.add_argument("--project", metavar="PATH", help="target Git repository root (default: infer from snapshot)")\n\n    onboard_reusable_contexts = onboard_sub.add_parser(\n        "reusable-contexts",\n        help="create or validate the human reusable-Context Catalog and assignment gate",\n    )\n    onboard_reusable_contexts.add_argument("snapshot", help="root of the prepared content-addressed evidence snapshot")\n    _add_workspace(onboard_reusable_contexts)\n    _add_structure_inputs(onboard_reusable_contexts)\n\n    onboard_placement_instruction = onboard_sub.add_parser(\n''',
)
# Renumber help paths.
text = read("src/contextcanon/cli.py")
text = text.replace("<workspace>/STEP-05b-placement-proposal.json", "<workspace>/STEP-06b-placement-proposal.json")
text = text.replace("<workspace>/STEP-07-placement.md", "<workspace>/STEP-08-placement.md")
write("src/contextcanon/cli.py", text)

# Materialize should hand off to reusable-contexts.
text = read("src/contextcanon/cli.py")
text = text.replace(
    'f"Run `contextcanon onboard placement-instruction {_snapshot_cli(snapshot)}`."',
    'f"Run `contextcanon onboard reusable-contexts {_snapshot_cli(snapshot)}`."',
)
write("src/contextcanon/cli.py", text)

# Insert new command handler before placement command group.
replace_once(
    "src/contextcanon/cli.py",
    '''            if args.onboard_command in {\n                "placement-instruction",\n''',
    '''            if args.onboard_command == "reusable-contexts":\n                workspace = open_onboarding_workspace(snapshot, _workspace_path(args.workspace), create=False)\n                structure_proposal_path = (\n                    Path(args.structure_proposal) if args.structure_proposal is not None else workspace.structure_proposal_path\n                )\n                structure_path = Path(args.structure) if args.structure is not None else workspace.structure_path\n                structure_proposal = load_onboarding_structure_proposal(structure_proposal_path, snapshot)\n                structure = load_structure_markdown(structure_path, structure_proposal)\n                plan, created = refresh_reusable_contexts(\n                    workspace.reusable_contexts_path,\n                    snapshot,\n                    structure_proposal.evidence_digest,\n                    structure,\n                )\n                verb = "created" if created else "validated"\n                print(f"{verb} reusable Context setup {plan.review_digest}")\n                print(f"Review file: {workspace.reusable_contexts_path}")\n                print(f"Catalog Nodes: {len(plan.catalog_packages)} · assignments: {len(plan.assignments)} · complete: {plan.is_complete}")\n                # Keep the old machine run-input cache populated for scripting/backward compatibility,\n                # but the human PLAN never asks the operator to reconstruct these values.\n                remember_run_inputs(\n                    snapshot,\n                    catalog_inputs=plan.catalog_package_inputs,\n                    owner_source_specs=plan.owner_source_specs,\n                )\n                stage = "reusable contexts accepted" if plan.is_complete else "reusable contexts review"\n                next_action = (\n                    f"Run `contextcanon onboard placement-instruction {_snapshot_cli(snapshot)}`."\n                    if plan.is_complete else\n                    f"Edit `{workspace.reusable_contexts_path.name}` (Catalog locations / sparse Assignments / Why), then rerun `contextcanon onboard reusable-contexts {_snapshot_cli(snapshot)}`."\n                )\n                update_workspace_checkpoint(\n                    workspace, snapshot,\n                    stage=stage,\n                    structure_digest=structure.structure_digest,\n                    next_action=next_action,\n                )\n                return 0\n\n            if args.onboard_command in {\n                "placement-instruction",\n''',
)

# Replace catalog/owner setup inside placement group with STEP-05-first resolution plus legacy fallback.
replace_once(
    "src/contextcanon/cli.py",
    '''                catalog = tuple(Path(path) for path in args.catalog_package)\n                catalog_inputs = tuple(args.catalog_package)\n                explicit_owner = tuple(args.owner_source) if hasattr(args, "owner_source") else ()\n                remembered_catalog, remembered_owner = remember_run_inputs(\n                    snapshot,\n                    catalog_inputs=catalog_inputs,\n                    owner_source_specs=explicit_owner,\n                )\n                if not catalog_inputs and remembered_catalog:\n                    catalog_inputs = remembered_catalog\n                    catalog = tuple(Path(path) for path in catalog_inputs)\n''',
    '''                catalog = tuple(Path(path) for path in args.catalog_package)\n                catalog_inputs = tuple(args.catalog_package)\n                explicit_owner = tuple(args.owner_source) if hasattr(args, "owner_source") else ()\n                owner_source_whys: dict[str, str] = {}\n                preaccepted_owner_sources = False\n\n                structure_proposal = load_onboarding_structure_proposal(structure_proposal_path, snapshot)\n                structure = load_structure_markdown(structure_path, structure_proposal)\n                remembered_catalog, remembered_owner = remember_run_inputs(\n                    snapshot,\n                    catalog_inputs=catalog_inputs,\n                    owner_source_specs=explicit_owner,\n                )\n                if not catalog_inputs and workspace.reusable_contexts_path.is_file():\n                    reusable = load_accepted_reusable_contexts(\n                        workspace.reusable_contexts_path,\n                        snapshot,\n                        structure_proposal.evidence_digest,\n                        structure,\n                    )\n                    catalog_inputs = reusable.catalog_package_inputs\n                    catalog = tuple(Path(path) for path in catalog_inputs)\n                    remembered_owner = reusable.owner_source_specs\n                    owner_source_whys = reusable.owner_source_whys\n                    preaccepted_owner_sources = True\n                elif not catalog_inputs and remembered_catalog:\n                    # Legacy/scripting compatibility for an onboarding started before STEP 05 existed.\n                    catalog_inputs = remembered_catalog\n                    catalog = tuple(Path(path) for path in catalog_inputs)\n''',
)

# Placement review receives durable Why and already-accepted STEP-05 decisions.
replace_once(
    "src/contextcanon/cli.py",
    '''                        owner_source_specs=owner_for_review,\n                    )\n''',
    '''                        owner_source_specs=owner_for_review,\n                        owner_source_whys=owner_source_whys,\n                        preaccepted_owner_sources=preaccepted_owner_sources,\n                    )\n''',
)

# Human-facing next actions: new artifact names and no parameter archaeology.
text = read("src/contextcanon/cli.py")
repls = {
    "STEP-05a-placement-instruction.md": "STEP-06a-placement-instruction.md",
    "STEP-05b-placement-proposal.json": "STEP-06b-placement-proposal.json",
    "STEP-07-placement.md": "STEP-08-placement.md",
    "STEP-07a-source-audit.md": "STEP-08a-source-audit.md",
    "STEP-08-placement-preview.md": "STEP-09-placement-preview.md",
    "STEP-09-placement-followup.md": "STEP-10-placement-followup.md",
    " with the exact `--catalog-package` inputs listed above": "",
    "Add any explicit owner choice once with `--owner-source TARGET_NODE_KEY=SOURCE_NODE_ID`.": "Reusable Context relationships were already accepted in STEP 05; no Source IDs need to be typed here.",
}
for old, new in repls.items():
    text = text.replace(old, new)
write("src/contextcanon/cli.py", text)

# ---------------------------------------------------------------------------
# Placement review: STEP 05 relations arrive sparse, accepted, and with Why.
# ---------------------------------------------------------------------------
replace_once(
    "src/contextcanon/onboarding_placement_review.py",
    '''from typing import Iterable\n''',
    '''from typing import Iterable, Mapping\n''',
)
replace_once(
    "src/contextcanon/onboarding_placement_review.py",
    '''    proposal_id: str | None\n\n    def to_dict(self) -> dict[str, object]:\n''',
    '''    proposal_id: str | None\n    relationship_why: str = ""\n\n    def to_dict(self) -> dict[str, object]:\n''',
)
replace_once(
    "src/contextcanon/onboarding_placement_review.py",
    '''            "proposal_id": self.proposal_id,\n        }\n''',
    '''            "proposal_id": self.proposal_id,\n            "relationship_why": self.relationship_why,\n        }\n''',
)

replace_function(
    "src/contextcanon/onboarding_placement_review.py",
    "_initial_sources",
    r'''def _initial_sources(
    proposal: OnboardingPlacementProposal,
    owner_source_specs: Iterable[str],
    *,
    owner_source_whys: Mapping[str, str] | None = None,
    preaccepted_owner_sources: bool = False,
) -> tuple[PlacementReviewSource, ...]:
    result: list[PlacementReviewSource] = []
    seen: set[tuple[str, str]] = set()
    packages = _package_by_id(proposal)
    node_keys = {node.key for node in proposal.structure.nodes}
    why_by_spec = dict(owner_source_whys or {})

    owner_pairs: dict[tuple[str, str], tuple[str, CompiledPackage]] = {}
    for spec in owner_source_specs:
        if "=" not in spec:
            raise _error("--owner-source must be TARGET_NODE_KEY=SOURCE_NODE_ID")
        target, source_id = (part.strip() for part in spec.split("=", 1))
        if target not in node_keys:
            raise _error(f"owner-selected Source references unknown target Node {target}")
        package = packages.get(source_id)
        if package is None:
            raise _error(f"owner-selected Source {source_id} was not supplied in the exact catalog")
        owner_pairs[(target, source_id)] = (spec, package)

    # Evidence-derived suggestions that duplicate an already accepted STEP-05
    # relationship do not create a second decision in Placement.
    for reuse in proposal.source_reuses:
        pair = (reuse.target_node_key, reuse.source_node_id)
        if pair in owner_pairs:
            continue
        seen.add(pair)
        result.append(
            PlacementReviewSource(
                review_id=reuse.id,
                origin="evidence-derived",
                target_node_key=reuse.target_node_key,
                decision="pending",
                source_node_id=reuse.source_node_id,
                source_name=reuse.source_name,
                source_version=reuse.source_version,
                source_normalized_digest=reuse.source_normalized_digest,
                source_package_digest=reuse.source_package_digest,
                review_note="",
                proposal_id=reuse.id,
                relationship_why=reuse.reason,
            )
        )

    for pair, (spec, package) in owner_pairs.items():
        if pair in seen:
            continue
        seen.add(pair)
        target, source_id = pair
        why = why_by_spec.get(spec, "").strip() or "Explicitly selected by the project owner."
        result.append(
            PlacementReviewSource(
                review_id="O-" + uuid.uuid4().hex[:10].upper(),
                origin="owner-selected",
                target_node_key=target,
                decision="accept" if preaccepted_owner_sources else "pending",
                source_node_id=source_id,
                source_name=package.metadata.name,
                source_version=package.metadata.version,
                source_normalized_digest=package.normalized_digest,
                source_package_digest=package.package_digest,
                review_note="",
                proposal_id=None,
                relationship_why=why,
            )
        )
    return tuple(result)
'''
)

replace_once(
    "src/contextcanon/onboarding_placement_review.py",
    '''def render_placement_review(\n    proposal: OnboardingPlacementProposal,\n    snapshot_root: Path,\n    *,\n    owner_source_specs: Iterable[str] = (),\n) -> str:\n''',
    '''def render_placement_review(\n    proposal: OnboardingPlacementProposal,\n    snapshot_root: Path,\n    *,\n    owner_source_specs: Iterable[str] = (),\n    owner_source_whys: Mapping[str, str] | None = None,\n    preaccepted_owner_sources: bool = False,\n) -> str:\n''',
)
replace_once(
    "src/contextcanon/onboarding_placement_review.py",
    '''    sources = _initial_sources(proposal, owner_source_specs)\n''',
    '''    sources = _initial_sources(\n        proposal,\n        owner_source_specs,\n        owner_source_whys=owner_source_whys,\n        preaccepted_owner_sources=preaccepted_owner_sources,\n    )\n''',
)
replace_once(
    "src/contextcanon/onboarding_placement_review.py",
    '''                    f"Review note: {source.review_note or '-'}",\n                    "",\n                    f"Exact package: `{source.source_version}` · `{source.source_package_digest}`",\n''',
    '''                    f"Why this Source applies: {source.relationship_why or '-'}",\n                    f"Review note: {source.review_note or '-'}",\n                    "",\n                    f"Exact package: `{source.source_version}` · `{source.source_package_digest}`",\n''',
)
replace_once(
    "src/contextcanon/onboarding_placement_review.py",
    '''                        "This Source was selected explicitly by the project owner from the supplied exact catalog. It is design input, not a claim derived from frozen project Evidence.",\n''',
    '''                        "This Source was selected explicitly by the project owner. When it came from STEP 05, that relationship is already accepted here and is shown only for compact traceability; it is design input, not a claim derived from frozen project Evidence.",\n''',
)
# Load Why when parsing rendered review; old reviews remain compatible.
replace_once(
    "src/contextcanon/onboarding_placement_review.py",
    '''        note = _find_line(block, "Review note: ", "Review note")\n        parsed_sources.append(\n''',
    '''        note = _find_line(block, "Review note: ", "Review note")\n        why_line = next((entry for entry in block if entry.startswith("Why this Source applies: ")), None)\n        relationship_why = "" if why_line is None else why_line[len("Why this Source applies: "):].strip()\n        if relationship_why == "-":\n            relationship_why = ""\n        parsed_sources.append(\n''',
)
replace_once(
    "src/contextcanon/onboarding_placement_review.py",
    '''                proposal_id=proposal_id,\n            )\n''',
    '''                proposal_id=proposal_id,\n                relationship_why=relationship_why,\n            )\n''',
)
replace_once(
    "src/contextcanon/onboarding_placement_review.py",
    '''def create_or_load_placement_review(\n    path: Path,\n    proposal: OnboardingPlacementProposal,\n    snapshot_root: Path,\n    *,\n    owner_source_specs: Iterable[str] = (),\n) -> tuple[OnboardingPlacementReview, bool]:\n''',
    '''def create_or_load_placement_review(\n    path: Path,\n    proposal: OnboardingPlacementProposal,\n    snapshot_root: Path,\n    *,\n    owner_source_specs: Iterable[str] = (),\n    owner_source_whys: Mapping[str, str] | None = None,\n    preaccepted_owner_sources: bool = False,\n) -> tuple[OnboardingPlacementReview, bool]:\n''',
)
replace_once(
    "src/contextcanon/onboarding_placement_review.py",
    '''        render_placement_review(proposal, snapshot_root, owner_source_specs=owner_source_specs),\n''',
    '''        render_placement_review(\n            proposal,\n            snapshot_root,\n            owner_source_specs=owner_source_specs,\n            owner_source_whys=owner_source_whys,\n            preaccepted_owner_sources=preaccepted_owner_sources,\n        ),\n''',
)

# ---------------------------------------------------------------------------
# Canonical Source relationship Why: authored locally and carried through
# immutable package imports so deep descendants can still explain the chain.
# ---------------------------------------------------------------------------
replace_once(
    "src/contextcanon/model.py",
    '''    node_path: str | None = None\n\n    @property\n''',
    '''    node_path: str | None = None\n    why: str | None = None\n\n    @property\n''',
)
replace_once(
    "src/contextcanon/model.py",
    '''class PackageDependency:\n    id: str\n    name: str\n    version: str\n    normalized_digest: str\n    package_digest: str\n''',
    '''class PackageDependency:\n    id: str\n    name: str\n    version: str\n    normalized_digest: str\n    package_digest: str\n    why: str | None = None\n''',
)

# Parser extracts an optional indented Why from each Source block.
replace_once(
    "src/contextcanon/parser.py",
    '''        result.append(\n            SourceRef(\n                attrs["id"],\n                match.group("name"),\n                attrs["version"],\n                match.group("path"),\n                normalized_digest,\n                package_digest,\n                transport,\n                transport_ref,\n                node_path,\n            )\n        )\n''',
    '''        block_end = i + 1\n        while block_end < end and SOURCE_RE.match(lines[block_end]) is None:\n            block_end += 1\n        why = None\n        for detail in lines[i + 1 : block_end]:\n            stripped = detail.strip()\n            if stripped.startswith("Why:"):\n                why = stripped[4:].strip() or None\n                break\n\n        result.append(\n            SourceRef(\n                attrs["id"],\n                match.group("name"),\n                attrs["version"],\n                match.group("path"),\n                normalized_digest,\n                package_digest,\n                transport,\n                transport_ref,\n                node_path,\n                why,\n            )\n        )\n''',
)

# Direct Source Why becomes authenticated import provenance; transitive package
# imports already carry it further through the Parent chain.
replace_once(
    "src/contextcanon/compiler.py",
    '''            compiled.imported_contexts = self._compose_imported_contexts(\n                composition_packages,\n                compiled.metadata.id,\n                compiled.metadata.name,\n            )\n''',
    '''            compiled.imported_contexts = self._compose_imported_contexts(\n                composition_packages,\n                compiled.metadata.id,\n                compiled.metadata.name,\n            )\n            source_whys = {source.id: source.why for source in parsed.sources if source.why}\n            if source_whys:\n                compiled.imported_contexts = [\n                    replace(dependency, why=source_whys.get(dependency.id, dependency.why))\n                    for dependency in compiled.imported_contexts\n                ]\n''',
)

# Package normalized provenance authenticates non-empty relationship Why.
replace_once(
    "src/contextcanon/package.py",
    '''    import_items = sorted(\n        (\n            {\n                "id": dependency.id,\n                "version": dependency.version,\n                "normalized_digest": dependency.normalized_digest,\n            }\n            for dependency in imports\n        ),\n        key=lambda item: (item["id"], item["version"], item["normalized_digest"]),\n    )\n''',
    '''    import_items = sorted(\n        (\n            {\n                **{\n                    "id": dependency.id,\n                    "version": dependency.version,\n                    "normalized_digest": dependency.normalized_digest,\n                },\n                **({"why": dependency.why} if dependency.why else {}),\n            }\n            for dependency in imports\n        ),\n        key=lambda item: (item["id"], item["version"], item["normalized_digest"]),\n    )\n''',
)
replace_once(
    "src/contextcanon/package.py",
    '''        _digest(item.get("package_digest"), f"imports[{index}].package_digest"),\n    )\n''',
    '''        _digest(item.get("package_digest"), f"imports[{index}].package_digest"),\n        None if item.get("why") is None else _string(item.get("why"), f"imports[{index}].why"),\n    )\n''',
)

# Published Source authoring carries the relationship rationale.
replace_once(
    "src/contextcanon/onboarding_placement_publish.py",
    '''        lines.extend(\n            [\n                f"- [{name}]({provenance.locator}) — `{source.source_version}`",\n                (\n''',
    '''        lines.append(f"- [{name}]({provenance.locator}) — `{source.source_version}`")\n        if source.relationship_why:\n            lines.append(f"  Why: {_safe_line(source.relationship_why, f'Source {source.review_id} relationship Why')}")\n        lines.extend(\n            [\n                (\n''',
)

# Generated Official Context shows the Why for direct or inherited imported Contexts.
replace_once(
    "src/contextcanon/render.py",
    '''            lines.append(\n                f"- **{dependency.name}** — `{dependency.version}` — {relation} — "\n                f"[inspect accepted carrier]({link})"\n            )\n''',
    '''            why = f" — Why: {dependency.why}" if dependency.why else ""\n            lines.append(\n                f"- **{dependency.name}** — `{dependency.version}` — {relation}{why} — "\n                f"[inspect accepted carrier]({link})"\n            )\n''',
)
# Machine YAML keeps the rationale inspectable too.
replace_once(
    "src/contextcanon/render.py",
    '''                f"    package_digest: {q(dependency.package_digest)}",\n            ])\n''',
    '''                f"    package_digest: {q(dependency.package_digest)}",\n            ])\n            if dependency.why:\n                lines.append(f"    why: {q(dependency.why)}")\n''',
)

# ---------------------------------------------------------------------------
# Reset model: STEP 05 config is a real human gate; renumber downstream steps.
# ---------------------------------------------------------------------------
replace_once(
    "src/contextcanon/onboarding_reset.py",
    '''    PLACEMENT_AUDIT_NAME,\n''',
    '''    PLACEMENT_AUDIT_NAME,\n    REUSABLE_CONTEXTS_NAME,\n''',
)
replace_once(
    "src/contextcanon/onboarding_reset.py",
    '''    STRUCTURE_PREVIEW_NAME: 4,\n    PLACEMENT_INSTRUCTION_NAME: 5,\n    PLACEMENT_PROPOSAL_NAME: 5,\n    PLACEMENT_REVIEW_NAME: 7,\n    PLACEMENT_AUDIT_NAME: 7,\n    PLACEMENT_PREVIEW_NAME: 8,\n    PLACEMENT_FOLLOWUP_NAME: 9,\n''',
    '''    STRUCTURE_PREVIEW_NAME: 4,\n    REUSABLE_CONTEXTS_NAME: 5,\n    PLACEMENT_INSTRUCTION_NAME: 6,\n    PLACEMENT_PROPOSAL_NAME: 6,\n    PLACEMENT_REVIEW_NAME: 8,\n    PLACEMENT_AUDIT_NAME: 8,\n    PLACEMENT_PREVIEW_NAME: 9,\n    PLACEMENT_FOLLOWUP_NAME: 10,\n''',
)
replace_once(
    "src/contextcanon/onboarding_reset.py",
    '''    step = 4 if argv[1] == "structure-materialize" else 9\n''',
    '''    step = 4 if argv[1] == "structure-materialize" else 10\n''',
)
replace_once(
    "src/contextcanon/onboarding_reset.py",
    '''    if from_step < 2 or from_step > 9:\n        raise _error("--from must be a numbered onboarding step from 2 through 9; frozen Evidence is intentionally preserved")\n''',
    '''    if from_step < 2 or from_step > 10:\n        raise _error("--from must be a numbered onboarding step from 2 through 10; frozen Evidence is intentionally preserved")\n''',
)
replace_once(
    "src/contextcanon/onboarding_reset.py",
    '''    if 9 in selected_steps:\n''',
    '''    if 10 in selected_steps:\n''',
)
# The new plan renderer handles reset checkboxes from the stage; old checklist rewrite is obsolete.
replace_function(
    "src/contextcanon/onboarding_reset.py",
    "_rewrite_plan_after_reset",
    r'''def _rewrite_plan_after_reset(workspace_root: Path, snapshot_root: Path, from_step: int) -> None:
    # update_workspace_checkpoint already regenerates the integrated step/command surface
    # from the reset stage. Keep this compatibility hook intentionally empty.
    return None
''',
)

# ---------------------------------------------------------------------------
# Placement instruction: selected reusable Contexts are established before the
# LLM pass. Keep catalog semantics visible but stop asking it to discover the
# already accepted relationships again.
# ---------------------------------------------------------------------------
replace_once(
    "src/contextcanon/onboarding_placement_instruction.py",
    '''            "Compare generic-looking project guidance with every verified immutable package below before proposing a duplicate local Rule. Use `source_reuses` only when one exact package materially covers evidence-backed guidance for one accepted Node. Copy the exact package identity.",\n''',
    '''            "These verified reusable packages were prepared before placement. Compare generic-looking project guidance with them before proposing a duplicate local Rule. Reusable Context assignment itself is a separate human gate; do not invent or re-decide owner-selected relationships in this LLM pass.",\n''',
)
replace_once(
    "src/contextcanon/onboarding_placement_instruction.py",
    '''        "14. Compare likely generic practices with every supplied reusable Source package before proposing a duplicate local Rule. A Source reuse is a separate Evidence-derived proposal entry; project-specific deltas may still remain local.",\n''',
    '''        "14. Compare likely generic practices with every supplied reusable Source package before proposing a duplicate local Rule. Reusable Context assignments are reviewed before this pass; project-specific deltas may still remain local. Return `source_reuses` only for a genuinely new Evidence-derived relationship not already established by the human reusable-Context gate.",\n''',
)

# ---------------------------------------------------------------------------
# Focused tests for the new human gate, integrated PLAN, and Source Why.
# ---------------------------------------------------------------------------
write(
    "tests/test_onboarding_reusable_contexts.py",
    r'''from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from contextcanon.compiler import Compiler
from contextcanon.onboarding_reusable_contexts import (
    ASSIGNMENTS_END,
    ASSIGNMENTS_START,
    CATALOG_END,
    CATALOG_START,
    load_accepted_reusable_contexts,
    refresh_reusable_contexts,
)
from contextcanon.onboarding_structure import HumanStructureNode, HumanStructurePlan
from contextcanon.outputs import write_outputs
from contextcanon.parser import parse_node


class ReusableContextsTests(unittest.TestCase):
    def _structure(self) -> HumanStructurePlan:
        return HumanStructurePlan(
            evidence_digest="a" * 64,
            proposal_digest="b" * 64,
            nodes=(
                HumanStructureNode("N-001", "AI Workstation", ".", "current", None, "N-001"),
                HumanStructureNode("N-002", "Bootstrap", "bootstrap", "current", "N-001", "N-002"),
            ),
            fixed_markdown=(),
            structure_digest="c" * 64,
        )

    def _catalog(self, root: Path) -> Path:
        node = root / "catalog" / "development-workflow"
        node.mkdir(parents=True)
        (root / "catalog" / ".git").mkdir()
        (node / "CONTEXT.src.md").write_text(
            "# Development Workflow — Local Context Source\n"
            '<!-- ctx:node id="workflow-node" version="0.2.0-draft" -->\n\n'
            "## Local Rules\n\n"
            "### Development\n\n"
            "- **Review before merge:** Keep changes reviewable.\n"
            "  Why: Humans should explicitly accept important changes.\n"
            '  <!-- ctx:rule id="WF-001" -->\n',
            encoding="utf-8",
        )
        compiled = Compiler(root / "catalog").compile(node)
        write_outputs(compiled)
        return root / "catalog"

    def test_sparse_human_gate_discovers_catalog_and_persists_assignment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot = root / ("a" * 64)
            snapshot.mkdir()
            workspace_file = root / "STEP-05-reusable-contexts.md"
            structure = self._structure()
            catalog = self._catalog(root)

            first, created = refresh_reusable_contexts(workspace_file, snapshot, "a" * 64, structure)
            self.assertTrue(created)
            self.assertFalse(first.is_complete)
            text = workspace_file.read_text(encoding="utf-8")
            self.assertIn("# STEP 05 — Reusable Contexts", text)
            self.assertNotIn("workflow-node", text)

            text = text.replace(
                CATALOG_START + "\n" + CATALOG_END,
                CATALOG_START + f"\n- `{catalog}`\n" + CATALOG_END,
            )
            text = text.replace("Decision: `pending`", "Decision: `accept`")
            assignment = (
                "- **AI Workstation** (`.`) ← **Development Workflow** (`0.2.0-draft`)\n"
                "  Why: Shared development workflow applies to the whole project.\n"
            )
            text = text.replace(
                ASSIGNMENTS_START + "\n" + ASSIGNMENTS_END,
                ASSIGNMENTS_START + "\n" + assignment + ASSIGNMENTS_END,
            )
            workspace_file.write_text(text, encoding="utf-8")

            second, created = refresh_reusable_contexts(workspace_file, snapshot, "a" * 64, structure)
            self.assertFalse(created)
            self.assertTrue(second.is_complete)
            self.assertEqual(second.owner_source_specs, ("N-001=workflow-node",))
            self.assertEqual(
                second.owner_source_whys["N-001=workflow-node"],
                "Shared development workflow applies to the whole project.",
            )
            accepted = load_accepted_reusable_contexts(workspace_file, snapshot, "a" * 64, structure)
            self.assertEqual(len(accepted.catalog_packages), 1)
            state = json.loads((snapshot / "reusable-contexts.json").read_text(encoding="utf-8"))
            self.assertEqual(state["assignments"][0]["source_node_id"], "workflow-node")

    def test_source_why_is_parsed_from_authored_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".git").mkdir()
            source = root / "shared"
            consumer = root / "consumer"
            source.mkdir()
            consumer.mkdir()
            (source / "CONTEXT.src.md").write_text(
                "# Shared — Local Context Source\n"
                '<!-- ctx:node id="shared" version="1.0.0" -->\n',
                encoding="utf-8",
            )
            (consumer / "CONTEXT.src.md").write_text(
                "# Consumer — Local Context Source\n"
                '<!-- ctx:node id="consumer" version="1.0.0" -->\n\n'
                "## Sources\n\n"
                "- [Shared](../shared) — `1.0.0`\n"
                "  Why: Shared policy applies to every consumer here.\n"
                '  <!-- ctx:source id="shared" version="1.0.0" -->\n',
                encoding="utf-8",
            )
            parsed = parse_node(consumer, root)
            self.assertEqual(parsed.sources[0].why, "Shared policy applies to every consumer here.")
            compiled = Compiler(root).compile(consumer)
            self.assertEqual(compiled.imported_contexts[0].why, "Shared policy applies to every consumer here.")
            self.assertIn("Why: Shared policy applies to every consumer here.", compiled.official_markdown)
            manifest = json.loads(compiled.package_manifest)
            self.assertEqual(manifest["imports"][0]["why"], "Shared policy applies to every consumer here.")
'''
)

# PLAN regression: integrated checkbox/explanation/command chapters, no CLI archaeology.
write(
    "tests/test_onboarding_plan_steps.py",
    r'''from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from contextcanon.onboarding_workspace import _exact_commands, open_onboarding_workspace


class OnboardingPlanStepsTests(unittest.TestCase):
    def test_plan_keeps_checkbox_explanation_and_command_together(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".git").mkdir()
            snapshot = root / ".context" / "onboarding" / ("a" * 64)
            snapshot.mkdir(parents=True)
            workspace = open_onboarding_workspace(snapshot, create=True)
            text = _exact_commands(
                workspace,
                snapshot,
                ("/legacy/catalog/package",),
                ("N-001=opaque-id",),
                completed={1, 2, 3, 4},
            )
            self.assertIn("### STEP 05 — Reusable Contexts", text)
            self.assertIn("where reusable external Context Nodes can be found", text)
            self.assertIn("contextcanon onboard reusable-contexts", text)
            self.assertIn("### STEP 06 — Placement proposal", text)
            self.assertIn("STEP-06a-placement-instruction.md", text)
            self.assertIn("STEP-08-placement.md", text)
            self.assertIn("STEP-10-placement-followup.md", text)
            self.assertNotIn("--catalog-package", text)
            self.assertNotIn("--owner-source", text)
            self.assertNotIn("opaque-id", text)
            self.assertIn("- [x] **Done**", text)
            self.assertIn("- [ ] **Done**", text)
'''
)

# Update durable framework PLAN with a final owner-UX block; generated self-context
# will be rebuilt by the quality workflow after tests pass.
plan = read("PLAN.md")
block = r'''

## Final owner-UX block: reusable Context setup and novice-safe runbook

**Status: ACTIVE — implementation under verification; owner acceptance pending.**

Purpose: remove the last onboarding step that required a human to remember Catalog paths, target Node keys, Source Node IDs and one-time CLI syntax. Reusable Context composition becomes its own human gate after project shelves are materialized and before placement reasoning begins.

- [x] 1. Add `STEP-05-reusable-contexts.md` as the single human surface for reusable Context Catalog locations, sparse Source→project-Node assignments, and a durable Why rationale; keep IDs/digests generated and read-only.
- [x] 2. Discover verified compiled Context Nodes from one or more Catalog directories, allow empty/no-reuse acceptance, and persist exact machine state so subsequent placement commands need no repeated Catalog/owner parameters.
- [x] 3. Move reusable Context decisions before the placement LLM; preaccepted STEP-05 relationships appear only as compact traceability in placement review, while duplicate LLM Source suggestions do not create a second owner decision.
- [x] 4. Publish the Source relationship Why into local `CONTEXT.src.md` and carry it as authenticated import provenance so generated descendants can explain not only where inherited Context came from but why the reusable Context was attached.
- [x] 5. Renumber downstream human artifacts to `STEP-06...STEP-10`, retain migration aliases for prior workspace filenames, and extend reset semantics through step 10.
- [x] 6. Replace the split top checklist / lower command manual with one integrated PLAN chapter per numbered STEP: same title vocabulary as the artifact names, novice-oriented subject/action explanation, completion checkbox, exact command, and artifact guidance in one place.
- [ ] 7. Run focused regressions, complete deterministic suite, self-build/check, diff hygiene and cleanup; then hand the exact clean PR head to the project owner for the final real `ai-workstation` onboarding/readability test. PR remains draft/unmerged until explicit owner approval.
'''
if "## Final owner-UX block: reusable Context setup and novice-safe runbook" not in plan:
    write("PLAN.md", plan.rstrip() + block + "\n")
