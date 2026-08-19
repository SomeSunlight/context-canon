# Architecture

ContextCanon separates a small human-facing surface from a deterministic machine core.

## Official package pipeline

```text
CONTEXT.src.md
       +
accepted source packages
       |
       v
    compiler
       |
       +--> Official Context Package
               |
               +--> CONTEXT.md       compact official entry
               +--> Topic material   required/optional deeper context
               +--> references       materialized where needed
               +--> skills/resources
               +--> .context/        normalized machine/package state
       |
       +--> AGENTS.md / .goosehints / other harness adapters
```

The package is canonical. Human/agent Markdown and machine YAML are generated views of the same result.

## Token economy is architectural

ContextCanon must not solve discoverability by eagerly loading everything.

The entry context contains broadly required information and a precise Topic map. Topic material is loaded only when relevant, with explicit Required versus Optional references. Deeper material may repeat this summary-first/link-onward pattern.

Progressive disclosure is therefore part of the package model, not merely a documentation style preference.

## `.context/`

`.context/` is intentionally analogous to `.git/` in spirit: important infrastructure that normally stays out of the user's way.

The directory is versioned where reproducibility requires it, but ordinary humans and agents should not need to browse it.

The POC collapses the primary machine bookkeeping into one `context.yaml` per node. Generated YAML may contain explanatory comments because occasional human inspection is useful, but it remains machine-owned.

## Nodes are not repositories

A ContextCanon node is an independently addressable/versioned context unit, not a Git repository.

A repository may contain several nodes. ContextCanon itself dogfoods this:

```text
contexts/standard/   public reusable ContextCanon Standard node
repository root      ContextCanon Development node
                     -> composes Standard + local development delta
```

Likewise, a node may consume sources from other repositories, local paths, or future package registries. Published/accepted packages rather than filesystem containment define composition.

## Machine model

Internally, the compiler may have rich structures for:

- node identity and version,
- accepted source packages,
- normalized rules and future element types,
- explicit change operations,
- Topics and load intent,
- provenance events,
- dependency graph,
- file/resource hashes,
- package and normalized-context digests.

These structures do not need one user-facing file each.

## Deterministic skeleton, semantic assistance at the edges

The compiler should deterministically handle what machines can prove:

- syntax and schema validation,
- stable IDs,
- dependency resolution,
- cycle/version errors,
- explicit remove/override/exception operations,
- dangling operation detection,
- provenance,
- materialization,
- exact diffs and hashes,
- generated views.

LLMs may assist with inherently semantic work:

- bootstrapping context from existing repositories,
- detecting likely natural-language conflicts,
- explaining the impact of source updates,
- suggesting where a conflict is best resolved,
- applying accepted context changes to project code.

LLM judgments never replace deterministic package identity or explicit durable resolutions.

## Versioned accepted composition

A source update does not immediately change consumers. Each child accepts an exact published source version/revision/package and rebuilds deliberately.

This keeps independent projects on independent lifecycles while still allowing shared context to improve over time.
