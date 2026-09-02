# Onboard an Existing Project

You have an existing Git project with README files, configuration, CI, architecture notes, operational documentation, agent instructions, and perhaps years of accumulated knowledge. ContextCanon onboarding helps turn that material into a **reviewed context structure** without pretending that an LLM should decide the project's architecture by itself.

The larger `ai-workstation` experiment exposed a simple ordering rule:

> **Design the shelves before placing the books.**

The first semantic pass reconstructs the coarse project model. The project owner reviews and edits that model. Only then does a second semantic pass propose where existing knowledge belongs.

That distinction matters. Repository archaeology can discover surprisingly good natural groupings, but it cannot safely decide future architecture. The `ai-workstation` structure reviewer, for example, proposed a plausible future local-model area below `compose`; the project owner removed it because the future implementation boundary is intentionally unresolved. That is the human gate working as designed.

## The whole idea

```text
existing Git repository
        ↓
ContextCanon freezes selected Evidence
        ↓
strong reasoning LLM proposes coarse structure
        ↓
human edits STEP-03-structure.md until it matches the project mental model
        ↓
ContextCanon previews/materializes only missing Node skeletons
        ↓
strong reasoning LLM places existing knowledge into that accepted structure
        ↓
human reviews STEP-07-placement.md with exact source excerpts
        ↓
only later: reviewed publication / cleanup / duplicate removal
```

ContextCanon handles exact identity, provenance, validation, deterministic generation, and state transitions. The LLM handles semantic interpretation. The project owner decides which interpretation becomes durable project truth.

> [!IMPORTANT]
> **Use a strong reasoning-capable model for onboarding.** The semantic passes compare scattered evidence and infer structure or placement. ContextCanon can prove that returned JSON refers to the exact frozen bytes and accepted structure, but it cannot turn weak semantic judgment into a good project model.

Once the context is organized, smaller or local models can benefit from receiving the right narrow context during ordinary work. The occasional onboarding/restructuring pass is where stronger reasoning has unusually high leverage.

## Operator rule: use the generated PLAN, not this page, as your keyboard script

This page explains **why** the stages exist. It is deliberately not the place where an operator should reconstruct long snapshot IDs or remember which flags belong on which nearly-identical command.

As soon as Step 2 opens `contextcanon-onboarding/`, use **`contextcanon-onboarding/PLAN.md` as the executable console for that run**. ContextCanon writes the exact snapshot-bound commands there, including remembered `--catalog-package` inputs, the one-time `--owner-source` choice, the current validated checkpoint, and reset commands. Copy those commands instead of rebuilding them from this documentation, terminal history, or chat history.

`contextcanon-onboarding/README.md` remains the stable orientation page. `PLAN.md` is the thing to follow while doing the onboarding.

## 1. Freeze the project Evidence

Run from the root of the Git repository:

```text
contextcanon onboard prepare .
```

ContextCanon creates a content-addressed snapshot such as:

```text
.context/onboarding/<evidence-digest>/
```

### What "frozen" means

Freezing does **not** lock the live repository. ContextCanon copies the selected review material into an immutable snapshot and records exact paths, sizes, hashes, and line counts.

That gives two important properties:

1. the LLM and later human review are talking about the **same exact project bytes**;
2. another semantic pass, corrected instruction, or review iteration can deliberately reuse the **same Evidence digest** without rescanning the live project and silently changing the basis of comparison.

Prepare a new snapshot when you intentionally want a new evidence basis, not merely because another onboarding experiment starts.

ContextCanon selects likely context carriers conservatively: README/CONTRIBUTING files, architecture/design/development documentation, common manifests and configuration, CI workflows, and common agent instructions. Ordinary source code is not copied wholesale. Important safe UTF-8 files can be added explicitly:

```text
contextcanon onboard prepare . \
  --include src/project_policy.py \
  --include config/example.ini
```

## 2. Discover the coarse structure

Use the snapshot from step 1:

```text
contextcanon onboard structure-instruction \
  .context/onboarding/<evidence-digest>
```

ContextCanon creates a visible human working directory:

```text
contextcanon-onboarding/
├── README.md
├── PLAN.md
└── STEP-02a-structure-instruction.md
```

`contextcanon-onboarding/PLAN.md` is the operator console for the in-progress onboarding. It contains the nine numbered steps, exact copy/paste commands for the current snapshot, both external-LLM handoffs, both human review gates, reset commands, and the latest ContextCanon-validated checkpoint. When returning after a pause, start there rather than reconstructing the command sequence from memory. `README.md` explains the workspace and points back to the PLAN.

