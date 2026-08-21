# Current State

ContextCanon has moved beyond architecture-only prototyping and beyond its first external proof. The framework now has a deterministic compiler, successful self-hosting, and a successful real-project/harness validation.

## What has been validated

The first external experiment used `SomeSunlight/teams-chat-exporter` on a dedicated branch.

The result was positive end to end:

- the generated files made the project's assumptions and structure easier to understand for a human reviewer;
- GitHub Copilot entered through generated `AGENTS.md` and used the compiled project context;
- an ordinary task stayed small;
- a Teams selector-maintenance task followed its Topic and used the required deeper resources;
- the model correctly preferred dated selector configuration over unnecessary Python changes;
- a low-cost model produced a strong project-specific answer when given the structured ContextCanon path.

The practical conclusion is that ContextCanon should now be hardened for broad daily use rather than subjected to more artificial proof-of-value tests.

## Current design baseline

- Every Context Node has one physical node-root directory; the directory path is location, not identity.
- `CONTEXT.src.md` is the human-editable source of truth.
- `CONTEXT.md` is the generated compact official entry view.
- `CONTEXT/` is optional and contains deeper compiled/materialized resources only when a Node needs them.
- Topics provide progressive disclosure with Required and Optional targets.
- Topic targets explicitly distinguish a Resource from another Context Node.
- Topic navigation does not imply Source composition.
- A Node may compose multiple independent Sources without implicit Source precedence.
- Stable IDs are mandatory for addressable elements; inherited Rule changes bind stable origin Node ID plus Rule ID.
- `.context/` is generated machine state and normally ignored by humans.
- Harness/model-specific files are thin generated adapters only.
- Deterministic operations form the framework skeleton; LLMs assist only where semantic interpretation is actually needed.
- Standardizing this structure across projects is itself a feature: humans and agents can use the same orientation path even when project domains differ.

## Executable compiler 0.2

The dependency-free Python CLI remains:

```text
contextcanon build --all .
contextcanon check --all .
```

Compiler 0.2 handles:

- node-root discovery,
- stable Node identity and version metadata,
- local filesystem Sources,
- Source identity/version validation and cycle detection,
- transitive inherited Rule composition,
- `Remove` and `Override` operations on inherited ordinary Rules,
- dangling and duplicate Change diagnostics,
- transitive Override provenance while preserving original Rule identity,
- Required/Optional Topic targets,
- explicit Resource/Context Node target types,
- `CONTEXT.md` generation,
- optional `CONTEXT/` materialization,
- recursive materialization closure for local Markdown links,
- `.context/context.yaml` generation,
- exact normalized and package SHA-256 digests,
- thin AGENTS/goose adapters,
- deterministic drift checking.

The implementation is intentionally layered:

```text
parser.py → model.py → compiler.py → render.py → outputs.py
                                           ↑
                                        cli.py
```

`parser.py` owns authoring grammar, `compiler.py` semantic truth, `render.py` deterministic projection, `outputs.py` filesystem comparison/writes, and `cli.py` orchestration. See [docs/compiler.md](docs/compiler.md).

## Important compiler quality finding

While adding Rule changes, a transitive rendering defect was found before broad rollout: the old renderer grouped inherited Rules only by direct Sources, so a grandparent Rule could be semantically present but omitted from a deeper descendant's `CONTEXT.md`.

Compiler 0.2 renders inherited Rules by their true origin Node instead. Regression tests now cover this transitive case together with Override propagation and Remove propagation.

This reinforces the development policy: central compiler semantics receive deterministic positive and negative fixtures before being trusted across many projects.

## ContextCanon dogfoods three Nodes

```text
ContextCanon Gateway ──Topic──> ContextCanon Framework Development
                                      ▲
                                      │ Source
                           ContextCanon Foundation
```

The compiler builds and checks all three from their `CONTEXT.src.md` files. Framework Development now includes a concise always-on Rule describing the compiler stage boundaries and a dedicated Compiler Implementation Topic pointing to the detailed compiler contract.

## Current focus

The active block is completing compiler 0.2 and regenerating all dogfood output with green CI.

After that, the next planned core layer is an **exact deterministic Context diff** based on stable identities and provenance. That diff will then support immutable external Source update review and later LLM-assisted code-impact analysis without putting semantic guesswork inside the compiler.

See [PLAN.md](PLAN.md) for the ordered core-hardening roadmap.
