# ContextCanon CLI quick reference

This is a navigation page, not a dump of every flag. Use `contextcanon <command> --help` for the exact options of one command.

## Everyday maintenance

| Goal | Command | What it does |
| --- | --- | --- |
| Show installed tool version | `contextcanon --version` | Confirms the installed ContextCanon release. |
| Inspect reusable imports | `contextcanon source list` | Shows each immutable import carrier with its semantic Parent/Reference relationship, accepted version, and candidate-discovery configuration. |
| Review/update one import | `contextcanon source update <name-or-id>` | Reviews a newer package. Parent updates preview normative local impact and may need downstream propagation; Reference updates remain informational and local. |
| Use one exact candidate ref | `contextcanon source update <name-or-id> --ref <ref>` | Reviews one branch/tag/commit without making that ref durable configuration. The `source` command name is a compatibility package/discovery surface, not a third relationship kind. |
| Review downstream impact | `contextcanon propagate` | Reviews changed Parent → Child relationships top-down from the current Node and asks before each acceptance. |
| Inspect propagation status | `contextcanon propagate --status --all .` | Read-only check for local Parent/Child edges whose accepted normative Parent snapshot is behind the current local Parent. Returns exit code 1 when propagation is pending. |
| Review every Parent graph | `contextcanon propagate --all` | Broadens the review scope to all semantic Parent edges in the repository; it does not imply blanket acceptance. |
| Normalize legacy import authoring | `contextcanon source normalize --all .` | Makes historical implicit Source → Parent semantics explicit; ordinary build/check do not rewrite authored relationship semantics. |
| Render generated Context | `contextcanon build --all .` | Rebuilds every Context Node in the repository. |
| Verify repository health | `contextcanon check --all .` | Reports generated drift, version/consistency problems, and pending local normative Parent propagation. A clean result means every discovered Node is internally consistent and every local Parent/Child edge is normatively current. |
| Inspect central discovery config | `contextcanon config show` | Validates and prints `contextcanon.yaml`. |

The normal loop is **Update → review Parent propagation when needed → Build → Check**. A Reference update has no propagation phase. `check --all` is the final repository health gate; use `propagate --status --all .` when you want the dependency/propagation part alone without changing anything. See [Maintain an existing ContextCanon project](maintenance.md) for the short propagation checklist.

> [!IMPORTANT]
> `--all` means **all Parent edges are in review scope**. Interactive propagation still asks at every changed edge. `--yes` suppresses those confirmations and is intended for controlled automation, not as the default human workflow.

## Work on one Parent relationship

`Parent` is the semantic higher-level Context accepted by a Child; it is not filesystem nesting. A Child keeps its last accepted Parent snapshot until a newer one is reviewed and accepted.

```text
contextcanon parent review [<parent-node-id>] --node <child>
contextcanon parent accept [<parent-node-id>] --node <child>
contextcanon parent propagate [path] [--all] [--status]
```

The first two commands are useful for one explicit edge. `contextcanon parent propagate` remains the explicit Parent-oriented form of the normal user command `contextcanon propagate`.

Before accepting a Parent update, check three things: **does it still apply here, does it coexist with the Child's other imported Contexts, and is the upstream change itself correct and complete from this Child's viewpoint?** If not, fix upstream or make an explicit justified local resolution rather than relying on import order.

## Browse and migrate Node versions

| Task | Command | Behavior |
| --- | --- | --- |
| Browse retained versions | `contextcanon versions list .` | Lists complete shared Node packages and current consumers; also browse `.context/versions/README.md`. |
| Preview legacy relocation | `contextcanon versions migrate .` | Read-only plan for consumer-local accepted packages; exact pins and package bytes are preserved. |
| Apply that migration | `contextcanon versions migrate . --apply` | Verifies shared copies before narrow old-wrapper retirement; retry resumes interrupted cleanup. |

See [Node versions and migration](node-versions.md). Run migration from the Git root, then `build --all` / `check --all`; use the normal reviewed update/propagation workflow for newly published shorter Resource layouts. Onboarding storage migration and automatic history pruning remain later work.

## Maintain Topic Resources

Direct Topic Resources have stable identities independent of their current repository paths. The Resource commands are deliberately grouped as one Git-like maintenance surface:

| Goal | Command | What it does |
| --- | --- | --- |
| List Resources | `contextcanon resource list` | Shows a labeled Markdown table: Resource ID, Context Node using the Resource, Resource path, and explicit Topic dependency with Topic ID, title, and required/optional intent. |
| Inspect changes | `contextcanon resource status` | Git-like view of Resource deviations from the last built package: modifications, missing paths, moves, and exact-hash rename candidates. Clean Resources are hidden by default; add `--all` to show them. |
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

`status` starts conservatively with exact SHA-256 matches. A unique byte-identical candidate is shown as an unconfirmed rename; multiple identical candidates remain visibly ambiguous. Interactive `reconcile` presents those exact candidates as a numbered human choice, while `--yes` deliberately skips ambiguity rather than guessing. `reconcile` never transfers identity merely because hashes match: the human confirms semantic continuity. For Markdown Resources, ContextCanon also compares the resolved relative-link closure and refuses a simple move when the same bytes would now pull in different local dependencies.

For an older ContextCanon project that still has path-only Resources, migrate once:

```text
contextcanon resource register
contextcanon build --all .
contextcanon check --all .
```

Moves also report project-authored Markdown links that still resolve to the old path. ContextCanon never rewrites that prose automatically; the operator reviews those links separately.

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

## Lower-level import-carrier commands

Phase 1 keeps the historical `source` command group as the compatibility maintenance surface for immutable reusable package carriers. Each carrier is semantically either **Parent** or **Reference**; `Source` is not a third relationship type. The guided `source update` command is the normal human path. Separate commands remain available when automation or debugging needs explicit stages:

```text
contextcanon source fetch <name-or-id>
contextcanon source review <name-or-id> <candidate-package>
contextcanon source accept <name-or-id> <candidate-package>
contextcanon source adopt <package>
```

They preserve the same rule: candidate discovery does not silently change accepted Context. Parent candidates are validated against normative composition; Reference candidates never inject their Rules or create downstream propagation.
