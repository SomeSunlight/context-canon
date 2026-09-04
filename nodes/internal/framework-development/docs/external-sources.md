# Immutable external Sources

ContextCanon separates **semantic composition** from **Source transport**.

A consumer should be able to keep using an already accepted Source even when the Source repository is unavailable, has moved, or contains a newer version that has not been reviewed yet.

The core rule is therefore:

> Normal `contextcanon build` composes accepted state. It does not discover, download, or upgrade external Sources.

## The immutable compiled artifact

A reusable compiled Source is represented by an artifact containing:

```text
.context/package.json
CONTEXT.md
CONTEXT/              optional
```

`CONTEXT.md` and optional `CONTEXT/` are the human/agent-facing Official Context Package. `.context/package.json` is the portable machine manifest needed to reconstruct the Source's compiled semantic state without reparsing `CONTEXT.src.md`.

The manifest carries stable Node metadata, accepted transitive Source identities, complete effective Rules and provenance, removal provenance, local Changes and Topics, exact package-file hashes, `normalized_digest`, and `package_digest`.

The loader verifies both semantic identity and every declared package file before composition.

## Why two digests?

They answer different questions.

`normalized_digest` asks whether this is the same canonical compiled meaning. Collections whose order has no semantic meaning are canonicalized before that digest is calculated.

`package_digest` asks whether these are exactly the same published `CONTEXT.md` and `CONTEXT/` bytes.

A presentation-only change can therefore change `package_digest` without changing `normalized_digest`. Accepted external Sources pin both rather than collapsing the two identities into one ambiguous hash.

## Accepted package store

An accepted external package is stored under the consumer Node:

```text
<consumer-node>/.context/sources/<package-digest>/
├── .context/package.json
├── CONTEXT.md
└── CONTEXT/              optional
```

This directory is **accepted reproducible project state**, not a live cache of the Source repository. It should be retained/versioned with the consumer wherever a clone is expected to build offline without contacting external Sources.

A package is content-addressed by `package_digest`; its manifest is then independently checked against the Source's expected Node ID, version, `normalized_digest`, and `package_digest`.

Temporary update candidates live separately under:

```text
<consumer-node>/.context/candidates/<package-digest>/
```

Candidates are not inheritance. Merely fetching one cannot change a normal build.

## Pinned authoring syntax

A local development Source may remain unpinned:

```markdown
- [Python Development](../python-development/) — `1.2.0`
  <!-- ctx:source id="<python-node-id>" version="1.2.0" -->
```

This remains the simple local-development case.

An accepted immutable Source adds both exact digests:

```markdown
- [Python Development](https://example.org/context-nodes.git) — `1.2.0`
  <!-- ctx:source id="<python-node-id>" version="1.2.0" normalized-digest="<sha256>" package-digest="<sha256>" -->
```

The digest pair is all-or-nothing. For a pinned Source, the visible link is provenance/update location. **Normal build does not dereference it.**

## Git transport and multi-Node repositories

Compiler 0.5 provides a generic Git candidate transport. It is not GitHub-specific and uses the system `git` executable.

A Git-backed Source adds three transport fields:

```markdown
- [Python Development](https://example.org/context-nodes.git) — `1.2.0`
  <!-- ctx:source id="<python-node-id>" version="1.2.0" normalized-digest="<sha256>" package-digest="<sha256>" transport="git" ref="main" node-path="nodes/library/python-development" -->
```

The fields mean:

- `transport="git"` — use generic Git for candidate retrieval;
- `ref="..."` — accepted Git provenance. Current onboarding records the exact accepted commit SHA. Historical symbolic branch/tag refs remain supported as an explicit discovery ref;
- `node-path="..."` — location of this Context Node inside the retrieved repository snapshot. Use `.` for a repository-root Node.

All three transport fields are required together. `node-path` is location only; the stable Node ID remains identity. Absolute paths, backslashes, and `..` traversal are rejected.

Transport metadata is used for **updates of an already accepted pinned Source**. Initial onboarding may select reusable Sources through its reviewed placement path. Normal post-onboarding work also has one explicit first-adoption command when the human already knows the exact published package to compose:

```text
contextcanon source adopt <published-package-node> --node <consumer-node>
```

