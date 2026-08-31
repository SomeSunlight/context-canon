# Onboarding Duplicate Cleanup

Use this design boundary when promoted onboarding meaning is already canonical in ContextCanon but the original mutable Markdown still contains the same maintained meaning.

## Goal: one meaning, one maintenance surface

ContextCanon exists to reduce context duplication, not to create another synchronized copy.

When placement action `promote` is accepted, the destination Context Node becomes the **single canonical maintenance surface** for that meaning. Initial placement publication deliberately leaves ordinary project Markdown untouched so adoption is rollback-safe and reviewable. Any resulting duplicate is therefore a **migration transition**, not an acceptable steady state.

The desired end state is:

```text
canonical detailed meaning
        ↓
Context Node

familiar README/docs surface
        ↓
short orientation / plain-language summary / "see here" link
        ↓
canonical Context Node
```

A familiar document may still explain the idea in friendlier or more informal words when that improves human understanding. It must not remain a second place where the same durable rule or detailed meaning has to be kept synchronized.

## What cleanup may do

For mutable Markdown only, a reviewed cleanup proposal may replace an exact promoted source excerpt with one of three outcomes:

1. **orientation + reference** — a concise human-facing summary and a link to the owning Context Node;
2. **reference only** — a short pointer such as "See the canonical project context" when repeating even a summary adds no value;
3. **remove** — no replacement when the surrounding document remains clear without the duplicate.

The replacement is presentation, not a second authority. It may deliberately use easier or more conversational wording than the canonical Context Node.

## What cleanup must never do

Cleanup must not:

- edit Markdown marked fixed/authoritative in the accepted structure;
- shorten or remove `topic-resource` content whose document remains the canonical maintenance surface;
- reinterpret an `authority-mapping` as permission to rewrite its authority;
- delete text merely because it looks similar to Node text;
- use line numbers alone as permission to mutate a live file;
- silently resolve an ambiguous overlap between promoted meaning and unrelated document prose;
- maintain the same complete rule/explanation in both the Node and the document after cleanup.

If the source excerpt cannot be isolated safely, leave it unchanged and surface an unresolved cleanup item.

## Review object

A cleanup candidate must be bound to the already accepted placement item and carry enough exact state to prove what is being changed:

- placement acceptance identity/digest;
- placement item stable authoring ID;
- owning destination Node identity/path;
- source repository-relative Markdown path;
- exact reviewed source excerpt and its byte/hash identity;
- current live file identity before mutation;
- proposed replacement kind: `orientation-reference`, `reference-only`, or `remove`;
- proposed replacement wording and target locator when applicable;
- semantic rationale explaining why the original is now redundant rather than independently authoritative.

The human review surface should show the **whole resulting file diff**, not only the replacement fragment. A good local replacement can still damage headings, list flow, examples, or surrounding explanations when seen in context.

## Deterministic versus semantic work

The split remains the standard ContextCanon split:

### Semantic reviewer

A strong reasoning model may:

- decide whether the accepted promoted meaning is a true duplicate in the mutable document;
- propose a short human-facing orientation sentence;
- decide whether a plain reference or removal is clearer;
- deliberately use simpler, friendlier, or more conversational wording when that improves the familiar document;
- identify cases that are too entangled to rewrite safely.

It may use only the accepted/frozen review material supplied for this cleanup task. It does not mutate files. The exact original source excerpt remains visible in the human cleanup review beside the proposal.

### Human

The project owner:

- accepts, rejects, or edits the proposed replacement;
- judges whether the familiar document is still useful and readable;
- decides when an intentionally friendlier summary is worth keeping.

### ContextCanon

Deterministic tooling:

1. binds the cleanup proposal to the exact accepted placement and exact source bytes;
2. derives the destination link mechanically from the accepted Node path rather than trusting an LLM-typed locator;
3. renders a complete before/after diff;
4. refuses stale or changed source files;
5. applies only explicitly reviewed replacements;
6. verifies that fixed/authority/resource boundaries were not crossed;
7. performs the mutation transaction-like and records exactly what changed.

## Link target

The cleanup link should point to the **human-facing canonical Context Node entry**, not to `.context/` bookkeeping and not to a transient onboarding artifact. Repository-relative links are preferred when the document and Node live in the same repository.

The exact rendered link target should be derived mechanically from the accepted destination Node path. A human or LLM should be free to edit the surrounding phrase — including something as short as "See here" — without having to type or maintain a second locator by hand.

## Git checkpoint before document mutation

Once placement has created or changed real Context Nodes, Git becomes the natural safety boundary for the next phase.

Before any duplicate-cleanup mutation, ContextCanon should require or strongly verify a **clean, committed working state** for the reviewed placement result. The intended sequence is:

```text
reviewed placement published
        ↓
review / commit the canonical Node changes
        ↓
start cleanup from that clean Git state
        ↓
LLM proposes document handoffs
        ↓
human reviews whole-document diffs
        ↓
ContextCanon applies only approved changes
        ↓
review / commit the cleaned version
```

ContextCanon should not silently create commits for the owner. Git is the recoverable version boundary; ContextCanon should detect a dirty or changed base before destructive cleanup and refuse to pretend it is still applying the reviewed transformation to the same state.

This also leaves a visible historical marker in the original document change: Git shows exactly where detailed prose was replaced by an orientation/reference to canonical Context. The owner can later simplify or remove that presentation link like any other ordinary documentation edit without changing the canonical Node meaning.

## UX constraint

Do not turn cleanup into another long penalty-box workflow. The operator should normally encounter one compact cleanup review after placement publication:

```text
placement published
        ↓
clean Git checkpoint of canonical Nodes
        ↓
cleanup candidates prepared from accepted promoted excerpts
        ↓
semantic replacement suggestions only where wording judgment is needed
        ↓
one human review of resulting document diffs
        ↓
preview / explicit publish
```

The exact command surface is intentionally not frozen yet. Real onboarding should determine whether this is best exposed as separate `placement-cleanup-*` commands or a smaller continuation from the visible onboarding workspace.

## Why cleanup is separate from initial placement publication

Placement establishes **future ownership**. Cleanup changes familiar project documents.

Keeping those as separate review boundaries gives the owner a safe sequence:

1. first verify that ContextCanon captured the right meaning in the right Node;
2. commit that reviewed canonical state as a recoverable Git checkpoint;
3. only then remove or shorten the old copy.

This preserves trust while still making non-redundancy the required final architecture rather than an optional cosmetic improvement.
