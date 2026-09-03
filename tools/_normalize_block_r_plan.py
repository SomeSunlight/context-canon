from pathlib import Path

path = Path("PLAN.md")
text = path.read_text(encoding="utf-8")
marker = "#### Block R — first production post-publish UX and parent composition findings\n"
index = text.find(marker)
if index < 0:
    raise SystemExit("Block R marker not found")

replacement = '''#### Block R — first production use after onboarding

Purpose: turn the first real `ai-workstation` onboarding result into a pleasant daily ContextCanon system: clear review surfaces, simple normal authoring, a real semantic Parent chain, and safe reusable-Source updates.

**Status: ACTIVE — R5 Semantic Parent relationship, step 1 of 5. Fast-run remains ACTIVE.**

**How to read this block:** `R1`, `R2`, ... are goals. Work them from top to bottom. Inside each goal, the numbered checkboxes are the implementation order. The next unchecked checkbox is the next work. No hidden `R4a/R4b` numbering is required to understand the plan.

##### R1 — Make the human review surfaces obvious and self-contained

- [x] 1. Give Step 03 and Step 07 quiet but visible edit boundaries.
- [x] 2. Put the Step 07 decision/Kind glossary directly into the review artifact.
- [x] 3. Remove `Action` as a fake independent choice; derive it from Kind.
- [x] 4. Add a source-file-first transformation audit beside the destination-first review.
- [x] 5. Show every linked promoted finding from one Source edit so zero semantic loss is easy to audit.

Checkpoint: Step 03/07 editing is visibly understandable; `STEP-07a-source-audit.md` is generated/read-only while Step 07 remains the sole editable placement truth.

##### R2 — Make normal post-onboarding authoring simple

- [x] 1. Add first-class Rule/Topic authoring commands so humans do not invent hidden IDs.
- [x] 2. Document the daily loop: read `CONTEXT.md`, edit `CONTEXT.src.md`/Resources, build, check, review dependency updates when present.

Checkpoint: `contextcanon author rule` and `contextcanon author topic` allocate stable IDs and write validated ordinary `CONTEXT.src.md`.

##### R3 — Make Source After review easy to audit from the original document

- [x] 1. Generate a deterministic source-first audit grouped by original file/range with exact Before and effective After.
- [x] 2. Include destination Node/content and all linked findings without creating a second human gate.

Checkpoint: focused audit/review/reset regressions plus the complete 167-test suite, self-hosted build/check and diff hygiene passed on the clean R3 product checkpoint.

##### R4 — Make Topics and Resources real transitive package semantics

- [x] 1. Inherit effective Topics through accepted Source packages, including deterministic diamond/conflict handling.
- [x] 2. Materialize Topic Resources under stable origin-Node namespaces and render the complete effective Rules + Topics context with provenance.

Checkpoint: pinned packages can provide Topics and exact Resource bytes fully offline. The focused R4 tests passed 37/37; the complete deterministic suite passed 168/168 together with self-hosted build/check and diff hygiene.

##### R5 — Semantic Parent relationship

Goal: turn the human-accepted Step-03 hierarchy into an explicit ContextCanon relation. Filesystem nesting remains only layout; it must never silently imply inheritance.

- [ ] 1. Add an explicit `Parent` relationship to the authoring grammar/model/compiler/package/rendering boundary, distinct from ordinary reusable Sources but reusing the same immutable package-composition machinery.
- [ ] 2. Persist every non-root accepted Step-03 parent into onboarding publication and pin the exact accepted Parent package locally in the Child.
- [ ] 3. Make Parent changes non-live: normal builds use the accepted package pin; a changed Parent can only become a candidate until reviewed/accepted.
- [ ] 4. Prove that the Parent chain carries complete effective Rules, Topics and Resources transitively, so a reusable Development Workflow attached at the intended ancestor reaches descendants without being selected on every Node.
- [ ] 5. Cover migration/idempotency/recovery for an already-published `ai-workstation`-like tree, then run the focused tests, complete suite, self-hosted build/check and hygiene gate.

Expected practical result: when working inside a subsystem, an agent can start at that subsystem's Node and receive the accepted higher-level context through the semantic Parent chain without loading unrelated sibling context.

##### R6 — Reusable Source update discovery UX

Goal: make newer reusable Node packages discoverable without weakening the accepted-snapshot model.

- [ ] 1. Let projects discover/fetch a newer reusable Source package without manually tracking package identities.
- [ ] 2. Keep every update candidate-only until explicit review/accept; never introduce live implicit pulls.
- [ ] 3. Document and test the normal update loop, including offline use of the last accepted package.

##### Deferred compatibility debt

Block Q remains intentionally deferred: an old in-flight onboarding snapshot created before `run-inputs.json` existed can lose a formerly owner-selected Source during reset/recreation. Fresh/current onboarding already persists and reuses owner-selected Sources correctly. Do not reopen the completed real placement merely to repair that legacy migration edge.

Post-publish basis: the owner accepted and published the first real `ai-workstation` placement and is now using the resulting Nodes as a productive system. That live use is the design driver for R5/R6; PR #13 remains draft and unmerged until explicit project-owner approval.
'''

path.write_text(text[:index] + replacement, encoding="utf-8")
