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

## What ContextCanon is trying to fix

Context windows are valuable working memory. They should be spent on the current problem, not on every architecture note, coding convention, troubleshooting guide, glossary, example, and harness-specific instruction a project has ever accumulated.

ContextCanon therefore starts with four ideas:

1. **Load less.** Keep the always-read entry small and use Topics to point to deeper Required or Optional context.
2. **Repeat less.** Compose reusable Context Nodes and describe only the local delta at each node.
3. **Calculate what can be calculated.** Parsing, IDs, dependency resolution, changes, provenance, diffs and package construction belong to a deterministic compiler; LLMs handle genuinely semantic work.
4. **Keep project knowledge portable.** Canonical context must not depend on Codex, Claude, goose, Copilot, or a particular model. Harness files stay thin adapters at the edge.

The larger goal is **context integration**: documentation, rules, terminology, examples, structured data, PDFs, diagrams, skills and hard-won operational experience should all be discoverable through the same model without all being loaded at once.

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

`CONTEXT/` exists only when deeper resources are actually needed. `.context/` is separate machine territory for identities, accepted sources, provenance, mappings, hashes and package metadata.

The editable `CONTEXT.src.md` answers a deliberately narrower question:

> What does this node add or change compared with its Sources?

The generated `CONTEXT.md` answers:

> What applies here, and where should I go next if this task needs more?

## A small surprise: you have already entered ContextCanon

This repository does not explain ContextCanon from outside and then switch it on later.

**The repository root is already one of the smallest useful ContextCanon nodes.**

Open [`CONTEXT.md`](CONTEXT.md): it contains no inherited Sources, no Rules and no deep package directory. Its only job is to recognize ContextCanon development work and direct that work to the deeper Development node.

```text
ContextCanon Gateway  ── Topic: development ──>  ContextCanon Development
                                                       ▲
                                                       │ Source
                                              ContextCanon Foundation
```

That gives this repository three real nodes with three different jobs:

- **[ContextCanon Gateway](CONTEXT.md)** — the almost-empty repository entry. It demonstrates progressive disclosure at the smallest useful scale.
- **[ContextCanon Foundation](nodes/foundation/CONTEXT.md)** — the reusable baseline: rules and Topics that other ContextCanon-managed nodes may compose.
- **[ContextCanon Development](nodes/development/CONTEXT.md)** — Foundation plus only the additional context needed to design and implement ContextCanon itself.

The first arrow above is **navigation**: Gateway does not inherit Development; a Topic sends a relevant task there. The second arrow is **composition**: Development accepts Foundation as a Source and adds a local delta.

Nothing special was invented for bootstrapping this repository. Gateway is an ordinary Context Node. That is intentional: if ContextCanon cannot represent "almost no context" cleanly, it has failed one of its own most important design goals.

## ContextCanon is also for humans

The same structure that saves model tokens makes a project easier to inspect:

- Sources show which reusable context is accepted.
- `CONTEXT.src.md` shows what is special here.
- `CONTEXT.md` shows the compiled result without forcing the reader through inheritance archaeology.
- visible stable IDs make inherited changes explicit and traceable.
- Topics keep the main view short while preserving a clear route to depth.

The framework deliberately uses constrained Markdown for human authoring and a boring machine representation underneath. Humans should not have to read YAML to understand the project; machines should not have to infer structure that can be represented exactly.

## Repository layout

```text
context-canon/
├── README.md
├── CONTRIBUTING.md
├── CHANGELOG.md
├── STATE.md
├── PLAN.md
│
├── CONTEXT.src.md       # tiny Gateway source
├── CONTEXT.md           # tiny generated Gateway entry
├── AGENTS.md            # generated root harness adapter
├── .goosehints          # generated root goose adapter
├── .context/            # Gateway machine state
│
├── nodes/
│   ├── README.md
│   ├── foundation/      # reusable ContextCanon Foundation node
│   │   ├── CONTEXT.src.md
│   │   ├── CONTEXT.md
│   │   ├── CONTEXT/
│   │   └── .context/
│   └── development/     # Foundation + ContextCanon development delta
│       ├── CONTEXT.src.md
│       ├── CONTEXT.md
│       ├── CONTEXT/
│       └── .context/
│
└── docs/                # human-edited specification and design documentation
```

Later the repository may publish more reusable Nodes under `nodes/`. They should be added because a real reusable context has emerged, not to fill a taxonomy in advance.

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

- [Concepts](docs/concepts.md) — the vocabulary and mental model.
- [Context composition](docs/composition.md) — Sources, local deltas, conflicts and updates.
- [Official context](docs/official-context.md) — `CONTEXT.md`, optional `CONTEXT/`, and package boundaries.
- [Topics and context integration](docs/topics.md) — how deeper context is selected.
- [Architecture](docs/architecture.md) — deterministic compiler boundary and node/package structure.
- [Use-case walkthrough](docs/use-case-walkthrough.md) — where the design has already been stress-tested.

See [STATE.md](STATE.md) for the current project situation and [PLAN.md](PLAN.md) for the next experiments.

## Influence

ContextCanon grew from experimenting with the filesystem-oriented progressive-disclosure ideas in Jake Van Clief and David McDermott's *Interpretable Context Methodology: Folder Structure as Agentic Architecture* and asking what would be needed for reusable, versioned context across independent projects, models and harnesses.

- Paper: https://arxiv.org/abs/2603.16021
- ICM repository: https://github.com/RinDig/Interpretable-Context-Methodology

ContextCanon is not an implementation of ICM. It focuses on composable Context Nodes, explicit local deltas, deterministic compilation, versioned source acceptance, self-contained packages and harness-neutral project context.

## Project status

ContextCanon is still a specification and prototype project. The architecture is being shaped deliberately through working repository POCs before the compiler is hardened.

That is also why the repository already uses the model it is defining: concrete use exposes ambiguity much faster than designing the whole system in the abstract.