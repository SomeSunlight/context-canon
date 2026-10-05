# Internal-project Owner Test — PR #108 Phase 1

Implementation under review: [PR #108](https://github.com/SomeSunlight/context-canon/pull/108), branch `agent/issue-107-shared-node-versions`. Product head `448d2c1488adf584130760a8c9db50b3a888a3ed` passed 394 deterministic tests and Actions run [37251101173](https://github.com/SomeSunlight/context-canon/actions/runs/37251101173), including 23 native Windows tests. Later #109 documentation commits do not change executable behavior.

This test targets an already-onboarded internal project. It covers normal operation and package relocation. Onboarding Evidence, frozen Catalogs, workspaces and reset journals are still Phase 2. Use a published project with no unfinished onboarding transaction; do not combine this pilot with an onboarding reset.

## 1. Keep a complete return point

Start with one representative product and its Children, then migrate each remaining Git repository separately. The storage boundary is the Git working-tree root, not each Context Node. If `my_company`, `P1` and feature folders share one Git repository, run migration once at that repository root.

For the first pilot, make a complete filesystem copy of the internal repository in File Explorer, including hidden `.git` and `.context` directories and any ignored/untracked inputs. Keep one untouched return copy and test in the other. A Git worktree or fresh clone alone does not copy ignored/untracked accepted state or onboarding material. Keep the pilot copy at a similar path depth so the Windows check remains representative.

Finish or record unrelated authoring first. Existing Git commits provide a useful additional checkpoint, but they cover only committed files. Do not push confidential project data anywhere for this test.

## 2. Confirm the existing editable tool points to this PR

Your existing editable installation is sufficient: checking out/updating the ContextCanon review branch changes the executable immediately. Installation is not a required test step.

```powershell
contextcanon --version
```

Expect release `0.10.0` with the review branch and its current commit. Commit identity is authoritative. If it still reports `main@28ce62e`, the editable checkout has not moved to PR #108 yet.

In the internal project, confirm the actual repository root:

```powershell
git rev-parse --show-toplevel
git status --short
```

Run the following repository-wide commands there. For one Node's imports, use its real Node path:

```powershell
contextcanon source list --node P1
```

Record the relationships and accepted versions in the IDE/Git diff. Replace `P1` with the relevant root if yours differs.

## 3. Test relocation before rebuilding or updating imports

```powershell
contextcanon versions migrate .
```

This is read-only. Inspect old/new locations, longest paths and any retained directories containing extra files. The preview includes current publications that will be retained as history; their local generated files stay in place.

Then apply exactly that relocation:

```powershell
contextcanon versions migrate . --apply
contextcanon versions list .
contextcanon versions migrate .
```

Before running `build`, inspect:

- Shared packages are under the single root `.context/versions/<token>/`.
- The same complete Node ID + normalized digest + package digest used by several Children has one directory; several versions of one Node may legitimately have several directories.
- Import IDs, accepted versions, both digests and Parent/Reference kinds are unchanged. An import URL pointing into its own retired wrapper may change mechanically; real provider/discovery URLs stay unchanged.
- Open `.context/versions/README.md`, follow a few package links and inspect a deep Child's accepted Parent and any Reference.
- The second preview no longer proposes retiring the already-migrated owned wrappers. It may still list current publications and intentionally retained wrappers containing extra files; empty output is not the criterion.
- Additional project files in legacy wrappers survive. No migration recovery transaction should remain after successful completion.

Migration does not fetch providers. It works with unavailable external providers if the accepted packages are present. Do not delete live internal Parent Nodes to simulate offline use.

**Return point A:** inspect and commit this relocation separately from later updates. Include the new shared versions and authored locator changes. Confirm `.context/versions/` is trackable; a pre-existing broad project ignore for `.context/` must not hide this durable library. Candidates, review receipts and migration recovery files remain scratch. Do not force-add an entire ignored `.context/` tree.

## 4. Rebuild and resolve only actual pending Parent changes

```powershell
contextcanon build --all .
contextcanon propagate --status --all .
```

The new compiler can publish a shorter current Resource layout and automatically advance a local Node's version. Old retained packages keep their exact bytes and internal paths. A pending local normative Parent update gives status exit code 1; this is a review request, not an automatic migration failure.

If status reports pending changes:

```powershell
contextcanon propagate --all .
```

Review each displayed Parent → Child change. Avoid `--yes` for the pilot. A storage-format transition may change package identity and versions; verify that effective Rules, local Overrides/Removes and the intended relationship meaning remain correct.

Then finish:

```powershell
contextcanon build --all .
contextcanon check --all .
contextcanon versions list .
```

Expect no generated drift and no pending local normative Parent updates. Inspect one root, product and deepest feature in the IDE: effective Rules should still be the intended ones, all Required Topic links should open, and linked Markdown documents/assets should resolve.

**Return point B:** commit the verified rebuild/propagation separately. A second `build --all` followed by `check --all` should be stable.

## 5. Test a provider update as a separate change

Moving an old accepted wrapper cannot shorten the paths inside that immutable package. For those savings, the provider must publish with the new compiler and the consumer must review/accept that new version.

For imports published by ContextCanon, use the PR ref explicitly while it remains unmerged:

```powershell
contextcanon source update "Development Workflow" --node P1 --ref agent/issue-107-shared-node-versions
```

Use the actual import name and consumer path. The one-off `--ref` does not change default discovery configuration.

If several imports share a transitive Parent (for example Development Workflow plus GitHub Local), inspect their candidate dependency versions together. Do not accept a mixed composition merely to get a shorter path. A conflict is a reason to stop this update block and align the common dependency through ordinary review; preserve return point B. Coordinated-update guidance is a separate open issue, #88.

After accepting a Parent update, run the ordinary reviewed propagation/build/check loop. A Reference update stays informational and does not send its Rules or relationship to Children. Test that boundary on an existing Reference, or in the pilot copy if you need a deliberate Reference scenario; do not add a production relationship solely for this test.

For offline verification, run normal `build`/`check` while external providers are unavailable or with network disconnected in the pilot. These commands must consume the accepted local packages without fetching.

**Return point C:** keep the provider update separate from the relocation and compiler rebuild.

## Interruption and rollback

If `--apply` is interrupted, rerun:

```powershell
contextcanon versions migrate . --apply
```

The command verifies and resumes owned recovery transactions. Do not manually delete `.context/migration-trash/`. If it refuses changed or unowned bytes, retain the error and those files; do not bypass integrity checks.

For a full rollback of the pilot, stop writes, return to the untouched full repository copy and switch the editable ContextCanon checkout back to the accepted `main` revision. Git switching/resetting alone leaves new untracked shared versions behind and does not restore ignored data. Restoring the complete copy avoids a mixed old/new storage state.

Do not manually prune old versions. “Retained history” in the index is not proof that pending reviews, old retained package dependencies or onboarding/reset recovery no longer need them.

## Owner acceptance record

Report:

1. The exact `contextcanon --version` output and actual Git root.
2. Whether preview/apply completed, old owned wrappers disappeared and any extra-file wrappers were intentionally retained.
3. Whether the shared history index and deep Node/Topic links work in the original Windows tools.
4. Whether final `check --all` and propagation status are clean, and whether a second build is stable.
5. Any provider-update or offline failure separately from pure relocation.

The project can stay confidential; command output and a small redacted path/error example are enough for diagnosis. On 2026-10-05 the owner reported successful migration/history browsing, successfully resumed propagation after the #110 Resource-move correction, and accepted Phase 1 for a squash merge. This sequence remains a reusable operator guide. Exact-current-head merge verification is recorded on PR #108; onboarding migration is the next phase after merge, and pruning remains deferred.
