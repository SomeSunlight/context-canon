# Architecture

ContextCanon separates a small human-facing authoring surface, a compact entry context, optional deeper package resources, and deterministic machine bookkeeping.

## Compilation pipeline

```text
CONTEXT.src.md
       +
accepted Source packages
       +
referenced source material
       |
       v
    compiler
       |
       +--> CONTEXT.md        compact official entry
       +--> CONTEXT/          deeper material, only when needed
       +--> .context/         machine state and package metadata
       +--> harness adapters  AGENTS.md, .goosehints, ...
```

`CONTEXT.md` is always present. `CONTEXT/` is generated only when a Node has resources to materialize. `.context/` is compiler-owned state about the Node and its package.

## A Node has one physical root

Every Context Node is organized around one **node-root directory**. That directory contains the Node's editable source, generated official entry, optional package resources, and machine state.

The node-root is a physical location, not identity. Moving or renaming the directory does not create a new Node as long as the stable Node ID remains the same.

A repository root may itself be a node root. Nested Nodes are also possible. Filesystem nesting alone does not create Source composition.

Category directories may organize several Nodes without becoming Nodes themselves. In this repository, `nodes/library/` and `nodes/internal/` are such categories.

The exact deterministic rules for discovering node roots and respecting nested-node boundaries remain a V1 item to freeze before compiler implementation.

## Token economy is architectural

ContextCanon must not solve discoverability by eagerly loading everything.

The entry context contains only broadly required information and a precise Topic map. Topic material is loaded when relevant, with explicit Required versus Optional targets. A deeper document may repeat the same pattern: summary first, links onward.

Progressive disclosure is therefore part of the architecture, not merely a writing preference.

## Gateway nodes: almost nothing can be enough

A valid Context Node may have zero Sources, zero Rules and zero materialized resources.

The root of this repository is **ContextCanon Gateway**. It contains one Topic: when the task concerns ContextCanon framework development, load the ContextCanon Framework Development Node. Because the Gateway has no deeper resources of its own, it has no `CONTEXT/` directory.

This is not a special node type. It is an ordinary Node at the smallest useful end of the model.

The same pattern can later route work in large repositories:

```text
Repository Gateway
   ├── backend task  ──> Backend Context
   ├── frontend task ──> Frontend Context
   └── release task  ──> Release Context
```

## Navigation is different from composition

A Topic target tells an agent **where to read next for this task**. A Source tells the compiler **which published context becomes part of this Node**.

ContextCanon itself demonstrates both:

```text
ContextCanon Gateway ──Topic──> ContextCanon Framework Development
                                      ▲
                                      │ Source
                           ContextCanon Foundation
```

The Gateway does not inherit Framework Development. Framework Development does inherit Foundation and adds a local delta.

## Natural source files, generated package files

Project documentation should stay where it makes sense to authors. The compiler materializes context resources into a Node's `CONTEXT/` directory when building a self-contained published package.

```text
docs/architecture.md
        ↓ materialize
nodes/internal/framework-development/CONTEXT/references/docs/architecture.md
```

Consumers of that Node can use the package without reconstructing the author's source layout.

## `.context/`

`.context/` is analogous to `.git/` in one important respect: it contains infrastructure that matters but should not dominate normal work.

The current POC uses one primary `.context/context.yaml` per Node. It records Node identity, accepted Source packages, normalized element identities, provenance, Topic targets, resource mapping, and future hashes/digests.

Generated YAML may contain explanatory comments because occasional human inspection is useful, but it remains machine-owned.

## ContextCanon's repository layout

This repository dogfoods three Nodes while keeping their roles visibly separated:

```text
repository root
└── ContextCanon Gateway

nodes/
├── library/                         organizational category, not a Node
│   └── foundation/                  ContextCanon Foundation
└── internal/                        organizational category, not a Node
    └── framework-development/       ContextCanon Framework Development
                                     -> composes Foundation + local delta
```

`library/` contains reusable Nodes distributed as part of ContextCanon. Every Node in that library must compose Foundation directly or transitively. `internal/` contains ContextCanon-specific Nodes that are not intended as reusable library modules.

These category names are repository conventions, not required directory names for other ContextCanon projects.

## The schema is the interface

ContextCanon does not need a separate "interface node" merely to describe structure.

The structural contract — what a Node, Source, Rule, Topic, Change, package, and identifier must contain — belongs to the ContextCanon schema/specification. That schema is the interface implemented by every Node.

A Context Node contains actual context content. Another reusable base Node is justified only when there is reusable **content** with its own lifecycle.

## Deterministic skeleton, semantic assistance at the edges

The compiler should deterministically handle what machines can prove:

- syntax and schema validation,
- node-root discovery and boundary checks,
- stable IDs,
- dependency resolution,
- cycle and version errors,
- explicit remove/override/exception operations,
- dangling operation detection,
- provenance,
- package materialization,
- exact diffs and hashes,
- generated views and adapters.

LLMs may assist with work that genuinely requires interpretation:

- bootstrapping context from an existing repository,
- detecting likely natural-language conflicts,
- explaining the impact of Source updates,
- suggesting where a conflict is best resolved,
- applying accepted context changes to project code.

LLM judgments never replace deterministic package identity or explicit durable resolutions.

## Versioned accepted composition

A Source update does not immediately change consumers. Each consumer accepts an exact published Source package and rebuilds deliberately.

This keeps independent projects on independent lifecycles while still allowing shared context to improve over time.
