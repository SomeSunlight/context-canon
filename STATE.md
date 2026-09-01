# Current State

The accepted `main` baseline remains PR #12, squash-merged as:

`bac1f52048b3d82cedb00b04fccd114607c4c915`

PR #13 on `agent/onboarding-placement-publication` remains the active **draft, unmerged** review branch. The project owner is now exercising the workflow directly on the real `ai-workstation` onboarding and has explicitly allowed corrections discovered during that review. This is not merge approval.

## What is implemented in PR #13

The placement proposal remains the strict machine/LLM contract, while `contextcanon-onboarding/STEP-07-placement.md` is the human gate. The editable review is destination-first and can change acceptance, destination, kind/action, title and maintained wording. Canonical Rule and Topic IDs are allocated once on the human side and remain stable across review/preview cycles. Invalid or duplicate stable human-side authoring IDs are rejected when the review is loaded, before preview/publication.

Placement distinguishes `overview`, `rule`, `topic-resource`, `ordinary-documentation`, `state`, `plan`, `authority-mapping` and `unresolved`, with placement actions appropriate to those semantics. Clear source wording can remain exact; light edits and synthesis stay explicit.

Reusable Sources have two visibly different origins:

- `evidence-derived` — the semantic pass found reuse from the supplied exact Source catalog;
- `owner-selected` — the project owner deliberately adds a supplied exact Source independently of what frozen project Evidence claimed.

Both remain bound to exact Node/version/normalized/package identity. Publication resolves durable Git locator, exact commit and Node path instead of writing a transient local checkout path. The final publication preview keeps the Source name, origin, version, package digest and Git provenance visible before mutation.

`contextcanon onboard placement-preview` renders exact per-Node `CONTEXT.src.md` deltas, Source changes, durable follow-ups and deferred mutable-Markdown cleanup candidates without mutating the project. `contextcanon onboard placement-publish` revalidates frozen Evidence and review identity, refuses stale Node source after preview, installs exact Source packages, compiles touched Nodes before writing generated output, writes an exact acceptance record, and rolls back its own changes on failure.

The structure review treats ordinary `project-documentation` Markdown as mutable by default. Paths proposed as `authoritative-reference` or `imported-corpus` are preselected as fixed candidates in the human review and can be corrected there; fixed Markdown may be referenced/mapped but is excluded from destructive cleanup planning.

## Owner-review corrections now implemented

The live `ai-workstation` review clarified several UX and semantic requirements that were under-specified in the earlier review candidate.

### Semantic shelves are not repository folders

The structure-discovery instruction now says explicitly that the current repository directory tree is Evidence, **not the taxonomy ContextCanon must preserve**. A non-root Node may use an existing repository directory or a new repository-relative directory that does not exist yet when that is the clearest durable semantic landing point.

This is particularly important for document-heavy projects where many unrelated documents may currently share one folder. The owner first edits the semantic shelf map; structure materialization then creates accepted missing Node directories/skeletons safely. Focused regression coverage exercises a genuinely absent `knowledge/operations` path and proves preview/materialization creates it rather than forcing the Node onto an existing directory.

### The visible onboarding workspace is now the operator runbook

`contextcanon-onboarding/README.md` now presents the workflow as an nine-step numbered sequence from Evidence freeze through placement publication. It visibly marks:

- external LLM handoff 1 — coarse structure;
- human gate 1 — `STEP-03-structure.md`;
- external LLM handoff 2 — placement;
- human gate 2 — `STEP-07-placement.md`.

The checkpoint remains the last ContextCanon-validated state, not a live watcher. Placement checkpoint updates now also retain the exact supplied `--catalog-package` input paths so later commands no longer rely on remembering them from chat/prose. `--owner-source` is explicitly documented as a **one-time review-creation choice**: once written into `STEP-07-placement.md`, preview/publication load that choice from review state and do not require the flag again.

This is intentionally still a visible onboarding workspace rather than pretending a temporary migration workflow is already an ordinary canonical project Context Node. The current correction solves the concrete operator problem with a self-contained runbook/checkpoint without inventing a special transient Node type.

### `promote` means one canonical maintenance surface

The intended steady state is now explicit: when an accepted placement uses `promote`, the destination ContextCanon surface becomes the **single canonical maintenance surface for that meaning**.

