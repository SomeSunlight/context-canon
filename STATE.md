# Current State

The accepted `main` baseline remains PR #12, squash-merged as:

`bac1f52048b3d82cedb00b04fccd114607c4c915`

PR #13 on `agent/onboarding-placement-publication` remains the active **draft, unmerged** review branch. The project owner is now exercising the workflow directly on the real `ai-workstation` onboarding and has explicitly allowed corrections discovered during that review. This is not merge approval.

## What is implemented in PR #13

The placement proposal remains the strict machine/LLM contract, while `contextcanon-onboarding/STEP-07-placement.md` is the human gate. The editable review is destination-first and can change acceptance, destination, kind/action, title and maintained wording. Canonical Rule and Topic IDs are allocated once on the human side and remain stable across review/preview cycles. Invalid or duplicate stable human-side authoring IDs are rejected when the review is loaded, before preview/publication.

Placement distinguishes `overview`, `rule`, `topic-resource`, `ordinary-documentation`, `state`, `plan`, `authority-mapping` and `unresolved`, with placement actions appropriate to those semantics. Clear source wording can remain exact; light edits and synthesis stay explicit.

Reusable Sources have two visibly different origins:

- `evidence-derived` — the semantic pass found reuse from the supplied exact Source catalog;
- `owner-selected` — the project owner deliberately adds a supplied exact Source independently of what frozen project Evidence claimed.

Both remain bound to exact Node/version/normalized/package identity. Publication resolves durable Git locator, exact commit and Node path instead of writing a transient local checkout path. The final publication preview keeps the Source name, origin, version, package digest and Git provenance visible before mutation.

`contextcanon onboard placement-preview` renders exact per-Node `CONTEXT.src.md` deltas, Source changes, durable follow-ups and deferred mutable-Markdown cleanup candidates without mutating the project. `contextcanon onboard placement-publish` revalidates frozen Evidence and review identity, refuses stale Node source after preview, installs exact Source packages, compiles touched Nodes before writing generated output, writes an exact acceptance record, and rolls back its own changes on failure.

The structure review treats ordinary `project-documentation` Markdown as mutable by default. Paths proposed as `authoritative-reference` or `imported-corpus` are preselected as fixed candidates in the human review and can be corrected there; fixed Markdown may be referenced/mapped but is excluded from destructive cleanup planning.

## Owner-review corrections now implemented

The live `ai-workstation` review clarified several UX and semantic requirements that were under-specified in the earlier review candidate.

### Semantic shelves are not repository folders

The structure-discovery instruction now says explicitly that the current repository directory tree is Evidence, **not the taxonomy ContextCanon must preserve**. A non-root Node may use an existing repository directory or a new repository-relative directory that does not exist yet when that is the clearest durable semantic landing point.

This is particularly important for document-heavy projects where many unrelated documents may currently share one folder. The owner first edits the semantic shelf map; structure materialization then creates accepted missing Node directories/skeletons safely. Focused regression coverage exercises a genuinely absent `knowledge/operations` path and proves preview/materialization creates it rather than forcing the Node onto an existing directory.

### The visible onboarding workspace is now the operator runbook

`contextcanon-onboarding/README.md` now presents the workflow as an nine-step numbered sequence from Evidence freeze through placement publication. It visibly marks:

- external LLM handoff 1 — coarse structure;
- human gate 1 — `STEP-03-structure.md`;
- external LLM handoff 2 — placement;
- human gate 2 — `STEP-07-placement.md`.

The checkpoint remains the last ContextCanon-validated state, not a live watcher. Placement checkpoint updates now also retain the exact supplied `--catalog-package` input paths so later commands no longer rely on remembering them from chat/prose. `--owner-source` is explicitly documented as a **one-time review-creation choice**: once written into `STEP-07-placement.md`, preview/publication load that choice from review state and do not require the flag again.

This is intentionally still a visible onboarding workspace rather than pretending a temporary migration workflow is already an ordinary canonical project Context Node. The current correction solves the concrete operator problem with a self-contained runbook/checkpoint without inventing a special transient Node type.

