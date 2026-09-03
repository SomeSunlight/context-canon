# Source Format

`CONTEXT.src.md` is the human-editable source of truth for one Context Node. The compiler never needs to reconstruct authored information from generated `CONTEXT.md`, `.context/context.yaml`, or `.context/package.json`.

The format is deliberately constrained Markdown: readable without special tooling, but structured enough for deterministic parsing.

## Node header

A source begins with a human-readable H1 and compiler-managed Node metadata:

```markdown
# Example Project — Local Context Source
<!-- ctx:node id="<stable-node-id>" version="0.1.0" -->
```

The stable ID is independent of the Node's directory path or display name. A root Node may additionally declare generated harness adapters, for example `adapters="agents,goose"`.

## Overview

`## Overview` is an optional short orientation block for the Node itself: what this place is, why it exists, and what background helps a human or agent understand it before applying Rules or following Topics.

```markdown
## Overview

This service owns customer-facing notification delivery. It exists separately from the billing service because delivery retries, provider failover, and message templates have their own operational lifecycle.
```

Overview text is copied into the generated `CONTEXT.md` near the top of the compact entry. It is **local presentation and orientation**, not inherited governance: using a Node as a Source does not copy its Overview into a child Node.

Changing only an Overview therefore changes the exact published package bytes and `package_digest`, but does not change `normalized_digest`. Rules, Changes, Sources, and Topics remain the semantic composition boundary.

Keep an Overview compact. It is always-read entry context, so deeper explanations belong behind Topics rather than turning the Overview into another preload document. In particular, use Topics for material that needs to be packaged as deeper Resources instead of relying on repository-local links from an Overview.

## Sources

`## Sources` lists accepted Context Nodes. The visible link names the Source location; the adjacent compiler-managed comment preserves stable identity and accepted version.

### Local development Source

An unpinned Source is resolved as a local node-root path inside the same repository:

```markdown
## Sources

- [ContextCanon Foundation](../foundation/) — `0.1.0`
  <!-- ctx:source id="<stable-node-id>" version="0.1.0" -->
```

This remains the simple development/dogfood case.

### Accepted immutable Source

An accepted external Source additionally pins both canonical semantics and exact published package bytes:

```markdown
## Sources

- [Python Development](https://example.org/context-nodes.git) — `1.2.0`
  <!-- ctx:source id="<stable-node-id>" version="1.2.0" normalized-digest="<sha256>" package-digest="<sha256>" -->
```

`normalized-digest` and `package-digest` are an all-or-nothing pair. Each is lowercase SHA-256 hexadecimal.

For a pinned Source, the visible link is provenance/update location rather than something ordinary `contextcanon build` dereferences. Build loads only the accepted immutable artifact from the consumer Node's `.context/sources/<package-digest>/` store and verifies Node ID, version, both digests, and package files.

This keeps normal builds offline and prevents a Source repository update from silently changing a consumer.

### Git update transport

A pinned Source may additionally describe how candidate updates are retrieved:

```markdown
- [Python Development](https://example.org/context-nodes.git) — `1.2.0`
  <!-- ctx:source id="<stable-node-id>" version="1.2.0" normalized-digest="<sha256>" package-digest="<sha256>" transport="git" ref="main" node-path="nodes/library/python-development" -->
```

`transport`, `ref`, and `node-path` are an all-or-nothing set. Compiler 0.4 supports `transport="git"`.

`ref` names the branch/tag/ref from which `contextcanon source fetch` retrieves a candidate. It is deliberately **not** the accepted identity; the accepted state remains pinned by version plus both digests.

`node-path` locates the Source Node inside the retrieved repository snapshot. Use `.` for a repository-root Node. It is location only and may not be absolute, contain `..`, or use backslashes.

Transport metadata is only for candidate discovery. Normal `build` never uses it.

Source order is not precedence. See [Context composition](composition.md) for immutable package storage and the fetch/review/accept workflow.

## Rules

`## Rules` contains the Node's local Rules. `###` headings group related Rules. Every Rule has a short visible title, a statement, rationale, and compiler-managed stable ID.

```markdown
### Security

- **Never commit secrets:** Credentials and secret values must stay outside version control.
  Why: Version control is not a secret store.
  <!-- ctx:rule id="SEC-001" -->
```

The title is part of the human presentation, not identity. Descendants address the stable ID.

## Changes

`## Changes` contains explicit local operations on inherited ordinary Rules.

