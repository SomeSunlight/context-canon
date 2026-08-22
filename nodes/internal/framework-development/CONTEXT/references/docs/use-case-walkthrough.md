# Use-case walkthrough

This document stress-tests ContextCanon as the implementation grows. The initial usefulness question has now been answered by a real external project; walkthroughs remain useful for compiler semantics and regression reasoning rather than as a gate before implementation.

## 1. Enter a repository through an almost-empty Gateway

An agent opens the ContextCanon repository. The root Node has no Sources, no Rules, one Topic, and no `CONTEXT/` directory.

For an ordinary orientation task, nothing deeper is loaded. When the task concerns ContextCanon's specification, documentation, Nodes, compiler, examples, or tooling, the Topic requires the Framework Development Node.

**Finding:** a useful Context Node can be extremely small. The compiler validates the typed Context Node target deterministically.

## 2. Start a small project

A newly initialized Node should require almost no framework knowledge. It can compose useful Sources, add only a local delta, and generate only the outputs it actually needs.

**Finding:** the common path must not require hand-written YAML, provenance, package metadata, or empty package directories. Unrelated projects do not need to inherit ContextCanon Foundation merely because they use ContextCanon.

## 3. Recognize a Node in the filesystem

A contributor browses an unfamiliar repository containing several ContextCanon Nodes.

Each actual Node has its own node-root directory containing `CONTEXT.src.md`, generated `CONTEXT.md`, optional `CONTEXT/`, and `.context/`. Directories that only group Nodes do not become Nodes merely because they sit under `nodes/`.

**Finding:** Node roots are discovered deterministically from `CONTEXT.src.md` while path remains separate from stable Node identity.

## 4. Work on an ordinary task without wasting context

A developer asks an agent to change a small function unrelated to logging, releases, security architecture, or database design. The agent should receive the compact entry and Topic map, not every linked document.

**Finding:** completeness belongs to the package; prompt size belongs to the current task.

The external `teams-chat-exporter` experiment confirmed this behavior with GitHub Copilot.

## 5. Work on a task that needs deeper context

A Teams selector-maintenance Topic required a dedicated selector guide and the current dated selector configuration while leaving broader contribution material optional.

The agent used those resources to distinguish a Teams DOM/configuration change from a genuine Python behavior change.

**Finding:** Required/Optional progressive disclosure works in a real harness and improves task framing.

## 6. Keep source documents natural while publishing a self-contained package

A project may edit `docs/architecture.md` in its natural location while the compiler materializes it into `CONTEXT/references/docs/architecture.md` for publication.

**Finding:** local Resource targets are materialized and generated drift is detected. If materialized Markdown links to another local file, that file is recursively included as part of the materialization closure.

## 7. Compose several independent Sources

A project may compose ContextCanon Foundation, Python Development, Company Security, Personal Coding Style and a small local delta. Source order is not precedence. Structural conflicts are deterministic errors; natural-language conflicts may need semantic review and explicit local resolution.

**Finding:** the compiler implements local Source identity/version checks, duplicate direct Source rejection, cycle detection, transitive Rule composition, and duplicate visible Rule-ID diagnostics. Source order is canonicalized in normalized semantics so declaration order cannot become accidental meaning. Broader external multi-Source use remains future hardening, not a conceptual blocker.

## 8. Change an imported Rule

A child references the stable visible ID published by its ancestor plus the ancestor Node's stable ID. Renaming or rewriting the Rule without changing identity does not retarget the operation.

Compiler 0.2 introduced:

- `Remove` — delete an inherited ordinary Rule from the child's effective Rule set;
- `Override` — preserve inherited identity while replacing the effective statement and recording override provenance.

**Finding:** explicit local changes make Source composition useful beyond purely additive inheritance.

## 9. Carry changes through another generation

Consider:

```text
Foundation ──> Team Standard ──> Project
```

Team Standard overrides one Foundation Rule and removes another. Project should inherit the overridden statement with Foundation identity plus Team Standard provenance, while the removed Rule should remain absent.

**Finding:** regression tests cover this transitive behavior. During implementation they exposed and fixed a renderer defect where grandparent Rules could be semantically inherited but omitted from a deeper `CONTEXT.md`.

## 10. A Source removes a Rule that a child still changes

A child Change targets `<origin-node-id>#<rule-id>`. If the effective inherited package no longer contains that identity, compilation must fail.

**Finding:** dangling Change diagnostics are implemented for current local Sources. This becomes especially important when external Source update acceptance arrives.

