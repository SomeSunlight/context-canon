# ContextCanon Gateway — Local Context Source
<!-- ctx:node id="a2f4c7e1-9b63-4c48-a19f-3de0c5b28f11" version="0.1.0-draft" adapters="agents,goose" -->

> [!IMPORTANT]
> **Edit this file to change the repository Gateway context.**
> `CONTEXT.md` and optional `CONTEXT/` resources are generated from this source.
>
> This Node is intentionally small: it has no Sources and no Rules. Its job is to provide enough orientation to understand ContextCanon and route a few top-level tasks to the deeper context required for that task.

## Overview

ContextCanon exists because project context tends to grow until every AI task begins by reading far more than it needs. Large advertised context windows are ceilings, not good operating targets: agent harnesses can quickly add system instructions, conversation history, tool traces, files, memories, and generated output. Hosted calls become more expensive as prompts grow, and near practical limits a harness may compact, truncate, or otherwise drop earlier material. A useful operating heuristic is therefore to keep generous headroom — often comfortably below half of the advertised maximum when practical — so the current task still has room to work.

ContextCanon's answer is not simply "use a bigger context window." It gives a project a small official entry, makes reusable context explicit, and uses Topics to load deeper knowledge only when a task needs it. Humans get the same map. ContextCanon grew from experimenting with filesystem-oriented progressive disclosure and not finding one existing mechanism that also combined reusable versioned context, deterministic package identity, explicit acceptance, and harness-neutral operation.

The aim is simple: an unfamiliar human or agent should be able to understand where they are, what applies here, and where to go next without unloading the whole ship first. A good project should provide a gangway, not require a fire hose full of documentation or a ladder tall enough to reach the deck.

## Topics

### Onboard an existing project

When adopting ContextCanon in an existing repository, preparing onboarding evidence, generating or running the onboarding instruction, validating an onboarding proposal, or deciding how to start using ContextCanon on an existing project:

Required:
- Resource: `docs/onboarding.md`
<!-- ctx:topic id="CCG-TOPIC-ONBOARDING" -->

### ContextCanon framework development

When changing ContextCanon's specification, documentation, Context Nodes, compiler, examples, harness integration, or project tooling:

Required:
- Context Node: `nodes/internal/framework-development`
<!-- ctx:topic id="CCG-TOPIC-DEVELOPMENT" -->
