from pathlib import Path

plan = Path("PLAN.md")
text = plan.read_text(encoding="utf-8")
marker = "## Active development block: reviewed placement publication on `ai-workstation`"
if text.count(marker) != 1:
    raise SystemExit(f"expected exactly one active placement block marker, got {text.count(marker)}")
prefix = text.split(marker, 1)[0]
block = '''## Active development block: placement ownership and reviewed publication on `ai-workstation`

PR #12 and the first real `ai-workstation` run proved the structure-first split: the project owner reviewed the coarse shelf map, corrected speculative future architecture, previewed the change, and materialized the seven missing Node skeletons without replacing the existing root. The first real placement run then exposed the next product boundary. The problem is not merely to link old text to Nodes; ContextCanon must help decide **where project truth should be maintained in the future** so redundancy decreases rather than becoming better indexed.

The real frozen `ai-workstation` Evidence and the resulting `placement.md` are the design pressure for this block. The project owner reviewed P-001 through P-015 in detail; the framework review compared the full placement with the prior leaf-first proposal and the reusable Development Workflow package. These are concrete first-customer findings, not speculative feature requests.

### Accepted real-placement findings

- [x] Treat future **ownership** as the primary placement question: distinguish the current evidence location from the place where canonical meaning should be maintained after onboarding.
- [x] Put destination first in the human review surface; it is the first decision the reviewer needs to understand.
- [x] Keep familiar repository documents useful but lightweight: README is orientation/navigation, not the durable home for volatile project state, future plan, detailed architecture, or every implementation invariant.
- [x] Add `overview` as a placement kind for stable local orientation such as Node responsibility; do not force durable descriptive architecture into temporary `state`.
- [x] Replace ambiguous placement action `move` with `promote`: establish canonical ContextCanon meaning at a destination now; any deletion/replacement of old duplicate prose belongs to a later cleanup operation.
- [x] Keep `reference` narrow: the natural source remains authoritative/current and the Node routes to it without copying the referenced text as maintained truth.
- [x] Keep `map` for an explicit local interpretation of fixed/authoritative material: preserve the authority, state what it means for this Node, and retain evidence/provenance.
- [x] Allow multiple references/resources from one Node; do not impose a 1:1 Node-to-document relationship.
- [x] Treat navigation back-links as generated/orientation concerns rather than another manually maintained semantic copy.
- [x] Separate user guidance from architecture even when both are currently mixed in one README; placement follows semantic ownership rather than existing file boundaries.
- [x] Let a central architecture document become thinner when its Node-local details acquire clearer ownership; retain cross-layer architecture and relationships centrally when useful.
- [x] Introduce a deliberately small document policy for this experiment: supported onboarding documents are Markdown and are classified `mutable` or `fixed`; non-Markdown authorities such as PDF are not supported yet rather than silently converted or partially interpreted.
- [x] For `mutable` Markdown, placement may recommend later extraction/reorganization; for `fixed` Markdown, use references or mappings and do not plan destructive edits.
- [x] Keep document cleanup as a separate reviewed follow-up after ContextCanon ownership is correct; do not combine first placement publication with arbitrary prose surgery.
- [x] Preserve exact source wording when it is already good, but allow a clearer Node-local overview/mapping when an authoritative or fixed source is awkwardly written; provenance must remain visible.
- [x] Keep Rule identity independent of title, wording, and location; a review-title correction such as the real P-012 label must not define semantic identity.
- [x] Prevent semantic regression between passes: the structured placement must not silently lose high-value rules or unresolved contradictions found in the same frozen Evidence, including the real `ai-workstation` contribution/release rules and version discrepancy.
- [x] Distinguish Evidence-derived reusable Source matches from **owner-selected Sources**. A project owner may deliberately choose a reusable Source such as Development Workflow even when frozen project Evidence cannot prove that future architectural choice.
- [x] Preserve project-specific deltas alongside a reusable Source instead of treating Source reuse as wholesale replacement of CONTRIBUTING or other local guidance.
- [x] Make `placement.md` the persistent human review state: edit decision, destination, kind/action and corrected canonical wording directly there; do not require a parallel findings list or large JSON edit.
- [x] Never silently overwrite human-edited `placement.md` on a later LLM run. A later proposal may become a new candidate or be discussed against the existing review, but no general semantic merge engine is required.
- [x] Keep migration/onboarding of an established repository separate from normal ContextCanon-native project life. New projects should start small and grow Nodes/Rules/Topics as real boundaries appear rather than repeatedly run software archaeology.
- [x] Record reusable-Node distribution as a later UX problem: consumers should not need to understand ContextCanon's own tool checkout merely to reuse library Nodes. Separate repository, catalog/registry, or Git layout remains deliberately undecided.
- [x] Explore a self-describing onboarding workspace before building a GUI: a human or LLM should be able to open `contextcanon-onboarding/` later and reconstruct current stage, accepted artifacts, and next operation from durable local guidance.

### Fast-run execution mode for this owner-approved block

The project owner approved implementing the whole real-placement correction without intermediate product acceptance. Apply the reusable Development Workflow's fast-run rule: keep PLAN/recovery checkpoints honest, split implementation into coherent bounded blocks, run focused deterministic checks inside each block, and defer PR-description polish, self-hosted package regeneration and the complete exact-head CI/zero-drift cycle until a coherent review candidate exists. This does not weaken the final project-owner review or merge gate.

#### Block A — placement semantics and document ownership

- [ ] Evolve the experimental placement contract from current-location sorting to future ownership: `overview`, `rule`, `topic-resource`, `ordinary-documentation`, `state`, `plan`, `authority-mapping`, `unresolved`; actions `keep`, `promote`, `reference`, `map`.
- [ ] Make the placement instruction explicitly minimize future redundancy, distinguish README/state/plan/architecture responsibilities, and forbid `reference` from becoming maintained text duplication.
- [ ] Add Markdown document policy (`mutable` / `fixed`) to the structure discovery/review boundary and reject unsupported non-Markdown knowledge bodies in this v1 experiment instead of inventing conversion semantics.
- [ ] Tell the semantic pass to preserve high-value Evidence findings across the two-pass split and surface unresolved contradictions rather than allowing a better hierarchy to become semantically poorer.
- [ ] Cover the real `ai-workstation` patterns in focused regression tests: README scope/plan pressure, Node responsibility as Overview, canonical repository Rule, mutable architecture split, fixed authority mapping, local CONTRIBUTING deltas, and unresolved version discrepancy.

#### Block B — editable human placement gate

- [ ] Redesign `placement.md` around the reviewer: destination first, then decision/kind/action, proposed maintained meaning, rationale and Evidence.
- [ ] Parse only a deliberately small editable Markdown control surface; keep Evidence/provenance rendering outside the editable contract.
- [ ] Allocate canonical Rule/Topic identities once in human review state and preserve them across repeated load/preview; titles and wording remain editable presentation.
- [ ] Preserve an existing human-edited placement review instead of overwriting it; fail clearly when a changed proposal requires a new candidate/review decision.
- [ ] Support explicit owner-selected reusable Sources independently of LLM-derived `source_reuses`, while retaining exact immutable package identity and project-specific local deltas.

#### Block C — deterministic placement preview and publication

- [ ] Add deterministic `placement-preview` that shows exact per-Node `CONTEXT.src.md` deltas, Source install/pin changes, and findings that intentionally remain outside Node authoring before mutation.
- [ ] Materialize accepted Overview, local Rules, Topics/Resources and Source state without replacing Node identity or unrelated authored content; repeated preview/publication must be safe.
- [ ] Carry accepted `state`, `plan`, `ordinary-documentation`, authority mappings and unresolved findings durably even when they are not automatically spliced into arbitrary repository prose.
- [ ] Keep existing mutable Markdown untouched during initial placement publication. A later cleanup preview may propose removing duplicate promoted text and leaving orientation/references, but that remains a distinct operation.
- [ ] Preserve exact Source package identity plus durable Git provenance/update metadata without writing a transient developer checkout path into project truth.

#### Block D — resumable onboarding UX and final real-project validation

- [ ] Make the visible onboarding workspace self-describing enough that a human or capable LLM can enter through one local file and reconstruct Evidence identity, accepted structure, current placement-review stage and next command without chat history.
- [ ] Document the distinction between one-time migration onboarding and ContextCanon-native project growth/maintenance; keep future context-audit ideas separate from initial onboarding.
- [ ] Record reusable Node distribution as an explicit later UX decision without selecting a repository/registry architecture in this block.
- [ ] Re-run the corrected placement pass against the real frozen `ai-workstation` Evidence and owner-edited structure, including owner-selected Development Workflow, and inspect the new editable review before publication.
- [ ] Validate preview/publication vertically on the real materialized `ai-workstation` Nodes with at least one Overview, root Rule, child-local Rule, Topic/Resource, fixed-authority mapping, mutable-document follow-up and reusable Development Workflow Source.
- [ ] After the coherent implementation settles, regenerate affected self-hosted Context packages, run the complete deterministic suite and `contextcanon check --all .` on the exact review head, inspect the PR diff for temporary/generated drift, and update PR #13 for project-owner review. Do not merge without explicit approval.
'''
plan.write_text(prefix + block, encoding="utf-8", newline="\n")

