# Current State

ContextCanon now has a stable deterministic core plus a structure-first onboarding path that has been exercised on the materially larger `SomeSunlight/ai-workstation` project.

The current project-owner accepted `main` baseline is PR #12, squash-merged as:

`bac1f52048b3d82cedb00b04fccd114607c4c915`

PR #12 replaced the earlier leaf-first onboarding assumption with a two-pass model:

1. discover and human-review the coarse Context structure;
2. only after those shelves are accepted, place existing project knowledge onto them.

Before merge, exact review head `0eafad15e0cddd4a79f5088cd51e7db9dbde4880` passed GitHub Actions run #372 with **112/112 tests** and zero generated drift for Gateway, Framework Development, Development Workflow, and Foundation.

## What the real `ai-workstation` test proved

The first structure proposal reconstructed a useful coarse project shape from the original frozen Evidence. The project owner then edited that hierarchy directly in `contextcanon-onboarding/structure.md`, including removing the speculative reserved local-model Node because the Evidence established deferral but did not establish a future Compose-based implementation boundary.

That human correction was the desired gate rather than a failure of the semantic pass: the LLM performed strong software archaeology, while future architecture remained owner-owned.

The subsequent real operator run also succeeded:

- `structure-preview.md` made the planned filesystem/Node changes understandable before mutation;
- the already-onboarded root Node remained protected;
- the missing child/group Node skeletons were materialized successfully;
- the resulting generated `CONTEXT.md` files now make the accepted structure visible even though their local semantic deltas are intentionally still almost empty.

This validates the structure-first direction strongly enough to continue with the second pass.

## Current self-hosted Nodes

ContextCanon currently uses four conceptual roles on its own repository:

### ContextCanon Gateway

The repository root is the compact entry point and routes deeper work through Topics.

### ContextCanon Foundation

`nodes/library/foundation/` is the reusable ContextCanon baseline. It owns the reusable authoring/Official-Context/Topic/Source-composition semantics.

### Development Workflow

`nodes/library/development-workflow/` is now a reusable Library Node with the same stable identity that previously lived under `nodes/internal/`.

It is intentionally independent from Foundation. Consumers that want both compose both explicitly; a reusable workflow does not force Foundation transitively merely because it is reusable.

### ContextCanon Framework Development

`nodes/internal/framework-development/` composes Foundation and Development Workflow separately, then adds only ContextCanon-specific architecture, implementation, onboarding, test/CI, and development guidance.

ContextCanon-specific `uv` installation guidance remains a local Framework Development delta rather than leaking into the reusable workflow.

## Current onboarding model

The preferred real-project path is now:

```text
existing repository
    ↓
freeze exact Evidence once
    ↓
structure-discovery instruction
    ↓
strong reasoning LLM
    ↓
strict structure proposal
    ↓
human-editable structure.md
    ↓
preview missing/protected Nodes
    ↓
materialize only accepted Node skeletons
    ↓
placement instruction bound to Evidence + edited structure
    ↓
strong reasoning LLM
    ↓
strict placement proposal
    ↓
evidence-rich placement.md review
    ↓
[publication/cleanup still to be completed]
```

The visible `contextcanon-onboarding/` directory is human working material. Immutable machine Evidence remains under `.context/onboarding/<digest>/`.

Frozen Evidence has proven useful for more than stale-review safety: the same exact project bytes can now be reused for changed semantic methods without re-running discovery from an accidentally different repository state.

## Placement semantics already implemented

The second semantic pass is bound to both the exact frozen Evidence and the exact edited structure digest.

It can propose:

- `rule`
- `topic-resource`
- `ordinary-documentation`
- `state`
- `plan`
- `authority-mapping`
- `unresolved`

and distinguishes placement operations:

- `keep`
- `move`
- `reference`
- `map`

When wording is carried forward, provenance is explicit:

- `exact`
- `lightly-edited`
- `synthesized`

The semantic instruction tells the model to prefer exact source wording when it is already clear. This intentionally changes the model's role from semantic rewriter to semantic curator/placer.

Placement can also compare generic project guidance with explicitly supplied verified reusable Source packages, including the promoted Development Workflow, so a project does not need a second copied workflow Node.

## Important boundaries that remain

ContextCanon still does **not** let an LLM publish project truth.

The merged PR #12 deliberately stops before destructive placement publication. In particular it does not yet:

- write reviewed placement decisions into all destination `CONTEXT.src.md` files;
- install/pin placement-selected Sources into their target Nodes;
- remove duplicated canonical rule text from README/CONTRIBUTING/other project documents;
- splice state/planning prose into arbitrary human documents;
- solve owner-selected Sources that arise during architecture review but were not themselves inferred from frozen Evidence;
- generalize cross-cutting graph relationships, authority corpora, or a browser UI beyond what real projects have demonstrated.

## Immediate next step

Continue the real `ai-workstation` onboarding rather than designing publication in isolation.

Use the already accepted `structure.md` and the original frozen Evidence to run the second placement LLM pass. Offer the reusable Development Workflow as an exact catalog package so the real result shows whether generic workflow guidance is reused rather than duplicated locally.

The next framework block should then make the reviewed placement result human-editable and deterministically previewable before writing Node authoring. The likely publication boundary is:

```text
placement-proposal.json
    ↓
placement.md human review/correction
    ↓
placement preview of exact CONTEXT.src.md / Source changes
    ↓
explicit human publication
```

Ordinary project documentation should remain in its natural home unless a later reviewed cleanup identifies true duplicate canonical rule text. State/plan/unresolved findings must remain durably recoverable even when they are not automatically spliced into prose documents.
