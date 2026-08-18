# Architecture

ContextCanon separates a small human-facing surface from a deterministic machine core.

## Repository surface

```text
CONTEXT.src.md   human-editable local source
       +
accepted source packages
       |
       v
    compiler
       |
       +--> CONTEXT.md       official human/agent context
       +--> AGENTS.md        harness adapter
       +--> .goosehints      harness adapter
       +--> .context/        machine state/package data
```

## `.context/`

`.context/` is intentionally analogous to `.git/` in spirit: important infrastructure that normally stays out of the user's way.

The directory is versioned where reproducibility requires it, but ordinary humans and agents should not need to browse it.

The current POC collapses machine bookkeeping into one primary file:

```text
.context/
└── context.yaml
```

Future standalone source snapshots and materialized references may also live beneath `.context/`.

## Machine model

Internally, the compiler may have rich structures for:

- node identity and version,
- accepted source packages,
- normalized rules and future element types,
- explicit change operations,
- Topics,
- provenance events,
- dependency graph,
- file/resource hashes,
- package and normalized-context digests.

These structures do not need one user-facing file each.

## Deterministic core, semantic assistance at the edges

The compiler should deterministically handle what machines can prove:

- syntax and schema validation,
- stable IDs,
- dependency resolution,
- cycle/version errors,
- explicit remove/override/exception operations,
- provenance,
- materialization,
- exact diffs and hashes,
- generated views.

LLMs may later assist with inherently semantic work:

- bootstrapping context from existing repositories,
- detecting likely natural-language conflicts,
- explaining the impact of source updates,
- suggesting where a conflict is best resolved,
- applying accepted context changes to project code.

LLM judgments never replace deterministic package identity or explicit human-approved resolutions.

## Versioned accepted inheritance

A source update does not immediately change children. Each child accepts an exact published source version/revision and rebuilds deliberately.

This keeps independent Git repositories and projects on independent lifecycles while still allowing shared context to improve over time.
