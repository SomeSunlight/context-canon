# Contributing

ContextCanon has two quite different kinds of contributions:

1. **develop the ContextCanon framework itself** — compiler, formats, CLI, onboarding workflow, documentation, internal Nodes and deterministic semantics;
2. **contribute reusable ContextCanon Nodes** — shared context under `nodes/library/` that other projects may later consume as Sources.

Both matter, but they require different context. A contributor should not have to understand the entire compiler roadmap merely to improve a reusable documentation or security Node.

## Choose your contribution path

### A. Framework development

Use this path when changing ContextCanon itself: compiler behavior, authoring grammar, package identity, Source transport, onboarding mechanics, CLI commands, framework documentation, tests, or internal Nodes.

Before changing anything:

1. Read the repository [CONTEXT.md](CONTEXT.md).
2. Follow its Framework Development Topic to [nodes/internal/framework-development/CONTEXT.md](nodes/internal/framework-development/CONTEXT.md).
3. Read [STATE.md](STATE.md) for the current project position.
4. Read [PLAN.md](PLAN.md) for the active implementation block.
5. Load only the Topic material required for the task.

Framework Development composes the internal [ContextCanon Development Workflow](nodes/internal/development-workflow/CONTEXT.src.md). Its Rules make long LLM-assisted work recoverable: put coherent work in PLAN before editing, checkpoint completed items immediately, keep recovery-critical decisions in the repository, batch related edits before dogfood regeneration, and still require exact-head green verification before review completion.

Framework changes should preserve the central rule: **everything that can be exact stays deterministic; LLMs are used only for explicit semantic interpretation steps.**

### B. Reusable Node contribution

Use this path when adding or improving context intended to be reused across projects under:

```text
nodes/library/<node-name>/
```

Start with:

1. the target Node's `CONTEXT.md` / `CONTEXT.src.md`, if it already exists;
2. [ContextCanon Foundation](nodes/library/foundation/CONTEXT.md), because reusable library Nodes compose Foundation directly or transitively;
3. [Source format](nodes/internal/framework-development/docs/source-format.md) for authoring syntax;
4. [Official context](nodes/internal/framework-development/docs/official-context.md) and [Context composition](nodes/internal/framework-development/docs/composition.md) when inheritance or packaging matters.

You normally do **not** need to read `STATE.md` or the whole framework `PLAN.md` merely to contribute Node content. Read them only when your Node contribution also requires a framework capability or changes the project roadmap.

A reusable Node contribution should answer questions such as:

- Is this guidance genuinely useful across more than one project?
- Does an existing library Node already cover it?
- Is it durable governance, a Topic-specific resource, or ordinary documentation?
- Can the Node remain small and composable rather than becoming another giant instruction bundle?
- Are stable IDs and Source relationships preserved?

Do not put an experiment into `nodes/library/` merely because it uses ContextCanon. Reusable library content should be reviewed as a product in its own right.

## Where context is edited

Four Nodes are currently dogfooded in this repository:

- Gateway: edit [CONTEXT.src.md](CONTEXT.src.md)
- Foundation: edit [nodes/library/foundation/CONTEXT.src.md](nodes/library/foundation/CONTEXT.src.md)
- Development Workflow: edit [nodes/internal/development-workflow/CONTEXT.src.md](nodes/internal/development-workflow/CONTEXT.src.md)
- Framework Development: edit [nodes/internal/framework-development/CONTEXT.src.md](nodes/internal/framework-development/CONTEXT.src.md)

Do not directly edit generated `CONTEXT.md`, `CONTEXT/`, harness adapters, `.context/context.yaml`, or `.context/package.json` files.

Technical framework documents are authored under [`nodes/internal/framework-development/docs/`](nodes/internal/framework-development/docs/). Files with similar names under a Node's generated `CONTEXT/references/` tree are compiler-materialized package copies, not another authoring surface.

After changing ContextCanon source or referenced material:

```text
python -m pip install -e .
python -m unittest discover -s tests -v
contextcanon check --all .
```

`check` performs compilation in memory and reports generated drift. Near a review boundary, use the reported drift to run `contextcanon build --all .` once for the coherent correction block, commit exactly that generated output, then require the exact final head to pass tests plus `contextcanon check --all .` at zero drift.

`build` may replace compiler-owned generated package files. It must not treat arbitrary repository files as disposable output.

## Framework implementation map

For framework contributors, the implementation is intentionally split into narrow layers:

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

pre-Context onboarding:
Git repository → onboarding.py → immutable evidence snapshot
                                      ↓
                        onboarding_instruction.py
                    deterministic semantic assignment
                                      ↓
                      external reasoning LLM
                                      ↓
                         proposal.json
                                      ↓
                       onboarding_proposal.py
                    strict deterministic validation
                                      ↓
                       onboarding_review.py
                human review binding + evidence view
                                      ↓
                    explicit onboard accept
                                      ↓
                      staged compile → authored context
                                      ↓
                           normal compiler
