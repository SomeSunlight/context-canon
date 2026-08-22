# Immutable external Sources

ContextCanon separates **semantic composition** from **Source transport**.

A consumer should be able to keep using an already accepted Source even when the Source repository is unavailable, has moved, or contains a newer version that has not been reviewed yet.

The core rule is therefore:

> Normal `contextcanon build` composes accepted state. It does not discover, download, or upgrade external Sources.

## The immutable compiled artifact

A reusable compiled Source is represented by an artifact containing:

```text
.context/package.json
CONTEXT.md
CONTEXT/              optional
```

`CONTEXT.md` and optional `CONTEXT/` are the human/agent-facing Official Context Package. `.context/package.json` is the portable machine manifest needed to reconstruct the Source's compiled semantic state without reparsing `CONTEXT.src.md`.

The manifest carries stable Node metadata, accepted transitive Source identities, complete effective Rules and provenance, removal provenance, local Changes and Topics, exact package-file hashes, `normalized_digest`, and `package_digest`.

The loader verifies both semantic identity and every declared package file before composition.

## Why two digests?

They answer different questions.

`normalized_digest` asks whether this is the same canonical compiled meaning. Collections whose order has no semantic meaning are canonicalized before that digest is calculated.

`package_digest` asks whether these are exactly the same published `CONTEXT.md` and `CONTEXT/` bytes.

A presentation-only change can therefore change `package_digest` without changing `normalized_digest`. Accepted external Sources pin both rather than collapsing the two identities into one ambiguous hash.

## Accepted package store

An accepted external package is stored under the consumer Node:

```text
<consumer-node>/.context/sources/<package-digest>/
├── .context/package.json
├── CONTEXT.md
└── CONTEXT/              optional
```

This directory is **accepted reproducible project state**, not a live cache of the Source repository. It should be retained/versioned with the consumer wherever a clone is expected to build offline without contacting external Sources.

A package is content-addressed by `package_digest`; its manifest is then independently checked against the Source's expected Node ID, version, `normalized_digest`, and `package_digest`.

Temporary update candidates live separately under:

```text
<consumer-node>/.context/candidates/<package-digest>/
```

Candidates are not inheritance. Merely fetching one cannot change a normal build.

## Pinned authoring syntax

A local development Source may remain unpinned:

```markdown
- [Python Development](../python-development/) — `1.2.0`
  <!-- ctx:source id="<python-node-id>" version="1.2.0" -->
```

An accepted immutable Source adds both exact digests:

```markdown
- [Python Development](https://example.org/context-nodes.git) — `1.2.0`
  <!-- ctx:source id="<python-node-id>" version="1.2.0" normalized-digest="<sha256>" package-digest="<sha256>" -->
```

The digest pair is all-or-nothing. For a pinned Source, the visible link is provenance/update location. **Normal build does not dereference it.**

## Git transport and multi-Node repositories

Compiler 0.4 provides a generic Git candidate transport. It is not GitHub-specific and uses the system `git` executable.

A Git-backed Source adds three transport fields:

```markdown
- [Python Development](https://example.org/context-nodes.git) — `1.2.0`
  <!-- ctx:source id="<python-node-id>" version="1.2.0" normalized-digest="<sha256>" package-digest="<sha256>" transport="git" ref="main" node-path="nodes/library/python-development" -->
```

The fields mean:

- `transport="git"` — use generic Git for candidate retrieval;
- `ref="main"` — branch/tag/ref used for candidate discovery;
- `node-path="..."` — location of this Context Node inside the retrieved repository snapshot. Use `.` for a repository-root Node.

All three transport fields are required together. `node-path` is location only; the stable Node ID remains identity. Absolute paths, backslashes, and `..` traversal are rejected.

Transport metadata is currently used for **updates of an already accepted pinned Source**. Initial selection/addition of reusable Sources will also be exercised by the reviewed project-onboarding workflow; it must not bypass review merely because a transport locator is available.

## Fetch, review, accept

Source updates are deliberately three explicit operations:

```text
contextcanon source fetch <source-node-id> --node <consumer-node>
contextcanon source review <source-node-id> <candidate-package> --node <consumer-node>
contextcanon source accept <source-node-id> <candidate-package> --node <consumer-node>
```

### Fetch

