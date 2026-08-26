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

## 3. Work in coherent edits, not micro-cycles

A full ContextCanon dogfood cycle after every tiny wording edit is unnecessary.

For one coherent correction block:

```text
PLAN checkpoint
      ↓
related authoring / implementation edits
      ↓
focused deterministic tests / repository checks
      ↓
CI exposes the exact generated drift once
      ↓
regenerate exactly that dogfood output once
      ↓
exact-head CI: all tests + zero drift
      ↓
project-owner review
```

If a change introduces a new deterministic behavior, test that behavior before relying on dogfood. If several related documentation/context edits all change the same generated package, allow them to settle before regenerating that package.

## 4. What CI proves and what it does not

A green CI run proves that the tested deterministic contracts and committed generated output agree on that exact Git head.

It does **not** mean:

- the product decision is good;
- the documentation is pleasant to use;
- semantic LLM output is correct;
- the project owner approved the result.

Those remain human review questions.

## 5. Keep obsolete CI work cheap

The GitHub Actions workflow uses concurrency cancellation. When a newer commit arrives on the same PR/ref, an older still-running test job is cancelled because it can no longer become the review head.

This does not weaken the final gate: the exact head handed to the project owner still has to complete the full deterministic suite and `contextcanon check --all .` with zero drift.

## 6. Review and merge boundary

Before calling a block review-ready:

- every intended PLAN item for the block is `[x]`, except the explicit project-owner review/merge items;
- documentation matches implemented behavior;
- relevant generated packages were regenerated from the compiler rather than hand-edited;
- the exact current head has green CI and zero generated drift;
- the PR description identifies that exact head and the verification result.

Keep the PR open until the project owner explicitly approves it. Merge only after that approval.
