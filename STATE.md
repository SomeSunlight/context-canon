# Current State

ContextCanon has moved from architecture-only prototyping to an executable deterministic walking skeleton. The repository now dogfoods a real compiler instead of manually modeled generated files.

## Current design baseline

- Every Context Node has one physical node-root directory; the directory path is location, not identity.
- `CONTEXT.src.md` is the human-editable source of truth.
- `CONTEXT.md` is the generated compact official entry view.
- `CONTEXT/` is optional and contains deeper compiled/materialized resources only when a Node needs them.
- Topics provide progressive disclosure with Required and Optional targets.
- Topic targets explicitly distinguish a Resource from another Context Node.
- A Topic may navigate to another Context Node; navigation does not imply inheritance.
- A Node may compose multiple independent Sources without implicit Source precedence.
- Stable IDs are mandatory for addressable elements; published Rules expose them visibly.
- `.context/` is generated machine state and normally ignored by humans.
- Harness/model-specific files are generated adapters only.
- Deterministic operations form the framework skeleton; LLMs assist where semantic interpretation is actually needed.

## Executable compiler

Walking Skeleton 1 now provides a dependency-free Python CLI:

```text
contextcanon build --all .
contextcanon check --all .
```

The current compiler handles the subset required by the three ContextCanon dogfood Nodes:

- node-root discovery,
- stable Node identity and version metadata,
- local filesystem Sources,
- Source identity/version validation and cycle detection,
- local and inherited Rule composition,
- Required/Optional Topic targets,
- explicit Resource/Context Node target types,
- `CONTEXT.md` generation,
- optional `CONTEXT/` materialization,
- recursive materialization closure for local links from Markdown resources,
- `.context/context.yaml` generation,
- semantic and package SHA-256 digests,
- thin AGENTS/goose adapters,
- deterministic drift checking.

Unsupported future semantics such as Remove/Override/Exception operations deliberately fail rather than being guessed or approximated.

## ContextCanon dogfoods three Nodes

```text
ContextCanon Gateway ──Topic──> ContextCanon Framework Development
                                      ▲
                                      │ Source
                           ContextCanon Foundation
```

The compiler now builds and checks all three from their `CONTEXT.src.md` files. Their generated official entries, machine state, adapters, and package resources are compiler output rather than hand-maintained POC artifacts.

## Findings from implementing the compiler

The first executable slice already changed the specification in useful ways:

1. Rule titles must live in `CONTEXT.src.md`. Keeping them only in generated YAML or `CONTEXT.md` would violate the single-source-of-truth rule.
2. Topic target kind must be explicit. The compiler should never infer from a path whether a target is a Resource or another Context Node.
3. A directly referenced Resource is only a materialization seed. Local links from materialized Markdown must be followed recursively if the published package is to remain internally navigable.
4. Generated output is a complete expected set, not a loose collection of files. `check` therefore detects stale extra files as well as missing or changed files.
5. The deterministic tests caught implementation mistakes immediately during the first refactoring, validating the strategy of keeping the compiler independently testable from any LLM.

## Deliberate limits before the first external project

Walking Skeleton 1 currently keeps Topic navigation local to the consuming Node while composing inherited Rules. Topic inheritance across Source package boundaries is deferred until package-location and materialization behavior are exercised in a real external project.

External Git/package Sources, update acceptance, Remove/Override/Exception operations, resource collision policy, and more complex nested-repository boundaries also remain later hardening work.

## Current focus

The next customer is deliberately simple rather than another framework-internal case: apply ContextCanon on a dedicated branch of a small existing repository where the relationship between project files, local Context, generated output, and LLM behavior is obvious.

That external experiment should complete Walking Skeleton 1 and begin Walking Skeleton 2. It will also provide the first useful setting for the later Context-change → deterministic diff → LLM code-impact workflow.

See [PLAN.md](PLAN.md) for the active checklist and [docs/compiler.md](docs/compiler.md) for the executable compiler contract.
