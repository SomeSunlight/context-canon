# Development Workflow Documentation

This directory contains the **human-authored explanation** of ContextCanon's internal development workflow.

Read [`change-workflow.md`](change-workflow.md) when you need the practical sequence for planning, resuming, reviewing, finalizing ContextCanon's self-hosted generated packages, and merging a coherent change block.

The durable normative Rules live one level up in [`../CONTEXT.src.md`](../CONTEXT.src.md). This directory explains how to apply them in practice; it is not a second rule source.

A useful mental model is:

```text
CONTEXT.src.md             durable workflow rules
        ↓
docs/change-workflow.md    practical operating explanation
        ↓
generated CONTEXT/...      compiler-owned package material
```

For the current single-developer flow, project-owner review may happen before all CI is green when remaining failures are understood and disclosed. Full exact-head green CI and zero generated drift belong to the final merge gate.
