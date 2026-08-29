# Onboard an Existing Project

You have an existing project in a Git directory: source code, README files, configuration, CI, architecture notes, perhaps old instructions for humans or AI tools. You want ContextCanon to sort that existing knowledge into a clean first Context Node **without requiring you to design the ContextCanon structure first**.

That is the onboarding use case.

You do **not** need an existing `CONTEXT.src.md`. The repository does not need to be perfectly documented either. Mixed, incomplete, or partly stale project documentation is exactly why the semantic review step exists.

## The whole idea from the user's point of view

You start with a normal Git project directory. ContextCanon examines likely context-carrying files, prepares one fixed review snapshot, gives you an assignment for a strong reasoning LLM, and then helps you review the LLM's proposed organization before anything becomes canonical.

In practical terms, you move one assignment **out** to the reasoning model and bring one JSON proposal **back**:

```text
(1) YOU HAVE
    an existing Git project directory
    README / CONTRIBUTING / docs / config / CI / agent instructions / ...
                         │
                         │  point ContextCanon at the directory
                         ▼
(2) CONTEXTCANON PREPARES A REVIEW SNAPSHOT
    contextcanon onboard prepare <project>
                         │
                         │  selected project evidence is "frozen"
                         ▼
(3) CONTEXTCANON GIVES YOU THE LLM ASSIGNMENT
    contextcanon onboard instruction ... > onboarding-instruction.md
                         │
                         │  give this file + frozen evidence to
                         ▼
(4) YOUR STRONG REASONING LLM
    sorts the project knowledge into Rules, Topics, reusable context,
    ordinary documentation, planning state, and unresolved questions
                         │
                         │  returns exactly one file
                         ▼
                    proposal.json
                         │
                         │  bring it back to ContextCanon
                         ▼
(5) CONTEXTCANON + YOU REVIEW IT
    validate → readable evidence review → accept / reject / correct
                         │
                         │  explicit human acceptance
                         ▼
(6) YOU GET
    CONTEXT.src.md + generated Official Context package
    + an acceptance record of exactly what was reviewed and accepted
```

### What does "freeze" mean here?

**Freezing does not lock your repository and it does not stop you editing the project.** ContextCanon copies the selected review material into a content-addressed snapshot and records the exact path, size and hash of every included file.

That gives you a simple but important advantage: **the LLM and the later human review are talking about the same project evidence.** If a README or configuration file changes while you are reviewing the proposal, ContextCanon can detect that before acceptance instead of silently applying yesterday's interpretation to today's project.

The frozen snapshot is therefore a review anchor, not a repository freeze. Your normal project can continue changing; an outdated review simply has to be prepared again.

The same property is useful while the onboarding method itself evolves. A different semantic pass, a corrected instruction, or another human review can deliberately reuse the **same Evidence digest** and therefore compare interpretations against one stable project basis instead of rescanning the live repository each time. Prepare a new snapshot when you intentionally want the evidence basis to change, not merely because another onboarding step or experiment starts.

### What is expected to be in the project directory?

A normal Git repository is enough. ContextCanon looks conservatively for likely context carriers such as:

- README, CONTRIBUTING, architecture, design and development documents;
- documentation below common documentation directories;
- project/build manifests and selected configuration;
- CI workflows;
- common AI/agent instruction files.

Ordinary source code is not copied wholesale during the first bootstrap. Important safe UTF-8 files can be included explicitly when needed. ContextCanon also excludes common secret/internal paths, symlinks and oversized evidence according to the documented safety limits.

So the folder does **not** need a special ContextCanon layout before onboarding. The point of onboarding is to help create that first structure from what the project already has.

> [!IMPORTANT]
> **Use a strong reasoning-capable model for the semantic review.** The useful part of the AI step is that it can compare scattered project material and propose what belongs together: durable Rules, deeper Topics, reusable cross-project practices, ordinary documentation, current planning state, contradictions, and unresolved questions. ContextCanon can verify the exact evidence and the returned structure, but it cannot turn weak semantic judgment into a good project model.

Once ContextCanon has organized the project context, smaller or local models can benefit greatly from receiving the right context during ordinary work. The occasional onboarding/restructuring pass is the place where stronger reasoning has unusually high leverage.

## The first onboarding pass, step by step

### 1. Freeze the project evidence

Run from the root of the Git repository you want to onboard:

```text
contextcanon onboard prepare .
```

ContextCanon prints a content-addressed snapshot path such as:

```text
.context/onboarding/<evidence-digest>/
```

The snapshot contains a `manifest.json` plus the selected files below `evidence/`. For a first experiment, inspect both once so you know exactly what the semantic reviewer will see.

If an important safe UTF-8 file was not selected automatically, include it explicitly:

```text
contextcanon onboard prepare . \
  --include src/project_policy.py \
  --include config/example.ini
```

### 2. Generate the LLM assignment

Use the snapshot path from step 1:

```text
contextcanon onboard instruction \
  .context/onboarding/<evidence-digest> \
  > onboarding-instruction.md
```

You do not invent the onboarding prompt. ContextCanon supplies the semantic task and the exact JSON contract.

### 3. Give one assignment to a strong reasoning LLM

This is the semantic sorting step. Give the model:

- `onboarding-instruction.md` as the controlling assignment;
- read access to the frozen `evidence/` directory.

The model must return **exactly one JSON object**. Save it as:

```text
proposal.json
```

Think of `proposal.json` as a findings report. The model proposes which existing knowledge appears to be:

