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
human edits structure.md until it matches the project mental model
        ↓
ContextCanon previews/materializes only missing Node skeletons
        ↓
strong reasoning LLM places existing knowledge into that accepted structure
        ↓
human reviews placement.md with exact source excerpts
        ↓
only later: reviewed publication / cleanup / duplicate removal
```

ContextCanon handles exact identity, provenance, validation, deterministic generation, and state transitions. The LLM handles semantic interpretation. The project owner decides which interpretation becomes durable project truth.

> [!IMPORTANT]
> **Use a strong reasoning-capable model for onboarding.** The semantic passes compare scattered evidence and infer structure or placement. ContextCanon can prove that returned JSON refers to the exact frozen bytes and accepted structure, but it cannot turn weak semantic judgment into a good project model.

Once the context is organized, smaller or local models can benefit from receiving the right narrow context during ordinary work. The occasional onboarding/restructuring pass is where stronger reasoning has unusually high leverage.

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
└── structure-instruction.md
```

Important onboarding Markdown is written directly as UTF-8 by ContextCanon rather than through shell redirection. This keeps the workflow reliable across shells — in particular Windows PowerShell codepage behavior — while `.context/` remains machine-oriented state.

Give the strong reasoning LLM:

- `contextcanon-onboarding/structure-instruction.md` as the controlling assignment;
- read access only to the frozen snapshot's `evidence/` directory.

The model returns exactly one JSON object. Save it as:

```text
contextcanon-onboarding/structure-proposal.json
```

The structure pass asks for:

- candidate local/grouping Nodes;
- one simple primary parent/child hierarchy for human orientation;
- larger knowledge bodies that should remain documentation, authoritative references, or imported corpora rather than becoming Nodes merely because they contain information;
- exact reusable Source matches only when a verified Source catalog was supplied;
- rationale, confidence, and exact frozen-Evidence provenance.

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
contextcanon-onboarding/structure.md
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
- add missing Nodes;
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
contextcanon-onboarding/structure-preview.md
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

Materialization creates only missing Node skeletons and their deterministic generated package files. Each new Node receives one fresh stable UUID. Existing Nodes and ordinary project files are not rewritten. Running the command again is idempotent once all Nodes exist.

At this point **the shelves exist, but the books have not been distributed yet**.

## 5. Generate the content-placement assignment

The second semantic pass is bound to both the exact frozen Evidence digest and the digest of the human-edited `structure.md`:

```text
contextcanon onboard placement-instruction \
  .context/onboarding/<evidence-digest> \
  --catalog-package <package-root-a>
```

ContextCanon writes `contextcanon-onboarding/placement-instruction.md`. Give that instruction and **only the same frozen `evidence/` tree** to a strong reasoning LLM. Save its single JSON response as `contextcanon-onboarding/placement-proposal.json`.

The placement question is no longer "where is this text today?". It is:

> **Where should this meaning be maintained from now on?**

The v1 proposal distinguishes:

- `overview` — short stable orientation about what a Node owns;
- `rule` — durable project-local governance;
- `topic-resource` — deeper Markdown that remains maintained at its natural repository path and is routed to by a Topic;
- `state` / `plan` — current situation or future work, kept distinct from inherited governance;
- `ordinary-documentation` — useful documents that remain ordinary documents;
- `authority-mapping` — a local interpretation of Markdown deliberately marked fixed/authoritative in `structure.md`;
- `unresolved` — ambiguity that must remain visible.

Actions are deliberately narrow:

- `promote` — maintain the reviewed meaning canonically at the destination ContextCanon surface;
- `reference` — only for `topic-resource`; keep the referenced Markdown as the maintenance surface and store routing, not a copied second meaning;
- `keep` — intentionally remain outside canonical Node authoring;
- `map` — preserve fixed Markdown as authority while recording the reviewed local relationship to it.

Clear source wording should normally remain `exact`; use `lightly-edited` only for small self-containment changes and `synthesized` only when new wording is genuinely required.

