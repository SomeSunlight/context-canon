# Reviewed Project Onboarding

ContextCanon onboarding is a semantic workflow above the deterministic compiler. Its purpose is to turn an existing repository into a reviewable ContextCanon proposal without letting an LLM directly invent or publish canonical project context.

The implemented deterministic boundary is now:

```text
existing Git repository
        ↓
contextcanon onboard prepare
        ↓
content-addressed evidence snapshot
        ↓
semantic proposal generation (LLM later)
        ↓
contextcanon onboard validate
        ↓
strict proposal bound to exact evidence
        ↓
future human review and explicit acceptance
        ↓
CONTEXT.src.md + Sources + Topics + Resources
        ↓
normal deterministic compiler
```

Neither `onboard prepare` nor `onboard validate` calls an LLM. Proposal generation is deliberately outside deterministic truth; validation brings its output back across an exact machine-checkable boundary.

## Why preparation is separate

An LLM must not reason over an undefined moving target such as "whatever files happen to be in the repository when the request is executed".

`onboard prepare` freezes the exact project evidence offered to the later semantic step. Every included file is bound by repository-relative path, byte size, SHA-256 hash, selection reason, and exact copied bytes.

This gives later review a stable question:

> Which exact repository evidence supported this proposed Rule, Topic, Source choice, or unresolved question?

If a selected source document changes later, a new evidence digest and a new snapshot are produced. The earlier snapshot remains independently reviewable.

## Preparing evidence

From a Git repository root:

```text
contextcanon onboard prepare .
```

Additional safe UTF-8 files may be added explicitly:

```text
contextcanon onboard prepare . --include src/project_policy.py --include config/example.ini
```

`prepare` deliberately does not require `CONTEXT.src.md`. It is meant for repositories that have not yet adopted ContextCanon.

Automatic inventory uses Git's repository visibility rules:

```text
git ls-files --cached --others --exclude-standard
```

Tracked files and non-ignored untracked files are therefore visible to the default selector. Git-ignored files are not silently offered. An explicit `--include` can add an otherwise ignored safe file, but explicit inclusion remains subject to path, secret, size, symlink, and UTF-8 checks.

Git is only the deterministic inventory boundary. Git state is not interpreted as project meaning.

## Conservative automatic selection

The default policy prefers likely high-value context carriers instead of copying the repository wholesale.

Current automatic categories are:

- root project documents such as README, CONTRIBUTING, CHANGELOG, ARCHITECTURE, DESIGN, DEVELOPMENT, SECURITY, and SUPPORT documents;
- UTF-8 text documentation below `docs/`, `doc/`, or `documentation/` directories;
- common harness instructions such as `AGENTS.md`, `CLAUDE.md`, `.goosehints`, GitHub Copilot instructions, and `.github/instructions/` text;
- selected root project/build manifests such as `pyproject.toml`, `package.json`, `Cargo.toml`, `go.mod`, Gradle/Maven files, common test/lint configuration, Docker/Compose files, and requirements files;
- GitHub Actions workflow YAML.

Ordinary source code is not automatically copied merely because it exists. A semantic workflow can request additional evidence explicitly when needed.

The selection policy is versioned in the evidence manifest so a future policy change cannot masquerade as the same preparation input.

## Safety boundaries

Automatic candidate files are excluded rather than copied when they cross a deterministic safety boundary.

Current boundaries include:

- `sensitive-path` for common credential, secret, environment, and key file names/formats;
- `framework-or-derived-path` for `.git/`, `.context/`, virtual environments, `node_modules`, and similar derived/internal trees;
- `symlink` because evidence must not silently dereference another location;
- `too-large` for a single file larger than **1 MiB**;
- `non-utf8` for material the current text-only workflow cannot safely present as text;
- a **16 MiB total evidence ceiling** so a repository containing thousands of individually small documentation files cannot create an unbounded snapshot.

The per-file and total limits are part of the manifest selection policy. The total limit fails preparation clearly before a final snapshot is published rather than silently truncating evidence.

