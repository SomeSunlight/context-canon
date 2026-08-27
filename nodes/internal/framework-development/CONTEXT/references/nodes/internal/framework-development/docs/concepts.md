# Concepts

ContextCanon manages reusable project context as versioned, composable knowledge rather than as one large harness-specific prompt file.

## Context Node

A **Context Node** is an independently addressable and versioned unit that publishes an Official Context Package.

### The node-root directory

Physically, every Context Node has exactly one **node-root directory**. That directory is where its ContextCanon files live:

```text
<node-root>/
├── CONTEXT.src.md
├── CONTEXT.md
├── CONTEXT/          optional deeper generated resources
└── .context/         generated machine state
```

The repository root may itself be a node-root directory. ContextCanon Gateway in this repository is an example.

A directory that merely groups Nodes is not automatically a Context Node. For example, `nodes/library/` and `nodes/internal/` organize this repository but contain no context of their own.

Node identity is logical rather than path-based. A Node may be renamed or moved to another directory without changing its stable identity. The path tells humans and tools where the Node currently lives; it is not the Node's identity.

A node may be large or extremely small. ContextCanon Gateway has no Sources and no Rules; one Topic is enough to make it useful.

## Context Source

A **Context Source** is the published Official Context Package of another node accepted at a specific immutable version/revision/package identity.

A node may compose zero, one, or several Sources. Sources may represent orthogonal concerns such as company governance, Python or Java development practice, security requirements, personal coding style, or a shared framework foundation.

Source order is not precedence. Filesystem nesting does not imply Source composition.

## Local Context

The **Local Context** is the node's own delta: local Rules, explicit changes to imported elements, and Topics. It is authored in `CONTEXT.src.md`.

This gives a reader an intentionally small answer to:

> What is special about this node compared with the context it composes?

## Official Context Package

The **Official Context Package** is the compiled result of accepted Source packages plus the Local Context.

It is the one canonical result that applies to the current node and is published for child nodes to compose.

`CONTEXT.md` is always the compact generated entry. `CONTEXT/` exists only when the node has deeper resources to materialize. `.context/` is related machine state about the package, not the human/agent context surface itself.

## Topics

A **Topic** describes when deeper context becomes relevant.

Topic material distinguishes:

- **Required** targets that must be loaded when the Topic applies,
- **Optional** targets that remain discoverable for deeper exploration.

A target may be a package resource or another Context Node entry. The latter is useful for Gateway nodes that route a task into a more specific context without inheriting that context themselves.

This pattern may repeat recursively: summary first, then deeper links.

## ContextCanon's four self-hosted Context Nodes

This repository currently uses four ordinary ContextCanon Nodes on itself, with different jobs:

- **ContextCanon Gateway** — the minimal repository-root Node; routes onboarding and framework-development tasks onward.
- **ContextCanon Foundation** — `nodes/library/foundation/`; the reusable baseline of the ContextCanon Node Library.
- **ContextCanon Development Workflow** — `nodes/internal/development-workflow/`; internal context for recoverable LLM-assisted development and project-owner review.
- **ContextCanon Framework Development** — `nodes/internal/framework-development/`; composes Foundation plus Development Workflow and adds only the context needed to design and implement ContextCanon itself.

Gateway → Framework Development is Topic navigation. Foundation → Framework Development and Development Workflow → Framework Development are Source composition.

The directories `nodes/library/` and `nodes/internal/` are organizational categories used by this repository, not framework-mandated paths.

## Schema versus Node

The ContextCanon schema/specification defines what a valid Node, Source, Rule, Topic, Change, identifier, and package look like. In object-oriented terms, this is the structural interface.

A Context Node contains actual context content. A separate "interface node" is unnecessary unless there is reusable context content that deserves its own lifecycle.

## Context is broader than Rules

Rules are the first structured element because they are easy to reason about and immediately useful. The model is intentionally extensible toward glossaries, examples, patterns, practices, hints, skills, structured data, media, and experience.

Future element types should reuse the same principles where appropriate: stable identity, Source composition, local delta, provenance, versioned publication, materialization, and progressive disclosure.
