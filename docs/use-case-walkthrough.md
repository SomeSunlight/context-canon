# Use-case walkthrough

This document stress-tests the ContextCanon design before compiler implementation is frozen.

The purpose is not to prove every detail. It is to find cases where a simple user action would become surprising, ambiguous, or disproportionately difficult.

## 1. Start a small project

A newly initialized node should require almost no framework knowledge.

Expected authoring flow:

1. `CONTEXT.src.md` is created with a short visible syntax guide.
2. A compiler-managed hidden template block shows copyable examples for a new rule, a source change, and a Topic.
3. The node composes the ContextCanon Standard plus any useful domain sources.
4. The human adds only the local delta.
5. The compiler creates the official package and harness adapters.

**Finding:** the common path must not require hand-written YAML, UUIDs, provenance, or package metadata.

## 2. Work on an ordinary task without wasting context

A developer asks an agent to change a small function unrelated to logging, releases, security architecture, or database design.

The agent should receive only:

- the compact official entry context,
- always-required rules,
- a concise Topic index.

It should **not** preload every linked architecture document merely because it exists.

**Finding:** the Official Context cannot mean "concatenate everything into `CONTEXT.md`." The Official Context is the complete compiled package; `CONTEXT.md` is its compact official entry view.

## 3. Work on a task that needs deeper context

A task changes logging.

The Logging Topic may say:

- **Required:** read the logging contract before editing logging code.
- **Optional:** consult troubleshooting notes and historical design discussion if useful.

The required material is loaded when the Topic applies. Optional links remain available for exploration.

A deeper document may itself begin with a short summary and link onward, exactly like a well-designed website.

**Finding:** Topic references need at least two load intentions: `required` and `optional`. Progressive disclosure may be recursive.

## 4. Compose several independent sources

A project composes:

- ContextCanon Standard,
- Python Development,
- Windows & PowerShell,
- Company Security,
- Personal Coding Style,
- a small local delta.

No source wins because of list order. Exact duplicate source versions are deduplicated. The same source required in incompatible versions is a deterministic dependency error.

Different source rules may still contradict each other semantically. The compiler preserves both; an LLM reviewer may flag the likely contradiction, but the durable resolution is an explicit local remove, override, or authorized exception.

**Finding:** composition remains tractable without a language-style method-resolution order.

## 5. Change an imported rule

A child wants to remove an inherited rule.

The user opens the published parent `CONTEXT.md`, sees the stable visible ID beside the rule, and references that ID in the child's `## Changes` section.

The title is copied for readability but is not identity.

If the parent later renames or rewrites the rule while preserving its identity, the child operation still targets the correct rule.

**Finding:** stable IDs must be visible in published official contexts, while local source IDs can remain compiler-managed HTML comments.

## 6. A source removes a rule that a child still changes

A child has an override for `PY-017`. A later accepted Python source version removes `PY-017`.

The compiler can prove that the child's operation now targets a missing element.

**Finding:** dangling remove/override/exception targets are deterministic diagnostics and must not be silently ignored. The update workflow should show them before acceptance.

## 7. Accept a source update

A reusable source publishes a new immutable package.

Children do not change live. A child remains pinned to its accepted source package until it explicitly reviews and accepts the new version/revision.

The update workflow can produce:

- exact deterministic structural/content changes,
- dangling-operation diagnostics,
- package identity changes,
- optional LLM interpretation of likely semantic impact and code consequences.

**Finding:** deterministic diff first, semantic review second.

## 8. Clone a child without source repositories

A child repository is cloned onto a machine that cannot reach its parent/source repositories.

The accepted source packages, normalized identities, and required materialized references are already available in the child's machine-managed package data.

The child remains understandable and reproducible.

**Finding:** published packages, not live repository traversal, are the inheritance/composition boundary.

## 9. Put several nodes in one Git repository

ContextCanon itself needs two different reusable contexts:

- **ContextCanon Standard**: the public baseline intended for managed client nodes.
- **ContextCanon Development**: the repository's own development context; it composes ContextCanon Standard and adds design/compiler rules.

The repository root is the Development node because that is what agents working on this repository need. The public Standard is a separate node under `contexts/standard/`.

**Finding:** node identity and lifecycle cannot be equated with Git repository boundaries. A repository may publish multiple independently addressable nodes.

## 10. Use different agent harnesses

Codex, goose, another agent, and a human work on the same repository.

They may enter through different adapter files, but all adapters point to the same official entry context and package meaning.

No authored project rule needs to know which harness is consuming it.

**Finding:** harness/model details stay at the adapter edge and must not leak into project code or canonical context semantics.

## 11. Edit `CONTEXT.src.md` without memorizing syntax

The source file contains a hidden compiler-maintained authoring template block. In raw Markdown it provides immediately copyable examples; rendered Markdown remains clean.

A default `compact` help mode should provide generic templates once. An optional future `expanded` mode may generate ready-to-edit change snippets for imported rules. A `none` mode may suppress help for experienced users.

Generating a full template for every imported rule by default would make large source files noisy and conflicts with ContextCanon's own progressive-disclosure goal.

**Finding:** authoring help is a presentation/tooling preference, not inherited project governance.

## 12. Grow beyond rules

Glossaries, patterns, examples, hints, practices, skills, and experience can later use the same package/composition/provenance model.

The important constraint is that these future element types do not force everything into the always-loaded entry context. They should participate in Topics and progressive disclosure.

## Conceptual issues to resolve before freezing compiler V1

The walkthrough found no reason to abandon the architecture, but it exposed several details that should be resolved before the deterministic compiler is hardened:

1. Define the exact boundary between the complete Official Context package and its compact `CONTEXT.md` entry view.
2. Freeze Topic syntax for `required` versus `optional` references and recursive loading.
3. Define source locators and immutable package identity for local paths, Git repositories, and releases.
4. Define stable ID generation, preservation, and duplicate detection.
5. Define deterministic diagnostics for dangling change operations after source updates.
6. Define how multiple nodes in one repository are addressed and published.
7. Decide where non-versioned authoring preferences such as template verbosity live.
8. Keep protected rules and authorized exceptions deterministic and explicit.

These are bounded design questions. None currently requires replacing the core composition model.