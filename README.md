# ContextCanon

**Give an AI the smallest useful context now — and an exact path to the rest when it matters.**

Most project context grows in one direction: more instructions, more documents, more examples, more tokens loaded before the real work even starts.

ContextCanon gives that context structure.

```text
                     ┌─ ordinary task ───────────────> start working
small CONTEXT.md ────┼─ logging task ───────────────> required logging context
                     └─ architecture task ──────────> required architecture context
                                                       └─ optional deeper material
```

**Context becomes a map, not a preload list.**

A project keeps a compact entry context, composes reusable context where useful, and exposes deeper knowledge only when a task needs it. The result stays readable for humans, cheap for LLM context windows, and precise enough for deterministic tooling.

That matters especially for **smaller, cheaper and local models**. ContextCanon cannot turn a weak model into a strong one, but it can avoid wasting model capability on reconstructing project structure and conventions from scratch. A well-scoped task with the right project knowledge gives smaller models a better chance to do useful work reliably.

For local agentic workflows this changes the economics. Tokens are abundant rather than individually billed, so harnesses can inspect, iterate and run repeatedly without every autonomous step accumulating API cost. ContextCanon aims to make those plentiful local tokens more effective by feeding the model the right context instead of simply more context.

There is a second benefit once ContextCanon is used across many projects: **the project context itself becomes standardized**. A human, sparring partner, or task agent can enter an unfamiliar repository and ask the same questions in the same places: What applies here? Which reusable foundations were accepted? What is special about this project? What is the current state? Where is it going? Which deeper references matter for this task? What changed, and which stable identities are affected?

The answers still belong to each project, but the way they are organized no longer has to be rediscovered every time. ContextCanon therefore aims to reduce not only model context cost but also the repeated architectural orientation cost paid by humans and agents moving between repositories.

## Bring an existing project aboard

The onboarding workflow starts with the material your project already has — README, CONTRIBUTING, architecture and development documentation, selected configuration, existing agent instructions, and other likely context carriers — and turns that material into a **reviewable proposal**.

The key idea is that ContextCanon does **not** hand the whole process to an LLM. Deterministic software handles the parts that can be exact; one external LLM step handles the semantic classification that ordinary code cannot reliably perform.

```text
[ContextCanon · deterministic] freeze exact project evidence
        ↓
[ContextCanon · deterministic] generate the semantic assignment
        ↓
[Your reasoning LLM · semantic] read frozen evidence and return proposal.json
        ↓
[ContextCanon · deterministic] validate JSON structure and provenance
        ↓
[Human · explicit decision] review and accept/correct
        ↓
canonical ContextCanon context
```

The LLM's entire handoff back to ContextCanon is **one JSON file**. It may propose meaning, but it cannot silently publish project truth.

> [!IMPORTANT]
> Onboarding is a difficult semantic review. Use a **strong reasoning-capable model**, not merely the fastest or cheapest general model available. ContextCanon can validate that the JSON is well formed and honestly points to frozen evidence; it cannot validate that a weak model made good architectural distinctions.

That does not conflict with ContextCanon's goal of making smaller/local models useful for normal project work. Once the context has been organized, those models benefit from receiving less but better-targeted information. The occasional context-structuring step is where stronger reasoning has unusually high leverage.

### First run

With the ContextCanon CLI available, start in the root of the Git repository you want to onboard:

```text
contextcanon onboard prepare .
```

The command prints the path of a frozen evidence snapshot under:

```text
.context/onboarding/<evidence-digest>/
```

That snapshot is the exact material the later semantic review is allowed to use. ContextCanon selects likely high-value project documents conservatively; it does not simply feed the whole repository to a model.

Next generate the framework-owned instruction for that exact snapshot:

```text
contextcanon onboard instruction .context/onboarding/<evidence-digest> > onboarding-instruction.md
```

Now leave deterministic ContextCanon for one step: give `onboarding-instruction.md` to a **strong reasoning LLM or agent harness** together with read access to the snapshot's `evidence/` directory. The model must return exactly one `contextcanon/onboarding-proposal/v0` JSON object; save it as `proposal.json`.

ContextCanon deliberately does not choose a provider or model for you. Configure the model run so the generated ContextCanon instruction controls the task and the **frozen evidence is the project evidence**; do not let the harness separately inject live-project `AGENTS.md`, workspace instructions, memories, or other project context as governing instructions.

The model is asked to sort useful project knowledge into a small set of review categories: project-local Rules, existing reusable Sources, candidates for new reusable context, Topic/Resource material, current state or plans, ordinary documentation that should remain ordinary documentation, and unresolved questions.

It is also told not to assume README or other conventional files are automatically current. For claims about the **currently implemented system**, direct implementation/configuration/manifest/CI/test evidence outweighs contradictory descriptive documentation. Documentation and meaningful source comments remain important for intent, rationale, workflow, constraints and target design. Unclear conflicts must remain visible instead of being silently reconciled.

Back inside deterministic ContextCanon, validate the model's JSON:

```text
contextcanon onboard validate .context/onboarding/<evidence-digest> proposal.json
```

Validation checks the proposal structure and every claimed evidence reference against the frozen snapshot. A valid proposal is still **only a proposal**.

> [!NOTE]
> The current implementation deliberately stops at this validated review artifact. The next development block adds the human review and explicit acceptance step that may create or replace canonical `CONTEXT.src.md`. Until that exists, do not treat a valid proposal as accepted project truth.

For the complete user walkthrough first, and the technical details only after that, read **[Onboard an existing project](docs/onboarding.md)**.

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
                         ┌─ onboarding Topic ──> onboarding guide