### `promote` means one canonical maintenance surface

The intended steady state is now explicit: when an accepted placement uses `promote`, the destination ContextCanon surface becomes the **single canonical maintenance surface for that meaning**.

Initial placement publication still leaves README/CONTRIBUTING/docs untouched for adoption safety. Any identical source prose that therefore remains is migration debt, not a second authority and not the desired final architecture.

A later cleanup may leave:

- a concise human-facing orientation plus a mechanically derived link to the owning Context Node;
- a reference only;
- or nothing when removal keeps the familiar document clear.

Friendly, informal or simplified wording is allowed in the orientation layer when it improves human understanding. What is forbidden as a steady state is maintaining the same complete rule/explanation independently in both the Node and the old document.

The separate technical contract is now recorded in `nodes/internal/framework-development/docs/onboarding-cleanup.md`. It binds cleanup to exact accepted placement/source bytes, requires whole-document diff review, keeps fixed Markdown and Topic/Resource authorities out of destructive cleanup, and separates semantic replacement suggestions from deterministic mutation. Broad automatic deletion is deliberately **not** implemented yet; the command UX remains unfrozen until another real onboarding validates the simplest flow.

## Owner-testing UX hardening

The second direct `ai-workstation` test exposed an operator-level failure even though the semantic mechanics were working: the workflow still made a returning user reconstruct similar commands, long digests, Source options, hidden validation steps, and artifact order from memory. That is now treated as a product defect, not user documentation debt.

The visible workspace now makes `PLAN.md` the executable operator console. It has nine numbered steps, includes Placement Validate as explicit Step 6, renders exact snapshot-bound copy/paste commands, remembers Source-catalog inputs and owner-selected Source state, and numbers artifacts so alphabetic file order follows the workflow (`STEP-02a-...` through `STEP-09-...`). CLI `--help` uses those same names.

`contextcanon onboard reset <snapshot> --from N` is now a safe testing primitive. Structure materialization and placement publication journal the ContextCanon-managed before/after bytes. Reset verifies the recorded after-state before rollback, preserves frozen Evidence, and refuses to overwrite later human edits. Older pre-journal runs get only a conservative cleanup of unmistakable untouched onboarding skeletons. Opening/resetting an older owned workspace refreshes its framework-owned PLAN to the current runbook rather than leaving stale step numbers behind.

If the visible workspace has been deleted entirely, reset now recreates the ContextCanon-owned workspace as well. The recreated `PLAN.md` is immediately bound to the preserved Evidence snapshot, marks the requested restart checkpoint, and contains the concrete restart/reset commands instead of an empty command placeholder. A foreign existing directory is still never taken over.

The placement reasoning pass also performs the semantic condensation now, while the owner is already thinking about the meaning: stable Overviews are concise summaries rather than copies of volatile version/platform prose; version/compatibility belongs in state; long snake sentences should be split into atomic findings/bullets; and architecture documents are not retained as Resources merely because of their filename when their durable semantics belong canonically in Nodes. Overview/State/Plan wording is presented to the human as `Summary` in the placement review.

## Real `ai-workstation` vertical validation

The earlier publication proof reused the original project bytes rather than a new live-repository interpretation:

- project commit: `4106fec3f7726d6c9bfedd70d30d9ed025b7c166`;
- reproduced frozen Evidence: `2a926bf353b252db4039e5c4b63b39abad6bab46c11982e88b3eb17e19cf203d`;
- accepted existing root Node ID: `aea56adf-2a26-43f0-b712-3bbeab7a3097`;
- seven accepted child/group Nodes;
- 33 Evidence-based placement findings;
- owner-selected Development Workflow Source `c4c94726-3cc7-4df6-b779-72bbf9c06f40`, package `1d82c87e4f4140791f354c9d9479df845eb65c13fce1c664ecb05bec9532c8eb`.

The human review resolved the Evidence-only version ambiguity as owner input: `pyproject.toml` should track the repository release version represented by CHANGELOG rather than leaving two stale independent version streams.

The disposable-clone publication test proved all of the following in one vertical run:

