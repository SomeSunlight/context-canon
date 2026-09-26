# GitHub — Local Context Source
<!-- ctx:node id="ccf4d7ee-4db1-4110-9ddc-5d70c69cf2bc" name="GitHub" version="0.1.0-draft" -->

## Sources

- [Development Workflow](../development-workflow/) — `0.3.0-draft`
  <!-- ctx:source id="c4c94726-3cc7-4df6-b779-72bbf9c06f40" version="0.3.0-draft" -->

## Local Overview

Concrete provider for projects that use ordinary GitHub infrastructure to implement the Development Workflow. The inherited workflow keeps the familiar Issue, branch, Pull Request, review, checks and merge lifecycle; this Node makes those terms mean the corresponding objects in the project's GitHub repository.

## Local Rules

### Development infrastructure

- **Use GitHub development objects:** Manage workflow Issues, Pull Requests, reviews, checks/CI status, and merge state in the project's GitHub repository. Branches and commits remain ordinary Git objects; when a capable local harness is available, edit and test the local working tree directly rather than treating GitHub file APIs as a substitute filesystem.
  Why: The workflow should use standard GitHub semantics and tools while local code work stays local when possible.
  <!-- ctx:rule id="GH-001" -->
