# Onboard an Existing Project

You have an existing Git project with README files, configuration, CI, architecture notes, operational documentation, agent instructions, and perhaps years of accumulated knowledge. ContextCanon onboarding helps turn that material into a **reviewed context structure** without pretending that an LLM should decide the project's architecture by itself.

The larger `ai-workstation` experiment exposed a simple ordering rule:

> **Design the shelves before placing the books.**

But even that starts one step too late. Before designing shelves, ContextCanon first looks at the **deliveries** already lying around the project and performs a deliberate **triage**: which material is direct source, which needs interpretation, which is only lookup material, and which should stay out.

The first semantic structure pass then reconstructs the coarse project model. The project owner reviews and edits that model. Only after the shelves exist does a second semantic pass propose where the reviewed meaning belongs.

That distinction matters. Repository archaeology can discover surprisingly good natural groupings, but it cannot safely decide future architecture. The `ai-workstation` structure reviewer, for example, proposed a plausible future local-model area below `compose`; the project owner removed it because the future implementation boundary is intentionally unresolved. That is the human gate working as designed.

## The whole idea

```text
existing project deliveries
        ↓
human tidies obvious clutter
        ↓
ContextCanon inventories what Git can see
        ↓
human triage: source / interpret / lookup / ignore
        ↓
ContextCanon freezes the exact reviewed Evidence
        ↓
[coming soon] interpret raw/ambiguous Evidence into reviewed meaning
        ↓
design the shelves: reasoning LLM proposes coarse structure
        ↓
human accepts/edits the shelf map
        ↓
ContextCanon materializes the reviewed Node structure
        ↓
compose reusable Contexts where they apply
        ↓
place the books: reasoning LLM proposes destinations for reviewed meaning
        ↓
human reviews exact placement/source transformations
        ↓
publication preview → explicit publish → later duplicate cleanup
```

The dedicated interpretation stage is deliberately marked **coming soon**. Today, `interpret` already preserves raw/ambiguous material as exact Evidence and prevents it from being treated as direct canonical truth; the later stage will turn that boundary into an explicit reviewed interpretation workflow rather than silently blending raw records with durable meaning.

ContextCanon handles exact identity, provenance, validation, deterministic generation, and state transitions. The LLM handles semantic interpretation. The project owner decides which interpretation becomes durable project truth.

> [!IMPORTANT]
> **Use a strong reasoning-capable model for onboarding.** The semantic passes compare scattered evidence and infer structure or placement. ContextCanon can prove that returned JSON refers to the exact frozen bytes and accepted structure, but it cannot turn weak semantic judgment into a good project model.

Once the context is organized, smaller or local models can benefit from receiving the right narrow context during ordinary work. The occasional onboarding/restructuring pass is where stronger reasoning has unusually high leverage.

## Operator rule: use the generated PLAN, not this page, as your keyboard script

This page explains **why** the stages exist. It is deliberately not the place where an operator should reconstruct long snapshot IDs or remember which flags belong on which nearly-identical command. For a stable command map — including how to go backwards on a live project — use the [Onboarding CLI reference](onboarding-cli.md).

Create the workspace first with `contextcanon onboard init .`. From that moment, use **`contextcanon-onboarding/PLAN.md` as the executable console for that run**. Each numbered STEP keeps its short title, beginner-oriented explanation, completion checkbox, exact command, and artifact guidance together. The PLAN is orchestration only: it deliberately does **not** become a second configuration file for Catalog paths, Source identities, or project decisions.

Reusable Context configuration lives in `STEP-07-reusable-contexts.md`, where it belongs. ContextCanon keeps exact IDs, digests, and remembered machine state behind that human gate. `contextcanon-onboarding/README.md` remains the stable orientation page; `PLAN.md` tells you what to do next.

## 0. Install and create the operator workspace

For ordinary use, install ContextCanon as an isolated uv tool rather than into the project environment being onboarded. The repository README keeps the short current installation commands.

From the Git repository root:

