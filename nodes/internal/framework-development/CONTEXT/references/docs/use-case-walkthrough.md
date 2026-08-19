# Use-case walkthrough

This document stress-tests ContextCanon before the compiler implementation is frozen. The purpose is to find cases where a simple user action would become surprising, ambiguous, or disproportionately difficult.

## 1. Enter a repository through an almost-empty Gateway

An agent opens the ContextCanon repository. The root Node has no Sources, no Rules, one Topic, and no `CONTEXT/` directory.

For an ordinary orientation task, nothing deeper is loaded. When the task concerns ContextCanon's specification, documentation, Nodes, compiler, examples, or tooling, the Topic requires `nodes/internal/framework-development/CONTEXT.md`.

**Finding:** a useful Context Node can be extremely small. This needs no special bootstrap mode; normal Topic semantics are sufficient.

**Open detail:** a Topic target may point to another Context Node rather than a package resource. V1 should represent that target explicitly enough for validation, diagnostics, and future package/location handling.

## 2. Start a small project

A newly initialized Node should require almost no framework knowledge. It can compose ContextCanon Foundation plus useful domain Sources, add only a local delta, and generate only the outputs it actually needs.

**Finding:** the common path must not require hand-written YAML, UUIDs, provenance, package metadata, or empty package directories.

## 3. Recognize a Node in the filesystem

A contributor browses an unfamiliar repository containing several ContextCanon Nodes.

Each actual Node has its own node-root directory containing `CONTEXT.src.md`, generated `CONTEXT.md`, optional `CONTEXT/`, and `.context/`. Directories that only group Nodes do not become Nodes merely because they sit under `nodes/`.

**Finding:** the physical organization must be obvious before a reader understands composition. Node-root discovery and nested-node boundaries must therefore become deterministic V1 behavior.

## 4. Work on an ordinary task without wasting context

A developer asks an agent to change a small function unrelated to logging, releases, security architecture, or database design. The agent should receive the compact entry and Topic map, not every linked document.

**Finding:** completeness belongs to the package; prompt size belongs to the current task.

## 5. Work on a task that needs deeper context

A Logging Topic can require the logging contract and optionally expose troubleshooting history. A deeper document may itself summarize first and link onward.

**Finding:** Topic targets need at least Required and Optional load intentions. Progressive disclosure may be recursive.

## 6. Keep source documents natural while publishing a self-contained package

A project may edit `docs/architecture.md` in its natural location while the compiler materializes it into `CONTEXT/references/docs/architecture.md` for publication.

**Finding:** authors should not reorganize repositories for the framework, while consumers should not depend on the author's source layout.

## 7. Compose several independent Sources

A project may compose ContextCanon Foundation, Python Development, Company Security, Personal Coding Style and a small local delta. Source order is not precedence. Structural conflicts are deterministic errors; natural-language conflicts may need semantic review and explicit local resolution.

**Finding:** composition remains tractable without a language-style method-resolution order.

## 8. Change an imported Rule

A child references the stable visible ID published by its parent. Renaming or rewriting the Rule without changing identity does not break the operation.

**Finding:** stable IDs must be visible in published official contexts, while local source IDs can remain compiler-managed comments.

## 9. A Source removes a Rule that a child still changes

The compiler can prove that an override now targets a missing element.

**Finding:** dangling changes are deterministic diagnostics and must not be silently ignored.

## 10. Accept a Source update

Consumers remain pinned until they explicitly review and accept a newer immutable Source package. Deterministic diff comes first; optional semantic interpretation comes second.

## 11. Clone a child without Source repositories

Accepted Source packages and required materialized resources must be available locally enough for the child to remain understandable and reproducible.

**Finding:** published packages, not live repository traversal, are the composition boundary.

## 12. Put several Nodes in one Git repository

ContextCanon itself needs three contexts with three jobs:

```text
Gateway ──Topic──> Framework Development
                         ▲
                         │ Source
                      Foundation
```

Their physical organization is deliberately explicit:

```text
repository root                    Gateway
nodes/library/foundation/          Foundation
nodes/internal/framework-development/  Framework Development
```

The intermediate `nodes/library/` and `nodes/internal/` directories are categories, not Nodes.

**Finding:** Node identity is not repository identity, and a clean filesystem taxonomy can aid humans without defining composition semantics.

## 13. Move and rename a Node without changing identity

During this POC, the framework-development Node moved from `nodes/development/` to `nodes/internal/framework-development/` and received a more descriptive name. Its stable Node ID remains unchanged.

Local filesystem locators and Topic targets must be updated, but the Node does not become a different logical entity merely because its path or display name changed.

**Finding:** a Node needs a physical directory, but the directory path must never be its identity.

## 14. Contribute a reusable ContextCanon Node

A contributor wants to add a reusable Node that should ship with ContextCanon.

It belongs in its own directory under:

```text
nodes/library/<node-name>/
```

Every Node in this library must compose ContextCanon Foundation directly or transitively. A ContextCanon-specific implementation context instead belongs under `nodes/internal/`. An example or experiment should not enter the library merely because it uses ContextCanon.

**Finding:** repository categories must make contribution placement obvious. `library/` and `internal/` are repository conventions, not framework-mandated paths.

## 15. Use different agent harnesses

Codex, goose, another agent, and a human may enter through different adapters, but the adapters first enter the applicable Context Node. In this repository they enter Gateway rather than hard-coding Framework Development.

**Finding:** harness details stay at the adapter edge while ContextCanon controls progressive disclosure.

## 16. Edit `CONTEXT.src.md` without memorizing syntax

Compiler-managed hidden template blocks can provide copyable examples in raw Markdown while rendered Markdown remains clean. Help verbosity is a tooling preference rather than inherited governance.

## 17. Grow from Topics into broader context integration

The same mechanism can later integrate glossaries, patterns, code examples, structured data, PDFs, diagrams, skills, test fixtures, and operational experience.

**Finding:** new context types should reuse package materialization, composition, provenance, and progressive disclosure rather than creating separate ad-hoc systems.

## Conceptual issues to resolve before freezing compiler V1

1. Freeze Topic syntax for Required versus Optional targets and recursive loading.
2. Define typed Topic targets, including links to another Context Node.
3. Define deterministic node-root discovery and nested-node boundary rules.
4. Define Source locators and immutable package identity, including moves without identity changes.
5. Define stable ID generation, preservation, and duplicate detection.
6. Define deterministic diagnostics for dangling changes.
7. Define how multiple Nodes in one repository are addressed and published.
8. Define exact source-to-`CONTEXT/` resource mapping and collision handling.
9. Decide where non-versioned authoring preferences such as template verbosity live.
10. Keep protected Rules and authorized exceptions deterministic and explicit.

These are bounded design questions. None currently requires replacing the core composition model.