Important onboarding Markdown is written directly as UTF-8 by ContextCanon rather than through shell redirection. This keeps the workflow reliable across shells — in particular Windows PowerShell codepage behavior — while `.context/` remains machine-oriented state.

Give the strong reasoning LLM:

- `contextcanon-onboarding/STEP-02a-structure-instruction.md` as the controlling assignment;
- read access only to the frozen snapshot's `evidence/` directory.

The model returns exactly one JSON object. Save it as:

```text
contextcanon-onboarding/STEP-02b-structure-proposal.json
```

The structure pass asks for:

- candidate local/grouping Nodes;
- one simple primary parent/child hierarchy for human orientation;
- larger knowledge bodies that should remain documentation, authoritative references, or imported corpora rather than becoming Nodes merely because they contain information;
- exact reusable Source matches only when a verified Source catalog was supplied;
- rationale, confidence, and exact frozen-Evidence provenance.

The current repository directory tree is **evidence about the project, not the taxonomy ContextCanon must preserve**. A proposed semantic Node may use an existing directory or a new repository-relative directory that does not exist yet. This matters especially for document-heavy repositories where many distinct knowledge areas currently live together in one folder. The human accepts the shelf map first; materialization can create the missing Node directories safely afterwards.

It deliberately does **not** distribute individual Rules or rewrite project prose yet.

## 3. Validate and edit the shelf map

Validate the machine proposal:

```text
contextcanon onboard structure-validate \
  .context/onboarding/<evidence-digest>
```

Then create the human-editable structure:

```text
contextcanon onboard structure-review \
  .context/onboarding/<evidence-digest>
```

ContextCanon creates:

```text
contextcanon-onboarding/STEP-03-structure.md
```

The top of that file is deliberately simple Markdown:

```markdown
- **AI Workstation** (`.`)
  - **Bootstrap** (`bootstrap`)
    - **Windows and WSL bootstrap** (`bootstrap/windows`)
    - **Linux bootstrap** (`bootstrap/linux`)
  - **Containerized application runtimes** (`compose`)
    - **Goose** (`compose/goose`)
    - **Open WebUI** (`compose/open-webui`)
```

The project owner may:

- rename proposed Nodes;
- re-parent them by indentation;
- remove speculative Nodes;
- add missing Nodes, including at new paths not present in the repository yet;
- add an explicitly planned future area with `[reserved]`.

The details below the tree retain the LLM rationale and exact Evidence excerpts. They are there to make the proposal reviewable; the hierarchy at the top is the human-owned shelf map.

The project owner's mental model is authoritative here. The LLM proposes structure; it does not impose taxonomy or future architecture.

## 4. Preview and materialize only missing Node skeletons

Before touching project Context files:

```text
contextcanon onboard structure-preview \
  .context/onboarding/<evidence-digest>
```

This writes:

```text
contextcanon-onboarding/STEP-04-structure-preview.md
```

The preview distinguishes:

- existing Context Nodes, whose stable identity is protected;
- existing ordinary project directories that can safely become Node roots;
- missing directories/Nodes that would be created;
- collisions with project-owned ContextCanon output paths.

For a project that already has an onboarded root Node, that root must remain an existing Node. ContextCanon will not create a replacement identity for it.

When the preview is satisfactory:

```text
contextcanon onboard structure-materialize \
  .context/onboarding/<evidence-digest>
```

Materialization creates missing accepted directories when necessary, then creates only the missing Node skeletons and their deterministic generated package files. Each new Node receives one fresh stable UUID. Existing Nodes and ordinary project files are not rewritten. Running the command again is idempotent once all Nodes exist.

At this point **the shelves exist, but the books have not been distributed yet**.

## 5. Generate the content-placement assignment

The second semantic pass is bound to both the exact frozen Evidence digest and the digest of the human-edited `STEP-03-structure.md`:

```text
contextcanon onboard placement-instruction \
  .context/onboarding/<evidence-digest> \
  --catalog-package <package-root-a>
```

ContextCanon writes `contextcanon-onboarding/STEP-05a-placement-instruction.md`. Give that instruction and **only the same frozen `evidence/` tree** to a strong reasoning LLM. Save its single JSON response as `contextcanon-onboarding/STEP-05b-placement-proposal.json`.

