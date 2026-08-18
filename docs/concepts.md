# Concepts

ContextCanon manages reusable project context as versioned, composable knowledge rather than as one large harness-specific prompt file.

## Context Node

A **Context Node** is an independently versioned unit that publishes an official context. A project repository is a natural node, but node identity is logical rather than tied to a physical path.

Every node has a stable opaque identity that survives renames or moves.

## Context Source

A **Context Source** is the published official context of another node accepted at a specific version/revision.

A node may compose zero, one, or several sources. Sources may represent orthogonal concerns such as:

- company or private governance,
- Python or Java development practice,
- security requirements,
- personal coding style,
- a shared framework or parent project.

## Local Context

The **Local Context** is the node's own delta: local rules, explicit changes to imported elements, and Topics.

It is authored in `CONTEXT.src.md`.

## Official Context

The **Official Context** is the compiled result of accepted sources plus the local context.

It is the one canonical context that:

1. applies to the current node,
2. is read by humans and agents,
3. is published for child nodes to consume.

There is intentionally no separate "context for this parent" and "context exported to children."

## Context is broader than rules

Rules are the first structured element because they are easy to reason about and immediately useful. The model is intentionally extensible toward glossaries, examples, patterns, practices, hints, skills, and experience.

These future element types should reuse the same principles: stable identity, source composition, local delta, provenance, versioned publication, and progressive disclosure where appropriate.
