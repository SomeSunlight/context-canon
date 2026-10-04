# Windows paths and local review scratch

ContextCanon preserves project and Resource paths. It reduces its own transient package paths and checks the full absolute destination before package copies or generated output writes on Windows.

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

The two package scratch stores are Node-local:

```text
.context/candidates/<digest-prefix>/
.context/parent-candidates/<digest-prefix>/
```

The directory token normally uses 16 hex characters, saving 48 characters compared with the historical full-digest directory. If a verified different package occupies that prefix, ContextCanon extends the token by eight characters until it finds a free path. Every reuse and acceptance verifies the **full** manifest/package digest; the short name never becomes identity. Existing full-digest candidate paths and review receipts remain readable.

Source candidate provenance remains a sibling `<full-package-digest>.git.json`; receipts live in `.context/source-reviews/` and `.context/parent-reviews/`. All four directories are local review scratch, rather than accepted governance records. Successful acceptance removes only its consumed candidate package, its matching provenance sidecar when present, and its matching receipt, after immutable installation and atomic pin publication succeed. Unrelated transactions remain intact. Explicitly supplied external package directories are never deleted. A failed acceptance retains candidate/receipt state for diagnosis or retry. If cleanup itself encounters a filesystem lock after successful acceptance, the command reports a warning and keeps the remaining scratch for manual cleanup.

Accepted `.context/sources/<full-package-digest>/` packages and exact pins remain durable, versionable offline state. Candidate cleanup never removes them, including previously accepted versions. Once an abandoned review is no longer needed, its scratch can be removed manually; ContextCanon does not add a broad cleanup command.

## Rebuild versus onboarding reset

The full digest in an **accepted** package path is still canonical, rather than a historical candidate token. Rebuilding or reinitializing the project would produce that same destination; new Node UUIDs would also have the same length. Short candidate tokens solve transient review depth, not accepted package depth. Shorter durable `sources` and packaged `references` locators, retaining full authoritative identities and supporting migration, are tracked separately in [Issue #107](https://github.com/SomeSunlight/context-canon/issues/107).

For an existing project, `contextcanon build --all .` regenerates derived Official Context and machine outputs from retained canonical authoring files, authored Resources and exact accepted imports. Keep `.context/sources/`: a live/remote provider may have changed or disappeared, so `CONTEXT.src.md` alone cannot always recover the pinned package bytes. Preserve any accepted inventory/Evidence and recovery state still needed by an unfinished onboarding. Git history recovers committed files only, not ignored/untracked state.

`contextcanon onboard reset . --from N` instead rolls back journaled onboarding mutations, including published authoring files where applicable. It is not a generic derived-output rebuild. General project reinitialization and optional identity remapping for independent project copies are tracked separately in [Issue #106](https://github.com/SomeSunlight/context-canon/issues/106); no such command is implemented here.

## Git visibility and repair for existing repositories

Onboarding initialization and candidate fetch/review maintain a marked repository `.gitignore` block with explicit rules:

```gitignore
**/.context/candidates/
**/.context/parent-candidates/
**/.context/source-reviews/
**/.context/parent-reviews/
```

That block remains useful after onboarding reset. Existing repositories automatically receive it on the next fetch/review; it may also be repaired manually by adding those four rules. Do not ignore `.context/sources/`.

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
