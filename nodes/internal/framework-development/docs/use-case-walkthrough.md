# Use-case walkthrough

This document stress-tests ContextCanon as the implementation grows. The initial usefulness question has already been answered by a real external project; walkthroughs now capture compiler findings and define the next realistic validation cases.

## 1. Enter a repository through an almost-empty Gateway

An agent opens the ContextCanon repository. The root Node has no Sources and no Rules. Its compact Overview explains what ContextCanon is, while two Topics route framework-development work to the deeper Framework Development Node and onboarding work to the user-facing onboarding guide.

Only the onboarding guide is materialized, so the Gateway has a small generated `CONTEXT/` directory without forcing that guide into unrelated tasks.

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

A project can keep an architecture document in its natural authored location while the compiler materializes it under `CONTEXT/references/...`. Local Markdown links are followed recursively and the repository-relative directory structure is preserved inside the materialized copy.

When a Node has materialized resources, the compiler also creates `CONTEXT/README.md`. It explains directly inside the generated folder that these are package copies, not another authoring surface, and why keeping them makes the Official Context Package usable independently of the original repository layout.

**Finding:** Resource targets are materialization seeds; package closure must preserve the references needed by the published material. Generated package structure should also explain itself to a human who encounters it directly.

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

ContextCanon itself currently dogfoods four Nodes in one repository:

- ContextCanon Gateway at the repository root;
- ContextCanon Foundation under `nodes/library/foundation/`;
- the internal ContextCanon Development Workflow under `nodes/internal/development-workflow/`;
- ContextCanon Framework Development under `nodes/internal/framework-development/`.

Framework Development composes both Foundation and Development Workflow explicitly. Their directory proximity under `nodes/` creates no inheritance by itself. Git transport tests also address a reusable Node below a nested `node-path`.

**Finding:** repository structure organizes Nodes but does not define identity or inheritance. This matters directly for future architecture/product/subsystem hierarchies where filesystem nesting may provide orientation without creating hidden context propagation.

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

Short directory `README.md` files now add another deliberately lightweight orientation layer where direct filesystem/GitHub browsing otherwise leaves ownership ambiguous. Generated `CONTEXT/` directories receive their own compiler-generated README so package copies explain themselves without becoming a second authoring truth.

**Finding:** standardizing project orientation is useful infrastructure independently of LLM token economics.

## 23. Run the first large 1:1 onboarding test

The first-adoption mechanics are now implemented on the current review branch. The next 1:1 test starts from a materially larger repository whose useful context is already scattered through `README.md`, `CONTRIBUTING.md`, architecture/development docs, configuration, existing agent instructions, and likely some stale or contradictory material.

The implemented path is:

```text
existing Git repository
      ↓
contextcanon onboard prepare
      ↓ exact frozen evidence
contextcanon onboard instruction
      ↓ framework-owned semantic assignment
strong external reasoning LLM
      ↓ one proposal.json
contextcanon onboard validate
      ↓ provenance-checked proposal
contextcanon onboard review
      ↓ human accept/reject decisions against exact evidence
contextcanon onboard accept
      ↓ staged compile + ownership checks + explicit publication
canonical Context Node + normal build/check
```

The LLM may propose project-local Rules, existing reusable Sources, candidate reusable Nodes, Topic/Resource material, state/planning findings, ordinary documentation, and unresolved questions. It cannot publish any of them by itself.

The real test deliberately has **two equally important axes**:

1. Is the onboarding workflow understandable, comfortable and trustworthy at realistic proposal size?
2. Is ContextCanon itself pleasant and useful when a messy project has to be cleaned up into sensible Nodes, Sources, Rules and Topics?

It must also test a question that mechanics alone cannot answer: whether ContextCanon Foundation should normally be offered/recommended as a reusable baseline during onboarding or remain fully opt-in. The repository Gateway is not a candidate baseline; it is local navigation for this repository.

**Finding to test:** the trust mechanics are now explicit enough that the next uncertainty should be semantic/product ergonomics — what the strong model classifies well, what the human corrects, how naturally reusable context is recognized, and whether the resulting context actually improves later work.

## 24. Grow into broader context integration

The same package/progressive-disclosure mechanisms can later integrate glossaries, patterns, code examples, structured data, PDFs, diagrams, skills, test fixtures, and operational experience.

**Finding:** new context types should reuse the same identity, package, provenance, and disclosure machinery rather than becoming parallel systems.

## Questions deliberately left for later layers

1. Protected Rules and authorized exceptions.
2. Topic composition/materialization across Source package boundaries.
3. Resource collision rules across composed packages.
4. Richer nested-repository boundary cases.
5. Reviewed re-onboarding/update of a repository that already has canonical ContextCanon context.
6. Semantic code-impact analysis from exact Context/Source diffs.
7. Second-pass extraction of high-value context hidden in source comments/docstrings after coarse ContextCanon adoption.

These are ordered implementation work, not unresolved proof-of-concept questions.
