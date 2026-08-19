# ContextCanon Nodes

This directory contains reusable or independently meaningful Context Nodes published by the ContextCanon project.

The repository currently uses two nodes here:

- [`foundation/`](foundation/) — **ContextCanon Foundation**, the reusable baseline.
- [`development/`](development/) — **ContextCanon Development**, which composes Foundation and adds only the context needed to design and implement ContextCanon itself.

The repository root is a third node, **ContextCanon Gateway**. It stays at the root because its job is to be the minimal entry for work on the repository.

More directories should be added here only when a real reusable context with its own identity and lifecycle emerges. The directory is not intended as an empty taxonomy of possible future node types.