Initial placement publication still leaves README/CONTRIBUTING/docs untouched for adoption safety. Any identical source prose that therefore remains is migration debt, not a second authority and not the desired final architecture.

A later cleanup may leave:

- a concise human-facing orientation plus a mechanically derived link to the owning Context Node;
- a reference only;
- or nothing when removal keeps the familiar document clear.

Friendly, informal or simplified wording is allowed in the orientation layer when it improves human understanding. What is forbidden as a steady state is maintaining the same complete rule/explanation independently in both the Node and the old document.

The separate technical contract is now recorded in `nodes/internal/framework-development/docs/onboarding-cleanup.md`. It binds cleanup to exact accepted placement/source bytes, requires whole-document diff review, keeps fixed Markdown and Topic/Resource authorities out of destructive cleanup, and separates semantic replacement suggestions from deterministic mutation. Broad automatic deletion is deliberately **not** implemented yet; the command UX remains unfrozen until another real onboarding validates the simplest flow.

## Owner-testing UX hardening

The second direct `ai-workstation` test exposed an operator-level failure even though the semantic mechanics were working: the workflow still made a returning user reconstruct similar commands, long digests, Source options, hidden validation steps, and artifact order from memory. That is now treated as a product defect, not user documentation debt.

The visible workspace now makes `PLAN.md` the executable operator console. It has nine numbered steps, includes Placement Validate as explicit Step 6, renders exact snapshot-bound copy/paste commands, remembers Source-catalog inputs and owner-selected Source state, and numbers artifacts so alphabetic file order follows the workflow (`STEP-02a-...` through `STEP-09-...`). CLI `--help` uses those same names.

`contextcanon onboard reset <snapshot> --from N` is now a safe testing primitive. Structure materialization and placement publication journal the ContextCanon-managed before/after bytes. Reset verifies the recorded after-state before rollback, preserves frozen Evidence, and refuses to overwrite later human edits. Older pre-journal runs get only a conservative cleanup of unmistakable untouched onboarding skeletons. Opening/resetting an older owned workspace refreshes its framework-owned PLAN to the current runbook rather than leaving stale step numbers behind.

If the visible workspace has been deleted entirely, reset now recreates the ContextCanon-owned workspace as well. The recreated `PLAN.md` is immediately bound to the preserved Evidence snapshot, marks the requested restart checkpoint, and contains the concrete restart/reset commands instead of an empty command placeholder. A foreign existing directory is still never taken over.

The placement reasoning pass also performs the semantic condensation now, while the owner is already thinking about the meaning: stable Overviews are concise summaries rather than copies of volatile version/platform prose; version/compatibility belongs in state; long snake sentences should be split into atomic findings/bullets; and architecture documents are not retained as Resources merely because of their filename when their durable semantics belong canonically in Nodes. Overview/State/Plan wording is presented to the human as `Summary` in the placement review.

## Real `ai-workstation` vertical validation

The earlier publication proof reused the original project bytes rather than a new live-repository interpretation:

- project commit: `4106fec3f7726d6c9bfedd70d30d9ed025b7c166`;
- reproduced frozen Evidence: `2a926bf353b252db4039e5c4b63b39abad6bab46c11982e88b3eb17e19cf203d`;
- accepted existing root Node ID: `aea56adf-2a26-43f0-b712-3bbeab7a3097`;
- seven accepted child/group Nodes;
- 33 Evidence-based placement findings;
- owner-selected Development Workflow Source `c4c94726-3cc7-4df6-b779-72bbf9c06f40`, package `1d82c87e4f4140791f354c9d9479df845eb65c13fce1c664ecb05bec9532c8eb`.

The human review resolved the Evidence-only version ambiguity as owner input: `pyproject.toml` should track the repository release version represented by CHANGELOG rather than leaving two stale independent version streams.

The disposable-clone publication test proved all of the following in one vertical run:

