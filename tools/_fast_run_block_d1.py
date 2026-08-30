from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    file = Path(path)
    text = file.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one target, found {count}: {old[:120]!r}")
    file.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")


# ---------------------------------------------------------------------------
# Workspace checkpoint: framework-owned, deterministic, last-confirmed state.
# ---------------------------------------------------------------------------
replace_once(
    "src/contextcanon/onboarding_workspace.py",
    '''WORKSPACE_MARKER = f'<!-- contextcanon:onboarding-workspace schema="{WORKSPACE_SCHEMA}" -->'\n''',
    '''WORKSPACE_MARKER = f'<!-- contextcanon:onboarding-workspace schema="{WORKSPACE_SCHEMA}" -->'\nCHECKPOINT_START = "<!-- contextcanon-onboarding-checkpoint:start -->"\nCHECKPOINT_END = "<!-- contextcanon-onboarding-checkpoint:end -->"\n''',
)
replace_once(
    "src/contextcanon/onboarding_workspace.py",
    '''The structure file is the human-owned coarse map. The placement pass is not allowed to redesign it. None of these working files become canonical Context merely because they exist; only explicit `placement-publish` changes reviewed Context Node authoring.\n\n## Ownership\n''',
    '''The structure file is the human-owned coarse map. The placement pass is not allowed to redesign it. None of these working files become canonical Context merely because they exist; only explicit `placement-publish` changes reviewed Context Node authoring.\n\n## Current checkpoint\n\n{CHECKPOINT_START}\nNo ContextCanon structure-first command has recorded a checkpoint in this workspace yet.\n{CHECKPOINT_END}\n\nThe checkpoint above is the **last state ContextCanon validated**, not a file watcher. If you edit `structure.md` or `placement.md`, the edit becomes authoritative human input only after the next ContextCanon command validates it and advances this checkpoint.\n\n## Ownership\n''',
)
insert = r'''

def _snapshot_label(snapshot_root: Path) -> str:
    snapshot = snapshot_root.resolve()
    project = find_repo_root(snapshot)
    try:
        return snapshot.relative_to(project).as_posix()
    except ValueError:
        return str(snapshot)


def update_workspace_checkpoint(
    workspace: OnboardingWorkspace,
    snapshot_root: Path,
    *,
    stage: str,
    next_action: str,
    structure_digest: str | None = None,
    placement_proposal_digest: str | None = None,
    placement_review_digest: str | None = None,
    placement_review_complete: bool | None = None,
    acceptance_digest: str | None = None,
    source_catalog: tuple[str, ...] = (),
) -> None:
    """Rewrite only the framework-owned checkpoint inside the visible README."""

    try:
        text = workspace.readme_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ContextCanonError(f"Missing onboarding workspace README: {workspace.readme_path}") from exc
    if WORKSPACE_MARKER not in text:
        raise ContextCanonError(f"Refusing to update unowned onboarding workspace README: {workspace.readme_path}")

    lines = [
        f"- Evidence: `{snapshot_root.resolve().name}`",
        f"- Snapshot: `{_snapshot_label(snapshot_root)}`",
        f"- Stage: **{stage}**",
    ]
    if structure_digest is not None:
        lines.append(f"- Accepted structure: `{structure_digest}`")
    if placement_proposal_digest is not None:
        lines.append(f"- Placement proposal: `{placement_proposal_digest}`")
    if placement_review_digest is not None:
        state = "complete" if placement_review_complete else "still has pending decisions"
        lines.append(f"- Placement review: `{placement_review_digest}` — {state}")
    if source_catalog:
        lines.append("- Exact reusable Source catalog:")
        lines.extend(f"  - `{item}`" for item in source_catalog)
    if acceptance_digest is not None:
        lines.append(f"- Placement acceptance: `{acceptance_digest}`")
    lines.extend(["", "**Next:**", "", next_action])
    block = CHECKPOINT_START + "\n" + "\n".join(lines) + "\n" + CHECKPOINT_END

    if CHECKPOINT_START in text or CHECKPOINT_END in text:
        if text.count(CHECKPOINT_START) != 1 or text.count(CHECKPOINT_END) != 1:
            raise ContextCanonError(f"Malformed onboarding checkpoint markers in {workspace.readme_path}")
        start = text.index(CHECKPOINT_START)
        end = text.index(CHECKPOINT_END, start) + len(CHECKPOINT_END)
        text = text[:start] + block + text[end:]
    else:
        anchor = "\n## Ownership\n"
        if anchor not in text:
            raise ContextCanonError(f"Cannot add onboarding checkpoint to unexpected README layout: {workspace.readme_path}")
        text = text.replace(
            anchor,
            "\n## Current checkpoint\n\n" + block +
            "\n\nThe checkpoint above is the **last state ContextCanon validated**, not a file watcher. "
            "If you edit `structure.md` or `placement.md`, the edit becomes authoritative human input only after "
            "the next ContextCanon command validates it and advances this checkpoint.\n" + anchor,
            1,
        )
    write_utf8(workspace.readme_path, text)
'''
workspace = Path("src/contextcanon/onboarding_workspace.py")
text = workspace.read_text(encoding="utf-8")
needle = "\ndef _default_workspace_root(snapshot_root: Path) -> Path:\n"
if text.count(needle) != 1:
    raise SystemExit("workspace insertion point changed")
