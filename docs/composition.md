# Context Composition

ContextCanon uses composition rather than a single inheritance tree.

```text
Business Context ──────┐
Python Context ─────────┤
Personal Style ─────────┼──> Local Delta ──> Official Context
Security Context ───────┘
```

## No implicit precedence

Source order does not mean priority. ContextCanon must never silently apply "first source wins" or "last source wins" semantics.

Different sources can therefore contribute independent rules without artificial hierarchy.

## Dependency graph

Source relationships form a directed acyclic graph.

The compiler can deterministically detect structural problems such as:

- dependency cycles,
- the same source required at incompatible accepted versions,
- invalid or missing referenced IDs,
- illegal operations on protected elements.

Identical source/version dependencies can be deduplicated.

## Semantic conflicts

Two different source elements may contradict each other even though their IDs are unrelated:

```text
Source A: Use spaces for indentation.
Source B: Use tabs for indentation.
```

A deterministic compiler cannot reliably infer that natural-language conflict. It keeps both unless an explicit local resolution exists.

An optional LLM reviewer may flag likely conflicts, explain them, and suggest where to resolve them. The durable decision remains explicit in source.

## Local changes

A node can resolve inherited context through explicit operations such as:

- **Remove** an inherited ordinary element,
- **Override** an inherited ordinary element while preserving its global identity,
- **Use Exception** when a protected element defines an authorized exception for this node.

Operations target stable published IDs, never titles or current wording.

Protected rules cannot simply be removed or overridden by descendants.

## Source updates are change requests

Children remain pinned to an accepted source version. A newly published source version is an update candidate, not live inheritance.

The intended workflow is:

1. detect a newer source version,
2. compute a complete deterministic diff,
3. optionally use an LLM to highlight likely semantic impact,
4. review and resolve changes,
5. explicitly accept the new source version,
6. rebuild the node's official context.

This preserves independent project lifecycles while still allowing context improvements to propagate deliberately.