```text
contextcanon --version
contextcanon onboard init .
```

The second command creates the visible `contextcanon-onboarding/` directory before any inventory/Evidence decision exists. Open its `PLAN.md`; all concrete run commands continue there. This page remains background/reference documentation rather than a keyboard script.

## 1. Tidy before durable references

Before ContextCanon creates durable Topic/Resource paths, use this cheapest moment to remove obvious repository/document clutter: accidental duplicates, `final-final` versions, clearly misplaced files, and temporary exports that should not become long-lived project landmarks.

This is deliberately **guidance rather than an automated rewrite**. ContextCanon does not move or delete project files during onboarding. The point is simply to avoid creating durable references to locations you already know are wrong.

## 2. Inventory and review the project files

Run from the Git repository root:

```text
contextcanon onboard inventory .
```

The command creates the visible onboarding workspace immediately and writes:

```text
contextcanon-onboarding/
├── README.md
├── PLAN.md
├── STEP-02-inventory-guide.md
└── STEP-02-inventory.csv
```

For a narrower first adoption, one or more repository-relative directories can be scanned:

```text
contextcanon onboard inventory . \
  --directory Jira \
  --directory P1
```

The inventory uses Git's visible tracked/untracked file set, respects normal Git ignores, and excludes ContextCanon's own machine/workspace material. It does **not** ask an LLM to decide what matters.

### What goes into Git

`contextcanon onboard init .` maintains a small marked block in the project `.gitignore`:

- the visible `contextcanon-onboarding/` workspace is transient and ignored;
- heavy `.context/onboarding/` Evidence snapshots, journals and temporary acceptance artifacts are ignored;
- two compact files remain Git-visible and should normally be committed:
  - `.context/onboarding/inventory-state.json` — inventory scope and deterministic rule configuration;
  - `.context/onboarding/inventory-acceptance.json` — the accepted per-path baseline including hashes plus reviewed `kind`, `handling`, `description` and `note`.

This split is deliberate. Before STEP 03, edits in the CSV are still unaccepted working state. STEP 03 turns that reviewed boundary into the compact durable acceptance files. After a fresh clone, `onboard init` followed by `onboard inventory` can regenerate the CSV from those committed files and surface current `new / changed / missing / unchanged` state without asking the owner to repeat prior classifications.

Later accepted structure/reusable-Context/placement decisions do not need the whole onboarding workspace as a second authority: after publication their meaning lives in canonical `CONTEXT.src.md`, Parent/Source relationships and reviewed project-source changes. The workspace remains useful review history but is not the canonical maintenance surface.

This does **not** yet mean that an already adopted project can be semantically re-onboarded by blindly replaying first-adoption publication. Incremental inventory recovery is supported; a full reviewed semantic update/re-onboarding contract remains separate work.


The CSV is the human gate. A generated local reference, `contextcanon-onboarding/STEP-02-inventory-guide.md`, explains **every** column, which fields the human edits, all handling/status values, and when a refresh is actually required. Keep that guide beside the CSV instead of reconstructing its semantics from this longer architecture page.

The important policy is:

- readable project documents and structured data are candidates for reviewed Evidence;
- raw meeting/chat/prestudy-like records default to `interpret`;
- opaque PDF/Word/PowerPoint-style originals default to `binary / ignore`; if relevant, provide a faithful same-basename Markdown transcription, which is recognized as `transcription / source`;
- ordinary source-code files are omitted from the default first-adoption CSV because per-file tracking would create noise/churn in real codebases; explicit custom rules can opt selected files back in;
- `.gitignore` is technical repository configuration and is ignored for semantic onboarding by default;
- Git submodule/gitlink directory entries are surfaced as `other / ignore`; the parent inventory does not descend into them, so onboard a relevant nested repository separately from its own Git root;
- unknown material remains `undecided` and blocks STEP 03 until the owner decides.

