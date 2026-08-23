# Contributing

ContextCanon has an executable deterministic compiler. Changes should keep the human model simple while preserving a compiler core that is exact, inspectable, and independently testable from any LLM.

## Before changing anything

1. Read the repository [CONTEXT.md](CONTEXT.md). It is intentionally a tiny Gateway.
2. For ContextCanon development work, follow its Required target to [nodes/internal/framework-development/CONTEXT.md](nodes/internal/framework-development/CONTEXT.md).
3. Read [STATE.md](STATE.md) for the current project situation.
4. Check [PLAN.md](PLAN.md) for the active compiler/workflow slice.
5. Load only the Topic material required for the task.

## Editing context

Three Context Nodes are currently dogfooded in this repository:

- Gateway: edit [CONTEXT.src.md](CONTEXT.src.md),
- Foundation: edit [nodes/library/foundation/CONTEXT.src.md](nodes/library/foundation/CONTEXT.src.md),
- Framework Development: edit [nodes/internal/framework-development/CONTEXT.src.md](nodes/internal/framework-development/CONTEXT.src.md).

Do not directly edit generated `CONTEXT.md`, `CONTEXT/`, harness adapters, `.context/context.yaml`, or `.context/package.json` files.

After changing ContextCanon source or referenced material:

```text
python -m pip install -e .
contextcanon build --all .
contextcanon check --all .
python -m unittest discover -s tests -v
```

`build` may replace compiler-owned generated package files. It must not treat arbitrary repository files as disposable output. `check` performs the same compilation in memory and reports drift.

## Compiler and workflow structure

The implementation is intentionally split into narrow layers:

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
                        semantic proposal generation
                                      ↓
                       onboarding_proposal.py
                         strict deterministic validation
                                      ↓
                         later human review/acceptance
                                      ↓
                         authored context → normal compiler
