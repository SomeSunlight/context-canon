# Context Composition

ContextCanon combines independent context Sources instead of relying on a single inheritance tree.

```text
Business Context ──────┐
Python Context ─────────┤
Personal Style ─────────┼──> Local Delta ──> Official Context Package
Security Context ───────┘
```

A Source is an accepted published package from another Context Node. Sources may live in the same Git repository or in independent repositories. Filesystem containment does not create inheritance.

Local development Sources can be resolved directly from another Node in the same repository. Accepted external Sources are immutable packages pinned by Node/version identity plus exact semantic and package digests.

## No implicit precedence

Source order does not mean priority. ContextCanon must never silently apply "first source wins" or "last source wins" semantics.

Different Sources can therefore contribute independent elements without an artificial method-resolution order.

The compiler canonicalizes direct Source order in normalized semantics. Reordering two otherwise identical Sources therefore cannot accidentally change `normalized_digest` or masquerade as semantic precedence.

## Dependency graph

Source relationships form a directed acyclic graph. The compiler deterministically detects structural problems such as dependency cycles, invalid Source identities/versions, dangling Changes, and incompatible transitive states of the same stable Rule.

Compiler 0.4 supports local unpinned Sources and immutable pinned external Sources. Both become `CompiledPackage` before Rule composition, so the same transitive composition and conflict rules apply regardless of Source transport.

## Structural Rule conflicts

A stable Rule identity can reach a consumer through several Source paths. The compiler never uses Source order to choose between those paths.

Equivalent compiled Rules with the same effective definition and provenance are deduplicated. If the same stable Rule arrives with different effective definitions or override provenance, compilation fails.

Remove is also carried as machine-level provenance rather than being forgotten as mere absence. Therefore a diamond such as this is detectable:

```text
              ┌─ Source A: removes Rule X ─┐
Foundation ───┤                            ├─> Consumer: conflict
              └─ Source B: keeps Rule X ──┘
```

The consumer cannot silently keep or drop Rule X. It must resolve the Source relationship explicitly.

Two paths may both carry compatible removal provenance; the resulting Rule remains absent while the machine state preserves the removals needed for later composition and diagnostics.

## Semantic conflicts

Two different Source elements may contradict each other even though their IDs are unrelated. A deterministic compiler cannot reliably prove every natural-language conflict. It preserves both unless an explicit local resolution exists.

An optional LLM reviewer may flag likely conflicts, explain them, and suggest where to resolve them. The durable decision remains explicit in source.

## Local changes

A Node can resolve inherited ordinary Rules through explicit **Remove** and **Override** operations.

A Change addresses a Rule by stable identity:

```text
<origin-node-id>#<rule-id>
```

Visible names, titles, wording, and filesystem paths are not identity.

### Remove

Remove makes the inherited Rule no longer part of this Node's official Rule set. Descendants inherit the already-removed result.

The compiler keeps a removal record containing the Rule identity, removing Node, and rationale. This is machine semantics, not an active Rule shown to normal readers.

### Override

Override keeps the inherited Rule identity and origin but replaces its effective statement. The overriding Node and its rationale become provenance on the compiled Rule. If another descendant overrides it again, identity remains stable while the effective meaning and override provenance advance.

### Dangling operations

If the target Rule is not inherited, compilation fails. This matters especially after Source updates: a parent removing or replacing an element cannot silently leave a child operation pointing at nothing.

A Node may define only one local Change against the same inherited Rule identity.

Protected Rules and **Use Exception** remain a later semantic layer. Protected Rules will prohibit ordinary Remove/Override and expose only explicitly authorized exceptions.

## Transitive composition

Composition is package meaning, not just direct-parent text.

```text
Foundation ──> Team Standard ──> Project
```

If Team Standard overrides a Foundation Rule, Project inherits that overridden Rule with Foundation identity and Team Standard override provenance. If Team Standard removes the Rule, Project does not expose it as active context but still carries the removal provenance needed for downstream composition.

This is why the compiler renders inherited Rules by their actual origin Node rather than only by the consumer's direct Source list, and why the machine representation contains more state than the human-facing active Rule list.

An immutable external package carries this complete effective state in `.context/package.json`; a descendant does not reconstruct it by parsing generated `CONTEXT.md`.

