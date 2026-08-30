from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

from contextcanon.compiler import Compiler, discover_nodes
from contextcanon.onboarding_placement import load_onboarding_placement_proposal
from contextcanon.onboarding_placement_review import load_placement_review
from contextcanon.onboarding_structure_materialize import (
    materialize_structure_skeletons,
    preview_structure_materialization,
)
from contextcanon.outputs import check_outputs
from contextcanon.parser import parse_node

AIW = Path("/tmp/ai-workstation-real-review")
EXPECTED_EVIDENCE = "2a926bf353b252db4039e5c4b63b39abad6bab46c11982e88b3eb17e19cf203d"
ROOT_ID = "aea56adf-2a26-43f0-b712-3bbeab7a3097"
WORKFLOW_ID = "c4c94726-3cc7-4df6-b779-72bbf9c06f40"
WORKFLOW_PACKAGE = "1d82c87e4f4140791f354c9d9479df845eb65c13fce1c664ecb05bec9532c8eb"


def run(*args: str, cwd: Path | None = None) -> str:
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"command failed ({result.returncode}): {' '.join(args)}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    return result.stdout.strip()


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_p033(block: str) -> str:
    block = block.replace(
        "## P-033 — Clarify repository versus Python project versioning",
        "## P-033 — Keep project version aligned with release version",
        1,
    )
    block = block.replace("Decision: `pending`", "Decision: `accept`", 1)
    block = block.replace("Kind: `unresolved`", "Kind: `rule`", 1)
    block = block.replace("Action: `keep`", "Action: `promote`", 1)
    block = block.replace(
        "Review note: -",
        "Review note: Owner resolved the Evidence ambiguity during onboarding review: raise pyproject.toml to at least the current CHANGELOG release and keep both release versions aligned from then on.",
        1,
    )
    start = block.index("### Maintained meaning\n")
    end = block.index("### Proposal rationale\n", start)
    maintained = (
        "### Maintained meaning\n\n"
        "Statement: Keep the project version in `pyproject.toml` aligned with the release version documented in `CHANGELOG.md`; changelog notes for a release belong under that same version.\n"
        "Why: The project should maintain one coherent release version instead of independent stale version streams.\n"
        "Wording: `synthesized`\n\n"
    )
    return block[:start] + maintained + block[end:]