Rerunning STEP 02 is **not** part of editing the CSV. Rerun it only when repository files were added, changed, renamed/moved, or removed before STEP 03. Existing semantic decisions for known rows are preserved while machine-owned hashes/status are refreshed. The human-facing status `unchanged` means the path and bytes still match the previous inventory/accepted baseline.

Custom deterministic rules remain available for deliberate exceptions:

```text
contextcanon onboard inventory . \
  --rule "contracts/*.csv=structured-data:source" \
  --rule "src/architecture.py=source-code:interpret"
```

### Speedyboarding

A team/tool may generate its own CSV. At minimum it can provide:

```csv
path,kind,handling,description
P1/product.md,document,source,Product definition
P1/parameters.csv,structured-data,source,Canonical P1 parameter catalog
```

ContextCanon still compares that table with the real repository scope before accepting it. An incomplete custom table cannot make unlisted live non-source-code files disappear silently. Ordinary source code follows the same default omission boundary as the generated inventory unless it is deliberately opted in.

## 3. Freeze the reviewed Evidence

Once the CSV is reviewed:

```text
contextcanon onboard prepare . \
  --inventory contextcanon-onboarding/STEP-02-inventory.csv
```

Running STEP 03 is the explicit acceptance action for the inventory. ContextCanon refuses:

- live repository files in scope that are absent from the CSV;
- stale hashes when a listed file changed after inventory generation;
- non-ignored missing files;
- `undecided` handling;
- blocked/sensitive paths marked for inclusion;
- `source` / `interpret` rows without a description.

Only `source` and `interpret` rows are copied into the content-addressed Evidence snapshot. `lookup` remains deliberately outside that eager semantic set.

ContextCanon creates a snapshot such as:

```text
.context/onboarding/<evidence-digest>/
```

### What "frozen" means

Freezing does **not** lock the live repository. ContextCanon copies the reviewed Evidence into an immutable snapshot with exact paths, sizes and hashes. Later structure/placement work therefore refers to the same bytes even when the live repository continues changing.

Prepare a new snapshot when you intentionally accept a new Evidence basis. For compatibility, `contextcanon onboard prepare .` without `--inventory` still uses the earlier conservative automatic selection path; the generated onboarding PLAN uses the reviewed inventory path.

## 4. Discover the coarse structure

Use the snapshot from STEP 03:

```text
contextcanon onboard structure-instruction \
  .context/onboarding/<evidence-digest>
```

ContextCanon creates a visible human working directory:

```text
contextcanon-onboarding/
├── README.md
├── PLAN.md
└── STEP-04a-structure-instruction.md
```

`contextcanon-onboarding/PLAN.md` is the operator console for the in-progress onboarding. It contains the twelve numbered steps, with each step's explanation, checkbox, exact copy/paste command, and artifact guidance in one place, plus the external-LLM handoffs, human gates, reset commands, and latest ContextCanon-validated checkpoint. When returning after a pause, start there rather than reconstructing the command sequence from memory. `README.md` explains the workspace and points back to the PLAN.

Important onboarding Markdown is written directly as UTF-8 by ContextCanon rather than through shell redirection. This keeps the workflow reliable across shells — in particular Windows PowerShell codepage behavior — while `.context/` remains machine-oriented state.

Give the strong reasoning LLM:

- `contextcanon-onboarding/STEP-04a-structure-instruction.md` as the controlling assignment;
- read access only to the frozen snapshot's `evidence/` directory.

**For an IDE/agent model, do not use the live repository as its project/workspace.** Open a separate temporary IDE project containing only a copy of the instruction and frozen `evidence/` tree. Let the agent create only the requested JSON there, then copy that JSON back into `contextcanon-onboarding/`. The semantic reviewer does not need to run ContextCanon or edit the PLAN.

The model returns exactly one JSON object. Save it as:

```text
contextcanon-onboarding/STEP-04b-structure-proposal.json
```

The structure pass asks for:

