# Node versions and migration

Each Git working tree has one shared library of complete immutable Node versions. A product and its nested Children use that same library, including imports from another repository. The provider's own checkout has a separate library. Filesystem nesting does not change a Node's identity or its Parent/Reference relationships.

| Location | Purpose |
| --- | --- |
| `<node>/CONTEXT.src.md` and authored documents | Editable current authoring |
| `<node>/CONTEXT.md`, `CONTEXT/`, `.context/package.json` | Current published Node package |
| `<git-root>/.context/versions/<token>/` | One retained complete package per exact Node version |
| `<git-root>/.context/versions/README.md` | Generated browsing index: versions, current consumers and retained history |
| `<node>/CONTEXT.src.md` import pins | The exact version accepted by that particular consumer |

A normal `build` retains both the previous verified publication and the new publication in the library. Installing an import reuses its exact version if already present. Updating a provider still requires separately reviewed consumer acceptance: sharing storage never updates a Child's pin. References remain informational and do not propagate.

```text
contextcanon versions list .
```

Open `.context/versions/README.md` to browse history. Directory tokens normally have 16 hexadecimal characters. They locate a binding of full Node ID, normalized digest and exact package digest, verified against `.context/package.json`. A verified prefix collision extends the token; malformed or changed existing content is rejected. Different Nodes can have identical human package bytes, so the byte digest alone is insufficient identity. No editable allocation ledger is needed, and `context.yaml` remains regenerable bookkeeping.

## Shorter Resource paths

New packages materialize Resource documents below `CONTEXT/references/<origin-token>/`, normally preserving directories relative to their authoring Node. This avoids repeating a Node's complete repository location in every package. Full Node IDs and original repository paths are bound in `.context/resource-origins.json`, verified package content rather than a disposable lookup cache.

Exact authored Markdown and relative links remain unchanged. When a Resource closure links outside its Node, the common base widens enough to preserve those links. ContextCanon does not flatten documents or impose a Node nesting limit; absolute Windows limits and unusually deep project-owned document paths still apply. Sharing a root library removes consumer nesting from accepted version and normal review storage.

## Migrate an existing project

Install the review branch (until released), then run these commands from the consuming project's Git root:

```text
contextcanon versions migrate .
contextcanon versions migrate . --apply
contextcanon build --all .
contextcanon check --all .
```

The first command is a read-only preview. Review its exact old/new locations and path lengths. `--apply` verifies every old accepted package, installs and verifies all shared copies, and only then retires narrowly owned `.context/sources/<full-digest>/` wrappers. Duplicate versions become one shared copy. If an old wrapper contains extra project files, it is kept and reported. No provider access is required.

Stable IDs, versions, both digests and Parent/Reference kinds remain unchanged. Real provider/discovery URLs remain unchanged too. An import URL pointing directly into its own old accepted wrapper is moved to the shared carrier; matching valid pending review receipts are mechanically rebound to that source edit, while stale reviews remain stale. The preview reports these edits. Ordinary prose and project documents are never rewritten.

The transition code is isolated in `storage_migration.py`; runtime readers do not depend on it. Interrupted retirement or link/review publication leaves a narrow recovery receipt under `.context/migration-trash/`. Rerun the same `--apply` command to verify remaining bytes and resume. Changed or unowned recovery files are refused. Commit the resulting shared library, authoring changes and generated output with Git; review scratch and migration recovery scratch are ignored.

Migration relocates **exact existing packages**. It does not rewrite their internal Resource layout or recover versions that were never retained. New shorter Resource layouts arrive when providers rebuild with this compiler and consumers accept those newly published versions through the normal update/propagation review. After local provider builds, use `contextcanon propagate --all .` to review pending normative updates, then build/check again. Remote imports use `contextcanon source update`.

## Retention and onboarding boundary

Old versions should eventually be removable when nothing still needs them. This phase deliberately has no automatic pruning command: current pins, pending reviews and onboarding/recovery history must all be accounted for first. An index row marked "retained history" only means no current direct pin/publication was found; it is not permission to delete that package. Git can recover committed versions, not ignored or untracked data.

Phase 1 covers normal authoring, publication history and Parent/Reference maintenance. Onboarding Evidence, frozen reusable Catalogs, workspaces and reset journals keep their existing storage and transaction behavior until Phase 2. This migration does not reinitialize a project or change Node IDs. Generic reinitialization remains separate Issue #106.
