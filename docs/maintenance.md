# Maintain an existing ContextCanon project

Once a project is onboarded, normal ContextCanon maintenance is a short loop:

```text
inspect / update  →  review downstream impact when needed  →  build  →  check
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

## Propagation is downstream review, not blind copying

When an accepted higher-level Context changes, dependent Children may need to move to a newer Parent snapshot. **Propagation** is the guided review of those Parent → Child edges, top-down.

For every changed edge, make this quick conceptual check before accepting it:

1. **Still applicable here?** Do the incoming changes make sense for this Child, or does this Child need a justified local Override/Remove?
2. **Compatible with the other imported Contexts?** If another Parent or Source says something incompatible, resolve the scopes explicitly. Import order is never precedence.
3. **Is the upstream change itself good enough?** From this Child's viewpoint, is the Parent change correct, complete, and well-scoped? If not, improve the Parent/Source instead of compensating locally for a bad reusable rule.

If a question fails, the usual choices are deliberately different:

- fix the Parent or Source when the reusable rule itself is wrong, incomplete, or too broad;
- use a local Override/Remove when the upstream rule is valid generally but intentionally does not apply here;
- add a narrower local Rule when the apparent conflict is really missing scope or precision.

Then do the detailed pass: read the actual changed Rules, Topics, Resources, and relevant local changes before accepting the edge. ContextCanon handles deterministic structural checks such as stable-identity conflicts and dangling changes; semantic correctness remains a human review decision.

From one changed Node, start the guided downstream review with:

```text
contextcanon propagate
```

From a repository root, `--all` deliberately broadens the **review scope** to every semantic Parent graph in the repository:

```text
contextcanon propagate --all
```

`--all` is not blanket approval. Normal interactive propagation still stops at each changed Parent → Child edge for review and confirmation. The explicit `--yes` option exists for controlled automation and removes that per-edge confirmation; it is not the normal novice workflow.

The explicit Parent-edge commands remain available when you want to work on one relationship only:

```text
contextcanon parent review [<parent-node-id>] --node <child>
contextcanon parent accept [<parent-node-id>] --node <child>
```

A Child that accepts a newer Parent may itself become a changed Parent for deeper Children. Propagation therefore walks top-down, but each Child keeps its own last accepted snapshot until its turn is reviewed.

## Render and verify

After the intended updates and propagation reviews are accepted:

```text
contextcanon build --all .
contextcanon check --all .
```

`build` renders the accepted effective Context into the generated Official Context Packages. `check` verifies that the generated state matches the current authored and accepted state.

## The normal mental model

```text
Update      inspect and accept a newer Source or Parent snapshot
Propagate   review whether an accepted change should advance each dependent Child
Build       render accepted effective Context
Check       verify that authored, accepted, and generated state agree
```

For the command map, see [CLI quick reference](cli.md). For the deeper composition model, including multiple Parents and conflict handling, see [Context composition](../nodes/library/foundation/docs/composition.md). For exact package and candidate mechanics, see [Immutable external Sources](../nodes/internal/framework-development/docs/external-sources.md).
