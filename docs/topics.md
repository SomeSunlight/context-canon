# Topics

Topics are ContextCanon's primary progressive-disclosure mechanism.

The official entry context should contain only broadly useful rules and a concise map to deeper information. Detailed architecture, logging, release, security, database, domain, glossary, examples, or experience can remain focused and be loaded when relevant.

## Required and optional material

A Topic has:

- a human name,
- a natural-language description of when it matters,
- **Required** references that must be loaded when the Topic applies,
- **Optional** references that remain available when deeper exploration is useful.

Example:

```markdown
### Logging

When changing logging, diagnostics, structured events, rotation, or troubleshooting:

Required:
- `docs/logging-contract.md`

Optional:
- `docs/logging-history.md`
- `docs/troubleshooting.md`
```

The exact V1 syntax is not yet frozen, but the semantic distinction is now required by the design.

## Recursive progressive disclosure

A required document should itself put the most important information first and may link to deeper detail.

This makes ContextCanon behave more like a well-designed website than a giant prompt file: orientation first, mandatory next steps explicit, optional depth available on demand.

## Why "Topics"?

"Routing" describes an implementation mechanism. "Topics" describes what humans actually think about: Logging, Architecture, Security, Releases, and so on.

## References stay where they naturally belong

A Topic may point to existing project documentation such as `SECURITY.md`, `CONTRIBUTING.md`, or `docs/architecture.md`. ContextCanon should not duplicate content merely to move it into a framework-specific folder.

When a node is published for standalone reuse, normative referenced material can be materialized into the published package so children do not depend on live access to the original source repository.

## Loading is not compilation

The compiler deterministically preserves Topic structure and package resources. Deciding that a natural-language task matches a Topic may be performed by an agent/harness unless a future deterministic trigger is available.

Once a Topic applies, the distinction between Required and Optional is explicit rather than left to hidden harness behavior.
