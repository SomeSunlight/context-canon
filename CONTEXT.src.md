# ContextCanon Gateway — Local Context Source
<!-- ctx:node id="a2f4c7e1-9b63-4c48-a19f-3de0c5b28f11" version="0.1.0-draft" adapters="agents,goose" -->

> [!IMPORTANT]
> **Edit this file to change the repository Gateway context.**
> `CONTEXT.md` and optional `CONTEXT/` resources are generated from this source.
>
> This Node is intentionally small: it has no Sources and no Rules. Its job is to provide enough orientation to understand ContextCanon and route a few top-level tasks to the deeper context required for that task.

## Overview

Most AI projects eventually build a **static context bundle** by hand or with an LLM: a prompt, instruction file, or curated summary that tries to contain everything the model should know. It works until something important is missing; then the harness searches other repository files opportunistically, and whether it finds the right detail becomes less predictable. As the project changes, copied context also drifts and every duplicate becomes another place to review and repair.

ContextCanon keeps the always-needed overview small, puts deeper detail behind explicit Topics, and makes reusable context a versioned Source instead of another copy. Humans and agents get the same landing points, while detailed knowledge can live close to the narrow context where it belongs without bloating every higher-level overview. Rebuilds propagate accepted Source and authoring changes deterministically into the generated child packages.

The aim is simple: an unfamiliar human or agent should be able to understand where they are, what applies here, and where to go next — without depending on a lucky repository search or maintaining the same guidance in several static prompt bundles.

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
