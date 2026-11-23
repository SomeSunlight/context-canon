# Development Workflow Documentation

This directory contains the **human-authored explanation** of the reusable Development Workflow Node.

Read [`version-provenance-python.md`](version-provenance-python.md) when implementing offline CLI version identity, PEP 610 Git installs, or an explicit read-only remote version check. Read [`change-workflow.md`](change-workflow.md) when you need the practical sequence for planning, resuming, reviewing, finalizing a coherent change, merging it, and closing the accepted baseline afterwards.

For public contributions to third-party GitHub repositories, [`external-github-publication.md`](external-github-publication.md) offers an **optional best practice** for publishing a reviewed issue through an authenticated personal `gh` CLI when a connected GitHub App has no write access. Alternatives remain valid; it is not a mandatory Rule.

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