```

Module contracts:

- **`model.py`** — typed compiler data only.
- **`parser.py`** — constrained authoring grammar and syntax validation.
- **`compiler.py`** — semantic compiler truth: Source composition, Rule changes, conflicts, targets and resource closure.
- **`package.py`** — immutable package state, canonical semantic digest, exact package identity and verification.
- **`diff.py` / `package_diff.py`** — deterministic comparison by stable identity.
- **`render.py`** — deterministic human/machine projection.
- **`outputs.py`** — compare/write compiler-owned generated output.
- **`git_transport.py`** — retrieve candidate bytes only.
- **`sources.py`** — deterministic candidate review receipts, immutable Source installation, and explicit Source acceptance.
- **`onboarding.py`** — deterministic pre-Context inventory and frozen evidence snapshots; no semantic classification.
- **`onboarding_instruction.py`** — deterministic rendering of the semantic assignment; no LLM invocation.
- **`onboarding_proposal.py`** — strict proposal/provenance validation; validation is not semantic acceptance.
- **`onboarding_review.py`** — exact proposal/review binding, human-readable evidence review, explicit acceptance checks, staged first-Node publication, and acceptance records.
- **`cli.py`** — orchestration only.

See [Compiler](nodes/internal/framework-development/docs/compiler.md), [Immutable external Sources](nodes/internal/framework-development/docs/external-sources.md), [Tests and GitHub Actions CI](nodes/internal/framework-development/docs/tests-and-ci.md), and [Onboarding](docs/onboarding.md) for details.

## Design principles

### Deterministic truth first

If behavior can be specified exactly, implement it deterministically. LLMs are appropriate for semantic interpretation, not Node identity, Source/package resolution, Rule operations, exact diffs, package integrity, acceptance state, provenance, hashes, onboarding evidence identity, instruction identity, proposal structural validity, or review/publication binding.

### Keep the pipeline one-way

Authoring is parsed into structures; compilation resolves meaning; immutable packages publish compiled meaning; diffs compare it; rendering projects it. Never reconstruct semantic truth from generated Markdown.

Onboarding follows the same principle earlier in the lifecycle: ContextCanon freezes evidence and defines the assignment, an external LLM proposes meaning, ContextCanon validates the proposal mechanically, a human reviews the exact findings/evidence, and explicit acceptance is required before durable context is authored.

### Stable identity beats wording and path

Rules and Nodes are referenced by stable identity. Renaming a Node, moving its directory, changing a Git `node-path`, or rewording a Rule must not silently retarget operations.

### Fail rather than guess

Unsupported syntax, incomplete pins, dangling Changes, duplicate identities, cycles, package corruption, invalid paths, unsafe onboarding evidence, oversized instructions, malformed proposal provenance, stale reviews/evidence, incomplete human decisions, or structural ambiguity should fail clearly.

Semantic uncertainty is different: an onboarding LLM should preserve it as an unresolved question rather than invent certainty.

### No implicit Source precedence

Multiple Sources are independent. Source order must not decide conflicts. Canonical semantic normalization likewise ignores ordering where the model assigns no semantic meaning.

### Keep accepted state reproducible

Accepted external packages under `.context/sources/<package-digest>/` are reproducible consumer state. Candidate packages and onboarding evidence are review/input state, not accepted governance. Onboarding acceptance records bind the human decision to exact evidence/proposal/review identities and the resulting canonical package identities.

### Keep filesystem mutation narrow

Compilation and diff should work in memory. Generated output, candidate retrieval, Source acceptance, onboarding preparation, and explicit onboarding acceptance own only explicit filesystem areas. Onboarding instruction rendering, proposal validation, and review inspection do not publish canonical context.

Initial `onboard accept` also refuses to replace an existing `CONTEXT.src.md`; reviewed re-onboarding/update semantics are a separate future workflow.

### Preserve human readability

The canonical authoring format remains constrained Markdown. Machine state can be boring; humans should be able to understand source and official context without a framework-specific editor.

The same applies to project documentation: `STATE.md`, `PLAN.md`, README and contribution guides should lead with the human story and reveal technical detail only when useful. Important directory boundaries should have short README files when that makes direct browsing self-explanatory.

## Tests and completion

Every deterministic feature should normally include successful and important failure cases, deterministic digest/order assertions where relevant, and drift checks when generated output changes.

Tests must not require an external LLM or network service. Git transport tests use local temporary repositories; onboarding tests use frozen local fixtures and locally built immutable Source packages.

GitHub Actions runs the unit/repository tests and `contextcanon check --all .`. The detailed flow and failure-reading guide lives in [Tests and GitHub Actions CI](nodes/internal/framework-development/docs/tests-and-ci.md).

A change is not complete merely because unit tests pass: committed dogfood packages must match current compiler output.

## Branch and merge cadence

`main` is the last project-owner-reviewed, fully reproducible ContextCanon stage. Work on one coherent block per branch/PR, finish tests/docs/dogfood/CI, then squash-merge before starting an unrelated block.

A block is ready only when:

- deterministic positive and negative tests pass;
- dogfood was regenerated by the compiler itself;
- `contextcanon check --all .` is clean;
- documentation matches implemented behavior;
- `STATE.md` says plainly where the project now stands;
- `PLAN.md` says plainly what has been accepted and what comes next.

The active LLM-assisted development cadence is additionally governed by the internal Development Workflow Node. In particular, coherent PLAN items are recorded before editing and completed checkboxes are updated as soon as the corresponding step is genuinely complete.

## Pull requests

Keep changes conceptually focused. Explain what changed, why it belongs in deterministic truth or an explicit semantic layer above it, and which practical need or invariant it serves.

GitHub Actions cancels superseded runs for the same PR/ref, so intermediate correction heads do not consume CI after a newer head exists. The exact head presented for review must still complete the full deterministic suite with zero drift.

Keep the PR open until the project owner explicitly approves the reviewed result.

If a new feature makes compiler semantics depend on hidden transport behavior, generated presentation, an unbound repository snapshot, unvalidated semantic output, or an LLM judgment, redesign the separation before merging.
