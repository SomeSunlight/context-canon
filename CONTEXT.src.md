# ContextCanon Gateway — Local Context Source
<!-- ctx:node id="a2f4c7e1-9b63-4c48-a19f-3de0c5b28f11" name="ContextCanon Gateway" version="0.3.24-draft" adapters="agents,goose" -->

<!-- contextcanon:format Node
Format: Node metadata follows the # title: ctx:node id="..." name="..." version="...". Preserve existing identity.
Details: CONTEXT-format.md
-->

<!-- contextcanon:source-help:intro:start -->
Edit this local Context source; ContextCanon generates CONTEXT.md from it.
Some sections use a strict syntax. The comments below show the expected format.
New Rules, Topics and Resources receive IDs automatically during build; preserve existing IDs.
See [the source format guide](CONTEXT-format.md) for examples and editing instructions.
<!-- contextcanon:source-help:intro:end -->


> [!IMPORTANT]
> **Edit this file to change the repository Gateway context.**
> `CONTEXT.md` and optional `CONTEXT/` resources are generated from this source.
>
> This Node is intentionally small: it has no Sources and no Rules. Its job is to provide enough orientation to understand ContextCanon and route a few top-level tasks to the deeper context required for that task.

## Context Imports

<!-- contextcanon:format Context Imports
Format: - [Name](location) — `version` — `relationship=parent|reference`; optional indented Why:, then ctx:source metadata. Preserve exact pins; use source list/adopt/update for package identity.
Details: CONTEXT-format.md
-->

## Local Overview

<!-- contextcanon:format Local Overview
Format: Ordinary Markdown orientation, local to this Node. Any existing placement identity follows its paragraph/item; do not change it.
Details: CONTEXT-format.md
-->

Most AI projects eventually build a **static context bundle** by hand or with an LLM: a prompt, instruction file, or curated summary that tries to contain everything the model should know. It works until something important is missing; then the harness searches other repository files opportunistically, and whether it finds the right detail becomes less predictable. As the project changes, copied context also drifts and every duplicate becomes another place to review and repair.

ContextCanon keeps the always-needed overview small, puts deeper detail behind explicit Topics, and makes reusable context a versioned Source instead of another copy. Humans and agents get the same landing points, while detailed knowledge can live close to the narrow context where it belongs without bloating every higher-level overview. Builds render each Node's accepted effective Context deterministically. Dependent Child Nodes keep their last accepted Parent snapshot until a newer one is explicitly reviewed through propagation.

The aim is simple: an unfamiliar human or agent should be able to understand where they are, what applies here, and where to go next — without depending on a lucky repository search or maintaining the same guidance in several static prompt bundles.

## Local Topics

<!-- contextcanon:format Local Topics
Format: ### Title, condition text, Required: and/or Optional:, then - Resource: `path` or - Context Node: `node-path`. Resource may have indented Why:. build adds missing Topic/Resource IDs after their entries; preserve existing IDs.
Details: CONTEXT-format.md
-->

### Onboard an existing project

When adopting ContextCanon in an existing repository, preparing onboarding evidence, generating or running the onboarding instruction, validating an onboarding proposal, or deciding how to start using ContextCanon on an existing project:

Required:
- Resource: `docs/onboarding.md`
  <!-- ctx:resource id="RESOURCE-99512F179D85" -->
- Resource: `docs/onboarding-cli.md`
  <!-- ctx:resource id="RESOURCE-5F43AABB6A6C" -->
<!-- ctx:topic id="CCG-TOPIC-ONBOARDING" -->

### Use and maintain ContextCanon

When inspecting, updating, propagating, building, checking, or learning the normal CLI workflow in an already-onboarded ContextCanon project:

Required:
- Resource: `docs/maintenance.md`
  <!-- ctx:resource id="RESOURCE-4C412020705C" -->
- Resource: `docs/cli.md`
  <!-- ctx:resource id="RESOURCE-FF07DC187B0F" -->
- Resource: `docs/node-versions.md`
  <!-- ctx:resource id="RESOURCE-NODE-VERSIONS" -->
<!-- ctx:topic id="CCG-TOPIC-MAINTENANCE" -->

### ContextCanon framework development

When changing ContextCanon's specification, documentation, Context Nodes, compiler, examples, harness integration, or project tooling:

Required:
- Context Node: `nodes/internal/framework-development`
<!-- ctx:topic id="CCG-TOPIC-DEVELOPMENT" -->