- all 8 accepted Context Nodes received their reviewed local deltas;
- existing root identity and unrelated authored root content survived;
- child Node IDs remained stable;
- frozen Evidence-covered project files remained byte-identical;
- root and child-local Rules, Overviews and cross-directory Topic/Resource routing materialized correctly;
- Development Workflow was pinned with exact package identity and durable Git provenance;
- accepted state/plan/ordinary-documentation semantics remained visible as 6 durable follow-ups;
- every resulting Node compiled with zero generated drift;
- the second preview showed the placement already materialized;
- the second publication changed 0 Context sources and reproduced acceptance digest `a206e3423e9ffaccf7c3f7a1a0e2f140251a834f3c6eaf9764cd952b95e509c4`.

The real frozen Evidence did not produce an accepted authority-mapping finding, so none was invented merely to exercise that feature. Fixed-authority mapping remains covered by deterministic framework validation/tests.

## Current verification state

The owner-testing hardening candidate now has **142 deterministic tests** after adding focused coverage for numbered CLI help and stale-PLAN refresh during reset. The preceding temporary hardening workflow already proved the 139-test implementation slice plus zero generated drift and removed its own temporary files before product commit `ee4c63772d0fe648347359f5e725b61c44452d54`.

This final documentation/help polish is validated by a temporary self-deleting workflow that runs Python compilation, all 142 tests, `contextcanon build --all .`, `contextcanon check --all .`, and `git diff --check` before it is allowed to create the clean product commit. The temporary workflow and helper script are removed from that commit.

Because bot-authored commits can produce GitHub's `action_required` result for the normal pull-request workflow, the clean product tree must then receive a repository-authored no-content checkpoint commit and a normal exact-head PR workflow. That final CI result, not the temporary harness alone, is the review proof.

## Latest reset recovery verification

The missing-workspace reset correction is covered by a direct regression test and passed ordinary PR workflow #482 / run `33498482979`. The final repository-authored checkpoint must retain the same product behavior, zero generated drift, and no temporary finalizer files before the owner reinstalls for the next `ai-workstation` run.

## Boundaries that intentionally remain

PR #13 still does **not** perform destructive onboarding cleanup. Initial publication remains non-destructive. The later cleanup contract is now explicit, but implementation awaits another real review of the desired user experience rather than growing a second long ceremony prematurely.

The project also does not yet choose a remote Node-library registry/distribution architecture, invent a special GroupNode type, make navigation hierarchy imply Source inheritance, automatically splice state/planning findings into arbitrary prose, or build a browser UI. Those remain separate questions to answer from further real use.

Normal ContextCanon-native project evolution is distinct from one-time migration onboarding: after adoption, humans edit canonical `CONTEXT.src.md`/project documentation and use normal build/check workflows rather than repeatedly re-running migration Evidence analysis.

## Immediate next step

Obtain the ordinary GitHub PR workflow on the exact clean product head. If green, keep PR #13 draft/unmerged and let the project owner reinstall that exact SHA and restart the real `ai-workstation` onboarding. The intended test UX is now deliberately simple: after reset/restart, open `contextcanon-onboarding/PLAN.md` and follow/copy it from top to bottom. Do not merge or begin destructive duplicate cleanup without explicit owner approval.

## Latest live Step-4 owner-test verification

The next direct `ai-workstation` test exposed two additional operator issues and one real Step-4 collision bug. The generated PLAN now places an explicit one-line pointer immediately above the checklist to the detailed copy/paste section, and the exact command section defines one shell-native `SNAPSHOT` variable so the long content-addressed Evidence path is written once rather than repeated through every command.

Structure preview/materialization no longer treats a provably ContextCanon-generated root `CONTEXT/` directory or the root `.context/onboarding/` namespace as a project-owned collision merely because the namespace exists. Recovery remains conservative: a missing root `CONTEXT.src.md` is recoverable only when `.context/package.json`, generated `.context/context.yaml`, or prior ContextCanon acceptance state proves one unambiguous stable root Node ID. Existing generated `CONTEXT.md`/`CONTEXT/` bytes are accepted only when their generated ownership can be verified; a foreign `CONTEXT/` directory still fails before mutation. Root recovery preserves the established Node ID, name, and version rather than allocating a replacement UUID.