The placement question is no longer "where is this text today?". It is:

> **Where should this meaning be maintained from now on?**

The v1 proposal distinguishes:

- `overview` — short stable orientation about what a Node owns;
- `rule` — durable project-local governance;
- `topic-resource` — deeper Markdown that remains maintained at its natural repository path and is routed to by a Topic;
- `state` / `plan` — current situation or future work, kept distinct from inherited governance;
- `ordinary-documentation` — useful documents that remain ordinary documents;
- `authority-mapping` — a local interpretation of Markdown deliberately marked fixed/authoritative in `STEP-03-structure.md`;
- `unresolved` — ambiguity that must remain visible.

Actions are deliberately narrow:

- `promote` — make the destination ContextCanon surface the **single canonical maintenance surface** for the reviewed meaning. Initial publication may temporarily leave the original mutable prose untouched for migration safety, but that duplicate is transitional, not the desired final state;
- `reference` — only for `topic-resource`; keep the referenced Markdown as the maintenance surface and store routing, not a copied second meaning;
- `keep` — intentionally remain outside canonical Node authoring;
- `map` — preserve fixed Markdown as authority while recording the reviewed local relationship to it.

The non-redundancy goal is therefore **one canonical meaning, many useful routes**. After a promoted meaning is safely canonical in its Node, reviewed cleanup should remove the duplicate from mutable documentation or replace it with a **real short summary plus the link** to the owning Context Node. The summary is not allowed to collapse into a content-free “details are in Context” pointer when the old location still matters to a first-time reader: it should preserve the gist, while the Node owns the exact maintained detail. Friendly or informal wording is fine when it improves comprehension; the same full rule or explanation must not remain maintained in both places.

Preserve precise existing wording for facts, constraints, and Rules when it is already the best canonical wording. **Overview is a condensation task, not a quotation task:** summarize the durable responsibility sharply and move volatile platform/version compatibility into `state`. Overview, State and Plan findings are deliberately bullet-sized; when one source block contains a list or matrix, prefer several short findings over one comma/semicolon snake sentence.

The human cockpit has one additional safety net: when a promoted finding has one unambiguous mutable Markdown range but the LLM proposes no Source After edit, `STEP-07-placement.md` exposes that exact range as an optional human override. It defaults to `reject`, so it never creates cleanup work by itself; the owner can edit the replacement and switch it to `accept` without hunting for the source range later.

Likewise, do not keep an architecture document as a Topic/Resource merely because its filename says `architecture.md`. When its durable responsibilities and invariants are better maintained in Context Nodes, promote those meanings now. A later reviewed cleanup may then reduce the old document to orientation/reference or remove it if no independent explanatory, diagrammatic, procedural, or authority value remains.

### Mutable and fixed Markdown

Ordinary `project-documentation` Markdown is mutable by default. Markdown proposed as `authoritative-reference` or `imported-corpus` is preselected as fixed in `STEP-03-structure.md`, and the project owner can correct that list before placement.

- **mutable** means ContextCanon may become the future owner of promoted meaning, but the first publication still does not delete or rewrite the old document;
- **fixed** means the document remains authoritative and may only be referenced/mapped by this onboarding flow.

Non-Markdown document authorities such as PDF/Word are deliberately unsupported in this version rather than hidden behind an implicit conversion mechanism.

## 6. Validate the placement proposal

Validate the LLM result using the same Source catalog:

```text
contextcanon onboard placement-validate \
  .context/onboarding/<evidence-digest> \
  --catalog-package <package-root-a>
```

## 7. Review and revalidate `STEP-07-placement.md`

After Step 6 succeeds, create the human review:

```text
contextcanon onboard placement-review \
  .context/onboarding/<evidence-digest> \
  --catalog-package <package-root-a>
```

`STEP-07-placement.md` is the **human-owned decision file**, not merely a rendered report. Each finding is destination-first:

```text
Destination
Decision: pending | accept | reject
Kind / Action
Maintained meaning
Proposal rationale
Exact Evidence excerpts
```

The owner may edit destination, decision, title, kind/action within the supported semantics, maintained wording, and review note directly in this Markdown. ContextCanon allocates authoring identity for future Rules/Topics once and preserves it across reloads even when human-facing titles or wording change.

An existing `STEP-07-placement.md` is never silently regenerated over human edits. If the semantic proposal changes, ContextCanon requires a new review path instead of inventing a merge engine.

