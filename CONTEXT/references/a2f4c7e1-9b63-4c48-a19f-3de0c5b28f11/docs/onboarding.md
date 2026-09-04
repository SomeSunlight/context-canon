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
human configures reusable Context catalog + sparse assignments in STEP-05
        ↓
strong reasoning LLM places existing knowledge into the already composed structure
        ↓
human reviews STEP-08-placement.md with exact source excerpts
        ↓
publication preview → explicit publish → later duplicate cleanup
```

ContextCanon handles exact identity, provenance, validation, deterministic generation, and state transitions. The LLM handles semantic interpretation. The project owner decides which interpretation becomes durable project truth.

> [!IMPORTANT]
> **Use a strong reasoning-capable model for onboarding.** The semantic passes compare scattered evidence and infer structure or placement. ContextCanon can prove that returned JSON refers to the exact frozen bytes and accepted structure, but it cannot turn weak semantic judgment into a good project model.

Once the context is organized, smaller or local models can benefit from receiving the right narrow context during ordinary work. The occasional onboarding/restructuring pass is where stronger reasoning has unusually high leverage.

## Operator rule: use the generated PLAN, not this page, as your keyboard script

This page explains **why** the stages exist. It is deliberately not the place where an operator should reconstruct long snapshot IDs or remember which flags belong on which nearly-identical command.

As soon as Step 2 opens `contextcanon-onboarding/`, use **`contextcanon-onboarding/PLAN.md` as the executable console for that run**. Each numbered STEP keeps its short title, beginner-oriented explanation, completion checkbox, exact command, and artifact guidance together. The PLAN is orchestration only: it deliberately does **not** become a second configuration file for Catalog paths, Source identities, or project decisions.

Reusable Context configuration lives in `STEP-05-reusable-contexts.md`, where it belongs. ContextCanon keeps exact IDs, digests, and remembered machine state behind that human gate. `contextcanon-onboarding/README.md` remains the stable orientation page; `PLAN.md` tells you what to do next.

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

`contextcanon-onboarding/PLAN.md` is the operator console for the in-progress onboarding. It contains the ten numbered steps, with each step's explanation, checkbox, exact copy/paste command, and artifact guidance in one place, plus the external-LLM handoffs, human gates, reset commands, and latest ContextCanon-validated checkpoint. When returning after a pause, start there rather than reconstructing the command sequence from memory. `README.md` explains the workspace and points back to the PLAN.

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

A useful side effect appears during the later book-placement pass: forcing every maintained statement onto an explicit semantic shelf often surfaces responsibilities, boundaries, duplicates, and unresolved questions that were previously scattered through prose. Even before opening the detailed Evidence, the concise placement finding titles become a surprisingly useful project index. Treat that as review value, not as permission for the LLM to invent answers: unresolved questions remain explicit local State until the project resolves them.

## 5. Select reusable Contexts

The project's own shelves now exist. Before asking an LLM to place the books, establish any **reusable external Context Nodes** that should already apply to those shelves.

Run:

```text
contextcanon onboard reusable-contexts \
  .context/onboarding/<evidence-digest>
```

The first run creates:

```text
contextcanon-onboarding/STEP-05-reusable-contexts.md
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

## 6. Generate the content-placement assignment

The second semantic pass is bound to the exact frozen Evidence, the human-edited project structure, and the exact reusable Context state accepted in Step 5:

```text
contextcanon onboard placement-instruction \
  .context/onboarding/<evidence-digest>
```

ContextCanon writes `contextcanon-onboarding/STEP-06a-placement-instruction.md`. Give that instruction and **only the same frozen `evidence/` tree** to a strong reasoning LLM. Save its single JSON response as `contextcanon-onboarding/STEP-06b-placement-proposal.json`.

The placement question is no longer "where is this text today?". It is:

> **Where should this meaning be maintained from now on?**

The v1 proposal distinguishes:

- `overview` — short stable orientation about what a Node owns;
- `rule` — durable project-local governance;
- `topic-resource` — deeper Markdown maintained at its natural repository path and routed to by a Topic;
- `state` / `plan` — current situation or future work, kept distinct from inherited governance;
- `ordinary-documentation` — useful documents that remain ordinary documents;
- `authority-mapping` — a local interpretation of Markdown deliberately marked fixed/authoritative in `STEP-03-structure.md`;
- `unresolved` — ambiguity that must remain visible.

Actions are deliberately narrow:

- `promote` — make the destination ContextCanon surface the **single canonical maintenance surface** for the reviewed meaning. Initial publication may temporarily leave original mutable prose untouched for migration safety, but that duplicate is transitional;
- `reference` — only for `topic-resource`; keep referenced Markdown as the maintenance surface and store routing rather than a copied second meaning;
- `keep` — intentionally remain outside canonical Node authoring;
- `map` — preserve fixed Markdown as authority while recording the reviewed local relationship to it.

The non-redundancy goal is **one canonical meaning, many useful routes**. After promoted meaning is safely canonical, reviewed cleanup can remove true duplicates or leave a concise orientation/summary plus a link.