`source adopt` is the first-adoption decision itself; it is not an update shortcut. ContextCanon loads and verifies the exact package, requires its package path to be clean in Git, records the repository origin, exact current commit and Node path, validates the consumer's complete prospective composition in memory, installs the immutable package locally, then atomically adds one normal Source declaration. It does not touch or rewrite historical onboarding acceptance. If the same Source identity is already present with a different package, adoption refuses and the existing fetch/review/accept update path remains mandatory. Repeating adoption of the exact same package is idempotent.

A transport locator never bypasses exact package binding. This command is especially useful when a reusable Source is deliberately added after onboarding or when an old migration run lost a pre-`run-inputs.json` owner choice: recovery becomes a new explicit owner decision instead of pretending lost historical state can be inferred.

## First adoption after onboarding

When a reusable published Node is not yet a Source of the consumer, adoption is intentionally one explicit operation followed by the ordinary build/check loop:

```text
contextcanon source adopt <published-package-node> --node <consumer-node>
contextcanon build <consumer-node>
contextcanon check <consumer-node>
```

This is appropriate only for **first adoption** of an exact package the operator has deliberately selected. Subsequent changes to that Source use the reviewable update loop below. If the consumer is an ancestor in a semantic Parent hierarchy, descendants do not change live: review/accept the affected Parent edges from the ancestor downward so each child deliberately advances to a Parent snapshot that already contains the newly adopted Source.

## Fetch, review, accept

Source updates are deliberately three explicit operations:

```text
contextcanon source fetch <source-node-id> --node <consumer-node>
contextcanon source review <source-node-id> <candidate-package> --node <consumer-node>
contextcanon source accept <source-node-id> <candidate-package> --node <consumer-node>
```

### Fetch

`source fetch` explicitly performs update discovery. When `ref` is an exact accepted commit SHA (the normal current-onboarding form), discovery reads the repository's current default branch rather than cloning that old accepted commit forever. Historical symbolic refs are followed directly. ContextCanon enters `node-path`, loads and fully verifies the immutable package already published there, copies only that immutable artifact to `.context/candidates/<package-digest>/`, and records the exact discovered Git commit in a sibling `<package-digest>.git.json` provenance record.

It does **not** modify `CONTEXT.src.md` or `.context/sources/`. The moving remote branch is used only long enough to discover one candidate; the persisted candidate immediately becomes content-addressed package bytes plus an exact Git commit.

### Review

`source review` compares the currently accepted package with the candidate using the deterministic Context diff. It also substitutes the candidate into the consumer's actual Source composition in memory and checks structural consequences, including dangling local Changes and Rule collisions.

A successful review writes a deterministic receipt under:

```text
.context/source-reviews/<candidate-package-digest>.json
```

The receipt is bound to the exact current `CONTEXT.src.md`, the currently accepted Source state, the candidate package identity, the deterministic diff, successful structural validation, and — for Git-fetched candidates — the exact frozen candidate commit plus locator/node-path provenance recorded at fetch time.

### Accept

`source accept` requires the matching review receipt. It revalidates the candidate, its frozen Git provenance and structural composition, rejects the operation if `CONTEXT.src.md` or the accepted Source state changed since review, installs the candidate into `.context/sources/<package-digest>/`, and then updates the visible Source version plus exact digest pins in `CONTEXT.src.md`. Acceptance never contacts the remote repository.

For the current exact-commit transport form, `ref` advances from the previously accepted commit to the exact reviewed candidate commit. Historical symbolic branch/tag refs remain symbolic so their explicitly chosen discovery channel is preserved. In both cases the normal build still uses only the accepted local package bytes.

This cannot force a human to read a review, but it prevents the supported acceptance path from skipping the deterministic review step entirely.

## Normal daily update loop — KISS

Updating a reusable Git-backed Source is intentionally boring. Only the first command needs the Source repository/network; everything after it uses frozen local candidate bytes.

```text
# 1. Explicitly look for a newer published package.
contextcanon source fetch <source-node-id> --node <consumer-node>

# The command prints the content-addressed Candidate package path. Use that path below.

# 2. Review the exact frozen candidate against the currently accepted Source.
contextcanon source review <source-node-id> <candidate-package> --node <consumer-node>

# 3. Accept exactly that reviewed candidate when the diff is wanted.
contextcanon source accept <source-node-id> <candidate-package> --node <consumer-node>

# 4. Regenerate/verify the consumer as usual.
contextcanon build <consumer-node>
contextcanon check <consumer-node>
```