- candidate local/grouping Nodes;
- one simple primary parent/child hierarchy for human orientation;
- larger knowledge bodies that should remain documentation, structured data, authoritative references, or imported corpora rather than becoming Nodes merely because they contain information;
- rationale, confidence, and exact frozen-Evidence provenance.

The current repository directory tree is **evidence about the project, not the taxonomy ContextCanon must preserve**. A proposed semantic Node may use an existing directory or a new repository-relative directory that does not exist yet. This matters especially for document-heavy repositories where many distinct knowledge areas currently live together in one folder. The human accepts the shelf map first; materialization can create the missing Node directories safely afterwards.

It deliberately does **not** distribute individual Rules or rewrite project prose yet.

## 5. Validate and edit the shelf map

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
contextcanon-onboarding/STEP-05-structure.md
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

## 6. Preview and materialize only missing Node skeletons

Before touching project Context files:

```text
contextcanon onboard structure-preview \
  .context/onboarding/<evidence-digest>
```

This writes:

```text
contextcanon-onboarding/STEP-06-structure-preview.md
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

A useful side effect appears during the later book-placement pass: forcing every maintained statement onto an explicit semantic shelf often surfaces responsibilities, boundaries, duplicates, and unresolved questions that were previously scattered through prose. Even before opening the detailed Evidence, the concise placement finding titles become a surprisingly useful project index. Treat that as review value, not as permission for the LLM to invent answers: unresolved questions remain explicit local State until the project resolves them.

## 7. Select reusable Contexts

The project's own shelves now exist. Before asking an LLM to place the books, establish any **reusable external Context Nodes** that should already apply to those shelves.

Run:

```text
contextcanon onboard reusable-contexts \
  .context/onboarding/<evidence-digest>
```

The first run creates:

```text
contextcanon-onboarding/STEP-07-reusable-contexts.md
```

This is a human-owned configuration/review surface, not part of the PLAN. It has three jobs:

1. **Catalog locations** — directories in which ContextCanon may discover compiled reusable Context Nodes;
2. **Assignments** — only the reusable relationships that should actually exist; there is deliberately no project-node × catalog-node matrix;
3. **Why** — the durable reason that each reusable Context applies at that project Node.

A typical edit looks like:

```markdown
## Catalog locations — editable

- `C:\Users\me\PycharmProjects\context-canon\nodes\library`

## Assignments — editable

Decision: `accept`

- **AI Workstation** (`.`) ← **Development Workflow** (`0.2.0-draft`)
  Why: Shared development workflow applies to the whole project.
```

Run the **same command again** after editing. ContextCanon scans the Catalog locations, fully verifies compiled packages, renders the available project/reusable Nodes for reference, resolves the human-readable assignment to stable IDs and exact package digests, and stores the validated machine state. You should not type Source UUIDs or package digests into the assignment.

An empty assignment list is valid: a project may simply have no reusable Contexts. Set `Decision` to `accept` only when the Catalog and sparse relationships are what you intend.

The relationship `Why` is not a Rule. A Rule says **what applies**; the Source relationship rationale says **why this whole reusable Context was composed here**. Publication carries that Why into local Source authoring and immutable import provenance, so descendants can later explain why an inherited reusable Context is in scope.

This gate deliberately happens **before** placement reasoning. The placement LLM therefore sees which reusable context already exists and can avoid promoting the same generic guidance again as a duplicate local Rule.

## 8. Generate the content-placement assignment

The second semantic pass is bound to the exact frozen Evidence, the human-edited project structure, and the exact reusable Context state accepted in Step 7:

```text
contextcanon onboard placement-instruction \
  .context/onboarding/<evidence-digest>
