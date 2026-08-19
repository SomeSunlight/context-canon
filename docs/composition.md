# Context Composition

ContextCanon uses composition rather than a single inheritance tree.

```text
Business Context ──────┐
Python Context ─────────┤
Personal Style ─────────┼──> Local Delta ──> Official Context Package
Security Context ───────┘
```

A source is an accepted published package from another Context Node. Sources may live in the same Git repository, another repository, or eventually another package location; repository containment is not inheritance.

## No implicit precedence

Source order does not mean priority. ContextCanon must never silently apply "first source wins" or "last source wins" semantics.

Different sources can therefore contribute independent elements without artificial hierarchy.

## Dependency graph

Source relationships form a directed acyclic graph.

The compiler can deterministically detect structural problems such as:

- dependency cycles,
- the same source required at incompatible accepted versions/packages,
- invalid or missing referenced IDs,
- dangling local change operations,
- illegal operations on protected elements.

Identical source/package dependencies can be deduplicated.

## Semantic conflicts

Two different source elements may contradict each other even though their IDs are unrelated:

```text
Source A: Use spaces for indentation.
Source B: Use tabs for indentation.
```

A deterministic compiler cannot reliably infer that natural-language conflict. It preserves both unless an explicit local resolution exists.

An optional LLM reviewer may flag likely conflicts, explain them, and suggest where to resolve them. The durable decision remains explicit in source.

## Local changes

A node can resolve inherited context through explicit operations such as:

- **Remove** an inherited ordinary element,
- **Override** an inherited ordinary element while preserving its global identity,
- **Use Exception** when a protected element defines an authorized exception for this node.

Operations target stable published IDs, never titles or current wording. The current title should still be shown beside the ID for human orientation.

Protected rules cannot simply be removed or overridden by descendants.

If a later accepted source package removes an element that a local operation still targets, the compiler reports a deterministic dangling-operation diagnostic rather than silently dropping the operation.

## Source updates are change requests

Consumers remain pinned to an accepted source package. A newly published source version is an update candidate, not live inheritance.

The intended workflow is:

1. detect a newer source package,
2. compute a complete deterministic diff,
3. identify structural consequences such as dangling operations,
4. optionally use an LLM to highlight likely semantic impact,
5. review and resolve changes,
6. explicitly accept the new source package,
7. rebuild the node's Official Context Package and entry view.

This preserves independent project lifecycles while still allowing shared context improvements to propagate deliberately.

## Multi-node repositories

A Git repository may publish several independently addressable Context Nodes.

ContextCanon itself is the first dogfood case:

- `contexts/standard/` publishes ContextCanon Standard,
- the repository root publishes ContextCanon Development and composes the Standard.

The exact locator syntax for selecting a node inside a repository is intentionally not frozen until the next vertical POC.
