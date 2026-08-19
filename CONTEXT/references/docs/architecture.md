# Architecture

ContextCanon separates a small human-facing authoring surface, a self-contained published context package, and deterministic machine bookkeeping.

## Compilation pipeline

```text
CONTEXT.src.md
       +
accepted source packages
       +
referenced source material
       |
       v
    compiler
       |
       +--> CONTEXT.md        compact official entry
       +--> CONTEXT/          materialized deeper context
       +--> .context/         machine state and package metadata
       +--> harness adapters  AGENTS.md, .goosehints, ...
```

`CONTEXT.md` plus `CONTEXT/` is the human/agent-facing Official Context Package. `.context/` is compiler-owned state about that package and its sources.

## Token economy is architectural

ContextCanon must not solve discoverability by eagerly loading everything.

The entry context contains broadly required information and a precise Topic map. Topic material is loaded only when relevant, with explicit Required versus Optional references. A deeper document may repeat the same pattern: summary first, links onward.

Progressive disclosure is therefore part of the architecture, not merely a writing preference.

## Natural source files, generated package files

Project documentation should stay where it makes sense to authors. The compiler materializes context resources into `CONTEXT/` when building the published package.

This creates a useful separation:

```text
docs/architecture.md                 human-edited source
CONTEXT/references/docs/architecture.md  generated package copy
```

Consumers can use the package without knowing the source repository layout.

## `.context/`

`.context/` is analogous to `.git/` in one important respect: it contains infrastructure that matters but should not dominate normal work.

The current POC uses one primary `.context/context.yaml` per node. It records node identity, accepted source packages, normalized element identities, provenance, resource mapping, and future hashes/digests.

Generated YAML may contain explanatory comments because occasional human inspection is useful, but it remains machine-owned.

## Nodes are not repositories

A ContextCanon node is an independently addressable and versioned context unit, not a Git repository.

This repository dogfoods two nodes:

```text
contexts/public/    ContextCanon Public (`t`)
repository root     ContextCanon Development (`t-intern`)
                    -> composes Public + local development delta
```

The public node is what ordinary client projects should consume. The internal node adds only the rules and Topics needed to design and implement ContextCanon itself.

A repository may contain several nodes; a node may also consume sources from other repositories or future package locations.

## The schema is the interface

ContextCanon does not currently need a third "interface node" analogous to a Java interface.

The structural contract — what a Node, Source, Rule, Topic, Change, package, and identifier must contain — belongs to the ContextCanon schema/specification. That schema is the interface implemented by every node.

A Context Node contains actual context content. We should create another base node only when there is reusable **content** that genuinely belongs neither to the public node nor to the internal one.

## Deterministic skeleton, semantic assistance at the edges

The compiler should deterministically handle what machines can prove:

- syntax and schema validation,
- stable IDs,
- dependency resolution,
- cycle and version errors,
- explicit remove/override/exception operations,
- dangling operation detection,
- provenance,
- package materialization,
- exact diffs and hashes,
- generated views and adapters.

LLMs may assist with work that genuinely requires interpretation:

- bootstrapping context from an existing repository,
- detecting likely natural-language conflicts,
- explaining the impact of source updates,
- suggesting where a conflict is best resolved,
- applying accepted context changes to project code.

LLM judgments never replace deterministic package identity or explicit durable resolutions.

## Versioned accepted composition

A source update does not immediately change consumers. Each consumer accepts an exact published source package and rebuilds deliberately.

This keeps independent projects on independent lifecycles while still allowing shared context to improve over time.