ContextCanon Gateway ───┤
                         └─ development Topic ─> ContextCanon Framework Development
                                                        ▲
                                                        │ Source
                                               ContextCanon Foundation
```

That gives this repository three real Nodes with three different jobs:

- **[ContextCanon Gateway](CONTEXT.md)** — the compact repository entry. It demonstrates always-read orientation plus progressive disclosure to deeper task-specific material.
- **[ContextCanon Foundation](nodes/library/foundation/CONTEXT.md)** — the common reusable baseline of the ContextCanon Node Library.
- **[ContextCanon Framework Development](nodes/internal/framework-development/CONTEXT.md)** — Foundation plus only the additional context needed to design and implement ContextCanon itself.

The Gateway arrows are **navigation**: Gateway does not inherit the onboarding guide or Framework Development as governance; Topics send relevant tasks there. The Foundation arrow is **composition**: Framework Development accepts Foundation as a Source and adds a local delta.

Every reusable Node that ships in the **ContextCanon Node Library** will compose Foundation directly or transitively. The Gateway is not a library module; it is the deliberately small entry Node for this repository.

Nothing special was invented for bootstrapping. Gateway is an ordinary Context Node. If ContextCanon cannot represent "almost no context" cleanly while still giving a newcomer enough orientation to know where they are, it has failed one of its own most important design goals.

## ContextCanon is also for humans

The same structure that saves model tokens makes a project easier to inspect:

- Sources show which reusable context is accepted.
- `CONTEXT.src.md` shows what is special here.
- `CONTEXT.md` shows the compiled result without forcing the reader through inheritance archaeology.
- visible stable IDs make inherited changes explicit and traceable.
- Topics keep the main view short while preserving a clear route to depth.
- `STATE.md` and `PLAN.md` give a familiar route to where the project is now and where it is going.

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
├── AGENTS.md
├── .goosehints
├── .context/
│
├── nodes/               # organizes additional Nodes; not itself a Node
│   ├── README.md
│   ├── library/         # reusable Nodes distributed with ContextCanon
│   │   ├── README.md
│   │   └── foundation/  # ContextCanon Foundation node root
│   │       ├── CONTEXT.src.md
│   │       ├── CONTEXT.md
│   │       ├── CONTEXT/
│   │       └── .context/
│   │
│   └── internal/        # Nodes used only to build/maintain ContextCanon
│       ├── README.md
│       └── framework-development/   # framework-development node root
│           ├── CONTEXT.src.md
│           ├── CONTEXT.md
│           ├── CONTEXT/
│           └── .context/
│
└── docs/                # human-edited specification and design documentation
```

### Where contributors add Nodes

The tree should answer this without guesswork:

- a **reusable Node intended to ship with ContextCanon** goes in `nodes/library/<node-name>/` and composes Foundation directly or transitively;
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

See [Immutable external Sources](docs/external-sources.md) for the complete contract.

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

- [Onboard an existing project](docs/onboarding.md) — first-user walkthrough from an existing repository to a validated proposal.
- [Concepts](docs/concepts.md) — Node roots, vocabulary and mental model.
- [Context composition](docs/composition.md) — Sources, local deltas, conflicts and updates.
- [Immutable external Sources](docs/external-sources.md) — exact packages, offline accepted state, candidate review and Git transport.
- [Official context](docs/official-context.md) — `CONTEXT.md`, optional `CONTEXT/`, and package boundaries.
- [Topics and context integration](docs/topics.md) — how deeper context is selected.
- [Architecture](docs/architecture.md) — deterministic compiler boundary and Node/package structure.
- [Compiler](docs/compiler.md) — implementation pipeline, invariants, tests, and deterministic capabilities.
- [Use-case walkthrough](docs/use-case-walkthrough.md) — where the design has already been stress-tested.

See [STATE.md](STATE.md) for the current project situation and [PLAN.md](PLAN.md) for the active development block.

## Influence

ContextCanon grew from experimenting with the filesystem-oriented progressive-disclosure ideas in Jake Van Clief and David McDermott's *Interpretable Context Methodology: Folder Structure as Agentic Architecture* and asking what would be needed for reusable, versioned context across independent projects, models and harnesses.

- Paper: https://arxiv.org/abs/2603.16021
- ICM repository: https://github.com/RinDig/Interpretable-Context-Methodology

ContextCanon is not an implementation of ICM. It focuses on composable Context Nodes, explicit local deltas, deterministic compilation, versioned Source acceptance, self-contained packages and harness-neutral project context.

## Project status

Compiler 0.4 is the accepted deterministic baseline. It provides immutable external Source packages, exact accepted pins, offline composition, deterministic candidate review, explicit acceptance, generic Git candidate transport, and atomic publication/recovery guarantees in addition to the earlier compiler, diff, composition, and progressive-disclosure capabilities.

The first user-reviewed onboarding slice is now merged. ContextCanon can deterministically freeze onboarding evidence, render the framework-owned semantic assignment, accept an explicitly supplied reusable Source catalog, and validate the external LLM's provenance-rich JSON proposal.

The active next block is **human review and explicit onboarding acceptance**: make a validated proposal easy to inspect and correct, require an explicit human decision before canonical ContextCanon source is created or replaced, and immediately run the normal deterministic compiler after acceptance.

Only after that review/acceptance path is stable will ContextCanon run the larger 1:1 onboarding test on a materially larger existing repository. That test should expose remaining semantic and workflow questions rather than reopen already solved compiler/package mechanics.
