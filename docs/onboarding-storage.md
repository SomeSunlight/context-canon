# Onboarding storage (Phase 2 implementation contract)

This branch is stacked on the owner-tested, unmerged Phase-1 branch. Do not merge it or apply it to the confidential internal project before the owner-test instructions and explicit active-run migration are complete.

## Identities and ownership

New runs use `<Git root>/.context/onboarding/<project token>/<Evidence token>/`. Project tokens hash the canonical repository-relative project path; run tokens shorten the existing full Evidence digest. Both normally use 16 hexadecimal characters and extend on a verified collision. `.scope.json` authenticates the complete project path; `.run.json` authenticates that project and the full Evidence digest against the frozen manifest. Directory names are locators, never identity. A resolver rejects mismatched markers, unsafe paths and symlinks instead of deriving the project from the new directory depth.

The v0 Evidence manifest and its file bytes remain unchanged. Identical project-relative Evidence can exist in two separate project scopes: each keeps its own immutable copy, review decisions, proposals, journal and provenance. This intentionally avoids introducing symlink/hardlink or cross-scope mutable-state ownership into Evidence recovery. Deduplication of complete reusable Node packages supplies the major storage/path reduction.

New subtree workspaces default to `<Git root>/contextcanon-onboarding-<project token>/`; a root project's familiar `contextcanon-onboarding/` remains. Existing local workspaces and explicit `--workspace` locations remain usable. Existing project-local runs stay readable pending explicit migration. Authored files and Evidence-relative paths remain at the selected project scope.

## Frozen whole-Node packages

STEP 07 freezes exact reusable packages into the Phase-1 `.context/versions/<complete-binding token>/` library. The key includes Node ID, normalized digest and exact package digest; equal human file bytes from two different Nodes cannot alias. Published imports still carry the full bindings and the selected Parent/Reference relationship. A Reference stays informational and does not propagate to semantic Children.

Provenance is a run-owned `catalog-provenance/<full binding key>.json` sidecar. It includes the complete binding and the original Git/local discovery information. A shared immutable package is never modified to add one run's provenance. The existing accepted review digest continues to cover the original Catalog paths and bindings; physical frozen locators are outside that semantic digest. Old local frozen packages and exact historical recovery remain supported, with full-binding verification.

The enclosing Parent is frozen once per run into the same library, with its exact binding and authoring locator in `enclosing-parent.json`. Later handoffs, STEP 07, preview and publication use those frozen bytes, even when the live Parent changes or disappears. Portable handoff inputs retain their existing schemas, deterministic bytes and project-relative Evidence layout.

## Publication, reset and Git visibility

Preview and publication use the normal compact compiler and the same shared packages. Reset restores canonical/generated files, reviewed source transformations and the run's acceptance record. Nested runs address their owned acceptance record with a restricted `@run/placement-acceptance.json` journal locator; arbitrary external paths are not claimed. Old project-relative v1 journals remain readable.

A reset verifies a whole journal record before changing it, atomically marks reversal in progress, then atomically persists each reversed record. Retry accepts only the recorded after bytes or the exact before bytes of an in-progress reversal. Other edits remain refusal conditions. Journal paths cannot escape the project or the one owned run acceptance file.

Rollback/reset retain the immutable shared library. Deleting a package merely because this run first installed it could break another run or accepted consumer; automatic reachability-based pruning remains deferred. The prior canonical pins, generated outputs and acceptance state are restored. Unknown scope files cause a conservative refusal, and a legacy root-level run never owns neighboring central project scopes.

Repository-wide ignore rules keep run payloads and generated workspaces out of normal staging, while `.scope.json`, inventory state and inventory acceptance remain Git-visible. The shared rule block survives individual project resets, so resetting one project cannot expose another project's transient files.

## Checkpoint and remaining scope

The runtime/storage checkpoint covers new phased onboarding and legacy readers. Separate preview/apply migration of existing active runs, legacy single-pass acceptance staging, owner migration instructions and final hosted Linux/Windows verification are the next blocks. No migration is implied by ordinary reads, and no shared-version or abandoned-candidate cleanup is authorized by this change.