Preserve precise existing wording for facts, constraints, and Rules when it is already the best canonical wording. **Overview is a condensation task, not a quotation task:** summarize durable responsibility sharply and keep volatile compatibility detail in local State. Prefer several atomic findings over one long snake sentence.

The human cockpit has one additional safety net: when a promoted finding has one unambiguous mutable Markdown range but the LLM proposes no Source After edit, `STEP-08-placement.md` exposes that exact range as an optional human override. It defaults to `reject`, so it never creates cleanup work by itself.

### Mutable and fixed Markdown

Ordinary `project-documentation` Markdown is mutable by default. Markdown proposed as `authoritative-reference` or `imported-corpus` is preselected as fixed in `STEP-03-structure.md`, and the project owner can correct that list before placement.

- **mutable** means ContextCanon may become the future owner of promoted meaning, but the first publication still does not delete or rewrite the old document;
- **fixed** means the document remains authoritative and may only be referenced/mapped by this onboarding flow.

Non-Markdown document authorities such as PDF/Word are deliberately unsupported in this version rather than hidden behind an implicit conversion mechanism.

## 7. Validate the placement proposal

Validate the LLM result:

```text
contextcanon onboard placement-validate \
  .context/onboarding/<evidence-digest>
```

ContextCanon checks the proposal against the frozen Evidence, accepted project structure, and exact reusable Context packages from Step 5. There is intentionally no separate Step-07 artifact.

## 8. Review and revalidate `STEP-08-placement.md`

Create/load the human review:

```text
contextcanon onboard placement-review \
  .context/onboarding/<evidence-digest>
```

`STEP-08-placement.md` is the **human-owned placement decision file**, not merely a rendered report. Each project finding is destination-first: destination, decision, kind/action, maintained meaning, proposal rationale, and exact Evidence excerpts.

The owner may edit destination, decision, title, supported kind/action semantics, maintained wording, and review note directly in Markdown. ContextCanon allocates stable authoring identity once and preserves it across reloads.

Reusable Context assignments already accepted in Step 5 are **not another selection matrix here**. They appear only as compact traceability. If frozen Evidence suggests a genuinely new reusable relationship that was not established in Step 5, that proposal remains an explicit human decision rather than being silently adopted.

Every successful placement-review validation regenerates read-only `STEP-08a-source-audit.md`, grouping source-before/source-after transformations by original file/range so semantic loss is easy to inspect.

## 9. Preview exact publication before mutation

Once every placement decision is resolved:

```text
contextcanon onboard placement-preview \
  .context/onboarding/<evidence-digest>
```

The command writes `contextcanon-onboarding/STEP-09-placement-preview.md` and changes no project file. The preview shows exact `CONTEXT.src.md` deltas, semantic Parent pins, reusable Source installation/provenance, accepted follow-ups, and reviewed mutable-document changes.

Preview verifies live Evidence-covered bytes and current Node source bytes. Publication later refuses if those inputs changed after preview.

## 10. Explicitly publish the reviewed placement

After reviewing the preview:

```text
contextcanon onboard placement-publish \
  .context/onboarding/<evidence-digest>
```

Publication transactionally materializes the semantics represented by the reviewed ContextCanon grammar: accepted local Overview/Rules/Topics/Resources, local State/Plan where supported, semantic Parent pins, and accepted exact reusable Sources. Existing Node identity and unrelated authored content are preserved.

The command writes `contextcanon-onboarding/STEP-10-placement-followup.md`. Generated Node `CONTEXT.md` files then expose inherited context and reusable provenance; a direct reusable Source's Why remains visible through immutable imported-context provenance in descendants.

Normal onboarding after Step 5 no longer asks the operator to repeat Catalog paths, Source Node IDs, or one-time Source-selection CLI syntax. ContextCanon retains those exact machine identities behind the accepted human gate.

### Visible workspace after the ten-step path

A typical workspace is:

```text
contextcanon-onboarding/
├── README.md
├── PLAN.md
├── STEP-02a-structure-instruction.md
├── STEP-02b-structure-proposal.json
├── STEP-03-structure.md
├── STEP-04-structure-preview.md
├── STEP-05-reusable-contexts.md
├── STEP-06a-placement-instruction.md
├── STEP-06b-placement-proposal.json
├── STEP-08-placement.md
├── STEP-08a-source-audit.md
├── STEP-09-placement-preview.md
└── STEP-10-placement-followup.md
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
prepare                  Which exact project bytes may be considered?
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

## Need the exact contracts and safety details?

This page is the first-user walkthrough. Compiler/schema details and the older accepted onboarding trust contract remain in the [onboarding technical reference](../nodes/internal/framework-development/docs/onboarding-reference.md#technical-reference).

The structure-first/reusable-context/placement contracts are validated through the real `ai-workstation` exercise in PR #13. The older single-pass technical reference remains useful for its trust-boundary details; the ten-step walkthrough on this page is the current human-facing structure-first path.

State and Plan are local first-class Node authoring: accepted placement findings of those kinds are written to `## Local State` and `## Local Plan` in the destination `CONTEXT.src.md` and therefore appear in generated `CONTEXT.md`. They are intentionally not inherited through reusable Sources; current project situation and future project work stay local to the Node that owns them.