## Deterministic diff is the update boundary

ContextCanon compares compiled state before any semantic reviewer or consumer code is involved.

For two snapshots of the same consumer Node:

```text
contextcanon diff <before-node-root> <after-node-root>
```

For an accepted external Source and a candidate Source package, `source review` applies the same stable-identity `ContextDiff` model directly to the immutable packages:

```text
accepted Source package
        +
candidate Source package
        ↓
deterministic package diff
        +
consumer structural validation
        ↓
review receipt
```

The diff reports Source package/version changes, effective Rule changes including active/removed transitions and override provenance, local Change differences, Topic changes, and materialized Resource content changes. Human-readable and JSON representations come from the same deterministic change model.

This means Source-update workflows do not need to infer change from prose or Git file layout. The exact compiled difference exists first; semantic impact analysis is an optional layer above it.

## Source updates are change requests

Consumers remain pinned to an accepted immutable Source package. A newly published Source version is an update candidate, not live inheritance.

Compiler 0.4 implements this workflow explicitly:

```text
contextcanon source fetch <source-node-id> --node <consumer-node>
        ↓
verified candidate under .context/candidates/<package-digest>/
        ↓
contextcanon source review <source-node-id> <candidate-package> --node <consumer-node>
        ↓
exact diff + consumer structural checks + deterministic review receipt
        ↓
contextcanon source accept <source-node-id> <candidate-package> --node <consumer-node>
        ↓
accepted immutable package + updated exact Source pin
        ↓
normal offline build
```

`source fetch` uses declared transport metadata only to discover candidate bytes. It cannot change accepted inheritance. `source review` substitutes the candidate into the actual consumer composition in memory so dangling local Changes and visible Rule collisions are detected before acceptance. `source accept` requires the matching non-stale review receipt.

The accepted Source pin records version, `normalized-digest`, and `package-digest`. Git `ref` and `node-path` remain update/location metadata rather than accepted identity.

## Accepted versus candidate state

Accepted external packages live under:

```text
<consumer>/.context/sources/<package-digest>/
```

They are reproducible consumer state and allow ordinary builds to remain independent of the Source repository.

Temporary update candidates live separately under:

```text
<consumer>/.context/candidates/<package-digest>/
```

A missing or corrupt accepted package is an error. It is never permission for `build` to fetch from the Source locator.

Package installation is staged and verified before atomic publication. Review receipts and Source-pin replacement are also published atomically. If the final canonical pin swap fails, the old `CONTEXT.src.md` and old accepted build state remain intact; a newly installed but unreferenced package is harmless immutable state.

## Topics and Resources compose transitively

A Source package carries its complete effective Topic set, not only the Topics authored directly in that Source. Resource targets are compiled to package-safe paths namespaced by the Topic's stable origin Node identity. Descendants therefore inherit both Topic conditions and the exact materialized Resource closure without consulting the Source repository.

When the same inherited Topic identity reaches a Node through several Source paths, equivalent Topic definitions are deduplicated. If their effective definitions differ, compilation fails. Origin-qualified Resource paths behave the same way: identical bytes deduplicate, while different bytes at the same stable inherited path are a structural conflict.

`Context Node` Topic targets remain navigation rather than composition. Packages preserve the stable target Node ID/name so an inherited Topic can still explain where it points; a consumer does not invent a local link when that target Node is not materialized in the consumer package.

## Navigation is not composition

A Topic may direct an agent to deeper information or even to another Context Node when a task needs it. That is progressive disclosure, not inheritance.

```text
Gateway ──Topic──> Deeper Context Node
                         ▲
                         │ Source
                    Foundation
```

The Gateway does not inherit the deeper Node. It merely sends relevant work there. The deeper Node composes Foundation only when that Source relationship is declared explicitly.

Keeping these relationships distinct prevents navigation choices from silently changing which Rules a Node publishes.

## Node directories do not define composition

Every Context Node is physically rooted in its own directory, but that directory is only its location. A parent directory, nested directory, Git repository, or sibling directory does not become a Source automatically.

This matters in repositories containing several Nodes: filesystem structure can organize them clearly without creating hidden context relationships.

The same principle applies to Git transport. A `node-path` says where the Node is found inside a retrieved repository snapshot; the stable Node ID says which Node it is.
