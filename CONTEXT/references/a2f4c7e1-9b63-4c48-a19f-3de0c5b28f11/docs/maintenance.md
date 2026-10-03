# Maintain an existing ContextCanon project

Once a project is onboarded, normal ContextCanon maintenance is a short loop:

```text
inspect / update  →  review downstream impact when needed  →  build  →  check
```

You normally start from the project's `CONTEXT.md`. It tells you what applies here and where deeper context lives. `CONTEXT.src.md` is the human-edited local source; generated `CONTEXT.md`, `CONTEXT/`, and `.context/` state are not hand-maintained.

## The three pieces that can meet in one Node

A Context Node can combine context maintained elsewhere and add only what is special locally:

- **Parent** — normative higher-level Context. Its Rules apply here; its Topics/Resources are available; the resulting normative Context may continue to semantic Children.
- **Reference** — useful related Context for this Node only. Its Rules do not apply and the relationship is not inherited.
- **Local Delta** — the Node's own Overview, Rules, Topics, Resources, and explicit Overrides/Removes against inherited Parent Rules.

Parents and Children can evolve independently. A Child keeps the last Parent snapshot it accepted. The Parent can continue changing without silently changing the Child. A Reference is also immutable/pinned when accepted, but updating it affects only the direct Node's informational Context.

Think of a technical standard plus a bibliography: an inherited standard constrains the subsystem; a cited paper can help explain the work without becoming a rule for every descendant.

## Inspect and update reusable imports

The current Phase-1 compatibility CLI keeps reusable import maintenance under `contextcanon source ...`. The command is a package/discovery surface, **not a third semantic relationship type**.

First inspect what this Node uses:

```text
contextcanon source list
```

Each entry is labeled `Parent` or `Reference`.

Then review a newer immutable package by human name:

```text
contextcanon source update "Development Workflow"
```

For a one-off branch, tag, or exact commit candidate:

```text
contextcanon source update "Development Workflow" --ref <git-ref>
```

For a **Parent**, the guided review explains the candidate's normative local effect and, after acceptance, any downstream Parent/Child review still needed. For a **Reference**, effective Rules are unchanged by definition; acceptance updates only this Node's informational Reference Context and no propagation step follows.

Before accepting either package, check that the candidate itself is correct and that the relationship kind is still the right one. A package that should govern this Node is a Parent; a package that is merely useful background is a Reference.

### Normalize legacy Sources once

Older `CONTEXT.src.md` files may still use `## Sources` with no explicit relationship marker. Their historical semantics were normative, so ContextCanon reads every such legacy import as **Parent**. It never silently converts one to Reference.

Make that default visible across a repository with:

```text
contextcanon source normalize --all .
```

This mechanically changes `Sources` to `Context Imports` and adds `relationship=parent` where the type was implicit. It does not make a semantic choice for the owner. Change an individual import to `relationship=reference` only when that is the intended relationship.

Normalization is explicit because ordinary `build` and `check` remain non-mutating with respect to human-authored semantic source. After normalization or an intentional reclassification, rebuild and verify normally.

## Propagation is downstream review, not blind copying

When an accepted higher-level Context changes, dependent Children may need to move to a newer Parent snapshot. **Propagation** is the guided review of those Parent → Child edges, top-down.

For every changed edge, make this quick conceptual check before accepting it:

1. **Still applicable here?** Do the incoming changes make sense for this Child, or does this Child need a justified local Override/Remove?
2. **Compatible with the other imported Contexts?** If another Parent says something incompatible, resolve the scopes explicitly. Import order is never precedence.
3. **Is the upstream change itself good enough?** From this Child's viewpoint, is the Parent change correct, complete, and well-scoped? If not, improve the Parent/Source instead of compensating locally for a bad reusable rule.

If a question fails, the usual choices are deliberately different:

