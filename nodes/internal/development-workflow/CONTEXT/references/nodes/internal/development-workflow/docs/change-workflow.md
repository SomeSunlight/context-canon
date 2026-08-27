# Executing a ContextCanon Development Block

Use this when a ContextCanon change is being designed, implemented, resumed after interruption, or prepared for project-owner review.

The aim is **recoverability without ceremony for ceremony's sake**: the repository should always say what is being done and what is already complete, while expensive/repetitive verification is performed at the points where it adds confidence.

## 1. Put the block in PLAN before editing

Before changing implementation, context structure, or substantial documentation:

1. add a short subsection to the active area of `PLAN.md`;
2. state why the block exists;
3. list concrete checkboxes that are small enough to show meaningful progress.

Do not make the checklist a transcript of every command. It is a recovery map for the development intent.

## 2. Check off completed work immediately

When one listed step is actually complete, change its checkbox to `[x]` immediately.

A completed step should not remain unchecked merely because the whole block is unfinished. Conversely, do not check a step merely because editing started; include the verification that makes that step genuinely complete.

This gives a new human or LLM session a simple recovery procedure:

```text
read CONTEXT.md
→ read STATE.md when current position matters
→ read active PLAN.md block
→ continue at the first unchecked item
```

Chat history may add useful discussion, but it must not be required to reconstruct the active plan.

### Resuming after a short conversational interruption

In the current single-developer workflow, a short interruption in the chat does not by itself make the repository state suspect.

When the project owner returns after a short pause, explicitly says to continue, and does not report any intervening repository change, resume from the last established branch/PR state. Do not spend the next work window re-fetching the whole repository, PR and CI history merely to prove that nothing changed.

Re-check the exact mutable state when there is a concrete reason: the project owner reports another edit, GitHub rejects a write because the head moved, a tool result contradicts the last checkpoint, or the next operation itself requires an exact current identity.

## 3. Work in coherent edits, not micro-cycles

A full regeneration cycle for ContextCanon's own generated Context packages after every tiny wording edit is unnecessary.

For one coherent correction block, the normal flow is now:

```text
PLAN checkpoint
      ↓
related authoring / implementation edits
      ↓
focused deterministic tests / repository checks
      ↓
CI may expose known generated drift or another understood intermediate failure
      ↓
present one coherent review candidate
      ↓
project-owner review
      ↓
if corrections are requested → return to coherent edits
      ↓
if project owner approves the large line
      ↓
final self-hosted package regeneration / final cleanup
      ↓
exact-head CI: all tests + zero drift
      ↓
squash-merge to main
      ↓
post-merge accepted-baseline/state checkpoint
      ↓
next coherent development block
```

If a change introduces new deterministic behavior, test that behavior before relying on generated-package consistency checks. If several related documentation/context edits all change the same generated package, allow them to settle before regenerating that package.

The important distinction is that **review-ready and merge-ready are different states**. A successful merge is then followed by one small closure step because the merge itself creates facts that a pre-merge candidate cannot truthfully record.

## 4. What CI proves and what it does not

A green CI run proves that the tested deterministic contracts and committed generated output agree on that exact Git head.

It does **not** mean:

- the product decision is good;
- the documentation is pleasant to use;
- semantic LLM output is correct;
- the project owner approved the result.

Those remain human review questions.

During project-owner review, CI may therefore still be red when the remaining failure is understood and explicitly disclosed — for example, intentionally stale generated Context packages after authored context changed. Unknown failures still need investigation; "review can happen before green" is not permission to ignore unexplained breakage.

## 5. Keep obsolete CI work cheap

The GitHub Actions workflow uses concurrency cancellation. When a newer commit arrives on the same PR/ref, an older still-running test job is cancelled because it can no longer become the merge head.

This makes intermediate review work cheaper. The strict requirement moves to the **merge gate**: after project-owner approval, the exact head that is intended for `main` must complete the full deterministic suite and `contextcanon check --all .` with zero drift.

## 6. Review-ready boundary

A block can be handed to the project owner for review when:

- the intended product/documentation structure is present and understandable;
- completed PLAN items are checkpointed honestly;
- relevant focused tests have been run far enough to expose obvious implementation/repository mistakes;
- known CI failures or generated drift are explained rather than hidden;
- the PR description tells the reviewer what changed, what deserves attention, and what remains technical finalization.

The reviewer should be able to judge the **large line** without waiting for repeated generated-package regeneration that may be invalidated by the next review correction.

## 7. Merge-ready boundary

After the project owner explicitly approves the reviewed result, finish the mechanical publication gate:

- apply any final approved corrections;
- regenerate only the compiler-owned self-hosted package output affected by the final authored state;
- run the exact current head through the complete deterministic suite;
- require `contextcanon check --all .` at zero generated drift;
- inspect the final diff against `main` for accidental temporary/placeholder files;
- update the PR description with the exact merge-ready head, test count and relevant package identities.

Only then squash-merge to `main`.

Merge-ready is not the final recovery checkpoint. The merge creates new repository facts — most obviously the actual merged state and, for a squash merge, the final `main` commit identity — that could not be checkpointed honestly on the pre-merge branch.

## 8. Close the accepted baseline after merge

Immediately after a reviewed PR has been merged, and **before starting the next coherent development block**, reconcile the durable status surfaces that were necessarily written from the pre-merge point of view.

At minimum:

1. verify the actual merged PR/state from repository metadata;
2. mark the completed merge outcome in `PLAN.md` when the preceding block tracked it explicitly;
3. update `STATE.md` to the newly accepted baseline and next real focus;
4. update README project-status text and `CHANGELOG.md` when the merge made them stale or incomplete;
5. correct the merged PR description when it still contains live wording such as "open", "not merged", or "current review candidate" — preserve the historical review evidence, but make its final outcome unambiguous;
6. search the small set of status/navigation documents for the old branch name, PR status, or previous accepted-baseline wording so another stale surface is not silently left behind.

Keep this checkpoint narrow. It records facts created by the just-completed merge; it is not a place to start the next feature or to smuggle in a new semantic decision. If repository policy requires changes through pull requests, use a small dedicated checkpoint branch/PR. Such a bookkeeping-only checkpoint closes the **preceding product block** and does not need to create a recursive new product-baseline checkpoint for itself.

If the checkpoint itself discovers that a real product, architecture, or workflow change is necessary, stop treating that part as bookkeeping: record a normal coherent development block in PLAN and review it normally.