After editing the existing review, rerun `contextcanon onboard placement-review ...` **without** repeating `--owner-source`. That reloads and validates the human gate. The exact command for the current run is already in `PLAN.md`; do not reconstruct it here.

### Explicit owner-selected reusable Sources

An LLM may propose Source reuse only when frozen project Evidence supports it. A project owner may nevertheless choose an exact reusable Source for architectural reasons outside that Evidence:

```text
contextcanon onboard placement-review \
  .context/onboarding/<evidence-digest> \
  --catalog-package <package-root> \
  --owner-source N-001=<source-node-id>
```

The review labels that Source `owner-selected`; it does not pretend the choice came from project Evidence. Both Evidence-derived and owner-selected Sources remain bound to the exact immutable package identity.

`--owner-source` is a **review-creation decision**, not a parameter that must be repeated forever. Once the selection has been written into `STEP-07-placement.md`, preview and publication load it from the human review state. The visible workspace runbook states this explicitly.

## 8. Preview exact publication before mutation

Once every placement decision is resolved:

```text
contextcanon onboard placement-preview \
  .context/onboarding/<evidence-digest> \
  --catalog-package <package-root-a>
```

The command writes `contextcanon-onboarding/STEP-08-placement-preview.md` and changes no project file. The preview shows:

- the exact `CONTEXT.src.md` delta for every affected Node;
- exact reusable Source package/Git provenance that would be installed and pinned;
- accepted findings intentionally retained outside today's Node authoring grammar;
- mutable Markdown that may later be a duplicate-cleanup candidate, without applying that cleanup.

Preview verifies the live Evidence-covered project bytes and the current Node source bytes. Publication later refuses if those inputs changed after the preview.

## 9. Explicitly publish the reviewed placement

After reviewing the preview:

```text
contextcanon onboard placement-publish \
  .context/onboarding/<evidence-digest> \
  --catalog-package <package-root-a>
```

Publication currently materializes only semantics the ContextCanon source grammar can represent cleanly:

- accepted Overview additions;
- accepted local Rules;
- accepted Topics/Resources;
- accepted exact reusable Sources.

Existing Node identity and unrelated authored Node content are preserved. A child Node may reference a repository resource outside its own directory; ContextCanon converts repository-relative Evidence paths into safe Node-relative locators such as `../../docs/architecture.md` while still forbidding repository escape.

Accepted `state`, `plan`, `ordinary-documentation`, `authority-mapping`, and `unresolved` findings are **not lost** and are not forced into arbitrary prose. They remain in the exact machine acceptance record and in visible `STEP-09-placement-followup.md` for deliberate later handling.

The first publication also leaves README/CONTRIBUTING/architecture and other mutable Markdown untouched. This is a safety boundary, not a decision to tolerate permanent redundancy. Removing proven duplicate prose is a separate reviewed cleanup operation: it must be bound to the accepted placement and exact source bytes, show the whole resulting document diff, and replace the old copy with orientation/reference or remove it only after explicit human review. The current technical cleanup contract is documented in `nodes/internal/framework-development/docs/onboarding-cleanup.md`; the exact command surface remains intentionally unfrozen until another real onboarding proves the simplest UX.

Reusable Source packages are copied into the target Node's accepted local `.context/sources/<package-digest>/` state. The authored Source declaration carries durable Git origin, exact commit SHA and Node path derived from the clean supplied Source checkout; a transient developer checkout path is never written into project truth.

Publication is transaction-like and idempotent: it recompiles touched Nodes, writes generated outputs, records exact resulting package/source digests, rolls back on failure, and a second unchanged preview/publication produces no additional source delta.

## Resetting an onboarding test safely

Testing onboarding should not require manually hunting down generated Context files. The workspace PLAN therefore includes one reset command for every restart point from Step 2 through Step 9, for example:

```text
contextcanon onboard reset .context/onboarding/<evidence-digest> --from 5
```

Reset deliberately preserves frozen Evidence. For current runs, ContextCanon journals the managed project bytes changed by structure materialization and placement publication, verifies that those bytes have not been edited afterward, and only then restores/removes its own changes. If a recorded managed file changed after ContextCanon wrote it, reset refuses rather than overwriting human work.

For older pre-journal test runs, reset can conservatively remove only unmistakable untouched onboarding skeleton Nodes whose generated outputs still exactly match the compiler. It does not treat arbitrary project changes as disposable.

