# Architecture

ContextCanon separates a small human-facing authoring surface, a compact entry context, optional deeper package resources, immutable compiled Source state, and deterministic machine bookkeeping.

## Compilation pipeline

```text
CONTEXT.src.md
       +
accepted Source packages
       +
referenced source material
       |
       v
    compiler
       |
       +--> CONTEXT.md             compact official entry
       +--> CONTEXT/               deeper material, only when needed
       +--> .context/context.yaml  local machine view
       +--> .context/package.json  portable immutable package manifest
       +--> harness adapters       AGENTS.md, .goosehints, ...
       +--> compiled state ──────> deterministic Context/package diff
```

`CONTEXT.md` is always present. `CONTEXT/` is generated only when a Node has resources to materialize. `.context/` is compiler-owned state about the Node, its package, accepted external Sources, candidates, and review state.

The implementation mirrors that conceptual pipeline with narrow stages:

```text
CONTEXT.src.md
      ↓
parser.py → model.py → compiler.py → package.py
                        │              │
                        ├──────────────┼→ diff.py / package_diff.py
                        ↓              ↓
                    render.py       immutable package
                        ↓
                    outputs.py

external Source update:
Git locator → git_transport.py → candidate package
                              → sources.py review/accept
                              → accepted package + exact pin
```

Parsing owns authoring grammar, compilation owns semantic truth, package code owns immutable package identity and verification, diff code compares already-compiled truth, rendering projects compiled meaning, and output/acceptance layers own their explicit filesystem mutations. See [compiler.md](compiler.md) for the module contracts and regression strategy.

## A Node has one physical root

Every Context Node is organized around one **node-root directory**. That directory contains the Node's editable source, generated official entry, optional package resources, and machine state.

The node-root is a physical location, not identity. Moving or renaming the directory does not create a new Node as long as the stable Node ID remains the same.

A repository root may itself be a node root. Nested Nodes are also possible. Filesystem nesting alone does not create Source composition.

Category directories may organize several Nodes without becoming Nodes themselves. In this repository, `nodes/library/` and `nodes/internal/` are such categories.

The compiler discovers node roots from `CONTEXT.src.md`. External Git transport likewise treats `node-path` only as a location inside a retrieved repository snapshot; stable Node ID remains identity. Richer nested-repository boundary cases remain broader hardening work.

## Token economy is architectural

ContextCanon must not solve discoverability by eagerly loading everything.

The entry context contains only broadly required information and a precise Topic map. Topic material is loaded when relevant, with explicit Required versus Optional targets. A deeper document may repeat the same pattern: summary first, links onward.

Progressive disclosure is therefore part of the architecture, not merely a writing preference.

This also helps smaller and local models. A local agent may have abundant tokens but limited model capability; the architecture should spend those tokens on the relevant problem rather than on repeatedly reconstructing repository assumptions.

## Standardized orientation is architectural

Across projects, ContextCanon gives humans and agents the same conceptual entry points even when the domain changes:

- `CONTEXT.md` — what applies here and where to go deeper,
- `CONTEXT.src.md` — what this Node adds or changes,
- Sources — which reusable foundations are accepted,
- Topics — which deeper knowledge applies to which tasks,
- `STATE.md` — where the project is now,
- `PLAN.md` — where it is going.

The content remains project-specific. The orientation workflow becomes reusable.

## Harness integration is explicit and minimal

Harness adapters are compatibility edges, not competing sources of project context. A harness should have one deliberate entry path into the canonical `CONTEXT.md`; ContextCanon should not generate redundant instruction files for the same harness unless observed behavior requires them.

For the tested GitHub Copilot setup in JetBrains, ContextCanon deliberately uses generated `AGENTS.md` as that entry point. JetBrains must have **Tools → GitHub Copilot → Customizations → Use AGENTS.md file** enabled. ContextCanon does **not** generate a separate `.github/copilot-instructions.md` for this setup.

This is an explicit architecture decision rather than an inference from whichever files a harness happens to notice. Revisit it only if a real Copilot/harness behavior change demonstrates that `AGENTS.md` is no longer sufficient. See [harnesses.md](harnesses.md) for current adapter details.

## Gateway nodes: almost nothing can be enough

A valid Context Node may have zero Sources, zero Rules and zero materialized resources.

The root of this repository is **ContextCanon Gateway**. It contains one Topic: when the task concerns ContextCanon framework development, load the ContextCanon Framework Development Node. Because the Gateway has no deeper resources of its own, it has no `CONTEXT/` directory.

This is not a special node type. It is an ordinary Node at the smallest useful end of the model.

The same pattern can later route work in large repositories:

```text
Repository Gateway
   ├── backend task  ──> Backend Context
   ├── frontend task ──> Frontend Context
   └── release task  ──> Release Context
```

## Navigation is different from composition

A Topic target tells an agent **where to read next for this task**. A Source tells the compiler **which published context becomes part of this Node**.

ContextCanon itself demonstrates both:

```text
ContextCanon Gateway ──Topic──> ContextCanon Framework Development
                                      ▲
                                      │ Source
                           ContextCanon Foundation
```

The Gateway does not inherit Framework Development. Framework Development does inherit Foundation and adds a local delta.

## Transitive composition preserves identity and state

Source composition is transitive package meaning, not a direct-parent text copy.

If `Foundation → Team Standard → Project`, a Foundation Rule remains identified by the Foundation Node ID plus Rule ID in Project. A Team Standard Override changes the effective statement and adds provenance without changing that identity. A Team Standard Remove makes the Rule absent from active downstream context while preserving a machine-level removal record.

