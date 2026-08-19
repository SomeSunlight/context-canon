# Official Context

The **Official Context** is the complete compiled context published by a node and used by that node itself.

It answers one question:

> What context officially applies here?

A child node may compose exactly that same published result. There is no separate hidden context for the parent and a different context exported to descendants.

## Concrete package layout

Every node has a generated `CONTEXT.md` entry. Deeper package material exists only when the node actually needs it:

```text
CONTEXT.md              compact official entry; always present
CONTEXT/                optional deeper compiled/package-local material
├── references/
├── topics/
├── glossaries/         future
├── examples/           future
├── skills/             future
└── ...
```

A tiny node with no materialized resources may legitimately have no `CONTEXT/` directory at all.

`.context/` is different. It contains compiler bookkeeping, accepted Source snapshots, provenance, hashes, package metadata, and other machine state. Humans normally do not need it to understand what applies.

## Why not put everything in `CONTEXT.md`?

Because completeness and prompt size are different concerns.

`CONTEXT.md` should contain the small amount of context that is broadly useful plus a precise Topic map. When a Topic applies, Required material is loaded from the package or another explicitly named target. Optional material remains available if more depth is useful.

This lets a package be complete without forcing every document, glossary, example, and historical note into every LLM turn.

## The minimal case matters

ContextCanon Gateway deliberately has no Sources, no Rules and no materialized `CONTEXT/` resources. Its `CONTEXT.md` only tells an agent when to enter the deeper Development node.

This is not a special bootstrap mode. It is an ordinary Context Node and demonstrates that ContextCanon must remain useful even when the useful context is almost nothing.

## Natural source locations, self-contained published package

Authors should not reorganize a repository merely to satisfy ContextCanon. Existing material may remain in natural locations such as `SECURITY.md`, `docs/architecture.md`, `schemas/domain.csv`, or `examples/client.py`.

During compilation, ContextCanon materializes resources that belong inside a published package under `CONTEXT/` and rewrites generated links to those package-local copies.

## What belongs in `CONTEXT.md`?

The entry should prioritize broadly required Rules, concise orientation, Topics with clear conditions, explicit Required and Optional targets, and stable visible IDs for published elements that descendants may reference.

It should not expose normal readers to package digests, provenance event lists, dependency internals, or every resource in the package.

## Generated output

`CONTEXT.md` and, when present, `CONTEXT/` are generated and should not be edited directly. Human changes belong in `CONTEXT.src.md` and in referenced source material.
