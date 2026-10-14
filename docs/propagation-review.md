# Understanding a propagation review

`contextcanon propagate --all .` inspects changed normative Parent snapshots top-down. **It is not blanket approval.** Every Child keeps its accepted Parent package until you explicitly approve that Child (or deliberately invoke the existing automated `--yes` mode).

## Short review by default; details on demand

A normal `contextcanon propagate --all .` run shows a short decision for each changed Child: Parent version, recognizable changed documents, a limited actual before/after diff, and a brief statement of the effective Child change. Long UUIDs, digests, review receipt paths and the full checklist are hidden until requested.

At each prompt:
- **`y`** accepts the candidate Parent for **this Child only**.
- **`n` or Enter** rejects this step and stops the propagation run; earlier accepted edges remain unchanged.
- **`d`** displays the exact old and new paths, more diff lines, technical IDs, checksums and detailed review guidance, then asks **the same question again**. Looking at details is never approval.
- **`s`** prints the **short review again** after reading details; this works repeatedly, without accepting the Parent. The console scrollback is not erased, but the concise change and decision are back together near the prompt.
- Use **`contextcanon propagate --all . --verbose`** to display this material immediately on each review. `contextcanon parent propagate` supports the same option. `--yes` retains its explicit existing automation behavior.

For example:

```text
[1/8] aiw operator interface (bin)
  Parent: ai-workstation 0.2.1 -> 0.2.2
  Change: 1 resource changed
Changed Resources:
  docs/troubleshooting.md — content changed
    Topic: Troubleshooting guide · Origin: ai-workstation
    --- accepted Parent
    +++ new Parent
    ...
    +# small test entry - to delete after the test
  Effect here if accepted: 1 resource changed.
Accept the new Parent for "aiw operator interface"? [y/N/d=details]
```

The optional `d` output is also useful if the diff was shortened or the content was binary, missing or imported from another checkout. A later Child may say that this is the **same upstream change as review 1**, while still requiring separate consent.

### About automatic version increments

A changed Parent source can receive its automatic **minimum patch version increase before the Child review**. This is the Parent's local authoring/version housekeeping, **not acceptance by the Child**. If the operator declines, the Child remains pinned to the previous accepted Parent package. Review the working-tree Git diff if abandoning a test change.

## Read human evidence first

When a Topic Resource changes, the review names the **authored source** and, when available, the **origin Node and Topic**. A small unified text diff compares bytes from the Child's previous *immutable accepted Parent snapshot* against the live compiled Parent candidate. It shows actual removed (`-`) and added (`+`) lines; it is not a language-model explanation.

The prompt also gives:
- **Old accepted snapshot**: a path into the repository's retained immutable ContextCanon version store (or a verified legacy accepted package).
- **New authored source**: the original repository file (e.g. `docs/troubleshooting.md`), not a cryptic copied Resource name.
- **Repetition note**: when the same Resource identity, action, old content fingerprint and new content fingerprint appear in a later review, the prompt says which earlier review already displayed the diff. The later Child is still a separate decision, not a new authored edit.

Paths from older package formats may lack authored origin metadata; the prompt then reports the stored path or explicitly says origin information is unavailable. For binary, oversized, missing or non-UTF-8 content, ContextCanon says why it cannot show an accurate inline diff. In such cases inspect the old and new paths before accepting.

### Reading the repeated-change example

A root project edits `docs/troubleshooting.md`, which is a **Topic Resource**, not an informational `relationship=reference` import. Its new bytes change the root's exported normative package. The root's Children and grandchildren consequently encounter newer Parent snapshots. The later screens can describe the same originating document change even though each edge has a different Parent, version and review receipt.

A Resource's changed content is not automatically a changed Rule. The CLI's Rule `Override/Remove` mechanism cannot be used to suppress an arbitrary inherited Resource. If the authoring material is wrongly scoped, correct the upstream Topic or reconsider the appropriate Parent/Reference relationship explicitly; do not guess from a Resource ID.

## Safety and scope

The evidence presentation is read-only. It does **not** relax structural checks, immutable package validation, Parent pinning, multi-Parent conflict handling, top-down order or explicit per-Child approval. If a Child does not accept the update, it retains the previous Parent version; the remaining edges are left for a later propagation run. `--status` remains non-mutating.

After accepted reviews, use `contextcanon build --all .` and `contextcanon check --all .`. Reducing the number of required decisions and reducing duplicated generated files are **separate design work** under [Issue #121](https://github.com/SomeSunlight/context-canon/issues/121), not part of this change.
