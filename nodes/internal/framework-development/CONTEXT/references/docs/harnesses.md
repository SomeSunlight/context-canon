# Harness Adapters

ContextCanon is harness- and model-independent.

`CONTEXT.md` is the compact official entry view into a node's Official Context Package. Harness-specific files are generated adapters that direct a particular tool to that entry view.

`CONTEXT.md` is deliberately self-describing: it states that Rules apply to every task in the Node and explains how to evaluate Topics and load Required versus Optional targets. Adapters therefore stay small and do not need to duplicate those semantics.

## Design rule

Canonical project context and project code must not depend on Codex, goose, Copilot, Claude, or another particular harness.

Do not copy the full project context into every harness-specific file. An adapter should be as small as the harness allows and contain only the mechanics needed to enter ContextCanon correctly.

## Gateway nodes

A harness adapter should enter the Context Node that applies at its filesystem scope. It should not bypass a minimal Gateway merely because a deeper node contains more information.

In this repository the root adapters enter **ContextCanon Gateway**. The Gateway then uses ordinary Topic semantics to require `nodes/internal/framework-development/CONTEXT.md` when a task concerns ContextCanon framework development.

This keeps harness behavior mechanical and lets ContextCanon itself decide how much context a task needs.

## AGENTS.md

ContextCanon can generate `AGENTS.md` as an entry point for harnesses that support it.

OpenAI documents `AGENTS.md` as persistent repository guidance for Codex, including hierarchical files scoped by directory. A generated adapter points Codex to the applicable `CONTEXT.md` rather than duplicating the complete package.

OpenAI references:
- https://openai.com/index/introducing-codex/
- https://openai.com/index/unrolling-the-codex-agent-loop/

## goose

Current goose documentation lists the default `CONTEXT_FILE_NAMES` value as `[".goosehints"]` and allows custom/multiple filenames.

ContextCanon therefore generates a small `.goosehints` adapter that points to the applicable `CONTEXT.md`, instead of assuming goose automatically loads `AGENTS.md`.

goose reference:
- https://github.com/block/goose/blob/main/documentation/docs/guides/environment-variables.md

## GitHub Copilot

GitHub Copilot Chat in JetBrains IDEs supports repository-wide custom instructions through `.github/copilot-instructions.md`. GitHub states that these instructions are automatically added to requests made in the repository context.

ContextCanon therefore generates `.github/copilot-instructions.md` for the `copilot` adapter. The file points Copilot to the root `CONTEXT.md`; it does not reproduce project Rules or Topic content.

For the JetBrains IDE workflow, ContextCanon does not rely on `AGENTS.md` being consumed by Copilot Chat. GitHub's current support matrix distinguishes repository-wide Copilot instructions from agent-instruction files used by other Copilot agent surfaces.

GitHub references:
- https://docs.github.com/en/copilot/how-tos/configure-custom-instructions-in-your-ide/add-repository-instructions-in-your-ide
- https://docs.github.com/en/copilot/reference/custom-instructions-support

## Other harnesses

Additional adapters should be added only after verifying the harness's current official behavior.

Harness configuration changes faster than the ContextCanon semantic model. Compatibility therefore belongs in this dedicated adapter layer rather than in project governance, canonical context semantics, or project code.
