# Architecture

ContextCanon separates a small human-facing authoring surface, a compact entry context, optional deeper package resources, immutable reusable-package state, explicit Parent/Reference semantics, and deterministic machine bookkeeping.

## Compilation pipeline

```text
CONTEXT.src.md
       +
accepted reusable packages
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

`CONTEXT.md` is always present. `CONTEXT/` is generated only when a Node has resources to materialize. Every non-empty generated `CONTEXT/` also contains a compiler-generated `README.md` that explains the package boundary and why `references/` contains materialized copies rather than a second authoring surface. `.context/` is compiler-owned state about the Node, its package, accepted reusable imports, candidates, and review state.

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

A repository root may itself be a node root. Nested Nodes are also possible. Filesystem nesting alone does not create Parent or Reference relationships.

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
- Parents / References — which reusable Context governs this Node and which Context is informational only,
- Topics — which deeper knowledge applies to which tasks,
- `STATE.md` — where the project is now,
- `PLAN.md` — where it is going.

The content remains project-specific. The orientation workflow becomes reusable.

Short repository `README.md` files can complement that semantic map at important physical directory boundaries. They should answer only local browsing questions — what this directory is, what is authored here, what is generated here, and where to go deeper — rather than duplicating the actual context or technical documentation.

## Harness integration is explicit and minimal

Harness adapters are compatibility edges, not competing sources of project context. A harness should have one deliberate entry path into the canonical `CONTEXT.md`; ContextCanon should not generate redundant instruction files for the same harness unless observed behavior requires them.

For the tested GitHub Copilot setup in JetBrains, ContextCanon deliberately uses generated `AGENTS.md` as that entry point. JetBrains must have **Tools → GitHub Copilot → Customizations → Use AGENTS.md file** enabled. ContextCanon does **not** generate a separate `.github/copilot-instructions.md` for this setup.

This is an explicit architecture decision rather than an inference from whichever files a harness happens to notice. Revisit it only if a real Copilot/harness behavior change demonstrates that `AGENTS.md` is no longer sufficient. See the reusable [Harness adapters](../../../library/foundation/docs/harnesses.md) guidance for current adapter details.

## Gateway nodes: almost nothing can be enough

A valid Context Node may have zero Parent/Reference imports, zero Rules and zero materialized resources. A Gateway can stay close to that minimum while still routing a few top-level tasks to the right depth.

The root of this repository is **ContextCanon Gateway**. It has no Parent/Reference imports and no Rules. Its `CONTEXT.md` currently recognizes two top-level tasks:

- framework-development work routes to the ContextCanon Framework Development Node;
- onboarding an existing project routes to the user-facing onboarding guide.

Only the onboarding guide is an authored materialized Resource. Because the Gateway has a resource, its generated `CONTEXT/` also contains the standard generated orientation `README.md`. The guide is not loaded for ordinary framework-development work merely because it exists in the package.

This is not a special node type. It is an ordinary small Node demonstrating progressive disclosure: the entry tells an agent **where to go**, while the deeper material is loaded only when its Topic matches.

The same pattern can route work in large repositories:

```text
Repository Gateway
   ├── backend task  ──> Backend Context
   ├── frontend task ──> Frontend Context
   └── release task  ──> Release Context
```

## Navigation is different from composition

A Topic target tells an agent **where to read next for this task**. A Parent tells the compiler **which published Context applies normatively**; a Reference attaches published Context as direct informational background without inheritance.

ContextCanon itself demonstrates both kinds of navigation plus composition:

```text
                         ┌─ Topic ──> ContextCanon Framework Development
ContextCanon Gateway ───┤
                         └─ Topic ──> onboarding guide

ContextCanon Foundation ─────────────┐
                                     ├─ Parent ──> ContextCanon Framework Development
