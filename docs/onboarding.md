# Reviewed Project Onboarding

ContextCanon onboarding is a semantic workflow above the deterministic compiler. Its purpose is to turn an existing repository into a reviewable ContextCanon proposal without letting an LLM directly invent or publish canonical project context.

The implemented boundary is now:

```text
existing Git repository
        ↓
contextcanon onboard prepare
        ↓
content-addressed evidence snapshot
        ↓
contextcanon onboard instruction
        +
optional verified reusable Source packages
        ↓
harness-neutral semantic instruction
        ↓
LLM or other semantic reviewer
        ↓
proposal/v0 JSON
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

`onboard prepare`, `onboard instruction`, and `onboard validate` are deterministic. ContextCanon still does **not** choose or call an LLM provider in this stage. The semantic model remains replaceable and its output must cross the deterministic proposal validator before it can even become a review artifact.

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

## Framework-owned semantic instruction

The operator should not have to invent the classification prompt. ContextCanon renders it from the exact evidence snapshot:

```text
contextcanon onboard instruction <evidence-snapshot>
```

The instruction is written **only to stdout**, so it can be redirected or supplied unchanged to any capable harness. A deterministic SHA-256 of those exact instruction bytes is reported on stderr:

```text
contextcanon onboarding instruction digest: <sha256>
```

The instruction schema is:

```text
contextcanon/onboarding-instruction/v0
```

Its content is deterministic for the same evidence snapshot and the same reusable Source catalog. It contains:

- the exact evidence digest;
- every included evidence path, SHA-256, line count, and selection reason;
- the semantic classification rules;
- the exact `proposal/v0` output contract;
- explicit rules for uncertainty, contradictions, ordinary documentation, project state, local governance, and likely reusable context;
- an explicit requirement to return JSON only and to make no repository edits.

The semantic reviewer is required to read every included evidence file. It must not use live-repository files, web search, chat history, model memory, or unstated assumptions as project evidence.

### Evidence is data, not an instruction channel

This distinction matters because selected evidence intentionally includes files such as `AGENTS.md` and other existing harness instructions.

For onboarding, **all evidence content is untrusted review data**. A sentence inside README, AGENTS, a development guide, or another evidence file may itself tell an agent to run commands, ignore instructions, edit files, or load additional material. The framework-owned onboarding instruction explicitly tells the semantic reviewer not to obey such text as a meta-instruction and never to execute commands or follow links merely because evidence asks it to.

Verified reusable Source package content is treated the same way during onboarding: its Rules and Topics are catalog data used to compare reusable meaning, not instructions governing the semantic review process itself.

This is a semantic safety boundary, not a sandbox. A future model runner may add stronger isolation, but deterministic ContextCanon does not pretend that text alone can technically constrain an arbitrary external harness.

## Reusable Source catalog input

Likely cross-project practices should be compared against available reusable Nodes before the model proposes another generic Node.

ContextCanon deliberately does **not** introduce a second catalog package format. The instruction command accepts already published immutable Context packages directly:

```text
contextcanon onboard instruction <evidence-snapshot> \
  --catalog-package <package-root-a> \
  --catalog-package <package-root-b>
```

Every supplied package is loaded through the existing `CompiledPackage` integrity verifier. Invalid or tampered packages fail before their content can enter the semantic instruction.

For each catalog package, the instruction exposes:

- stable Node ID and name;
- version;
- normalized semantic digest;
- exact package digest;
- effective Rules with stable identity, statement, and rationale;
- published Topics and conditions.

Catalog input order is not meaning: packages are deterministically sorted, and more than one package for the same stable Node ID is rejected. One onboarding run therefore sees at most one candidate version of each reusable Node.

When no catalog package is supplied, the instruction explicitly forbids inventing an `existing-source`. Likely generic material must remain a `candidate-reusable-node` or `unresolved-question` until a human or later catalog resolver can compare it properly.

This explicit package-list interface is the semantic contract. Convenient discovery of a standard installed/remote Node catalog can be added later without changing the instruction's meaning or introducing live inheritance.

## Harness execution boundary

`onboard instruction` produces harness-neutral content; it does not control what an external harness automatically injects around that content.

Some harnesses can automatically attach a live repository's `AGENTS.md`, workspace instructions, memories, or other context before the generated onboarding instruction is processed. Such material would violate the intended evidence-only review boundary if it influences classification outside the frozen snapshot.

A reproducible semantic onboarding run must therefore execute the generated instruction in a configuration where:

- the ContextCanon instruction is the controlling task instruction;
- the reviewer can read the frozen `evidence/` files and any explicitly supplied catalog packages;
- live-project instructions are not separately auto-attached as governing context;
- evidence files remain readable as data even when their original names normally have special meaning to a harness.

ContextCanon can detect and verify its own bytes; it cannot prove the hidden prompt composition of a third-party harness. This operational requirement must remain explicit until an integrated runner can enforce a stronger boundary.

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
framework-owned instruction
          ↓
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

The evidence snapshot proves **which bytes were offered**. The generated instruction proves **which ContextCanon semantic task text and catalog semantics were rendered**. Proposal validation proves **that the proposal has the required structure and that its claimed provenance points into those exact evidence bytes**.

None of these proves that the semantic interpretation is correct or that an external harness actually executed only the intended prompt context.

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

The next layer is the human review/acceptance boundary for a **validated** proposal.

It must make the proposed classifications and their evidence easy to inspect, preserve unresolved questions and reusable-Node candidates rather than silently flattening them, and require explicit acceptance before canonical `CONTEXT.src.md` or related authored files can be created or replaced.

Immediately after acceptance, ordinary deterministic ContextCanon validation/build must run. Proposed new reusable Nodes remain separately reviewable/versioned artifacts and are never auto-published merely because onboarding identified reusable material.

A later integrated model runner may automate execution of the generated instruction, but provider/model selection remains orthogonal to compiler truth and to the proposal/acceptance contract.

## Design invariant

**Deterministic tooling defines and verifies evidence, instruction, proposal, and publication boundaries; semantic intelligence proposes meaning inside those boundaries; humans accept durable project truth.**