def main() -> None:
    repo = Path.cwd()
    if not AIW.is_dir():
        raise SystemExit("real review harness checkout is missing")
    snapshot = AIW / ".context" / "onboarding" / EXPECTED_EVIDENCE
    workspace = AIW / "contextcanon-onboarding"
    structure_proposal = workspace / "structure-proposal.json"
    structure_md = workspace / "structure.md"
    placement_proposal = workspace / "placement-proposal.json"
    placement_md = workspace / "placement.md"

    # Isolate reusable Source provenance from runtime helper edits in this checkout.
    catalog_repo = Path("/tmp/contextcanon-real-catalog")
    shutil.rmtree(catalog_repo, ignore_errors=True)
    origin = run("git", "remote", "get-url", "origin", cwd=repo)
    head = run("git", "rev-parse", "HEAD", cwd=repo)
    run("git", "clone", "-q", origin, str(catalog_repo))
    run("git", "checkout", "-q", head, cwd=catalog_repo)
    catalog = catalog_repo / "nodes" / "library" / "development-workflow"
    package = json.loads((catalog / ".context" / "package.json").read_text(encoding="utf-8"))
    if package["digests"]["package"] != WORKFLOW_PACKAGE:
        raise SystemExit(f"unexpected Development Workflow package: {package['digests']['package']}")

    # Snapshot every frozen Evidence-covered source byte before ContextCanon mutation.
    manifest = json.loads((snapshot / "manifest.json").read_text(encoding="utf-8"))
    evidence_before = {entry["path"]: digest(AIW / entry["path"]) for entry in manifest["files"]}

    # Structure continuation: exact accepted root stays, seven child/group skeletons are created once.
    structure_preview = preview_structure_materialization(
        snapshot, structure_proposal, structure_md, project_root=AIW
    )
    existing = [item for item in structure_preview.items if item.status == "existing"]
    create = [item for item in structure_preview.items if item.status == "create"]
    if len(existing) != 1 or existing[0].path != "." or existing[0].existing_node_id != ROOT_ID:
        raise SystemExit(f"root continuation identity mismatch: {existing}")
    if len(create) != 7:
        raise SystemExit(f"expected seven child/group nodes, got {len(create)}")
    materialize_structure_skeletons(structure_preview)
    second_structure_preview = preview_structure_materialization(
        snapshot, structure_proposal, structure_md, project_root=AIW
    )
    if any(item.status != "existing" for item in second_structure_preview.items):
        raise SystemExit("structure materialization is not idempotent")
    child_ids_before = {
        item.path: parse_node(AIW / item.path, AIW).metadata.id
        for item in second_structure_preview.items if item.path != "."
    }

    # Human review: accept the Evidence-derived classifications, explicitly accept the
    # owner-selected Source, and resolve only the one known version ambiguity as owner input.
    review_text = placement_md.read_text(encoding="utf-8")
    review_text = review_text.replace("Decision: `pending`", "Decision: `accept`")
    p033_start = review_text.index("## P-033 —")
    source_start = review_text.index("# Reusable Sources", p033_start)
    review_text = review_text[:p033_start] + replace_p033(review_text[p033_start:source_start]) + review_text[source_start:]
    placement_md.write_text(review_text, encoding="utf-8", newline="\n")

    proposal = load_onboarding_placement_proposal(
        placement_proposal,
        snapshot,
        structure_proposal,
        structure_md,
        catalog_package_roots=[catalog],
    )
    review = load_placement_review(placement_md, proposal, snapshot)
    if not review.is_complete:
        raise SystemExit("human review should be complete")
    p033 = next(item for item in review.items if item.proposal_id == "P-033")
    if p033.kind != "rule" or p033.action != "promote" or p033.decision != "accept":
        raise SystemExit("owner version decision did not round-trip as a Rule")
    sources = [source for source in review.sources if source.source_node_id == WORKFLOW_ID]
    if len(sources) != 1 or sources[0].origin != "owner-selected" or sources[0].decision != "accept":
        raise SystemExit("owner-selected Development Workflow did not round-trip")

    # Exact preview before mutation.
    preview_output = run(
        "contextcanon", "onboard", "placement-preview", str(snapshot),
        "--workspace", str(workspace), "--project", str(AIW),
        "--catalog-package", str(catalog), cwd=AIW,
    )
    preview_md = (workspace / "placement-preview.md").read_text(encoding="utf-8")
    if "Review complete: **yes**" not in preview_md:
        raise SystemExit("publication preview did not recognize complete review")
    if "Development Workflow" not in preview_md or "owner-selected" not in preview_md:
        raise SystemExit("publication preview lost owner-selected Source provenance")
    if "compose/goose" not in preview_md or "../../README.md" not in preview_md:
        raise SystemExit("real preview did not expose child-node README routing")
    if (snapshot / "placement-acceptance.json").exists():
        raise SystemExit("preview mutated acceptance state")

    # Explicit controlled publication in the disposable clone.
    publish_output = run(
        "contextcanon", "onboard", "placement-publish", str(snapshot),
        "--workspace", str(workspace), "--project", str(AIW),
        "--catalog-package", str(catalog), cwd=AIW,
    )
    acceptance = snapshot / "placement-acceptance.json"
    payload = json.loads(acceptance.read_text(encoding="utf-8"))

    # All original project Evidence remains byte-identical; cleanup is intentionally separate.
    evidence_after = {path: digest(AIW / path) for path in evidence_before}
    if evidence_after != evidence_before:
        changed = [path for path in evidence_before if evidence_before[path] != evidence_after[path]]
        raise SystemExit(f"publication changed frozen project Markdown/config: {changed}")

    # Existing identity/content survives; all child identities are stable.
    root = parse_node(AIW, AIW)
    if root.metadata.id != ROOT_ID:
        raise SystemExit(f"root Node ID changed: {root.metadata.id}")
    root_source = (AIW / "CONTEXT.src.md").read_text(encoding="utf-8")
    if "AIW-EXISTING-001" not in root_source or "Existing accepted root context" not in root_source:
        raise SystemExit("unrelated authored root content was lost")
    child_ids_after = {
        path: parse_node(AIW / path, AIW).metadata.id for path in child_ids_before
    }
    if child_ids_after != child_ids_before:
        raise SystemExit("child Node identity changed during placement publication")

    # Representative materialization across all semantic surfaces.
    bootstrap = (AIW / "bootstrap" / "CONTEXT.src.md").read_text(encoding="utf-8")
    windows = (AIW / "bootstrap" / "windows" / "CONTEXT.src.md").read_text(encoding="utf-8")
    linux = (AIW / "bootstrap" / "linux" / "CONTEXT.src.md").read_text(encoding="utf-8")
    aiw_src = (AIW / "bin" / "CONTEXT.src.md").read_text(encoding="utf-8")
    runtimes = (AIW / "compose" / "CONTEXT.src.md").read_text(encoding="utf-8")
    goose = (AIW / "compose" / "goose" / "CONTEXT.src.md").read_text(encoding="utf-8")
    webui = (AIW / "compose" / "open-webui" / "CONTEXT.src.md").read_text(encoding="utf-8")
    assertions = [
        ("Bootstrap owns the repeatable workstation foundation", bootstrap),
        ("Preserve idempotency", bootstrap),
        ("Windows and WSL bootstrap owns", windows),
        ("Work inside the WSL Linux filesystem", linux),
        ("stable user interface for installation and operation", aiw_src),
        ("Resource: `../README.md`", aiw_src),
        ("Secrets must not be committed", runtimes),
        ("Resource: `../SECURITY.md`", runtimes),
        ("exactly one explicitly registered host workspace", goose),
        ("Resource: `../../README.md`", goose),
        ("Open WebUI is a persistent Docker service", webui),
        ("Resource: `../../README.md`", webui),
        ("Keep project version in `pyproject.toml` aligned", root_source),
    ]
    missing = [needle for needle, haystack in assertions if needle not in haystack]
    if missing:
        raise SystemExit(f"representative publication assertions missing: {missing}")

    # Source is exact, pinned and transport provenance points to a durable Git commit,
    # never the developer checkout path.
    source = next(source for source in root.sources if source.id == WORKFLOW_ID)
    if source.package_digest != WORKFLOW_PACKAGE or source.transport != "git":
        raise SystemExit("Development Workflow Source is not exact/pinned Git provenance")
    if not source.transport_ref or not re.fullmatch(r"[0-9a-f]{40}", source.transport_ref):
        raise SystemExit(f"invalid Source Git ref: {source.transport_ref}")
    if source.node_path != "nodes/library/development-workflow":
        raise SystemExit(f"unexpected Source node path: {source.node_path}")
    if str(repo) in root_source or str(catalog_repo) in root_source:
        raise SystemExit("transient ContextCanon checkout path leaked into AI Workstation truth")

    # Follow-ups preserve accepted state/plan/ordinary docs, but P-033 is now materialized
    # as the human-resolved local Rule rather than an unresolved follow-up.
    followup_kinds = {item["kind"] for item in payload["followups"]}
    if not {"state", "plan", "ordinary-documentation"}.issubset(followup_kinds):
        raise SystemExit(f"missing durable follow-up kinds: {followup_kinds}")
    if any(item["proposal_id"] == "P-033" for item in payload["followups"]):
        raise SystemExit("resolved version question incorrectly remained a follow-up")
    followup_md = (workspace / "placement-followup.md").read_text(encoding="utf-8")
    if "Local model integration is intentionally deferred" not in followup_md:
        raise SystemExit("project plan disappeared from visible follow-up")

    # Every generated Node package must be exact after publication.
    compiler = Compiler(AIW)
    drift: dict[str, list[str]] = {}
    for node in discover_nodes(AIW):
        current = check_outputs(compiler.compile(node))
        if current:
            drift[node.relative_to(AIW).as_posix() or "."] = current
    if drift:
        raise SystemExit(f"generated drift after real publication: {drift}")

    # Second preview/publication is idempotent.
    run(
        "contextcanon", "onboard", "placement-preview", str(snapshot),
        "--workspace", str(workspace), "--project", str(AIW),
        "--catalog-package", str(catalog), cwd=AIW,
    )
    second_preview = (workspace / "placement-preview.md").read_text(encoding="utf-8")
    if "No `CONTEXT.src.md` delta" not in second_preview:
        raise SystemExit("second real preview is not source-idempotent")
    acceptance_before = acceptance.read_bytes()
    second_publish = run(
        "contextcanon", "onboard", "placement-publish", str(snapshot),
        "--workspace", str(workspace), "--project", str(AIW),
        "--catalog-package", str(catalog), cwd=AIW,
    )
    if acceptance.read_bytes() != acceptance_before:
        raise SystemExit("second publication changed exact acceptance record")

    report = {
        "schema": "contextcanon/real-world-validation/v1",
        "ai_workstation_commit": run("git", "rev-parse", "HEAD", cwd=AIW),
        "evidence_digest": EXPECTED_EVIDENCE,
        "structure": {
            "existing_root_id": ROOT_ID,
            "created_child_nodes": 7,
            "child_node_ids_stable": True,
        },
        "placement": {
            "proposal_items": len(proposal.items),
            "human_review_complete": True,
            "owner_version_question_resolved_as_rule": True,
            "owner_selected_source": WORKFLOW_ID,
            "owner_selected_source_package": WORKFLOW_PACKAGE,
            "followup_kinds": sorted(followup_kinds),
        },
        "publication": {
            "evidence_bytes_unchanged": True,
            "root_identity_preserved": True,
            "unrelated_root_content_preserved": True,
            "cross_directory_topic_routing_verified": True,
            "source_git_provenance_verified": True,
            "zero_generated_drift": True,
            "second_preview_publish_idempotent": True,
            "acceptance_digest": hashlib.sha256(acceptance_before).hexdigest(),
        },
        "commands": {
            "preview": preview_output,
            "publish": publish_output,
            "second_publish": second_publish,
        },
    }
    (repo / "_real-ai-workstation-publication-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