The reset command also refreshes an older framework-owned workspace PLAN to the current numbered runbook before restarting, so upgrading ContextCanon does not leave the operator following stale filenames or step numbers.

## Migration onboarding versus normal ContextCanon-native growth

The structure-first flow above is primarily a **migration/onboarding workflow for an existing knowledge-rich repository**. It performs repository archaeology, proposes a shelf map, redistributes existing meaning, and records what remains outside current canonical authoring.

Once a project is ContextCanon-native, ordinary growth should usually be much simpler:

```text
new project knowledge
→ edit the relevant existing CONTEXT.src.md / Topic resource / project state surface
→ normal review
→ contextcanon build/check
```

Do not rerun full migration onboarding for every normal feature. A future "context audit" may intentionally re-examine accumulated repository knowledge, drift or changed structure, but that is a separate lifecycle operation and should not be smuggled into initial onboarding semantics.

### Reusable Node distribution remains an explicit later UX decision

This work proves immutable reusable Source packages, exact Git provenance, owner selection and local accepted package state. It deliberately does **not** choose how a wider Node library should be discovered/distributed in the long term (single Git repository, multiple repositories, registry, catalog service, or another mechanism). That distribution UX needs its own real use cases before ContextCanon hardens an architecture.

## Visible workspace versus machine state

During the experiment the two areas have different jobs:

```text
.context/onboarding/<digest>/
    immutable Evidence and machine/provenance state

contextcanon-onboarding/
    human/LLM working artifacts
    README.md
    PLAN.md
    STEP-02a-structure-instruction.md
    STEP-02b-structure-proposal.json
    STEP-03-structure.md
    STEP-04-structure-preview.md
    STEP-05a-placement-instruction.md
    STEP-05b-placement-proposal.json
    STEP-07-placement.md
    STEP-08-placement-preview.md
    STEP-09-placement-followup.md
```

The visible workspace has a ContextCanon ownership marker. If a directory with the same name already exists without that marker, ContextCanon refuses to take it over; use `--workspace <path>` instead.

## Legacy single-pass first adoption

The accepted `main` baseline still contains the earlier single-pass first-adoption workflow:

```text
prepare → instruction → external LLM → proposal.json
→ validate → review → explicit onboard accept
```

That path established important trust boundaries: immutable Evidence, exact proposal provenance, human decisions, exact Source package binding, staged compilation, rollback-safe first publication, and refusal to overwrite an existing `CONTEXT.src.md`.

PR #12 does **not** silently reinterpret those accepted artifacts. The structure-first path is a separate experiment layered on the same frozen-Evidence foundation. Once the larger real-project flow is accepted, the documentation/API can be consolidated deliberately instead of pretending the old and new semantic contracts are the same thing.

## Why the explicit stages exist

The flow is longer than a one-shot "read my repository and reorganize it" prompt because each stage owns a different kind of truth:

```text
prepare                Which exact project bytes may be considered?
structure instruction  What coarse semantic task is being asked?
reasoning LLM           What knowledge areas seem to exist?
structure validate      Does the proposal honestly cite those exact bytes?
human structure edit    What is the project's intended mental model?
preview/materialize     Which Node identities/files would actually be created?
placement instruction  Where should existing knowledge live in that model?
reasoning LLM           What placements/reuses seem justified by Evidence?
placement validate      Is that exact JSON bound to Evidence + structure + Sources?
human placement review  Do these moves/references/mappings actually make sense?
later publication       Which reviewed changes may safely become canonical?
```

Deterministic mechanisms handle identity, integrity, reproducibility, and state transitions. Reasoning models handle semantic interpretation. Humans own architecture and acceptance.

## Need the exact contracts and safety details?

This page is the first-user walkthrough. Compiler/schema details and the older accepted onboarding trust contract remain in the [onboarding technical reference](../nodes/internal/framework-development/docs/onboarding-reference.md#technical-reference).

The structure/placement contracts are still being validated through the real `ai-workstation` exercise. They should be promoted into the technical reference only after this vertical test settles their semantics rather than documenting an abstraction before it survives use.

State and Plan are local first-class Node authoring: accepted placement findings of those kinds are written to `## State` and `## Plan` in the destination `CONTEXT.src.md` and therefore appear in generated `CONTEXT.md`. They are intentionally not inherited through reusable Sources; current project situation and future project work stay local to the Node that owns them.
