# Current State

ContextCanon has completed two repository-based architecture/UX prototype rounds and repeated mental walkthroughs of critical use cases.

The current design baseline is:

- `CONTEXT.src.md` is the human-editable local delta.
- `CONTEXT.md` is the generated compact official entry view.
- `CONTEXT/` contains deeper compiled/materialized context resources.
- Together, `CONTEXT.md` and `CONTEXT/` form the human/agent-facing **Official Context Package**.
- Topics provide progressive disclosure and distinguish **Required** from **Optional** deeper material.
- A node may compose multiple independent context sources without implicit source precedence.
- Stable IDs are mandatory for addressable elements; published parent contexts expose IDs visibly.
- `.context/` is machine-managed state and normally ignored by humans; one primary `context.yaml` per node is the current POC shape.
- Harness/model-specific files are adapters only.
- Deterministic operations form the framework skeleton; LLMs assist where semantic interpretation is actually needed.

## ContextCanon dogfoods two nodes

- `contexts/public/` is **ContextCanon Public (`t`)**, the public baseline intended for ordinary client nodes.
- the repository root is **ContextCanon Development (`t-intern`)**, which composes `t` and adds design/compiler rules.

The ContextCanon schema/specification defines the structural interface implemented by both nodes. A separate interface node is not currently needed because an interface describes structure, while a Context Node publishes actual context content.

## Current POC refinement

The latest refinement makes the package boundary physical rather than merely conceptual:

```text
CONTEXT.md
CONTEXT/
```

Source material may stay in natural repository locations such as `docs/`. The future compiler will materialize resources needed by the published package into `CONTEXT/` and rewrite generated links accordingly.

`docs/topics.md` now treats Topics as a general context-integration mechanism that can later include glossaries, code examples, structured data, PDFs, images, skills, and operational experience without loading all of it eagerly.

No production compiler exists yet. Current generated files and package copies are manually modeled POC output.

## Current focus

Run the next vertical POC against real example repositories using the public `t` node, self-contained `CONTEXT/` resources, Required/Optional Topics, local deltas, and at least one source-update scenario before freezing the V1 parser/model.

See [PLAN.md](PLAN.md) for the active checklist.