`source fetch` clones the declared Git ref into a temporary checkout, enters `node-path`, loads and fully verifies the immutable package already published there, then copies only that immutable artifact to `.context/candidates/<package-digest>/`.

It does **not** modify `CONTEXT.src.md` or `.context/sources/`.

### Review

`source review` compares the currently accepted package with the candidate using the deterministic Context diff. It also substitutes the candidate into the consumer's actual Source composition in memory and checks structural consequences, including dangling local Changes and Rule collisions.

A successful review writes a deterministic receipt under:

```text
.context/source-reviews/<candidate-package-digest>.json
```

The receipt is bound to the exact current `CONTEXT.src.md`, the currently accepted Source state, the candidate package identity, the deterministic diff, and successful structural validation.

### Accept

`source accept` requires the matching review receipt. It revalidates the candidate and structural composition, rejects the operation if `CONTEXT.src.md` or the accepted Source state changed since review, installs the candidate into `.context/sources/<package-digest>/`, and then updates the visible Source version plus exact digest pins in `CONTEXT.src.md`.

Git transport metadata is preserved when the pin is updated.

This cannot force a human to read a review, but it prevents the supported acceptance path from skipping the deterministic review step entirely.

## Atomic publication and interrupted operations

Candidate and accepted packages are never published directly into their final content-addressed directories. ContextCanon copies them into a sibling staging directory, loads and verifies the staged package, and only then atomically replaces the final directory entry.

The canonical Source pin in `CONTEXT.src.md` follows the same principle: updated text is written to a sibling temporary file, flushed and `fsync`ed, then published with an atomic replace. A failure before the final replace leaves the previous Source file intact.

This creates a deliberate recovery boundary. If acceptance installs the new immutable package successfully but the final pin swap fails, the new package may remain in `.context/sources/` as **unreferenced immutable state**, while `CONTEXT.src.md` still points to the previous accepted package. A normal build therefore continues to use the old accepted Source rather than observing a half-applied update.

Regression coverage simulates failure exactly at that final replace and verifies that the original `CONTEXT.src.md` bytes remain unchanged, no temporary file remains, and the consumer still compiles against the old pin.

## One semantic composition path

Local and external Sources converge before Rule composition:

```text
local Source Node ──compile──> CompiledPackage ─┐
                                                ├──> Rule composition
accepted external artifact ──load/verify───────> CompiledPackage ─┘
```

Remove/Override behavior, diamond-conflict detection, provenance, and downstream normalized semantics therefore do not have separate remote implementations. Transport bugs cannot silently create a second composition language.

## Presentation order versus canonical semantics

The immutable artifact preserves effective Rule and Topic presentation order so a descendant built from a local Source and a descendant built from the same accepted offline package can render equivalent official context.

Canonical semantic hashing remains independently order-insensitive where order has no defined meaning. Hash-normalization sorting is not reused as package presentation order.

## Failure behavior

Normal build fails rather than fetching or guessing when the pinned accepted package is absent, malformed, has wrong files/digests, or disagrees with the Source ID/version/pins.

Git candidate fetch fails on unsupported/incomplete transport metadata, an unavailable ref, an invalid/missing `node-path`, a missing Git executable, an invalid immutable package, or a candidate with the wrong stable Node ID.

A missing accepted package is never permission for normal `build` to contact the Source locator automatically.

## Candidate updates are change requests

The complete update model is:

```text
accepted package
      +
Git-fetched candidate package
      ↓
deterministic Context diff
      ↓
consumer structural validation
      ↓
review receipt
      ↓
optional semantic/LLM impact review
      ↓
explicit acceptance
      ↓
new accepted package + new exact pin
```

A newer package is therefore a change request, not live inheritance. The deterministic review result is also the natural exact input to later LLM impact analysis.

## Current implementation boundary

Compiler 0.4 implements immutable manifests, full package verification, offline accepted-package composition, exact Source pins, deterministic package diff, review receipts, explicit acceptance, multi-Node Git addressing, generic Git candidate retrieval, staged package publication, and atomic canonical-pin replacement.

The implementation block is complete once its regenerated repository dogfood and final exact-head CI are synchronized. The next validation block then exercises reviewed LLM-assisted onboarding of a larger pre-existing project, including the decision whether extracted rules stay local or should use/become reusable generic Nodes.