```

ContextCanon writes `contextcanon-onboarding/STEP-08a-placement-instruction.md`. Again, for an IDE/agent model, use a **separate temporary project** containing only that instruction plus a copy of the same frozen `evidence/` tree. Save/copy only its single JSON response back as `contextcanon-onboarding/STEP-08b-placement-proposal.json`.

The placement question is no longer "where is this text today?". It is:

> **Where should this meaning be maintained from now on?**

The v1 proposal distinguishes:

- `overview` — short stable orientation about what a Node owns;
- `rule` — durable project-local governance;
- `topic-resource` — deeper material maintained at its natural repository path and routed to by a Topic; this may be Markdown or structured textual data such as CSV/JSON/YAML;
- `state` / `plan` — current situation or future work, kept distinct from inherited governance;
- `ordinary-documentation` — useful documents that remain ordinary documents;
- `authority-mapping` — a local interpretation of fixed/authoritative material; Markdown must already be marked fixed in `STEP-05-structure.md`, while structured technical Evidence such as CSV/JSON may remain authoritative in its natural format;
- `unresolved` — ambiguity that must remain visible.

Actions are deliberately narrow:

- `promote` — make the destination ContextCanon surface the **single canonical maintenance surface** for the reviewed meaning. Initial publication may temporarily leave original mutable prose untouched for migration safety, but that duplicate is transitional;
- `reference` — only for `topic-resource`; keep the referenced resource as the maintenance surface and store routing rather than a copied second meaning;
- `keep` — intentionally remain outside canonical Node authoring;
- `map` — preserve fixed/technical authority in its natural format while recording the reviewed local relationship to it.

The non-redundancy goal is **one canonical meaning, many useful routes**. After promoted meaning is safely canonical, reviewed cleanup can remove true duplicates or leave a concise orientation/summary plus a link.

Preserve precise existing wording for facts, constraints, and Rules when it is already the best canonical wording. **Overview is a condensation task, not a quotation task:** summarize durable responsibility sharply and keep volatile compatibility detail in local State. Prefer several atomic findings over one long snake sentence.

The human cockpit has one additional safety net: when a promoted finding has one unambiguous mutable Markdown range but the LLM proposes no Source After edit, `STEP-10-placement.md` exposes that exact range as an optional human override. It defaults to `reject`, so it never creates cleanup work by itself.

### Mutable and fixed Markdown

Ordinary `project-documentation` Markdown is mutable by default. Markdown proposed as `authoritative-reference` or `imported-corpus` is preselected as fixed in `STEP-05-structure.md`, and the project owner can correct that list before placement.

- **mutable** means ContextCanon may become the future owner of promoted meaning, but the first publication still does not delete or rewrite the old document;
- **fixed** means the document remains authoritative and may only be referenced/mapped by this onboarding flow.

Structured textual data such as CSV/JSON/YAML is first-class Evidence and may remain a Topic/Resource or technical authority without conversion to Markdown. Opaque document authorities such as PDF/Word are deliberately unsupported directly; use the reviewed same-basename textual transcription path when their content matters.

## 9. Validate the placement proposal

Validate the LLM result:

```text
contextcanon onboard placement-validate \
  .context/onboarding/<evidence-digest>
```

ContextCanon checks the proposal against the frozen Evidence, accepted project structure, and exact reusable Context packages from STEP 07. STEP 09 is validation-only and intentionally has no separate artifact.

## 10. Review and revalidate `STEP-10-placement.md`

Create/load the human review:

```text
contextcanon onboard placement-review \
  .context/onboarding/<evidence-digest>
```

`STEP-10-placement.md` is the **human-owned placement decision file**, not merely a rendered report. Each project finding is destination-first: destination, decision, kind/action, maintained meaning, proposal rationale, and exact Evidence excerpts.

The owner may edit destination, decision, title, supported kind/action semantics, maintained wording, and review note directly in Markdown. ContextCanon allocates stable authoring identity once and preserves it across reloads.

Reusable Context assignments already accepted in Step 7 are **not another selection matrix here**. They appear only as compact traceability. If frozen Evidence suggests a genuinely new reusable relationship that was not established in STEP 07, that proposal remains an explicit human decision rather than being silently adopted.

Every successful placement-review validation regenerates read-only `STEP-10a-source-audit.md`, grouping source-before/source-after transformations by original file/range so semantic loss is easy to inspect.

## 11. Preview exact publication before mutation

Once every placement decision is resolved:

```text
contextcanon onboard placement-preview \
  .context/onboarding/<evidence-digest>