Focused coverage reproduces the exact failing shape and also proves the foreign-directory refusal. The complete suite now passes **144/144 tests**, followed by full `contextcanon build --all .`, `contextcanon check --all .`, and `git diff --check` with zero generated drift. PR #13 remains draft and unmerged; the next action is continued project-owner testing on a normal exact-head CI checkpoint.

## Latest child-node restart recovery

The next live `ai-workstation` Step-4 run exposed `bootstrap` with a missing `CONTEXT.src.md` but existing `.context` machine state. Recovery is now Node-local: every accepted Node may recover its authoring skeleton only from its own verifiable generated identity/state; only the project root may additionally use prior onboarding acceptance records. This preserves stable child IDs across reset/retest cycles without weakening foreign-path collision protection. Focused regressions cover both successful child recovery and refusal of unknown child `.context` entries.

## Latest placement transformation owner-test correction

The active PR now treats placement review as the complete migration cockpit rather than a destination-only findings report. Promoted mutable-Markdown meaning can carry an exact reviewed Source After transformation in the same semantic proposal and human gate. Publication applies accepted source-document edits transactionally with Context Node authoring and preserves idempotency by recognizing the exact reviewed post-migration bytes. Frozen Evidence remains immutable review input; fixed Markdown, non-Markdown technical authorities and unrelated Evidence remain protected from this cleanup path. Placement now publishes reviewed State/Plan as local `## State` / `## Plan` authoring in the destination `CONTEXT.src.md`; generated `CONTEXT.md` carries them as operational project context, while reusable Sources do not inherit them. Exact Source catalog and owner-selected Source inputs are now also retained in snapshot-owned run state so reset cannot forget them.

## Latest State/Plan publication completion

The active onboarding path now treats State and Plan as first-class local Node content. Accepted placement State/Plan findings are written transactionally with the rest of Node authoring, shown as `Into Node — editable` during human review, included in publication preview, and removed from migration follow-up. They render into Official Context and local machine state but are deliberately excluded from inherited Source semantics.

## Latest shared Source-edit parsing correction

The real `ai-workstation` Step-7 review exposed a parser boundary bug when one promoted finding owns more than one Source After edit. The renderer correctly materialized each Source edit once, but the parser previously scanned from one Source-edit marker until the next placement item/Source heading, so a sibling Source edit under the same finding contributed a second `Source edit note:` and caused validation to fail. Source-edit parsing now stops at the next Source-edit marker as well; multiple non-overlapping edits under one finding round-trip independently.

## Latest placement-summary and cockpit correction

The real `ai-workstation` Step-7 review showed that the LLM could still satisfy the earlier placement prompt with version-heavy stable Overview, comma-heavy State, and Source After replacements that were little more than “see Project Context”. The semantic instruction now requires stable Overview to shed volatile compatibility already modeled as State, makes Overview/State/Plan findings bullet-sized, and requires a useful plain-language gist plus the canonical Context link wherever a human-facing source location remains useful. STEP-07 also keeps a conservative human escape hatch: an unambiguous mutable source range omitted by the LLM is rendered as an optional review-only edit defaulting to reject, so the owner may correct the source aftermath in place without reconstructing paths/ranges. Single-finding source edits no longer print a tautological self-reference such as `Linked promoted findings: P-004`; genuinely shared edits still point to the one editable owner block.

## Latest placement semantic-integrity correction

The latest real `ai-workstation` placement review exposed a more important invariant than wording quality: Source After cleanup must not be able to remove a fact merely because another duplicate passage happens to mention it elsewhere. The placement instruction therefore performs a per-edit zero-loss audit against the exact frozen source range. Every removed substantive fact must remain in the source summary or be carried by linked promoted findings whose Evidence cites that removed range. Stable Overview can still shed volatile versions, but the corresponding State findings must explicitly carry those facts from the same mixed source.

