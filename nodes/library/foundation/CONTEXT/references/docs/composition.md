# Context Composition

ContextCanon combines independent context Sources instead of relying on a single inheritance tree.

```text
Business Context ──────┐
Python Context ─────────┤
Personal Style ─────────┼──> Local Delta ──> Official Context Package
Security Context ───────┘
```

A Source is an accepted published package from another Context Node. Sources may live in the same Git repository, another repository, or eventually another package location. Filesystem containment does not create inheritance.

## No implicit precedence

Source order does not mean priority. ContextCanon must never silently apply "first source wins" or "last source wins" semantics.

Different Sources can therefore contribute independent elements without an artificial method-resolution order.

## Dependency graph

Source relationships form a directed acyclic graph. The compiler can deterministically detect structural problems such as dependency cycles, incompatible accepted Source versions, invalid referenced IDs, dangling changes, and illegal operations on protected elements.

Walking Skeleton 1 implements cycle detection plus Source Node ID/version validation for local-path Sources.

## Semantic conflicts

Two different Source elements may contradict each other even though their IDs are unrelated. A deterministic compiler cannot reliably prove every natural-language conflict. It preserves both unless an explicit local resolution exists.

An optional LLM reviewer may flag likely conflicts, explain them, and suggest where to resolve them. The durable decision remains explicit in source.

## Local changes

A Node will be able to resolve inherited context through explicit operations such as **Remove**, **Override**, or **Use Exception** for an authorized exception to a protected Rule.

These operations are part of the specification but intentionally not implemented in Walking Skeleton 1. Unsupported syntax should fail rather than be approximated.

## Source updates are change requests

Consumers ultimately remain pinned to an accepted Source package. A newly published Source version is an update candidate, not live inheritance.

The intended workflow is: detect a newer package, compute a deterministic diff, identify structural consequences, optionally add semantic LLM review, explicitly accept the update, and rebuild the consumer.

## Navigation is not composition

A Topic may direct an agent to deeper information or even to another Context Node when a task needs it. That is progressive disclosure, not inheritance.

```text
ContextCanon Gateway ──Topic──> ContextCanon Framework Development
                                      ▲
                                      │ Source
                           ContextCanon Foundation
```

The Gateway does not inherit Framework Development. It merely sends framework-development work there. Framework Development does inherit Foundation as a Source and then adds its local delta.

Keeping these relationships distinct prevents navigation choices from silently changing which Rules a Node publishes.

## Node directories do not define composition

Every Context Node is physically rooted in its own directory, but that directory is only its location. A parent directory, nested directory, Git repository, or sibling directory does not become a Source automatically.

This matters in repositories containing several Nodes: filesystem structure can organize them clearly without creating hidden context relationships.

## ContextCanon's own Node organization

This repository contains three real Nodes:

- the repository root is **ContextCanon Gateway**,
- `nodes/library/foundation/` is **ContextCanon Foundation**,
- `nodes/internal/framework-development/` is **ContextCanon Framework Development**.

The intermediate `nodes/`, `nodes/library/`, and `nodes/internal/` directories are organizational containers, not Context Nodes.

Every reusable Node distributed in the **ContextCanon Node Library** must compose Foundation directly or transitively through another library Node. That is a policy of this library, not a required directory structure or inheritance Rule for unrelated projects using ContextCanon.

Walking Skeleton 1 supports local node-root locators. External repository/package locators remain a later hardening step.
