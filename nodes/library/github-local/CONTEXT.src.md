# GitHub Local — Local Context Source
<!-- ctx:node id="63b92022-db1a-4875-be99-017726cbfce7" name="GitHub Local" version="0.1.7-draft" -->

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

## Context Imports

<!-- contextcanon:format Context Imports
Format: - [Name](location) — `version` — `relationship=parent|reference`; optional indented Why:, then ctx:source metadata. Preserve exact pins; use source list/adopt/update for package identity.
Details: CONTEXT-format.md
-->

- [Development Workflow](../development-workflow/) — `0.3.7-draft` — `relationship=parent`
  <!-- ctx:source id="c4c94726-3cc7-4df6-b779-72bbf9c06f40" version="0.3.7-draft" -->

## Local Overview

<!-- contextcanon:format Local Overview
Format: Ordinary Markdown orientation, local to this Node. Any existing placement identity follows its paragraph/item; do not change it.
Details: CONTEXT-format.md
-->

Concrete provider for restricted-network or private development that needs the familiar GitHub workflow without depending on github.com. Normal agents keep using Issue, branch, Pull Request, review, checks and merge concepts; the configured `github.local` runtime supplies the local GitHub-compatible operations.

## Local Rules

<!-- contextcanon:format Local Rules
Format: ### Group, then - **Title:** Statement, then indented Why: Rationale. build adds a missing ctx:rule ID after the entry; preserve existing IDs.
Details: CONTEXT-format.md
-->

### Development infrastructure

- **Use GitHub Local development objects:** Use the configured `github.local` provider for workflow Issue, Pull Request, review, checks and merge operations; use the local Git repository for branches, commits, diffs and working-tree changes.
  Why: Humans and LLMs should work with familiar GitHub semantics without carrying a provider-abstraction translation table in normal task context.
  <!-- ctx:rule id="GHL-001" -->

- **Keep Issues visible project documentation:** Persist local Issues as ordinary visible project documents under `issues/`; do not hide their canonical content in ContextCanon machine state or an opaque runtime database.
  Why: The reasons, decisions and history behind changes are durable project knowledge and must remain directly inspectable even when `github.local` is not running.
  <!-- ctx:rule id="GHL-002" -->

- **Do not silently switch providers:** If the configured `github.local` runtime is unavailable or lacks a required operation, fail clearly rather than silently creating equivalent objects in github.com, Jira, Bitbucket, or another external system.
  Why: Restricted/private projects must not leak development state or acquire an accidental second workflow system.
  <!-- ctx:rule id="GHL-003" -->

## Local Topics

<!-- contextcanon:format Local Topics
Format: ### Title, condition text, Required: and/or Optional:, then - Resource: `path` or - Context Node: `node-path`. Resource may have indented Why:. build adds missing Topic/Resource IDs after their entries; preserve existing IDs.
Details: CONTEXT-format.md
-->

### Configure or operate GitHub Local

When installing, configuring, integrating, troubleshooting, or extending the local GitHub-compatible provider or its MCP bridge:

Required:
- Resource: `docs/provider.md`
  <!-- ctx:resource id="RESOURCE-CEFEEDC80FA7" -->
<!-- ctx:topic id="GHL-TOPIC-PROVIDER" -->
