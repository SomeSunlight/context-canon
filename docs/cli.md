# ContextCanon CLI quick reference

This is a navigation page, not a dump of every flag. Use `contextcanon <command> --help` for the exact options of one command.

## Everyday maintenance

| Goal | Command | What it does |
| --- | --- | --- |
| Show installed tool version | `contextcanon --version` | Confirms the installed ContextCanon release. |
| Inspect reusable Sources | `contextcanon source list` | Shows accepted Source versions plus candidate-discovery configuration. |
| Review/update one Source | `contextcanon source update <name-or-id>` | Fetches a candidate, shows the external change, validates local composition, and asks before acceptance. |
| Use one exact candidate ref | `contextcanon source update <name-or-id> --ref <ref>` | Reviews one branch/tag/commit without making that ref durable configuration. |
| Propagate accepted Context | `contextcanon propagate --all` | Reviews Parent relationships top-down and carries accepted Context to dependent Nodes. |
| Render generated Context | `contextcanon build --all .` | Rebuilds every Context Node in the repository. |
| Verify generated state | `contextcanon check --all .` | Reports drift or consistency problems. |
| Inspect central discovery config | `contextcanon config show` | Validates and prints `contextcanon.yaml`. |

The normal loop is **Update → Propagate → Build → Check**. See [Maintain an existing ContextCanon project](maintenance.md).

## Work on one Parent relationship

`Parent` is the semantic higher-level Context accepted by a Child; it is not filesystem nesting. A Child keeps its last accepted Parent snapshot until a newer one is reviewed and accepted.

```text
contextcanon parent review [<parent-node-id>] --node <child>
contextcanon parent accept [<parent-node-id>] --node <child>
contextcanon parent propagate --all
```

The first two commands are useful for one explicit edge. `contextcanon parent propagate --all` remains the explicit Parent-oriented form of the normal user command `contextcanon propagate --all`.

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
