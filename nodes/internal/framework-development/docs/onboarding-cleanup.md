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
- identify cases that are too entangled to rewrite safely.

It may use only the accepted/frozen review material supplied for this cleanup task. It does not mutate files.

### Human

The project owner:

- accepts, rejects, or edits the proposed replacement;
- judges whether the familiar document is still useful and readable;
- decides when an intentionally friendlier summary is worth keeping.

### ContextCanon

Deterministic tooling:

1. binds the cleanup proposal to the exact accepted placement and exact source bytes;
2. renders a complete before/after diff;
3. refuses stale or changed source files;
4. applies only explicitly reviewed replacements;
5. verifies that fixed/authority/resource boundaries were not crossed;
6. performs the mutation transaction-like and records exactly what changed.

## Link target

The cleanup link should point to the **human-facing canonical Context Node entry**, not to `.context/` bookkeeping and not to a transient onboarding artifact. Repository-relative links are preferred when the document and Node live in the same repository.

The exact rendered link format should be derived mechanically from the accepted destination Node path. A human or LLM should not have to type or maintain a second locator by hand.

## UX constraint

Do not turn cleanup into another long penalty-box workflow. The operator should normally encounter one compact cleanup review after placement publication:

```text
placement published
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
2. only then remove or shorten the old copy.

This preserves trust while still making non-redundancy the required final architecture rather than an optional cosmetic improvement.
