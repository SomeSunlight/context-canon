# Official Context

The **Official Context** is the complete compiled package for a node.

It answers one fundamental question:

> What context does this node officially publish and operate under?

The same package meaning applies to the node itself and is what child nodes may compose. This prevents a parent from operating under one truth while publishing another.

## Package versus entry view

The Official Context is deliberately **not** defined as "all text concatenated into one Markdown file."

A package may contain:

- always-required rules,
- Topic definitions,
- required and optional deeper material,
- materialized references,
- skills,
- future context element types such as glossaries, examples, patterns, and experience,
- normalized machine data and provenance.

`CONTEXT.md` is the compact generated **official entry view** into that package.

This distinction is essential for token economy: the entry should orient a model quickly and tell it exactly what to load next without occupying the context window with unrelated detail.

## What `CONTEXT.md` should contain

The entry view should prioritize:

1. rules that are broadly required,
2. concise orientation,
3. a Topic index with clear conditions,
4. explicit **Required** versus **Optional** deeper reads,
5. stable visible IDs for published elements that descendants may reference.

It should not force readers to inspect provenance, digests, dependency internals, or every available project document.

## Published IDs are visible

Rules and other addressable elements that children may change must display a stable ID.

Recommended presentation:

```markdown
#### `SEC-017` — External network access

Agents must not access external networks from this environment.
```

Titles and wording are presentation. The stable ID is contract identity.

## Machine completeness

`.context/context.yaml` and package resources may contain the complete normalized machine view even when `CONTEXT.md` intentionally stays small.

This is not a second truth: both are generated views of the same Official Context Package.

## Generated header

`CONTEXT.md` should clearly state that it is generated, point to `CONTEXT.src.md` for editing, identify the node/version, and link to ContextCanon documentation.
