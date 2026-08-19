# Concepts

ContextCanon manages reusable project context as versioned, composable knowledge rather than as one large harness-specific prompt file.

## Context Node

A **Context Node** is an independently addressable and versioned unit that publishes an Official Context Package.

Node identity is logical rather than tied to a Git repository or physical directory. One repository may contain several nodes, and a node may move without changing identity.

Every published node has a stable opaque identity that survives ordinary renames or moves.

## Context Source

A **Context Source** is the published Official Context Package of another node accepted at a specific immutable version/revision/package identity.

A node may compose zero, one, or several sources. Sources may represent orthogonal concerns such as:

- company or private governance,
- Python or Java development practice,
- security requirements,
- personal coding style,
- a shared framework or parent project.

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
3. is exposed to humans and agents through `CONTEXT.md` plus `CONTEXT/`.

There is intentionally no separate "context used by this parent" and "context exported to children."

`.context/` is related machine state about the package, not the human/agent context surface itself.

## `CONTEXT.md` and `CONTEXT/`

`CONTEXT.md` is the compact generated official **entry view**. `CONTEXT/` holds deeper package-local resources.

The entry should contain broadly required context and a precise Topic map, not every piece of material available in the package.

This distinction allows the package to remain complete while protecting the LLM context window from unrelated information.

## Topics

A **Topic** describes when deeper context becomes relevant.

Topic material distinguishes:

- **Required** material that must be loaded when the Topic applies,
- **Optional** material that remains discoverable for deeper exploration.

This pattern may repeat recursively: summary first, then deeper links.

Topics are also the first general context-integration mechanism: they can later connect tasks not only to Markdown, but also to glossaries, example code, structured data, PDFs, images, skills, and experience.

## Schema versus Node

The ContextCanon schema/specification defines what a valid Node, Source, Rule, Topic, Change, identifier, and package look like. In object-oriented terms, this is the structural interface.

A Context Node contains actual context content. A separate "interface node" is therefore unnecessary unless there is reusable context content that deserves its own lifecycle.

## Context is broader than rules

Rules are the first structured element because they are easy to reason about and immediately useful. The model is intentionally extensible toward glossaries, examples, patterns, practices, hints, skills, structured data, media, and experience.

Future element types should reuse the same principles where appropriate: stable identity, source composition, local delta, provenance, versioned publication, materialization, and progressive disclosure.