The important mental model is:

```text
remote moving state ──fetch once──> frozen candidate ──review──> reviewed snapshot ──accept──> accepted local package
                                           │                                              │
                                           └── never used by normal build                 └── normal/offline build uses this
```

No package digest needs to be invented or looked up by the operator: `fetch` discovers the package and prints its exact local candidate path. If the Source repository disappears immediately afterwards, review and accept still work from that path. After acceptance, `.context/candidates/` and `.context/source-reviews/` are scratch/review state; the durable offline boundary is `.context/sources/<accepted-package-digest>/` plus the exact pin in `CONTEXT.src.md`.

If no update is desired, do nothing. A newer remote commit has zero effect on `build` or `check` until this explicit loop reaches `accept`.

## Atomic publication and interrupted operations

Candidate and accepted packages are never published directly into their final content-addressed directories. ContextCanon copies them into a sibling staging directory, loads and verifies the staged package, and only then atomically replaces the final directory entry.

The canonical Source pin in `CONTEXT.src.md` follows the same principle: updated text is written to a sibling temporary file, flushed and `fsync`ed, then published with an atomic replace. A failure before the final replace leaves the previous Source file intact.

This creates a deliberate recovery boundary. If acceptance installs the new immutable package successfully but the final pin swap fails, the new package may remain in `.context/sources/` as **unreferenced immutable state**, while `CONTEXT.src.md` still points to the previous accepted package. A normal build therefore continues to use the old accepted Source rather than observing a half-applied update.

Regression coverage simulates failure exactly at that final replace and verifies that the original `CONTEXT.src.md` bytes remain unchanged, no temporary file remains, and the consumer still compiles against the old pin.

## One semantic composition path

Local and external Sources converge before Rule composition:

```text
local Source Node ──compile──> CompiledPackage ─┐
                                                ├──> Rule composition
accepted external artifact ──load/verify───────> CompiledPackage ─┘
```

Remove/Override behavior, diamond-conflict detection, provenance, and downstream normalized semantics therefore do not have separate remote implementations. Transport bugs cannot silently create a second composition language.

## Presentation order versus canonical semantics

The immutable artifact preserves effective Rule and Topic presentation order so a descendant built from a local Source and a descendant built from the same accepted offline package can render equivalent official context.

Canonical semantic hashing remains independently order-insensitive where order has no defined meaning. Hash-normalization sorting is not reused as package presentation order.

## Failure behavior

Normal build fails rather than fetching or guessing when the pinned accepted package is absent, malformed, has wrong files/digests, or disagrees with the Source ID/version/pins.

Git candidate fetch fails on unsupported/incomplete transport metadata, an unavailable ref, an invalid/missing `node-path`, a missing Git executable, an invalid immutable package, or a candidate with the wrong stable Node ID.

A missing accepted package is never permission for normal `build` to contact the Source locator automatically.

## Candidate updates are change requests

The complete update model is:

```text
accepted package
      +
Git-fetched candidate package
      ↓
deterministic Context diff
      ↓
consumer structural validation
      ↓
review receipt
      ↓
optional semantic/LLM impact review
      ↓
explicit acceptance
      ↓
new accepted package + new exact pin
```

A newer package is therefore a change request, not live inheritance. The deterministic review result is also the natural exact input to later LLM impact analysis.

## Current implementation boundary

Compiler 0.5 implements immutable manifests, full package verification, offline accepted-package composition, exact Source pins, deterministic package diff, review receipts, explicit acceptance, multi-Node Git addressing, generic Git candidate retrieval, staged package publication, atomic canonical-pin replacement, and exact-commit capture for update candidates discovered from a moving remote branch.

The current reviewed first-adoption onboarding layer can also propose an existing reusable Source from a verified catalog and bind that proposal through human review to the exact Node ID, name, version, normalized digest, and package digest that were inspected. Final onboarding acceptance requires the same immutable package again and then pins it into normal offline consumer state.

What remains unvalidated is primarily product/semantic experience rather than Source trust mechanics: the larger real-project test must show whether people and a strong reasoning model naturally recognize when project guidance should stay local, reuse an existing Source, or become a candidate reusable Node.
