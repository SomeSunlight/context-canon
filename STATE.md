# Current State

ContextCanon has completed two architecture/UX prototype rounds using several real repositories as examples.

The second POC materially simplified the user experience and is the current design baseline:

- `CONTEXT.src.md` is the human-editable local context source.
- `CONTEXT.md` is the generated official context.
- The official context applies to the node itself and is also what child nodes consume.
- A node may compose multiple independent context sources.
- `.context/` is machine-managed state and is normally ignored by humans.
- Machine bookkeeping is consolidated into one primary `.context/context.yaml` file.
- Topics replace user-facing routing terminology.
- Stable IDs are mandatory for addressable elements; published parent contexts expose rule IDs visibly so children can reference them safely.

No production compiler exists yet. The files in this repository manually model the intended compiler output so the design can continue to be tested vertically before implementation is hardened.

## Current focus

Validate the specification with concrete workflows before implementing the deterministic compiler core.

See [PLAN.md](PLAN.md) for the active checklist.