That removal record matters in a DAG: if another Source path still carries the same Rule, the compiler can detect the contradiction instead of inventing Source precedence. Likewise, two different effective Overrides of the same stable Rule are a structural conflict, while equivalent compiled Rule state may be deduplicated.

This identity- and state-preserving model enables exact diffs, dangling-operation checks, Source-update review, and standalone Source packages.

## Semantic identity is different from package presentation

ContextCanon distinguishes the normalized semantic meaning of a Node from the exact bytes of its published package.

`normalized_digest` is calculated from a canonical representation of semantic state. Collections with no defined semantic ordering are normalized so declaration order cannot accidentally become meaning or precedence.

`package_digest` covers the exact human/agent-facing `CONTEXT.md` plus materialized resources. Presentation-only reorderings may therefore change package bytes while leaving normalized semantics unchanged.

The deterministic diff preserves that distinction: it reports stable semantic entries when meaning changes and can separately report a package-presentation change when only generated bytes differ.

Accepted external Sources pin both digests. Semantic equality therefore does not erase the exact identity of the published human/agent package.

## Natural source files, generated package files

Project documentation should stay where it makes sense to authors. The compiler materializes context resources into a Node's `CONTEXT/` directory when building a self-contained published package.

```text
docs/architecture.md
        ↓ materialize
nodes/internal/framework-development/CONTEXT/references/docs/architecture.md
```

Consumers of that Node can use the package without reconstructing the author's source layout.

A directly referenced Markdown document can itself point to other local files. The compiler therefore computes a **materialization closure**: Topic Resource targets are seeds, and local relative links are followed recursively into the package. External links remain external.

The immutable `.context/package.json` manifest records the exact package file set, hashes, and sizes. Loading an accepted external package verifies that file set before its semantic state can enter composition.

## `.context/`

`.context/` is analogous to `.git/` in one important respect: it contains infrastructure that matters but should not dominate normal work.

For a compiled Node, `.context/context.yaml` is the local explanatory machine view and `.context/package.json` is the portable immutable package manifest. A consumer of external Sources may additionally hold content-addressed accepted packages, temporary candidates, and review receipts below `.context/`.

Accepted external packages are reproducible project state:

```text
.context/sources/<package-digest>/
```

Candidate packages are separate update state:

```text
.context/candidates/<package-digest>/
```

Generated machine files may remain occasionally inspectable by humans, but they are compiler-owned and are not an alternative authoring surface.

## ContextCanon's repository layout

This repository dogfoods three Nodes while keeping their roles visibly separated:

```text
repository root
└── ContextCanon Gateway

nodes/
├── library/                         organizational category, not a Node
│   └── foundation/                  ContextCanon Foundation
└── internal/                        organizational category, not a Node
    └── framework-development/       ContextCanon Framework Development
                                     -> composes Foundation + local delta
```

`library/` contains reusable Nodes distributed as part of ContextCanon. Every Node in that library must compose Foundation directly or transitively. `internal/` contains ContextCanon-specific Nodes that are not intended as reusable library modules.

These category names are repository conventions, not required directory names for other ContextCanon projects.

## The schema is the interface

ContextCanon does not need a separate "interface node" merely to describe structure.

The structural contract — what a Node, Source, Rule, Topic, Change, package, identifier, and deterministic diff must contain — belongs to the ContextCanon schema/specification. That schema is the interface implemented by every Node.

A Context Node contains actual context content. Another reusable base Node is justified only when there is reusable **content** with its own lifecycle.

## Deterministic skeleton, semantic assistance at the edges

Compiler 0.4 deterministically handles the current source grammar, node-root discovery, stable IDs, local Source resolution, immutable external Source packages, exact Source pins, package integrity verification, cycle/version errors, transitive Rule composition, Remove/Override operations, override/removal provenance, deterministic same-Rule DAG conflicts, dangling Change diagnostics, Topic targets, resource materialization, canonical semantic normalization, exact hashes, compiled Context/package diff, Git candidate retrieval, review receipts, explicit Source acceptance, generated views, adapters, drift checks, and atomic publication of Source-update state.

The next validation block deliberately adds a **semantic workflow above that deterministic core**: reviewed LLM-assisted onboarding of an existing repository. Deterministic tooling will inventory evidence and preserve provenance; an LLM may classify and reorganize meaning into a proposal; a human must explicitly accept the proposal before canonical ContextCanon source is created.

Other later deterministic capabilities include protected Rules and authorized exceptions, Topic composition/materialization across Source package boundaries, richer resource-collision policy, and broader repository-boundary diagnostics.

LLMs may assist with work that genuinely requires interpretation:

- bootstrapping context from an existing repository,
- detecting likely natural-language conflicts,
- explaining the impact of Source updates,
- suggesting where a conflict is best resolved,
- mapping exact Context changes to likely affected project files,
- applying accepted context changes to project code.

LLM judgments never replace deterministic package identity, exact diffs, structural validation, or explicit durable resolutions.

## Versioned accepted composition

A Source update does not immediately change consumers. Each consumer accepts an exact immutable Source package deliberately.

The implemented external update path is:

```text
accepted package
      ↓
source fetch      → verified candidate package only
      ↓
source review     → exact package diff + consumer structural validation + receipt
      ↓
source accept     → atomically published accepted package + exact updated pin
      ↓
normal offline build
```

Git `ref` and `node-path` describe candidate discovery and location; they are not accepted identity. Ordinary `build` never turns missing accepted state into implicit network access.

Candidate and accepted package directories are staged and verified before atomic publication. Review receipts and Source-pin changes are also published atomically. If the final pin replacement fails after the candidate package was installed, the old `CONTEXT.src.md` remains intact and the old accepted build state remains authoritative.

This separation makes a newer Source version a reviewable change request rather than live inheritance.
