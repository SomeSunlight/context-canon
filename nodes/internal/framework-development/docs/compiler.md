# Compiler

ContextCanon has an executable deterministic core. The compiler deliberately separates authoring syntax, semantic composition, immutable package state, rendering, exact comparison, Source transport, and filesystem mutation so each layer stays testable without an LLM.

## Commands

For normal compilation:

```text
contextcanon build --all .
contextcanon check --all .
contextcanon diff <before-node-root> <after-node-root>
contextcanon diff <before-node-root> <after-node-root> --json
```

For an already accepted external Source with Git update metadata:

```text
contextcanon source fetch <source-node-id> --node <consumer-node>
contextcanon source review <source-node-id> <candidate-package> --node <consumer-node>
contextcanon source accept <source-node-id> <candidate-package> --node <consumer-node>
```

`build` and `check` always consume accepted state. They never use Source transport metadata to discover or download a newer Source.

`source fetch` is candidate discovery only. `source review` computes an exact package diff and runs the candidate through the consumer's structural composition checks. `source accept` requires the resulting review receipt before it can install the candidate and change the exact Source pin.

## Compiler structure

The implementation follows a one-way pipeline:

```text
CONTEXT.src.md
      ↓
parser.py          authoring syntax → ParsedNode
      ↓
compiler.py        local Source compile / accepted package load
      ↓
CompiledPackage   common immutable semantic Source boundary
      ↓
compose → Change → validate → collect resources → normalize/digest
      ├──────────────────────────────→ diff.py / package_diff.py
      ↓
render.py          deterministic human/machine projections
      ↓
outputs.py         exact generated output set

external update path:
Source transport metadata
      ↓
git_transport.py  candidate bytes only
      ↓
immutable candidate package
      ↓
sources.py        review receipt → explicit acceptance
      ↓
accepted package store + updated exact pin
```

The boundaries are deliberate:

- `model.py` defines typed deterministic data structures.
- `parser.py` owns constrained Markdown grammar and syntax validation.
- `compiler.py` owns semantic composition, Rule changes, conflicts, target validation, resource closure, and accepted-package resolution.
- `package.py` defines the immutable compiled package manifest, semantic normalization, exact package identity, serialization, loading, and integrity verification.
- `diff.py` compares compiled consumer Nodes; `package_diff.py` applies the same stable-identity diff model directly to immutable Source packages.
- `render.py` projects compiled truth into `CONTEXT.md`, `.context/context.yaml`, and thin harness adapters.
- `outputs.py` compares/writes compiler-owned generated output.
- `git_transport.py` retrieves candidate bytes through generic Git but knows nothing about Rule composition.
- `sources.py` owns deterministic candidate review receipts and explicit acceptance.
- `cli.py` only orchestrates these layers.

## Compiler invariants

Changes should preserve these properties:

1. **One-way data flow.** Generated presentation is never parsed back into semantic truth.
2. **No LLM in deterministic truth.** Identity, composition, package verification, diff, transport state transitions, and hashes are reproducible.
3. **No silent approximation.** Invalid, ambiguous, dangling, incomplete, or corrupt state fails clearly.
4. **Stable identity before presentation.** Rule operations and diffs bind stable IDs, not titles or paths.
5. **No implicit Source precedence.** Source list order does not resolve conflicts.
6. **Canonical semantics ignore meaningless order.** `normalized_digest` is not accidental presentation identity.
7. **Presentation order is still preserved where readers see it.** Canonical hashing must not reorder a loaded package's effective presentation.
8. **Accepted state is separate from candidate state.** Fetching a candidate cannot change normal build output.
9. **Normal build is offline with respect to external Sources.** A missing accepted package is an error, not permission to fetch.
10. **Filesystem mutation stays narrow.** Compilation can run in memory; dedicated output/acceptance layers own writes.

## What Compiler 0.4 implements

Compiler 0.4 includes all 0.3 behavior plus immutable external Source packages and reviewed update acceptance.

The deterministic core now handles:

- Node discovery, stable IDs and versions;
- local unpinned Sources inside the repository;
- immutable pinned Sources from a consumer-local accepted package store;
- a common `CompiledPackage` semantic boundary for local and external Sources;
- Source identity/version validation and dependency-cycle detection for local compilation;
- transitive Rule composition, Remove/Override, provenance, dangling diagnostics, and diamond conflicts;
- Required/Optional Topics and materialized Resource closure;
- canonical semantic normalization and exact package digests;
- deterministic Node and package diff;
- versioned `.context/package.json` manifests containing the complete compiled state required by descendants;
- full manifest/file/digest verification without needing `CONTEXT.src.md` from the Source;
- consumer-local accepted packages under `.context/sources/<package-digest>/`;
- candidate packages under `.context/candidates/<package-digest>/`;
- exact Source pins using version, `normalized-digest`, and `package-digest`;
- generic Git candidate retrieval with explicit `ref` and `node-path` for repositories containing multiple Nodes;
- structural review of a candidate in the real consumer composition before acceptance;
- deterministic review receipts bound to the exact consumer source state;
- explicit acceptance that preserves transport metadata and changes the Source pin only after successful review;
- generated `CONTEXT.md`, optional `CONTEXT/`, `.context/context.yaml`, `.context/package.json`, and thin harness adapters;
- deterministic drift checking.

No LLM participates in these operations.

## Immutable package boundary

A compiled reusable Source artifact contains:

```text
.context/package.json
CONTEXT.md
CONTEXT/              optional
```

