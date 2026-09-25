# Onboarding design and trust contract

This is a **framework-development document**, not the operator command reference. It records the onboarding architecture, trust boundaries, compatibility contracts, and implementation rationale used when changing ContextCanon itself.

For normal project onboarding, use the root user documentation: `docs/onboarding.md` for the walkthrough and `docs/onboarding-cli.md` for commands.

Use this design document when you already have a Git repository and want to understand or change how ContextCanon turns existing knowledge into structured ContextCanon context.

You do **not** need an existing `CONTEXT.src.md`, and you do not need to decide the final ContextCanon structure before you start.

## Current architecture in one picture

The current first-adoption path has **three distinct concerns** before publication:

1. **delivery triage** — decide which existing artifacts are direct source, need interpretation, are lookup-only, or should be ignored;
2. **shelf design** — infer and human-review the Context Node structure before placing detailed meaning;
3. **placement** — decide where reviewed meaning belongs, including reusable Context composition and reviewed source transformations.

```text
existing project deliveries
        ↓
STEP 01  human cleanup before durable references
        ↓
STEP 02  deterministic Git-visible inventory
         + human triage: source / interpret / lookup / ignore
        ↓
STEP 03  immutable reviewed Evidence snapshot
        ↓
        ├── [coming soon] explicit interpretation of raw/ambiguous Evidence
        ↓
STEP 04  structure instruction → reasoning model proposal
        ↓
STEP 05  human structure review
        ↓
STEP 06  deterministic structure preview/materialization
        ↓
STEP 07  human reusable-Context composition
        ↓
STEP 08  placement instruction → reasoning model proposal
        ↓
STEP 09  deterministic placement validation
        ↓
STEP 10  human placement + source-transformation review
        ↓
STEP 11  deterministic publication preview
        ↓
STEP 12  explicit transactional publication
```

The future interpretation stage is deliberately shown before shelf/placement reasoning but is not yet an implemented numbered step. Today, `interpret` is already a first-class triage decision: the exact raw bytes enter Evidence but are marked as material whose statements must not silently become canonical truth.

The reasoning model is replaceable. It proposes structure or placement only inside an exact task/Evidence boundary. Deterministic code owns identity, hashes, validation, state transitions and publication. The project owner owns architecture and acceptance.

## Why shelves come before books

Repository archaeology can suggest useful groupings, but filesystem layout and current prose do not automatically define the intended semantic architecture. The structure pass therefore proposes coarse Node boundaries first; the owner edits them; only then may placement reasoning distribute durable meaning.

This separation also allows one Git repository to contain many Context Nodes. Repository nesting is evidence and location, not implicit semantic inheritance. Parent and reusable Source relationships remain explicit.

## Recovery is part of the architecture

Onboarding is designed for live projects, not disposable clones. The normal recovery entry from the Git root is:

```text
contextcanon onboard reset . --from <STEP>
```

Reset semantics are intentionally progressive:

- STEP 01 — roll back later managed onboarding mutations, remove the owned onboarding workspace and all onboarding machine state, and remove ContextCanon's marked onboarding `.gitignore` block;
- STEP 02 — keep the initialized workspace but discard inventory/Evidence/later work;
- STEP 03 — keep the reviewed inventory CSV plus scope/rules, but discard accepted Evidence/later work;
- STEP 04–12 — preserve accepted inventory + frozen Evidence and roll back managed semantic work from the requested step onward.

The journal refuses to overwrite project files that changed after ContextCanon recorded them. Reset is therefore a bounded recovery mechanism, not a disguised repository checkout.

## Current operator surfaces

The root user documentation owns the human workflow:

- `docs/onboarding.md` — conceptual walkthrough;
- `docs/onboarding-cli.md` — stable command reference;
- generated `contextcanon-onboarding/PLAN.md` — concrete run/checkpoint console;
- generated `STEP-02-inventory-guide.md` — inventory CSV field/value reference.

This framework-development document records *why those surfaces behave that way* and the trust contracts behind them.

# Technical reference

## Implemented workflow

```text
onboard init
  → STEP 01 tidy guidance
  → STEP 02 inventory + human triage
  → STEP 03 prepare reviewed immutable Evidence
  → STEP 04 structure instruction / external reasoning proposal
  → STEP 05 human structure review
  → STEP 06 structure preview + materialization
  → STEP 07 reusable Context review
  → STEP 08 placement instruction / external reasoning proposal
  → STEP 09 placement validation
  → STEP 10 human placement/source-edit review
  → STEP 11 exact publication preview
  → STEP 12 transactional publication
```

