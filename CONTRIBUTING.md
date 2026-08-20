# Contributing

ContextCanon now has an executable deterministic compiler walking skeleton. Changes should keep the human model simple while extending the compiler only as far as an end-to-end use case requires.

## Before changing anything

1. Read the repository [CONTEXT.md](CONTEXT.md). It is intentionally a tiny Gateway.
2. For ContextCanon development work, follow its Required target to [nodes/internal/framework-development/CONTEXT.md](nodes/internal/framework-development/CONTEXT.md).
3. Read [STATE.md](STATE.md) for the current project situation.
4. Check [PLAN.md](PLAN.md) for the active executable slice.
5. Load only the Topic material required for the task.

## Editing context

Three Context Nodes are currently dogfooded in this repository:

- Gateway: edit [CONTEXT.src.md](CONTEXT.src.md),
- Foundation: edit [nodes/library/foundation/CONTEXT.src.md](nodes/library/foundation/CONTEXT.src.md),
- Framework Development: edit [nodes/internal/framework-development/CONTEXT.src.md](nodes/internal/framework-development/CONTEXT.src.md).

Do not directly edit generated `CONTEXT.md`, `CONTEXT/`, harness adapters, or `.context/context.yaml` files.

After changing ContextCanon source or referenced material, rebuild and verify the generated result:

```text
python -m pip install -e .
contextcanon build --all .
contextcanon check --all .
```

`build` is allowed to add, replace, or remove generated package files so the filesystem matches the compiler's expected output. `check` performs the same compilation in memory and fails when committed output has drifted.

## Tests

Run the deterministic test suite before publishing compiler changes:

```text
python -m unittest discover -s tests -v
```

The tests must not require an LLM, network service, or external repository. New deterministic behavior should normally arrive with a fixture that proves it.

GitHub Actions runs both the unit tests and `contextcanon check --all .`.

## Design principles

- Prefer a simple human-facing model over exposing compiler internals.
- Keep deterministic mechanics deterministic; use LLMs only where semantic interpretation is actually required.
- Do not introduce framework machinery without a concrete end-to-end use case.
- Preserve harness and model independence.
- Make important project knowledge easy to find without loading all of it into every model context.
- Keep tiny Nodes genuinely tiny; empty generated structures are not a feature.
- Unsupported semantics should fail clearly rather than be approximated silently.

## Pull requests

Keep changes focused. Explain what changed, why it is needed, and which observed use case or failure motivated it. Separate deterministic compiler truth from any LLM-assisted interpretation layered on top.