Open semantic questions discovered during onboarding are now first-class local project state. `unresolved` findings require a destination Node and action `promote`; publication renders them under that Node's State as `Open question: ...`. The question remains unanswered and can be investigated after onboarding, so semantic archaeology improves the project backlog without turning the migration itself into a research project.

The Step-07 cockpit now visibly marks editable controls, destination content and Source After replacement regions with `✏️ EDITABLE` labels that survive ordinary rendered Markdown views. Review-only optional source cleanup is explicitly independent from finding acceptance: leaving an H-edit at `reject` keeps the source byte range unchanged while the promoted finding may still be accepted. Automatically invented H-fallbacks are deliberately withheld for Markdown retained as Topic/Resource and for CHANGELOG/patch history.

## Active fast-run boundary

The current project-owner testing sequence is explicitly recorded as **Fast-run status — ACTIVE** in PLAN. Its scope is the live `ai-workstation` onboarding corrections through the next coherent owner-review candidate. Fast-run reduces repeated intermediate ceremony but does not alter authority: PR #13 remains draft/unmerged, unknown failures still require investigation, and final owner review plus exact-head merge verification remain mandatory. The reusable Development Workflow now requires both the ACTIVE scope/exit checkpoint and a later CLOSED checkpoint when ordinary cadence resumes.

## Latest Source-edit blank-separator validation correction

The next real `ai-workstation` placement validation exposed an intentionally narrow mismatch between semantic provenance and contiguous Markdown editing. A reviewed Source After edit may need to span a blank separator line between two Evidence-backed blocks; requiring a promoted finding to cite that empty line adds no semantic safety and rejected an otherwise sound proposal. Placement validation now requires linked promoted Evidence to cover every non-blank line in the edited frozen range while allowing blank/whitespace-only separators. Content-bearing headings, table rows, comments and prose remain covered or validation fails with the exact missing line numbers.

## Latest remembered owner-Source recreation correction

The real `ai-workstation` production review exposed that `placement-review` loaded persisted owner Source specs from snapshot-owned `run-inputs.json` but still passed only the current CLI `--owner-source` arguments into review creation. As a result, a reset/recreated Step 7 could silently lose the previously selected Development Workflow Source even though machine state still remembered it. Review creation now uses the remembered owner choice when the review file is absent, while repeated validation of an existing human review keeps the one-time owner-selection boundary unchanged.

## Latest first production post-publish checkpoint

The real `ai-workstation` onboarding has now crossed the end-to-end boundary: the project owner accepted the placement review and completed publication locally, then began inspecting and planning normal work from the resulting Nodes. This is the first run where ContextCanon is being judged not only as an onboarding pipeline but as the project's ongoing working context.

The completed run exposed a clear next UX layer. Structure review needs the same visible edit affordance as placement review but with quieter markers; placement review needs an inline glossary of its editable decisions/kinds/actions; and Source After review is still cognitively expensive because source-file transformations can combine findings from distant parts of the destination-first review. A future source-file-first audit surface should show exact before/after text and direct landing destinations for every removed meaning.

Normal authoring also has an ergonomics gap: the executable source format currently requires compiler-managed stable IDs for Rules and Topics, so adding a new Rule by hand still requires a `ctx:rule` ID. Stable identity remains correct, but ordinary authors should receive a ContextCanon command/write mechanism that allocates those IDs rather than editing invisible bookkeeping manually.

Most importantly, post-publication inspection sharpened the semantic-parent requirement. The owner-accepted hierarchy from onboarding Step 03 should become an explicit accepted composition relationship rather than remain only onboarding structure metadata. This should not be implicit filesystem inheritance. The reviewed parent relationship should pin an accepted Parent package into the Child, letting the Child keep its previous effective context until a Parent update is reviewed and accepted. Existing compiler behavior already composes inherited Rules transitively, but Topics are explicitly local-only today; the next architecture block must define inherited Topic/resource package semantics and render the complete effective Rules + Topics in every Node's `CONTEXT.md`.

