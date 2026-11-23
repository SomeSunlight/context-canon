# ADR candidate — Issue #141: exact history identity with Git-tracked byte references

Status: **research candidate only; owner architecture gate OPEN** (2026-11-23). This is not a production-storage decision and is not permission to migrate or rewrite existing accepted v4 packages.

## Decision question and outcome

Prefer investigating **immutable exact bytes + compact references + on-demand materialization**, initially for *accepted historical packages only*. Keep human-authoritative CONTEXT.src.md, published CONTEXT.md/CONTEXT/, review decisions and all accepted Node/Parent identities untouched. A content-addressed, Git-tracked object pool with small immutable per-package references is the most promising next engineering candidate; a canonical standalone archive has lower path count but materially worse Git inspection/merge transparency. Neither has passed the owner compatibility gate. **Do not implement runtime storage changes in this research PR.**

Git already deduplicates identical blobs, so the principal intended win is fewer worktree paths and fewer repeated new-file diff lines, not a promise of lower Git pack bytes. Eliminating normative Child approvals is out of scope (#121).

## Grounded baseline: real #137 history, exact Git trees

Immutable baseline commits: before 5a1f2bff24a9f6c6af49d96044eaf15b80d0d0b6; after 359f7efe6b02d59b75d3c7e5ffedfa7ed9c9c99c. These are the *same logical Resource-addition* scenario. Current main after accepted #140 is 5e872f417a3a390dbd0b701506150dd8bcbef6c8; correctness changes in #140 are NOT a storage comparison.

| Metric | Accepted v4 #137 |
| --- | ---: |
| Total PR changed paths | 82 |
| Total text additions/deletions | +9,198 / -101 |
| History changed paths | 55 (54 added; 1 inventory modified) |
| History added text lines | 8,677 |
| New complete accepted package identities | 4 |
| Added historical blob paths and summed bytes | 54; 543,280 B |
| New distinct historical Git blob identities and summed sizes | 12; 172,611 B |
| New optional 4,113-B Resource | 8 materializations in current + history, plus one authored original |

Counts were independently recomputed from exact recursive Git tree API objects and 82 PR #137 changed-file records. The 12 genuinely new historical blobs are 4 package.json, 4 CONTEXT.md, 3 resource-origins.json and 1 Resource. Existing Git content reuse explains the physical/diff mismatch. See plans/issue-139-amplification.md.

**CAS analytical projection, NOT a measured production implementation:** if *all prior v4 history had first been represented as the same object store*, the exact same #137 delta would introduce **12 new unique byte objects + 4 per-package reference manifests**, rather than 54 complete historical paths; plus the already modified inventory (17 versus 55 history changes). Holding the 27 non-history paths fixed gives a **provisional 44 versus 82 changed-path bound**. This projection omits actual reference serialization size, any format-conversion migration, and changes needed for a correct browsing index; it must not be quoted as a passing implementation benchmark. New object bytes are 172,611 B before reference overhead, versus 543,280 B of materialized historical paths. Unique Git blobs will not fall just because their names change.

## Bounded local comparative prototype: synthetic scenario, not real-tree replay

Standalone reproducible prototype: prototype_issue141_storage.py (delivered with this handoff; not integrated into runtime). It constructs byte-identical v4 materialization for each candidate, compares actual temporary Git repositories before/after each identical synthetic workload, and measures Git diff, checkout, deduplicated blobs and packed repository size after git gc. It checks content-address corruption and missing objects. Its optional --repo mode reads exact before/after #137 commits via read-only git archive into temporary directories, without touching the checked-out source. **The real --repo mode and native Windows execution remain to be performed in a clone with those commits.**

| Synthetic four-Node addition | v4 directories | SHA-256 objects + refs | canonical tar | canonical tar.gz |
| --- | ---: | ---: | ---: | ---: |
| Changed tracked paths | 59 | 20 | 9 | 9 |
| Text added lines shown by Git | 2,682 | 243 | 8 | 8 |
| Binary diff paths | 0 | 0 | 4 | 4 |
| Full checkout bytes after | 167,962 | 42,368 | 317,556 | 8,270 |
| Unique checked-out blob bytes | 26,292 | 42,368 | 317,556 | 8,270 |
| Pack-size growth (git gc; small fixture) | +3,847 | +5,001 | +2,619 | +5,031 |

The small synthetic fixture models four new versions (plus four older retained packages) with history-file shape 8/9/8/29. It is **not** the actual #137 file data. Synthetic eight-edge fixture (eight new versions and eight independently changed authoring files) gives v4 **129 changed paths**, CAS **35**, tar/tar.gz **17**; these are **not** measured replays of the real #121 128-file case. Simulated review prompts are held at eight, not merged into one decision. Pack results are tiny and sensitive to Git version/gc/data; no universal pack-size advantage follows. Binary archive diffs showing few text lines are loss of reviewability, not an equivalent improvement in human-inspectable text.

## State, authority and lifecycle inventory

| Data | Authoritative? | Mutability / needed durability | Decision |
| --- | --- | --- | --- |
| CONTEXT.src.md, authored Resources, explicit import pins | Yes, human-controlled | ordinary editable, Git source | unchanged |
| Current CONTEXT.md, CONTEXT/, package.json | Accepted compiled publication | rebuildable *only with exact accepted inputs*, meaningful current inspection | unchanged; not casually disposable |
| Accepted exact v4 package history | Yes, as historical evidence | immutable by contract; clone/offline/branch persistent | retain untouched; candidate new refs must restore *exact original v4 bytes* |
| Origin mapping, Node/Resource IDs, normalized and package digests | Identity/evidence | authenticated by package, must survive restore | part of exact materialized v4 |
| Propagation/pending review receipts, decisions | review provenance / recovery | Git-retained if contract requires; ephemeral scratch only when proven | inventory separately; no silent deletion |
| Onboarding frozen Evidence, handoffs, reusable Parent packages, journals | may be acceptance and recovery authority | must preserve #117 durability, #135 onboarding freeze | no changes in #141 |
| Version README, projections, diagnostics, caches | mixed: regenerate only where source-of-truth exists | publication may be user-visible; caches can be transient | determine and document before reclassifying |
| Future external readonly original and interpretations | future separate authority domains | original immutable; interpretations replaceable/versioned; acceptance separate | leave capability open; no importer |

## Minimal candidate boundary

1. Persist each distinct **exact byte string** as one Git-tracked object, addressed by SHA-256 of the bytes (not a Git SHA-1, normalized text digest, or LLM semantic digest). Use explicit Git attributes -text so core.autocrlf cannot change the object in transit.
2. Persist one **immutable per-Node-version reference** containing the stable Node ID, exact v4 manifest identity and a sorted list of relative member paths, sizes and SHA-256. Use existing package_key identity (Node ID + normalized digest + package digest); refuse collisions, ambiguous duplicate names, symlinks, '..', absolute paths, absent or modified objects, unexpected extra package members and digest mismatches.
3. **Materialize on demand** into a temporary directory or bytes map, then run existing complete v4 load_package/load_package_files and ensure original exact file bytes, normalized digest, package digest, origin mapping and dependency pins validate. Standalone exported v4 packages remain exactly inspectable offline without the object pool. A reference alone is not a standalone package and cannot be advertised as one.
4. Publish objects first, verify and fsync according to platform, publish immutable reference last through atomic replacement; avoid valid-looking partial acceptance. On a crash, orphan byte objects are harmless but missing referenced objects are fatal until recovered. Never silently reinterpret the live Parent as accepted. Git staging/commit remains user-controlled.
5. **Dual read**: untouched legacy directory v4 first; future ref format only where explicitly present. Fail closed on same-key disagreement. No auto-conversion, forced re-onboarding, history garbage collection or branch-dependent mutable allocation ledger. Plan deterministic conflict handling for diverged branches; identical object SHA means identical bytes; a ref conflict is a real version conflict.
6. Historical browsing must switch to an explicit read-only inspect/export surface. The prototype intentionally does not rewrite current versions/README links; this is a **known incomplete compatibility requirement**, not a usable production reader.

A path example: .context/objects/sha256/60/4c769e... holds bytes for a Resource; .context/revisions/49f2e7ab082cfba5.json binds all v4 members. No Node has silently accepted the other Node's changes merely because a shared byte object exists.

## Why the other paths do not automatically win

- **Canonical tar/tar.gz:** self-contained, easy one-file export, 4 new archive files in #137's historical increment, but Git displays opaque binary diffs, no built-in per-Resource history review, independent archives repeat shared bytes before Git pack heuristics, and deterministic ordering/metadata, Windows paths, extraction hardening and corruption rules must be maintained. Compressed archives can be *larger* in Git packs even when checkout files are smaller. Worth maintaining as an export format, not automatically the authoritative Git storage.
- **SQLite / one large ledger:** introduces opaque branch/merge conflicts and crash/database maintenance inside the Git working tree without proving physical gain. Not selected by default.
- **Hard links / Git blob reuse:** identical Git bytes are already deduplicated; links cannot eliminate PR paths and risk accidental cross-file edits.
- **Drop descendant snapshots / strip Resources / lazy provider lookup:** violates accepted child identity, independently inspectable exact v4 packages, offline clones, and recovery.
- **Git object database as sole application store:** Git garbage collection, branch semantics, SHA format and tools become runtime dependencies; committed plaintext references do not ensure all required objects remain reachable as repository files. Do not rely on hidden filters or an external server.

## #135 IDE containment: what the architecture can, and cannot, solve

Moving 54 history paths to 12 content-addressed paths plus four refs reduces search results and edit targets, but **raw Git-tracked objects remain ordinary files**. Global IDE Find/Replace can still corrupt them. SHA checking detects drift but does not prevent it. File permissions, Git attributes, generated-file labeling and readonly filesystem bits are **not reliable cross-IDE editing protection**. Binary archives hide content from ordinary search but sacrifice textual inspectability; this tradeoff requires #135. Later options include keeping a clean Git-committed backing store outside ordinary IDE content roots, deliberate IDE indexing exclusions on supported IDEs, guarded export/inspect workflows and an integrity-check surface. Never claim #141 alone solves #135.

## Future readonly chats: no storage commitment, avoid a dead end

Three distinct identities: (A) **original raw chat bytes** with content digest and clear confidentiality/retention policy; (B) **independent interpretation records**, each with own version/method/model context and claim-level provenance to byte-range/message-ID plus segment checksum; (C) **explicitly accepted Context** with a separately recorded authority/pin. Multiple incompatible interpretations may coexist, be rejected, or be recomputed without modifying the original. Stable anchors must identify a concrete representation and offsets; line numbers alone are fragile when exporting chats.

Do **not** automatically commit private chats, prompts, credentials, excerpts, provenance anchors, or even sensitive hashes to the project Git history: Git deletion does not erase old commits or remote clones. Default to externally held readonly originals and local/private interpretations unless a user authorizes a public/project-persistent redacted or encrypted representation, with a proven portable key/recovery story. Confidential originals might never enter Git; therefore content-addressed *identification* is a portable concept but Git-backed *storage* must remain an optional policy. No chat importer, interpretation taxonomy or auto-acceptance in #141.

## Required owner gate before production

- Real **same #137 Resource-addition** replay from the exact two commits on v4, CAS and archives using the local prototype --repo mode, with actual counts, Git pack bytes, exact object and manifest size, and working history browse/export (not a projection). Preserve a machine-readable result fixture.
- Real **#121 eight-edge / 128-file** workload: recover the exact old/new ai-workstation commits or construct and explicitly approve an equivalent full repo fixture; don't relabel a synthetic shape as the actual case. Count independent prompts separately.
- Complete v4/v5 dual loader, exact existing digest tests, legacy/mixed/nested/partly onboarded projects, full and offline Windows/Linux clones including core.autocrlf=true, branch switch/merge, rematerialization, ambiguous/missing/corrupted objects, crash/retry and portability/path lengths. No converted v4, no deletion or pruning.
- Demonstrate useful human inspection after moving history; quantify search/IDE exposure in #135 separately. Preserve unchanged onboarding #117 workflow.
- Present measured simplification **including implementation/recovery cost**, then seek owner's architectural approval before an implementation PR or actual migration. If gains do not justify the new reference format, retain v4.

## Scope allocation

- **#141:** measured physical history representation, exact byte/identity restoration, Git/offline compatibility and safe optional dual read.
- **#135:** IDE isolation, Find/Replace prevention, ordinary discoverability versus explicit readonly inspection, storage visibility across onboarding and caches.
- **#121:** Context classification, policy/acceptance distribution and whether eight separate semantic decisions are justified; *never infer consent from shared storage*.
- **Future separate issue:** read-only external originals, confidential chat persistence policy, independent interpretation/version/provenance, explicit Context promotion. This ADR only preserves the design separation.

Research branch contains no runtime modification and is not authorized for automatic merge.
