# ContextCanon

**Give an AI the smallest useful context now — and an exact path to the rest when it matters.**

A common response to growing project knowledge is to assemble a **static context bundle**: an instruction file, curated prompt, or LLM-written summary containing what the model is supposed to know. It works until something important is missing; then the harness searches other repository files opportunistically. As the project changes, copied context drifts and every duplicate becomes another place to review and repair.

ContextCanon gives that context structure instead of another static copy.

```text
                     ┌─ ordinary task ───────────────> start working
small CONTEXT.md ────┼─ logging task ───────────────> required logging context
                     └─ architecture task ──────────> required architecture context
                                                       └─ optional deeper material
```

**Context becomes a map, not a preload list.**

A project keeps a compact dependable entry context, composes reusable context where useful, and exposes deeper knowledge only when a task needs it. Detailed guidance can live close to the narrow context where it belongs without bloating every higher-level overview; humans and agents still get clear landing points when they enter anywhere in the tree.

Reusable Sources also give shared guidance one maintained origin. When accepted Sources or authored context change, deterministic rebuilds propagate the updated result into consuming Nodes instead of requiring the same static prompt bundle to be rewritten in several places.

That matters especially for **smaller, cheaper and local models**. ContextCanon cannot turn a weak model into a strong one, but it can avoid wasting model capability on reconstructing project structure and conventions from scratch. A well-scoped task with the right project knowledge gives smaller models a better chance to do useful work reliably.

For local agentic workflows this changes the economics. Tokens are abundant rather than individually billed, so harnesses can inspect, iterate and run repeatedly without every autonomous step accumulating API cost. ContextCanon aims to make those plentiful local tokens more effective by feeding the model the right context instead of simply more context.

There is a second benefit once ContextCanon is used across many projects: **the project context itself becomes standardized**. A human, sparring partner, or task agent can enter an unfamiliar repository and ask the same questions in the same places: What applies here? Which reusable foundations were accepted? What is special about this project? What is the current state? Where is it going? Which deeper references matter for this task? What changed, and which stable identities are affected?

The answers still belong to each project, but the way they are organized no longer has to be rediscovered every time. ContextCanon therefore aims to reduce not only model context cost but also the repeated architectural orientation cost paid by humans and agents moving between repositories.

## Bring an existing project aboard

The onboarding workflow starts with the material your project already has — README, CONTRIBUTING, architecture and development documentation, selected configuration, existing agent instructions, and other likely context carriers — and turns that material into a **reviewed Context structure before it tries to rewrite or relocate individual knowledge**.

The larger `ai-workstation` experiment exposed an important ordering rule: **design the shelves before placing the books.** A strong reasoning LLM can reconstruct a surprisingly useful coarse project model from frozen evidence, but the project owner must own that model because future architecture and intended module boundaries cannot be inferred safely from repository archaeology alone.

The current structure-first experiment therefore uses two semantic passes:

```text
[ContextCanon · deterministic] freeze exact project evidence
        ↓
[ContextCanon · deterministic] generate structure-discovery assignment
        ↓
[Reasoning LLM · semantic] propose coarse Node tree + non-Node knowledge bodies
        ↓
[ContextCanon + Human] validate and edit structure.md
        ↓
[ContextCanon · deterministic] preview/materialize only missing Node skeletons
        ↓
[ContextCanon · deterministic] generate placement assignment bound to that structure
        ↓
[Reasoning LLM · semantic] propose where existing knowledge belongs
        ↓
[ContextCanon + Human] validate and inspect placement.md
        ↓
[later, only after review] publish/move/reference/map accepted knowledge safely
```

The LLM proposes semantics; it does not publish project truth. The project owner may rename, re-parent, remove, or add Nodes in the human-editable `structure.md`. The second pass is then forbidden from redesigning that hierarchy: it places knowledge into the accepted structure, preserves good original wording where possible, and marks wording as `exact`, `lightly-edited`, or `synthesized`.

> [!IMPORTANT]
> Onboarding is a difficult semantic review. Use a **strong reasoning-capable model**, not merely the fastest or cheapest general model available. ContextCanon can validate that returned JSON is well formed, bound to the accepted structure, and honestly points to frozen evidence; it cannot validate that a weak model made good architectural distinctions.

That does not conflict with ContextCanon's goal of making smaller/local models useful for normal project work. Once the context has been organized, those models benefit from receiving less but better-targeted information. The occasional context-structuring or restructuring step is where stronger reasoning has unusually high leverage.

### Structure-first experimental run

With the ContextCanon CLI available, start in the root of the Git repository you want to onboard:

```text
contextcanon onboard prepare .
```

