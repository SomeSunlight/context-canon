# Windows paths and local review scratch

ContextCanon preserves project files and exact Resource links. Normal authoring retains complete immutable Node versions once in a shared Git-root library and scopes review scratch there by consumer. It shortens its own package paths and checks the full absolute destination before package copies or generated output writes on Windows.

## Compatibility preflight

Preflight counts UTF-16 units in the entire absolute path, excluding the terminating NUL. Its default policy is:

| Destination length | Behavior |
| --- | --- |
| Below 240 | Proceed without a path-budget diagnostic |
| 240–259 | Warn and proceed |
| 260 or more | Stop before mutation, unless explicitly opted in to long paths |

The 240-unit target leaves interoperability headroom below traditional Win32 file/directory limits; it is not a proven filesystem failure. Real owner testing found that rejecting an existing 251-unit accepted package prevented propagation before the project could benefit from shorter candidate scratch. The warning band allows that transition without requiring a reinitialization or a blanket long-path opt-in. Directory APIs and downstream applications can still fail within this band. Non-Windows runs do not apply this policy.

Preflight covers Source/Reference and Parent candidates, temporary Git checkouts before files are checked out, accepted immutable imports, generated Official Context outputs, and onboarding Evidence, frozen reusable packages, semantic handoffs and publication. Final destinations are checked as well as staging paths: a short temporary path cannot conceal a longer accepted destination. Output preflight runs before stale generated files are removed.

A warning or error reports the action/store, the longest absolute destination and its length, the project/Node root contribution and the ContextCanon-owned store/package prefixes. A top-level `CONTEXT.md` can remain readable while a deep `CONTEXT/references/<uuid>/nodes/.../docs/...md` target exceeds the budget. Git staging, an IDE link and a file API can fail at different layers; partial success elsewhere does not prove a path is safe. Do not rename project documents blindly when internal package structure consumes the budget.

Move the **whole checkout** nearer the drive root, for example from `C:\Users\Owner\PycharmProjects\Project` to `C:\Projektverzeichnis`, then use the new location for commands and IDE links. This shortens every descendant without changing project-relative imports or Resource paths. The diagnostic calculates the shortening needed for its longest destination to fall below 240; for a 251-unit path, 12 units are sufficient and a 13-unit reduction yields 238. Check the other destinations too: relocating one project does not guarantee that every package in every project fits.

For a Git-related failure, Git for Windows supports:

```powershell
git config core.longpaths true
```

Use `git config --global core.longpaths true` deliberately if it should apply to future repositories too. Enable Windows long-path support where organizational policy permits. Each downstream application must also support long paths; neither setting makes every editor, renderer or file API compatible.

After verifying your actual toolchain, explicitly allow these paths in the current PowerShell session:

```powershell
$env:CONTEXTCANON_ALLOW_LONG_PATHS = "1"
```

ContextCanon then also treats destinations at or above 260 as warnings and proceeds. Its disposable Git candidate checkout also opts into `core.longpaths=true` for that checkout operation. The setting does not change project Git configuration or enable OS policy. Remove the session opt-in to restore the default warning/error thresholds:

```powershell
Remove-Item Env:CONTEXTCANON_ALLOW_LONG_PATHS
```

See Microsoft's [maximum path length documentation](https://learn.microsoft.com/en-us/windows/win32/fileio/maximum-file-path-limitation) for OS/application requirements and the Git for Windows [core configuration documentation](https://github.com/git-for-windows/git/blob/main/Documentation/config/core.adoc) for `core.longpaths`.

## Candidate identity and lifetime

Candidates separate review from acceptance: freeze exact possible update bytes, review those bytes against the current consumer, and accept precisely that reviewed package without re-reading a moving provider. A normal build never uses candidate state.

The two normal-authoring package scratch stores are Git-root-local and consumer-scoped:

```text
.context/candidates/<consumer-token>/<package-token>/
.context/parent-candidates/<consumer-token>/<package-token>/
```

