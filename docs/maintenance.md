# Maintain an existing ContextCanon project

Once a project is onboarded, normal ContextCanon maintenance is a short loop:

```text
inspect / update  →  propagate  →  build  →  check
```

You normally start from the project's `CONTEXT.md`. It tells you what applies here and where deeper context lives. `CONTEXT.src.md` is the human-edited local source; generated `CONTEXT.md`, `CONTEXT/`, and `.context/` state are not hand-maintained.

## The three pieces that can meet in one Node

A Context Node can combine context maintained elsewhere and add only what is special locally:

- **Source** — an independent reusable context imported into this Node, such as a Development Workflow or security baseline.
- **Parent** — an accepted higher-level project or subsystem context that this Child specializes.
- **Local Delta** — the Child's own Overview, Rules, Topics, Resources, and explicit Overrides/Removes.

A useful property follows from this model: **Parents and Children can evolve independently.** A Child keeps the last Parent snapshot it accepted. The Parent can continue changing without silently changing the Child. Later, ContextCanon can compare the newer Parent with the Child's accepted snapshot and help carry the change forward.

Think of a student's notes from a lecture: the lecture material may be revised later, while the student's existing notes stay exactly as they were until the changes are reviewed and incorporated. ContextCanon keeps the previous accepted snapshot so that comparison is deterministic rather than reconstructed from memory.

## Update a reusable Source

First see what this Node currently accepts:

```text
contextcanon source list
```

Then review a newer Source by human name:

```text
contextcanon source update "Development Workflow"
```

For a one-off branch, tag, or exact commit candidate:

```text
contextcanon source update "Development Workflow" --ref <git-ref>
```

The review first describes **what changed in the external Source package**. Accepting it changes the Source snapshot used by the direct consumer Node. It does not silently update descendant Nodes and it does not rebuild generated Markdown yet.

Imported Rules normally become part of the consumer's effective Context. A project-specific difference is expressed explicitly with a local Override or Remove and a rationale; Source order is never hidden precedence.

## Propagate an accepted change

After a higher-level Node changes, carry that accepted Context through dependent Child Nodes:

```text
contextcanon propagate --all
```

**Propagation** means: compare each Child's last accepted Parent snapshot with the newer Parent, show the difference, and accept the newer snapshot only after review. ContextCanon walks Parent edges top-down so a change can flow from a project root through subsystems to deeper Children without updating unrelated siblings.

The explicit Parent-edge commands remain available when you want to work on one relationship only:

```text
contextcanon parent review [<parent-node-id>] --node <child>
contextcanon parent accept [<parent-node-id>] --node <child>
```

## Render and verify

After accepted updates and propagation:

```text
contextcanon build --all .
contextcanon check --all .
```

`build` renders the accepted effective Context into the generated Official Context Packages. `check` verifies that the generated state matches the current authored and accepted state.

## The normal mental model

```text
Update      inspect and accept a newer Source or Parent snapshot
Propagate   carry an accepted Context change through dependent Parent edges
Build       render accepted effective Context
Check       verify that authored, accepted, and generated state agree
```

For the command map, see [CLI quick reference](cli.md). For the deeper composition model, including multiple Parents and conflict handling, see [Context composition](../nodes/library/foundation/docs/composition.md). For exact package and candidate mechanics, see [Immutable external Sources](../nodes/internal/framework-development/docs/external-sources.md).