text = text.replace(needle, insert + needle, 1)
workspace.write_text(text, encoding="utf-8", newline="\n")

# ---------------------------------------------------------------------------
# CLI checkpoint orchestration for the current structure-first path.
# ---------------------------------------------------------------------------
replace_once(
    "src/contextcanon/cli.py",
    'from .onboarding_workspace import open_onboarding_workspace, write_utf8\n',
    'from .onboarding_workspace import open_onboarding_workspace, update_workspace_checkpoint, write_utf8\n',
)
# structure instruction
replace_once(
    "src/contextcanon/cli.py",
    '''                print(f"Expected LLM output: {workspace.structure_proposal_path}")\n                return 0\n''',
    '''                print(f"Expected LLM output: {workspace.structure_proposal_path}")\n                update_workspace_checkpoint(\n                    workspace, snapshot,\n                    stage="structure instruction ready",\n                    next_action=(\n                        "Give `structure-instruction.md` and only the frozen `evidence/` tree to a strong reasoning LLM. "\n                        "Save its single JSON result as `structure-proposal.json`, then run "\n                        f"`contextcanon onboard structure-validate {_snapshot_cli(snapshot)}`."\n                    ),\n                )\n                return 0\n''',
)
# helper _snapshot_cli near workspace helper
replace_once(
    "src/contextcanon/cli.py",
    '''def _workspace_path(value: str | None) -> Path | None:\n    return Path(value) if value is not None else None\n\n\ndef _add_workspace''',
    '''def _workspace_path(value: str | None) -> Path | None:\n    return Path(value) if value is not None else None\n\n\ndef _snapshot_cli(snapshot: Path) -> str:\n    try:\n        return snapshot.resolve().relative_to(find_repo_root(snapshot)).as_posix()\n    except ValueError:\n        return str(snapshot)\n\n\ndef _catalog_labels(packages) -> tuple[str, ...]:\n    return tuple(\n        f"{package.metadata.id} · {package.metadata.name} · {package.metadata.version} · {package.package_digest}"\n        for package in packages\n    )\n\n\ndef _add_workspace''',
)
# structure validate
replace_once(
    "src/contextcanon/cli.py",
    '''                print(f"Source reuses: {len(proposal.source_reuses)}")\n                return 0\n\n            if args.onboard_command == "structure-review":\n''',
    '''                print(f"Source reuses: {len(proposal.source_reuses)}")\n                if args.proposal is None:\n                    update_workspace_checkpoint(\n                        workspace, snapshot,\n                        stage="structure proposal validated",\n                        next_action=f"Run `contextcanon onboard structure-review {_snapshot_cli(snapshot)}` and edit `structure.md`.",\n                    )\n                return 0\n\n            if args.onboard_command == "structure-review":\n''',
)
# structure review
replace_once(
    "src/contextcanon/cli.py",
    '''                print(f"Nodes in edited tree: {len(plan.nodes)}")\n                return 0\n\n            if args.onboard_command in {"structure-preview", "structure-materialize"}:\n''',
    '''                print(f"Nodes in edited tree: {len(plan.nodes)}")\n                if workspace is not None:\n                    update_workspace_checkpoint(\n                        workspace, snapshot,\n                        stage="human structure validated",\n                        structure_digest=plan.structure_digest,\n                        next_action=f"Run `contextcanon onboard structure-preview {_snapshot_cli(snapshot)}`.",\n                    )\n                return 0\n\n            if args.onboard_command in {"structure-preview", "structure-materialize"}:\n''',
)
# structure preview/materialize returns
replace_once(
    "src/contextcanon/cli.py",
    '''                if args.onboard_command == "structure-preview":\n                    return 0\n                created = materialize_structure_skeletons(preview)\n                print(f"Materialized Node skeletons: {len(created)}")\n                for path in created:\n                    print(f"  - {path}")\n                return 0\n''',
    '''                if args.onboard_command == "structure-preview":\n                    next_action = (\n                        f"Run `contextcanon onboard structure-materialize {_snapshot_cli(snapshot)}` after reviewing `structure-preview.md`."\n                        if missing else\n                        f"Run `contextcanon onboard placement-instruction {_snapshot_cli(snapshot)}`."\n                    )\n                    update_workspace_checkpoint(\n                        workspace, snapshot, stage="structure previewed",\n                        structure_digest=preview.structure_digest, next_action=next_action,\n                    )\n                    return 0\n                created = materialize_structure_skeletons(preview)\n                print(f"Materialized Node skeletons: {len(created)}")\n                for path in created:\n                    print(f"  - {path}")\n                update_workspace_checkpoint(\n                    workspace, snapshot, stage="structure materialized",\n                    structure_digest=preview.structure_digest,\n                    next_action=f"Run `contextcanon onboard placement-instruction {_snapshot_cli(snapshot)}`.",\n                )\n                return 0\n''',
)
# placement instruction checkpoint
replace_once(
    "src/contextcanon/cli.py",
    '''                    print(f"Expected LLM output: {workspace.placement_proposal_path}")\n                    return 0\n''',
    '''                    print(f"Expected LLM output: {workspace.placement_proposal_path}")\n                    update_workspace_checkpoint(\n                        workspace, snapshot, stage="placement instruction ready",\n                        structure_digest=instruction.structure_digest,\n                        next_action=(\n                            "Give `placement-instruction.md` and only the frozen `evidence/` tree to a strong reasoning LLM. "\n                            "Save its single JSON result as `placement-proposal.json`, then run "\n                            f"`contextcanon onboard placement-validate {_snapshot_cli(snapshot)}` with the same `--catalog-package` inputs."\n                        ),\n                    )\n                    return 0\n''',
)
# placement validate
replace_once(
    "src/contextcanon/cli.py",
    '''                    print(f"Source reuses: {len(proposal.source_reuses)}")\n                    return 0\n\n                review_path = Path(args.review) if args.review is not None else workspace.placement_path\n''',
    '''                    print(f"Source reuses: {len(proposal.source_reuses)}")\n                    update_workspace_checkpoint(\n                        workspace, snapshot, stage="placement proposal validated",\n                        structure_digest=proposal.structure_digest,\n                        placement_proposal_digest=proposal.proposal_digest,\n                        source_catalog=_catalog_labels(proposal.catalog_packages),\n                        next_action=(\n                            f"Run `contextcanon onboard placement-review {_snapshot_cli(snapshot)}` with the same `--catalog-package` inputs. "\n                            "Add any explicit owner choice with `--owner-source TARGET_NODE_KEY=SOURCE_NODE_ID`."\n                        ),\n                    )\n                    return 0\n\n                review_path = Path(args.review) if args.review is not None else workspace.placement_path\n''',
)
# placement review
replace_once(
    "src/contextcanon/cli.py",
    '''                    print(f"Items: {len(review.items)} · Sources: {len(review.sources)} · complete: {review.is_complete}")\n                    return 0\n\n                review = load_placement_review(review_path, proposal, snapshot)\n''',
    '''                    print(f"Items: {len(review.items)} · Sources: {len(review.sources)} · complete: {review.is_complete}")\n                    next_action = (\n                        f"Run `contextcanon onboard placement-preview {_snapshot_cli(snapshot)}` with the same `--catalog-package` inputs."\n                        if review.is_complete else\n                        "Edit `placement.md`: set every Decision to `accept` or `reject` and correct destination/maintained meaning where needed. "\n                        f"Then run `contextcanon onboard placement-preview {_snapshot_cli(snapshot)}` with the same `--catalog-package` inputs."\n                    )\n                    update_workspace_checkpoint(\n                        workspace, snapshot, stage="human placement review",\n                        structure_digest=proposal.structure_digest,\n                        placement_proposal_digest=proposal.proposal_digest,\n                        placement_review_digest=review.review_digest,\n                        placement_review_complete=review.is_complete,\n                        source_catalog=_catalog_labels(proposal.catalog_packages),\n                        next_action=next_action,\n                    )\n                    return 0\n\n                review = load_placement_review(review_path, proposal, snapshot)\n''',
)
# placement preview and publish
replace_once(
    "src/contextcanon/cli.py",
    '''                if args.onboard_command == "placement-preview":\n                    return 0\n\n                acceptance_path = (\n''',
    '''                if args.onboard_command == "placement-preview":\n                    next_action = (\n                        f"Review `placement-preview.md`, then run `contextcanon onboard placement-publish {_snapshot_cli(snapshot)}` with the same `--catalog-package` inputs."\n                        if preview.review_complete else\n                        "Return to `placement.md`, resolve all pending decisions, and preview again."\n                    )\n                    update_workspace_checkpoint(\n                        workspace, snapshot, stage="placement publication previewed",\n                        structure_digest=preview.structure_digest,\n                        placement_proposal_digest=preview.proposal_digest,\n                        placement_review_digest=preview.review_digest,\n                        placement_review_complete=preview.review_complete,\n                        source_catalog=_catalog_labels(proposal.catalog_packages),\n                        next_action=next_action,\n                    )\n                    return 0\n\n                acceptance_path = (\n''',
)
replace_once(
    "src/contextcanon/cli.py",
    '''                print(f"Follow-up: {workspace.placement_followup_path}")\n                return 0\n''',
    '''                print(f"Follow-up: {workspace.placement_followup_path}")\n                update_workspace_checkpoint(\n                    workspace, snapshot, stage="placement published",\n                    structure_digest=preview.structure_digest,\n                    placement_proposal_digest=preview.proposal_digest,\n                    placement_review_digest=preview.review_digest,\n                    placement_review_complete=True,\n                    acceptance_digest=result.acceptance_digest,\n                    source_catalog=_catalog_labels(proposal.catalog_packages),\n                    next_action=(\n                        "Review `placement-followup.md`. Mutable-Markdown duplicate cleanup is deliberately a separate later operation; "\n                        "ordinary ContextCanon-native project growth now happens by editing the relevant Node sources directly, not by rerunning migration onboarding."\n                    ),\n                )\n                return 0\n''',
)

