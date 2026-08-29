# ContextCanon Nodes

A **Context Node lives in its own node-root directory**. The node root contains that Node's `CONTEXT.src.md`, generated `CONTEXT.md`, optional `CONTEXT/` resources, and `.context/` machine state.

This `nodes/` directory is only an organizational container. It is **not** a Context Node itself.

Current organization:

```text
nodes/
├── library/                   reusable Nodes distributed with ContextCanon
│   ├── foundation/            ContextCanon Foundation
│   └── development-workflow/  reusable Development Workflow
└── internal/                  Nodes used only by ContextCanon itself
    └── framework-development/ ContextCanon Framework Development
```

The category directories `library/` and `internal/` are also not Nodes. The actual Node roots are the directories beneath them.

The repository root is another Node, **ContextCanon Gateway**. It stays at the repository root because its job is to be the minimal entry for work on this repository.

## Which category should a new Node use?

- Reusable Nodes intended to ship with ContextCanon belong under [`library/`](library/).
- ContextCanon-specific implementation or operational Nodes belong under [`internal/`](internal/).
- Examples and experiments should not be mixed into the reusable library simply because they use ContextCanon.

These categories are conventions of this repository. The ContextCanon framework itself does not require other repositories to use the same directory names.

A Node's stable identity is independent of its path. Moving a Node between directories changes its location, not its identity. The Development Workflow is a concrete example: after real cross-project use proved reuse, its existing Node ID moved from `internal/` to `library/` instead of creating a duplicate Node.
