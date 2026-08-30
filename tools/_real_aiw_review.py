from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from contextcanon.compiler import Compiler
from contextcanon.onboarding import prepare_onboarding_evidence
from contextcanon.onboarding_placement import PLACEMENT_PROPOSAL_SCHEMA
from contextcanon.onboarding_structure import STRUCTURE_PROPOSAL_SCHEMA, create_or_load_structure_markdown, load_structure_markdown, load_onboarding_structure_proposal
from contextcanon.outputs import write_outputs

EXPECTED_EVIDENCE = "2a926bf353b252db4039e5c4b63b39abad6bab46c11982e88b3eb17e19cf203d"
AIW_COMMIT = "4106fec3f7726d6c9bfedd70d30d9ed025b7c166"
ROOT_ID = "aea56adf-2a26-43f0-b712-3bbeab7a3097"
WORKFLOW_ID = "c4c94726-3cc7-4df6-b779-72bbf9c06f40"
HASH = {
    ".github/workflows/validate.yml": "441c086b51bb2fe56877df3529d80a3d1f8dabdde677602ad87fc1b6d171ddcd",
    "CHANGELOG.md": "2a6941b47ab2a411f599203c6f9487430ae2f553ca6e381012945ad7ce9bdb54",
    "CONTRIBUTING.md": "ca4cbe961352bb09e2fad6be95881db2210ab194991cdcef7956a832cc224b73",
    "README.md": "32f00926fa7ea3d2a228424ae6062b61ca58a7f30c965197ee56478d2ebd67b8",
    "SECURITY.md": "8e49872fd096e6aefdf799b7120f7996d16696b336292b540bc50b643ea0b542",
    "docs/PATCH-0.4.7.md": "c06a08c9d10b281c744c2ac75bdd0a1fb0daf989ff89805db16ab7e91d00bce7",
    "docs/architecture.md": "359bb341fccb339f30dfd48365dc097b741292520fcdd4fefcd7fb65238bc311",
    "docs/clean-room-test.md": "96bb9a79a5fa3205fa0bd1097ced3f9dc5f3bb169a677903d32a2892aaaffa0c",
    "docs/repository-setup.md": "1d54e84bfb37512c7fa395f78427a4924cd1702020bddee5d7bddb6095a0becc",
    "docs/troubleshooting.md": "025b723d0680d83f67d42bea2c49d50306153ffd3dad6f8ac760ed6123778cc8",
    "pyproject.toml": "4bdee0e71f4dfccb3245ba1efe17d5c47d830b17f5ee7c7c963d36a6d33f6dff",
}


def ev(path: str, start: int, end: int) -> dict[str, object]:
    return {"path": path, "sha256": HASH[path], "start_line": start, "end_line": end}


def run(*args: str, cwd: Path | None = None) -> str:
    return subprocess.run(args, cwd=cwd, check=True, text=True, capture_output=True).stdout.strip()


