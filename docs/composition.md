# Context Composition

ContextCanon combines independent context sources instead of relying on a single inheritance tree.

```text
Business Context ──────┐
Python Context ─────────┤
Personal Style ─────────┼──> Local Delta ──> Official Context Package
Security Context ───────┘
```

A Source is an accepted published package from another Context Node. Sources may live in the same Git repository, another repository, or eventually another package location. Repository containment does not define context inheritance.

## No implicit precedence

Source order does not mean priority. ContextCanon must never silently apply "first source wins" or "last source wins" semantics.

Different Sources can therefore contribute independent elements without an artificial method-resolution order.

## Dependency graph

Source relationships form a directed acyclic graph. The compiler can deterministically detect structural problems such as dependency cycles, incompatible accepted source versions, invalid referenced IDs, dangling changes, and illegal operations on protected elements.

## Semantic conflicts

Two different Source elements may contradict each other even though their IDs are unrelated. A deterministic compiler cannot reliably prove every natural-language conflict. It preserves both unless an explicit local resolution exists.

An optional LLM reviewer may flag likely conflicts, explain them, and suggest where to resolve them. The durable decision remains explicit in source.

## Local changes

A node can resolve inherited context through explicit operations such as **Remove**, **Override**, or **Use Exception** for an authorized exception to a protected Rule.

Operations target stable published IDs, never titles or current wording. If a later accepted Source package removes an element that a local operation still targets, the compiler reports a deterministic dangling-operation diagnostic rather than silently dropping it.

## Source updates are change requests

Consumers remain pinned to an accepted Source package. A newly published Source version is an update candidate, not live inheritance.

The intended workflow is: detect a newer package, compute a deterministic diff, identify structural consequences, optionally add semantic LLM review, explicitly accept the update, and rebuild the consumer.

## Navigation is not composition

A Topic may direct an agent to deeper information or even to another Context Node when a task needs it. That is progressive disclosure, not inheritance.

```text
ContextCanon Gateway ──Topic──> ContextCanon Development
                                      ▲
                                      │ Source
                           ContextCanon Foundation
```

The Gateway does not inherit Development. It merely sends development work there. Development does inherit Foundation as an accepted Source and then adds its local delta.

Keeping these relationships distinct prevents navigation choices from silently changing which Rules a node publishes.

## Multi-node repositories

A Git repository may publish several independently addressable Context Nodes. This repository contains three real nodes with different jobs:

- the repository root is **ContextCanon Gateway**, a deliberately tiny entry node,
- `nodes/foundation/` publishes **ContextCanon Foundation**, the reusable baseline,
- `nodes/development/` publishes **ContextCanon Development**, which composes Foundation and adds framework-development context.

The exact external locator syntax for selecting a node inside a repository remains intentionally open until the next vertical POC.