The command prints the path of a frozen evidence snapshot under:

```text
.context/onboarding/<evidence-digest>/
```

The snapshot is an immutable review anchor, not a lock on the live repository. It lets different semantic instructions or human review iterations operate on **the same exact project bytes** until you deliberately choose a new evidence basis.

Generate the first semantic assignment:

```text
contextcanon onboard structure-instruction \
  .context/onboarding/<evidence-digest>
```

ContextCanon writes important working files itself as UTF-8 into the visible:

```text
contextcanon-onboarding/
```

This avoids shell-redirection/codepage surprises and keeps editable review artifacts out of both the repository root and the machine-oriented `.context/` tree.

Give `contextcanon-onboarding/structure-instruction.md` to a strong reasoning model together with read access to the frozen snapshot's `evidence/` directory. Save the returned JSON as:

```text
contextcanon-onboarding/structure-proposal.json
```

Validate and render the editable hierarchy:

```text
contextcanon onboard structure-validate .context/onboarding/<evidence-digest>
contextcanon onboard structure-review   .context/onboarding/<evidence-digest>
```

Now review and edit `contextcanon-onboarding/structure.md`. Indentation defines the primary human hierarchy. Existing proposal Nodes retain review-local keys; future/reserved Nodes can be added explicitly when the evidence and project owner justify them.

Before creating any missing Nodes:

```text
contextcanon onboard structure-preview .context/onboarding/<evidence-digest>
```

The preview protects existing Context Nodes by stable identity and shows exactly which missing skeletons would be created. When the coarse structure is satisfactory, explicit materialization creates only those missing skeletons:

```text
contextcanon onboard structure-materialize .context/onboarding/<evidence-digest>
```

Existing Nodes and ordinary project files are not rewritten by this step.

The second semantic pass is then generated from the **same frozen Evidence plus the exact edited structure digest**:

```text
contextcanon onboard placement-instruction \
  .context/onboarding/<evidence-digest>
```

Reusable immutable Source packages may be supplied explicitly with repeated `--catalog-package` arguments. The model compares generic-looking local guidance with those exact packages rather than inventing duplicate reusable rules.

Save the returned JSON as `contextcanon-onboarding/placement-proposal.json`, then:

```text
contextcanon onboard placement-validate .context/onboarding/<evidence-digest>
contextcanon onboard placement-review   .context/onboarding/<evidence-digest>
```

`placement.md` shows each source excerpt beside its proposed destination, operation and canonical wording. The current experiment deliberately stops there: destructive cleanup or publication of relocated knowledge is designed only after the real placement result has been reviewed.

The older single-pass first-adoption `instruction → validate → review → accept` path remains available while this larger experiment is being validated; it is not silently reinterpreted as the new two-pass contract.

For the user walkthrough and technical trust boundaries, read **[Onboard an existing project](docs/onboarding.md)**.

## One simple physical rule: a Node has its own directory

A **Context Node lives in exactly one node-root directory**.

That directory contains the files belonging to that Node:

```text
<node-root>/
├── CONTEXT.src.md       human-edited local context
├── CONTEXT.md           generated compact official entry
├── CONTEXT/             optional deeper generated resources
└── .context/            generated machine/package state
```

The node-root may be the root of a Git repository or a directory deeper inside it. A repository can therefore contain several Nodes.

The directory path is **location, not identity**. A Node keeps a stable ID when it is renamed or moved. Likewise, a directory that merely groups Nodes is not itself a Node unless it has its own ContextCanon files.

That distinction is important in this repository: `nodes/library/` and `nodes/internal/` are organizational categories; the actual Nodes are directories below them.

## The core model

A Context Node combines accepted reusable Sources with a small Local Delta:

```text
Context Source A ─────┐
Context Source B ─────┤
Context Source C ─────┼──> deterministic compile ──> Official Context Package
                      │
Local Delta ──────────┘
```

The human-facing package begins with:

```text
CONTEXT.md              compact entry; read first
CONTEXT/                optional deeper compiled/materialized context
```

`CONTEXT/` exists only when deeper resources are actually needed. `.context/` is separate machine territory for identities, accepted Sources, provenance, mappings, hashes and package metadata.

The editable `CONTEXT.src.md` answers a deliberately narrower question:

> What does this Node add or change compared with its Sources?

The generated `CONTEXT.md` answers:

> What applies here, and where should I go next if this task needs more?

## A small surprise: you have already entered ContextCanon

This repository does not explain ContextCanon from outside and then switch it on later.

**The repository root is already one of the smallest useful ContextCanon Nodes.**