## 11. Compare two compiled Context versions

A project needs to know exactly what changed before asking either a human or an LLM to reason about impact.

Compiler 0.3 compares two snapshots of the same stable Node with:

```text
contextcanon diff <before-node-root> <after-node-root>
contextcanon diff <before-node-root> <after-node-root> --json
```

The diff uses stable identities and compiled state rather than Markdown line positions. It can report Node metadata, Source package state, local Changes, effective Rules, Topics, and materialized Resource content.

An inherited Rule that changes from active to removed is one state transition on the same `<origin-node-id>#<rule-id>`. An Override keeps the original Rule identity while exposing its effective statement and provenance changes. Transitive Overrides therefore remain traceable to the Foundation Rule rather than becoming unrelated child Rules.

**Finding:** Context change is now a first-class deterministic artifact suitable as exact input to later Source-update review and code-impact analysis.

## 12. Reorder things that have no semantic order

Two authors reorder independent Sources or Topic targets without changing their meaning.

The human package may change presentation order, but Source order must not become precedence and Topic-target ordering has no current semantic meaning.

**Finding:** compiler 0.3 canonicalizes semantically unordered collections for `normalized_digest` and diff comparison. Package bytes may still differ when presentation changes, which is reported separately rather than mislabeled as a semantic change.

## 13. Accept a Source update

Consumers should remain pinned until they explicitly review and accept a newer immutable Source package. Deterministic diff comes first; optional semantic interpretation comes second.

**Finding:** the compiler now records Source version/package digest and provides the deterministic Context diff. Immutable external package pinning, candidate discovery, and acceptance are the next central layer.

## 14. Clone a child without Source repositories

Accepted Source packages and required materialized resources must eventually be available locally enough for the child to remain understandable and reproducible.

**Finding:** local-path Sources are sufficient for current dogfood, but broad multi-repository adoption requires immutable external package transport/cache semantics.

## 15. Put several Nodes in one Git repository

ContextCanon itself uses Gateway, Foundation, and Framework Development in one repository. Intermediate category directories are not Nodes.

**Finding:** the compiler discovers all three and can build/check them in one command.

## 16. Move and rename a Node without changing identity

Framework Development previously moved and retained its stable Node ID.

**Finding:** stable Node ID is identity; path is location.

## 17. Contribute a reusable ContextCanon Node

A reusable Node that ships with ContextCanon belongs under `nodes/library/<node-name>/` and composes Foundation directly or transitively.

**Finding:** repository placement is governance, not a generic ContextCanon filesystem requirement.

## 18. Use different agent harnesses

Codex, GitHub Copilot, goose, another agent, and a human may enter through different harness mechanics, but each enters the same canonical Context Node.

For GitHub Copilot in the tested JetBrains setup, ContextCanon relies on generated `AGENTS.md` with the harness configured to attach it to chat requests. goose continues to use `.goosehints`.

**Finding:** harness semantics belong at the edge; canonical context remains model/harness-neutral.

## 19. Use smaller and local models

The external experiment also produced a strong answer from a low-cost model once the task was well framed by project context.

**Finding:** ContextCanon is not only about reducing paid prompt tokens. Better context management can make smaller and local models more useful by spending their capability on the actual task instead of rediscovering project assumptions.

## 20. Standardize orientation across projects

A human or agent moving between ContextCanon projects should know where to look for:

- what applies now (`CONTEXT.md`),
- what is special here (`CONTEXT.src.md`),
- reusable foundations (Sources),
- deeper task-specific knowledge (Topics),
- current situation (`STATE.md`),
- next direction (`PLAN.md`).

**Finding:** standardizing the shape of project context is itself useful architectural infrastructure, independently of token savings.

## 21. Grow from Topics into broader context integration

The same mechanism can later integrate glossaries, patterns, code examples, structured data, PDFs, diagrams, skills, test fixtures, and operational experience.

**Finding:** new context types should reuse the same identity, package, provenance, and progressive-disclosure mechanisms rather than becoming parallel context systems.

## Questions deliberately left for later compiler layers

1. Immutable external Git/package Source locators, caching, candidate discovery, and explicit update acceptance.
2. Protected Rules and authorized exceptions.
3. Topic composition/materialization across Source package boundaries.
4. Resource collisions across composed packages.
5. Nested Git repository and more complex Node-boundary behavior.
6. Richer authoring/scaffolding and safe compiler-owned generated-file manifests.

These are ordered implementation work, not unresolved proof-of-concept questions.
