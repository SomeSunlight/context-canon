# Use-case walkthrough

This document stress-tests ContextCanon as the implementation grows. The initial usefulness question has already been answered by a real external project; walkthroughs now capture compiler findings and define the next realistic validation cases.

## 1. Enter a repository through an almost-empty Gateway

An agent opens the ContextCanon repository. The root Node has no Sources, no Rules, one Topic, and no `CONTEXT/` directory. Framework-development work follows that Topic to the deeper Development Node.

**Finding:** a useful Context Node can be extremely small. Progressive disclosure is not an optimization added after the model; it is part of the basic shape.

## 2. Start a small project

A small Node can compose useful Sources, add only a local delta, and generate only the outputs it actually needs.

**Finding:** the common path must not require hand-written YAML, provenance bookkeeping, or empty package directories. Unrelated projects do not inherit ContextCanon Foundation merely because they use ContextCanon.

## 3. Recognize Nodes in the filesystem

A repository may contain several Nodes. Each actual node root contains `CONTEXT.src.md`; grouping directories do not become Nodes automatically.

**Finding:** path is deterministic location, not stable identity.

## 4. Work on an ordinary task without wasting context

The external `teams-chat-exporter` experiment showed that an ordinary task can enter through `AGENTS.md` and `CONTEXT.md` without eagerly loading every deeper document.

**Finding:** completeness belongs to the package; prompt size belongs to the current task.

## 5. Follow a Topic when the task needs depth

A Teams selector-maintenance task matched a Topic requiring a selector guide and the current dated selector configuration. The model used those resources to distinguish configuration maintenance from a Python behavior change.

**Finding:** Required/Optional progressive disclosure works in a real harness and materially improves task framing.

## 6. Keep source documents natural while publishing a self-contained package

A project can keep `docs/architecture.md` in its normal location while the compiler materializes it under `CONTEXT/references/...`. Local Markdown links are followed recursively.

**Finding:** Resource targets are materialization seeds; package closure must preserve the references needed by the published material.

## 7. Compose independent Sources

A project may combine reusable development, security, style, and domain Sources plus a local delta. Source order is not precedence.

**Finding:** duplicate identities, cycles, incompatible diamond state, and visible Rule-ID collisions are deterministic errors. Natural-language conflict remains a semantic review problem rather than something Source order may silently resolve.

## 8. Change an inherited Rule

A child addresses an inherited Rule by stable origin Node ID plus Rule ID.

`Remove` makes it inactive while preserving removal provenance. `Override` keeps inherited identity while replacing the effective statement and recording modification provenance.

**Finding:** Source composition is useful beyond additive inheritance without making titles, paths, or parent order into identity.

## 9. Carry changes through another generation

```text
Foundation ──> Team Standard ──> Project
```

If Team Standard overrides a Foundation Rule, Project inherits the new meaning with Foundation identity and Team Standard provenance. A removed Rule remains absent while its removal provenance survives.

**Finding:** implementation exposed and fixed a real renderer defect where a grandparent Rule could remain semantically inherited yet disappear from a descendant's `CONTEXT.md`.

## 10. Detect a dangling child Change

If a Source update removes the stable Rule targeted by a consumer's local Override, that consumer must not silently continue.

**Finding:** dangling Changes are deterministic errors and later become part of Source-candidate structural review.

## 11. Compare compiled Context exactly

Compiler 0.3 introduced:

```text
contextcanon diff <before-node-root> <after-node-root>
contextcanon diff <before-node-root> <after-node-root> --json
```

Rules, Sources, Changes, Topics, and Resources are compared by compiled identity/state rather than Markdown line positions.

**Finding:** Context change is a first-class exact artifact and can be handed to human or LLM analysis without asking either to rediscover what changed.

## 12. Separate semantic identity from presentation identity

Reordering semantically unordered Sources or Topic targets must not alter `normalized_digest`. Generated presentation bytes may still differ and therefore change `package_digest`.

**Finding:** ContextCanon needs both identities. Semantic canonicalization must also not be reused as presentation order when an immutable package is later loaded.

## 13. Use an accepted Source without its repository

Compiler 0.4 publishes a reusable artifact:

```text
.context/package.json
CONTEXT.md
CONTEXT/              optional
```

A test compiles a Source, deletes its original Source repository entirely, then loads the artifact and reconstructs the full effective Rule state, provenance, Topics, dependencies, and both digests.

**Finding:** external composition must consume a complete compiled machine manifest; parsing `CONTEXT.md` back into semantics would invert the compiler pipeline.

## 14. Build a consumer completely offline

A pinned Source carries version, `normalized-digest`, and `package-digest`. Its accepted package lives under the consumer's `.context/sources/<package-digest>/`.