The known legacy in-flight owner-Source recovery defect remains deferred. The first real published `ai-workstation` run may therefore lack the intended Development Workflow Source. The fast-run stays ACTIVE while the owner inspects the published Nodes and the project transitions to a new chat; PR #13 remains draft/unmerged and requires explicit owner approval before any merge gate.

## Latest Block R1 review-surface checkpoint

The first post-publish UX slice is complete. Step 03 now marks the editable semantic Node tree with quiet visible cues instead of relying only on hidden comments. Step 07 is self-contained about Decision, Destination, Kind, derived Action, Wording and Review-note semantics, and its editable regions use lower-noise visual boundaries.

`Action` is no longer an independent human control in placement review. The renderer shows it as derived from `Kind`, and the parser deterministically reconstructs the only valid Kind→Action mapping. Stable review semantics and the existing placement proposal contract are unchanged. The remaining Block R work — source-file-first transformation audit, ordinary post-onboarding authoring ergonomics, semantic parent composition/Topic inheritance and Source-update UX — remains pending. Fast-run stays active and PR #13 remains draft/unmerged.

## Latest Block R2 normal-authoring checkpoint

Normal ContextCanon-native project work no longer requires authors to invent hidden Rule/Topic IDs. `contextcanon author rule` and `contextcanon author topic` write the same ordinary `CONTEXT.src.md` syntax humans already maintain, allocate one stable `RULE-...` / `TOPIC-...` identity, validate the resulting Node, and leave build/check explicit. There is no secondary authoring database.

The reusable Source-format guidance now records the minimal post-onboarding loop: read effective `CONTEXT.md`, edit `CONTEXT.src.md` and natural Resources, use the authoring commands for new identified elements, build, check, and review Source candidates explicitly before acceptance. The remaining Block R work is the source-file-first transformation audit plus the larger semantic-parent/Topic-inheritance and Source-update UX blocks. Fast-run remains active; PR #13 remains draft and unmerged.

## Latest Block R3 source-transformation-audit checkpoint

The remaining post-publish review-UX gap is closed without creating a second human gate. Every successful `contextcanon onboard placement-review` validation now deterministically regenerates `STEP-07a-source-audit.md` from the currently parsed `STEP-07-placement.md`. Step 07 remains the only editable placement truth; the audit is explicitly generated/read-only and reset together with Step 07.

The audit reverses the review axis from destination-first to source-first. Source edits are grouped by original file and exact frozen range; each shows exact Before, the decision-dependent effective After (or unchanged source for rejection), any non-applied candidate replacement, and every linked P-finding with its current decision, destination Node, Kind/derived Action and reviewed destination content. This makes zero-semantic-loss review possible from one source transformation without hunting across unrelated finding sections.

Blocks R1-R3 now close the immediate production review/authoring UX findings. The next substantial Block R work is semantic parent composition: persisting the owner-accepted Step-03 hierarchy as explicit accepted package relationships, extending inheritance to Topics/resources, and rendering complete effective context. Source-update discovery UX remains a later adjacent slice. Fast-run remains active; PR #13 remains draft and unmerged.

## Latest Block R4a effective-Topic package checkpoint

Topics are now effective transitive package semantics rather than local-only presentation. The compiler turns local Resource targets into origin-Node-namespaced package paths and carries stable Context-Node target identity in compiled Topic targets. `CompiledPackage.topics` therefore contains inherited plus local Topics, and descendants can compose them without parsing generated `CONTEXT.md` or consulting the Source repository.

Inherited Resource trees use `CONTEXT/references/<origin-node-id>/...` (with deterministic hashing only for path-unsafe IDs). This makes the collision rule structural and Source-order-free: the same stable origin path with identical bytes deduplicates through diamonds; different bytes at that path fail compilation/review. Pinned external Source packages can now provide Topics and Resources entirely offline. Official `CONTEXT.md` renders inherited Topics grouped by origin alongside local Topics; inherited Context-Node navigation shows the stable target identity when no consumer-local link can safely be promised.

This deliberately precedes the Parent relationship itself. The next Block R slice can now model an accepted semantic Parent as a distinct exact package edge while reusing the already-general Rule/Topic composition machinery. Fast-run remains active; PR #13 remains draft and unmerged.