# ---------------------------------------------------------------------------
# Documentation: current structure-first migration versus native growth.
# Replace the now-obsolete placement/stop-point portion of docs/onboarding.md.
# ---------------------------------------------------------------------------
doc = Path("docs/onboarding.md")
text = doc.read_text(encoding="utf-8")
start = text.index("## 5. Generate the content-placement assignment")
end = text.index("## Visible workspace versus machine state")
replacement = r'''## 5. Generate the content-placement assignment

The second semantic pass is bound to both the exact frozen Evidence digest and the digest of the human-edited `structure.md`:

```text
contextcanon onboard placement-instruction \
  .context/onboarding/<evidence-digest> \
  --catalog-package <package-root-a>
```

ContextCanon writes `contextcanon-onboarding/placement-instruction.md`. Give that instruction and **only the same frozen `evidence/` tree** to a strong reasoning LLM. Save its single JSON response as `contextcanon-onboarding/placement-proposal.json`.

The placement question is no longer "where is this text today?". It is:

> **Where should this meaning be maintained from now on?**

The v1 proposal distinguishes:

- `overview` — short stable orientation about what a Node owns;
- `rule` — durable project-local governance;
- `topic-resource` — deeper Markdown that remains maintained at its natural repository path and is routed to by a Topic;
- `state` / `plan` — current situation or future work, kept distinct from inherited governance;
- `ordinary-documentation` — useful documents that remain ordinary documents;
- `authority-mapping` — a local interpretation of Markdown deliberately marked fixed/authoritative in `structure.md`;
- `unresolved` — ambiguity that must remain visible.

Actions are deliberately narrow:

- `promote` — maintain the reviewed meaning canonically at the destination ContextCanon surface;
- `reference` — only for `topic-resource`; keep the referenced Markdown as the maintenance surface and store routing, not a copied second meaning;
- `keep` — intentionally remain outside canonical Node authoring;
- `map` — preserve fixed Markdown as authority while recording the reviewed local relationship to it.

Clear source wording should normally remain `exact`; use `lightly-edited` only for small self-containment changes and `synthesized` only when new wording is genuinely required.

### Mutable and fixed Markdown

During structure review, all proposed Markdown knowledge bodies are mutable by default. The owner may list selected proposed Markdown paths under `## Fixed Markdown` in `structure.md`.

- **mutable** means ContextCanon may become the future owner of promoted meaning, but the first publication still does not delete or rewrite the old document;
- **fixed** means the document remains authoritative and may only be referenced/mapped by this onboarding flow.

Non-Markdown document authorities such as PDF/Word are deliberately unsupported in this version rather than hidden behind an implicit conversion mechanism.

## 6. Validate and edit `placement.md`

Validate the LLM result using the same Source catalog:

```text
contextcanon onboard placement-validate \
  .context/onboarding/<evidence-digest> \
  --catalog-package <package-root-a>
```

Then create the human review:

```text
contextcanon onboard placement-review \
  .context/onboarding/<evidence-digest> \
  --catalog-package <package-root-a>
```

`placement.md` is the **human-owned decision file**, not merely a rendered report. Each finding is destination-first:

```text
Destination
Decision: pending | accept | reject
Kind / Action
Maintained meaning
Proposal rationale
Exact Evidence excerpts
```

The owner may edit destination, decision, title, kind/action within the supported semantics, maintained wording, and review note directly in this Markdown. ContextCanon allocates authoring identity for future Rules/Topics once and preserves it across reloads even when human-facing titles or wording change.

An existing `placement.md` is never silently regenerated over human edits. If the semantic proposal changes, ContextCanon requires a new review path instead of inventing a merge engine.

### Explicit owner-selected reusable Sources

An LLM may propose Source reuse only when frozen project Evidence supports it. A project owner may nevertheless choose an exact reusable Source for architectural reasons outside that Evidence:

```text
contextcanon onboard placement-review \
  .context/onboarding/<evidence-digest> \
  --catalog-package <package-root> \
  --owner-source N-001=<source-node-id>
```

The review labels that Source `owner-selected`; it does not pretend the choice came from project Evidence. Both Evidence-derived and owner-selected Sources remain bound to the exact immutable package identity.

## 7. Preview exact publication before mutation

Once every placement decision is resolved:

```text
contextcanon onboard placement-preview \
  .context/onboarding/<evidence-digest> \
  --catalog-package <package-root-a>
```

The command writes `contextcanon-onboarding/placement-preview.md` and changes no project file. The preview shows:

- the exact `CONTEXT.src.md` delta for every affected Node;
- exact reusable Source package/Git provenance that would be installed and pinned;
- accepted findings intentionally retained outside today's Node authoring grammar;
- mutable Markdown that may later be a duplicate-cleanup candidate, without applying that cleanup.

Preview verifies the live Evidence-covered project bytes and the current Node source bytes. Publication later refuses if those inputs changed after the preview.

## 8. Explicitly publish the reviewed placement

After reviewing the preview:

```text
contextcanon onboard placement-publish \
  .context/onboarding/<evidence-digest> \
  --catalog-package <package-root-a>
```

Publication currently materializes only semantics the ContextCanon source grammar can represent cleanly:

- accepted Overview additions;
- accepted local Rules;
- accepted Topics/Resources;
- accepted exact reusable Sources.

Existing Node identity and unrelated authored Node content are preserved. A child Node may reference a repository resource outside its own directory; ContextCanon converts repository-relative Evidence paths into safe Node-relative locators such as `../../docs/architecture.md` while still forbidding repository escape.

Accepted `state`, `plan`, `ordinary-documentation`, `authority-mapping`, and `unresolved` findings are **not lost** and are not forced into arbitrary prose. They remain in the exact machine acceptance record and in visible `placement-followup.md` for deliberate later handling.

The first publication also leaves README/CONTRIBUTING/architecture and other mutable Markdown untouched. Removing proven duplicate prose is a separate future cleanup operation with its own preview/review boundary.

Reusable Source packages are copied into the target Node's accepted local `.context/sources/<package-digest>/` state. The authored Source declaration carries durable Git origin, exact commit SHA and Node path derived from the clean supplied Source checkout; a transient developer checkout path is never written into project truth.

Publication is transaction-like and idempotent: it recompiles touched Nodes, writes generated outputs, records exact resulting package/source digests, rolls back on failure, and a second unchanged preview/publication produces no additional source delta.

## Migration onboarding versus normal ContextCanon-native growth

The structure-first flow above is primarily a **migration/onboarding workflow for an existing knowledge-rich repository**. It performs repository archaeology, proposes a shelf map, redistributes existing meaning, and records what remains outside current canonical authoring.

Once a project is ContextCanon-native, ordinary growth should usually be much simpler:

```text
new project knowledge
→ edit the relevant existing CONTEXT.src.md / Topic resource / project state surface
→ normal review
→ contextcanon build/check
```

Do not rerun full migration onboarding for every normal feature. A future "context audit" may intentionally re-examine accumulated repository knowledge, drift or changed structure, but that is a separate lifecycle operation and should not be smuggled into initial onboarding semantics.

### Reusable Node distribution remains an explicit later UX decision

This work proves immutable reusable Source packages, exact Git provenance, owner selection and local accepted package state. It deliberately does **not** choose how a wider Node library should be discovered/distributed in the long term (single Git repository, multiple repositories, registry, catalog service, or another mechanism). That distribution UX needs its own real use cases before ContextCanon hardens an architecture.

'''
text = text[:start] + replacement + text[end:]
# update visible workspace listing later in same doc
text = text.replace(
    '''    placement-proposal.json\n    placement.md\n''',
    '''    placement-proposal.json\n    placement.md\n    placement-preview.md\n    placement-followup.md\n''',
)
doc.write_text(text, encoding="utf-8", newline="\n")

