# ContextCanon Node Library

This directory contains reusable Context Nodes that are distributed as part of ContextCanon.

Each actual Context Node lives in its **own node-root directory**. A node-root directory contains its `CONTEXT.src.md`, generated `CONTEXT.md`, optional `CONTEXT/` resources, and `.context/` machine state.

The category directory `library/` is not itself a Context Node.

## Foundation

[`foundation/`](foundation/) is **ContextCanon Foundation**, the common baseline of the ContextCanon Node Library.

Every reusable Node published in this library must compose Foundation either directly or transitively through another library Node. This keeps the shared framework contract in one place while still allowing specialized Nodes to add only their own delta.

## Adding a reusable Node

A new reusable Node intended to ship with ContextCanon belongs at:

```text
nodes/library/<node-name>/
```

It should receive its own stable Node identity and lifecycle. Do not add examples, experiments, or repository-internal contexts to the library merely because they use ContextCanon.

ContextCanon-specific internal Nodes live under [`../internal/`](../internal/) instead.
