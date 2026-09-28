# ContextCanon CLI quick reference

This is a navigation page, not a dump of every flag. Use `contextcanon <command> --help` for the exact options of one command.

## Everyday maintenance

| Goal | Command | What it does |
| --- | --- | --- |
| Show installed tool version | `contextcanon --version` | Confirms the installed ContextCanon release. |
| Inspect reusable Sources | `contextcanon source list` | Shows the Source versions currently used here plus candidate-discovery configuration. |
| Review/update one Source | `contextcanon source update <name-or-id>` | Shows what is used here now, what newer candidate was found, what changed there, what would change locally, and asks before applying it. |
| Use one exact candidate ref | `contextcanon source update <name-or-id> --ref <ref>` | Reviews one branch/tag/commit without making that ref durable configuration. |
| Review downstream impact | `contextcanon propagate` | Reviews changed Parent → Child relationships top-down from the current Node and asks before each acceptance. |
| Review every Parent graph | `contextcanon propagate --all` | Broadens the review scope to all semantic Parent edges in the repository; it does not imply blanket acceptance. |
| Render generated Context | `contextcanon build --all .` | Rebuilds every Context Node in the repository. |
| Verify generated state | `contextcanon check --all .` | Reports drift or consistency problems. |
| Inspect central discovery config | `contextcanon config show` | Validates and prints `contextcanon.yaml`. |

The normal loop is **Update → review propagation when needed → Build → Check**. See [Maintain an existing ContextCanon project](maintenance.md) for the short propagation checklist.

> [!IMPORTANT]
> `--all` means **all Parent edges are in review scope**. Interactive propagation still asks at every changed edge. `--yes` suppresses those confirmations and is intended for controlled automation, not as the default human workflow.

## Work on one Parent relationship

`Parent` is the semantic higher-level Context accepted by a Child; it is not filesystem nesting. A Child keeps its last accepted Parent snapshot until a newer one is reviewed and accepted.

```text
contextcanon parent review [<parent-node-id>] --node <child>
contextcanon parent accept [<parent-node-id>] --node <child>
contextcanon parent propagate [path] [--all]
```

The first two commands are useful for one explicit edge. `contextcanon parent propagate` remains the explicit Parent-oriented form of the normal user command `contextcanon propagate`.

Before accepting a Parent update, check three things: **does it still apply here, does it coexist with the Child's other imported Contexts, and is the upstream change itself correct and complete from this Child's viewpoint?** If not, fix upstream or make an explicit justified local resolution rather than relying on import order.

## Maintain Topic Resources

Direct Topic Resources have stable identities independent of their current repository paths. The Resource commands are deliberately grouped as one Git-like maintenance surface:

| Goal | Command | What it does |
| --- | --- | --- |
| List Resources | `contextcanon resource list` | Shows stable Resource ID, current path, owning Context Node, and the Topics that use it. |
| Inspect changes | `contextcanon resource status` | Compares registered Resources with the last built package and reports modifications, missing paths, moves, and exact-hash rename candidates without changing anything. |
| Register an older project | `contextcanon resource register` | Explicitly adds stable IDs to legacy path-only direct Topic Resources. Normal `build`/`check` never performs this migration silently. |
| Move a Resource explicitly | `contextcanon resource move OLD NEW` | Moves the physical file and updates every affected ContextCanon Resource locator atomically while preserving stable Resource IDs. `resource mv` is an alias. |
| Reconcile external renames | `contextcanon resource reconcile` | Reviews files already renamed by an IDE, file manager, or Git operation and asks before preserving their Resource identities at the new paths. |

These commands operate across the repository's Context Nodes by default because one physical file may be referenced by more than one Node.

For an externally performed rename, the normal flow is:

```text
contextcanon resource status
contextcanon resource reconcile
contextcanon build --all .
contextcanon check --all .
```

`status` starts conservatively with exact SHA-256 matches. A unique byte-identical candidate is shown as an unconfirmed rename; multiple identical candidates remain ambiguous. `reconcile` never transfers identity merely because hashes match: the human confirms semantic continuity. For Markdown Resources, ContextCanon also compares the resolved relative-link closure and refuses a simple move when the same bytes would now pull in different local dependencies.

For an older ContextCanon project that still has path-only Resources, migrate once:

```text
contextcanon resource register
contextcanon build --all .
contextcanon check --all .
```

`contextcanon check` remains non-interactive. If a registered Resource is missing, it reports the problem and points to the Resource status/reconcile workflow rather than guessing or rewriting authoring state.

## Author normal Context

```text
contextcanon author rule  [path] --group ... --title ... --statement ... --why ...
contextcanon author topic [path] --title ... --condition ... [targets...]
```

These commands allocate stable IDs so authors do not have to invent machine metadata manually. Direct edits to `CONTEXT.src.md` and authored Resources remain normal when appropriate.

## Compare Context

```text
contextcanon diff <before-node-root> <after-node-root>
```

This compares two compiled snapshots of the same Node using stable Context identities rather than Git line layout.

## Onboard a project

Start a first adoption with:

```text
contextcanon onboard init .
```

Then follow the generated `contextcanon-onboarding/PLAN.md`.

For the onboarding command map — especially **go back / restart** with `contextcanon onboard reset . --from <STEP>` — use the dedicated **[Onboarding CLI reference](onboarding-cli.md)**. The conceptual walkthrough remains in **[Onboard an existing project](onboarding.md)**.

## Lower-level Source commands

The guided `source update` command is the normal human path. Separate commands remain available when automation or debugging needs explicit stages:

```text
contextcanon source fetch <name-or-id>
contextcanon source review <name-or-id> <candidate-package>
contextcanon source accept <name-or-id> <candidate-package>
contextcanon source adopt <package>
```

They preserve the same rule: candidate discovery does not silently change accepted Context.
