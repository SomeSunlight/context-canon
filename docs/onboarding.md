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

The second semantic pass is bound to both:

- the exact frozen Evidence digest;
- the exact digest of the human-edited `structure.md`.

Generate it with:

```text
contextcanon onboard placement-instruction \
  .context/onboarding/<evidence-digest>
```

ContextCanon writes:

```text
contextcanon-onboarding/placement-instruction.md
```

The placement LLM is explicitly told **not to redesign the structure**. Its primary question is:

> Where should this existing information live?

rather than:

> How can I rewrite this into more abstract ContextCanon prose?

The proposal distinguishes at least these operations:

- **keep** — leave ordinary documentation or unresolved information where it naturally lives;
- **move** — project-owned canonical governance/state is buried in an accidental location and should later become canonical at a destination Node;
- **reference** — a document/resource is already in the right natural location; the Node should route to it rather than duplicate it;
- **map** — preserve an authoritative policy/standard and explicitly map project context to it rather than rewriting the authority as local truth.

For Rules, State, Plan, or authority mappings the model also records wording origin:

- `exact` — good source wording is retained verbatim;
- `lightly-edited` — only small changes are necessary to make the fragment self-contained;
- `synthesized` — no good existing wording exists and a new formulation is genuinely required.

Clear existing language should normally stay clear existing language.

## 6. Reuse exact Sources instead of creating duplicates

Reusable immutable Source packages can be shown to the placement reviewer explicitly:

```text
contextcanon onboard placement-instruction \
  .context/onboarding/<evidence-digest> \
  --catalog-package <package-root-a> \
  --catalog-package <package-root-b>
```

The LLM may propose a Source reuse only when frozen project Evidence supports the match. The proposal is bound to the exact Source Node ID, name, version, normalized digest, and package digest that the reviewer saw.

A reusable Node does not automatically imply ContextCanon Foundation or another Source. Dependencies are properties of the reusable package itself. Independent Sources stay independently selectable.

If the project owner wants a Source for architectural reasons that are **not represented in the frozen Evidence**, the semantic reviewer must not manufacture evidence from chat memory. That is a legitimate human follow-up requirement rather than permission to weaken provenance. The larger real-project experiment is being used to determine the cleanest owner-facing mechanism for such explicit Source selection.

## 7. Validate and inspect the placement proposal

Give `placement-instruction.md` plus the same frozen `evidence/` directory to the reasoning LLM. Save its JSON response as:

```text
contextcanon-onboarding/placement-proposal.json
```

Validate it using the same Source catalog, when one was supplied to the LLM:

```text
contextcanon onboard placement-validate \
  .context/onboarding/<evidence-digest> \
  --catalog-package <package-root-a>
```

Then render the evidence-rich human review:

```text
contextcanon onboard placement-review \
  .context/onboarding/<evidence-digest> \
  --catalog-package <package-root-a>
```

ContextCanon writes:

```text
contextcanon-onboarding/placement.md
```

For every finding it shows:

```text
exact source excerpt
        ↓
proposed destination Node
        ↓
keep / move / reference / map
        ↓
proposed canonical wording + wording origin
```

Reusable Source matches are shown separately with exact package identity and the project Evidence that motivated the match.

## 8. Current experimental stop point

**The structure-first experiment deliberately stops after `placement.md`.**

There is not yet a command that automatically:

- rewrites existing project documentation;
- removes duplicate old Rules;
- writes the placement proposal into every Node;
- installs a proposed external Source;
- splices prose automatically into STATE/PLAN;
- performs destructive cleanup.

That boundary is intentional. The first real `ai-workstation` placement result should be reviewed before ContextCanon hardens publication semantics for moving, referencing, mapping, or cleaning up real project knowledge.

This is vertical validation before framework hardening: first prove that the resulting structure and placement are useful to the project owner, then automate exactly the repetitive part that real use shows is safe.

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
