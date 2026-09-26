# GitHub Local — Local Context Source
<!-- ctx:node id="63b92022-db1a-4875-be99-017726cbfce7" name="GitHub Local" version="0.1.0-draft" -->

## Sources

- [Development Workflow](../development-workflow/) — `0.3.0-draft`
  <!-- ctx:source id="c4c94726-3cc7-4df6-b779-72bbf9c06f40" version="0.3.0-draft" -->

## Local Overview

Concrete provider for restricted-network or private development that needs the familiar GitHub workflow without depending on github.com. Normal agents keep using Issue, branch, Pull Request, review, checks and merge concepts; the configured `github.local` runtime supplies the local GitHub-compatible operations.

## Local Rules

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

### Configure or operate GitHub Local

When installing, configuring, integrating, troubleshooting, or extending the local GitHub-compatible provider or its MCP bridge:

Required:
- Resource: `docs/provider.md`
<!-- ctx:topic id="GHL-TOPIC-PROVIDER" -->
