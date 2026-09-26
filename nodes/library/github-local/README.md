# GitHub Local

This reusable Context Node is the local provider for [Development Workflow](../development-workflow/).

Its purpose is deliberately narrow: preserve the well-known GitHub development model for projects that cannot or should not use github.com.

```text
Issue → branch → Pull Request → review → checks → merge
```

Normal project work should not need to understand a provider abstraction. Agents use the familiar workflow and the configured `github.local` tooling. Provider/runtime details are loaded only when installation, configuration or troubleshooting makes them relevant.

The executable `github.local` runtime is intentionally **not part of ContextCanon**. It is a separate application boundary; this Node defines only the project-facing Context that applies when that provider is selected.
