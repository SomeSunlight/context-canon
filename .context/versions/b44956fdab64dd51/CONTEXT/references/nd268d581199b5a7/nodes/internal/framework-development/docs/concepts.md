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

A node may be large or extremely small. ContextCanon Gateway has no Parent/Reference imports and no Rules; one Topic is enough to make it useful.

## Parent and Reference

A reusable Context relationship has one of two semantic kinds.

A **Parent** is normative semantic ancestry. The accepted Parent package contributes effective Rules, Topics, Resources and Change provenance to this Node; the resulting normative Context may continue through semantic Parent/Child relationships. A Node may have several Parents, and Parent order is never precedence.

A **Reference** is direct informational Context. Its Rules do not apply, its Overrides/Removes do not alter the current Node, and the Reference relationship is not inherited by Children. Its informational Topics/Resources may still be exposed to humans and LLMs in the current Node.

Both relationship kinds may use the same immutable package/provenance carrier. The historical implementation and CLI term **Source** remains for that package/discovery machinery in Phase 1; it is not a third semantic relationship type. Legacy imports without an explicit relationship are interpreted as Parent so existing governance cannot silently disappear.

## Local Context

The **Local Context** is the node's own delta: local Rules, explicit changes to imported elements, and Topics. It is authored in `CONTEXT.src.md`.

This gives a reader an intentionally small answer to:

> What is special about this node compared with the context it composes?

## Official Context Package

The **Official Context Package** is the one canonical compiled artifact for the Node. Its local view contains effective normative Parent/local Context plus clearly separated direct informational References.

Only the **normative export** is published through Parent/Child composition. Reference Rules and Reference relationships never enter that export.

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

Gateway → Framework Development is Topic navigation. Foundation → Framework Development and Development Workflow → Framework Development are normative Parent composition.

The directories `nodes/library/` and `nodes/internal/` are organizational categories used by this repository, not framework-mandated paths.

## Schema versus Node

The ContextCanon schema/specification defines what a valid Node, Parent/Reference relationship, Rule, Topic, Change, identifier, and package look like. In object-oriented terms, this is the structural interface.

A Context Node contains actual context content. A separate "interface node" is unnecessary unless there is reusable context content that deserves its own lifecycle.

## Context is broader than Rules

Rules are the first structured element because they are easy to reason about and immediately useful. The model is intentionally extensible toward glossaries, examples, patterns, practices, hints, skills, structured data, media, and experience.

Future element types should reuse the same principles where appropriate: stable identity, explicit relationship semantics, local delta, provenance, versioned publication, materialization, and progressive disclosure.
