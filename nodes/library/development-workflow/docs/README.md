# Development Workflow Documentation

This directory contains the **human-authored explanation** of the reusable Development Workflow Node.

Read [`change-workflow.md`](change-workflow.md) when you need the practical sequence for planning, resuming, reviewing, finalizing a coherent change, merging it, and closing the accepted baseline afterwards.

The durable normative Rules live one level up in [`../CONTEXT.src.md`](../CONTEXT.src.md). This directory explains how to apply them in practice; it is not a second rule source.

A useful mental model is:

```text
CONTEXT.src.md             durable workflow rules
        ↓
docs/change-workflow.md    practical operating explanation
        ↓
generated CONTEXT/...      compiler-owned package material
```

Project-specific tooling, exact test commands, release mechanics, and platform conventions stay with the consuming project. The reusable workflow defines the lifecycle boundaries; consumers provide their local implementation details.
