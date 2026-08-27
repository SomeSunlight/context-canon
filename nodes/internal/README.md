# Internal Context Nodes

This directory contains Context Nodes used to design, implement, maintain, or operate ContextCanon itself. They are not part of the reusable ContextCanon Node Library.

Each actual Context Node lives in its own **node-root directory**. The category directory `internal/` is only organizational and is not itself a Context Node.

Current internal Nodes:

- [`framework-development/`](framework-development/) — **ContextCanon Framework Development**, the context for designing and implementing ContextCanon. It composes ContextCanon Foundation plus the internal Development Workflow and adds only framework-development context.
- [`development-workflow/`](development-workflow/) — **ContextCanon Development Workflow**, ContextCanon's own internal Rules for recoverable LLM-assisted planning, checkpointing, proportional verification, and project-owner review.

Add another internal Node only when ContextCanon itself has a distinct context with its own identity and lifecycle.

Reusable Nodes intended for ContextCanon users belong under [`../library/`](../library/) instead.
