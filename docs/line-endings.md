# Git line endings and platform migration

ContextCanon accepts ordinary UTF-8 project text with LF, CRLF or mixed line endings. Its frozen Evidence and compiled packages nevertheless preserve exact bytes. Normalizing line endings is a content change at that boundary, in either direction.

## Which files may change?

| Surface | Current behavior | EOL migration |
| --- | --- | --- |
| Editable `CONTEXT.src.md` | Text parsing accepts ordinary LF/CRLF/mixed input. Pending update reviews can bind the exact source bytes. | Conversion is allowed; refresh any pending review afterwards. |
| Live project documents, including CSVs | Inventory hashes raw bytes. Topic Resources are copied without EOL normalization. | Convert before inventory/Evidence freeze where possible. After publication, rebuild the owning Node and review dependent updates. |
| Frozen onboarding Evidence | The manifest binds each file's SHA-256 and byte size. References contain its path, hash and line range. | Preserve bytes. A converted live file requires refreshed inventory, a new Evidence basis and dependent onboarding work. |
| Published `CONTEXT.md`, `CONTEXT/`, accepted/retained packages | File hashes, sizes and the exact `package_digest` are verified. Generated-output checks compare bytes. | Preserve copies; use normal publication/update commands to create a new version from changed authoring files. |
| `.context/` and onboarding workspaces/handoffs | Mixed machine state: some JSON/text readers tolerate EOL, while receipts, inputs, results and recovery records can bind exact bytes. | Preserve the whole managed boundary instead of guessing which files are safe. |

There is no byte-offset or public-key-signature requirement in the Evidence reference model. SHA-256 and size verification alone are sufficient to reject an EOL-only edit. Line ranges are computed using `splitlines()`, so pure CRLF/LF conversion normally keeps the same line numbers; the accompanying hash still changes.

`normalized_digest` describes canonical compiled semantics, not EOL-normalized Resource content. It does not exempt files from the independent exact package checks. Framework-rendered package text is UTF-8 with LF; materialized Resources retain their input bytes, including mixed endings and binary assets. This can legitimately put several EOL styles in one package.

## Recommended repository attributes

For LF in editable text and in future checkouts on every platform:

```gitattributes
# Ordinary project text; Git still detects binary files.
* text=auto eol=lf

# Preserve exact ContextCanon package, Evidence and review bytes.
# Keep these AFTER broader text/extension rules.
**/.context/** -text
CONTEXT.md -text
**/CONTEXT/** -text
**/contextcanon-onboarding/** -text
```

The patterns apply at the Git root and below nested Node roots. `CONTEXT.md` is a basename pattern; `**` includes root-level as well as nested directories. `.context/**` protection covers current `.context/versions/`, onboarding runs and legacy Source/Parent stores. Onboarding workspace protection also covers frozen handoffs and compact inventory files whose raw bytes can be recorded. Add equivalent rules for a custom workspace or an exported handoff outside these default paths.

`-text` only disables Git's EOL conversion. The `binary` macro also disables text diff/merge behavior, which is unnecessary here. Do not mark all project CSVs or Markdown as binary merely because they supplied Evidence. The live authoring file and its frozen copy have different lifecycles. Other Git filters/encoding transforms must also leave bound bytes intact.

`core.autocrlf=input` is compatible with this policy. `* text=auto` alone does not explicitly force LF checkout across all contributor configurations; adding `eol=lf` makes that policy repository-owned. Attributes do not change files already present in the working tree, repair previous conversions, or include ignored Evidence in Git. ContextCanon currently manages transient Git ignores, but does not install these EOL attributes automatically.

## Existing Windows project moving to Linux/WSL

1. Preserve a byte-exact backup of the complete original working tree, including ignored `.context/` onboarding data and handoffs. An ordinary clone does not transfer ignored/untracked state. Check the original project with `contextcanon check --all .`; `contextcanon versions list .` also verifies retained history. These checks do not validate every archived onboarding run.
2. Add the preservation attributes **before** staging normalization. Check representative root/nested package and Evidence paths with `git check-attr text eol -- <path>`. Protected paths must report `text: unset`; this disables conversion even if an earlier rule still assigns `eol=lf`. Check nearer `.gitattributes` files and local `.git/info/attributes` if the result differs.
3. Convert only editable project text to LF. Leave `.context/`, generated `CONTEXT.md`/`CONTEXT/` and onboarding workspaces/handoffs byte-exact. Use a text-aware conversion, keeping encodings and binary assets intact. For CSVs, CRLF inside a quoted multiline field is part of the field value too; confirm the consuming application accepts the intended LF values.
4. From the Git root, stage normalization and inspect it:

   ```text
   git add .gitattributes
   git add --renormalize .
   git diff --cached --stat
   git diff --cached --ignore-space-at-eol
   ```

   `git add` converts the **index** representation. It leaves existing working-tree CRLF unchanged. `git ls-files --eol` distinguishes `i/lf` from `w/crlf`; use explicit source conversion or a fresh checkout of the reviewed normalization commit to obtain actual LF working-tree text. Keep the complete backup when moving ignored state into that checkout.
