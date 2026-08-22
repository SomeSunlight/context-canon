# Current State

ContextCanon has moved beyond architecture-only prototyping and beyond its first external proof. The framework now has a deterministic compiler, successful self-hosting, a successful real-project/harness validation, inherited Rule changes, and an exact compiled Context diff.

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

## Executable compiler 0.3

The dependency-free Python CLI now has three core operations:

```text
contextcanon build --all .
contextcanon check --all .
contextcanon diff <before-node-root> <after-node-root>
```

`diff` also supports `--json` for deterministic machine-readable output.

Compiler 0.3 handles:

- node-root discovery,
- stable Node identity and version metadata,
- local filesystem Sources,
- Source identity/version validation and cycle detection,
- transitive inherited Rule composition,
- `Remove` and `Override` operations on inherited ordinary Rules,
- dangling and duplicate Change diagnostics,
- transitive Override and Remove provenance while preserving original Rule identity,
- deterministic diamond-graph conflict handling without Source precedence,
- Required/Optional Topic targets,
- explicit Resource/Context Node target types,
- `CONTEXT.md` generation,
- optional `CONTEXT/` materialization,
- recursive materialization closure for local Markdown links,
- `.context/context.yaml` generation,
- canonical semantic normalization and exact normalized/package SHA-256 digests,
- deterministic Context diff by stable identities for Nodes, Sources, Changes, Rules, Topics, and Resources,
- human-readable and JSON diff output,
- thin AGENTS/goose adapters,
- deterministic drift checking.

The implementation is intentionally layered:

```text
parser.py → model.py → compiler.py → render.py → outputs.py
                         │
                         └────────────→ diff.py
                                           ↑
                                        cli.py
```

`parser.py` owns authoring grammar, `compiler.py` semantic truth, `render.py` deterministic projection, `outputs.py` filesystem comparison/writes, `diff.py` exact comparison of compiled states, and `cli.py` orchestration. See [docs/compiler.md](docs/compiler.md).

## Compiler quality findings

Compiler hardening has already exposed defects that were not obvious from the architecture alone:

- while adding Rule changes, a transitive rendering defect was found: a grandparent Rule could be semantically inherited but omitted from a deeper descendant's `CONTEXT.md`;
- diamond tests showed that Remove needs explicit transitive removal provenance rather than disappearing as simple absence;
- diff work exposed that `normalized_digest` must canonicalize semantically unordered collections such as Source order and Topic-target presentation order.

Regression tests now cover these cases. This reinforces the development policy: central compiler semantics receive deterministic positive and negative fixtures before being trusted across many projects.

## ContextCanon dogfoods three Nodes

```text
ContextCanon Gateway ──Topic──> ContextCanon Framework Development
                                      ▲
                                      │ Source
                           ContextCanon Foundation
```

The compiler builds and checks all three from their `CONTEXT.src.md` files. Framework Development includes an always-on compiler-stage Rule and a dedicated Compiler Implementation Topic pointing to the detailed compiler contract.

## Current focus

Compiler 0.3 is in its release-completion phase: documentation, dogfood outputs, and final CI are being synchronized on `agent/compiler-walking-skeleton`.

Once that branch is fully green, PR #2 will be updated to describe the actual accepted baseline and squash-merged to `main`. `main` will then represent the last accepted, fully reproducible ContextCanon stage.

The next core block — **immutable external Sources and explicit update acceptance** — will start from that new `main` on a fresh branch. It will use the deterministic diff as the exact review input for Source package updates rather than silently changing consumers.

See [PLAN.md](PLAN.md) for the ordered core-hardening roadmap and branch/merge cadence.
