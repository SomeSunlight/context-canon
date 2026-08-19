# Use-case walkthrough

This document stress-tests ContextCanon before the compiler implementation is frozen. The purpose is to find cases where a simple user action would become surprising, ambiguous, or disproportionately difficult.

## 1. Enter a repository through an almost-empty Gateway

An agent opens the ContextCanon repository.

The root Context Node contains:

- no Sources,
- no Rules,
- one Topic,
- no materialized `CONTEXT/` directory.

For an ordinary orientation task, nothing deeper is loaded. When the task concerns ContextCanon's specification, documentation, nodes, compiler, examples, or tooling, the Topic requires `nodes/development/CONTEXT.md`.

**Finding:** a useful Context Node can be extremely small. This needs no special bootstrap mode; the normal Topic mechanism is sufficient.

**Open detail:** a Topic target may point to another Context Node rather than a package resource. V1 should represent that target explicitly enough for validation, diagnostics, and future package/location handling.

## 2. Start a small project

A newly initialized node should require almost no framework knowledge.

Expected authoring flow:

1. `CONTEXT.src.md` is created with a short visible syntax guide.
2. A compiler-managed hidden template block shows copyable examples for a new rule, a source change, and a Topic.
3. The node composes ContextCanon Foundation plus any useful domain sources.
4. The human adds only the local delta.
5. The compiler creates `CONTEXT.md`, optional `CONTEXT/`, machine state, and harness adapters.

**Finding:** the common path must not require hand-written YAML, UUIDs, provenance, package metadata, or empty package directories.

## 3. Work on an ordinary task without wasting context

A developer asks an agent to change a small function unrelated to logging, releases, security architecture, or database design.

The agent should receive only:

- the compact `CONTEXT.md` entry,
- always-required rules,
- a concise Topic index.

It should not preload every linked architecture document merely because it exists.

**Finding:** completeness belongs to the package; prompt size belongs to the current task.

## 4. Work on a task that needs deeper context

A task changes logging.

The Logging Topic may say:

- **Required:** read the logging contract before editing logging code.
- **Optional:** consult troubleshooting notes and historical design discussion if useful.

The required material is loaded when the Topic applies. Optional links remain available for exploration.

A deeper document may itself begin with a short summary and link onward, like a well-designed website.

**Finding:** Topic references need at least two load intentions: `required` and `optional`. Progressive disclosure may be recursive.

## 5. Keep source documents natural while publishing a self-contained package

A project maintains architecture documentation at `docs/architecture.md` because that is where developers expect to edit it.

`CONTEXT.src.md` references that source path. During compilation, ContextCanon materializes the file into the published package:

```text
source:     docs/architecture.md
published:  CONTEXT/references/docs/architecture.md
```

Generated `CONTEXT.md` points to the package-local copy.

**Finding:** authors should not reorganize repositories for the framework, while consumers should not depend on the author's repository layout.

## 6. Compose several independent sources

A project composes:

- ContextCanon Foundation,
- Python Development,
- Windows & PowerShell,
- Company Security,
- Personal Coding Style,
- a small local delta.

No source wins because of list order. Exact duplicate source versions are deduplicated. The same source required in incompatible versions is a deterministic dependency error.

Different source rules may still contradict each other semantically. The compiler preserves both; an LLM reviewer may flag the likely contradiction, but the durable resolution is an explicit local remove, override, or authorized exception.

**Finding:** composition remains tractable without a language-style method-resolution order.

## 7. Change an imported rule

A child wants to remove an inherited rule.

The user opens the published parent `CONTEXT.md`, sees the stable visible ID beside the rule, and references that ID in the child's `## Changes` section.

The title is copied for readability but is not identity.

If the parent later renames or rewrites the rule while preserving its identity, the child operation still targets the correct rule.

**Finding:** stable IDs must be visible in published official contexts, while local source IDs can remain compiler-managed HTML comments.

