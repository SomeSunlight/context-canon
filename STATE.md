# Current State

ContextCanon has moved beyond architecture-only prototyping and beyond its first external proof. Compiler 0.3 is now the accepted baseline on `main`: deterministic self-hosting, real-project/harness validation, inherited Rule changes, canonical semantic normalization, and exact compiled Context diff are all established.

## Accepted stable baseline

PR #2 was squash-merged to `main` as commit `c2e3f1af3e9b80f81d6adb9b6eeb04c297bee910`.

The accepted baseline has 26 deterministic regression tests plus repository dogfood drift checking. The compiler remains dependency-free and no LLM participates in deterministic compiler truth.

The first external experiment used `SomeSunlight/teams-chat-exporter` and validated the intended runtime path end to end:

- generated files improved architectural orientation for a human reviewer;
- GitHub Copilot entered through generated `AGENTS.md` and used `CONTEXT.md`;
- an ordinary task stayed small;
- a Teams selector-maintenance task followed its Topic and loaded the Required deeper resources;
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

## Executable compiler 0.3

```text
contextcanon build --all .
contextcanon check --all .
contextcanon diff <before-node-root> <after-node-root>
contextcanon diff <before-node-root> <after-node-root> --json
```

The implementation is intentionally layered:

```text
parser.py → model.py → compiler.py → render.py → outputs.py
                         │
                         └────────────→ diff.py
                                           ↑
                                        cli.py
```

See [docs/compiler.md](docs/compiler.md) for the current compiler contract.

## Active block: immutable external Sources and update acceptance

Development now continues on fresh branch `agent/immutable-external-sources`, created directly from the accepted 0.3 `main` commit.

The purpose of this block is to let a consumer compose a reusable Source **without requiring the Source repository to be live or checked out during normal deterministic builds**.

The key architecture question comes before transport syntax: define the smallest immutable compiled Source artifact that contains enough semantic state for downstream composition and enough human/agent material for inspection. Transport, cache, candidate discovery, and explicit acceptance must remain separate from semantic composition.

The intended update model is:

```text
accepted immutable Source package
          ↓
offline deterministic consumer build

newer candidate package
          ↓
exact Context diff
          ↓
optional semantic impact review
          ↓
explicit acceptance
          ↓
new deterministic consumer build
```

A normal `build` must never silently fetch or switch a consumer to a newer Source package.

See [PLAN.md](PLAN.md) for the ordered implementation steps and merge cadence.
