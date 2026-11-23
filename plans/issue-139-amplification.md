# Issue #139 — measured self-hosted amplification and architecture boundary

Baseline: accepted `main` before PR #137 = `5a1f2bff24a9f6c6af49d96044eaf15b80d0d0b6`;
after the owner's squash = `359f7efe6b02d59b75d3c7e5ffedfa7ed9c9c99c`.
Both Git tree inventories and the 82 GitHub PR file records were counted, **not estimates**.
The logical change was one optional Development Workflow Resource, not a mandatory Rule.
No onboarding UX or #121 classification work is authorized here.

## PR #137 attribution (GitHub changed-file API)

| Artifact class | Changed tracked paths | Added lines | Deleted lines |
| --- | ---: | ---: | ---: |
| Immutable history (`.context/versions/`) | 55 | 8,677 | 4 |
| Four current Node machine files (`.context/`) | 12 | 217 | 80 |
| Four current `CONTEXT.md` | 4 | 43 | 7 |
| Four current Resource copies | 4 | 180 | 0 |
| Four authored sources/imports | 4 | 21 | 10 |
| Doc and PLAN edits | 3 | 60 | 0 |
| **Total** | **82** | **9,198** | **101** |

History: **54 added immutable artifact files** representing four entire newly accepted
Node packages, plus the modified generated versions README inventory. Of the 54 added
files, 38 were inherited or local Resource document copies; the remaining 16 were
four package manifests, four resource-origin records, four Official Context entries,
and four generated package READMEs. The historical diff alone accounts for
8,677 / 9,198 = **94.34% of added text lines**.

The new `external-github-publication.md` is 4,113 bytes. It appears at **eight
new generated paths** (four current + four historical), or 32,904 materialized
bytes, in addition to the one 4,113-byte human-authored original. All nine paths
share one Git blob SHA, `de7c0b2825d88637d69dcf228a422b650c44d915`.

## Two exact Git tree inventories

| Metric | Before | After | Delta |
| --- | ---: | ---: | ---: |
| Tracked blob paths | 749 | 808 | +59 |
| Tracked logical file sizes, sum of blob paths | 8,606,755 B | 9,183,552 B | +576,797 B |
| Unique blob SHA-1 identities across working tree | 319 | 331 | +12 |
| Sum of unique working-tree blob sizes | 4,191,564 B | 4,369,734 B | +178,170 B |
| Immutable-history blob paths | 452 | 506 | +54 |
| Immutable-history path sizes | 5,034,839 B | 5,578,667 B | +543,828 B |

The 59 *added* paths total 563,845 B, but represent only 33 distinct blobs
(390,705 B when counted once); of these 12 blobs, 172,611 B uncompressed,
were not already present in the pre-PR Git tree. Other new paths reuse older
blobs. This is **not** an estimate of compressed packfile growth: Git already
deduplicates equal blob objects, and the actual compressed disk delta depends
on `git gc`, packing, filesystem and checkout settings.

Important separation: a Git diff repeats added full-file *lines* for every
new immutable package path, even when the Git object store deduplicates the
identical bytes. Shared Git blob identity does not remove checkout file paths.
The four new accepted Node identities were triggered by normative Topic
propagation through three local consumers. Merely avoiding redundant writes
of unchanged existing files will not eliminate the 54 new history paths.

## Workstream A vs physical optimization

A solves an actual correctness defect without changing the package format.
The unpinned local Parent may advance while the Child still holds an old
accepted version. A verified previous Child publication plus the exact retained
Parent package supply a reproducible old binding. The existing live-Parent
candidate and explicit review remain the only way to advance. Never resolve a
missing or corrupt historical package by pretending the live Parent is accepted.
External pinned Sources remain strict.

Workstream A's candidate **does not reduce the representative #137 physical
diff**: with the existing v4 complete-package contract, the same authoring
change still creates four exact immutable versions and materializes each
necessary standalone package. A baseline-to-candidate reduction must not be
claimed without re-running that same case.

## Options and bounded decision for B

1. **Filesystem hard links or deduplicated Git blobs:** Git already reuses
   identical blob objects; hard links could change checkout disk use but leave
   the 82-path/9k-line review explosion intact. Windows links, editing and
   staging introduce integrity hazards. Not selected.