# Root README: replace one stale experimental-stop sentence if present and add current publication story compactly.
readme = Path("README.md")
text = readme.read_text(encoding="utf-8")
text = text.replace(
    "The current structure-first experiment deliberately stops before automatic placement publication or cleanup.",
    "The structure-first flow now continues through editable placement review, exact publication preview, and explicit reviewed placement publication; duplicate cleanup remains a separate later operation.",
)
readme.write_text(text, encoding="utf-8", newline="\n")

# PLAN checkpoint first three Block D items only. Real project validation remains open.
plan = Path("PLAN.md")
text = plan.read_text(encoding="utf-8")
for old in [
    "- [ ] Make the visible onboarding workspace self-describing enough that a human or capable LLM can enter through one local file and reconstruct Evidence identity, accepted structure, current placement-review stage and next command without chat history.",
    "- [ ] Document the distinction between one-time migration onboarding and ContextCanon-native project growth/maintenance; keep future context-audit ideas separate from initial onboarding.",
    "- [ ] Record reusable Node distribution as an explicit later UX decision without selecting a repository/registry architecture in this block.",
]:
    if old not in text:
        raise SystemExit(f"PLAN D1 item missing: {old}")
    text = text.replace(old, old.replace("- [ ]", "- [x]", 1), 1)
