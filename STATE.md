# Current State

The accepted `main` baseline remains PR #12, squash-merged as:

`bac1f52048b3d82cedb00b04fccd114607c4c915`

PR #13 on `agent/onboarding-placement-publication` is the active review candidate. It completes the second half of structure-first migration onboarding: after humans accept the shelves, reviewed project knowledge can now be placed onto those Nodes, previewed as exact authoring/Source changes, and explicitly published without treating the semantic LLM as project authority.

## What is implemented in PR #13

The placement proposal remains the strict machine/LLM contract, while `contextcanon-onboarding/placement.md` is the human gate. The editable review is destination-first and can change acceptance, destination, kind/action, title and maintained wording. Canonical Rule and Topic IDs are allocated once on the human side and remain stable across review/preview cycles.

Placement now distinguishes `overview`, `rule`, `topic-resource`, `ordinary-documentation`, `state`, `plan`, `authority-mapping` and `unresolved`, with placement actions appropriate to those semantics. Clear source wording can remain exact; light edits and synthesis stay explicit.

Reusable Sources have two visibly different origins:

- `evidence-derived` — the semantic pass found reuse from the supplied exact Source catalog;
- `owner-selected` — the project owner deliberately adds a supplied exact Source independently of what frozen project Evidence claimed.

Both remain bound to exact Node/version/normalized/package identity. Publication resolves durable Git locator, exact commit and Node path instead of writing a transient local checkout path. The final publication preview keeps the Source name, origin, version, package digest and Git provenance visible before mutation.

`contextcanon onboard placement-preview` renders exact per-Node `CONTEXT.src.md` deltas, Source changes, durable follow-ups and deferred mutable-Markdown cleanup candidates without mutating the project. `contextcanon onboard placement-publish` revalidates frozen Evidence and review identity, refuses stale Node source after preview, installs exact Source packages, compiles touched Nodes before writing generated output, writes an exact acceptance record, and rolls back its own changes on failure.

Initial placement deliberately does not rewrite README, CONTRIBUTING, architecture or other ordinary mutable project Markdown. Accepted state, plan, ordinary-documentation, authority-mapping and unresolved findings that are not safely expressible in current Node authoring remain recoverable in exact acceptance/follow-up state. Duplicate text removal is a separate later cleanup review.

The visible `contextcanon-onboarding/README.md` is now a deterministic resumption checkpoint: it records the last ContextCanon-validated Evidence/structure/placement stage, exact Source catalog identities and next safe command. It does not pretend that an arbitrary human edit has already been validated.

## Real `ai-workstation` vertical validation

The final real test reused the original project bytes rather than a new live-repository interpretation:

- project commit: `4106fec3f7726d6c9bfedd70d30d9ed025b7c166`;
- reproduced frozen Evidence: `2a926bf353b252db4039e5c4b63b39abad6bab46c11982e88b3eb17e19cf203d`;
- accepted existing root Node ID: `aea56adf-2a26-43f0-b712-3bbeab7a3097`;
- seven accepted child/group Nodes;
- 33 Evidence-based placement findings;
- owner-selected Development Workflow Source `c4c94726-3cc7-4df6-b779-72bbf9c06f40`, package `1d82c87e4f4140791f354c9d9479df845eb65c13fce1c664ecb05bec9532c8eb`.

The human review also resolved the Evidence-only version ambiguity as owner input: `pyproject.toml` should track the repository release version represented by CHANGELOG rather than leaving two stale independent version streams.

The disposable-clone publication test proved all of the following in one vertical run:

- all 8 accepted Context Nodes received their reviewed local deltas;
- existing root identity and unrelated authored root content survived;
- child Node IDs remained stable;
- frozen Evidence-covered project files remained byte-identical;
- root and child-local Rules, Overviews and cross-directory Topic/Resource routing materialized correctly;
- Development Workflow was pinned with exact package identity and durable Git provenance;
- accepted state/plan/ordinary-documentation semantics remained visible as durable follow-ups;
- every resulting Node compiled with zero generated drift;
- the second preview showed the placement already materialized;
- the second publication changed 0 Context sources and reproduced acceptance digest `a206e3423e9ffaccf7c3f7a1a0e2f140251a834f3c6eaf9764cd952b95e509c4`.

The real run found one product gap that synthetic tests had missed: publication preview originally showed only Source Git transport details and lost the human-review distinction between owner-selected and Evidence-derived reuse. PR #13 now preserves that provenance and exact Source identity through the preview, with a regression test.

## Review-candidate verification

The temporary real-test workflow, harness, reports and diagnostics have been removed from the final PR diff. The cleaned candidate tree was regenerated and passed **129/129 tests** plus `contextcanon check --all .` for Gateway, Framework Development, Development Workflow and Foundation with zero generated drift. The net diff against `main` contains only product code, tests, documentation/planning and their generated Context packages.

The first clean commit was produced by the temporary GitHub Actions finalizer, so GitHub attributed its PR synchronization to `github-actions[bot]` and marked that automatic PR run `action_required` without creating a job. A normal repository-authored PLAN/STATE checkpoint now follows to obtain an ordinary exact-current-head PR workflow without changing product semantics.

## Boundaries that intentionally remain

PR #13 does **not** implement destructive onboarding cleanup. README/CONTRIBUTING/docs remain project-owned and untouched during placement publication. A later cleanup workflow may preview true duplicate canonical text and require explicit confirmation before removing it.

The project also does not yet choose a remote Node-library registry/distribution architecture, invent a special GroupNode type, make navigation hierarchy imply Source inheritance, automatically splice state/planning findings into arbitrary prose, or build a browser UI. Those remain separate questions to answer from further real use.

Normal ContextCanon-native project evolution is distinct from one-time migration onboarding: after adoption, humans edit canonical `CONTEXT.src.md`/project documentation and use normal build/check workflows rather than repeatedly re-running migration Evidence analysis.

## Immediate next step

Obtain the normal exact-current-head PR #13 GitHub Actions result for this review-candidate checkpoint. If it is all green with zero generated drift, present PR #13 for explicit project-owner review. Do not merge, start duplicate-text cleanup, or begin another development block before that review decision.