## 8. A source removes a rule that a child still changes

A child has an override for `PY-017`. A later accepted Python source version removes `PY-017`.

The compiler can prove that the child's operation now targets a missing element.

**Finding:** dangling remove/override/exception targets are deterministic diagnostics and must not be silently ignored. The update workflow should show them before acceptance.

## 9. Accept a source update

A reusable source publishes a new immutable package.

Consumers do not change live. A child remains pinned to its accepted source package until it explicitly reviews and accepts the new version/revision.

The update workflow can produce:

- exact deterministic structural/content changes,
- dangling-operation diagnostics,
- package identity changes,
- optional LLM interpretation of likely semantic impact and code consequences.

**Finding:** deterministic diff first, semantic review second.

## 10. Clone a child without source repositories

A child repository is cloned onto a machine that cannot reach its parent/source repositories.

The accepted source packages, normalized identities, and required materialized references are already available locally.

The child remains understandable and reproducible.

**Finding:** published packages, not live repository traversal, are the composition boundary.

## 11. Put several nodes in one Git repository

ContextCanon itself needs three contexts with three jobs:

- **ContextCanon Gateway**: the minimal repository entry; routes development tasks onward.
- **ContextCanon Foundation**: the reusable baseline intended for other managed nodes.
- **ContextCanon Development**: composes Foundation and adds design/compiler rules.

```text
Gateway ──Topic──> Development
                     ▲
                     │ Source
                  Foundation
```

The structural contract implemented by all three nodes is defined by the ContextCanon schema/specification. A separate interface node would be justified only if it carried reusable context content, not merely structure.

**Finding:** node identity and lifecycle cannot be equated with Git repository boundaries. Topic navigation and Source composition are distinct relationships.

## 12. Use different agent harnesses

Codex, goose, another agent, and a human work on the same repository.

They may enter through different adapter files, but the adapters first enter the applicable Context Node. In this repository that is the minimal Gateway; the adapters do not hard-code Development.

**Finding:** harness/model details stay at the adapter edge, while ContextCanon controls progressive disclosure.

## 13. Edit `CONTEXT.src.md` without memorizing syntax

The source file contains a hidden compiler-maintained authoring template block. In raw Markdown it provides immediately copyable examples; rendered Markdown remains clean.

A default `compact` help mode should provide generic templates once. An optional future `expanded` mode may generate ready-to-edit change snippets for imported rules. A `none` mode may suppress help for experienced users.

Generating a full template for every imported rule by default would make large source files noisy and conflicts with ContextCanon's own progressive-disclosure goal.

**Finding:** authoring help is a presentation/tooling preference, not inherited project governance.

## 14. Grow from Topics into broader context integration

A Topic initially links a task to Markdown documentation. The same mechanism can later integrate other context resources when they become relevant:

- glossaries and terminology,
- patterns and example code,
- CSV files, schemas, and tables,
- PDFs, images, and diagrams,
- skills and workflows,
- test fixtures,
- operational experience and known pitfalls.

**Finding:** future element types should reuse package materialization, composition, provenance, and progressive disclosure instead of creating separate ad-hoc context systems.

## Conceptual issues to resolve before freezing compiler V1

The walkthrough found no reason to abandon the architecture, but several implementation contracts still need a vertical POC:

1. Freeze Topic syntax for `required` versus `optional` targets and recursive loading.
2. Define typed Topic targets, including links to another Context Node.
3. Define source locators and immutable package identity for local paths, Git repositories, and releases.
4. Define stable ID generation, preservation, and duplicate detection.
5. Define deterministic diagnostics for dangling change operations after source updates.
6. Define how multiple nodes in one repository are addressed and published.
7. Define exact source-to-`CONTEXT/` resource mapping and collision handling.
8. Decide where non-versioned authoring preferences such as template verbosity live.
9. Keep protected rules and authorized exceptions deterministic and explicit.

These are bounded design questions. None currently requires replacing the core composition model.