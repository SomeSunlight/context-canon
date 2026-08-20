# Use-case walkthrough

This document stress-tests ContextCanon as the implementation grows. Mental walkthroughs are now used selectively when an executable slice exposes a concrete ambiguity; they are no longer a gate before building the compiler.

## 1. Enter a repository through an almost-empty Gateway

An agent opens the ContextCanon repository. The root Node has no Sources, no Rules, one Topic, and no `CONTEXT/` directory.

For an ordinary orientation task, nothing deeper is loaded. When the task concerns ContextCanon's specification, documentation, Nodes, compiler, examples, or tooling, the Topic requires the Framework Development Node.

**Finding:** a useful Context Node can be extremely small. The walking-skeleton compiler now validates the typed Context Node target deterministically.

## 2. Start a small project

A newly initialized Node should require almost no framework knowledge. It can compose ContextCanon Foundation plus useful domain Sources, add only a local delta, and generate only the outputs it actually needs.

**Finding:** the common path must not require hand-written YAML, provenance, package metadata, or empty package directories.

## 3. Recognize a Node in the filesystem

A contributor browses an unfamiliar repository containing several ContextCanon Nodes.

Each actual Node has its own node-root directory containing `CONTEXT.src.md`, generated `CONTEXT.md`, optional `CONTEXT/`, and `.context/`. Directories that only group Nodes do not become Nodes merely because they sit under `nodes/`.

**Finding:** Walking Skeleton 1 discovers Nodes deterministically from `CONTEXT.src.md` while keeping path separate from stable Node identity.

## 4. Work on an ordinary task without wasting context

A developer asks an agent to change a small function unrelated to logging, releases, security architecture, or database design. The agent should receive the compact entry and Topic map, not every linked document.

**Finding:** completeness belongs to the package; prompt size belongs to the current task.

## 5. Work on a task that needs deeper context

A Logging Topic can require the logging contract and optionally expose troubleshooting history. A deeper document may itself summarize first and link onward.

**Finding:** Required and Optional are now explicit parser syntax.

## 6. Keep source documents natural while publishing a self-contained package

A project may edit `docs/architecture.md` in its natural location while the compiler materializes it into `CONTEXT/references/docs/architecture.md` for publication.

**Finding:** Walking Skeleton 1 implements this for local Resource targets and detects generated drift. If a materialized Markdown resource links to another local file, that file is recursively included as part of the materialization closure.

## 7. Compose several independent Sources

A project may compose ContextCanon Foundation, Python Development, Company Security, Personal Coding Style and a small local delta. Source order is not precedence. Structural conflicts are deterministic errors; natural-language conflicts may need semantic review and explicit local resolution.

**Finding:** the first compiler implements local Source identity/version checks, cycle detection, Rule composition, and duplicate visible Rule-ID diagnostics. Multiple real orthogonal Sources remain an external-project test.

## 8. Change an imported Rule

A child references the stable visible ID published by its parent. Renaming or rewriting the Rule without changing identity does not break the operation.

**Finding:** stable IDs are parsed and published now; Remove/Override operations remain deliberately unimplemented until the first real need.

## 9. A Source removes a Rule that a child still changes

The compiler can eventually prove that an override targets a missing element.

**Finding:** dangling change diagnostics remain a hardening step after change operations exist.

## 10. Accept a Source update

Consumers should remain pinned until they explicitly review and accept a newer immutable Source package. Deterministic diff comes first; optional semantic interpretation comes second.

**Finding:** the walking skeleton records Source package digests, but external package pinning and acceptance workflow come later.

## 11. Clone a child without Source repositories

Accepted Source packages and required materialized resources must eventually be available locally enough for the child to remain understandable and reproducible.

**Finding:** local-path Sources are sufficient for the walking skeleton; standalone external package transport remains unresolved until exercised.

## 12. Put several Nodes in one Git repository

ContextCanon itself uses Gateway, Foundation, and Framework Development in one repository. Intermediate category directories are not Nodes.

**Finding:** the executable compiler now discovers all three and can build/check them in one command.

## 13. Move and rename a Node without changing identity

Framework Development previously moved and retained its stable Node ID.

**Finding:** the compiler treats stable Node ID as identity and validates Source references against it rather than equating identity with path.

## 14. Contribute a reusable ContextCanon Node

A reusable Node that ships with ContextCanon belongs under `nodes/library/<node-name>/` and composes Foundation directly or transitively.

**Finding:** repository placement is governance, not a generic ContextCanon filesystem requirement.

## 15. Use different agent harnesses

Codex, goose, another agent, and a human may enter through different adapters, but the adapters first enter the applicable Context Node.

**Finding:** Walking Skeleton 1 generates configured thin adapters; harness semantics remain outside canonical project context.

## 16. Edit `CONTEXT.src.md` without memorizing syntax

Compiler-managed hidden template blocks can provide copyable examples in raw Markdown while rendered Markdown remains clean.

**Finding:** automatic authoring scaffolding remains later tooling; the parser now has a concrete minimal grammar to scaffold.

## 17. Grow from Topics into broader context integration

The same mechanism can later integrate glossaries, patterns, code examples, structured data, PDFs, diagrams, skills, test fixtures, and operational experience.

**Finding:** new context types should arrive through real end-to-end needs, not speculative grammar expansion.

## Questions deliberately left for observed failures

1. Topic inheritance and materialization across Source package boundaries.
2. External Git/package Source locators and immutable acceptance workflow.
3. Remove, Override, protected Rules, and authorized exceptions.
4. Nested Git repository and more complex Node-boundary behavior.
5. Resource collisions across composed packages.
6. Non-versioned authoring preferences and richer scaffolding.

These are no longer blockers for the walking skeleton. Each becomes a deterministic regression case when a real project exposes the need.
