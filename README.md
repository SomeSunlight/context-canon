# ContextCanon

**Give humans and AI agents less context — and the right context at the right time.**

Context windows are valuable working memory. A project should not spend them by eagerly loading every architecture note, coding convention, troubleshooting guide, glossary, example, and harness-specific instruction before the actual task even starts.

ContextCanon takes the opposite approach: keep the entry context small, make deeper knowledge precisely discoverable, and load it only when the current task needs it.

Think of it like a well-designed website:

- the landing page gives immediate orientation,
- important rules are always visible,
- a Topic says when deeper information is **required**,
- optional links remain available when more detail is useful,
- deeper pages can repeat the same pattern: summary first, links onward.

This saves tokens at every iteration while still giving an agent a clear path to the information it actually needs.

## Why ContextCanon?

### 1. Progressive disclosure instead of context flooding

The official entry context stays compact. Topic-specific architecture, logging, security, release, database, domain, glossary, examples, and experience are loaded only when relevant.

The complete official context still exists as a versioned package; it simply does not need to occupy the prompt all at once.

### 2. Context integration, not just another rules file

The same mechanism can eventually integrate many kinds of project knowledge into the working context when they become relevant:

- documentation and architecture,
- terminology and glossaries,
- patterns and example code,
- CSV files, schemas, tables, and other structured data,
- PDFs, images, and diagrams,
- skills and workflows,
- operational experience and known pitfalls.

The aim is not to make one enormous knowledge bundle. The aim is to make all of this information systematically discoverable while loading only the useful part.

### 3. Transparent composition

A node composes reusable context sources and records only its local delta: what it adds, removes, overrides, or changes.

That makes two views easy to understand:

- `CONTEXT.src.md` — what is special about this node,
- `CONTEXT.md` — the generated compact entry view of what applies here.

Stable visible IDs in published contexts make inherited changes explicit and traceable without turning titles or wording into identifiers.

### 4. Model- and harness-independent project knowledge

Canonical context must not create hidden dependencies on Codex, Claude, goose, Copilot, or any particular LLM. Harness-specific files are thin adapters at the edge.

Project code and project truth stay independent of the tool currently reading them.

### 5. Deterministic skeleton, semantic intelligence on top

Operations that can be specified exactly should not be delegated to an LLM.

Parsing, IDs, dependency resolution, version checks, explicit removes/overrides/exceptions, provenance, materialization, exact diffs, and package identity belong to a deterministic compiler.

LLMs are valuable where meaning must be interpreted: detecting likely natural-language conflicts, explaining impact, suggesting resolutions, bootstrapping context, or applying accepted context changes to code.

**As much determinism as possible forms the skeleton; LLM reasoning adds the muscles.**

### 6. Reusable context gets better over time

A Python, Java, company-security, personal-style, or domain context can be improved once and reused by many child nodes. Recurring contradictions and duplicated guidance can then be resolved closer to their source instead of being rediscovered independently in every project.

## Core model

```text
Context Source A ─────┐
Context Source B ─────┤
Context Source C ─────┼──> compile ──> Official Context Package
                      │                         │
Local Delta ──────────┘                         ├── CONTEXT.md
                                                └── CONTEXT/
```

The **Official Context Package** is the canonical result for a node. It applies to the node itself and is the package published to child nodes.

Its physical human/agent-facing form is deliberately simple:

```text
CONTEXT.md              compact entry; read first
CONTEXT/                deeper compiled/materialized context
├── references/
├── topics/             future generated topic material
├── glossaries/         future
├── examples/           future
├── skills/             future
└── ...
```

`.context/` remains separate machine territory: compiler state, accepted source snapshots, provenance, resource maps, hashes, and package metadata.

Source documents may stay where authors naturally maintain them. During compilation, resources needed by the published package are materialized under `CONTEXT/`, and generated links point to those package-local copies.

## ContextCanon uses ContextCanon

This repository intentionally contains two nodes:

- [`contexts/public/`](contexts/public/) — **ContextCanon Public (`t`)**, the public baseline intended for ordinary client nodes.
- the repository root — **ContextCanon Development (`t-intern`)**, which composes `t` and adds only the rules and Topics needed to design and implement ContextCanon itself.

```text
ContextCanon Public (t)
          │
          ▼
ContextCanon Development (t-intern)
```

This is deliberate dogfooding: a Git repository and a ContextCanon node are not the same concept. One repository may publish several independently addressable nodes.

The structural contract of a Context Node is defined by the ContextCanon schema/specification. That schema plays the role of an interface; it is not itself another Context Node unless reusable context content eventually justifies one.

## Repository surface

```text
repository/
├── README.md
├── CONTRIBUTING.md
├── CHANGELOG.md
├── STATE.md
├── PLAN.md
│
├── CONTEXT.src.md       # edit: local t-intern delta
├── CONTEXT.md           # read first: generated t-intern entry
├── CONTEXT/             # generated t-intern package resources
├── AGENTS.md            # generated harness adapter
├── .goosehints          # generated goose adapter
│
├── contexts/
│   └── public/          # reusable public t node
│       ├── CONTEXT.src.md
│       ├── CONTEXT.md
│       ├── CONTEXT/
│       └── .context/
│
└── .context/            # generated machine state for t-intern
    └── context.yaml
```

## Start here

- [Concepts](docs/concepts.md)
- [Context composition](docs/composition.md)
- [Source format](docs/source-format.md)
- [Official context](docs/official-context.md)
- [Topics and context integration](docs/topics.md)
- [State and planning](docs/state.md)
- [Harness adapters](docs/harnesses.md)
- [Architecture](docs/architecture.md)
- [Use-case walkthrough](docs/use-case-walkthrough.md)

## Influence

ContextCanon grew from experimenting with the filesystem-oriented progressive-disclosure ideas in Jake Van Clief and David McDermott's *Interpretable Context Methodology: Folder Structure as Agentic Architecture* and asking what would be needed for reusable, versioned project context across independent repositories, models, and harnesses.

- Paper: https://arxiv.org/abs/2603.16021
- ICM repository: https://github.com/RinDig/Interpretable-Context-Methodology

ContextCanon is not an implementation of ICM. It focuses on composable context nodes, explicit local deltas, deterministic compilation, versioned source acceptance, self-contained packages, and harness-neutral project context.

## Project status

ContextCanon is currently a specification and prototype project. Two repository-based POCs and systematic use-case walkthroughs have shaped the current design; no production compiler exists yet.

See [STATE.md](STATE.md) for the current situation and [PLAN.md](PLAN.md) for the next validation steps.
