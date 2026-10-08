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

Reusable Parent Context gives shared guidance one maintained origin, while References attach useful background without turning it into governance. Deterministic builds render the accepted result without rewriting copied prompt bundles. Dependent Child Nodes advance to newer Parent snapshots only through an explicit propagation review; Reference updates stay local.

That matters especially for **smaller, cheaper and local models**. ContextCanon cannot turn a weak model into a strong one, but it can avoid wasting model capability on reconstructing project structure and conventions from scratch. A well-scoped task with the right project knowledge gives smaller models a better chance to do useful work reliably.

For local agentic workflows this changes the economics. Tokens are abundant rather than individually billed, so harnesses can inspect, iterate and run repeatedly without every autonomous step accumulating API cost. ContextCanon aims to make those plentiful local tokens more effective by feeding the model the right context instead of simply more context.

There is a second benefit once ContextCanon is used across many projects: **the project context itself becomes standardized**. A human, sparring partner, or task agent can enter an unfamiliar repository and ask the same questions in the same places: What applies here? Which reusable foundations were accepted? What is special about this project? What is the current state? Where is it going? Which deeper references matter for this task? What changed, and which stable identities are affected?

The answers still belong to each project, but the way they are organized no longer has to be rediscovered every time. ContextCanon therefore aims to reduce not only model context cost but also the repeated architectural orientation cost paid by humans and agents moving between repositories.

## Bring an existing project aboard

### 1. Install the CLI

