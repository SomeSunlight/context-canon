# Context Composition

ContextCanon combines independent context Sources instead of relying on a single inheritance tree.

```text
Business Context ──────┐
Python Context ─────────┤
Personal Style ─────────┼──> Local Delta ──> Official Context Package
Security Context ───────┘
```

A Source is an accepted published package from another Context Node. Sources may live in the same Git repository, another repository, or eventually another package location. Filesystem containment does not create inheritance.

## No implicit precedence

Source order does not mean priority. ContextCanon must never silently apply "first source wins" or "last source wins" semantics.

Different Sources can therefore contribute independent elements without an artificial method-resolution order.

## Dependency graph

Source relationships form a directed acyclic graph. The compiler can deterministically detect structural problems such as dependency cycles, incompatible accepted Source versions, invalid referenced IDs, dangling changes, and illegal operations on protected elements.

Compiler 0.2 implements cycle detection, Source Node ID/version validation for local-path Sources, transitive Rule composition, dangling Remove/Override diagnostics, and deterministic conflicts for incompatible transitive states of the same stable Rule.

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

A Node can now resolve inherited ordinary Rules through explicit **Remove** and **Override** operations.

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

If the target Rule is not inherited, compilation fails. This matters especially after future Source updates: a parent removing or replacing an element cannot silently leave a child operation pointing at nothing.

A Node may define only one local Change against the same inherited Rule identity.

Protected Rules and **Use Exception** remain a later semantic layer. Protected Rules will prohibit ordinary Remove/Override and expose only explicitly authorized exceptions.

## Transitive composition

Composition is package meaning, not just direct-parent text.

```text
Foundation ──> Team Standard ──> Project
```

If Team Standard overrides a Foundation Rule, Project inherits that overridden Rule with Foundation identity and Team Standard override provenance. If Team Standard removes the Rule, Project does not expose it as active context but still carries the removal provenance needed for downstream composition.

This is why the compiler renders inherited Rules by their actual origin Node rather than only by the consumer's direct Source list, and why the machine representation contains more state than the human-facing active Rule list.

## Source updates are change requests

Consumers ultimately remain pinned to an accepted Source package. A newly published Source version is an update candidate, not live inheritance.

The intended workflow is: detect a newer package, compute a deterministic diff, identify structural consequences such as dangling Changes, optionally add semantic LLM review, explicitly accept the update, and rebuild the consumer.

Compiler 0.2 records local Source version plus compiled Source package digest, but immutable external package resolution and acceptance are not yet implemented.

## Navigation is not composition

A Topic may direct an agent to deeper information or even to another Context Node when a task needs it. That is progressive disclosure, not inheritance.

```text
ContextCanon Gateway ──Topic──> ContextCanon Framework Development
                                      ▲
                                      │ Source
                           ContextCanon Foundation
```

The Gateway does not inherit Framework Development. It merely sends framework-development work there. Framework Development does inherit Foundation as a Source and then adds its local delta.

Keeping these relationships distinct prevents navigation choices from silently changing which Rules a Node publishes.

## Node directories do not define composition

Every Context Node is physically rooted in its own directory, but that directory is only its location. A parent directory, nested directory, Git repository, or sibling directory does not become a Source automatically.

This matters in repositories containing several Nodes: filesystem structure can organize them clearly without creating hidden context relationships.

## ContextCanon's own Node organization

This repository contains three real Nodes:

- the repository root is **ContextCanon Gateway**,
- `nodes/library/foundation/` is **ContextCanon Foundation**,
- `nodes/internal/framework-development/` is **ContextCanon Framework Development**.

The intermediate `nodes/`, `nodes/library/`, and `nodes/internal/` directories are organizational containers, not Context Nodes.

Every reusable Node distributed in the **ContextCanon Node Library** must compose Foundation directly or transitively through another library Node. That is a policy of this library, not a required directory structure or inheritance Rule for unrelated projects using ContextCanon.

Compiler 0.2 supports local node-root locators. Immutable external repository/package locators remain a planned core step.