Regression coverage deliberately gives the Source an unusable `https://example.invalid/...` locator and deletes the provider checkout. Normal build still succeeds from accepted state.

**Finding:** a Source locator is not live inheritance. Normal build must never turn a missing package into implicit network access.

## 15. Fetch a newer Git candidate without changing inheritance

A provider repository contains a reusable Node below `nodes/library/python-development/`. The consumer has v1 accepted while the provider's `main` now publishes v2.

Git transport uses explicit metadata:

```text
transport="git"
ref="main"
node-path="nodes/library/python-development"
```

`source fetch` clones the ref temporarily, verifies the immutable package at `node-path`, and stores v2 under `.context/candidates/<digest>/`.

A normal consumer build immediately afterward still uses v1.

**Finding:** transport is candidate acquisition, not composition. Multi-Node repository paths remain location while stable Node ID remains identity.

## 16. Review and explicitly accept a Source update

The update path is now:

```text
source fetch
    ↓
source review
    ↓ exact package diff + consumer structural validation
review receipt
    ↓
source accept
    ↓
new accepted package + new exact pin
```

Review rejects a candidate that makes a local consumer Change dangling. The receipt is bound to the exact current `CONTEXT.src.md`, accepted Source state, and candidate identity; changing the consumer after review invalidates acceptance.

**Finding:** the supported path cannot skip deterministic review. Optional semantic/LLM impact review can later consume the same exact diff without entering compiler truth.

## 17. Preserve one composition algorithm for local and external Sources

A locally compiled Node and an accepted external artifact both become `CompiledPackage` before Rule composition.

**Finding:** external Sources do not get a second Remove/Override or conflict implementation. Transport and semantic composition stay orthogonal.

## 18. Put several Nodes in one Git repository

ContextCanon itself uses Gateway, Foundation, and Framework Development in one repository. Git transport tests also address a reusable Node below a nested `node-path`.

**Finding:** repository structure organizes Nodes but does not define identity or inheritance.

## 19. Move or rename a Node without changing identity

Framework Development previously moved while retaining its stable Node ID.

**Finding:** path changes are location changes, not logical replacement.

## 20. Use different agent harnesses

Codex, GitHub Copilot, goose, another agent, and a human may enter through different harness mechanics while consuming the same canonical context.

In the tested JetBrains Copilot setup, generated `AGENTS.md` is the entry point; goose uses `.goosehints`.

**Finding:** harness semantics belong at the edge.

## 21. Use smaller and local models

The external experiment produced a strong project-specific answer from a low-cost model once the task was framed by the right context.

**Finding:** ContextCanon is not only token minimization. Structured context lets smaller/local models spend capability on the task rather than repeatedly reconstructing project assumptions.

## 22. Standardize orientation across projects

A human or agent can consistently ask: what applies (`CONTEXT.md`), what is special here (`CONTEXT.src.md`), what is reused (Sources), what deeper knowledge applies (Topics), what is the current state (`STATE.md`), and what comes next (`PLAN.md`).

**Finding:** standardizing project orientation is useful infrastructure independently of LLM token economics.

## 23. Onboard a pre-existing larger project without manually curating it first

The next 1:1 test starts from a repository whose useful context is already scattered through `README.md`, `CONTRIBUTING.md`, architecture/development docs, configuration, and existing instructions.

ContextCanon will provide a deterministic inventory plus a harness-neutral LLM onboarding instruction. The LLM must produce a **proposal**, not Official Context, with provenance for each extracted item and classifications such as:

- project-local Rule;
- existing reusable Source;
- candidate reusable/generic Node;
- Topic/Resource;
- state/planning;
- ordinary documentation that should remain ordinary documentation;
- unresolved question.

A human must review and explicitly accept the proposal before canonical ContextCanon source is created.

**Finding to test:** onboarding should use LLM semantic capability to reorganize an existing project's knowledge without making the compiler semantic, and it should actively reduce duplication by identifying reusable Python/testing/writing/language conventions rather than copying every rule locally.

## 24. Grow into broader context integration

The same package/progressive-disclosure mechanisms can later integrate glossaries, patterns, code examples, structured data, PDFs, diagrams, skills, test fixtures, and operational experience.

**Finding:** new context types should reuse the same identity, package, provenance, and disclosure machinery rather than becoming parallel systems.

## Questions deliberately left for later layers

1. Protected Rules and authorized exceptions.
2. Topic composition/materialization across Source package boundaries.
3. Resource collision rules across composed packages.
4. Richer nested-repository boundary cases.
5. Reviewed LLM-assisted onboarding implementation and generic-Node catalog selection.
6. Semantic code-impact analysis from exact Context/Source diffs.

These are ordered implementation work, not unresolved proof-of-concept questions.
