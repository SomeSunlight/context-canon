from pathlib import Path

PLAN_BLOCK = '''#### Block R — first production post-publish UX and parent composition findings

Purpose: capture what became visible only after the first real `ai-workstation` placement was fully accepted and published. The end-to-end publish succeeded; the owner is now inspecting the resulting Nodes as a real working project. These findings are the next product/design backlog, not reasons to rewind the completed onboarding run.

**Status: NEXT — preserve now, implement in coherent follow-up blocks after post-publish inspection. Fast-run remains ACTIVE.**

##### Review surfaces

- [ ] Give Step 03 the same visible edit affordance as Step 07, but use a quieter presentation that preserves the visual dominance of the Node tree. Apply the same lower-noise treatment to Step 07 so editable boundaries are obvious without overwhelming headings/content.
- [ ] Make Step 07 self-contained about every editable control. Show allowed `Decision` values and a concise Kind/Action glossary directly in the review artifact; an operator inside another repository must not need to know that `docs/onboarding.md` exists in the ContextCanon repository.
- [ ] Reconsider whether `Action` should be independently editable at all. Current validation effectively derives one action from each kind (`promote`, `reference`, `keep`, `map`); the review UX should expose meaningful choices rather than a pseudo-choice that can only form one valid Kind/Action pair.
- [ ] Reduce rendered/source switching during review. Evaluate a separate source-file-first transformation review surface for Source After edits, grouped by original file/range and showing exact before/after plus every linked P-finding and final destination Node/content.
- [ ] Make cross-linked E-edits easy to audit for zero semantic loss: from one source edit, the owner should be able to see where each removed substantive meaning lands without chasing findings from unrelated parts of the document.

##### Normal authoring after onboarding

- [ ] Add first-class authoring ergonomics for new Rules/Topics after onboarding so humans do not have to invent or hand-maintain invisible `ctx:*` identity comments. Preserve stable IDs, but provide an explicit ContextCanon authoring/write command or equivalent safe mechanism that allocates the ID once.
- [ ] Document the minimal post-onboarding daily loop for ordinary projects: read `CONTEXT.md`, edit `CONTEXT.src.md`/Resources, build, check, and review Source updates when present.

##### Accepted semantic parent relationships

- [ ] Persist the human-accepted Step-03 parent/child hierarchy into the materialized Nodes as an explicit ContextCanon relationship. This must come from the reviewed semantic structure, not from filesystem nesting; repository directories alone still do not imply composition.
- [ ] Model the accepted semantic parent as a Source-like accepted package edge so a Child uses the exact accepted Parent snapshot. A later Parent change becomes a candidate and does not alter the Child until reviewed/accepted.
- [ ] Extend compiled inheritance from Rules to Topics. Today Rules compose transitively, while Topics are intentionally local-only; define package locator/resource semantics so accepted Parent/Source Topics and their Resources can be rendered safely in the Child.
- [ ] Render each Node's `CONTEXT.md` as the complete effective working context: all effective inherited + local Rules and all effective inherited + local Topics, with provenance and accepted-package boundaries preserved.
- [ ] Use the parent chain to make repository-wide workflow context practical. In `ai-workstation`, once the Development Workflow Source is correctly attached at the intended ancestor, descendants should receive that accepted workflow transitively instead of requiring the Source to be selected independently on every Node.
- [ ] Revisit Source update UX so projects can discover/fetch newer reusable Node packages without manually tracking remote package identities; updates must remain candidates requiring review/accept, never live implicit pulls.

Post-publish checkpoint: the owner set the current placement decisions to `accept` and completed real publication locally in `ai-workstation`. The resulting project is now being inspected as the first genuinely productive ContextCanon onboarding result. The known legacy owner-Source recovery defect from Block Q remained present, so this run may lack the intended Development Workflow Source; that is recorded test debt, not a reason to discard the published semantic placement.
'''

STATE_BLOCK = '''## Latest first production post-publish checkpoint

The real `ai-workstation` onboarding has now crossed the end-to-end boundary: the project owner accepted the placement review and completed publication locally, then began inspecting and planning normal work from the resulting Nodes. This is the first run where ContextCanon is being judged not only as an onboarding pipeline but as the project's ongoing working context.

The completed run exposed a clear next UX layer. Structure review needs the same visible edit affordance as placement review but with quieter markers; placement review needs an inline glossary of its editable decisions/kinds/actions; and Source After review is still cognitively expensive because source-file transformations can combine findings from distant parts of the destination-first review. A future source-file-first audit surface should show exact before/after text and direct landing destinations for every removed meaning.

Normal authoring also has an ergonomics gap: the executable source format currently requires compiler-managed stable IDs for Rules and Topics, so adding a new Rule by hand still requires a `ctx:rule` ID. Stable identity remains correct, but ordinary authors should receive a ContextCanon command/write mechanism that allocates those IDs rather than editing invisible bookkeeping manually.

Most importantly, post-publication inspection sharpened the semantic-parent requirement. The owner-accepted hierarchy from onboarding Step 03 should become an explicit accepted composition relationship rather than remain only onboarding structure metadata. This should not be implicit filesystem inheritance. The reviewed parent relationship should pin an accepted Parent package into the Child, letting the Child keep its previous effective context until a Parent update is reviewed and accepted. Existing compiler behavior already composes inherited Rules transitively, but Topics are explicitly local-only today; the next architecture block must define inherited Topic/resource package semantics and render the complete effective Rules + Topics in every Node's `CONTEXT.md`.

The known legacy in-flight owner-Source recovery defect remains deferred. The first real published `ai-workstation` run may therefore lack the intended Development Workflow Source. The fast-run stays ACTIVE while the owner inspects the published Nodes and the project transitions to a new chat; PR #13 remains draft/unmerged and requires explicit owner approval before any merge gate.
'''


def append_once(path: str, marker: str, block: str) -> None:
    p = Path(path)
    text = p.read_text(encoding='utf-8')
    if marker not in text:
        p.write_text(text.rstrip() + '\n\n' + block.rstrip() + '\n', encoding='utf-8')


append_once('PLAN.md', 'Block R — first production post-publish UX and parent composition findings', PLAN_BLOCK)
append_once('STATE.md', 'Latest first production post-publish checkpoint', STATE_BLOCK)