Every semantic proposal is downstream of exact frozen Evidence. Every publication is downstream of a human gate. The generated PLAN carries the exact current command/checkpoint so the operator does not reconstruct snapshot IDs or prior decisions from memory.

The current structure-first path supersedes the older single-pass first-adoption workflow for normal use. The older proposal/review/accept contracts remain implemented only as compatibility behavior and are documented later in this file as legacy contracts.

## Reviewed inventory preflight contract

The normal structure-first first-adoption path separates **repository inventory** from the later immutable Evidence snapshot. It also gives the operator a visible runbook before any inventory decision exists:

```text
contextcanon onboard init .
        ↓
contextcanon-onboarding/PLAN.md
        ↓
STEP 01  tidy obvious repository/document clutter before durable references exist
STEP 02  contextcanon onboard inventory → STEP-02-inventory.csv → human review
STEP 03  contextcanon onboard prepare --inventory ... → immutable Evidence snapshot
```

`onboard init` creates only the ContextCanon-owned visible workspace, including the generated PLAN and `STEP-02-inventory-guide.md`. It does not scan or accept project material. The generated PLAN is the operator console; the guide is the field/value reference for the CSV.

STEP 01 is guidance only. ContextCanon does not move/delete project files during first adoption.

STEP 02 starts from Git-visible tracked and non-ignored untracked files in the whole repository or one/more explicitly selected repository-relative directories. ContextCanon-owned `.context/` state and the visible onboarding workspace are outside the project-material inventory domain. The generated CSV is a human review surface; exact scanning/state bookkeeping remains machine-owned under `.context/onboarding/`.

The Git persistence boundary is explicit. `onboard init` maintains one bounded block in the repository `.gitignore` that ignores the visible workspace and transient/heavy `.context/onboarding/` material while re-including exactly `inventory-state.json` and `inventory-acceptance.json`. The former records portable inventory scope/rules; the latter records the accepted per-path baseline and owner-reviewed semantic columns. They are intentionally compact and Git-visible so a clone can reconstruct the inventory review surface. If no explicit `--directory` or `--rule` arguments are supplied on a later refresh, STEP 02 reuses the durable state.

Unaccepted CSV edits remain workspace state. STEP 03 is the durability boundary: only then is the reviewed inventory written into the compact acceptance baseline. Frozen Evidence snapshots remain reproducible cache/review material rather than normal Git history. Canonical semantic publication later carries accepted structure/Source/placement meaning into ContextCanon authoring itself; the visible onboarding workspace is not a second canonical authority.

This restore behavior preserves inventory decisions and drift detection. It does not silently turn first-adoption publication into an update protocol for an already adopted project; semantic re-onboarding/merge remains a separate reviewed contract.


The normal inventory intentionally does **not** enumerate every visible source-code file. Ordinary language source suffixes are omitted by default because large, fast-changing code trees would turn the onboarding table into a per-file change tracker. A deliberate `--rule GLOB=KIND:HANDLING` may opt selected source files back into the inventory. A later code-aware selection mechanism may replace this coarse boundary without changing the human acceptance principle.

The reviewed row has two independent semantic axes:

- **kind** says what the artifact roughly is: `document`, `transcription`, `structured-data`, `configuration`, `source-code`, `raw-record`, `generated`, `binary`, `other`, or `unknown`;
- **handling** says what first-adoption Evidence should do with it:
  - `source` — include the exact bytes as direct project Evidence;
  - `interpret` — include the exact bytes, while recording that the material is raw/ambiguous input whose statements must not silently become canonical truth;
  - `lookup` — keep explicitly known material outside the eager Evidence set;
  - `ignore` — intentionally exclude it;
  - `undecided` — block STEP 03.

`transcription` is a technical representation kind, not semantic interpretation. Opaque office/PDF originals default to `binary / ignore`. If `name.pdf`, `name.docx`, `name.pptx`, or a similar opaque document matters for semantic onboarding, the owner supplies a faithful same-directory, same-basename `name.md`. ContextCanon then recognizes that Markdown companion as `transcription / source` and keeps the original ignored. The generated `hint` column explains missing/recognized companions. Semantic condensation belongs later; a transcription should remain faithful to the original.

`.gitignore` is classified truthfully as configuration but defaults to `ignore`; repository ignore mechanics are not project semantic Evidence merely because the file is visible.

