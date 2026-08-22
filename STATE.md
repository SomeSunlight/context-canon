# Current State

ContextCanon has moved beyond architecture-only prototyping and beyond its first external proof. Compiler 0.3 is the accepted baseline on `main`: deterministic self-hosting, real-project/harness validation, inherited Rule changes, canonical semantic normalization, and exact compiled Context diff are established.

## Accepted stable baseline

PR #2 was squash-merged to `main` as commit `c2e3f1af3e9b80f81d6adb9b6eeb04c297bee910`.

The accepted baseline has 26 deterministic regression tests plus repository dogfood drift checking. The compiler remains dependency-free and no LLM participates in deterministic compiler truth.

The first external experiment used `SomeSunlight/teams-chat-exporter` and validated the intended runtime path end to end:

- generated files improved architectural orientation for a human reviewer;
- GitHub Copilot entered through generated `AGENTS.md` and used `CONTEXT.md`;
- an ordinary task stayed small;
- a Teams selector-maintenance task followed its Topic and loaded Required deeper resources;
- the model correctly preferred dated selector configuration over unnecessary Python changes;
- a low-cost model produced a strong project-specific answer when given the structured ContextCanon path.

The practical conclusion remains: ContextCanon should now be hardened for broad daily use rather than subjected to more artificial proof-of-value tests.

## Current design baseline

- Every Context Node has one physical node-root directory; path is location, not identity.
- `CONTEXT.src.md` is the human-editable source of truth.
- `CONTEXT.md` is the generated compact official entry view.
- `CONTEXT/` is optional deeper compiled/materialized context.
- `.context/` is generated machine state and normally ignored by humans.
- Topics provide Required/Optional progressive disclosure.
- Topic navigation does not imply Source composition.
- Source composition is a DAG with no implicit Source precedence.
- Stable IDs address context elements independently of titles, wording, and paths.
- Inherited Rule `Remove`/`Override` preserve exact identity and provenance transitively.
- `normalized_digest` identifies canonical semantic state; `package_digest` identifies exact human/agent package bytes.
- `contextcanon diff` compares two compiled snapshots of the same stable Node by identity and provenance.
- Harness-specific files remain thin generated adapters; the tested JetBrains Copilot setup uses `AGENTS.md`.
- Deterministic operations form the framework skeleton; LLMs assist only where semantic interpretation is actually needed.

## Executable compiler 0.3 baseline

```text
contextcanon build --all .
contextcanon check --all .
contextcanon diff <before-node-root> <after-node-root>
contextcanon diff <before-node-root> <after-node-root> --json
```

The implementation remains layered so parsing, semantic composition, rendering, filesystem output, and diffing can be tested independently.

## Active Compiler 0.4 block: immutable external Sources

Development continues on `agent/immutable-external-sources`.

The central package boundary now exists. Every compiled Node can publish a standalone immutable artifact consisting of:

```text
.context/package.json
CONTEXT.md
CONTEXT/              optional
```

The machine manifest contains enough exact state to reconstruct downstream Rule composition without the Source repository: effective Rule statements/rationales/groups, stable origins, Override provenance, Remove provenance, local Changes and Topics, transitive Source dependency identities, exact file hashes, `normalized_digest`, and `package_digest`.

The package loader verifies semantic and byte-level integrity and has regression coverage for tampering, missing resources, and path escape. A round-trip test deletes the original Source repository before loading the artifact.

Pinned external Source references now carry both `normalized-digest` and `package-digest`. The pair is all-or-nothing. A consumer resolves an accepted pinned package from:

```text
<consumer-node>/.context/sources/<package-digest>/
```

A normal build does not dereference the pinned Source locator. Regression coverage deliberately uses an unusable `https://example.invalid/...` locator, removes the Source checkout, and still composes inherited Rules plus a local Override successfully from the accepted package alone.

Local unpinned Sources remain the simple development path. Both local and pinned Sources now enter Rule composition through the same `CompiledPackage` semantic boundary.

The current deterministic suite has 36 passing tests. Repository dogfood output is intentionally not frozen yet because 0.4 documentation and machine manifests are still changing; current CI failure is generated-output drift only.

Remaining work in this block includes removing a temporary 0.3 compatibility view used by renderer/diff code, documenting the pinned Source contract, candidate discovery, deterministic accepted-versus-candidate comparison, explicit acceptance, multi-Node external addressing, and a first practical Git/repository transport. Normal `build` must remain offline and must never silently change an accepted Source.

## Next validation: LLM-assisted onboarding of an existing project

The next larger 1:1 test must exercise **framework-driven onboarding**, not another manually curated ContextCanon setup.

An existing project often already contains context spread across `README.md`, `CONTRIBUTING.md`, architecture/development documents, agent instructions, configuration, and source-code conventions. ContextCanon needs a reproducible way to ask an LLM with repository access to reorganize that material into a proposed ContextCanon structure.

This belongs above deterministic compiler truth:

```text
existing project
      ↓
deterministic inventory
      ↓
framework-supplied LLM onboarding instruction
      ↓
reviewable proposal with provenance
      ↓
mandatory human review
      ↓
explicit acceptance
      ↓
normal ContextCanon build
```

The onboarding LLM must not simply copy everything into one local Node. It must distinguish project-local Rules and Topics from existing reusable Sources and from **candidate generic Nodes**. Typical reusable candidates include Python development conventions, testing policy, writing/user-guidance style, language conventions, and other practices that should not be duplicated independently in every project.

Every proposed item must remain traceable to existing project material, and uncertainty or contradictions must be surfaced rather than guessed away. A proposal for a new generic Node is itself subject to separate review; onboarding may recommend such extraction but must not silently publish shared policy.

The result is also required to preserve useful normal repository documents. ContextCanon onboarding is not a destructive migration that empties README or CONTRIBUTING merely because some of their content becomes canonical context.

The larger external test will therefore run a framework-generated onboarding instruction through an LLM that has repository access, review its proposal against the project sources, explicitly accept the corrected result, compile it, and only then test normal and Topic-specific agent tasks. The onboarding structure must not be authored in advance from this conversation's accumulated knowledge.

See [PLAN.md](PLAN.md) for the detailed Source-hardening and onboarding roadmap.
