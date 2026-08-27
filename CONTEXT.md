# ContextCanon Gateway — Official Context

> [!CAUTION]
> **GENERATED FILE — DO NOT EDIT.**
> This is the compact official entry for this Context Node.
> Together with `CONTEXT/` it forms the human/agent-facing Official Context Package.
>
> Edit [CONTEXT.src.md](CONTEXT.src.md) instead.

**Node:** ContextCanon Gateway  
**Context version:** `0.1.0-draft`

## Overview

Most AI projects eventually build a **static context bundle** by hand or with an LLM: a prompt, instruction file, or curated summary that tries to contain everything the model should know. It works until something important is missing; then the harness searches other repository files opportunistically, and whether it finds the right detail becomes less predictable. As the project changes, copied context also drifts and every duplicate becomes another place to review and repair.

ContextCanon keeps the always-needed overview small, puts deeper detail behind explicit Topics, and makes reusable context a versioned Source instead of another copy. Humans and agents get the same landing points, while detailed knowledge can live close to the narrow context where it belongs without bloating every higher-level overview. Rebuilds propagate accepted Source and authoring changes deterministically into the generated child packages.

The aim is simple: an unfamiliar human or agent should be able to understand where they are, what applies here, and where to go next — without depending on a lucky repository search or maintaining the same guidance in several static prompt bundles.

## How to use this context

For the current task, evaluate each Topic condition. When one matches, read every **Required** target before continuing; read **Optional** targets only when useful.

This Node defines no Rules.

## Topics

### Onboard an existing project

When adopting ContextCanon in an existing repository, preparing onboarding evidence, generating or running the onboarding instruction, validating an onboarding proposal, or deciding how to start using ContextCanon on an existing project:

**Required**

- [`CONTEXT/references/docs/onboarding.md`](CONTEXT/references/docs/onboarding.md)

### ContextCanon framework development

When changing ContextCanon's specification, documentation, Context Nodes, compiler, examples, harness integration, or project tooling:

**Required**

- [ContextCanon Framework Development](nodes/internal/framework-development/CONTEXT.md)