Git may expose a submodule/gitlink as one index path while its working-tree path is a directory. Reviewed inventory classifies that path as `other / ignore` with rule `git-directory-entry`, does not hash or descend into it, and tells the operator to onboard the nested repository separately if its content matters. STEP 03 refuses a directory/gitlink row changed to `source` or `interpret` instead of attempting a file read.

Deterministic default rules may prefill classification for familiar documentation, structured data, raw-record names, generated paths and opaque formats. They are convenience only. The owner may edit the human semantic columns directly, and optional repeatable `--rule GLOB=KIND:HANDLING` inputs customize deterministic defaults without adding an LLM to the inventory stage.

STEP 02 is repeatable **when the repository files changed**. It is not rerun merely because the owner edited the CSV. Refresh compares live material with the previous/accepted per-path SHA-256 baseline and surfaces `new`, `changed`, `missing`, or `unchanged`. Human semantic columns for known paths are preserved. Legacy CSV status `present` is accepted and normalized to `unchanged`.

STEP 03 is the inventory acceptance boundary. Before freezing Evidence, ContextCanon refuses:

- live in-scope non-source-code files omitted from the CSV;
- stale listed SHA-256 values;
- non-ignored missing files;
- `undecided` handling;
- blocked/sensitive paths selected for inclusion;
- `source` / `interpret` rows without a short description.

Only `source` and `interpret` rows enter the snapshot. The accepted inventory identity and per-file reviewed baseline are stored separately from the content-addressed Evidence package so later inventory refresh can explain repository drift.

For compatibility, `contextcanon onboard prepare .` without `--inventory` retains the earlier conservative selector. The generated current onboarding PLAN uses the reviewed inventory path; compatibility behavior must not become the hidden definition of normal first adoption again.

## Evidence snapshot contract

`onboard prepare` freezes the exact project evidence offered to the later semantic step. Every included file is bound by repository-relative path, byte size, SHA-256 hash, selection reason, and exact copied bytes.

The legacy automatic Evidence selector and the reviewed inventory scanner both start from Git's repository visibility rules:

```text
git ls-files --cached --others --exclude-standard
```

Tracked files and non-ignored untracked files are visible. Git-ignored files are not silently offered. In the reviewed path, the CSV decides which visible files become Evidence. In the compatibility path, the older default selector chooses familiar context carriers and explicit `--include` may add an otherwise ignored safe file, subject to path, secret, size, symlink, and UTF-8 checks.

Current deterministic evidence boundaries include:

- common credential, secret, environment and key paths;
- `.git/`, `.context/`, virtual environments, `node_modules`, and similar generated/internal trees;
- symlinks;
- UTF-8 text only;
- **1 MiB per file**;
- **16 MiB total evidence**.

Matching content-addressed snapshots are verified and reused. Modified or corrupt snapshot content fails rather than being silently repaired.

## Legacy single-pass semantic instruction contract

The sections from here through **Accepted onboarding artifacts** describe the earlier single-pass compatibility workflow (`prepare → instruction → proposal → validate → review → accept`). They remain useful trust-contract history and compatibility documentation, but they are **not** the current operator path or current step numbering.


`contextcanon onboard instruction <snapshot>` produces schema:

```text
contextcanon/onboarding-instruction/v0
```

The exact instruction bytes are deterministic for one verified evidence snapshot plus one explicitly supplied Source catalog. The instruction itself is written only to stdout; its SHA-256 is reported on stderr.

The fully rendered instruction is capped at **4 MiB (4,194,304 UTF-8 bytes)**. An oversized instruction fails rather than being truncated.

Evidence and reusable Source package contents are untrusted review data, not meta-instructions. ContextCanon cannot prove the hidden prompt composition of an arbitrary external harness, so the operator must run the semantic review in a configuration where the generated ContextCanon assignment controls the task and frozen evidence is read as data.

## Legacy single-pass semantic proposal contract

The LLM returns:

```text
contextcanon/onboarding-proposal/v0
```

Every proposal item requires:

- a stable proposal-local ID;
- one supported classification;
- title and rationale;
- confidence `high`, `medium`, or `low`;
- one or more evidence references with path, SHA-256 and line range;
- a strict kind-specific payload.

For newly generated `existing-source` findings, the payload carries stable Source Node ID/name plus exact Source version, normalized digest and package digest. Historical v0 findings without those three exact identity fields remain structurally readable, but acceptance refuses to publish them until corrected/regenerated.

