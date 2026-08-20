# Harness Adapters

ContextCanon is harness- and model-independent.

`CONTEXT.md` is the compact official entry view into a node's Official Context Package. Harness-specific files are generated adapters that direct a particular tool to that entry view and, where the harness permits, to the Topic-loading behavior.

## Design rule

Canonical project context and project code must not depend on Codex, goose, Claude, Copilot, or another particular harness.

Do not copy the full project context into every harness-specific file. An adapter should be as small as the harness allows and contain only the mechanics needed to enter ContextCanon correctly.

## Gateway nodes

A harness adapter should enter the Context Node that applies at its filesystem scope. It should not bypass a minimal Gateway merely because a deeper node contains more information.

In this repository the root adapters enter **ContextCanon Gateway**. The Gateway then uses ordinary Topic semantics to require `nodes/internal/framework-development/CONTEXT.md` when a task concerns ContextCanon framework development.

This keeps harness behavior mechanical and lets ContextCanon itself decide how much context a task needs.

## AGENTS.md

ContextCanon can generate `AGENTS.md` as an entry point for harnesses that support it.

OpenAI documents `AGENTS.md` as persistent repository guidance for Codex, including hierarchical files scoped by directory. A generated adapter should point Codex to the applicable `CONTEXT.md`, tell it to follow Required Topic targets when a Topic applies, and avoid duplicating the complete package.

OpenAI references:
- https://openai.com/index/introducing-codex/
- https://openai.com/index/unrolling-the-codex-agent-loop/

## goose

Current goose documentation lists the default `CONTEXT_FILE_NAMES` value as `[".goosehints"]` and allows custom/multiple filenames.

ContextCanon therefore generates a small `.goosehints` adapter that points to the applicable `CONTEXT.md`, instead of assuming goose automatically loads `AGENTS.md`.

goose reference:
- https://github.com/block/goose/blob/main/documentation/docs/guides/environment-variables.md

## Other harnesses

Additional adapters should be added only after verifying the harness's current official behavior.

Harness configuration changes faster than the ContextCanon semantic model. Compatibility therefore belongs in this dedicated adapter layer rather than in project governance, canonical context semantics, or project code.
