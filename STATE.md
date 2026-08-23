# Current State

ContextCanon has moved beyond architecture-only prototyping and its first external proof. **Compiler 0.4 is the accepted stable baseline on `main`**, including immutable external Sources, reviewed Source updates, generic Git candidate transport, and atomic publication/recovery.

The active development branch is `agent/reviewed-onboarding` / draft PR #6. Its purpose is to add a semantic onboarding workflow **above** deterministic compiler truth without letting an LLM directly create accepted project context.

## Accepted Compiler 0.4 baseline

The accepted compiler boundary is `CompiledPackage`:

```text
local Source Node ──compile──────────┐
                                     ├──> CompiledPackage ──> composition
accepted external package ──verify──┘
```

Accepted external packages are pinned by stable Node/version identity plus both semantic and exact package digests, stored under the consumer at `.context/sources/<package-digest>/`, and used offline by normal `build`.

Source updates remain explicit change requests:

```text
source fetch   → candidate only
source review  → exact package diff + consumer structural validation + receipt
source accept  → exact accepted package + updated pin
```

A normal build never dereferences update transport metadata or repairs missing accepted state through hidden network access.

## Active reviewed-onboarding substrate

The first onboarding stable point is intentionally deterministic even though onboarding as a whole is semantic.

The implemented working pipeline is:

```text
existing Git repository
      ↓
contextcanon onboard prepare
      ↓
content-addressed frozen evidence snapshot
      ↓
semantic proposal generation (LLM not yet supplied by ContextCanon)
      ↓
contextcanon onboard validate
      ↓
strict proposal bound to exact evidence
      ↓
future human review and explicit acceptance
      ↓
canonical ContextCanon authoring
      ↓
normal deterministic compiler
```

### Evidence preparation

`contextcanon onboard prepare <project>` works before a repository has any Context Node.

Automatic inventory is based on:

```text
git ls-files --cached --others --exclude-standard
```

The selector deliberately chooses likely context carriers instead of ingesting the whole repository: root project documents, text documentation directories, known agent instructions, selected project/build manifests, and GitHub Actions workflows. Ordinary source code is not automatic evidence.

Additional safe files can be included explicitly with repeated `--include` arguments, including otherwise Git-ignored files when the operator deliberately chooses them.

Prepared evidence is frozen under:

```text
.context/onboarding/<evidence-digest>/
├── manifest.json
└── evidence/<original paths>
```

The manifest records exact path, reason, size, SHA-256 and copied location for every included file plus deterministic exclusions. Absolute checkout paths and timestamps are absent from identity.

Safety boundaries include common secret/key/environment/generated paths, symlinks, UTF-8-only text, **1 MiB per file**, and **16 MiB total evidence**. The total limit prevents a large documentation tree from creating an unbounded snapshot even when every individual file is small.

Matching snapshots are verified and reused. Modified/corrupt content-addressed state fails rather than being silently repaired. New snapshots are staged before publication.

### Proposal validation

Semantic output is represented by `contextcanon/onboarding-proposal/v0`, distinct from Official Context and from accepted authored source.

Every proposal item requires:

- proposal-local stable ID;
- one supported classification;
- title and rationale;
- explicit high/medium/low confidence;
- at least one exact evidence reference with path, SHA-256 and line range;
- a strict kind-specific payload.

Supported classifications currently cover local Rule, existing Source, candidate reusable Node, Topic/Resource, state/planning, ordinary documentation, and unresolved question.

`contextcanon onboard validate <snapshot> <proposal.json>` reloads the evidence snapshot and verifies its exact file set, hashes, evidence digest and supported Evidence v0 safety policy before validating the proposal. A rehashed manifest that weakens the preparation policy must still fail on consumption.

A valid proposal receives a deterministic `proposal_digest`. That digest identifies one exact review artifact; **validation is not acceptance** and does not claim the semantic interpretation is correct.

## Current quality gate

Before the final PR #6 merge, the exact branch head must pass:

- the full pre-existing Compiler 0.4 regression suite;
- onboarding evidence positive/negative cases;
- proposal schema/provenance/hash/line-range cases;
- weakened-policy and aggregate-size regression cases;
- `contextcanon check --all .` with zero dogfood drift.

The previous PR head passed 64 tests plus zero drift. The final hardening adds two regressions, so the expected final suite is **66 tests**. This count is not treated as accepted until the final exact head passes CI.

No LLM participates in evidence selection, evidence identity, snapshot verification, proposal structural/provenance validation, proposal identity, compiler truth, package verification, Source transport state transitions, review receipts, or Source acceptance.

## Next slice after this stable point

The next slice supplies the **framework-owned harness-neutral LLM onboarding instruction** instead of requiring an operator to invent a prompt.

That instruction must consume one exact frozen evidence snapshot and produce the validated proposal schema. It must require evidence-only reasoning, explicit uncertainty/contradictions, provenance and rationale, and a disciplined distinction between project-local context, existing reusable Sources, candidate generic Nodes, Topic/Resource material, state/planning, ordinary documentation, and unresolved questions.

Likely reusable practices must be compared against an available ContextCanon Node catalog before being duplicated locally. New reusable Nodes remain separately reviewable and are never auto-published.

After the instruction layer comes the human review/acceptance boundary. Only explicit acceptance may create or replace canonical `CONTEXT.src.md` or related authored context, followed immediately by deterministic ContextCanon validation/build.

See [PLAN.md](PLAN.md) for the ordered implementation and larger 1:1 validation steps.
