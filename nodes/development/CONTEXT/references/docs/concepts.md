# Concepts

ContextCanon manages reusable project context as versioned, composable knowledge rather than as one large harness-specific prompt file.

## Context Node

A **Context Node** is an independently addressable and versioned unit that publishes an Official Context Package.

Node identity is logical rather than tied to a Git repository or physical directory. One repository may contain several nodes, and a node may move without changing identity.

A node may be large or extremely small. ContextCanon Gateway in this repository has no Sources and no Rules; one Topic is enough to make it useful.

## Context Source

A **Context Source** is the published Official Context Package of another node accepted at a specific immutable version/revision/package identity.

A node may compose zero, one, or several sources. Sources may represent orthogonal concerns such as:

- company or private governance,
- Python or Java development practice,
- security requirements,
- personal coding style,
- a shared framework foundation.

Source order is not precedence.

## Local Context

The **Local Context** is the node's own delta: local rules, explicit changes to imported elements, and Topics.

It is authored in `CONTEXT.src.md`.

This gives a reader an intentionally small answer to:

> What is special about this node compared with the context it composes?

## Official Context Package

The **Official Context Package** is the compiled result of accepted source packages plus the Local Context.

It is the one canonical result that:

1. applies to the current node,
2. is published for child nodes to compose,
3. is exposed to humans and agents through `CONTEXT.md` and, when needed, `CONTEXT/`.

`CONTEXT.md` is always the compact generated entry. `CONTEXT/` exists only when the node has deeper resources to materialize.

`.context/` is related machine state about the package, not the human/agent context surface itself.

## Topics

A **Topic** describes when deeper context becomes relevant.

Topic material distinguishes:

- **Required** targets that must be loaded when the Topic applies,
- **Optional** targets that remain discoverable for deeper exploration.

A target may be a package resource or another Context Node entry. The latter is useful for Gateway nodes that route a task into a more specific context without inheriting that context themselves.

This pattern may repeat recursively: summary first, then deeper links.

## Gateway, Foundation and Development

This repository uses three ordinary nodes to demonstrate three different jobs:

- **ContextCanon Gateway** — the minimal root entry; routes development tasks onward.
- **ContextCanon Foundation** — reusable baseline context with no parent Sources.
- **ContextCanon Development** — composes Foundation and adds only the framework-development delta.

Gateway → Development is Topic navigation. Foundation → Development is Source composition.

## Schema versus Node

The ContextCanon schema/specification defines what a valid Node, Source, Rule, Topic, Change, identifier, and package look like. In object-oriented terms, this is the structural interface.

A Context Node contains actual context content. A separate "interface node" is unnecessary unless there is reusable context content that deserves its own lifecycle.

## Context is broader than rules

Rules are the first structured element because they are easy to reason about and immediately useful. The model is intentionally extensible toward glossaries, examples, patterns, practices, hints, skills, structured data, media, and experience.

Future element types should reuse the same principles where appropriate: stable identity, source composition, local delta, provenance, versioned publication, materialization, and progressive disclosure.