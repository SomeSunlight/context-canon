# ContextCanon Node Library

This directory contains reusable Context Nodes that are distributed as part of ContextCanon.

Each actual Context Node lives in its **own node-root directory**. A node-root directory contains its `CONTEXT.src.md`, generated `CONTEXT.md`, optional `CONTEXT/` resources, and `.context/` machine state.

The category directory `library/` is not itself a Context Node.

## Current reusable Nodes

- [`foundation/`](foundation/) — **ContextCanon Foundation**, the reusable baseline for ContextCanon authoring, composition, progressive disclosure, stable identity, harness neutrality, and repository conventions.
- [`development-workflow/`](development-workflow/) — **Development Workflow**, the shared Issue/branch/Pull Request/review/checks/merge lifecycle. It defines the workflow contract without choosing the infrastructure that implements it.
- [`github/`](github/) — **GitHub**, a concrete Development Workflow provider for ordinary github.com development infrastructure.
- [`github-local/`](github-local/) — **GitHub Local**, a concrete Development Workflow provider for a local GitHub-compatible development surface with visible repository Issues.

The provider split is intentionally simple:

```text
Development Workflow
        ▲
        │ Source
   ┌────┴─────┐
 GitHub    GitHub Local
```

The workflow keeps the familiar development vocabulary. A provider makes that vocabulary concrete so normal agents do not have to interpret a project-specific abstraction table on every task.

## Composition policy

A reusable library Node should compose another Source only when its own semantics actually depend on that Source.

Foundation is the natural baseline for Nodes whose meaning depends on ContextCanon authoring/governance conventions, but it is **not a mandatory transitive dependency for every reusable Node**. Independent concerns should remain independent Sources so consumers can compose exactly what they need without removing unrelated inherited context later.

Source dependencies are therefore explicit product decisions, not a library-directory inheritance rule.

## Adding a reusable Node

A new reusable Node intended to ship with ContextCanon belongs at:

```text
nodes/library/<node-name>/
```

It should receive its own stable Node identity and lifecycle. Do not add examples, experiments, or repository-internal contexts to the library merely because they use ContextCanon.

ContextCanon-specific internal Nodes live under [`../internal/`](../internal/) instead.
