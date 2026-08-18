# Topics

Topics provide progressive disclosure.

The official context should contain the small set of rules and navigation cues that are broadly useful. Detailed architecture, logging, release, security, database, or domain information can remain in focused documents and be loaded only when needed.

A Topic has a human name, a natural-language description of when it matters, and one or more references or skills to load.

Example:

```markdown
### Logging

When changing logging, diagnostics, structured events, rotation, or troubleshooting, read:
- `docs/logging.md`
```

## Why "Topics"?

"Routing" describes how a compiler or agent may implement the behavior. "Topics" describes what a user actually sees and thinks about: Logging, Architecture, Security, Releases, and so on.

ContextCanon keeps implementation vocabulary out of the normal human interface where possible.

## References stay where they naturally belong

A Topic may point to existing project documentation such as `SECURITY.md`, `CONTRIBUTING.md`, or `docs/architecture.md`. ContextCanon should not duplicate content merely to move it into a framework-specific folder.

When a node is published for standalone reuse, normative referenced material can be materialized into the published package so children do not depend on live access to the original source repository.
