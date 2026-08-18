# Contributing

ContextCanon is currently specification-first. Changes should make the framework easier to understand and use before making the implementation more elaborate.

## Before changing anything

1. Read [CONTEXT.md](CONTEXT.md) for the official project context.
2. Read [STATE.md](STATE.md) for the current development situation.
3. Check [PLAN.md](PLAN.md) if the change affects the current validation work.
4. Load only the topic-specific documentation needed for the task.

## Editing context

Edit [CONTEXT.src.md](CONTEXT.src.md), not `CONTEXT.md`, `AGENTS.md`, `.goosehints`, or `.context/context.yaml`.

Until the compiler exists, generated files are maintained manually for prototyping, but they must still be treated as generated artifacts and kept semantically consistent with `CONTEXT.src.md`.

## Design principles

- Prefer a simple human-facing model over exposing compiler internals.
- Keep deterministic mechanics deterministic; use LLMs only where semantic interpretation is actually required.
- Do not introduce framework machinery without a concrete use case.
- Preserve harness and model independence.
- Make important project knowledge easy to find without loading all of it into every model context.

## Pull requests

Keep changes focused. Explain what changed, why it is needed, and which use case or design pressure motivated it. Documentation-only changes do not require runtime tests, but links and internal consistency should be checked.