- all 8 accepted Context Nodes received their reviewed local deltas;
- existing root identity and unrelated authored root content survived;
- child Node IDs remained stable;
- frozen Evidence-covered project files remained byte-identical;
- root and child-local Rules, Overviews and cross-directory Topic/Resource routing materialized correctly;
- Development Workflow was pinned with exact package identity and durable Git provenance;
- accepted state/plan/ordinary-documentation semantics remained visible as 6 durable follow-ups;
- every resulting Node compiled with zero generated drift;
- the second preview showed the placement already materialized;
- the second publication changed 0 Context sources and reproduced acceptance digest `a206e3423e9ffaccf7c3f7a1a0e2f140251a834f3c6eaf9764cd952b95e509c4`.

The real frozen Evidence did not produce an accepted authority-mapping finding, so none was invented merely to exercise that feature. Fixed-authority mapping remains covered by deterministic framework validation/tests.

## Current verification state

The owner-testing hardening candidate now has **142 deterministic tests** after adding focused coverage for numbered CLI help and stale-PLAN refresh during reset. The preceding temporary hardening workflow already proved the 139-test implementation slice plus zero generated drift and removed its own temporary files before product commit `ee4c63772d0fe648347359f5e725b61c44452d54`.

This final documentation/help polish is validated by a temporary self-deleting workflow that runs Python compilation, all 142 tests, `contextcanon build --all .`, `contextcanon check --all .`, and `git diff --check` before it is allowed to create the clean product commit. The temporary workflow and helper script are removed from that commit.

Because bot-authored commits can produce GitHub's `action_required` result for the normal pull-request workflow, the clean product tree must then receive a repository-authored no-content checkpoint commit and a normal exact-head PR workflow. That final CI result, not the temporary harness alone, is the review proof.

## Latest reset recovery verification

The missing-workspace reset correction is covered by a direct regression test and passed ordinary PR workflow #482 / run `33498482979`. The final repository-authored checkpoint must retain the same product behavior, zero generated drift, and no temporary finalizer files before the owner reinstalls for the next `ai-workstation` run.

## Boundaries that intentionally remain

PR #13 still does **not** perform destructive onboarding cleanup. Initial publication remains non-destructive. The later cleanup contract is now explicit, but implementation awaits another real review of the desired user experience rather than growing a second long ceremony prematurely.

The project also does not yet choose a remote Node-library registry/distribution architecture, invent a special GroupNode type, make navigation hierarchy imply Source inheritance, automatically splice state/planning findings into arbitrary prose, or build a browser UI. Those remain separate questions to answer from further real use.

Normal ContextCanon-native project evolution is distinct from one-time migration onboarding: after adoption, humans edit canonical `CONTEXT.src.md`/project documentation and use normal build/check workflows rather than repeatedly re-running migration Evidence analysis.

## Immediate next step

Obtain the ordinary GitHub PR workflow on the exact clean product head. If green, keep PR #13 draft/unmerged and let the project owner reinstall that exact SHA and restart the real `ai-workstation` onboarding. The intended test UX is now deliberately simple: after reset/restart, open `contextcanon-onboarding/PLAN.md` and follow/copy it from top to bottom. Do not merge or begin destructive duplicate cleanup without explicit owner approval.

## Latest live Step-4 owner-test verification

The next direct `ai-workstation` test exposed two additional operator issues and one real Step-4 collision bug. The generated PLAN now places an explicit one-line pointer immediately above the checklist to the detailed copy/paste section, and the exact command section defines one shell-native `SNAPSHOT` variable so the long content-addressed Evidence path is written once rather than repeated through every command.

Structure preview/materialization no longer treats a provably ContextCanon-generated root `CONTEXT/` directory or the root `.context/onboarding/` namespace as a project-owned collision merely because the namespace exists. Recovery remains conservative: a missing root `CONTEXT.src.md` is recoverable only when `.context/package.json`, generated `.context/context.yaml`, or prior ContextCanon acceptance state proves one unambiguous stable root Node ID. Existing generated `CONTEXT.md`/`CONTEXT/` bytes are accepted only when their generated ownership can be verified; a foreign `CONTEXT/` directory still fails before mutation. Root recovery preserves the established Node ID, name, and version rather than allocating a replacement UUID.

Focused coverage reproduces the exact failing shape and also proves the foreign-directory refusal. The complete suite now passes **144/144 tests**, followed by full `contextcanon build --all .`, `contextcanon check --all .`, and `git diff --check` with zero generated drift. PR #13 remains draft and unmerged; the next action is continued project-owner testing on a normal exact-head CI checkpoint.
