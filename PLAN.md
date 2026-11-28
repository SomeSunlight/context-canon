# Plan

## Target architecture research — #144 / #121 / #123 / #124 / #135 / #141 (2026-11-24)

Research and owner decision only. Preserve the successful official Context contract and the entire onboarding flow. No production code, package rewrite, project migration, automatic merge or new storage/schema commitment is authorized.

Accepted main at `5e872f417a3a390dbd0b701506150dd8bcbef6c8` includes owner squash of #140; the pre-merge handoff below is historical. #139 is closed, #134 remains open pending its separate closure verification. #141 and Draft #142 remain research, not accepted production storage. No changes to their branches.

- [x] Inventory actual main source, compiler/model/package boundaries, onboarding implementation/documentation, active-run/version migration, planning and related issue decisions; identify verified facts versus open experiments.
- [x] Record recommended domain model, alternatives, migration/onboarding parity contract, staged gates and E2E exercise in [target architecture research](plans/issue-144-target-architecture.md).
- [x] Link the research checkpoint from #144 and coordinate #121/#123/#124/#135/#141 without closing or superseding existing requirements.
- [x] Capture owner refinement: decentralized Hdez, rebuildable new engine, one live accepted contract per relationship/aggregate, Git history rather than all historical copies, one-time conversion instead of permanent dual runtime; no active onboarding runs.
- [x] Record owner refinement: direct human Hdez editing plus small LLM/programmatic write interface, reimport/rebuild, rule/acceptance/validation/State round trip as a first-prototype gate.
- [x] Owner approved internal separation of Snapshot Engine, Dependency Core, ContextCanon and optional Artifact Tracker; record architecture boundaries, preferred YAML/sealed-object candidate, staged transition and explicit multi-project CONTEXT.src.md round-trip acceptance in section 0A.
- [x] Record newly identified change-management gap and initial external research (NASA, FAA, IBM DOORS, NIST, engineering change propagation), with candidate work-package/closure model explicitly open in section 0B.
- [ ] Review change-management approach with owner, resolve acceptance/implementation/verification distinctions (#121), select bounded real-project fixtures and authorize prototype. No code yet.
- [ ] In disposable copies only, characterize multiple real-project source/effective baselines; prove independent snapshot seam then one-time Hdez conversion/new engine, regenerated CONTEXT.src.md and CONTEXT.md parity, owner review, exact historical recovery and manual/programmatic write/rebuild.
- [ ] Prove independent dependency core with actual Hello World Extended file relations and real Parent update; then grouped change-case proof with actual verification, closure, stale evidence, interruption, exceptions and no unnecessary cascades; compare #121 real replay and user burden.
- [ ] Prove fresh twelve-step onboarding, native Windows/Linux, offline/branch/recovery and owner multi-project source/effective parity. Separate approval before production switch and legacy runtime removal; no permanent dual authority.
- [ ] Consider remote scopes/reporting, HTML interactivity and standalone packages only after demonstrated need; no automatic merge or production migration.


## Priority A — local unpinned Parent propagation: handoff to owner (#134 / #139, 2026-11-23)

**Current disposition:** [PR #140](https://github.com/SomeSunlight/context-canon/pull/140) implements Priority A, is ready for the owner's **squash-merge**, and is not yet merged. The owner has accepted the automated/real-graph evidence as a practical alternative to repeating a complex manual reproduction inside self-hosted ContextCanon. Operational monitoring after merge is sufficient for now; it is **not** a claim that future regressions are impossible.

Accepted base remains `main` at `359f7efe6b02d59b75d3c7e5ffedfa7ed9c9c99c` (owner's squash of #137). This checkpoint is a PR-branch handoff, **not** an already accepted main checkpoint.

- [x] Identify and correct the local unpinned Source-version deadlock: compile a Child against the byte-verified historical Parent identity already recorded in its verified last publication, and discover the changed live Parent for explicit review. Missing or altered history fails closed; external pinned imports remain strict.
- [x] Fix adjacent local Source entry marker lookahead exposed by the real six-Node reproduction. Do not bind an import to metadata belonging to the next import.
- [x] Preserve separate decline/accept/partial-resume behavior and exact adopted identity, auto-bump semantics, offline verification and onboarding's user-visible behavior. Report pending normative propagation from `build --all` rather than silently calling it complete.
- [x] Test eight new focused regressions plus the complete six-Node self-hosted Resource-edit reproduction in a **disposable** Git worktree. Three direct Child approvals, four graph edges, and zero generated drift after acceptance.
- [x] Pass the exact-head [Linux and native Windows CI run #45220263243](https://github.com/SomeSunlight/context-canon/actions/runs/45220263243): **509 Linux tests, 119 native Windows tests**, real-graph reproduction, generated drift check, both jobs green at `aed97dc9a0e96ff9952a57392dc5c6afb51b967b`.
- [x] Measure PR #137: 82 changed paths, +9,198/-101 lines, including 54 new immutable version files. The real Resource-edit reproduction yielded 77 changed paths, +8,813/-96 lines, again 54 historical files. These are *different logical changes*, **not** evidence of storage savings; see [the quantified report](plans/issue-139-amplification.md).
- [x] Separate Priority B instead of changing storage or weakening historical identity in this PR: [#141](https://github.com/SomeSunlight/context-canon/issues/141) is the bounded cross-platform storage prototype; [#135](https://github.com/SomeSunlight/context-canon/issues/135) retains the wider visibility/IDE problem. No #121 governance/classification changes here.
- [x] Owner agreed that the focused fix may be accepted on this evidence and assessed in ordinary future usage instead of attempting a further manual reproduction.
- [ ] **Final handoff:** latest commit's hosted Linux/Windows gates green; owner performs the squash-merge of PR #140. Do not merge automatically.
- [ ] **After the merge only:** record the resulting squash SHA and acceptance in `STATE.md`; close #134 after verifying the merged result, and close or re-scope the combined #139 while retaining #141/#135 for Priority B. Avoid further A changes unless a concrete regression appears.

**Scope stop:** Priority A is finished for owner review. No speculative storage migration, new propagation-governance policy, broad Find/Replace protection, or onboarding redesign in this PR. Subsequent architectural discussion begins from #141/#135 as separate work.

## Optional external GitHub publication best practice — Issue #136 (2026-11-23)

Purpose: capture a successful operator-owned `gh issue create` fallback when the connected GitHub App cannot post to an external public upstream repository. This is guidance, **not a new mandatory Rule**, and is evidence for the classification work in #121.

Writable scope: Development Workflow `CONTEXT.src.md` optional Topic, `docs/external-github-publication.md`, docs index, PLAN checkpoint, and the compiler-generated packages plus reviewed local Source version references in its three in-repository consumers. Never edit generated machine manifests directly; preserve immutable historical packages.

- [x] Verify upstream publication at [NVIDIA/NemoClaw #14784](https://github.com/NVIDIA/NemoClaw/issues/14784) and record the non-binding guidance decision in [#136](https://github.com/SomeSunlight/context-canon/issues/136).
- [x] Add an optional Topic and human-readable publication guide; link the guide in the Development Workflow docs index.
- [x] Supply the real-world classification example to [#121](https://github.com/SomeSunlight/context-canon/issues/121), without implementing any new schema.
- [x] Review the proposed best practice in PR #137, including its deliberately non-mandatory status.
- [x] Build new Topic/Resource IDs; use documented #134 manual local Source version update for Framework Development, GitHub and GitHub Local; regenerate all affected packages. `contextcanon check --all .` passed 6 Nodes and all 4 Parent/Child edges. Exact published head `74745a2` passed Linux/full suite plus generated drift and native Windows portability (Actions run 45202352252).
- [x] Owner squash-merged PR #137 into main at `359f7efe6b02d59b75d3c7e5ffedfa7ed9c9c99c` (2026-11-23). Coordinated follow-up: [#139](https://github.com/SomeSunlight/context-canon/issues/139).

## Version provenance and opt-in GitHub check — Issue #130 (2026-11-07)

Purpose: identify the exact installed ContextCanon commit from a uv Git URL, and compare it on demand with the corresponding GitHub branch without ever making \`--version\` network-dependent.

Writable scope: \`src/contextcanon/version.py\`, new \`src/contextcanon/version_check.py\`, CLI integration, focused tests, README, Development Workflow authored provenance guide plus only its necessary reviewed generated packages/accepted pins, CHANGELOG and these PLAN/STATE checkpoints. Separate downstream tool Issues follow the reusable guide's publication; #131's architecture decision remains independent.

- [x] Extend #130 with the owner's opt-in check contract and inspect github-local's working PEP 610 implementation.
- [x] Implement installed commit provenance and explicit read-only remote Git history comparison, including safe unknown status.
- [x] Add focused regression tests for offline \`--version\`, VCS metadata, ancestry directions, override/default branch and failures.
- [x] Update Development Workflow's reusable pattern and ContextCanon user documentation.
- [x] Regenerate/review self-hosted Context packages, author all three local consumer pins in Markdown, and confirm all four accepted Parent relations via `contextcanon check --all .`. Workflow 0.3.9-draft; Framework 0.3.26-draft; GitHub 0.1.10-draft; GitHub Local 0.1.9-draft. One exact historical package byte was restored from a hash-verified donor (#133); the temporary branch-only regeneration CI workflow was removed.
- [ ] Pass exact-head Linux/full and native Windows tests, plus generated drift check, and present PR #132 for owner review.
- [x] Create downstream version-contract Issues: github-local #25, Llama_Dispatcher #33, ai-workstation #56, ConfluenceBridge #2, teams-chat-exporter #2; defer adoption until the accepted Development Workflow is published. Track the local Source/Parent propagation limitation separately in context-canon #134.
- [ ] Owner approval and merge; post-merge accepted baseline checkpoint.


## Active review block — resilient filesystem cleanup (#127)

Purpose: Windows may leave recursively fileless directory skeletons after cleanup/branch operations; these must not block later builds. Define one reusable Development Workflow method, preserve strict immutable package integrity, and make ContextCanon build retry deletion of harmless tool-owned leftovers.

- [x] Record [Issue #127](https://github.com/SomeSunlight/context-canon/issues/127) and scope the cross-platform method.
- [x] Author the Development Workflow Rule/Topic and filesystem-cleanup reference under the owning Node.
- [x] Add shared best-effort directory helper, safe orphan classification, build cleanup, and regression cases.
- [x] Explicitly stage Development Workflow 0.3.8-draft in all three in-repository normative consumers for owner review (no downstream repository pins changed).
- [x] Run complete unit tests and regenerate official Context via `contextcanon build --all .` using the actual compiler, review/commit generated artifacts, propagate the newer Development Workflow Parent with explicit acceptance, and verify exact-head `check --all .` before merge.
- [ ] Owner review and merge approval; then close the accepted-baseline checkpoint.



## Human-first propagation evidence — Issue #120 (Fast Track, 2026-10-14)

**Owner explicitly approved Fast Track.** Goal: turn the repetitive eight-edge `ai-workstation/docs/troubleshooting.md` propagation into informed, human-scale approvals with recognized origin/path, exact before/after differences, and repeated-change orientation. No intermediate product-review stops; present one coherent PR candidate to owner when ready. **Do not merge without owner approval** and require exact-head green checks before any owner-approved merge.

**Writable scope:** `src/contextcanon/cli.py` (presentation/orchestration only), focused new pure renderer `src/contextcanon/propagation_evidence.py`, `tests/test_propagation_review_ux.py`, `tests/test_configuration_and_update_ux.py` and `tests/test_version_store.py` (only assertions invalidated by the new default output), `README.md`, new standalone user guide `docs/propagation-review.md`, `CHANGELOG.md`, `PLAN.md` and review-only `STATE.md` if recovery facts require it. Editing the already-published normative `docs/maintenance.md` Resource is deferred to a separate coherent self-hosted regeneration, avoiding unrelated generated-package churn in this UI-only Fast Track. Exclude version/pin/receipt formats, compilation, storage, new propagation policy, explicit Resource/Topic scope changes, regenerated package content unless unavoidable and separately documented. Issue #121 owns semantic cascade/storage design.

- [x] Reproduce owner mental-model failure from 8-step uploaded `propagate --all` log: same root Resource ID appears at each of eight reviews; absent paths, old/new content and clear repeated origin.
- [x] Inspect existing human review renderer, Resource identity/origins, immutable package Source/Parent snapshots, and relevant test fixtures.
- [x] Implement deterministic review evidence from verified old/new packages, including origin Node/path/Topic when known, changed bytes with bounded real text diff, missing/binary/truncation evidence, and a concise repeated-upstream trail; new pure presenter in `src/contextcanon/propagation_evidence.py`.
- [x] Correct Rule-specific Override/Remove guidance for Resource-only changes without changing per-edge confirmations, `--yes`, status, receipt or accepted-pin code.
- [x] Add focused tests for original Resource content change through two generations, same-origin suppression, binary fallback and Resource move. Complete Linux and native Windows CI both passed on implementation head `a99efee4696bd8e8bc9628924b62d8923790f215`: [Validate run 38609647565](https://github.com/SomeSunlight/context-canon/actions/runs/38609647565).
- [x] Document review reading order and exact paths from README and new `docs/propagation-review.md` without changing the self-hosted Gateway's already-published mandatory `docs/maintenance.md` Resource; update CHANGELOG. Any later consolidation into that Reference-managed guide must regenerate published Context with its own coherent review. Hosted CI passed on the code/docs head.
- [x] Create [PR #122](https://github.com/SomeSunlight/context-canon/pull/122) for owner review and practical testing; both Linux and native Windows jobs passed on the actual reviewed code/docs head `a99efee4696bd8e8bc9628924b62d8923790f215` in [run 38609647565](https://github.com/SomeSunlight/context-canon/actions/runs/38609647565). This PLAN-only record commit does not modify executable behavior.
- [x] **Fast Track exit:** one coherent tested review candidate published. Return to ordinary owner review / exact-head merge gate; no automatic merge.
- [x] Owner tested a real `docs/troubleshooting.md` Resource edit from ai-workstation and confirmed the evidence is technically correct; feedback: excessive repeated explanatory prose and unsolicited UUIDs/hashes separated the diff from the actual approval. This triggers a focused in-PR readability refinement (same Issue #120).
- [x] Refine the default into a compact change/diff/effect/prompt flow, offer `d` to inspect the complete existing review evidence before deciding again, and add a `--verbose` flag for both propagation entrypoints. Keep `--yes`, status, Parent pins and receipts unchanged; clarify Parent automatic patch bumps before Child acceptance.
- [x] Owner tested the compact view on real ai-workstation 0.2.1 → 0.2.2: concise document diff and interactive `d` work. Owner feedback: `Effect here if accepted: 1 resource changed` is a redundant count, not a human explanation; after `d`, provide a way to return to the concise card.
- [x] Add precise, evidence-bound plain-language Child impact for single, unchanged-through-inheritance Resource changes; use a safe general fallback for more complex or mismatching effective diffs. Add `s` = reprint short review at every confirmation prompt, allowing `d → s → y/N` without accepting accidentally.
- [ ] Verify this final refinement with focused regressions and native Windows/Linux CI; then hand off the exact review branch for owner retest on the same pending AI Workstation change. **No merge without approval.**

**Baseline:** start from current `main` after owner has merged unrelated AI Workstation #32. Avoid speculative changes to ContextCanon accepted packages. Framework's existing CC-001/002/003/005/007/011 and CCI-001/005/013 apply.


This is the recovery index, not the implementation diary. Read [STATE.md](STATE.md) for current facts, then the linked detail plan for the work you are doing. Check off completed detail items immediately; keep older checkpoints in the archive.

## Git line-ending guidance (#112) — 2026-10-08

Accepted baseline: the owner squash-merged #114 as `25553e6`. Earlier #114 review status below is historical. Purpose: answer the Windows/WSL migration question from current code and document the exact-byte boundary before users normalize existing repositories. This is a bounded documentation contribution to open #112, not implementation of its general publication/transport policy.

Writable scope: README.md, docs/line-endings.md, CHANGELOG.md and PLAN/STATE recovery checkpoints. Keep runtime, package formats, generated output, existing frozen bytes, accepted pins and repository Git settings unchanged.

- [x] Trace raw Evidence hashes/sizes, live acceptance checks, package digests, Resource copying, source text parsing and exact output drift; confirm the limited legacy Git-history recovery is not general EOL tolerance.
- [x] Verify LF/CRLF/mixed Evidence and package behavior plus the proposed Git attributes in temporary repositories, including nested Nodes and both checkout directions. All three frozen variants validate unchanged and reject EOL-only edits; source semantics stay equal and generated CONTEXT.md reports drift. Eighteen real Git commit/checkout combinations preserve root/nested exact bytes with the LF policy and Windows authoring overrides.
- [x] Add a brief README section and detailed migration/Git-attribute guidance, including working-tree versus index behavior, ongoing/completed onboarding and exact recovery limits.
- [x] Verify documentation links, generated consistency and relevant existing regressions; prepare a review candidate that references #112 without closing its remaining transport scope. All 69 relevant existing tests pass, all six self-hosted Nodes have zero drift and all four normative edges are current. An additional 54 complete-package loads pass after real Git round trips. Publication/hosted CI and owner review remain live PR metadata; leave merge to the owner.

## Complete source authoring usability (#115 / #89; expands #114)

The owner clarified the missing original scope on 2026-10-08. Extend the open Resource-Why PR #114 on `agent/issue-113-resource-notes`; do not merge. Accepted main remains `d0a9db3d3b0d1cc1dfce32caadf2a52b1eb5ae80`; the green Why-only candidate is `3a505f9f7de6226fa2ec213b910cec617c4db9a0`.

Purpose: every new/existing CONTEXT.src.md must explain its authoring contract. The owner's explicit request authorizes normal build to migrate source-only orientation, marked format help, import placement, trailing identity/provenance markers and missing stable IDs for valid new Rules/Topics/Resources. This narrowly supersedes the older no-source-write build convention. Never infer malformed prose, change Parent/Reference meaning, reallocate existing identity, alter accepted pins or mutate frozen packages. check remains read-only.

- [x] Add shared source-only authoring help/diagnostics, a visible format-guide link, section examples and a complete root documentation/README entry. The distributed guide is bundled for offline use; root documentation exposes the complete same contract.
- [x] Implement idempotent build migration across the selected Nodes: Imports first, help refresh, trailing placement markers, allocate missing IDs once, validate before writing and preserve user bytes/meaning outside the narrow authoring changes. Candidate diagnostics point to the original unchanged file; all selected candidates compile before any source write, with rollback/concurrent-edit/ownership checks.
- [x] Apply the same layout/help to onboarding skeletons, compatibility publication and reviewed placement preview/publication; keep managed blocks and frozen/review state compatible. Existing 451 tests and 53 focused authoring/onboarding tests pass; final full-suite verification follows the last review changes.
- [x] Regress existing/new/nested/offline Nodes, parent/reference pins, missing-ID authoring, invalid Rules/Topics/Resources, help isolation, State/Plan identity placement, idempotence, failed writes and onboarding contracts; run complete tests and document real migration usage. All 475 tests pass, including 22 source-authoring regressions and updated onboarding contracts. The installed wheel also completes offline build/migration/check with bundled guidance.
- [x] Prepare the expanded Draft #114 with recoverable implementation/regeneration checkpoints and complete local verification. All six self-hosted sources are migrated; repeated build makes no changes, check reports zero drift and all four normative edges are current. Exact published-head hosted Linux/Windows proof and owner-review status are live PR metadata; no status-only commit should invalidate that head. Leave owner review and merge as explicit gates.

Native Windows first exposed a fixture alias issue: RUNNER~1 and the resolved runneradmin directory were compared as different Paths, so two injected write/concurrent-edit failures were not triggered. Resolve the temporary repository once in the fixture so the rollback tests exercise the intended failure on both platforms. Product migration already resolves all roots; no product/package change is required. The corrected candidate must pass fresh exact-head Windows as well as Linux evidence in #114.

## Resource target notes (#113)

Accepted baseline: the owner squash-merged Phase 2 as `d0a9db3d3b0d1cc1dfce32caadf2a52b1eb5ae80` (#111). The older Phase-2 preparation blocks below are historical. Resource notes are a separate review branch, `agent/issue-113-resource-notes`; Topic inheritance visibility remains deferred.

Purpose: add an optional indented single-line `Why:` below each Resource target, following the owner's preference for explicit syntax. Preserve explanations through rendering, immutable packages, composition, review and Resource maintenance. VALID/OBSOLETE are ordinary text, not status enums or Required/Optional control. Existing syntax and unannotated package identities stay compatible; arbitrary trailing prose remains unsupported.

- [x] Implement Resource-only Why parsing, typed/package preservation, rendering, review identity and register/move/reconcile preservation. Before documentation edits, all six self-hosted Nodes still have zero generated drift and all four normative edges remain current, proving unannotated output compatibility.
- [x] Cover the reported mixed identified/path-only targets, malformed syntax, offline Parent/Reference packages, Why-only review changes and Resource lifecycle. Seven focused regressions pass, including metadata before/after Why, canonical target reordering, registration idempotence, explicit move and external rename reconciliation.
- [x] Document syntax and prepare a separate Draft PR: all 451 deterministic/repository-consistency tests pass, including seven new regressions; diff hygiene is clean. Expected generated drift is confined to Foundation and Framework Development copies of the two edited syntax guides. All four normative edges remain current. Regeneration follows owner review; no merge is authorized.

The owner authorized finalization on 2026-10-08. No merge is authorized; leave the squash merge to the owner.

- [x] Regenerate Foundation at `0.2.5-draft` and Framework Development at `0.3.23-draft`, advance the explicit local Foundation import and retain both previous immutable publications. All six Nodes now have zero generated drift; all four normative edges are current.
- [x] Pass all 451 deterministic/repository-consistency tests, zero generated drift for six Nodes, current normative state for all four local edges and diff hygiene. Final candidate is prepared for publication. Exact-head hosted Linux/Windows evidence and PR readiness are live metadata in #114; mark ready only after both jobs succeed, without a status-only commit that invalidates the verified head.

## Phase-2 owner acceptance and merge preparation (#107 / #111)

Purpose: the owner confirms successful real migration and orderly short paths, accepts the result for main, and explicitly defers a new end-to-end onboarding to the next real adoption. Record that precise test boundary in PLAN/STATE, the Phase-2 plan and backlog; prepare PR #111 for the owner's squash merge. Future onboarding findings belong in new Issues. No executable, packaged Resource or release-version change belongs to this closure.

- [x] Record successful migration/path validation and owner acceptance without claiming a fresh end-to-end onboarding test.
- [x] Reconcile the current planning surfaces and verify documentation links (all four repository-consistency tests pass), zero generated drift for six Nodes, all four normative edges current and diff hygiene before publishing the closure.

Exact-head Linux/Windows CI and PR readiness remain live PR metadata. Keep #107 open until the merge closes it. After the owner's squash merge, record the actual accepted main commit in the baseline checkpoint; do not merge on the owner's behalf.

## Active owner-test correction — preserve unbound IDE metadata (#107)

Purpose: the reported STEP-04 extras are JetBrains `.idea/` files, including its own `.gitignore`. The owner wants ordinary IDE metadata to stop blocking ContextCanon. Existing handoff PLAN already excludes post-preparation `.idea/`/`.vscode/` from Evidence. Inventory respects Git standard ignores for untracked files; migration cannot use Git ignores as an ownership boundary because complete managed workspaces/runs are ignored too.

- [x] Exclude unbound `.idea/`/`.vscode/` metadata at workspace/task roots from migration inputs, copying and retirement; preserve those paths in place and report them. Explicitly bound Evidence/Parent/control/result bytes and isolated immutable packages stay fully verified; other unknown files still refuse.
- [x] Preserve metadata during interrupted package install/copy/retirement, including IDE edits/new files during recovery. Keep ownership/path/symlink protections for governed inputs and avoid treating arbitrary Git-ignored files as harmless.
- [x] Regress root/subtree and STEP 04/08 metadata, existing destination metadata, immutable/bound tampering and unrelated ignored files; all 32 migration tests pass and owner guidance/checkpoints are updated.
- [x] Regenerate the two self-hosted packages affected by the packaged owner-guide update (Gateway `0.3.23-draft`, Framework Development `0.3.22-draft`), retain their previous immutable versions, and repeat the complete local gate: 444 tests pass, all six Nodes have zero drift and all four normative edges are current. The implementation already passes 444 Linux and 82 native Windows tests on `06adaed`; its hosted failure was only the stale guide copies. Fast-forward publication and fresh exact-head Linux/native Windows proof remain live PR metadata; owner retries preview/apply without moving IDE files.

## Active owner-test correction — handoff file diagnostics (#107)

Purpose: the owner's migration in Itop now refuses `unknown/missing handoff files` without identifying the task or files. First make this refusal actionable without assuming its cause or claiming/deleting unrecognized content. Preserve frozen inputs, review decisions and result bytes; distinguish unknown files from missing required files and report STEP/root paths.

- [x] Report sorted unknown and missing relative paths, selected handoff STEP/root, unchanged-state assurance, and distinct preserve/report versus restore guidance.
- [x] Regress root/subtree, STEP 04/08 and preview/apply with unknown/missing/mixed files; preserve all remaining bytes/directories and avoid receipts. Retain successful RESULT.json migration and existing tampering guards; all 28 migration tests pass.
- [x] Verify the bounded correction locally and prepare publication on Draft #111: 440 tests pass, six self-hosted Nodes have zero drift, all four normative edges are current, and diff hygiene is clean. Fresh exact-head Linux/native Windows evidence remains live PR metadata.
- [x] Owner reported six JetBrains `.idea/` files in STEP 04 and explicitly requested IDE metadata tolerance. Continue with the bounded preservation block above; no blanket Git-ignore bypass.

## Active owner-test correction — legacy frozen Catalog recovery (#107)

Purpose: migration reaches an original Foundation authoring directory and rejects its authoring files as unknown immutable-package content. Distinguish isolated stores from live authoring roots, prefer exact retained packages, and reuse the existing Git-history recovery path for pre-freezing onboarding state. Snapshot/consumer/provider retained bytes take precedence; only full Node/version/normalized/package bindings may recover missing legacy bytes. Preview must not write into either repository or change provider checkouts, review files or accepted digests.

- [x] Factor the existing package validator/Git recovery reader for verified in-memory historical bytes; keep one package semantic/digest validation implementation and existing recovery writers.
- [x] Resolve missing legacy Catalog bytes and provenance deterministically, distinguish authoring files from strict store contents, and refuse advanced/unrecoverable provider substitution with useful diagnostics.
- [x] Regress exact live-package fallback, changed provider with retained history/Git history, missing/corrupt historical bytes, preview/apply/interruption and unchanged STEP-07/08/10/publication.
- [x] Verify the full correction and prepare publication on Draft #111; fresh exact-head Linux/Windows evidence remains live PR metadata.
- [x] Close native Windows findings: restore legacy CRLF artifact bytes only when size and full hash prove the original bytes, add a portable Git-autocrlf regression, and correct UTF-8/path-alias assumptions in tests. All 438 tests and self-host checks pass locally; prepare the fast-forward publication and record fresh hosted evidence in #111.
- [x] Owner confirms successful migration and orderly short paths, accepts Phase 2 for main, and defers a fresh onboarding to the next real adoption. See the closure block above.

## Active owner-test correction — migration workspace diagnostics (#107)

Purpose: the owner supplied a valid legacy snapshot but migration reports unknown workspace content without naming it. Keep the existing conservative ownership check; report the exact top-level blockers so the owner can distinguish personal/IDE files from unsupported historical ContextCanon artifacts. No automatic claiming, movement or deletion of unrecognized content is authorized.

- [x] Report sorted concrete unknown files/directories, selected workspace and unchanged-state/action guidance.
- [x] Regress preview and apply refusal with default/explicit snapshots, root/subtree workspaces and empty unknown directories; preserve all bytes and avoid creating receipts.
- [x] Verify the full candidate and prepare publication on Draft #111; fresh exact-head Linux/Windows CI remains live PR metadata.
- [x] Owner identified three obsolete anonymized exchange copies, removed them and successfully passed the workspace guard; no compatibility exception is needed.

## Post-merge baseline reconciliation — PR #108 (2026-10-06)

Purpose: record the owner's actual Phase-1 squash merge at `dc20fdb86980d5b6adb801d299a4610e0a297ae3`, integrate that accepted baseline into Draft PR #111, and run fresh exact-head Linux/Windows CI while the owner tests onboarding. The accepted Phase-1 tree exactly matches the previous stacked base. Preserve branch ancestry with a merge so an existing editable test checkout can continue using fast-forward pulls; do not rewrite the owner's active branch history or alter executable behavior.

- [x] Verify the actual Phase-1 merge and identical accepted/base trees; keep #107 open for Phase 2.
- [x] Integrate accepted main and reconcile PLAN/STATE/detail-plan current status.
- [x] Verify the documentation-only reconciliation and prepare its publication on #111 targeting main.

- [x] Owner accepts Phase 2 after successful real migration/path validation; a new end-to-end onboarding is deferred by the owner. Squash merge remains the owner's next action.

Fresh exact-head Linux/Windows results are a live gate recorded in PR #111, not another status-only commit.

## Phase-2 pre-merge position (historical)

Accepted `main`: `dc20fdb86980d5b6adb801d299a4610e0a297ae3` (owner-tested PR #108, squash-merged on 2026-10-06).

Owner-accepted change: **#107 Phase 2 onboarding storage**, branch `agent/issue-107-onboarding-versions`, PR #111 targeting `main`, being finalized for the owner's squash merge. Its original stacked Phase-1 base exactly matches the accepted squash tree. Accepted main is integrated with preserved editable-test branch ancestry. Real migration succeeds and the owner reports no remaining long paths in that project; a fresh end-to-end onboarding is explicitly deferred. See the [Phase-2 plan](plans/issue-107-phase-2.md) and [owner test](plans/issue-107-onboarding-owner-test.md).

[PR #108](https://github.com/SomeSunlight/context-canon/pull/108) is accepted: shared complete Node versions, shorter new Resource layouts and separate preview/apply migration for normal operation. #109 recovery and the #110 Resource-move correction are included. Phase 2 is now owner accepted; keep #107 open until the owner's merge of #111 closes it.

| Main point | Status | Detail / next action |
| --- | --- | --- |
| Restore a usable plan and review the interrupted work (#109) | Complete; owner accepted | [Recovery checklist](plans/issue-107-phase-1.md#recovery-and-owner-test-preparation-109) |
| Resource-move review correction (#110) | Fixed; owner retest successful | [Correction checklist](plans/issue-110-resource-move-review.md) |
| Shared versions and migration (#107 Phase 1) | Accepted in main via PR #108 | [Implementation contract and checkpoints](plans/issue-107-phase-1.md); [internal-project owner test](plans/issue-107-owner-test.md); [operator guide](docs/node-versions.md) |
| Onboarding storage and reset/recovery (#107 Phase 2) | Owner accepted after real migration; preparing #111 for squash merge | [Phase-2 checklist](plans/issue-107-phase-2.md) |
| Safe unused-version pruning | Deferred; complete reachability required | [Phase-2 prerequisite](plans/issue-107-phase-2.md) |
| Reinitialization / copied-project ID remapping (#106) | Separate open issue | [Backlog](plans/backlog.md) |
| Other proposed work and unresolved issue bookkeeping | Unscheduled | [Backlog](plans/backlog.md) |
| Previous accepted work and historical decisions | Archived | [Implementation history through PR #105](plans/archive/implementation-history-through-pr-105.md) |

## Current block — recovery and owner testing (#109)

Purpose: make the plan resumable after a lost Work chat, independently verify PR #108, and give the owner an executable test/migration sequence for the already-onboarded internal project. Recovery and real owner testing are complete; the owner squash-merged PR #108 on 2026-10-06 after the complete gate passed.

- [x] Preserve and separate overview, Phase-1 detail, deferred Phase-2 work and history.
- [x] Verify the published implementation and record remaining work or test limitations.
- [x] Document the internal-project migration/test sequence, checkpoints and rollback.
- [x] Publish the documentation on PR #108 and confirm final verification.
- [x] Owner tests and approves Phase 1, including the corrected propagation.

## Current block — Phase-1 merge readiness (#107 / #109 / #110)

Scope: record the owner's successful test/acceptance, preserve the remaining onboarding and legacy-candidate cleanup scope, publish one documentation closure, confirm exact-head full Linux/Windows verification, and mark PR #108 ready for the owner's squash merge. No product change or Phase-2 implementation belongs to this block.

- [x] Record owner acceptance and the next Phase-2 boundary in the current status/detail plans.
- [x] Prepare and locally verify the documentation-only closure, including repository links, zero generated drift and propagation health.
- [x] Owner squash-merged PR #108 after complete exact-head Linux/Windows CI as `dc20fdb86980d5b6adb801d299a4610e0a297ae3`; #107 stays open for Phase 2.

Final CI and readiness are live PR metadata: record them there without creating another status-only commit that invalidates the verified head. This index and STATE are reconciled with the actual Phase-1 squash baseline; new Phase-2 verification remains live PR metadata.

## Active owner-test correction (#110)

Completed scope: render Resource moves in guided Parent/Source review, preserve review/acceptance safety, regression-test the real failure and publish the correction on PR #108. See the [bounded checklist](plans/issue-110-resource-move-review.md). The owner confirms the correction works; migration need not be repeated.

## Resuming after an interruption

1. Read root `CONTEXT.md`, follow its applicable Topics, then read `STATE.md` and this index.
2. Open the active detail plan and resume at its first unfinished action. Consult history only when a decision needs explanation.
3. Verify the current branch/head before writing; do not let two chats write the same review branch concurrently.
4. Keep implementation completion, automated verification, owner approval and merge as distinct states.

The original PLAN text is retained in the linked detail/history files. Historical open boxes are listed in the backlog for reconciliation rather than treated as new implementation authority.
