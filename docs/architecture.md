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

The implementation mirrors that conceptual pipeline with narrow stages:

```text
parser.py → model.py → compiler.py → render.py → outputs.py
                                           ↑
                                        cli.py
```

Parsing owns authoring grammar, compilation owns semantic truth, rendering projects compiled meaning, and the output layer alone mutates generated files. See [compiler.md](compiler.md) for the module contracts and regression strategy.

## A Node has one physical root

Every Context Node is organized around one **node-root directory**. That directory contains the Node's editable source, generated official entry, optional package resources, and machine state.

The node-root is a physical location, not identity. Moving or renaming the directory does not create a new Node as long as the stable Node ID remains the same.

A repository root may itself be a node root. Nested Nodes are also possible. Filesystem nesting alone does not create Source composition.

Category directories may organize several Nodes without becoming Nodes themselves. In this repository, `nodes/library/` and `nodes/internal/` are such categories.

The compiler discovers node roots from `CONTEXT.src.md`. More complex nested-repository boundary behavior will be hardened as part of broader package-boundary work.

## Token economy is architectural

ContextCanon must not solve discoverability by eagerly loading everything.

The entry context contains only broadly required information and a precise Topic map. Topic material is loaded when relevant, with explicit Required versus Optional targets. A deeper document may repeat the same pattern: summary first, links onward.

Progressive disclosure is therefore part of the architecture, not merely a writing preference.

This also helps smaller and local models. A local agent may have abundant tokens but limited model capability; the architecture should spend those tokens on the relevant problem rather than on repeatedly reconstructing repository assumptions.

## Standardized orientation is architectural

Across projects, ContextCanon gives humans and agents the same conceptual entry points even when the domain changes:

- `CONTEXT.md` — what applies here and where to go deeper,
- `CONTEXT.src.md` — what this Node adds or changes,
- Sources — which reusable foundations are accepted,
- Topics — which deeper knowledge applies to which tasks,
- `STATE.md` — where the project is now,
- `PLAN.md` — where it is going.

The content remains project-specific. The orientation workflow becomes reusable.

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

## Transitive composition preserves identity and state

Source composition is transitive package meaning, not a direct-parent text copy.

If `Foundation → Team Standard → Project`, a Foundation Rule remains identified by the Foundation Node ID plus Rule ID in Project. A Team Standard Override changes the effective statement and adds provenance without changing that identity. A Team Standard Remove makes the Rule absent from active downstream context while preserving a machine-level removal record.

That removal record matters in a DAG: if another Source path still carries the same Rule, the compiler can detect the contradiction instead of inventing Source precedence. Likewise, two different effective Overrides of the same stable Rule are a structural conflict, while equivalent compiled Rule state may be deduplicated.

This identity- and state-preserving model is what makes later exact diffs, dangling-operation checks, Source-update impact analysis, and standalone Source packages possible.

## Natural source files, generated package files

Project documentation should stay where it makes sense to authors. The compiler materializes context resources into a Node's `CONTEXT/` directory when building a self-contained published package.

```text
docs/architecture.md
        ↓ materialize
nodes/internal/framework-development/CONTEXT/references/docs/architecture.md
```

Consumers of that Node can use the package without reconstructing the author's source layout.

A directly referenced Markdown document can itself point to other local files. The compiler therefore computes a **materialization closure**: Topic Resource targets are seeds, and local relative links are followed recursively into the package. External links remain external.

## `.context/`

`.context/` is analogous to `.git/` in one important respect: it contains infrastructure that matters but should not dominate normal work.

The compiler generates one primary `.context/context.yaml` per Node. It records Node identity, accepted local Sources, local Changes, normalized element identities, override provenance, removal provenance, Topic targets, resource mapping, and exact digests.

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

Compiler 0.2 deterministically handles the current source grammar, node-root discovery, stable IDs, local Source resolution, cycle/version errors, transitive Rule composition, Remove/Override operations, override/removal provenance, deterministic same-Rule DAG conflicts, dangling Change diagnostics, Topic targets, resource materialization, exact hashes, generated views, adapters, and drift checks.

Planned deterministic capabilities include exact compiled Context diff, immutable external Source packages and update acceptance, protected Rules and authorized exceptions, and broader package-boundary diagnostics.

LLMs may assist with work that genuinely requires interpretation:

- bootstrapping context from an existing repository,
- detecting likely natural-language conflicts,
- explaining the impact of Source updates,
- suggesting where a conflict is best resolved,
- mapping exact Context changes to likely affected project files,
- applying accepted context changes to project code.

LLM judgments never replace deterministic package identity or explicit durable resolutions.

## Versioned accepted composition

A Source update does not immediately change consumers. Each consumer will ultimately accept an exact published Source package and rebuild deliberately.

Compiler 0.2 validates local Source identity and version and records the compiled Source package digest. Exact Context diff and immutable external package pinning are the next core layers needed to turn that recorded identity into a complete multi-repository update workflow.
