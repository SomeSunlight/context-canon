# Topics

A Topic answers a practical question:

> When this kind of work is being done, what additional context should be read?

`CONTEXT.md` should stay small. It contains the Rules that are broadly relevant and a concise list of Topics. Each Topic describes when it matters and points to the deeper information needed for that work.

## Required and Optional information

A Topic contains two load intentions:

- **Required** — must be read when the Topic applies.
- **Optional** — useful for deeper understanding, troubleshooting, history, or unusual cases.

The source syntax also distinguishes target kind explicitly:

```markdown
### Logging

When changing logging, diagnostics, structured events, rotation, or troubleshooting:

Required:
- Resource: `docs/logging-contract.md`
  <!-- ctx:resource id="RESOURCE-LOGGING-CONTRACT" -->

Optional:
- Resource: `docs/logging-history.md`
  <!-- ctx:resource id="RESOURCE-LOGGING-HISTORY" -->
```

A Gateway can navigate to another Node without composing it:

```markdown
Required:
- Context Node: `nodes/internal/framework-development`
```

The distinction matters. A model should not guess whether a target is mandatory, and the compiler should not guess whether a filesystem path means package material or another Node.

## Explain an individual Resource

A Resource target may have one optional, indented, single-line `Why:` explanation:

```markdown
Required:
- Resource: `samples/variant-6.jsonc`
  Why: Version 6 - valid example of the current payload shape.
  <!-- ctx:resource id="RESOURCE-CURRENT-SAMPLE" -->
- Resource: `samples/variant-0-legacy.json`
  Why: Obsolete payload, retained for migration comparisons.
  <!-- ctx:resource id="RESOURCE-LEGACY-SAMPLE" -->
```

The text explains why this Resource is useful for this Topic. It is shown below the link in the generated context and retained in immutable packages and inherited Topics. A change to the explanation appears in Topic review.

`Why:` does not define a status or change the load intention. A Resource marked Required remains required even if its explanation calls it obsolete; its file must still exist. Use Optional when reading it is optional. The Resource identity comment may appear immediately before or after `Why:`. Legacy targets without a Resource ID can also have an explanation; registering them preserves the text.

Keep the explanation on one line and indent it below the Resource. Empty or repeated `Why:` fields, `Why:` on Context Node targets, and arbitrary text after the backticked locator are rejected. Move existing trailing annotations such as `(OBSOLETE)` onto `Why:` rather than adding a second authoring convention.

## Progressive disclosure can repeat

A required document should again put the most important information first. It may then point to more detailed material.

The result resembles a well-designed website: the first page gives orientation, important next steps are explicit, and deeper information remains one link away instead of being placed on the first page.

## Topics are also context integration

At first, a Topic may simply connect a task with a Markdown document. The mechanism is more general than that.

A Topic is a structured way to integrate additional information into the working context when it becomes relevant. Over time this may include:

- architecture and design documents,
- glossaries and domain terminology,
- coding patterns and example code,
- CSV files, schemas, tables, and other structured data,
- PDFs, images, and diagrams,
- skills and executable workflows,
- test fixtures and examples,
- operational experience, known pitfalls, and troubleshooting knowledge.

This is one of ContextCanon's larger opportunities: the same transparent mechanism can bring many kinds of project knowledge into an agent's context without making all of it permanently resident in the prompt.

## Resource identity and location

A direct Resource target has stable identity independent of its current path. The `ctx:resource` ID is scoped by its origin Context Node; the path beside it says where that Resource currently lives.

This distinction matters during ordinary maintenance. Renaming `reports/table.md` to `reports/table.csv` can preserve the same Resource identity after explicit review even though the package path changes. ContextCanon does not infer that semantic continuity merely from a filename or hash: `resource status` establishes deterministic facts and `resource reconcile` asks a human to confirm an externally performed move.

A physical file may be used as a direct Resource by several Context Nodes. Each Node owns its own Resource identity. A physical move therefore has to discover and update all affected ContextCanon locators together rather than updating one Node and leaving another dangling.

Transitive files reached from a Markdown Resource are different. They are exact materialization dependencies, not automatically first-class Resource identities. Their resolved closure is still safety-critical: a byte-identical Markdown move is refused as a simple rename if relative links would resolve to a different closure.

## Source location and published location

Authors should keep information where it naturally belongs. A security document may remain `SECURITY.md`; architecture documentation may remain under `docs/`; a glossary may live beside the domain model.

When ContextCanon builds an Official Context Package, Resource targets are seeds for materialization under `CONTEXT/`. If a materialized Markdown file links to another local file, that target is recursively included so the package remains internally navigable. External links remain external.

The generated `CONTEXT.md` links to the package-local seed resources; deeper links continue from there. A generated `CONTEXT/README.md` explains the package directory itself when materialized resources exist, including why `references/` contains copies and where those copies originated.

## What decides that a Topic applies?

The compiler preserves Topic definitions deterministically. A harness or agent may decide that a natural-language task matches a Topic, because that decision can require semantic interpretation.

Once a Topic applies, however, Required versus Optional and Resource versus Context Node are explicit. The harness should not invent its own meaning for those targets.

## Package composition

Effective Topics and their Resource closures compose across accepted Source and Parent package boundaries. Stable origin Node identity keeps inherited Resource identities scoped correctly while generated package paths keep exact materialized bytes inspectable.