Package tokens normally use 16 hex characters, bind full Node identity plus normalized/exact digests, and extend on a verified prefix collision. Scope metadata verifies the full consumer Node identity and worktree-relative location; reviews cannot cross consumers. Malformed or changed stored content fails rather than being reused. Legacy Node-local candidates and review receipts remain readable.

Source provenance uses a compact Source/candidate token with `.git.json`; source and parent receipts use compact tokens in corresponding Git-root consumer scopes. All four stores are ignored scratch. Successful acceptance removes only its consumed candidate/provenance/receipt after shared immutable installation and atomic pin publication. Other consumers, unrelated transactions, external candidate directories and accepted history survive. Failed acceptance retains scratch; a cleanup lock warns and preserves the remaining receipt for diagnosis.

Accepted packages now live in `<git-root>/.context/versions/<token>/`, independent of Child nesting. Commit this library for offline use. Normal builds also retain previous/current local publications there. New Resource namespaces normally use at most 16 characters and Node-relative document directories; full origins remain authenticated metadata. Cross-Node Resource links preserve their actual required directory layout.

## Existing projects and onboarding reset

Use the read-only `contextcanon versions migrate .` preview from the Git root, then `--apply` to relocate verified legacy accepted stores. This explicit migration preserves exact packages and pins, deduplicates shared versions and resumes interrupted narrow cleanup. Rebuilding alone does not remove old directories. New shorter Resource layouts require providers to republish and consumers to accept the update normally. See [Node versions and migration](node-versions.md).

For an existing project, `contextcanon build --all .` regenerates Official Context and machine outputs from canonical authoring, Resources and accepted inputs. Do not delete the shared version library or unmigrated `.context/sources/`: a provider may have changed or disappeared. Preserve inventory/Evidence and reset state still needed by onboarding. Git recovers committed files only, not ignored/untracked state.

`contextcanon onboard reset . --from N` rolls back journaled onboarding mutations, including authoring files where applicable; it is not a derived-output rebuild. Phase 1 does not migrate onboarding Evidence, frozen packages or journals. Generic reinitialization and optional identity remapping remain [Issue #106](https://github.com/SomeSunlight/context-canon/issues/106).

## Git visibility and repair for existing repositories

Onboarding initialization and candidate fetch/review maintain a marked repository `.gitignore` block with explicit rules:

```gitignore
**/.context/candidates/
**/.context/parent-candidates/
**/.context/source-reviews/
**/.context/parent-reviews/
**/.context/migration-trash/
```

That block remains useful after onboarding reset. Existing repositories automatically receive it on the next fetch/review; it may also be repaired manually by adding those five rules. Do not ignore `.context/versions/` or legacy `.context/sources/`.

For an emergency local-only repair without modifying tracked `.gitignore`:

```powershell
Add-Content .git/info/exclude "`n**/.context/candidates/`n**/.context/parent-candidates/`n**/.context/source-reviews/`n**/.context/parent-reviews/"
```

Onboarding's separate managed block uses recursive rules, including at nested and simultaneous local onboarding roots:

```gitignore
# >>> ContextCanon onboarding (managed)
**/contextcanon-onboarding/
**/.context/onboarding/*
!**/.context/onboarding/inventory-state.json
!**/.context/onboarding/inventory-acceptance.json
# <<< ContextCanon onboarding (managed)
```

Refreshing the block migrates the historical root-anchored form in place, idempotently. An explicitly chosen custom workspace inside the selected project keeps its own anchored ignore rule as well. The two compact inventory files stay trackable at every onboarding root; transient snapshots and workspaces remain ignored. Remove a manually authored broad `**/.context/onboarding/` rule if present: Git cannot re-include files below an ignored parent directory with these negations. Tracked historical scratch is unaffected by new ignores; use a deliberate `git rm --cached` on only the scratch paths if they were previously committed.
