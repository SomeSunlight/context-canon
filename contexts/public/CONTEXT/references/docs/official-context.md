# Official Context

The **Official Context** is the complete compiled context published by a node and used by that node itself.

It answers one question:

> What context officially applies here?

A child node may compose exactly that same published result. There is no separate hidden context for the parent and a different context exported to descendants.

## Concrete package layout

The human- and agent-facing package has a simple physical shape:

```text
CONTEXT.md              compact official entry
CONTEXT/                deeper compiled/package-local material
├── references/
├── topics/             optional generated topic material
├── glossaries/         future
├── examples/           future
├── skills/             future
└── ...
```

Together, `CONTEXT.md` and `CONTEXT/` are the **Official Context Package**.

`.context/` is different. It contains compiler bookkeeping, accepted source snapshots, provenance, hashes, package metadata, and other machine state. Humans normally do not need it to understand what applies.

## Why not put everything in `CONTEXT.md`?

Because completeness and prompt size are different concerns.

`CONTEXT.md` should contain the small amount of context that is broadly useful plus a precise Topic map. When a Topic applies, Required material is loaded from the package. Optional material remains available if more depth is useful.

This lets a package be complete without forcing every document, glossary, example, and historical note into every LLM turn.

## Natural source locations, self-contained published package

Authors should not reorganize a repository merely to satisfy ContextCanon. Existing material may remain in natural locations such as:

```text
SECURITY.md
docs/architecture.md
schemas/domain.csv
examples/client.py
```

`CONTEXT.src.md` may reference those source files directly.

During compilation, ContextCanon materializes the resources that belong to the published context under `CONTEXT/` and rewrites generated `CONTEXT.md` links to the package-local copies.

For example:

```text
source:     docs/architecture.md
published:  CONTEXT/references/docs/architecture.md
```

A published node can therefore be consumed without depending on the original repository layout or live access to its sources.

## What belongs in `CONTEXT.md`?

The entry should prioritize:

1. rules that are broadly required,
2. concise orientation,
3. Topics with clear conditions,
4. explicit Required and Optional reads,
5. stable visible IDs for published elements that descendants may reference.

It should not expose normal readers to package digests, provenance event lists, dependency internals, or every resource in the package.

## Published IDs are visible

Rules and other addressable elements that descendants may change must display a stable ID.

```markdown
#### `SEC-017` — External network access

Agents must not access external networks from this environment.
```

The title and wording are presentation. The stable ID is contract identity.

## Generated output

`CONTEXT.md` and `CONTEXT/` are generated and should not be edited directly. Human changes belong in `CONTEXT.src.md` and in the referenced source material.

The generated header should identify the node and version, point to `CONTEXT.src.md`, and make the package boundary clear.