ContextCanon Development Workflow ───┘
```

The Gateway does not inherit either Topic target as governance. Framework Development explicitly composes Foundation and the internal Development Workflow as Parents, then adds its local delta.

## Transitive composition preserves identity and state

Parent composition is transitive package meaning, not a direct-parent text copy. References are deliberately non-transitive.

If `Foundation → Team Standard → Project`, a Foundation Rule remains identified by the Foundation Node ID plus Rule ID in Project. A Team Standard Override changes the effective statement and adds provenance without changing that identity. A Team Standard Remove makes the Rule absent from active downstream context while preserving a machine-level removal record.

That removal record matters in a DAG: if another Parent path still carries the same Rule, the compiler can detect the contradiction instead of inventing Parent precedence. Likewise, two different effective Overrides of the same stable Rule are a structural conflict, while equivalent compiled Rule state may be deduplicated.

This identity- and state-preserving model enables exact diffs, dangling-operation checks, Parent-update review, and standalone reusable packages.

## Semantic identity is different from package presentation

ContextCanon distinguishes the normalized semantic meaning of a Node from the exact bytes of its published package.

`normalized_digest` is calculated from a canonical representation of semantic state. Collections with no defined semantic ordering are normalized so declaration order cannot accidentally become meaning or precedence.

`package_digest` covers the exact human/agent-facing `CONTEXT.md` plus materialized resources. Presentation-only reorderings may therefore change package bytes while leaving normalized semantics unchanged.

The deterministic diff preserves that distinction: it reports stable semantic entries when meaning changes and can separately report a package-presentation change when only generated bytes differ.

Accepted external reusable imports pin both digests and their direct Parent/Reference kind. Semantic equality therefore does not erase the exact identity of the published human/agent package.

## Resource identity is different from Resource location

Direct Topic Resources follow the same identity principle as Nodes, Rules, and Topics: identity is not a filesystem path.

A direct Resource is identified by its origin Node plus stable Resource ID. Its authored path records only the current location from which exact package bytes are materialized. This allows an explicitly reviewed rename to preserve semantic identity while still changing the exact package layout.

ContextCanon deliberately keeps the human decision in that transition. A byte-identical file at another path is only a **candidate** for the same Resource; duplicates make automatic identity transfer unsafe. `resource status` establishes deterministic evidence, and `resource reconcile` asks the human whether semantic continuity is intended.

Only direct Topic Resource seeds become first-class semantic Resources. Files reached through Markdown closure remain exact package dependencies without acquiring a separate identity-management lifecycle. Their resolution still constrains moves: relocating a Markdown seed must not silently change which relative files enter the package.

Resource identities are origin-Node scoped. The same physical repository file may therefore carry different Resource IDs when intentionally exposed by several Context Nodes. A physical move must update every affected ContextCanon reference together or fail without partial mutation.

## Natural source files, generated package files

Project documentation should stay with the Node that owns its meaning. In this repository, reusable authoring-format, Official Context, Topic, composition, and harness guidance is owned by ContextCanon Foundation under `nodes/library/foundation/docs/`. Framework-specific architecture, compiler, onboarding, test/CI, state, and use-case documentation is owned by Framework Development under its local `docs/` directory.

The compiler materializes exact Topic Resource closures under `CONTEXT/references/<origin-token>/`. New paths preserve authoring-Node-relative directories where possible; cross-Node links widen the common base to retain exact relative links. A normal local `docs/architecture.md` therefore becomes `CONTEXT/references/<origin-token>/docs/architecture.md` rather than repeating the Node's entire repository location.

Full Node identities and original repository paths are recorded in `.context/resource-origins.json`, authenticated exact package content. Compact namespace collisions are detected; directory tokens do not become semantic identity. Direct references to Foundation-owned documents retain their original authorship in this mapping. Resource move/status reads the mapping rather than attempting to infer origin from a short directory name.

A self-contained package may later be copied or accepted without the original source repository. In that situation the authored path above may not exist at all, while the materialized package copy still contains the exact reviewed resource bytes. The generated `CONTEXT/README.md` explains this boundary at the place where a human browsing the package is most likely to notice the apparent duplication.

A directly referenced Markdown document can itself point to other local files. The compiler therefore computes a **materialization closure**: Topic Resource targets are seeds, and local relative links are followed recursively into the package. External links remain external.

The immutable `.context/package.json` manifest records the exact package file set, hashes, and sizes. Loading an accepted external package verifies that file set before its semantic state can enter composition.

## `.context/`

`.context/` is analogous to `.git/` in one important respect: it contains infrastructure that matters but should not dominate normal work.

For a compiled Node, `.context/context.yaml` remains the regenerable explanatory machine view. `.context/package.json` is the immutable package manifest; package v4 also authenticates `.context/resource-origins.json` whenever Resource files exist.

Each consuming Git working tree has one `.context/versions/<token>/` library of whole immutable Node versions. The provider's checkout has its own library. A library entry binds full Node ID, normalized semantic digest and exact package digest; identical human bytes can legitimately belong to different Nodes. Prefixes normally use 16 hex characters, extend for verified collisions and are always checked against complete package identity. No editable allocation index is needed.

Normal publication retains the previous verified package and new package before replacing local generated output. Imported versions are installed once and shared across nested consumers; exact per-consumer Parent/Reference pins still determine which version governs or informs that Node. Whole immutable effective packages remain self-contained; Resource copies needed for that property are not flattened or turned into live upstream reads.

`version_store.py` is the shared resolver/install boundary; `version_history.py` retains publication history and produces a regenerable browsing index. Normal candidates and reviews live at the Git root in consumer-owned scopes, so cleanup cannot consume another Child's pending review. `storage_migration.py` is a separate removable transition: preview first, verify every copy before narrow legacy-wrapper removal, preserve pins, and resume interrupted cleanup/link-review rebinding. Old packages and consumer-local stores remain readable without implicit rewriting.

Onboarding storage/publication/reset migration is Phase 2. Phase 1 preserves that process's legacy transaction boundary with package-format compatibility. Automatic history pruning is deferred until onboarding/recovery reachability is included. Generated machine files are inspectable infrastructure, not an alternative authoring surface.

## ContextCanon's repository layout

This repository currently uses ContextCanon on itself through four Nodes while keeping navigation, reusable governance, and internal development method visibly separated:

```text
repository root
└── ContextCanon Gateway

