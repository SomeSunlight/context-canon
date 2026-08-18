# ContextCanon

**Composable, versioned project context for humans and AI agents.**

ContextCanon lets a project compose reusable context sources with a small local delta and publish one official context that applies to both the project itself and its child nodes.

The goal is simple: stop repeating project rules, terminology, architecture hints, examples, and hard-won experience in every AI chat or harness-specific instruction file.

## The core model

```text
Context Source A ─────┐
Context Source B ─────┤
Context Source C ─────┼──> compile ──> Official Context
                      │
Local Delta ──────────┘
```

The **Official Context** is the project's notice board: what applies here. The same published context is what child nodes may compose as a source.

ContextCanon is deliberately independent of any specific LLM or agent harness. Harness files such as `AGENTS.md` or `.goosehints` are thin generated entry points, not sources of truth.

## What belongs in context?

Rules are the first use case, not the limit. The architecture is intended to grow toward reusable:

- rules and constraints,
- terminology and glossaries,
- topic-specific references,
- patterns and example code,
- hints and practices,
- skills and workflows,
- experience and known pitfalls.

All of these help humans and models understand *how this project works and why*.

## Human-facing files

```text
repository/
├── README.md
├── CONTRIBUTING.md
├── CHANGELOG.md
├── STATE.md
├── PLAN.md
│
├── CONTEXT.src.md       # edit: local context and source composition
├── CONTEXT.md           # read: generated official context
├── AGENTS.md            # generated harness adapter
├── .goosehints          # generated goose adapter
│
└── .context/            # generated machine state; normally ignore
    └── context.yaml
```

`CONTEXT.src.md` shows only what this node adds or changes. `CONTEXT.md` shows the fully compiled official result. `.context/` contains IDs, source snapshots, provenance, digests, and other compiler bookkeeping.

## Start here

- [Concepts](docs/concepts.md)
- [Context composition](docs/composition.md)
- [Source format](docs/source-format.md)
- [Official context](docs/official-context.md)
- [Topics](docs/topics.md)
- [State and planning](docs/state.md)
- [Harness adapters](docs/harnesses.md)
- [Architecture](docs/architecture.md)

## Project status

ContextCanon is currently a specification and prototype project. The user-facing architecture has been explored through two repository-based POCs; no production compiler exists yet.

See [STATE.md](STATE.md) for the current situation and [PLAN.md](PLAN.md) for the next validation steps.
