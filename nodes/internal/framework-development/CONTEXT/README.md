# Generated Context package resources

> [!CAUTION]
> **GENERATED DIRECTORY — DO NOT EDIT THESE FILES.**
> Start with [`../CONTEXT.md`](../CONTEXT.md), the compact Official Context entry for this Node.

This `CONTEXT/` directory exists because the Node has deeper Topic resources that should be available **without loading them into every task**.

## Why `references/` may look like duplicate documentation

`references/` contains exact materialized copies of authored Topic resources. The path after `CONTEXT/references/` preserves the resource's repository-relative source path at build time.

For example:

```text
nodes/internal/framework-development/docs/architecture.md
        ↓ deterministic materialization
CONTEXT/references/nodes/internal/framework-development/docs/architecture.md
```

The first path is the authored source. The second path is generated package content and is **not another maintenance surface**.

The copy is intentional: it makes the Official Context Package self-contained, so the package can later be published or consumed without needing the original authoring repository layout. In a standalone package the original source path may no longer exist; the materialized copy is what preserves the reviewed resource bytes.

`contextcanon build` refreshes generated package files. `contextcanon check` reports drift when committed generated output no longer matches the authored source and compiler.
