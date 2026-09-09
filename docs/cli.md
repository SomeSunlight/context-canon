# ContextCanon CLI quick reference

This is a navigation page, not a dump of every flag. Use `contextcanon <command> --help` for the exact options of one command.

## Everyday maintenance

| Goal | Command | What it does |
| --- | --- | --- |
| Show installed tool version | `contextcanon --version` | Confirms the installed ContextCanon release. |
| Inspect reusable Sources | `contextcanon source list` | Shows accepted Source versions plus candidate-discovery configuration. |
| Review/update one Source | `contextcanon source update <name-or-id>` | Fetches a candidate, shows the external change and local effect, validates composition, and asks before acceptance. |
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

```text
contextcanon onboard ...
```

Onboarding has its own reviewed multi-step workflow. Start with [Onboard an existing project](onboarding.md) rather than reconstructing it from CLI help.

## Lower-level Source commands

The guided `source update` command is the normal human path. Separate commands remain available when automation or debugging needs explicit stages:

```text
contextcanon source fetch <name-or-id>
contextcanon source review <name-or-id> <candidate-package>
contextcanon source accept <name-or-id> <candidate-package>
contextcanon source adopt <package>
```

They preserve the same rule: candidate discovery does not silently change accepted Context.
