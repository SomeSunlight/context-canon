# Context Composition

ContextCanon combines independent context sources instead of relying on a single inheritance tree.

```text
Business Context ──────┐
Python Context ─────────┤
Personal Style ─────────┼──> Local Delta ──> Official Context Package
Security Context ───────┘
```

A source is an accepted published package from another Context Node. Sources may live in the same Git repository, another repository, or eventually another package location. Repository containment does not define context inheritance.

## No implicit precedence

Source order does not mean priority. ContextCanon must never silently apply "first source wins" or "last source wins" semantics.

Different sources can therefore contribute independent elements without an artificial method-resolution order.

## Dependency graph

Source relationships form a directed acyclic graph. The compiler can deterministically detect structural problems such as:

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

A deterministic compiler cannot reliably prove that these natural-language rules conflict. It preserves both unless an explicit local resolution exists.

An optional LLM reviewer may flag likely conflicts, explain them, and suggest where to resolve them. The durable decision remains explicit in source.

## Local changes

A node can resolve inherited context through explicit operations such as:

- **Remove** an inherited ordinary element,
- **Override** an inherited ordinary element while preserving its global identity,
- **Use Exception** when a protected element defines an authorized exception for this node.

Operations target stable published IDs, never titles or current wording. The current title should still appear beside the ID for human orientation.

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
7. rebuild the node's Official Context Package.

## Multi-node repositories

A Git repository may publish several independently addressable Context Nodes.

ContextCanon itself is the first dogfood case:

- `contexts/public/` publishes **ContextCanon Public (`t`)**,
- the repository root publishes **ContextCanon Development (`t-intern`)** and composes `t`.

The exact locator syntax for selecting a node inside a repository remains intentionally open until the next vertical POC.