- a durable project-local Rule;
- already covered by a supplied reusable Source;
- a candidate for a new reusable Node;
- deeper Topic-specific material;
- current state or planning;
- ordinary documentation that should stay ordinary documentation;
- an unresolved question or contradiction.

The model proposes meaning; it does not publish project truth.

### 4. Validate the proposal

Bring `proposal.json` back to ContextCanon:

```text
contextcanon onboard validate \
  .context/onboarding/<evidence-digest> \
  proposal.json
```

ContextCanon verifies schema, exact evidence references, hashes and line ranges and computes a deterministic `proposal_digest`.

This proves that the proposal refers to the frozen evidence correctly. It does **not** prove that the model's semantic judgment is correct.

### 5. Create the human review

```text
contextcanon onboard review \
  .context/onboarding/<evidence-digest> \
  proposal.json \
  review.json \
  --node-name "My Project"
```

ContextCanon creates `review.json` with every finding initially `pending` and prints a readable review report. For each proposal item you see its classification, confidence, rationale, proposed payload and the exact cited evidence lines.

Change every decision in `review.json` to either `accept` or `reject`.

If the **finding itself** is wrong — wrong classification, wording, evidence, payload, or reusable Source identity — correct `proposal.json`, validate again and create a fresh review. This keeps one semantic proposal language instead of hiding corrections in a second patch format.

### 6. Explicitly accept the completed review

When no decision remains `pending`:

```text
contextcanon onboard accept \
  .context/onboarding/<evidence-digest> \
  proposal.json \
  review.json \
  --project .
```

This is the publication step. Before writing canonical context, ContextCanon rechecks that:

- the live project files still match the frozen evidence you reviewed;
- the review still matches the exact proposal;
- every accepted reusable Source is the same exact immutable package the semantic reviewer saw;
- the proposed Context Node compiles in staging;
- Topic Markdown closure cannot pull unreviewed local files into the package;
- first adoption would not overwrite an existing project-owned compiler output path.

Only then does it create the first canonical `CONTEXT.src.md`, build/check the generated Official Context package and write the acceptance record. If first publication fails after it begins, ContextCanon rolls the newly created canonical/generated state back instead of leaving the repository half-adopted.

## What you get

A successful first onboarding gives the project a reviewed first Context Node rather than a pile of AI-generated edits:

```text
CONTEXT.src.md                     editable canonical authoring
CONTEXT.md                         generated compact official entry
CONTEXT/                           generated deeper resources when needed
.context/context.yaml              compiler-owned local machine view
.context/package.json              exact portable package identity
.context/onboarding/accepted/...   review and acceptance provenance
```

Accepted local Rules and Topics become canonical authoring. Rejected findings remain rejected and recorded. Ordinary documentation stays ordinary documentation. Candidate reusable Nodes and unresolved questions remain separate follow-up artifacts instead of being silently flattened into local Rules or invented answers.

## Reusable Sources are optional and exact

ContextCanon can show the semantic reviewer already-published reusable Source packages so that generic practices can be consolidated rather than copied into every project:

```text
contextcanon onboard instruction <evidence-snapshot> \
  --catalog-package <package-root-a> \
  --catalog-package <package-root-b>
```

If no catalog is supplied, the model is not allowed to invent an `existing-source` match.

If the model proposes an existing Source and the human accepts it, final acceptance requires **the exact same immutable package identity** again: stable Node ID, name, version, normalized digest and package digest. A different or newer package for the same Node is rejected rather than silently changing what was reviewed.

Current first-adoption behavior does **not** add a Source automatically. In particular, the repository-local ContextCanon Gateway is not a reusable baseline. Whether ContextCanon Foundation should normally be offered or recommended as the starting reusable Source is intentionally left for the larger real-project onboarding test rather than being made a silent default before we have used the workflow at scale.

## Important first-adoption safety limits

First-adoption v0 is deliberately conservative:

- an existing `CONTEXT.src.md` is a hard stop; re-onboarding needs a separate reviewed update workflow;
- a pre-existing `CONTEXT/` tree is not seized;
- any actual compiler-output collision discovered by staged compilation stops publication;
- changed live evidence invalidates the reviewed snapshot;
- no pending human decision may be published;
- unreviewed files cannot enter through Markdown-link closure;
- failed first publication is rolled back.

These are trust boundaries, not conveniences to bypass.

## Why the workflow has separate steps

The workflow may look more explicit than a one-shot "read my repository and set everything up" prompt. That is intentional:

```text
ContextCanon prepare      Which exact project bytes may be considered?
ContextCanon instruction  What semantic task and output contract are being asked?
External reasoning LLM    What do those bytes appear to mean?
ContextCanon validate     Does the JSON provably refer to those exact bytes?
ContextCanon review       Can a human inspect each finding and its evidence?
Human decision            Which findings do we accept or reject?
ContextCanon accept       Is that exact reviewed state safe to publish now?
Compiler/build/check      Does the accepted canonical Node actually compile exactly?
```

Deterministic parts handle identity, integrity, reproducibility and state transitions. The reasoning model handles the narrow part that ordinary programming cannot solve well: interpreting messy human project knowledge. The human handles the part neither one should fake: deciding which interpretation becomes durable project truth.

## Need the exact contracts and safety details?

This page is intentionally the **first-contact guide**. The full schema, evidence-selection limits, compatibility behavior, acceptance contract, classification semantics and deterministic safety properties remain available in the [onboarding technical reference](onboarding-reference.md#technical-reference).

That split is deliberate progressive disclosure: start with what you need to perform and understand onboarding; open the reference when you are implementing, auditing, debugging, or changing the mechanism.
