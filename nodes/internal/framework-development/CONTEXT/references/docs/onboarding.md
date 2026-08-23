# Reviewed Project Onboarding

ContextCanon onboarding is a semantic workflow above the deterministic compiler. Its purpose is to turn an existing repository into a reviewable ContextCanon proposal without letting an LLM directly invent or publish canonical project context.

The workflow begins with a deterministic evidence boundary:

```text
existing Git repository
        ↓
contextcanon onboard prepare
        ↓
content-addressed evidence snapshot
        ↓
framework-supplied LLM classification instruction
        ↓
provenance-rich proposal
        ↓
human review and correction
        ↓
explicit acceptance
        ↓
CONTEXT.src.md + Sources + Topics + Resources
        ↓
normal deterministic compiler
```

Only the first boundary is implemented in the initial onboarding slice. No LLM participates in `onboard prepare`.

## Why preparation is a separate deterministic step

An LLM must not reason over an undefined moving target such as "whatever files happen to be in the repository when the request is executed".

`onboard prepare` freezes the exact project evidence offered to the later semantic step. Every included file is bound by repository-relative path, byte size, SHA-256 hash, selection reason, and exact copied bytes.

This gives later review a stable question:

> Which exact repository evidence supported this proposed Rule, Topic, Source choice, or unresolved question?

If a selected source document changes later, a new evidence digest and a new snapshot are produced. The earlier snapshot remains independently reviewable.

## Command

From a Git repository root:

```text
contextcanon onboard prepare .
```

Additional safe UTF-8 files may be added explicitly:

```text
contextcanon onboard prepare . --include src/project_policy.py --include config/example.ini
```

`prepare` deliberately does not require `CONTEXT.src.md`. It is meant for repositories that have not yet adopted ContextCanon.

## Repository inventory boundary

Automatic inventory uses Git's own repository visibility rules:

```text
git ls-files --cached --others --exclude-standard
```

That means tracked files and non-ignored untracked files are visible to the default selector. Git-ignored files are not silently offered to the onboarding model.

An explicit `--include` can add an otherwise ignored safe file. Explicit inclusion is still subject to path, secret, size, symlink, and UTF-8 safety checks.

Git is used here as a deterministic inventory boundary. Git state is not interpreted as project meaning.

## Conservative automatic evidence selection

The default policy intentionally prefers likely high-value context carriers rather than copying the repository wholesale.

Current automatic categories are:

- root project documents such as README, CONTRIBUTING, CHANGELOG, ARCHITECTURE, DESIGN, DEVELOPMENT, SECURITY, and SUPPORT documents;
- UTF-8 text documentation below `docs/`, `doc/`, or `documentation/` directories;
- common harness instructions such as `AGENTS.md`, `CLAUDE.md`, `.goosehints`, GitHub Copilot instructions, and `.github/instructions/` Markdown;
- selected root project/build manifests such as `pyproject.toml`, `package.json`, `Cargo.toml`, `go.mod`, Gradle/Maven files, common test/lint configuration, Docker/Compose files, and requirements files;
- GitHub Actions workflow YAML.

Ordinary source code is not automatically copied merely because it exists. A later semantic workflow may request additional evidence explicitly when needed.

The selection policy is versioned in the evidence manifest so a later policy change cannot masquerade as the same preparation input.

## Safety boundaries

Automatic candidate files are excluded rather than copied when they cross a deterministic safety boundary.

Current exclusion reasons include:

- `sensitive-path` for common credential/secret/key file names and formats;
- `framework-or-derived-path` for `.git/`, `.context/`, virtual environments, `node_modules`, and similar derived/internal trees;
- `symlink` because evidence must not silently dereference another location;
- `too-large` for files larger than 1 MiB;
- `non-utf8` for material the current text-only semantic workflow cannot safely present as text.

Automatic candidates that are rejected are recorded in the manifest by path and exclusion reason. Their contents are not copied.

Explicitly requested evidence fails clearly instead of silently weakening the operator's request when it violates one of these boundaries.

This is intentionally conservative. Later versions may add explicit reviewed mechanisms for binary documents, PDFs, or larger material rather than weakening the default text boundary.

## Evidence snapshot layout

Prepared evidence is stored under:

```text
.context/onboarding/<evidence-digest>/
├── manifest.json
└── evidence/
    └── <original repository-relative paths>
```

`manifest.json` uses schema:

```text
contextcanon/onboarding-evidence/v0
```

For every included file it records:

- repository-relative path;
- selection reason;
- exact byte size;
- SHA-256 content hash;
- snapshot-relative copied location.

It also records the versioned selection policy, UTF-8 requirement, size limit, and excluded automatic candidates.

The evidence digest is SHA-256 over the canonical manifest payload before the digest field itself is added. Absolute machine paths and timestamps are deliberately absent, so the same offered evidence and selection decisions produce the same identity on another checkout.

## Content-addressed and immutable in practice

If the same preparation produces an already existing digest, ContextCanon verifies the existing manifest, file set, sizes, and hashes and reuses it.

If an existing snapshot with that identity has been modified or corrupted, preparation fails. It does not silently repair or reinterpret that directory.

A newly prepared snapshot is built in a sibling staging directory and renamed into its content-addressed location only after all evidence and the manifest have been written. This keeps incomplete preparation out of the final evidence identity.

## What preparation does not prove

The snapshot proves **which bytes were offered**, not whether those bytes are correct, current, internally consistent, or suitable as ContextCanon governance.

In particular, `prepare` does not decide that:

- README prose is a Rule;
- an existing agent instruction should remain project-local;
- a convention belongs in a reusable generic Node;
- two documents agree;
- a Source should be accepted;
- current project state should become inherited governance.

Those are semantic questions for the later proposal/review stage.

## Next semantic layer

The next onboarding slice will define a proposal format and a framework-supplied LLM instruction that consumes one exact evidence snapshot.

Every semantic proposal item must carry evidence provenance and rationale. The classifier must distinguish at least:

- project-local Rule;
- existing reusable Source;
- candidate reusable/generic Node;
- Topic/Resource material;
- state/planning;
- ordinary documentation that should remain ordinary documentation;
- unresolved question or contradiction.

The LLM must be allowed to say that evidence is insufficient or contradictory. It must not fill gaps from unstated project assumptions.

Proposal generation still does not create canonical ContextCanon source. Human review and explicit acceptance remain a mandatory boundary before `CONTEXT.src.md` or related authored context is created or replaced.

## Design invariant

**Deterministic tooling defines and verifies the evidence and publication boundaries; semantic intelligence proposes meaning inside those boundaries; humans accept durable project truth.**
