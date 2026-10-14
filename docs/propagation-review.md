# Understanding a propagation review

`contextcanon propagate --all .` inspects changed normative Parent snapshots top-down. **It is not blanket approval.** Every Child keeps its accepted Parent package until you explicitly approve that Child (or deliberately invoke the existing automated `--yes` mode).

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
