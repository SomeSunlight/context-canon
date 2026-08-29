# Internal Context Nodes

This directory contains Context Nodes used to design, implement, maintain, or operate ContextCanon itself. They are not part of the reusable ContextCanon Node Library.

Each actual Context Node lives in its own **node-root directory**. The category directory `internal/` is only organizational and is not itself a Context Node.

Current internal Node:

- [`framework-development/`](framework-development/) — **ContextCanon Framework Development**, the context for designing and implementing ContextCanon. It composes ContextCanon Foundation plus the reusable Development Workflow and adds only framework-development context.

The Development Workflow originally lived here while reuse was unproven. The real `ai-workstation` onboarding exercise demonstrated cross-project value, so the same stable Node identity now lives under [`../library/development-workflow/`](../library/development-workflow/) rather than being copied into a second Node.

Add another internal Node only when ContextCanon itself has a distinct context with its own identity and lifecycle.

Reusable Nodes intended for ContextCanon users belong under [`../library/`](../library/) instead.
