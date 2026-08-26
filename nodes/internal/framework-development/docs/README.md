# Framework Development documentation

These are the **human-authored technical documents owned by the ContextCanon Framework Development Node**.

Use the Node's [`CONTEXT.md`](../CONTEXT.md) rather than reading this whole directory up front. Its Topics select the documents needed for a compiler, architecture, onboarding, format, composition, harness, test/CI, or state/planning task.

## Authoring versus generated package copies

Files here are source documentation. During compilation, Topic resources are copied into the Node's generated `CONTEXT/references/...` tree so the Official Context Package is self-contained.

That means a document may be visible twice in the repository tree:

```text
nodes/internal/framework-development/docs/architecture.md
        ↓ deterministic materialization
nodes/internal/framework-development/CONTEXT/references/nodes/internal/framework-development/docs/architecture.md
```

Only the first path is authored. The second is generated package output and must not be edited or maintained separately. `contextcanon check --all .` detects stale generated copies.

The somewhat explicit generated path is intentional: it preserves the repository-relative origin of the materialized resource and makes provenance visible inside the package.