```

The command writes `contextcanon-onboarding/STEP-11-placement-preview.md` and changes no project file. The preview shows exact `CONTEXT.src.md` deltas, semantic Parent pins, reusable Source installation/provenance, accepted follow-ups, and reviewed mutable-document changes.

Preview verifies live Evidence-covered bytes and current Node source bytes. Publication later refuses if those inputs changed after preview.

## 12. Explicitly publish the reviewed placement

After reviewing the preview:

```text
contextcanon onboard placement-publish \
  .context/onboarding/<evidence-digest>
```

Publication transactionally materializes the semantics represented by the reviewed ContextCanon grammar: accepted local Overview/Rules/Topics/Resources, local State/Plan where supported, semantic Parent pins, and accepted exact reusable Sources. Existing Node identity and unrelated authored content are preserved.

The command writes `contextcanon-onboarding/STEP-12-placement-followup.md`. Generated Node `CONTEXT.md` files then expose inherited context and reusable provenance; a direct reusable Source's Why remains visible through immutable imported-context provenance in descendants.

Normal onboarding after Step 7 no longer asks the operator to repeat Catalog paths, Source Node IDs, or one-time Source-selection CLI syntax. ContextCanon retains those exact machine identities behind the accepted human gate.

### Visible workspace after the twelve-step path

A typical workspace is:

```text
contextcanon-onboarding/
├── README.md
├── PLAN.md
├── STEP-02-inventory.csv
├── STEP-02-inventory-guide.md
├── STEP-04a-structure-instruction.md
├── STEP-04b-structure-proposal.json
├── STEP-05-structure.md
├── STEP-06-structure-preview.md
├── STEP-07-reusable-contexts.md
├── STEP-08a-placement-instruction.md
├── STEP-08b-placement-proposal.json
├── STEP-10-placement.md
├── STEP-10a-source-audit.md
├── STEP-11-placement-preview.md
└── STEP-12-placement-followup.md
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
inventory                Which repository files exist and how should onboarding treat them?
prepare                  Which reviewed source/interpret bytes become exact Evidence?
structure instruction    What coarse semantic task is being asked?
reasoning LLM             What knowledge areas seem to exist?
structure validate        Does the proposal honestly cite those exact bytes?
human structure edit      What is the project's intended mental model?
preview/materialize       Which Node identities/files would actually be created?
reusable Context review   Which external Contexts apply to which shelves, and why?
placement instruction    Where should remaining project knowledge live?
reasoning LLM             What placements seem justified by Evidence?
placement validate        Is that JSON bound to Evidence + structure + accepted reusable Contexts?
human placement review    Do these moves/references/mappings actually make sense?
preview + publication     Which reviewed changes may safely become canonical?
```

Deterministic mechanisms handle identity, integrity, reproducibility, and state transitions. Reasoning models handle semantic interpretation. Humans own architecture and acceptance.

## Need the framework design and trust contract?

This page is the first-user walkthrough. Framework developers can inspect the internal [onboarding design and trust contract](../nodes/internal/framework-development/docs/onboarding-design.md). It explains compiler/schema boundaries, provenance rules, compatibility behavior, and why the deterministic/semantic stages are separated; it is **not** the operator CLI reference.

The structure-first/reusable-context/placement contracts were validated through the real `ai-workstation` onboarding line. The internal design document preserves those trust boundaries and compatibility decisions; this twelve-step walkthrough remains the current human-facing first-adoption flow.

State and Plan are local first-class Node authoring: accepted placement findings of those kinds are written to `## Local State` and `## Local Plan` in the destination `CONTEXT.src.md` and therefore appear in generated `CONTEXT.md`. They are intentionally not inherited through reusable Sources; current project situation and future project work stay local to the Node that owns them.