- fix the Parent when the reusable rule itself is wrong, incomplete, or too broad;
- use a local Override/Remove when the upstream rule is valid generally but intentionally does not apply here;
- add a narrower local Rule when the apparent conflict is really missing scope or precision.

Then do the detailed pass: read the actual changed Rules, Topics, Resources, and relevant local changes before accepting the edge. ContextCanon handles deterministic structural checks such as stable-identity conflicts and dangling changes; semantic correctness remains a human review decision.

For a read-only dependency check before changing anything, inspect propagation status:

```text
contextcanon propagate --status --all .
```

It returns exit code 1 when any local Child still accepts an older normative Parent export. Package-only changes whose normative export is unchanged are reported as requiring no propagation. The status check does not bump versions, create review receipts, or update accepted pins.

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

## Rename or move a Topic Resource

A direct Topic Resource has a stable Resource ID in `CONTEXT.src.md`. Its filesystem path is its **current location**, not its semantic identity. This lets ordinary repository cleanup remain explicit instead of turning every rename into a delete/add of Context meaning.

If you want ContextCanon to perform the move:

```text
contextcanon resource move docs/old-name.md docs/new-name.csv
```

ContextCanon moves the file and updates all ContextCanon Topic Resource locators that point to that same physical file. It preserves each owning Node's stable Resource identity. Arbitrary project-owned Markdown links are not blindly rewritten. If ContextCanon finds Markdown links that still point to the old Resource path, the move/reconcile result lists them explicitly for manual review.

If the file was already renamed in an IDE, file manager, or by Git, inspect the repository first:

```text
contextcanon resource status
```

A unique byte-identical candidate is displayed as an unconfirmed rename. Then run:

```text
contextcanon resource reconcile
```

The review shows the old and proposed new path, stable Resource IDs, exact hash match, byte count, and line count for UTF-8 text. ContextCanon asks before changing authoring state. Multiple identical candidates remain ambiguous in `status`; interactive `reconcile` offers them as a numbered human choice. Non-interactive `--yes` deliberately skips them rather than guessing.

> [!NOTE]
> This rename/reconcile path has now been exercised extensively in a real owner project. Unique renames were detected correctly, interactive confirmation preserved identity cleanly, and deliberately ambiguous byte-identical candidates were presented as explicit numbered choices instead of being guessed. The owner test completed successfully.

Markdown needs one extra safety check: moving an unchanged Markdown file can change what relative links such as `images/diagram.svg` mean. ContextCanon therefore compares the resolved package closure before and after the candidate move. A changed closure is not accepted as a simple rename.

Moving a Resource across a Context Node's physical ownership boundary is also not treated as a routine rename. That is a stronger semantic **rehome** operation and is deliberately refused by the first move implementation.

After an accepted move/reconciliation, render and verify normally:

```text
contextcanon build --all .
contextcanon check --all .
```

The exact package layout changes and therefore the package identity changes. ContextCanon's normal version discipline still applies, as do Parent propagation and immutable import update/review mechanisms for consumers of the changed package.

## Render and verify

After the intended updates and propagation reviews are accepted:

```text
contextcanon build --all .
contextcanon check --all .
```

`build` renders the accepted effective Context into the generated Official Context Packages. A single-Node `check` verifies that Node's authored, accepted and generated state. Repository-wide `check --all` goes one step further: it also runs the same read-only propagation-status logic as `propagate --status --all .` and returns non-zero while any local normative Parent/Child update remains pending. It never accepts or propagates the update automatically.

## The normal mental model

```text
Update      inspect and accept a newer Parent or Reference package
Propagate   review only normative Parent changes across dependent Children
Build       render accepted effective Context
Check       verify authored/generated consistency and, with --all, full local Parent propagation
```

For the command map, see [CLI quick reference](cli.md). For the deeper composition model, including multiple Parents and conflict handling, see [Context composition](../nodes/library/foundation/docs/composition.md). For exact package and candidate mechanics, see [Immutable external Sources](../nodes/internal/framework-development/docs/external-sources.md).