nodes/
├── library/                         organizational category, not a Node
│   └── foundation/                  ContextCanon Foundation
└── internal/                        organizational category, not a Node
    ├── development-workflow/        ContextCanon Development Workflow
    │                                internal self-hosted development method
    └── framework-development/       ContextCanon Framework Development
                                     -> composes Foundation
                                     -> composes Development Workflow
                                     -> adds framework-local delta
```

`library/` contains reusable Nodes distributed as part of ContextCanon. Every Node in that library must compose Foundation directly or transitively. `internal/` contains ContextCanon-specific Nodes that are not intended as reusable library modules.

Development Workflow is deliberately internal while the PLAN/checkpoint/verification method is being proven on ContextCanon itself. If unrelated projects later validate the same method, it can be reviewed for promotion to the reusable library rather than being declared generic in advance.

These category names are repository conventions, not required directory names for other ContextCanon projects.

## The schema is the interface

ContextCanon does not need a separate "interface node" merely to describe structure.

The structural contract — what a Node, Source, Rule, Topic, Change, package, identifier, and deterministic diff must contain — belongs to the ContextCanon schema/specification. That schema is the interface implemented by every Node.

A Context Node contains actual context content. Another reusable base Node is justified only when there is reusable **content** with its own lifecycle.

## Deterministic skeleton, semantic assistance at the edges

Compiler 0.7 deterministically handles the current source grammar, node-root discovery, stable IDs, local and immutable reusable packages, explicit Parent/Reference relationships with legacy Source→Parent compatibility, exact pins, package integrity verification, cycle/version errors, Parent-only transitive Rule/Topic composition, non-transitive informational References, Remove/Override operations, provenance, deterministic same-Rule DAG conflicts, dangling Change diagnostics, resource materialization, canonical semantic normalization, exact package and normative-export hashes, Context/package diff, Git candidate retrieval, review receipts, explicit package acceptance, generated views, adapters, drift checks, and atomic update state.

Reviewed onboarding adds bounded semantic tasks above that deterministic core. Deterministic tooling freezes repository evidence, selects the task-specific input set and renders the framework-owned assignment; a reasoning LLM may interpret or reorganize meaning only inside that box; deterministic validation binds the result back to exact inputs; the human then reviews and explicitly decides what may become durable truth.

The same Progressive Disclosure principle therefore applies before an LLM reasons, not only when an agent later consumes compiled Context. A Semantic Handoff Task receives a disposable filesystem world containing only its deterministic instruction, explicitly bound frozen Evidence and accepted-state inputs required for that task. Current structure and placement tasks use the complete frozen Evidence set; the handoff builder can bind a narrower subset for future tasks without changing the contract. Prior raw model proposals, reviews, IDE metadata and chat history are not implicit inputs. Physical duplication of immutable Evidence between isolated handoffs is acceptable; semantic isolation is more important than provider-specific cache behavior.

This is a deterministic **semantic-task harness**, not a general agent orchestrator. ContextCanon defines task identity, context selection, result contract and the next deterministic validator, while the human chooses and starts any policy-approved model. A model never advances the workflow merely because it returned successfully. The same boundary can later support explicit interpretation of chats/meeting notes, assisted inventory triage or other semantic transformations while preserving the distinction between raw Evidence, reviewed interpretation and canonical Context.

First-adoption acceptance is implemented as a separate deterministic publication boundary: ContextCanon rechecks the reviewed evidence against the live repository, verifies exact reusable Source identities, stages and compiles the proposed Node, checks output ownership, publishes only after those checks succeed, runs normal build/check, and records the accepted state.

Other later deterministic capabilities include protected Rules and authorized exceptions, richer resource-collision policy beyond the current stable-origin exact-byte rule, and broader repository-boundary diagnostics. Effective Parent Topics and their Resource closures compose across package boundaries without parsing generated Markdown; direct Reference Topics/Resources remain local to the referencing Node.

LLMs may assist with work that genuinely requires interpretation:

- bootstrapping context from an existing repository,
- detecting likely natural-language conflicts,
- explaining the impact of Source updates,
- suggesting where a conflict is best resolved,
- mapping exact Context changes to likely affected project files,
- applying accepted context changes to project code.

LLM judgments never replace deterministic package identity, exact diffs, structural validation, or explicit durable resolutions.

## First-adoption trust invariants

The onboarding implementation deliberately treats several properties as architectural trust boundaries rather than incidental implementation details.

### New Node identity is not evidence identity

A first onboarding review creates or receives a stable Node ID as **human-owned review state**. When ContextCanon generates that ID, it uses a fresh UUID once and stores it in `review.json`; it never derives an independent Node identity from the evidence digest.

Evidence identity answers "which exact bytes were reviewed?" Node identity answers "which continuing Context Node is this?" Two unrelated projects can contain identical evidence bytes and must therefore still receive independent Node identities.

### A reviewed reusable Source means one exact package

When the semantic reviewer proposes an `existing-source`, the proposal is bound to the Source Node ID, name, version, normalized digest, and package digest that the reviewer actually inspected.

Final acceptance requires that exact immutable package again. A newer package with the same stable Source Node ID is a different review object, not a silent substitute. Historical proposal shapes that lack exact package identity may remain readable, but they cannot cross the publication boundary as an accepted Source.

### First adoption must not seize project-owned paths

The staged compile determines which output paths the proposed first Node would own. Before canonical publication, ContextCanon refuses if those paths already exist in the project; a pre-existing `CONTEXT/` tree and an existing `CONTEXT.src.md` are explicit first-adoption stops.

This check is based on the outputs of the actual staged Node rather than a broad filename blacklist. The purpose is ownership safety: adopting ContextCanon must not silently repurpose an existing project file merely because its name collides with a generated ContextCanon output.

### First-adoption publication is rollback-safe

After preflight succeeds, first adoption may install immutable Source packages, write canonical source, generate outputs, and publish the final acceptance record. Those writes form one transaction-like publication step.

If that publication fails before the acceptance record is complete, ContextCanon removes the newly created canonical/generated state, partial onboarding acceptance artifacts, and Source packages installed only by that failed attempt. Pre-existing accepted Source state is preserved.

The invariant is that an operator should recover by fixing the cause and retrying, not by reverse-engineering whether the repository is half-adopted.

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

## Repository-root onboarding storage

The selected project scope remains the semantic/authoring unit. Its frozen Evidence and mutable reviews use authenticated short root-scoped runs; exact reusable/enclosing-Parent packages use the ordinary complete-Node version library. STEP-04/08 handoffs have short project/Evidence/step locators and preserve their portable input contract. A visible workspace holds human gates and the exact operator PLAN.

`onboarding_storage.py` owns normal routing and full ownership validation. Explicit removable `onboarding_migration.py` owns old-run preview/apply receipts, copy verification and retirement. Runtime activation is independent of migration receipts. Directory tokens never replace full Node, Evidence or package identity, and shared immutable history is outside one run's rollback ownership. See [onboarding-design.md](onboarding-design.md).
