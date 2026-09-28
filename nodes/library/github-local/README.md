# GitHub Local

This reusable Context Node is the local provider for [Development Workflow](../development-workflow/).

Its purpose is deliberately narrow: preserve the well-known GitHub development model for projects that cannot or should not use github.com.

```text
Issue → branch → Pull Request → review → checks → merge
```

Normal project work should not need to understand a provider abstraction. Agents use the familiar workflow and the configured `github.local` tooling. Provider/runtime details are loaded only when installation, configuration or troubleshooting makes them relevant.

The executable `github.local` runtime is intentionally **not part of ContextCanon**. It is a separate application boundary; this Node defines only the project-facing Context that applies when that provider is selected.

## Runtime / installation status

The **Context Node is available now**, but the executable `github.local` runtime is **not implemented yet**. Work on that separate project is starting now.

Until that runtime exists, selecting GitHub Local during ContextCanon onboarding establishes the intended workflow semantics and durable project Context, but it does **not** by itself install or start a local forge or connect an agent to one.

The future runtime project will own the operational path:

```text
install github.local
        ↓
start/use local GitHub-compatible API
        ↓
point the official GitHub MCP server at it
        ↓
connect Copilot / Goose / Hermes / another capable agent
```

Exact installation commands, supported GitHub API/MCP operations, authentication, process lifetime, and storage layout will be documented by that runtime project once implemented. This Context Node should stay stable even if those operational details evolve.
