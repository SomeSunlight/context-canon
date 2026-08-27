# Changelog

All notable ContextCanon changes will be documented here.

## Unreleased

### Added

- Initial public ContextCanon specification.
- Human-editable `CONTEXT.src.md` local-delta model.
- Generated compact `CONTEXT.md` entry view and optional `CONTEXT/` package resources.
- **ContextCanon Gateway** as a minimal root Node that routes framework-development work through normal Topic semantics.
- **ContextCanon Foundation** as the common baseline of the reusable ContextCanon Node Library.
- **ContextCanon Framework Development** as Foundation plus a local framework-development delta.
- **ContextCanon Development Workflow** as an internal self-hosted Node for recoverable LLM-assisted development, proportional verification, explicit project-owner review, and accepted-baseline closure after merge.
- Explicit node-root directory model: every Node has one physical root while stable identity remains independent of path.
- Repository separation between reusable Nodes under `nodes/library/` and ContextCanon-internal Nodes under `nodes/internal/`.
- Explicit distinction between Topic navigation and Source composition.
- Multi-Source context composition without implicit precedence.
- Stable IDs for addressable context elements, visible in published contexts.
- Topics with Required and Optional progressive-disclosure semantics.
- Context-integration roadmap for glossaries, structured data, examples, PDFs/images, skills, and experience.
- `STATE.md` and `PLAN.md` separation.
- Harness-neutral official context with thin generated adapters.
- Single `.context/context.yaml` machine-state concept per Node.
- Public documentation-style Rule for precise, plain technical prose.
- Executable deterministic compiler commands for build, drift checking, and exact compiled Context diff.
- Inherited Rule `Remove` and `Override` with stable identity, provenance, dangling diagnostics, and deterministic diamond-conflict handling.
- Canonical semantic normalization separated from exact package-byte identity.
- Immutable external Source packages with complete `.context/package.json` manifests and strict integrity verification.
- Offline accepted external Source composition from consumer-local exact package pins.
- Deterministic Source candidate diff/review receipts and explicit acceptance before changing an accepted Source.
- Generic Git candidate transport with explicit ref and multi-Node `node-path` addressing.
- Atomic staging/publication of candidate and accepted packages, review receipts, and canonical Source-pin updates, including recovery from a failed final pin swap.
- CI generated-drift diagnostics with exact short-lived snapshots for compiler-owned output.
- Deterministic `contextcanon onboard prepare` for pre-Context Git repositories, with conservative evidence selection, Git-ignore-aware inventory, explicit safe includes, immutable content-addressed evidence snapshots, and exact provenance.
- Onboarding evidence safety bounds for sensitive/generated paths, symlinks, UTF-8 text, 1 MiB per file, and 16 MiB total, with policy revalidation when snapshots are consumed later.
- Strict `contextcanon/onboarding-proposal/v0` review artifacts with typed classifications, rationale/confidence, exact evidence hashes and line ranges, kind-specific payload validation, and deterministic proposal identity.
- `contextcanon onboard validate` to verify untrusted semantic onboarding proposals against one exact frozen evidence snapshot without accepting or publishing project context.
- `contextcanon/onboarding-review/v0` human-review state bound to exact Evidence and Proposal identities, with human-owned Node identity and explicit `pending` / `accept` / `reject` decisions.
- `contextcanon onboard review` with a readable evidence report showing every semantic finding beside its rationale, confidence, proposed payload, exact references, and cited lines.
- `contextcanon onboard accept` as the explicit first-adoption publication action, including live-Evidence revalidation and refusal of incomplete or stale review state.
- Exact reusable Source-package binding across onboarding semantic review, human review, and final acceptance; accepted first-adoption Sources remain pinned and buildable offline.
- Staged first-adoption compilation that prevents unreviewed Markdown closure, detects project-owned output collisions before publication, refuses replacement of an existing `CONTEXT.src.md`, and rolls back newly created canonical/generated state after publication failure.
- Acceptance records binding exact evidence/proposal/review decisions, accepted Sources, and resulting Context/package identities.
- Authored documentation ownership under the Node that owns it, with generated `CONTEXT/references/` material clearly treated as package copies rather than a second authoring surface.
- Lightweight authored README orientation at useful repository directory boundaries and compiler-generated `CONTEXT/README.md` orientation for non-empty generated package trees.
- Separate review-ready and merge-ready development gates: coherent human review may happen with understood generated drift, while the exact merge head must pass the full deterministic suite and zero-drift check.
- Explicit post-merge accepted-baseline/state checkpoint so `PLAN.md`, `STATE.md`, README/CHANGELOG status, and historical PR wording are reconciled before the next coherent development block begins.
