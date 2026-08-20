# Compiler Walking Skeleton

ContextCanon now has an executable deterministic core. The first compiler is deliberately small: it implements the path from authored `CONTEXT.src.md` to generated context for the repository's current dogfood Nodes without trying to finish the whole future language.

## Commands

After installing the project in editable mode:

```text
python -m pip install -e .
contextcanon build --all .
contextcanon check --all .
```

`build` parses and validates source, resolves local Sources, composes Rules, generates official entries and machine state, materializes Topic resources, and creates configured harness adapters.

`check` performs the same deterministic compilation in memory and exits non-zero when committed generated output has drifted.

Both commands also accept a single node-root directory instead of `--all`.

## What is deterministic now

The walking skeleton already handles:

- node-root discovery from `CONTEXT.src.md`,
- stable Node IDs and versions,
- local filesystem Sources inside one repository,
- Source ID/version validation,
- dependency-cycle detection,
- local Rules with stable IDs, titles, groups, and rationale,
- Rule composition without Source precedence,
- Required and Optional Topic targets,
- explicit `Resource` versus `Context Node` targets,
- validation that targets stay inside the repository,
- `CONTEXT.md` generation,
- optional `CONTEXT/` resource materialization,
- `.context/context.yaml` generation,
- semantic and package SHA-256 digests,
- thin `AGENTS.md` and `.goosehints` generation when requested by Node metadata,
- drift detection.

No LLM is involved in any of these operations.

## Materialization closure

A Resource target is only the seed of a self-contained package. If a materialized Markdown resource links to another local file, the compiler follows that link recursively and materializes the referenced file as well. External URLs remain external.

This behavior was discovered by running the first compiler against ContextCanon itself: directly copying `docs/source-format.md` would have left its link to `compiler.md` broken inside the published package.

## Deliberate limitations

Walking Skeleton 1 does not yet implement the whole specification. In particular:

- Sources are local filesystem Nodes; Git/package locators come later.
- Inherited Rules are composed; Topic inheritance across Source package boundaries is deferred until package-locator and materialization behavior is exercised in a real external project.
- Remove, Override, protected Rules, and authorized exceptions are not implemented yet.
- Source update acceptance and immutable external package pinning are not implemented yet.
- Natural-language semantic conflicts are never guessed by the compiler.

Unsupported behavior should fail clearly rather than be approximated silently.

## Digests

The compiler calculates two exact hashes:

- `normalized_digest` identifies the normalized compiled semantic model used by the current Node.
- `package_digest` identifies the generated human/agent package: `CONTEXT.md` plus any materialized `CONTEXT/` resources.

Generated machine state is excluded from `package_digest` so the digest does not contain itself.

## Test strategy

Compiler tests use temporary repository fixtures and standard-library `unittest`. They require no network, external service, or model. The dogfood graph is represented by Gateway, Foundation, and Framework Development fixtures so compiler changes repeatedly exercise the same structural relationships as this repository.

A separate repository-consistency test checks local Markdown links. This catches ordinary maintenance drift that ContextCanon itself should make harder to create.

## Next semantic layer

The compiler remains the skeleton. The next end-to-end experiment adds an LLM above it: first to propose context for a real project, then to consume an exact compiled Context diff and identify which code, configuration, tests, or documentation are likely affected by a changed Rule.