The manifest contains complete effective Rule state rather than trying to reconstruct semantics from `CONTEXT.md`. That distinction matters: human presentation is an output, not a parser input.

A descendant therefore sees the same semantic type regardless of how its Source arrived:

```text
local Node ──compile──────────┐
                              ├──> CompiledPackage ──> composition
accepted external artifact ──┘
```

This is why Remove/Override and conflict handling do not have a special remote implementation.

## Digests

The compiler keeps two identities:

- `normalized_digest` — canonical compiled semantic state;
- `package_digest` — exact human/agent package bytes (`CONTEXT.md` plus `CONTEXT/`).

Machine manifests are excluded from `package_digest` so a digest never hashes itself.

For Source dependencies, semantic normalization depends on the accepted Source's `normalized_digest`; exact package bytes remain independently pinned by `package_digest`. A presentation-only Source change can therefore be represented without pretending semantic meaning changed.

## Accepted versus candidate packages

Accepted external packages live under the consumer Node:

```text
.context/sources/<package-digest>/
```

This is reproducible accepted project state and should be retained with a project that must build offline.

Candidate packages live separately:

```text
.context/candidates/<package-digest>/
```

A candidate does not affect `build`. The supported update path is:

```text
fetch → deterministic package diff → consumer structural validation
      → review receipt → explicit accept → new pin → normal build
```

The review receipt records the accepted state, candidate identity, consumer Node ID, exact SHA-256 of `CONTEXT.src.md`, structural-validation result, and deterministic diff. Acceptance rejects stale receipts when the consumer source or accepted Source changed after review.

## Git transport

Git transport is intentionally generic rather than GitHub-specific. A Source may declare:

```text
transport="git"
ref="main"
node-path="nodes/library/python-development"
```

`ref` is candidate discovery state, not accepted identity. `node-path` is location inside that retrieved snapshot, not Node identity.

The transport clones the requested ref to a temporary checkout, enters the validated `node-path`, loads and verifies the already published immutable package there, copies only that package into the consumer's candidate store, and removes the checkout.

Transport never edits the consumer or accepted store.

## Rule changes and transitive composition

`Remove` deletes an inherited ordinary Rule while carrying a transitive removal record. `Override` preserves the original `<origin-node-id>#<rule-id>` identity and replaces only the effective statement while recording modification provenance.

A dangling Change fails. A diamond where one path keeps a Rule and another removes it fails. Different effective definitions/provenance for the same stable Rule also fail rather than invoking Source precedence.

These rules are identical whether the contributing Source was locally compiled or loaded from an immutable package.

## Deterministic diff

`contextcanon diff` compares two compiled snapshots of the same stable consumer Node. `package_diff.py` uses the same `ContextDiff`/`DiffEntry` model for two immutable versions of one Source Node.

Entries cover Node metadata, direct Source dependencies, local Changes, effective active/removed Rules, Topics, and materialized Resources. An active-to-removed Rule remains one state transition for the same stable identity.

Human and JSON output are projections of the same deterministic model. The JSON schema remains `contextcanon/diff/v0`.

## Materialization closure

A Resource target is a seed, not necessarily the entire package. Local Markdown links are followed recursively so materialized resources remain self-contained. External URLs stay external.

When a Node has materialized resources, the compiler also creates `CONTEXT/README.md` as generated package orientation. That file explains the generated boundary and why `CONTEXT/references/` contains package copies rather than another authoring surface.

The immutable package manifest records exact hashes and sizes of the resulting published files and rejects missing, extra, or modified package content when loaded.

## Test strategy

The deterministic suite uses standard-library `unittest` and temporary repositories. Compiler/package tests require no network or external service.

Git transport tests use a real **local** temporary Git repository, including a Context Node nested inside a multi-Node-style path. They prove that:

- v1 can remain the accepted Source while Git exposes v2;
- `source fetch` stores v2 only as a candidate;
- a normal build still uses v1 before acceptance;
- review produces a deterministic diff and receipt;
- acceptance updates the exact pin and accepted package;
- the following offline build uses v2;
- missing node paths and unknown refs fail;
- transport metadata is complete and path-safe.

Package tests also cover source-repository deletion, semantic manifest tampering, human-package tampering, missing resources, invalid paths, and preservation of presentation order.

Repository dogfood is the second test level: CI runs `contextcanon check --all .` and fails when committed generated packages differ from current deterministic compiler output.

For the repository's complete GitHub Actions flow and failure-reading guide, see [Tests and GitHub Actions CI](tests-and-ci.md).

## Current boundary after Compiler 0.4

Compiler 0.4 deliberately still leaves several layers for later:

- Topic composition/materialization across Source package boundaries;
- protected Rules and authorized exceptions;
- richer resource collision policy across composed packages;
- semantic natural-language conflict detection;
- LLM impact analysis above exact Source diffs;
- reviewed re-onboarding/update of a project that already has canonical ContextCanon context.

The reviewed **first-adoption onboarding** path now sits above this deterministic compiler boundary: ContextCanon freezes exact evidence, generates the semantic assignment, validates the external reasoning model's proposal, binds a human review to exact evidence/proposal state, and publishes the first canonical Node only after explicit acceptance and deterministic staging/build checks.

The next major validation is therefore not another missing onboarding trust mechanism. It is the larger real 1:1 onboarding test on a materially larger existing repository, which must test both the onboarding experience and the usefulness of the resulting ContextCanon structure in ordinary work.