source = Path("nodes/library/development-workflow/CONTEXT.src.md")
text = source.read_text(encoding="utf-8")
needle = '''- **Batch related edits before expensive final verification:** For one coherent correction block, make the related authoring/code changes and run proportionate focused checks first; do not repeat the project's most expensive generated-output, integration, packaging, or full verification cycle after every micro-edit.
  Why: Final verification is valuable, but repeating it on superseded intermediate heads adds ceremony without increasing confidence in the candidate that will actually be reviewed or merged.
  <!-- ctx:rule id="CCW-004" -->
'''
replacement = needle + '''
- **Use owner-approved fast-run blocks without weakening the final gate:** When the project owner explicitly approves a coherent implementation scope and says intermediate product review is unnecessary, keep durable PLAN/recovery checkpoints and focused verification inside bounded work blocks, but defer repeated PR-description polish, full CI, generated-output regeneration, and other review ceremony until the coherent review candidate.
  Why: Explicit delegation can remove intermediate coordination cost without sacrificing recoverability, final human review, or exact-head merge verification.
  <!-- ctx:rule id="CCW-009" -->
'''
if text.count(needle) != 1:
    raise SystemExit("development workflow CCW-004 insertion point changed")
source.write_text(text.replace(needle, replacement), encoding="utf-8", newline="\n")

doc = Path("nodes/library/development-workflow/docs/change-workflow.md")
text = doc.read_text(encoding="utf-8")
needle = "The important distinction is that **review-ready and merge-ready are different states**. A successful merge is followed by one small closure step because the merge itself creates facts that a pre-merge candidate cannot truthfully record.\n"
addition = needle + '''
### Owner-approved fast-run blocks

Sometimes the project owner has already reviewed the product direction and explicitly delegates a coherent implementation phase without wanting to approve every intermediate block. In that case, keep the recovery map and meaningful focused checks, but do not manufacture repeated PR handoffs, full CI cycles, generated-output refreshes, or status-polish commits merely because normal review would have happened between those blocks.

Fast-run changes **cadence, not authority**: the work still stays on a review branch, PLAN remains current enough to resume after interruption, unknown failures are investigated, and the resulting coherent candidate still requires project-owner review followed by the ordinary exact-head merge gate.
'''
if text.count(needle) != 1:
    raise SystemExit("development workflow fast-run documentation insertion point changed")
doc.write_text(text.replace(needle, addition), encoding="utf-8", newline="\n")
