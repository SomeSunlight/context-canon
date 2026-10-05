# GitHub Local Provider Boundary

`github.local` is intended to be a small local GitHub-compatible development service, not a second ContextCanon subsystem and not a complete clone of GitHub.

## Normal operating model

A capable local agent works on code through the local filesystem, shell and Git working tree:

```text
Copilot / Goose / Hermes / other agent
        │
        ├── filesystem + shell ──> local working tree + Git
        │
        └── GitHub tools ────────> official GitHub MCP server
                                      │
                                      └── github.local API
```

The GitHub-compatible tool surface exists for forge concepts such as Issues, Pull Requests, reviews, checks and merge state. It should not become a filesystem proxy when the harness can already work on the local checkout.

## Runtime boundary

The executable runtime is a separate project/application. ContextCanon may publish this provider Context and projects may select it, but ContextCanon does not need to stay running for development work and does not own the local forge server.

The intended first implementation is deliberately small:

- expose only the GitHub-compatible API subset required by the enabled official GitHub MCP tools;
- use native local Git for branches, commits, diffs and merges;
- keep canonical Issue content as visible Markdown below `issues/`;
- add further GitHub-compatible operations only when real workflows require them;
- never require a cloud service merely to preserve the workflow.

A practical integration may point the official GitHub MCP server at a loopback GitHub-compatible host. Exact process-launch, port, authentication and storage details belong to the separate `github.local` runtime project and are intentionally not fixed by this Context Node.

## Portability

The important contract is the development language seen by humans and agents:

```text
Issue → branch → Pull Request → review → checks → merge
```

A project can therefore move between GitHub and GitHub Local without replacing that mental model. Provider changes alter the infrastructure underneath the workflow, not the workflow vocabulary loaded into every task.
