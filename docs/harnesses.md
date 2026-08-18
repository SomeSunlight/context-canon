# Harness Adapters

ContextCanon is harness- and model-independent. `CONTEXT.md` is the official project context; harness files are generated entry points that direct a particular tool to it.

## Design rule

Do not copy the full project context into every harness-specific file. An adapter should be as small as the harness allows.

This avoids duplicated truth when a repository is used by several tools.

## AGENTS.md

ContextCanon can generate `AGENTS.md` as an entry point for harnesses that support it.

OpenAI documents `AGENTS.md` as persistent repository guidance for Codex, including hierarchical files scoped by directory. ContextCanon's generated root adapter should therefore point Codex to the official `CONTEXT.md` and relevant State/Topics rather than duplicating the complete context.

OpenAI references:
- https://openai.com/index/introducing-codex/
- https://openai.com/index/unrolling-the-codex-agent-loop/

## goose

As of the current goose documentation, the default `CONTEXT_FILE_NAMES` value is `[".goosehints"]`. It can be configured to load additional/custom context filenames.

ContextCanon therefore generates a small `.goosehints` adapter that points to `CONTEXT.md`, instead of assuming goose will automatically load `AGENTS.md`.

goose reference:
- https://github.com/aaif-goose/goose/blob/main/documentation/docs/guides/environment-variables.md

## Other harnesses

Additional adapters should be added only after verifying the harness's current official behavior. Harness configuration changes faster than the ContextCanon semantic model, so compatibility belongs in this dedicated layer rather than in project governance.