## Latest Block R5 step-1 semantic-Parent checkpoint

ContextCanon now has an explicit `## Parent` authoring relationship. Parent is always an exact immutable package pin and remains distinct from ordinary reusable Sources in parsed state, compiled state, human rendering, machine YAML, package metadata and deterministic diff. Filesystem nesting still carries no composition meaning.

The compiler composes the accepted Parent package through the same Rule/Topic/Resource conflict machinery as Sources, while the normalized semantic digest records the Parent role separately. Existing packages without Parent metadata remain valid because the optional Parent semantic field is absent when no Parent exists. Normal builds load the Parent only from the Child's local immutable package store and never dereference the Parent locator.

R5 step 2 is next: persist the owner-accepted Step-03 hierarchy during onboarding publication and install the exact resulting Parent package into each Child. PR #13 remains draft and unmerged; fast-run remains active.

## Latest Block R5 step-2 onboarding-Parent publication checkpoint

Structure-first placement publication now preserves the owner-accepted Step-03 hierarchy as exact semantic Parent pins. Preview evaluates every accepted structure Node parent-to-child with the normal compiler behind a read-only overlay: reviewed future `CONTEXT.src.md` text, accepted Source-After Resource bytes and exact catalog packages are visible to compilation without mutating the project. The Child pin therefore names the exact final Parent package from the same reviewed publication, including any Parent meaning or Resource bytes being changed in that publication.

Publication writes the reviewed source/document deltas transactionally, installs direct reusable Source packages, then walks the semantic Parent chain from roots to leaves. Each final Parent artifact is installed into the Child's local immutable `.context/sources/<package-digest>/` store before the Child is compiled. Acceptance records preserve the Parent edge and exact package identity; rerunning the same reviewed publication is idempotent.

R5 step 3 is next: give Parent updates the same non-live candidate/review/accept safety as reusable Source updates. PR #13 remains draft and unmerged; fast-run remains active.

## Latest Block R5 step 3 Parent-update checkpoint

Semantic Parent updates now have their own explicit `contextcanon parent review` / `contextcanon parent accept` gate. Ordinary Child builds remain pinned to accepted package bytes and never dereference the live Parent locator. Review explicitly compiles the current same-project Parent into a content-addressed candidate, validates it against the Child's real Rule/Topic composition and stores an exact receipt; accept installs and pins exactly that reviewed snapshot even if the live Parent changes again afterwards. R5 now proceeds to the full transitive Parent-chain proof.

## Latest Block R5 step 4 Parent-chain checkpoint

The complete scoped-context chain is now regression-proven: a reusable Development Workflow Source attached at a project ancestor reaches a deep subsystem Tool through immutable Parent packages together with project/subsystem Rules, Topics and exact Resource bytes, while an unrelated sibling contributes nothing. The leaf remains compilable from its direct Parent package even after upstream Source/Parent authoring files are removed, demonstrating that the semantic chain is accepted package reachability rather than filesystem recursion. R5 now proceeds to migration/idempotency/recovery for an already-published ai-workstation-like tree.

## Latest Block R5 complete semantic-Parent checkpoint

Block R5 is complete. The accepted Step-03 hierarchy is now durable package semantics rather than a review-only tree: non-root Nodes pin exact Parent packages, ordinary builds are non-live, Parent changes require explicit review/accept, reusable Sources and complete effective Rules/Topics/Resources flow through the Parent chain without sibling leakage, and already-published pre-Parent placements have a narrow exact-byte migration path with idempotent republish and Step-9 recovery of the prior acceptance/package state. The next Block R work is R6 Source-update discovery UX.

## Latest Block R6 step 1 Source-discovery checkpoint

Git-backed reusable Source discovery now distinguishes the accepted Git provenance from the moving update-discovery surface. A Source pinned by current onboarding to an exact old commit can explicitly `source fetch` the repository's newer default-branch package; ContextCanon immediately freezes the candidate under its package digest and records the exact discovered Git commit beside it. Normal build and accepted Source pins remain untouched. R6 proceeds to binding review/accept to that exact candidate without live pulls.