Automatic candidates rejected after selection are recorded by path and exclusion reason. Their contents are not copied. Explicitly requested evidence fails clearly instead of silently weakening the operator's request when it violates a boundary.

This is intentionally conservative. Later versions may add explicit reviewed mechanisms for PDFs, binary material, or larger evidence sets rather than weakening the default text boundary.

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

For every included file it records repository-relative path, selection reason, exact byte size, SHA-256 content hash, and snapshot-relative copied location. It also records the versioned selection policy, UTF-8 requirement, per-file and total size limits, inventory mechanism, and excluded automatic candidates.

The evidence digest is SHA-256 over the canonical manifest payload before the digest field itself is added. Absolute machine paths and timestamps are deliberately absent, so the same offered evidence and selection decisions produce the same identity on another checkout.

If the same preparation produces an already existing digest, ContextCanon verifies the existing manifest, file set, sizes, and hashes and reuses it. If that content-addressed snapshot has been modified or corrupted, preparation fails rather than repairing it silently.

A new snapshot is built in a sibling staging directory and renamed into its content-addressed location only after evidence and manifest are complete.

## Semantic proposal format

A semantic onboarding proposal is **not** Official Context and is not accepted governance. It is a typed review artifact using:

```text
contextcanon/onboarding-proposal/v0
```

The top level binds the proposal to one exact `evidence_digest` and contains typed proposal items. Every item requires:

- a stable proposal-local `id`;
- one supported classification `kind`;
- title and rationale;
- explicit confidence: `high`, `medium`, or `low`;
- one or more evidence references containing path, SHA-256, start line, and end line;
- a kind-specific payload.

Supported classifications are:

- `local-rule`;
- `existing-source`;
- `candidate-reusable-node`;
- `topic-resource`;
- `state-planning`;
- `ordinary-documentation`;
- `unresolved-question`.

The payload schema is strict for each kind. Unknown fields fail rather than being ignored. Resource/document paths that claim to refer to project evidence must actually exist in the frozen snapshot.

## Validating a proposal

A proposal can be checked with:

```text
contextcanon onboard validate <evidence-snapshot> <proposal.json>
```

Validation reloads and verifies the evidence snapshot, then checks proposal schema, exact evidence digest, unique item IDs, supported kinds, confidence values, non-empty provenance, evidence file hashes, line ranges, and kind-specific payloads.

A successful validation produces a deterministic `proposal_digest` over the normalized proposal. This digest identifies the exact review object; it does not imply human acceptance.

This distinction is important:

```text
LLM or other semantic producer
          ↓
untrusted proposal JSON
          ↓
deterministic validate
          ↓
verified review artifact
          ≠
accepted project truth
```

## What the deterministic boundary does not prove

The evidence snapshot proves **which bytes were offered**. Proposal validation proves **that the proposal has the required structure and that its claimed provenance points into those exact bytes**.

Neither step proves that the semantic interpretation is correct.

In particular, deterministic onboarding does not decide that:

- README prose is a Rule;
- an existing agent instruction should remain project-local;
- a convention belongs in a reusable generic Node;
- two documents agree semantically;
- a Source should be accepted;
- current project state should become inherited governance;
- a high-confidence LLM judgment is actually right.

Those remain semantic and human-review questions.

## Next layer

The next slice supplies the **framework-owned harness-neutral LLM onboarding instruction**. The operator should not have to invent the classification prompt manually.

That instruction must require the semantic model to:

- use the frozen evidence rather than unstated project assumptions;
- surface uncertainty and contradictions;
- produce the exact proposal schema;
- provide provenance and rationale for every item;
- distinguish project-local context from likely reusable generic context;
- compare reusable candidates against the available ContextCanon Node catalog before duplicating them locally;
- preserve useful ordinary README/CONTRIBUTING/docs material instead of treating onboarding as destructive migration.

After that comes mandatory human review and explicit acceptance. Only acceptance may create or replace canonical authored ContextCanon files, followed immediately by normal deterministic validation/build.

## Design invariant

**Deterministic tooling defines and verifies evidence, proposal, and publication boundaries; semantic intelligence proposes meaning inside those boundaries; humans accept durable project truth.**