def main() -> None:
    root = Path.cwd()
    aiw = Path("/tmp/ai-workstation-real-review")
    shutil.rmtree(aiw, ignore_errors=True)
    run("git", "clone", "-q", "https://github.com/SomeSunlight/ai-workstation.git", str(aiw))
    run("git", "checkout", "-q", AIW_COMMIT, cwd=aiw)
    prepared = prepare_onboarding_evidence(aiw)
    if prepared.evidence_digest != EXPECTED_EVIDENCE:
        raise SystemExit(f"Evidence mismatch: {prepared.evidence_digest}")
    snapshot = prepared.snapshot_root
    workspace = aiw / "contextcanon-onboarding"
    workspace.mkdir(exist_ok=True)

    # Previously accepted root identity: keep it exact and prove unrelated authored
    # content survives structure materialization and later placement publication.
    (aiw / "CONTEXT.src.md").write_text(
        "# ai-workstation — Local Context Source\n"
        f'<!-- ctx:node id="{ROOT_ID}" version="0.1.0" -->\n\n'
        "## Overview\n\n"
        "Existing accepted root context remains authored outside placement-managed blocks.\n\n"
        "## Rules\n\n"
        "### Existing baseline\n\n"
        "- **Preserve accepted root identity:** Existing adopted Context remains present while structure-first onboarding continues.\n"
        "  Why: The real continuation test must not turn re-onboarding into first adoption.\n"
        '  <!-- ctx:rule id="AIW-EXISTING-001" -->\n',
        encoding="utf-8",
    )
    write_outputs(Compiler(aiw).compile(aiw))

    structure = {
        "schema": STRUCTURE_PROPOSAL_SCHEMA,
        "evidence_digest": EXPECTED_EVIDENCE,
        "nodes": [
            {"key":"N-001","name":"AI Workstation","parent_key":None,"suggested_path":".","lifecycle":"current","purpose":"Project-wide workstation context.","rationale":"The evidence describes one reproducible workstation project spanning host setup, operator interface and application runtimes.","confidence":"high","evidence":[ev("README.md",1,8),ev("docs/architecture.md",3,13)]},
            {"key":"N-002","name":"Bootstrap","parent_key":"N-001","suggested_path":"bootstrap","lifecycle":"current","purpose":"Workstation foundation and restartable installation.","rationale":"Windows/WSL, Linux bootstrap and Ansible host configuration form the repeatable host foundation.","confidence":"high","evidence":[ev("README.md",268,285),ev("docs/architecture.md",3,10)]},
            {"key":"N-003","name":"Windows and WSL bootstrap","parent_key":"N-002","suggested_path":"bootstrap/windows","lifecycle":"current","purpose":"Windows, WSL, reboot continuation and distribution lifecycle.","rationale":"The architecture assigns this responsibility to PowerShell and the user documentation exposes the Windows entry point.","confidence":"high","evidence":[ev("docs/architecture.md",3,6),ev("README.md",10,32)]},
            {"key":"N-004","name":"Linux bootstrap","parent_key":"N-002","suggested_path":"bootstrap/linux","lifecycle":"current","purpose":"Minimal Linux runtime plus Ansible-managed host state.","rationale":"The accepted owner structure groups Linux bootstrap and the Ansible host foundation below Bootstrap.","confidence":"high","evidence":[ev("docs/architecture.md",3,8),ev("README.md",276,285)]},
            {"key":"N-005","name":"aiw operator interface","parent_key":"N-001","suggested_path":"bin","lifecycle":"current","purpose":"Stable interactive and scriptable operator entry point.","rationale":"The architecture explicitly assigns aiw the stable installation/operation interface and README makes it the human-friendly entry point.","confidence":"high","evidence":[ev("docs/architecture.md",8,10),ev("README.md",35,72)]},
            {"key":"N-006","name":"Containerized application runtimes","parent_key":"N-001","suggested_path":"compose","lifecycle":"current","purpose":"Cross-runtime Compose, mount, network, resource and security concerns.","rationale":"Compose owns runtime service boundaries shared by separately managed Goose and Open WebUI runtimes.","confidence":"high","evidence":[ev("docs/architecture.md",8,10),ev("SECURITY.md",3,10)]},
            {"key":"N-007","name":"Goose","parent_key":"N-006","suggested_path":"compose/goose","lifecycle":"current","purpose":"Isolated short-lived Goose sessions and delegated workspaces.","rationale":"Goose has a distinct lifecycle and security boundary with exactly one selected writable workspace.","confidence":"high","evidence":[ev("README.md",94,139),ev("SECURITY.md",12,26)]},
            {"key":"N-008","name":"Open WebUI","parent_key":"N-006","suggested_path":"compose/open-webui","lifecycle":"current","purpose":"Persistent localhost Open WebUI service and its data/provider boundary.","rationale":"Open WebUI is a separately managed persistent service with its own lifecycle, storage and network boundary.","confidence":"high","evidence":[ev("README.md",142,194),ev("SECURITY.md",28,40)]},
        ],
        "knowledge_bodies": [
            {"key":"K-001","kind":"project-documentation","name":"Architecture documentation","suggested_node_key":"N-001","paths":["docs/architecture.md"],"purpose":"Architecture responsibilities and installation authority.","rationale":"Keep the architecture document as project-owned Markdown while routing to it where useful.","confidence":"high","evidence":[ev("docs/architecture.md",1,13)]},
            {"key":"K-002","kind":"project-documentation","name":"User operation and recovery documentation","suggested_node_key":"N-001","paths":["README.md","docs/clean-room-test.md","docs/troubleshooting.md"],"purpose":"User, operator and recovery guidance.","rationale":"These are natural task documents rather than Node hierarchy entries.","confidence":"high","evidence":[ev("README.md",1,365),ev("docs/clean-room-test.md",1,58),ev("docs/troubleshooting.md",1,145)]},
            {"key":"K-003","kind":"project-documentation","name":"Security policy","suggested_node_key":"N-006","paths":["SECURITY.md"],"purpose":"Detailed runtime security and vulnerability guidance.","rationale":"Security stays mutable project-owned Markdown in this real test; task context routes to it instead of duplicating the whole policy.","confidence":"high","evidence":[ev("SECURITY.md",1,46)]},
            {"key":"K-004","kind":"project-documentation","name":"Contribution and release record","suggested_node_key":"N-001","paths":["CONTRIBUTING.md","CHANGELOG.md","docs/repository-setup.md","docs/PATCH-0.4.7.md"],"purpose":"Contribution requirements and historical release/setup records.","rationale":"Placement will separate durable governance from history rather than converting this corpus wholesale.","confidence":"high","evidence":[ev("CONTRIBUTING.md",1,8),ev("CHANGELOG.md",1,89)]},
        ],
        "source_reuses": [],
    }
    sp = workspace / "structure-proposal.json"
    sm = workspace / "structure.md"
    sp.write_text(json.dumps(structure, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    create_or_load_structure_markdown(snapshot, sp, sm)
    sproposal = load_onboarding_structure_proposal(sp, snapshot)
    human_structure = load_structure_markdown(sm, sproposal)

    def item(i: int, title: str, kind: str, action: str, dest: str | None, rationale: str, evidence: list[dict[str, object]], payload: dict[str, object], confidence: str = "high") -> dict[str, object]:
        return {"id":f"P-{i:03d}","title":title,"kind":kind,"action":action,"destination_node_key":dest,"rationale":rationale,"confidence":confidence,"evidence":evidence,"payload":payload}

    items = [
        item(1,"Project responsibility","overview","promote","N-001","Stable first-contact orientation belongs at the project root.",[ev("README.md",1,3)],{"text":"Reproducible AI workstation for Windows 11, WSL 2 and Ubuntu 24.04.","wording_origin":"exact"}),
        item(2,"Current project scope","state","promote","N-001","This is the current implemented scope, not timeless governance and not a reason to preserve README as its only future owner.",[ev("README.md",5,8)],{"text":"Current scope: repeatable Windows/WSL bootstrap, locked Ansible host setup, Docker Engine, isolated Goose CLI sessions using OpenRouter, and a persistent Open WebUI service.","wording_origin":"lightly-edited"}),
        item(3,"Local model integration deferred","plan","promote","N-001","The evidence explicitly marks this as later work; the owner removed the speculative reserved Node from structure, so the plan stays project-level.",[ev("README.md",5,8)],{"text":"Local model integration is intentionally deferred to the next phase.","wording_origin":"exact"}),
        item(4,"Repository is the installation specification","rule","promote","N-001","This is a durable project-wide authority rule, not merely descriptive architecture.",[ev("docs/architecture.md",12,13)],{"statement":"The repository is the installation specification.","why":"Running containers and manually modified hosts are not treated as the source of truth.","wording_origin":"exact"}),
        item(5,"Synchronize version definitions documentation and tests","rule","promote","N-001","This is repository-specific release governance that remains a local delta even when a generic Development Workflow Source is selected by the owner.",[ev("CONTRIBUTING.md",7,8)],{"statement":"Update `config/versions.json`, documentation and tests together.","why":"Keep project release metadata, documentation and verification synchronized.","wording_origin":"exact"}),
        item(6,"Run release check before committing","rule","promote","N-001","The project names a concrete mandatory validation command that a generic workflow Source should not replace.",[ev("CONTRIBUTING.md",7,8)],{"statement":"Run `./tools/release-check.sh` before committing.","why":"This repository defines release-check as its local pre-commit release validation.","wording_origin":"exact"}),
        item(7,"Bootstrap responsibility","overview","promote","N-002","The accepted grouping Node should orient changes spanning Windows, Linux bootstrap and host configuration.",[ev("docs/architecture.md",3,10),ev("README.md",268,285)],{"text":"Bootstrap owns the repeatable workstation foundation across Windows/WSL provisioning, Linux bootstrap and Ansible-managed Ubuntu host state.","wording_origin":"synthesized"}),
        item(8,"Keep installation entry points thin","rule","promote","N-002","This governs both installation entry points and belongs at their shared Bootstrap parent.",[ev("CONTRIBUTING.md",3,5)],{"statement":"Keep installation entry points thin and move implementation into modules.","why":"Preserve the repository's explicit separation between entry points and implementation modules.","wording_origin":"exact"}),
        item(9,"Preserve idempotent installation","rule","promote","N-002","Restartability is a durable installer invariant across Windows and Linux.",[ev("CONTRIBUTING.md",4,6),ev("README.md",276,285)],{"statement":"Preserve idempotency: a second run must be safe.","why":"Both installation entry points are intended to be rerun safely after interruption.","wording_origin":"exact"}),
        item(10,"Never automate destructive migration","rule","promote","N-002","The repository makes non-destructive migration an explicit durable installation boundary.",[ev("CONTRIBUTING.md",5,6),ev("docs/clean-room-test.md",1,20)],{"statement":"Never introduce an automatic destructive migration.","why":"Existing distributions and working reference state must not be silently destroyed during installation or testing.","wording_origin":"exact"}),
        item(11,"Windows and WSL responsibility","overview","promote","N-003","The architecture assigns a clear stable responsibility to the Windows/PowerShell layer.",[ev("docs/architecture.md",3,6)],{"text":"Windows and WSL bootstrap owns Windows, WSL, reboot continuation and distribution lifecycle.","wording_origin":"lightly-edited"}),
        item(12,"Linux bootstrap responsibility","overview","promote","N-004","The accepted owner structure groups the minimal Linux runtime with Ansible-managed host state.",[ev("docs/architecture.md",5,8)],{"text":"Linux bootstrap owns minimal packages, uv and the locked Ansible runtime; Ansible manages Ubuntu host state and Docker Engine.","wording_origin":"lightly-edited"}),
        item(13,"Develop active Linux tree inside WSL filesystem","rule","promote","N-004","This is an explicit development/permission constraint for Linux-side work.",[ev("CONTRIBUTING.md",1,4),ev("docs/repository-setup.md",8,14)],{"statement":"Work inside the WSL Linux filesystem, not under `/mnt/c`.","why":"Linux permissions and tooling behavior should come from the Linux filesystem rather than synthetic Windows-mounted modes.","wording_origin":"exact"}),
        item(14,"aiw responsibility","overview","promote","N-005","The architecture names aiw as the stable operator interface.",[ev("docs/architecture.md",8,10),ev("README.md",35,56)],{"text":"`aiw` is the stable user interface for installation and operation.","wording_origin":"lightly-edited"}),
        item(15,"Container runtime responsibility","overview","promote","N-006","This parent Node owns runtime concerns shared by Goose and Open WebUI rather than either child alone.",[ev("docs/architecture.md",8,10)],{"text":"Containerized application runtimes use Dockerfile for service image contents and Compose for services, mounts, networks and resource limits.","wording_origin":"lightly-edited"}),
        item(16,"Keep runtime secrets out of repositories and images","rule","promote","N-006","This is a cross-runtime security invariant, not just user instructions.",[ev("SECURITY.md",5,10),ev("README.md",74,92)],{"statement":"Secrets must not be committed, copied into images or stored in Compose files.","why":"Runtime credentials belong in the Git-ignored `.env` file with restrictive permissions, outside versioned or image content.","wording_origin":"exact"}),
        item(17,"Do not give application containers Docker control","rule","promote","N-006","The security policy applies this boundary to both agent and application containers.",[ev("SECURITY.md",5,9)],{"statement":"Agent and application containers do not receive the Docker socket.","why":"The Docker socket would grant host-level container control beyond the intended runtime boundary.","wording_origin":"exact"}),
        item(18,"Goose responsibility","overview","promote","N-007","Stable Goose architecture is more useful as Node orientation than as duplicated transient state.",[ev("README.md",94,105),ev("SECURITY.md",12,26)],{"text":"Goose runs short-lived containers with exactly one explicitly registered writable workspace while persistent Goose state and session history remain outside the ephemeral container root.","wording_origin":"lightly-edited"}),
        item(19,"Constrain Goose to the selected workspace","rule","promote","N-007","This is the defining least-privilege boundary for the agent runtime.",[ev("SECURITY.md",12,26)],{"statement":"Each Goose session receives exactly one explicitly registered host workspace mounted read-write and no unrelated WSL or Windows directories unless deliberately selected.","why":"The selected workspace is delegated authority; broad host paths and unrelated data remain outside the agent boundary.","wording_origin":"lightly-edited"}),
        item(20,"Open WebUI responsibility","overview","promote","N-008","The service has a stable lifecycle, storage and local-network identity distinct from Goose.",[ev("README.md",142,184),ev("SECURITY.md",28,40)],{"text":"Open WebUI is a persistent Docker service bound to localhost, with application state in a named Docker volume and no host workspace or Docker socket.","wording_origin":"lightly-edited"}),
        item(21,"Keep Open WebUI local and authenticated by default","rule","promote","N-008","This is durable service-specific security governance.",[ev("SECURITY.md",28,40)],{"statement":"Keep Open WebUI bound to `127.0.0.1` with authentication enabled unless equivalent TLS, authentication and network controls are deliberately added for broader exposure.","why":"The documented default boundary assumes local access and warns against publishing the service without compensating controls.","wording_origin":"lightly-edited"}),
        item(22,"Architecture reference","topic-resource","reference","N-001","The architecture document remains a natural maintained source for layer responsibilities and installation authority.",[ev("docs/architecture.md",1,13)],{"condition":"When changing layer responsibilities, installation authority, or cross-layer architecture, consult the architecture document.","resource_paths":["docs/architecture.md"]}),
        item(23,"CI validation reference","topic-resource","reference","N-001","Executable CI is the natural source for the exact current validation pipeline.",[ev(".github/workflows/validate.yml",17,61)],{"condition":"When changing validation, dependencies, smoke checks, Ansible linting or playbook syntax checks, inspect the validation workflow.","resource_paths":[".github/workflows/validate.yml"]}),
        item(24,"Bootstrap recovery reference","topic-resource","reference","N-002","Clean-room and troubleshooting procedures are deep task material, not broad Rules.",[ev("docs/clean-room-test.md",1,20),ev("docs/clean-room-test.md",41,58),ev("docs/troubleshooting.md",1,145)],{"condition":"When testing installation isolation, reinstalling safely, or diagnosing WSL, shortcut, permission, Docker, elevation or bootstrap failures, use the recovery documentation.","resource_paths":["docs/clean-room-test.md","docs/troubleshooting.md"]}),
        item(25,"aiw operator guide","topic-resource","reference","N-005","README remains the maintained first-contact operator guide; the Node should route to it rather than reproduce all commands.",[ev("README.md",35,72),ev("README.md",259,285)],{"condition":"When operating AI Workstation through `aiw`, discovering commands, checking status or updating the installation, use the operator guide in README.","resource_paths":["README.md"]}),
        item(26,"Goose operator guide","topic-resource","reference","N-007","README already owns detailed Goose workspace/session commands.",[ev("README.md",94,139)],{"condition":"When registering Goose workspaces, starting/resuming sessions, running prompts or inspecting Goose runtime commands, use the Goose section of README.","resource_paths":["README.md"]}),
        item(27,"Open WebUI operator guide","topic-resource","reference","N-008","README already owns detailed Open WebUI lifecycle and first-use commands.",[ev("README.md",142,194)],{"condition":"When starting, stopping, opening, configuring or diagnosing Open WebUI, use the Open WebUI section of README.","resource_paths":["README.md"]}),
        item(28,"Runtime security reference","topic-resource","reference","N-006","SECURITY.md remains mutable project-owned detailed security guidance; routing is preferable to copying the entire policy into Rules.",[ev("SECURITY.md",1,46)],{"condition":"When changing container privileges, Docker exposure, workspace delegation, secret handling, Open WebUI exposure or vulnerability reporting, consult SECURITY.md.","resource_paths":["SECURITY.md"]}),
        item(29,"Repository creation record","ordinary-documentation","keep",None,"This document explicitly says it is only for creating the public repository from the tested prototype, not normal operation.",[ev("docs/repository-setup.md",1,10),ev("docs/repository-setup.md",31,78)],{"document_paths":["docs/repository-setup.md"],"reason":"Keep as historical/special-purpose repository-creation documentation rather than canonical current Node semantics."}),
        item(30,"Release history","ordinary-documentation","keep",None,"The changelog is chronological history; current semantics may cite it as corroboration but should not duplicate it as current Context.",[ev("CHANGELOG.md",1,89)],{"document_paths":["CHANGELOG.md"],"reason":"Keep as chronological release history."}),
        item(31,"Historical patch note","ordinary-documentation","keep",None,"This records one historical 0.4.7 implementation fix and should not become broad current governance.",[ev("docs/PATCH-0.4.7.md",1,10)],{"document_paths":["docs/PATCH-0.4.7.md"],"reason":"Keep as historical patch documentation."}),
        item(32,"Supported host baseline","state","promote","N-001","The supported platform list describes current compatibility state that may evolve.",[ev("README.md",337,345)],{"text":"Supported host: Windows 11 with current Store WSL; PowerShell 7.4 or newer; Ubuntu 24.04 under WSL 2; x86-64 Windows and WSL architecture.","wording_origin":"lightly-edited"}),
        item(33,"Clarify repository versus Python project versioning","unresolved","keep","N-001","Frozen Evidence shows CHANGELOG 0.6.2 while pyproject declares 0.1.0 and does not define whether these version streams are intentionally independent.",[ev("CHANGELOG.md",1,5),ev("pyproject.toml",1,5),ev("pyproject.toml",11,12),ev("CONTRIBUTING.md",7,8)],{"question":"What is the intended relationship between the repository/release version in CHANGELOG.md and the project version in pyproject.toml?"}),
    ]

    placement = {
        "schema": PLACEMENT_PROPOSAL_SCHEMA,
        "evidence_digest": EXPECTED_EVIDENCE,
        "structure_digest": human_structure.structure_digest,
        "items": items,
        "source_reuses": [],
    }
    pp = workspace / "placement-proposal.json"
    pp.write_text(json.dumps(placement, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Run the actual CLI contract, including explicit owner-selected reusable Source.
    catalog = root / "nodes" / "library" / "development-workflow"
    run("contextcanon", "onboard", "placement-validate", str(snapshot), "--workspace", str(workspace), "--catalog-package", str(catalog), cwd=aiw)
    run(
        "contextcanon", "onboard", "placement-review", str(snapshot),
        "--workspace", str(workspace), "--catalog-package", str(catalog),
        "--owner-source", f"N-001={WORKFLOW_ID}", cwd=aiw,
    )

    # Copy the new human-facing review plus a concise deterministic report back to
    # the framework branch for explicit inspection before the controlled publish test.
    shutil.copy2(workspace / "placement.md", root / "_real-ai-workstation-placement-review.md")
    report = {
        "evidence_digest": EXPECTED_EVIDENCE,
        "ai_workstation_commit": AIW_COMMIT,
        "root_node_id": ROOT_ID,
        "structure_digest": human_structure.structure_digest,
        "placement_items": len(items),
        "owner_selected_source": WORKFLOW_ID,
        "source_package_digest": json.loads((catalog / ".context" / "package.json").read_text(encoding="utf-8"))["digests"]["package"],
        "note": "Temporary inspection artifact. No AI Workstation repository mutation was published by this review-generation step.",
    }
    (root / "_real-ai-workstation-placement-review.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