### Mutable and fixed Markdown

During structure review, all proposed Markdown knowledge bodies are mutable by default. The owner may list selected proposed Markdown paths under `## Fixed Markdown` in `structure.md`.

- **mutable** means ContextCanon may become the future owner of promoted meaning, but the first publication still does not delete or rewrite the old document;
- **fixed** means the document remains authoritative and may only be referenced/mapped by this onboarding flow.

Non-Markdown document authorities such as PDF/Word are deliberately unsupported in this version rather than hidden behind an implicit conversion mechanism.

## 6. Validate and edit `placement.md`

Validate the LLM result using the same Source catalog:

```text
contextcanon onboard placement-validate \
  .context/onboarding/<evidence-digest> \
  --catalog-package <package-root-a>
```

Then create the human review:

```text
contextcanon onboard placement-review \
  .context/onboarding/<evidence-digest> \
  --catalog-package <package-root-a>
```

`placement.md` is the **human-owned decision file**, not merely a rendered report. Each finding is destination-first:

```text
Destination
Decision: pending | accept | reject
Kind / Action
Maintained meaning
Proposal rationale
Exact Evidence excerpts
```

The owner may edit destination, decision, title, kind/action within the supported semantics, maintained wording, and review note directly in this Markdown. ContextCanon allocates authoring identity for future Rules/Topics once and preserves it across reloads even when human-facing titles or wording change.

An existing `placement.md` is never silently regenerated over human edits. If the semantic proposal changes, ContextCanon requires a new review path instead of inventing a merge engine.

### Explicit owner-selected reusable Sources

An LLM may propose Source reuse only when frozen project Evidence supports it. A project owner may nevertheless choose an exact reusable Source for architectural reasons outside that Evidence:

```text
contextcanon onboard placement-review \
  .context/onboarding/<evidence-digest> \
  --catalog-package <package-root> \
  --owner-source N-001=<source-node-id>
```

The review labels that Source `owner-selected`; it does not pretend the choice came from project Evidence. Both Evidence-derived and owner-selected Sources remain bound to the exact immutable package identity.

## 7. Preview exact publication before mutation

Once every placement decision is resolved:

```text
contextcanon onboard placement-preview \
  .context/onboarding/<evidence-digest> \
  --catalog-package <package-root-a>
```

The command writes `contextcanon-onboarding/placement-preview.md` and changes no project file. The preview shows:

- the exact `CONTEXT.src.md` delta for every affected Node;
- exact reusable Source package/Git provenance that would be installed and pinned;
- accepted findings intentionally retained outside today's Node authoring grammar;
- mutable Markdown that may later be a duplicate-cleanup candidate, without applying that cleanup.

Preview verifies the live Evidence-covered project bytes and the current Node source bytes. Publication later refuses if those inputs changed after the preview.

## 8. Explicitly publish the reviewed placement

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

Accepted `state`, `plan`, `ordinary-documentation`, `authority-mapping`, and `unresolved` findings are **not lost** and are not forced into arbitrary prose. They remain in the exact machine acceptance record and in visible `placement-followup.md` for deliberate later handling.

The first publication also leaves README/CONTRIBUTING/architecture and other mutable Markdown untouched. Removing proven duplicate prose is a separate future cleanup operation with its own preview/review boundary.

Reusable Source packages are copied into the target Node's accepted local `.context/sources/<package-digest>/` state. The authored Source declaration carries durable Git origin, exact commit SHA and Node path derived from the clean supplied Source checkout; a transient developer checkout path is never written into project truth.

Publication is transaction-like and idempotent: it recompiles touched Nodes, writes generated outputs, records exact resulting package/source digests, rolls back on failure, and a second unchanged preview/publication produces no additional source delta.

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
    structure-instruction.md
    structure-proposal.json
    structure.md
    structure-preview.md
    placement-instruction.md
    placement-proposal.json
    placement.md
    placement-preview.md
    placement-followup.md
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
