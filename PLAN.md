# Plan

## Completed validation

ContextCanon has passed both self-hosted and external validation.

- [x] Establish Gateway, Foundation, and Framework Development as real dogfood Nodes.
- [x] Build the first deterministic compiler and run it against the repository itself.
- [x] Apply ContextCanon to `SomeSunlight/teams-chat-exporter` on a dedicated experiment branch.
- [x] Generate the Official Context Package deterministically in that external project.
- [x] Enter the project through a real GitHub Copilot harness using generated `AGENTS.md`.
- [x] Run an ordinary task that required no deeper Topic material.
- [x] Run a Teams-selector task that required the Topic's deeper resources.
- [x] Confirm that the model used the project context to distinguish configuration changes from Python behavior changes.
- [x] Confirm that the structure is useful to a human reviewer as an architectural orientation interface, not only as LLM prompt machinery.
- [x] Confirm that progressive disclosure is useful even with a low-cost model, strengthening the case for smaller and local LLMs.

The conclusion is now strong enough to change development strategy: **stop proving that ContextCanon is useful and complete the deterministic core needed for broad daily use.**

## Strategy: harden the reusable compiler core

ContextCanon should soon be usable across many real projects without repeatedly hitting known missing fundamentals.

That does not mean implementing everything at once. Each compiler step remains a coherent deterministic layer with explicit source syntax, positive and negative regression fixtures, repository dogfood, and CI drift checking.

```text
human-authored Context
        ↓
parse exact syntax
        ↓
resolve + compose exact semantics
        ↓
validate identities and operations
        ↓
render deterministic Official Context Package
        ↓
exact diff / package identity
        ↓
optional LLM interpretation or project work
```

No LLM belongs inside deterministic compiler truth.

## Compiler 0.2 — inherited Rule changes

This is the current semantic hardening block.

- [x] Fix rendering so transitively inherited Rules remain visible by their true origin Node.
- [x] Add explicit `Remove` operations for inherited ordinary Rules.
- [x] Add explicit `Override` operations while preserving inherited Rule identity.
- [x] Carry Override provenance transitively into descendants.
- [x] Carry Remove provenance transitively so absence remains meaningful in later composition.
- [x] Reject dangling Changes instead of silently ignoring them.
- [x] Reject duplicate local Changes against the same inherited Rule identity.
- [x] Reject diamond graphs where the same stable Rule arrives with incompatible effective definitions/provenance.
- [x] Reject a diamond where one Source path keeps a Rule and another explicitly removed it.
- [x] Deduplicate compatible repeated Rule state without inventing Source precedence.
- [x] Include Changes, override provenance, and removal provenance in exact normalized semantics.
- [x] Add positive, dangling, duplicate, transitive, and diamond-conflict regression fixtures.
- [x] Document the compiler pipeline and stage boundaries in `docs/compiler.md` and `CONTRIBUTING.md`.
- [x] Expose the compiler module architecture directly in Framework Development context.
- [ ] Regenerate all dogfood packages with compiler 0.2 and finish with green CI.

## Next: deterministic Context diff

The next compiler layer should make Context change itself a first-class exact artifact.

```text
old compiled Context
        +
new compiled Context
        ↓
exact deterministic change set
        ↓
Rule IDs / Topic IDs / Sources / package changes
        ↓
optional LLM impact review
```

- [ ] Define a normalized machine-readable diff model based on stable identity and provenance.
- [ ] Detect added, removed, and changed Rules without relying on titles or textual file diffs.
- [ ] Distinguish inherited semantic changes from local source changes where provenance permits.
- [ ] Include Source package/version changes and Topic changes.
- [ ] Produce a compact human-readable summary from the same deterministic diff.
- [ ] Add CLI support without coupling the diff to a particular harness.
- [ ] Test unchanged, additive, removed, overridden, and transitive cases.

This diff becomes the exact input to later semantic impact analysis.

## Next: immutable external Sources and update acceptance

Broad use across independent projects requires reusable Sources without live dependency on another checkout.

- [ ] Define an immutable external Source/package locator contract.
- [ ] Pin exact Source identity, version, and package digest.
- [ ] Keep accepted packages usable without a live Source repository.
- [ ] Detect newer Source packages as candidates rather than silently inheriting them.
- [ ] Compare accepted and candidate packages using the deterministic Context diff.
- [ ] Require explicit acceptance before rebuilding a consumer against a new Source package.
- [ ] Surface dangling local Changes caused by accepted Source updates.
- [ ] Support addressing Nodes inside repositories containing multiple Context Nodes.

Transport/cache mechanics should remain separate from semantic composition.

## Then: protected Rules and authorized exceptions

- [ ] Mark selected Rules as protected in their owning Node.
- [ ] Reject ordinary Remove/Override against protected Rules.
- [ ] Let the owner define stable authorized exceptions.
- [ ] Add explicit `Use Exception` syntax in consumers.
- [ ] Preserve exception provenance transitively.
- [ ] Add deterministic invalid/dangling exception diagnostics.

Governance validation is not a security boundary; it makes declared policy mechanically checkable.

## Broader compiler hardening

After those central layers:

- [ ] Multiple orthogonal Sources with broader structural conflict diagnostics.
- [ ] Resource collision rules across composed packages.
- [ ] Topic composition/materialization across Source package boundaries.
- [ ] Nested Git repository boundary behavior.
- [ ] Safe compiler-owned generated-file manifest if automatic stale adapter cleanup is later needed.
- [ ] Authoring assistance for Node initialization, stable IDs, and compact templates.

## Semantic layer above the compiler

Once deterministic diff exists, implement the first high-level workflow:

```text
exact Context diff
        ↓
LLM impact review
        ↓
Rule ID → affected files / code / config / tests / docs
        ↓
reason → proposed action
```

- [ ] Keep impact analysis outside deterministic compiler truth.
- [ ] Require a reason for each suggested affected location.
- [ ] Let a human approve/reject the impact set.
- [ ] Let an agent implement approved changes while following the new Official Context.
- [ ] Keep the workflow harness-neutral so local models, goose, Copilot, Codex, Hermes, and others can consume the same exact change set.

## Context integration roadmap

Add context types through the same progressive-disclosure and package mechanisms rather than parallel systems:

- [ ] Glossaries and domain terminology.
- [ ] Coding patterns and example code.
- [ ] CSV files, schemas, tables, and other structured data.
- [ ] PDFs, images, diagrams, and other reference media.
- [ ] Skills and executable workflows.
- [ ] Test fixtures and worked examples.
- [ ] Operational experience, known pitfalls, and troubleshooting knowledge.

## Working rule

**Build central deterministic semantics deliberately, then use them aggressively.**

The external proof has been made. The quality bar now is that ContextCanon should become boring infrastructure: predictable enough to place under many projects and stop thinking about unless the context itself changes.
