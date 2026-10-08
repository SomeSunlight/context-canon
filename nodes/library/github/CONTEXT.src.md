# GitHub — Local Context Source
<!-- ctx:node id="ccf4d7ee-4db1-4110-9ddc-5d70c69cf2bc" name="GitHub" version="0.1.8-draft" -->

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

Concrete provider for projects that use ordinary GitHub infrastructure to implement the Development Workflow. The inherited workflow keeps the familiar Issue, branch, Pull Request, review, checks and merge lifecycle; this Node makes those terms mean the corresponding objects in the project's GitHub repository.

## Local Rules

<!-- contextcanon:format Local Rules
Format: ### Group, then - **Title:** Statement, then indented Why: Rationale. build adds a missing ctx:rule ID after the entry; preserve existing IDs.
Details: CONTEXT-format.md
-->

### Development infrastructure

- **Use GitHub development objects:** Manage workflow Issues, Pull Requests, reviews, checks/CI status, and merge state in the project's GitHub repository. Branches and commits remain ordinary Git objects; when a capable local harness is available, edit and test the local working tree directly rather than treating GitHub file APIs as a substitute filesystem.
  Why: The workflow should use standard GitHub semantics and tools while local code work stays local when possible.
  <!-- ctx:rule id="GH-001" -->
