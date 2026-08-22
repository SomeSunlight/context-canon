# Contributing

ContextCanon has an executable deterministic compiler. Changes should keep the human model simple while preserving a compiler core that is exact, inspectable, and independently testable from any LLM.

## Before changing anything

1. Read the repository [CONTEXT.md](CONTEXT.md). It is intentionally a tiny Gateway.
2. For ContextCanon development work, follow its Required target to [nodes/internal/framework-development/CONTEXT.md](nodes/internal/framework-development/CONTEXT.md).
3. Read [STATE.md](STATE.md) for the current project situation.
4. Check [PLAN.md](PLAN.md) for the active compiler slice.
5. Load only the Topic material required for the task.

## Editing context

Three Context Nodes are currently dogfooded in this repository:

- Gateway: edit [CONTEXT.src.md](CONTEXT.src.md),
- Foundation: edit [nodes/library/foundation/CONTEXT.src.md](nodes/library/foundation/CONTEXT.src.md),
- Framework Development: edit [nodes/internal/framework-development/CONTEXT.src.md](nodes/internal/framework-development/CONTEXT.src.md).

Do not directly edit generated `CONTEXT.md`, `CONTEXT/`, harness adapters, or `.context/context.yaml` files.

After changing ContextCanon source or referenced material, rebuild and verify the generated result:

```text
python -m pip install -e .
contextcanon build --all .
contextcanon check --all .
```

`build` may add, replace, or remove files **inside compiler-owned generated package locations** so the filesystem matches the expected deterministic result. It must not treat arbitrary repository files as disposable generated output.

`check` performs the same compilation in memory and fails when committed output has drifted.

To compare two snapshots of the same stable Context Node:

```text
contextcanon diff <before-node-root> <after-node-root>
contextcanon diff <before-node-root> <after-node-root> --json
```

The diff is deterministic compiler output, not semantic LLM judgment.

## Compiler structure

The compiler is intentionally split into narrow layers:

```text
CONTEXT.src.md
      ↓
parser.py → model.py → compiler.py → render.py → outputs.py
                        │
                        └────────────→ diff.py
                                          ↑
                                       cli.py
```

Use the modules according to their contracts:

- **`model.py`** — typed data only. Do not put parsing, rendering, diff presentation, or filesystem mutation here.
- **`parser.py`** — authoring grammar and syntax validation. It produces typed source structures and must never write generated files.
- **`compiler.py`** — semantic truth: Source graphs, identity validation, Rule composition, Remove/Override, target validation, resource closure, provenance, canonical normalization, and digests.
- **`diff.py`** — exact comparison of two already-compiled Nodes by stable identity. It must not parse source, invent semantic meaning, or mutate files.
- **`render.py`** — deterministic projection from compiled structures to human/machine text. Do not hide semantic decisions in rendering.
- **`links.py`** — narrow local Markdown-link extraction used by materialization closure.
- **`outputs.py`** — compares and writes the exact generated output set. It should not know composition semantics.
- **`cli.py`** — command orchestration. Keep business logic out of the CLI.

See [docs/compiler.md](docs/compiler.md) for the complete compiler contract.

## Design principles

### Deterministic truth first

If behavior can be specified exactly, implement it deterministically. LLMs are appropriate for semantic interpretation, not for Node identity, dependency resolution, Rule operations, exact diffs, package contents, provenance, or hashes.

The same authored input plus the same accepted Sources must produce byte-identical official output.

### Keep the pipeline one-way

Parsing produces structures; compilation resolves meaning; diff compares compiled meaning; rendering projects meaning; the output layer compares or writes bytes. Later stages must not reconstruct decisions that belong to earlier ones.

This makes bugs local: a grammar failure belongs in the parser, a composition failure in the compiler, a comparison failure in the diff layer, a formatting failure in the renderer, and a drift/write failure in the output layer.

### Stable identity beats wording and path

Rules and other addressable elements are referenced by stable identity. Renaming a Node, moving its directory, or rewording a Rule must not silently retarget operations.

Remove/Override and deterministic Rule diff therefore bind the inherited Rule's origin Node ID plus Rule ID rather than its visible title.

### Fail rather than guess

Unsupported syntax, dangling Changes, duplicate operations or Source identities, cycles, identity mismatches, invalid targets, or structural ambiguity should produce a clear error. Do not make the compiler "helpful" by guessing semantics.

### No implicit precedence

Multiple Sources are independent. Source order must not become a hidden method-resolution order. If two Sources create a structural ambiguity, resolve it explicitly or fail.

Canonical semantic normalization must likewise ignore order where the model does not define order as meaningful.

### Distinguish semantics from presentation

`normalized_digest` identifies canonical compiled meaning. `package_digest` identifies exact published package bytes. A presentation-only reorder may change the package without changing semantic identity.

The deterministic diff should preserve this distinction rather than reporting cosmetic ordering as a semantic Rule or Topic change.

### Keep filesystem mutation narrow

Compilation and diff must be possible entirely in memory. Only the output layer writes files.

Generated cleanup must remain scoped to files/directories that ContextCanon can identify as compiler-owned. Never add a generic "delete everything that is not expected" behavior to a project directory.

### Preserve human readability

The source format is constrained Markdown because humans should be able to understand and review the project without a framework-specific editor. Machine state may be boring; human source and official context should remain lucid.

### Optimize the problem before the model

ContextCanon should make the relevant project knowledge obvious and progressively loadable. That helps strong models, but it is especially valuable for smaller, cheaper, and local models that should not spend capability rediscovering architecture and conventions on every task.

### Grow the compiler in coherent semantic blocks

After the successful external proof, ContextCanon no longer needs a new miniature use case before every obviously necessary core feature. It still should not batch unrelated semantics into one risky change.

Prefer one coherent compiler layer, complete its positive and negative regression tests, regenerate all dogfood Nodes, and let CI prove determinism before moving on.

## Tests

Run the deterministic test suite before publishing compiler changes:

```text
python -m unittest discover -s tests -v
```

The tests must not require an LLM, network service, or external repository. Every deterministic feature should normally include:

- at least one successful fixture,
- important invalid/dangling cases,
- a transitive/composed case when inheritance is involved,
- a determinism/drift check when generated output changes.

For diff behavior, add fixtures that prove stable identity, relevant changed fields, deterministic ordering/JSON, and the distinction between semantic and presentation-only changes.

GitHub Actions runs both the unit tests and `contextcanon check --all .`.

A change is not complete merely because unit tests pass: committed dogfood packages must also match current compiler output.

## Branch and merge cadence

`main` is the last accepted, fully reproducible ContextCanon stage. Work on a coherent core feature in a dedicated branch, keep that branch until its tests, documentation, dogfood outputs, and CI are complete, then merge it before starting an unrelated core block.

A core block is ready to merge only when:

- deterministic positive and negative tests pass,
- repository dogfood was regenerated by the compiler itself,
- `contextcanon check --all .` is clean,
- relevant documentation matches implemented behavior,
- `STATE.md` and `PLAN.md` describe the resulting stage and next block.

Prefer squash merges for these development blocks so `main` records clear accepted stages rather than every implementation experiment. Start the next major block from the new `main` on a fresh branch.

## Pull requests

Keep changes conceptually focused. Explain what changed, why it belongs in deterministic compiler truth, and which invariant or practical need it serves.

Separate deterministic compiler facts from LLM-assisted interpretation layered on top. If a new feature weakens reproducibility or makes a compiler stage depend on hidden behavior in another stage, redesign it before merging.