5. In a completed adoption, convert live Resource sources, run `contextcanon build --all .`, review downstream changes with `contextcanon propagate --all .`, then build/check again. External consumers use their ordinary Source-update review. Earlier accepted/history packages remain byte-exact. Conversion can change package identity and advance a Node version even when no words changed.
6. In an unfinished onboarding, regenerate inventory after changing live Evidence, prepare a new snapshot and redo work dependent on that Evidence. Old snapshots remain valid historical inputs if their own bytes were preserved, but final publication checks live files against the reviewed snapshot. Do not edit recorded hashes/sizes or continue a pending review as though the bytes were unchanged.

For a new project, finish source EOL conversion before STEP 02 inventory and STEP 03 Evidence freeze. If the goal is also LF in new package Resources, normalize their authoring files before building. Existing frozen CRLF/mixed history remains in its original format. There is currently no supported command that converts all accepted history to LF while retaining its identity.

## Linux project moving to Windows/CRLF

The same exact-byte boundary applies. The LF policy above works on Windows too and overrides `core.autocrlf=true` for text checkout. Modern editors can work directly with LF files.

When a Windows application requires CRLF, add overrides for specific editable files/directories **before** the preservation rules, for example:

```gitattributes
* text=auto eol=lf
doc/** text=auto eol=crlf
CONTEXT.src.md text eol=crlf

**/.context/** -text
CONTEXT.md -text
**/CONTEXT/** -text
**/contextcanon-onboarding/** -text
```

Git still stores normalized LF text in the index; those editable paths receive CRLF on checkout. Keep compiler-generated adapters such as `AGENTS.md` and `.goosehints`, and the generated `CONTEXT-format.md`, on LF to avoid byte-drift reports. Broader `*.md eol=crlf` rules would also affect generated Markdown; prefer explicit authoring paths. Resource bytes compiled from a CRLF checkout produce a different exact package from those compiled from an LF checkout, so use the ordinary version/review path when publishing.

## Already converted frozen data

Setting `-text` now prevents future EOL conversion; it cannot restore already changed bytes or make an old manifest match them. Prefer the original working tree/backup, a verified retained package, or a byte-preserving archive. Restore the original complete binding, not a newly calculated hash pretending to be the old review.

The legacy Git-history reader used by onboarding migration can recover an LF-stored package artifact as CRLF only when the reconstructed bytes match **both** the recorded complete SHA-256 and size. This narrowly verified recovery is not general EOL tolerance, does not apply to arbitrary Evidence snapshots, and cannot be assumed to reconstruct mixed endings. Normal package loading remains strict.

[Issue #112](https://github.com/SomeSunlight/context-canon/issues/112) tracks the broader package publication/transport policy. This guide documents the current contract and an operator-controlled preservation policy; it does not claim automatic conversion or repair support.

## Implementation and verification

The relevant boundaries are [Evidence capture](../src/contextcanon/onboarding.py), [snapshot/reference validation](../src/contextcanon/onboarding_proposal.py), [live Evidence acceptance](../src/contextcanon/onboarding_review.py), [immutable packages](../src/contextcanon/package.py), [Resource materialization](../src/contextcanon/compiler.py), [generated-output comparison](../src/contextcanon/outputs.py) and [legacy Git-history recovery](../src/contextcanon/onboarding_reusable_contexts.py).

Temporary Linux/Git experiments verify LF/CRLF/mixed Evidence preservation and EOL-only rejection, unchanged source parsing semantics, exact Resource package identities and generated-output drift. The attribute examples preserve root/nested frozen LF/CRLF/mixed/binary content across 18 commit/checkout combinations using `core.autocrlf=false`, `input` and `true`, including explicit Windows CRLF authoring overrides. A further 54 complete-package loads verify published nested carriers and retained versions after Git round trips, including binary Resource closures. This is portable Git-policy evidence, not a new native-Windows end-to-end migration claim.

Git's own [attributes](https://git-scm.com/docs/gitattributes) and [configuration](https://git-scm.com/docs/git-config) documentation define normalization, checkout styles and attribute precedence.