Compiler 0.4 supports **Remove** and **Override**. Both operations bind the inherited Rule's stable identity: origin Node ID plus Rule ID. Visible Source names and Rule titles help humans but do not define identity.

### Remove

```markdown
## Changes

### Remove

- `Company Security / SEC-014` — Require legacy audit header
  Why: This project uses the replacement audit protocol instead.
  <!-- ctx:change op="remove" source-id="<stable-source-node-id>" rule-id="SEC-014" -->
```

A Remove deletes that inherited Rule from this Node's official Rule set. Descendants inherit the already-removed result.

If the targeted identity is not inherited, compilation fails with a dangling-Change diagnostic. Remove cannot silently become a no-op.

### Override

```markdown
## Changes

### Override

- `Python Development / PY-007` — Supported Python version
  New rule: Production code must support Python 3.12 or newer.
  Why: This project has standardized on the 3.12 runtime baseline.
  <!-- ctx:change op="override" source-id="<stable-source-node-id>" rule-id="PY-007" -->
```

An Override preserves the inherited Rule's identity, title, group, and origin, but replaces its effective statement for this Node. The compiler records the overriding Node and rationale as provenance. Descendants inherit that overridden meaning unless they explicitly change it again.

Only the statement is currently overridable. Renaming or regrouping an inherited Rule is deliberately not disguised as an Override.

A Node may define at most one local Change for a given inherited Rule identity.

Protected Rules and authorized exceptions are a later semantic layer. They will constrain which Changes are legal rather than changing the basic identity model.

## Topics

A Topic states when deeper context applies and explicitly types every target.

```markdown
## Topics

### Logging

When changing logging, diagnostics, or structured events:

Required:
- Resource: `docs/logging-contract.md`

Optional:
- Resource: `docs/logging-history.md`
```

A Topic can also navigate to another Context Node without composing it:

```markdown
Required:
- Context Node: `nodes/internal/framework-development`
```

`Resource` targets are materialized into the generated `CONTEXT/` package. `Context Node` targets point to another node root and remain navigation rather than Source composition.

Every Topic ends with a compiler-managed stable ID:

```markdown
<!-- ctx:topic id="LOGGING" -->
```

## Normal authoring after onboarding

After a project has adopted ContextCanon, ordinary work does not repeat migration onboarding. The canonical source remains `CONTEXT.src.md` plus the Node's natural Resource files.

For existing text, edit `CONTEXT.src.md` directly. For a **new Rule or Topic**, prefer the deterministic authoring commands so ContextCanon allocates the hidden stable identity once instead of making the author invent a `ctx:rule` or `ctx:topic` comment:

```text
contextcanon author rule . --group Security --title "Keep secrets out of Git" --statement "Credentials and secret values must stay outside version control." --why "Version control is not a secret store."

contextcanon author topic . --title Logging --condition "When changing logging or diagnostics:" --required-resource docs/logging-contract.md
```

The commands write ordinary source syntax; they do **not** create another authoring database and they do not hide publication behind a write. The resulting `CONTEXT.src.md` is immediately readable and editable by hand. ContextCanon merely allocates the stable `RULE-...` or `TOPIC-...` identity and validates that the edited Node still parses.

The minimal daily loop is intentionally boring:

```text
read CONTEXT.md for the effective working context
→ edit CONTEXT.src.md and/or natural Resource files
→ use contextcanon author rule/topic when creating a new identified element
→ contextcanon build <node-or-repository>
→ contextcanon check <node-or-repository>
→ when a reusable Source has a candidate update, review it before explicit acceptance
```

Use `--all` with `build`/`check` when repository-wide generated state should be refreshed or verified. Source candidate discovery/review/acceptance remains a separate explicit workflow; normal authoring and normal builds never silently pull newer Source meaning.

## Compiler-managed authoring help

Raw Markdown may contain compiler-managed HTML comment blocks with copyable examples. These blocks are authoring help only; they do not carry critical human meaning and disappear from rendered Markdown.

A useful Change template is:

```markdown
### Override

- `Source name / RULE-ID` — Current rule title
  New rule: Replacement statement.
  Why: Why this Node differs.
  <!-- ctx:change op="override" source-id="<stable-source-node-id>" rule-id="RULE-ID" -->
```

## Current compiler contract

The executable compiler may intentionally support a narrower language than later specification layers. Unsupported syntax must fail clearly rather than be inferred. Implementation-specific module details belong to the implementation's own development documentation; this Foundation document describes the reusable authoring contract rather than one repository's internal module status.
