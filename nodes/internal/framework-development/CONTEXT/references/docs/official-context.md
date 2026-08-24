# Official Context

The **Official Context** is the complete compiled context published by a node and used by that node itself.

It answers one question:

> What context officially applies here?

A child node may compose exactly that same published semantic result. There is no separate hidden governance for the parent and a different governance exported to descendants.

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

## Overview: what is this place?

A Node may begin its compact entry with a short local `Overview`. It answers the orientation questions that are neither Rules nor conditional deep context: what this Node represents, why it exists, and what background helps a human or agent understand the surrounding problem.

An Overview is deliberately **not inherited governance**. Child Nodes do not receive a Source's introductory prose merely because they compose its Rules. The Overview remains part of the exact published `CONTEXT.md`, so changing it changes the package bytes and `package_digest`, but not the Node's normalized semantic digest.

This distinction lets a Node explain itself without pretending every explanatory sentence is a Rule. The Overview should remain short; deeper explanation belongs behind Topics.

## Small gateways matter

A valid Context Node can be very small. ContextCanon Gateway at this repository root has no Sources and no Rules, but it is no longer empty orientation: its Overview briefly explains why ContextCanon exists, while two Topics route relevant work deeper.

- onboarding an existing project loads the user-facing onboarding guide as a Required Resource;
- ContextCanon framework-development work navigates to the deeper Framework Development Node.

The Gateway therefore has a small `CONTEXT/` directory for the onboarding guide, but that guide is not loaded for unrelated work.

This is not a special bootstrap mode. It is an ordinary Context Node demonstrating two complementary ideas at once: enough always-read orientation to understand where you are, and progressive disclosure for everything that does not belong in every task.

## Natural source locations, self-contained published package

Authors should not reorganize a repository merely to satisfy ContextCanon. Existing material may remain in natural locations such as `SECURITY.md`, `docs/architecture.md`, `schemas/domain.csv`, or `examples/client.py`.

During compilation, ContextCanon materializes resources that belong inside a published package under `CONTEXT/` and rewrites generated links to those package-local copies.

## What belongs in `CONTEXT.md`?

The entry should prioritize a concise Overview when orientation is useful, broadly required Rules, Topics with clear conditions, explicit Required and Optional targets, and stable visible IDs for published elements that descendants may reference.

It should not expose normal readers to package digests, provenance event lists, dependency internals, or every resource in the package. Nor should an Overview become a hidden preload document: if material matters only for a recognizable task, it belongs behind a Topic.

## Generated output

`CONTEXT.md` and, when present, `CONTEXT/` are generated and should not be edited directly. Human changes belong in `CONTEXT.src.md` and in referenced source material.