Open [`CONTEXT.md`](CONTEXT.md): it contains no inherited Sources and no Rules. It gives a short Overview of why ContextCanon exists, then uses two Topics to route only the tasks that need more depth: onboarding an existing project and developing ContextCanon itself.

```text
                         ┌─ Topic ──> onboarding guide
ContextCanon Gateway ───┤
                         └─ Topic ──> ContextCanon Framework Development
                                           ▲              ▲
                                           │ Source       │ Source
                              ContextCanon Foundation     │
                                                   Development Workflow
```

That gives this repository **four real Nodes with four different jobs**:

- **[ContextCanon Gateway](CONTEXT.md)** — the compact repository entry. It demonstrates always-read orientation plus progressive disclosure to deeper task-specific material.
- **[ContextCanon Foundation](nodes/library/foundation/CONTEXT.md)** — the reusable baseline for ContextCanon-specific authoring and governance conventions.
- **[Development Workflow](nodes/library/development-workflow/CONTEXT.src.md)** — a reusable, Foundation-independent workflow for recoverable planning, proportional verification, explicit project-owner review, merge gates and post-merge baseline closure. It moved from `internal/` to `library/` with the **same stable Node ID** after `ai-workstation` proved its cross-project value.
- **[ContextCanon Framework Development](nodes/internal/framework-development/CONTEXT.md)** — Foundation plus Development Workflow plus only the ContextCanon-specific delta needed to design and implement the framework itself.

The Gateway arrows are **navigation**: Gateway does not inherit the onboarding guide or Framework Development as governance; Topics send relevant tasks there. The two upward arrows are **composition**: Framework Development accepts Foundation and Development Workflow as independent Sources and then adds a local delta.

Reusable Nodes do **not** automatically inherit Foundation merely because they live in the library. A library Node composes Foundation only when its own semantics actually depend on Foundation. Independent reusable concerns remain independent Sources so consumers can choose them separately instead of removing unwanted transitive governance later.

Nothing special was invented for bootstrapping. Gateway is an ordinary Context Node. If ContextCanon cannot represent "almost no context" cleanly while still giving a newcomer enough orientation to know where they are, it has failed one of its own most important design goals.

## ContextCanon is also for humans

The same structure that saves model tokens makes a project easier to inspect:

- Sources show which reusable context is accepted.
- `CONTEXT.src.md` shows what is special here.
- `CONTEXT.md` shows the compiled result without forcing the reader through inheritance archaeology.
- visible stable IDs make inherited changes explicit and traceable.
- Topics keep the main view short while preserving a clear route to depth.
- `STATE.md` and `PLAN.md` give a familiar route to where the project is now and where it is going.
- short `README.md` files at important directory boundaries explain ownership when a human browses the tree directly.

The framework deliberately uses constrained Markdown for human authoring and a boring machine representation underneath. Humans should not have to read YAML to understand the project; machines should not have to infer structure that can be represented exactly.

Across repositories, that consistency becomes a lightweight architectural interface: the domain changes, but the orientation workflow does not.

## Repository layout

```text
context-canon/
├── README.md
├── CONTRIBUTING.md
├── CHANGELOG.md
├── STATE.md
├── PLAN.md
│
├── CONTEXT.src.md       # ContextCanon Gateway node root = repository root
├── CONTEXT.md
├── CONTEXT/             # generated Gateway package resources
├── AGENTS.md
├── .goosehints
├── .context/
│
├── docs/                # Gateway-owned user documentation
│   ├── README.md
│   └── onboarding.md
│
└── nodes/               # organizes additional Nodes; not itself a Node
    ├── README.md
    ├── library/         # reusable Nodes distributed with ContextCanon
    │   ├── README.md
    │   ├── foundation/
    │   │   ├── README.md
    │   │   ├── CONTEXT.src.md
    │   │   ├── CONTEXT.md
    │   │   ├── docs/
    │   │   ├── CONTEXT/
    │   │   └── .context/
    │   └── development-workflow/
    │       ├── README.md
    │       ├── CONTEXT.src.md
    │       └── docs/
    │
    └── internal/        # Nodes used only to build/maintain ContextCanon
        ├── README.md
        └── framework-development/
            ├── README.md
            ├── CONTEXT.src.md
            ├── CONTEXT.md
            ├── docs/
            ├── CONTEXT/
            └── .context/
```

A useful distinction when browsing is explicit: **authored technical documents live below the Node that owns them; `CONTEXT/references/...` contains generated package copies, not a second maintenance surface.** The copies exist so an Official Context Package can live independently of the repository that originally authored its resources.

### Where contributors add Nodes

The tree should answer this without guesswork:

