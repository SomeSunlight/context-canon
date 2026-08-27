# Framework Development documentation

These are the **human-authored framework-specific documents owned by the ContextCanon Framework Development Node**.

Use the Node's [`CONTEXT.md`](../CONTEXT.md) rather than reading this whole directory up front. Its Topics select the documents needed for compiler implementation, framework architecture, reviewed onboarding, tests/CI, project state/planning, or framework-specific use cases.

Reusable ContextCanon authoring-format, Official Context, Topic, composition, and harness guidance is owned by [ContextCanon Foundation](../../../library/foundation/) under [`../../../library/foundation/docs/`](../../../library/foundation/docs/). Framework Development references those Foundation resources when needed instead of maintaining a second authored copy here.

## Authoring versus generated package copies

Files here are source documentation. During compilation, Topic resources are copied into the Node's generated `CONTEXT/references/...` tree so the Official Context Package is self-contained.

That means a framework-specific document may be visible twice in the repository tree:

```text
nodes/internal/framework-development/docs/architecture.md
        ↓ deterministic materialization
nodes/internal/framework-development/CONTEXT/references/nodes/internal/framework-development/docs/architecture.md
```

Only the first path is authored. The second is generated package output and must not be edited or maintained separately. Cross-Node Foundation resources are materialized from their owning authored paths in the same deterministic way. `contextcanon check --all .` detects stale generated copies.

The explicit generated path is intentional: it preserves the repository-relative origin of the materialized resource and makes provenance visible inside the package.