plan.write_text(text, encoding="utf-8", newline="\n")

# Focused checkpoint regression.
test = Path("tests/test_onboarding_workspace_checkpoint.py")
test.write_text(r'''from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from contextcanon.onboarding import prepare_onboarding_evidence
from contextcanon.onboarding_workspace import (
    CHECKPOINT_END,
    CHECKPOINT_START,
    open_onboarding_workspace,
    update_workspace_checkpoint,
)


class WorkspaceCheckpointTests(unittest.TestCase):
    def test_checkpoint_is_framework_owned_replaced_not_duplicated_and_resume_ready(self):
        repo = Path(tempfile.mkdtemp())
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        (repo / "README.md").write_text("# Project\n", encoding="utf-8")
        prepared = prepare_onboarding_evidence(repo)
        workspace = open_onboarding_workspace(prepared.snapshot_root, create=True)

        update_workspace_checkpoint(
            workspace,
            prepared.snapshot_root,
            stage="human placement review",
            structure_digest="1" * 64,
            placement_proposal_digest="2" * 64,
            placement_review_digest="3" * 64,
            placement_review_complete=False,
            source_catalog=("source-id · Workflow · 1.0.0 · " + "4" * 64,),
            next_action="Edit `placement.md`, then run `contextcanon onboard placement-preview ...`.",
        )
        first = workspace.readme_path.read_text(encoding="utf-8")
        self.assertEqual(first.count(CHECKPOINT_START), 1)
        self.assertEqual(first.count(CHECKPOINT_END), 1)
        self.assertIn(prepared.evidence_digest, first)
        self.assertIn("human placement review", first)
        self.assertIn("1" * 64, first)
        self.assertIn("still has pending decisions", first)
        self.assertIn("placement-preview", first)

        update_workspace_checkpoint(
            workspace,
            prepared.snapshot_root,
            stage="placement published",
            structure_digest="1" * 64,
            placement_proposal_digest="2" * 64,
            placement_review_digest="5" * 64,
            placement_review_complete=True,
            acceptance_digest="6" * 64,
            next_action="Review `placement-followup.md`.",
        )
        second = workspace.readme_path.read_text(encoding="utf-8")
        self.assertEqual(second.count(CHECKPOINT_START), 1)
        self.assertNotIn("still has pending decisions", second)
        self.assertIn("placement published", second)
        self.assertIn("6" * 64, second)
        self.assertIn("placement-followup.md", second)


if __name__ == "__main__":
    unittest.main()
''', encoding="utf-8", newline="\n")