- a **reusable Node intended to ship with ContextCanon** goes in `nodes/library/<node-name>/`; it composes only the Sources its semantics actually require;
- a **ContextCanon-internal Node** goes in `nodes/internal/<node-name>/`;
- an **example or experiment** does not enter the library merely because it uses ContextCanon.

These category names are conventions of this repository. ContextCanon does not require other projects to use `library/` or `internal/`; it only requires each Node to have a clear node root.

## Immutable external Sources

Reusable Sources are not live includes from another Git repository. A consumer accepts an exact immutable Source package and can build offline from its own accepted state.

Compiler 0.4 separates candidate discovery from accepted inheritance:

```text
source fetch  → candidate only
source review → exact diff + consumer structural validation + receipt
source accept → immutable accepted package + exact updated pin
```

Normal `build` never fetches a missing Source implicitly. Git repository location, ref, and `node-path` are update transport metadata; stable Node identity plus version and exact digests define accepted state.

See [Immutable external Sources](nodes/internal/framework-development/docs/external-sources.md) for the complete contract.

## Why the package can contain more than Markdown

Topics are the first integration mechanism, not the final data model. The same progressive-disclosure pattern can later connect a task to:

- documentation and architecture,
- terminology and glossaries,
- patterns and example code,
- CSV files, schemas, tables and other structured data,
- PDFs, images and diagrams,
- skills and executable workflows,
- test material,
- operational experience and known pitfalls.

The constraint stays the same: adding knowledge must not imply eagerly loading it.

## Start here

If the five-second idea above is enough, the best next reads are:

- [Onboard an existing project](docs/onboarding.md) — first-user walkthrough and current structure-first experiment.
- [Development Workflow](nodes/library/development-workflow/CONTEXT.src.md) — reusable planning, review, merge-gate and baseline-closure workflow.
- [Concepts](nodes/internal/framework-development/docs/concepts.md) — Node roots, vocabulary and mental model.
- [Context composition](nodes/library/foundation/docs/composition.md) — Sources, local deltas, conflicts and updates.
- [Immutable external Sources](nodes/internal/framework-development/docs/external-sources.md) — exact packages, offline accepted state, candidate review and Git transport.
- [Official context](nodes/library/foundation/docs/official-context.md) — `CONTEXT.md`, optional `CONTEXT/`, and package boundaries.
- [Topics and context integration](nodes/library/foundation/docs/topics.md) — how deeper context is selected.
- [Architecture](nodes/internal/framework-development/docs/architecture.md) — deterministic compiler boundary and Node/package structure.
- [Compiler](nodes/internal/framework-development/docs/compiler.md) — implementation pipeline, invariants, tests, and deterministic capabilities.
- [Tests and GitHub Actions CI](nodes/internal/framework-development/docs/tests-and-ci.md) — the two deterministic test levels and how PR checks work.
- [Use-case walkthrough](nodes/internal/framework-development/docs/use-case-walkthrough.md) — where the design has already been stress-tested.

See [STATE.md](STATE.md) for the current project situation and [PLAN.md](PLAN.md) for the active development block.

## Influence

ContextCanon grew from experimenting with the filesystem-oriented progressive-disclosure ideas in Jake Van Clief and David McDermott's *Interpretable Context Methodology: Folder Structure as Agentic Architecture* and asking what would be needed for reusable, versioned context across independent projects, models and harnesses.

- Paper: https://arxiv.org/abs/2603.16021
- ICM repository: https://github.com/RinDig/Interpretable-Context-Methodology

ContextCanon is not an implementation of ICM. It focuses on composable Context Nodes, explicit local deltas, deterministic compilation, versioned Source acceptance, self-contained packages and harness-neutral project context.

## Project status

The current project-owner accepted `main` baseline is PR #9, squash-merged as `f7afe5c82942ecb9e3a04696455f8c960cc9b144`. Compiler 0.4 remains the deterministic foundation for immutable external Sources, exact accepted pins, offline composition, deterministic candidate review, explicit acceptance, generic Git candidate transport, and atomic publication/recovery.

The first-adoption onboarding trust boundary is accepted on `main`; PR #12 is now using the materially larger `ai-workstation` run to test the next product layer: **structure first, content placement second**. The real structure review has already demonstrated useful human correction of a plausible LLM-reconstructed project model, and it exposed the Development Workflow as genuinely reusable cross-project context.

PR #12 therefore also promotes that workflow from internal experimental context to the reusable Node Library with the same stable identity, while keeping Foundation as an independent optional Source rather than a forced transitive dependency.

The current review boundary stops after an evidence-rich placement proposal. Publication and cleanup of relocated knowledge will be designed only after the project owner has inspected the real `ai-workstation` placement result.