`onboard validate` reloads and verifies the evidence snapshot, validates every field/reference, and computes a deterministic `proposal_digest` over the normalized proposal.

Validation proves the review object is structurally bound to exact evidence. It does not prove semantic correctness.

## Legacy single-pass human review contract

The review schema is:

```text
contextcanon/onboarding-review/v0
```

It binds:

- exact `evidence_digest`;
- exact `proposal_digest`;
- human-owned canonical Node ID/name/version;
- exactly one decision per proposal item in proposal order.

Allowed decisions are exactly:

```text
pending
accept
reject
```

The normalized review receives its own deterministic `review_digest`.

Creating a review cannot publish project context. Loading a review whose `proposal_digest` no longer matches the proposal fails.

A default Node ID is a fresh UUID created once with a new review, not a digest-derived identity. Reopening that review reuses the stored ID.

## Legacy single-pass acceptance contract

Final publication is represented by:

```text
contextcanon/onboarding-acceptance/v0
```

Acceptance requires:

- exact verified Evidence v0 snapshot;
- exact validated Proposal v0;
- exact matching Review v0;
- zero `pending` decisions;
- unchanged live bytes for every frozen evidence file;
- exact immutable package identity match for every accepted `existing-source` item;
- successful staged compilation before canonical source publication;
- no collision with pre-existing paths that the staged Node would generate, and no pre-existing `CONTEXT/` tree;
- successful ordinary build/check immediately after publication;
- successful acceptance-record publication, otherwise first-adoption output is rolled back.

The acceptance record stores evidence/proposal/review identities, Node identity, accepted/rejected item IDs, exact accepted Source package identities, canonical `CONTEXT.src.md` SHA-256, resulting normalized/package digests, and generated output list.

## Legacy single-pass accepted artifacts

The accepted review record is stored under:

```text
.context/onboarding/accepted/<proposal-digest>/
├── acceptance.json
├── reusable-candidates.json   # only when accepted candidates exist
└── unresolved.json            # only when accepted unresolved questions exist
```

The evidence snapshot remains separately content-addressed under `.context/onboarding/<evidence-digest>/`.

These records are review/provenance state, not extra inherited governance.

## Deterministic safety properties exercised in tests

The regression suite covers, among other onboarding acceptance cases:

- every finding begins pending;
- exact evidence lines are rendered for review;
- fresh default Node identities are not derived from identical evidence;
- changed proposal invalidates the prior review;
- pending decisions block acceptance;
- changed live evidence blocks acceptance;
- accepted local Rules/Topics compile into canonical context;
- rejected Rules are absent from canonical context but remain in the acceptance record;
- reusable candidates and unresolved questions remain separate follow-up artifacts;
- historical unbound `existing-source` findings remain readable but cannot be accepted;
- accepted reusable Sources must match the exact version and both digests inspected by the semantic reviewer;
- accepted reusable Sources continue building offline after the original Source repository is removed;
- first-onboarding v0 refuses destructive replacement of existing `CONTEXT.src.md` and generated-output collisions;
- Topic Markdown closure cannot pull a file outside frozen evidence into the accepted package;
- simulated failure while publishing the final acceptance record rolls first adoption back.

## Design invariant

**ContextCanon deterministically defines and verifies evidence, task, proposal, review binding and publication mechanics; a capable semantic model proposes meaning inside that box; an explicit human decision chooses durable project truth; the ordinary compiler verifies the result immediately.**

## Upgrading a placement published before semantic Parent edges

A placement accepted by an older ContextCanon build may already contain the reviewed Nodes and Sources while its reviewed structure hierarchy (current STEP 05) was not yet persisted as semantic Parent pins. Re-running the same exact placement preview/publication is the migration path; no new semantic LLM pass is required.

ContextCanon allows this acceptance upgrade only when the old record is the same Evidence/Structure/Proposal/Review identity, has no Parent state yet, covers every accepted structure Node, and every current `CONTEXT.src.md` still has the exact `source_sha256` recorded by that old acceptance. The migration then adds the reviewed Parent blocks/packages parent-first and replaces the acceptance record transactionally. A later human Node edit disables automatic migration and requires explicit review instead.

STEP 12 publication is journaled together with the placement acceptance file, Node sources, generated outputs and immutable package-store changes. Reset from STEP 12 after such a migration therefore restores both the pre-Parent Node tree and its exact legacy acceptance record rather than leaving machine acceptance ahead of canonical source.