## Latest Block R6 step 2 exact-Source-update checkpoint

Reusable Source review/accept is now bound to the exact Git candidate provenance frozen during fetch as well as package identity and consumer state. The remote may move again after review without changing what accept means; acceptance never contacts it. Current exact-commit Source pins advance to the reviewed candidate commit, while historical symbolic discovery refs remain symbolic. Normal builds remain fully offline against accepted local package bytes. R6 proceeds to documenting and proving the ordinary daily update loop.

## Latest Block R complete first-production-use checkpoint

Block R is complete and the owner-approved fast-run is CLOSED. ContextCanon now has human-readable onboarding review surfaces, simple normal Rule/Topic authoring, source-first migration audit, transitive package-safe Topics/Resources, explicit immutable semantic Parent chains with safe update/migration/recovery, and a complete reusable-Source fetch/review/accept loop whose normal builds remain offline on accepted packages. The next useful validation is the real published `ai-workstation` tree: migrate its reviewed Step-03 hierarchy to Parent pins and exercise work from a subsystem Node. PR #13 remains draft/unmerged pending explicit owner approval.

## Latest Block S real machine-state resource determinism checkpoint

The project owner's current `ai-workstation` machine snapshot exposed a compiler-0.4 package feedback loop: an exact Topic Resource (`SECURITY.md`) linked to generated `CONTEXT.md`, so resource closure copied whichever generated Official Context happened to exist and then followed its `CONTEXT.src.md` edit link. The placement acceptance therefore recorded a different root package digest from the package actually written by the same Step-9 journal even though normalized semantics and `CONTEXT.src.md` bytes agreed. Compiler 0.5 now treats a Markdown closure link to its owning Node's generated `CONTEXT.md` as a deterministic package-local bridge to the package's top-level Official Context. It never reads previous generated bytes, preserves the exact authored Resource bytes and link shape, avoids copying `CONTEXT.src.md` merely through generated output, and lets normal output cleanup remove the old compiler-0.4 copy. A regression reproduces the stale generated-context/resource-tree shape and proves first-build/second-build package identity plus zero drift. Block S proceeds to explicit recovery/re-adoption of the lost legacy Development Workflow owner Source.

## Latest Block S explicit Source re-adoption checkpoint

A reusable Source that is genuinely absent from old machine/onboarding state is no longer treated as reconstructible history. `contextcanon source adopt <package-node> --node <consumer>` provides a normal post-onboarding first-adoption action: it fully verifies the exact published package, requires a clean Git package path, freezes origin/exact HEAD/node-path provenance, validates the future consumer composition before mutation, installs the immutable package, and atomically adds one ordinary Source declaration. Historical placement acceptance remains unchanged. Exact repeat adoption is idempotent; an existing Source identity with different package state is refused so updates stay on fetch/review/accept. This gives the real ai-workstation a safe way to explicitly re-adopt the Development Workflow at the root without replaying its 58 accepted placement decisions. Block S proceeds to the combined real-machine upgrade proof with Source plus Parent chain and offline descendant context.

## Latest Block S complete real machine-state upgrade checkpoint

Block S is complete against a compact regression distilled from the owner's supplied `ai-workstation` machine state. The exact nine authored Node identities produce eight semantic Parent edges; compiler-0.4 generated-Resource feedback is removed; a genuinely lost legacy owner Source is recovered only through explicit normal `source adopt`, not invented historical state; and the combined upgrade is proven end-to-end. The safe order is: migrate the still-byte-exact legacy placement to Parent pins first, explicitly adopt the current Development Workflow package at the root, then review/accept Parent updates top-down. Goose and Ansible receive the workflow plus only their own ancestor/local project context, siblings remain excluded, and a deep leaf still compiles with the workflow Resource after both the original reusable Node checkout and the root's direct Source package are removed. Historical placement acceptance remains byte-stable through ordinary Source adoption and Parent updates. PR #13 remains draft/unmerged pending explicit owner approval.