ContextCanon is meant to be a standalone command-line tool, independent of the Python environment of the project you are onboarding. The recommended installation uses [uv](https://docs.astral.sh/uv/).

Install uv once:

**Windows**

```powershell
winget install --id=astral-sh.uv -e
```

**Linux / macOS**

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then install ContextCanon directly from GitHub:

```text
uv tool install git+https://github.com/SomeSunlight/context-canon.git
uv tool update-shell
contextcanon --version
```

ContextCanon requires Python 3.11 or newer; uv can obtain a compatible managed Python automatically when needed. If the shell has just been updated, open a new terminal before retrying `contextcanon --version`.

### 2. Let ContextCanon create the runbook

Open the Git repository you want to onboard and run:

```text
contextcanon onboard init .
```

This creates:

```text
contextcanon-onboarding/
├── README.md
├── PLAN.md
└── STEP-02-inventory-guide.md
```

**Now open `contextcanon-onboarding/PLAN.md` and continue there.** From this point on, the generated PLAN is the operator console for the concrete onboarding run: it tells you what to do next, gives the exact commands, and records the validated checkpoint so you can resume later without remembering this README or an old chat.

The onboarding itself deliberately separates deterministic mechanics from semantic judgment:

```text
tidy project material
        ↓
inventory + human triage
        ↓
freeze exact reviewed Evidence
        ↓
fresh isolated reasoning handoff → shelf proposal
        ↓
human accepts/edits the structure
        ↓
optionally compose reusable Context
        ↓
fresh isolated reasoning handoff → book-placement proposal
        ↓
human reviews semantic placement + source transformations
        ↓
preview + explicit publication
```

The LLM proposes semantics; it does not publish project truth. Each semantic pass gets a fresh **Semantic Handoff Workspace** containing only the task instruction, the exact frozen Evidence, and accepted state required for that pass. ContextCanon regains control for deterministic validation; the project owner remains responsible for architecture and acceptance. For onboarding, use a strong reasoning-capable model even if ordinary later tasks can run on smaller/local models.

For the conceptual walkthrough, see **[Onboard an existing project](docs/onboarding.md)**. For a stable command map — especially reset/restart — see **[Onboarding CLI](docs/onboarding-cli.md)**. During an actual run, follow the generated `contextcanon-onboarding/PLAN.md`.

## Maintain an onboarded project

After onboarding, the normal operator loop is short:

```text
inspect / update  →  review downstream propagation when needed  →  build  →  check
```

Start with **[Maintain an existing ContextCanon project](docs/maintenance.md)**. It explains Parent versus Reference from the user's point of view, the three-question propagation review, and when to fix upstream versus use a justified local Override/Remove. Use the **[CLI quick reference](docs/cli.md)** as the compact command map; exact flags remain available through `contextcanon <command> --help`.

`contextcanon propagate` reviews only semantic descendants of the selected Context Node. `--all` deliberately broadens the review scope to every Parent graph in the repository; it is not blanket approval.

## Edit the local Context source

Edit `CONTEXT.src.md`; ContextCanon generates `CONTEXT.md` from it. Each meaningful section has a short format comment and the source links to an offline `CONTEXT-format.md` guide beside it. For new Rules, Topics and Resources, use the examples and omit IDs; build adds them automatically.

`contextcanon build --all .` also migrates existing sources: it puts Context Imports first, refreshes authoring help and places historical State/Plan identity comments after their entries. Existing IDs and accepted Parent/Reference pins are preserved. `check` remains read-only. See [Editing CONTEXT.src.md](docs/context-source-format.md) for the complete syntax and examples.

## Four concerns that should not be tangled together

ContextCanon deliberately does **not** try to be the agent, the development process and the forge at the same time.

| Concern | Answers | Examples |
| --- | --- | --- |
| **ContextCanon** | What applies here, and where should I go deeper for this task? | Context Nodes, Parents, References, Topics, State, Plan |
| **Development Workflow** | How does a change move from reason to accepted baseline? | Issue → branch → Pull Request → review → checks → merge |
| **Workflow provider** | Which infrastructure implements those familiar development objects? | GitHub, GitHub Local |
| **Agent / harness** | Which model or tool actually performs the work? | Copilot, Goose, Hermes, ChatGPT, other IDE/CLI agents |

The separation is practical rather than theoretical. A project can change agent without rewriting its Context. It can use GitHub or a local GitHub-compatible provider without inventing a second workflow language for the model. And ContextCanon remains useful for projects that do not use the Development Workflow at all.

**Abstraction stays below normal model context.** The reusable Development Workflow keeps the familiar words Issue, branch, Pull Request, review, checks and merge. A concrete provider composes that workflow and makes those words operational. ContextCanon does not introduce an `implements` keyword or a parallel abstract vocabulary just to express this relationship.

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

A Context Node combines normative Parents, optional informational References, and a small Local Delta:

```text
Parent Context A ─────┐
Parent Context B ─────┼──> normative effective Context ─┐
Local Delta ──────────┘                                 ├──> Official Context Package
Reference Context .... informational only .............┘
```

The human-facing package begins with:

```text
CONTEXT.md              compact entry; read first
CONTEXT/                optional deeper compiled/materialized context
```

`CONTEXT/` exists only when deeper resources are actually needed. `.context/` is separate machine territory for identities, accepted immutable imports, provenance, mappings, hashes and package metadata.

The editable `CONTEXT.src.md` answers a deliberately narrower question:

> What does this Node add or change compared with its Parents, and which direct References are useful here?

The generated `CONTEXT.md` answers:

> What applies here, and where should I go next if this task needs more?

## A small surprise: you have already entered ContextCanon

This repository does not explain ContextCanon from outside and then switch it on later.

**The repository root is already one of the smallest useful ContextCanon Nodes.**

Open [`CONTEXT.md`](CONTEXT.md): it contains no inherited Parents and no Rules. It gives a short Overview of why ContextCanon exists, then routes only tasks that need more depth.

```text
                         ┌─ Topic ──> onboarding / maintenance docs
ContextCanon Gateway ───┤
                         └─ Topic ──> ContextCanon Framework Development
                                           ▲              ▲
                                           │ Parent       │ Parent
                              ContextCanon Foundation     │
                                                   Development Workflow

Reusable workflow providers:
                         Development Workflow
                                  ▲
                                  │ Parent
                           ┌──────┴──────┐
                         GitHub      GitHub Local
```

That gives this repository **six real Nodes with different jobs**:

- **[ContextCanon Gateway](CONTEXT.md)** — the compact repository entry and progressive-disclosure router.
- **[ContextCanon Foundation](nodes/library/foundation/CONTEXT.md)** — reusable ContextCanon authoring/composition/governance conventions.
- **[Development Workflow](nodes/library/development-workflow/CONTEXT.src.md)** — the reusable Issue/branch/Pull Request/review/checks/merge lifecycle, independent of a concrete forge.
- **[GitHub](nodes/library/github/CONTEXT.md)** — the concrete provider for ordinary github.com development infrastructure.
- **[GitHub Local](nodes/library/github-local/CONTEXT.md)** — the concrete provider for a local GitHub-compatible development surface; the executable `github.local` runtime is intentionally a separate future project.
- **[ContextCanon Framework Development](nodes/internal/framework-development/CONTEXT.md)** — Foundation plus Development Workflow plus only the ContextCanon-specific delta needed to design and implement this framework.

The Gateway arrows are **navigation**: Topics send a relevant task to deeper material without inheriting all of it. The upward arrows are **normative Parent composition**: one Node accepts another Node as governing Context.

The provider diagram uses “workflow/provider” as a familiar software analogy, not as extra ContextCanon grammar. GitHub and GitHub Local are ordinary reusable Nodes that compose Development Workflow. Likewise, reusable Nodes do **not** automatically inherit Foundation merely because they live in the library; every Parent relationship is an explicit semantic product decision.

Nothing special was invented for bootstrapping. Gateway is an ordinary Context Node. If ContextCanon cannot represent “almost no context” cleanly while still giving a newcomer enough orientation to know where they are, it has failed one of its own most important design goals.

## ContextCanon is also for humans

The same structure that saves model tokens makes a project easier to inspect:

- Parent/Reference relationships show which reusable Context applies normatively and which is informational only.
- `CONTEXT.src.md` shows what is special here.
- `CONTEXT.md` shows the compiled result without forcing the reader through inheritance archaeology.
- visible stable IDs make inherited changes explicit and traceable.
- Topics keep the main view short while preserving a clear route to depth.
- `STATE.md` and `PLAN.md` give a familiar route to where the project is now and where it is going.
- short `README.md` files at important directory boundaries explain ownership when a human browses the tree directly.

The framework deliberately uses constrained Markdown for human authoring and a boring machine representation underneath. Humans should not have to read YAML to understand the project; machines should not have to infer structure that can be represented exactly.

Across repositories, that consistency becomes a lightweight architectural interface: the domain changes, but the orientation workflow does not.

A project README has a different job from canonical Context. It is a **human first-contact projection**: summarize the project, explain why it exists, and route readers to the maintained detail. It should not become a second copy of every Rule, architecture invariant or volatile State. ContextCanon therefore works perfectly well when a project starts with no README at all; canonical Nodes can be established first and human-facing orientation can be written from that structure later. Automatic README projection is not currently a ContextCanon feature — keeping that boundary explicit is preferable to pretending generated prose is already authoritative.

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
│   ├── onboarding.md
│   ├── maintenance.md
│   └── cli.md
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
    │   ├── development-workflow/
    │   │   ├── README.md
    │   │   ├── CONTEXT.src.md
    │   │   └── docs/
    │   ├── github/
    │   │   ├── README.md
    │   │   └── CONTEXT.src.md
    │   └── github-local/
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

- a **reusable Node intended to ship with ContextCanon** goes in `nodes/library/<node-name>/`; it composes only the Parents its semantics actually require;
- a **ContextCanon-internal Node** goes in `nodes/internal/<node-name>/`;
- an **example or experiment** does not enter the library merely because it uses ContextCanon.

These category names are conventions of this repository. ContextCanon does not require other projects to use `library/` or `internal/`; it only requires each Node to have a clear node root.

## Immutable reusable imports

Reusable imports are not live includes from another Git repository. A consumer accepts an exact immutable package, marks the relationship Parent or Reference, and can build offline from its own accepted state.

The compiler separates candidate discovery from accepted inheritance:

```text
source fetch  → candidate only
source review → exact diff + consumer structural validation + receipt
source accept → immutable accepted package + exact updated pin
```

Normal `build` never fetches a missing import implicitly. Git repository location, ref, and `node-path` are update transport metadata; stable Node identity plus version and exact digests define accepted state.

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

## Git line endings: Windows, Linux and WSL

**Normalize editable project text before freezing Evidence. Preserve frozen ContextCanon bytes.** Evidence snapshots and published/accepted packages bind exact SHA-256 hashes and byte sizes: changing CRLF to LF, or LF to CRLF, invalidates those copies even when their text and line numbers look equivalent. Original project CSVs can use LF; they do not need a blanket binary declaration.

For LF project text, put this in the repository-root `.gitattributes`, with the preservation rules after general text rules:

```gitattributes
* text=auto eol=lf
**/.context/** -text
CONTEXT.md -text
**/CONTEXT/** -text
**/contextcanon-onboarding/** -text
```

These rules also cover nested Nodes. `-text` disables Git EOL conversion while retaining ordinary text diffs. Keep existing CRLF/mixed frozen copies unchanged; `git add --renormalize .` updates the index, not the current working-tree files. ContextCanon does not currently install these attributes automatically. See [line-ending migration](docs/line-endings.md) for existing projects, ongoing onboarding, Windows CRLF workflows and recovery limits ([#112](https://github.com/SomeSunlight/context-canon/issues/112)).

## Start here

If the five-second idea above is enough, the best next reads are:

- [Onboard an existing project](docs/onboarding.md) — first-user walkthrough for delivery triage, shelf design and placement.
- [Onboarding CLI](docs/onboarding-cli.md) — onboarding command map, including reset/restart from any STEP 01–12.
- [Maintain an existing ContextCanon project](docs/maintenance.md) — Parent/Reference updates, downstream Parent propagation review, build, and check.
- [CLI quick reference](docs/cli.md) — compact command map for normal operation.
- [Development Workflow](nodes/library/development-workflow/CONTEXT.src.md) — reusable Issue/branch/Pull Request/review/checks/merge lifecycle independent of a concrete forge.
- [GitHub](nodes/library/github/CONTEXT.md) — concrete provider for the Development Workflow on github.com.
- [GitHub Local](nodes/library/github-local/CONTEXT.md) — local GitHub-compatible provider Context for restricted/private development.
- [Concepts](nodes/internal/framework-development/docs/concepts.md) — Node roots, vocabulary and mental model.
- [Context composition](nodes/library/foundation/docs/composition.md) — Parents, References, local deltas, conflicts and updates.
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

ContextCanon is not an implementation of ICM. It focuses on composable Context Nodes, explicit Parent/Reference relationships, local deltas, deterministic compilation, versioned package acceptance, self-contained packages and harness-neutral project context.

## Project status

The current project-owner accepted `main` baseline is **ContextCanon 0.9.9**, from PR #54, squash-merged as `efa5946dac2ed4933ad250539f6a2836a39db7ca`.

That baseline is the first one validated through a complete real confidential **non-GitHub corporate-project onboarding**: reviewed inventory and immutable Evidence, structure-first shelf design, reusable Context selection including GitHub Local, isolated Semantic Handoffs for structure and placement, split human P/E review, deterministic preview and explicit publication. The final owner-test fixes simplified STEP-07 Assignments to plain raw text and made Markdown Topic Resource closure tolerate self-contained `data:` images from real-world Confluence/Chrome exports.

The important conclusion is not that onboarding has become “finished”. It is that the current separation has survived a substantially different real project: deterministic ContextCanon mechanics around bounded semantic LLM work, with human architecture/acceptance gates between them.

See [STATE.md](STATE.md) for the accepted current situation, [PLAN.md](PLAN.md) for the active development block, and [CHANGELOG.md](CHANGELOG.md) for the incremental owner-test history.
