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

ContextCanon exists because project context tends to grow until every AI task begins by reading far more than it needs. Large advertised context windows are ceilings, not good operating targets: agent harnesses can quickly add system instructions, conversation history, tool traces, files, memories, and generated output. Hosted calls become more expensive as prompts grow, and near practical limits a harness may compact, truncate, or otherwise drop earlier material. A useful operating heuristic is therefore to keep generous headroom — often comfortably below half of the advertised maximum when practical — so the current task still has room to work.

ContextCanon's answer is not simply "use a bigger context window." It gives a project a small official entry, makes reusable context explicit, and uses Topics to load deeper knowledge only when a task needs it. Humans get the same map. ContextCanon grew from experimenting with filesystem-oriented progressive disclosure and not finding one existing mechanism that also combined reusable versioned context, deterministic package identity, explicit acceptance, and harness-neutral operation.

The aim is simple: an unfamiliar human or agent should be able to understand where they are, what applies here, and where to go next without unloading the whole ship first. A good project should provide a gangway, not require a fire hose full of documentation or a ladder tall enough to reach the deck.

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