2. **Suppress descendant historical versions or remove copied Resources:**
   would weaken exact accepted Node versions and the self-contained offline
   Resource contract. Not selected.
3. **Shared content-addressed history Resource objects + immutable manifests:**
   can reduce historical paths and readable diff duplication, but changes
   `load_package`, consumer installation, package export, legacy migration,
   security checks and crash recovery. Requires a formal compatibility design
   and cross-platform prototype before production. No invisible indirection.
4. **Deterministic standalone history archives:** could drastically reduce
   file count, but Git can no longer present a readable per-Resource history
   diff without a dedicated viewer. All callers expecting directories need
   compatibility handling. Also requires a separate proof.

**Decision at this checkpoint:** keep exact v4 packages unchanged in the
correctness PR, avoid speculative storage rewrite. Make #135's separate storage
evaluation prove one of (3)/(4) on an isolated fixture with these same metrics:
Git paths, text lines, checkout bytes, unique Git blobs, readability, byte
identity, branch/merge, Linux/Windows, offline clones, migration and recovery.
A safe migration must preserve old v4 history and not alter onboarding's
user-visible state or operator steps. The owner retains the architecture gate.

## Exact real-graph correctness reproduction after the A fix

The automated [`scripts/reproduce_issue139.py`](../scripts/reproduce_issue139.py)
runs against **all six existing ContextCanon Nodes in an isolated Git worktree**
from the tested PR head. It edits *only the existing optional*
`nodes/library/development-workflow/docs/external-github-publication.md`
Resource, without manually adjusting any `ctx:source` version. Linux CI
[run 45219377649](https://github.com/SomeSunlight/context-canon/actions/runs/45219377649)
reports:

- Parent `0.3.10-draft → 0.3.11-draft`; read-only propagation status
  reports pending, and pre-review `build --all` writes no new accepted Child
  imports but returns exit code 1 (pending).
- **Three separate prompted yes decisions** advance the three direct
  Children. The fourth local edge (Foundation) remains normatively current.
  `build --all` and `check --all` both finish cleanly afterward.
- The scratch worktree's staged Git diff: **77 changed paths,
  +8,813/-96 lines**, with **54 newly added immutable historical files**
  from **four new accepted package identities**.
- The real graph also exposed a second bug absent from the original small
  fixture: adjacent Source entries could both match the second Parent's
  marker during acceptance. Stopping at the next import fixes this;
  targeted multi-Parent regression and the complete replay now pass.

This is a separate observed **Resource edit** whereas #137 added a previously
absent Resource, so 77 versus 82 paths is **not a measured storage
optimization**. Crucially, both cases still add **54 complete historical
artifact files**. Under the unchanged self-contained v4 contract, PR #140
corrects approval mechanics but does not reduce Git history amplification.
The measured B hypothesis and safe compatibility prototype are tracked in
[#141](https://github.com/SomeSunlight/context-canon/issues/141), separate from
#135's wider IDE visibility and encapsulation research. Any future approach
must measure a *paired identical* scenario with the old/current layout.

## Reproduction/validation commands for an independent checkout

```sh
# PR #137's exact accepted before and after trees:
git diff --stat 5a1f2bff24a9f6c6af49d96044eaf15b80d0d0b6 359f7efe6b02d59b75d3c7e5ffedfa7ed9c9c99c
git diff --numstat 5a1f2bff24a9f6c6af49d96044eaf15b80d0d0b6 359f7efe6b02d59b75d3c7e5ffedfa7ed9c9c99c
git ls-tree -r -l 5a1f2bff24a9f6c6af49d96044eaf15b80d0d0b6
git ls-tree -r -l 359f7efe6b02d59b75d3c7e5ffedfa7ed9c9c99c

# After branch implementation, reproduce the real graph and verify drift:
python scripts/reproduce_issue139.py
python -m unittest discover -s tests
contextcanon build --all .
contextcanon check --all .
git status --short
```

The GitHub API measurement can be repeated independently from the exact
commit tree URLs and PR #137 file-list endpoint. The baseline is intentionally
immutable; future B candidates should report *their own* before/after run,
not conflate an unrelated correctness-only PR with a storage optimization.
