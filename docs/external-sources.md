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

The manifest carries, among other things:

- stable Node ID, name, and version;
- accepted transitive Source identities;
- effective Rules including statement, rationale, group, stable origin, and Override provenance;
- removal provenance;
- local Changes and Topics;
- exact package-file hashes;
- `normalized_digest` for canonical compiled semantics;
- `package_digest` for the exact human/agent package bytes.

The loader verifies both semantic identity and every declared package file before composition.

## Why two digests?

They answer different questions.

`normalized_digest` answers:

> Is this the same canonical compiled meaning?

Collections whose order has no semantic meaning are canonicalized before this digest is calculated.

`package_digest` answers:

> Are these exactly the same published `CONTEXT.md` and `CONTEXT/` bytes?

A presentation-only change can therefore change `package_digest` without changing `normalized_digest`.

Accepted external Sources pin both. ContextCanon does not collapse these two identities into one ambiguous hash.

## Consumer-local accepted package store

An accepted external package is stored under the consumer Node:

```text
<consumer-node>/.context/sources/<package-digest>/
├── .context/package.json
├── CONTEXT.md
└── CONTEXT/              optional
```

This store belongs to the consumer's machine state. It records the exact artifact that the consumer has accepted rather than acting as a live view of an external repository.

A package is content-addressed by `package_digest`; its manifest is then independently checked against the Source's expected Node ID, version, `normalized_digest`, and `package_digest`.

## Pinned authoring syntax

A local development Source may remain unpinned:

```markdown
- [Python Development](../python-development/) — `1.2.0`
  <!-- ctx:source id="<python-node-id>" version="1.2.0" -->
```

An accepted immutable Source adds both exact digests:

```markdown
- [Python Development](https://example.org/context-nodes/python-development) — `1.2.0`
  <!-- ctx:source id="<python-node-id>" version="1.2.0" normalized-digest="<sha256>" package-digest="<sha256>" -->
```

The pair is all-or-nothing. Supplying only one digest is invalid.

For a pinned Source, the visible link is provenance and an update/discovery location. **Normal build does not dereference it.** Build resolves only the accepted local artifact whose `package-digest` is pinned in source.

This means an offline build remains deterministic and a broken or unreachable external locator does not invalidate already accepted context.

## One semantic composition path

Local and external Sources converge before Rule composition:

```text
local Source Node ──compile──> CompiledPackage ─┐
                                                ├──> Rule composition
accepted external artifact ──load/verify───────> CompiledPackage ─┘
```

Remove/Override behavior, diamond-conflict detection, provenance, and downstream normalized semantics therefore do not have separate "remote Source" implementations.

This boundary is deliberate. Transport bugs must not create a second composition language.

## Presentation order versus canonical semantics

The immutable artifact preserves effective Rule and Topic presentation order so a descendant built from a local Source and a descendant built from the same accepted offline package can render equivalent official context.

Canonical semantic hashing remains independently order-insensitive where order has no defined meaning. The manifest must not use hash-normalization sorting as a replacement for package presentation order.

## Failure behavior

Normal build fails rather than fetching or guessing when:

- the pinned package is absent from `.context/sources/<package-digest>/`;
- the package manifest is malformed;
- semantic content does not match `normalized_digest`;
- published files do not match their exact hashes/package digest;
- Node ID or version differs from the Source reference;
- the Source pin is incomplete.

A missing accepted package is not permission to contact the Source locator automatically.

## Candidate updates and explicit acceptance

Candidate discovery is a separate workflow from build.

The intended update path is:

```text
accepted package
      +
new candidate package
      ↓
deterministic Context diff
      ↓
structural diagnostics
      ↓
optional semantic impact review
      ↓
explicit acceptance
      ↓
new local accepted package + new exact pin
```

A newer package is therefore a change request, not live inheritance.

The transport used to obtain a candidate may initially be Git/repository based, but transport remains outside the semantic compiler boundary. Multi-Node repository addressing also belongs to locator/transport metadata rather than Node identity.

## Current implementation boundary

Compiler 0.4 currently implements the immutable manifest, full verification, consumer-local package store lookup, exact Source pins, and offline composition. Candidate discovery, explicit acceptance tooling, multi-Node external locator syntax, and practical Git transport are the remaining parts of this compiler block.
