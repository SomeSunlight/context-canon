# Current State

ContextCanon has moved beyond architecture-only prototyping and its first external proof. **Compiler 0.4 is the accepted stable baseline on `main`** after PR #3 was squash-merged as commit `7fd1aa64fb1f853a2bd4be84a9ed1afaf07d5de9`.

## Accepted baseline on main

The accepted baseline now includes deterministic self-hosting, real-project/harness validation, inherited Rule `Remove`/`Override`, transitive provenance and conflict diagnostics, canonical semantic normalization, exact compiled Context diff, immutable external Source packages, reviewed Source updates, generic Git candidate transport, and atomic publication/recovery guarantees.

The practical conclusion is settled: ContextCanon is useful enough to build central reusable functionality and then apply it aggressively to larger projects.

## Compiler 0.4

Compiler 0.4 adds immutable external Sources and reviewed Source-update acceptance while preserving the rule that normal compilation is deterministic and offline with respect to external Sources.

The common semantic boundary is `CompiledPackage`:

```text
local Source Node ──compile──────────┐
                                     ├──> CompiledPackage ──> composition
accepted external package ──verify──┘
```

A reusable package contains:

```text
.context/package.json
CONTEXT.md
CONTEXT/              optional
```

`.context/package.json` preserves the complete compiled state needed by descendants: effective Rules, statements, rationale, groups, stable origin, Override provenance, Remove provenance, local Changes and Topics, transitive Source dependency identities, file hashes, `normalized_digest`, and `package_digest`. Generated human presentation is never parsed back into semantic truth.

Accepted external packages live under the consumer Node at:

```text
.context/sources/<package-digest>/
```

This is reproducible accepted project state. A normal `build` uses only this pinned package, verifies Node ID/version/both digests/package files, and never dereferences Source transport metadata. Missing or corrupt accepted state is an error rather than permission to fetch.

Candidate packages are separate:

```text
.context/candidates/<package-digest>/
```

The accepted update workflow is:

```text
contextcanon source fetch <source-id> --node <consumer>
        ↓
Git candidate only
        ↓
contextcanon source review <source-id> <candidate> --node <consumer>
        ↓
exact package diff + real consumer structural validation + review receipt
        ↓
contextcanon source accept <source-id> <candidate> --node <consumer>
        ↓
new accepted package + exact updated pin
```

Review receipts are bound to the exact consumer `CONTEXT.src.md`, current accepted Source state, candidate identity, deterministic diff, and successful structural validation. Acceptance rejects stale review state.

Git transport is generic rather than GitHub-specific. Pinned Sources may declare `transport="git"`, `ref="..."`, and safe relative `node-path="..."`. `node-path` supports repositories containing several Context Nodes while stable Node ID remains identity.

## Recovery and publication guarantees

Candidate and accepted packages are copied into sibling staging directories, verified there, and only then atomically published to their content-addressed destination.

Review receipts and the canonical Source pin use sibling temporary files followed by atomic replacement. The Source-pin temporary file is flushed and `fsync`ed before publication.

If the new immutable package is already installed but the final `CONTEXT.src.md` pin swap fails, the previous canonical source bytes remain intact. The new package may remain as harmless unreferenced immutable state, while ordinary compilation continues against the old accepted pin. A regression test simulates this final replace failure.

## Quality status

The deterministic suite is **45/45 green**. It covers package round-trip after deleting the Source repository, semantic and byte-level tampering, offline pinned composition, missing/mismatched accepted packages, deterministic review/accept, stale review receipts, dangling consumer Changes, a real local Git repository moving from accepted v1 to candidate v2 without changing build output before explicit acceptance, and atomic recovery from a failed final Source-pin publication.

Gateway, Foundation, and Framework Development dogfood packages were regenerated from the final Compiler 0.4 implementation and documentation. The final exact PR head passed the full suite and `contextcanon check --all .` with zero drift before the squash merge.

CI drift diagnostics include newly generated files in textual drift output and upload a one-day exact generated snapshot only on failure, including hidden `.context/` state. This avoids reconstructing compiler output manually when drift occurs.

No LLM participates in compiler truth, package verification, Source transport state transitions, review receipts, or acceptance.

## Next active block: reviewed LLM-assisted onboarding

The next larger 1:1 test must no longer rely on this conversation or a human manually curating ContextCanon files first. ContextCanon itself will provide a reproducible onboarding workflow for a pre-existing repository.

The intended boundary is:

```text
existing project
      ↓
deterministic inventory
      ↓
framework-supplied harness-neutral LLM instruction
      ↓
reviewable proposal with provenance
      ↓
mandatory human review
      ↓
explicit acceptance
      ↓
CONTEXT.src.md + Sources + Topics + Resources
      ↓
normal deterministic compiler
```

The inventory step interprets nothing semantically. The LLM proposal must trace each proposed item to inspected repository material, expose uncertainty or contradictions, and classify information rather than dumping everything into one local Node. At minimum it must distinguish project-local Rules, existing reusable Sources, candidate reusable/generic Nodes, Topic/Resource material, state/planning, ordinary documentation, and unresolved questions.

Cross-project practices such as Python development conventions, testing policy, writing/user-guidance style, and language conventions are explicit candidates for reusable Nodes. The LLM should compare such candidates against the available ContextCanon Node catalog before duplicating them locally. A proposed new generic Node is itself reviewable and is never auto-published.

Onboarding is not destructive migration: useful `README.md`, `CONTRIBUTING.md`, architecture docs, and similar familiar repository documents remain useful in their normal roles.

The onboarding implementation starts on a fresh branch from the accepted 0.4 `main` baseline.

See [PLAN.md](PLAN.md) for the ordered implementation and validation steps.
