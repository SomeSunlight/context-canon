# Contributing

ContextCanon is currently specification-first. Changes should make the framework easier to understand and use before making the implementation more elaborate.

## Before changing anything

1. Read the repository [CONTEXT.md](CONTEXT.md). It is intentionally a tiny Gateway.
2. For ContextCanon development work, follow its Required target to [nodes/development/CONTEXT.md](nodes/development/CONTEXT.md).
3. Read [STATE.md](STATE.md) for the current project situation.
4. Check [PLAN.md](PLAN.md) if the change affects active validation work.
5. Load only the Topic material required for the task.

## Editing context

Three Context Nodes are currently dogfooded in this repository:

- Gateway: edit [CONTEXT.src.md](CONTEXT.src.md),
- Foundation: edit [nodes/foundation/CONTEXT.src.md](nodes/foundation/CONTEXT.src.md),
- Development: edit [nodes/development/CONTEXT.src.md](nodes/development/CONTEXT.src.md).

Do not directly edit generated `CONTEXT.md`, `CONTEXT/`, harness adapters, or `.context/context.yaml` files.

Until the compiler exists, generated files are maintained manually for prototyping, but they must still be treated as generated artifacts and kept semantically consistent with their sources.

## Design principles

- Prefer a simple human-facing model over exposing compiler internals.
- Keep deterministic mechanics deterministic; use LLMs only where semantic interpretation is actually required.
- Do not introduce framework machinery without a concrete use case.
- Preserve harness and model independence.
- Make important project knowledge easy to find without loading all of it into every model context.
- Keep tiny nodes genuinely tiny; empty generated structures are not a feature.

## Pull requests

Keep changes focused. Explain what changed, why it is needed, and which use case or design pressure motivated it. Documentation-only changes do not require runtime tests, but links and internal consistency should be checked.