```

Use modules according to their contracts:

- **`model.py`** — typed compiler data only.
- **`parser.py`** — authoring grammar and syntax validation; no filesystem writes.
- **`compiler.py`** — semantic compiler truth: Source composition, Rule changes, conflict/target validation, resource closure.
- **`package.py`** — immutable compiled package boundary, canonical semantic digest, exact package digest, serialization/loading/integrity checks.
- **`diff.py`** — exact compiled-Node comparison.
- **`package_diff.py`** — exact immutable Source-package comparison using the same diff model.
- **`render.py`** — deterministic human/machine projection; no hidden semantic decisions.
- **`links.py`** — local Markdown-link extraction for materialization closure.
- **`outputs.py`** — compare/write compiler-owned generated output.
- **`git_transport.py`** — retrieve candidate bytes only; no composition or acceptance semantics.
- **`sources.py`** — structural candidate review, deterministic receipt, and explicit acceptance.
- **`onboarding.py`** — deterministic pre-Context Git inventory, evidence selection, safety limits, content-addressed evidence snapshots, and snapshot publication; it must not make semantic classification decisions.
- **`onboarding_proposal.py`** — strict proposal schema, evidence-snapshot verification, provenance/hash/line-range validation, typed payload validation, and deterministic proposal identity; it validates semantic output but does not decide whether that output is correct or accepted.
- **`cli.py`** — command orchestration only.

See [docs/compiler.md](docs/compiler.md), [docs/external-sources.md](docs/external-sources.md), and [docs/onboarding.md](docs/onboarding.md).

## Design principles

### Deterministic truth first

If behavior can be specified exactly, implement it deterministically. LLMs are appropriate for semantic interpretation, not Node identity, Source/package resolution, Rule operations, exact diffs, package integrity, acceptance state, provenance, hashes, onboarding evidence identity, or proposal structural validity.

### Keep the pipeline one-way

Authoring is parsed into structures; compilation resolves meaning; immutable packages publish compiled meaning; diffs compare compiled meaning; rendering projects it. Never reconstruct semantic truth from generated Markdown.

Onboarding follows the same rule from an earlier project state: repository evidence is frozen first, semantic interpretation produces a proposal, deterministic validation verifies the proposal/evidence boundary, human acceptance creates authored ContextCanon source, and only then does the normal compiler run. LLM output is never parsed directly as Official Context.

### Stable identity beats wording and path

Rules and Nodes are referenced by stable identity. Renaming a Node, moving its directory, changing a Git `node-path`, or rewording a Rule must not silently retarget operations.

Onboarding likewise gives the frozen evidence set and normalized proposal their own deterministic digests so later review is not accidentally performed against a moving repository or a different proposal.

### Fail rather than guess

Unsupported syntax, incomplete pins/transport metadata, dangling Changes, duplicate identities, cycles, package corruption, invalid paths, unsafe onboarding evidence, malformed proposal provenance, or structural ambiguity should fail clearly.

### No implicit Source precedence

Multiple Sources are independent. Source order must not decide conflicts. Canonical semantic normalization likewise ignores ordering where the model does not assign semantic meaning.

### Distinguish semantics, presentation, transport, evidence, and proposal

`normalized_digest` identifies canonical compiled meaning. `package_digest` identifies exact human/agent package bytes. Git refs and repository paths are transport/location metadata, not either identity.

An onboarding `evidence_digest` identifies the exact selected input bytes and deterministic selection decisions offered to a semantic workflow. It does not claim that those bytes are correct project governance.

A validated onboarding `proposal_digest` identifies one exact typed interpretation of one exact evidence snapshot. Validation does not imply acceptance.

A candidate fetched from Git is not accepted context. Normal `build` must continue to consume the previously accepted package until explicit acceptance changes the pin.

### Keep accepted state reproducible

Accepted external packages under `.context/sources/<package-digest>/` are part of the consumer's reproducible project state and should be retained with a project that must build without its Source repository. Candidate packages are temporary update state.

Onboarding evidence under `.context/onboarding/<evidence-digest>/` is review input rather than accepted governance. It is content-addressed and transient by default.

### Keep filesystem mutation narrow

Compilation and diff should be possible in memory. Generated output, candidate retrieval, Source acceptance, and onboarding preparation each own only their explicit filesystem areas. Proposal validation is read-only. Never add generic repository cleanup.

### Preserve human review boundaries

Deterministic tooling can require that `source review` succeeds before `source accept`, but semantic decisions still belong to humans or explicitly invoked LLM workflows.

Onboarding is stricter still: `onboard prepare` only freezes evidence and `onboard validate` only proves structural/provenance validity. A later semantic producer must create a provenance-rich proposal, and human review/explicit acceptance stays between that interpretation and canonical `CONTEXT.src.md` creation or replacement.

### Preserve human readability

The canonical authoring format remains constrained Markdown. Machine state can be boring; humans should be able to understand source and official context without a framework-specific editor.

## Tests

Every deterministic feature should normally include:

- a successful fixture,
- important invalid/corrupt/dangling cases,
- transitive/composed cases when inheritance is involved,
- deterministic ordering/digest assertions where relevant,
- drift checks when generated output changes.

Compiler/package tests must not require a network service or an LLM. Git transport tests use local temporary Git repositories so CI remains self-contained. Onboarding tests likewise use local temporary Git repositories and must prove evidence identity, safety exclusions, explicit-inclusion behavior, immutable snapshot verification, total/every-file size bounds, proposal schema strictness, provenance/hash/line-range validation, deterministic proposal identity, and independence from an existing Context Node.

GitHub Actions runs the unit/repository tests and `contextcanon check --all .`. A change is not complete merely because unit tests pass: committed dogfood packages must also match current compiler output.

## Branch and merge cadence

`main` is the last accepted, fully reproducible ContextCanon stage. Work on one coherent core block per branch/PR, finish tests/docs/dogfood/CI, then squash-merge before starting the next unrelated block.

A core block is ready only when:

- deterministic positive and negative tests pass,
- dogfood was regenerated by the compiler itself,
- `contextcanon check --all .` is clean,
- documentation matches implemented behavior,
- `STATE.md` and `PLAN.md` describe the resulting stage and next block.

## Pull requests

Keep changes conceptually focused. Explain what changed, why it belongs in deterministic truth or in an explicit semantic layer above it, and which invariant/practical need it serves.

If a new feature makes compiler semantics depend on hidden transport behavior, generated presentation, an unbound repository snapshot, unvalidated semantic output, or an LLM judgment, redesign the boundary before merging.
