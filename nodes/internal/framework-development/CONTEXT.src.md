# ContextCanon Framework Development — Local Context Source
<!-- ctx:node id="8b8f6ad7-2d17-4f9f-9a6c-8cb0bc5d8c2a" version="0.1.0-draft" -->

> [!IMPORTANT]
> **Edit this file to change the context for designing and implementing ContextCanon itself.**
> `CONTEXT.md` and `CONTEXT/` are generated from this source plus accepted Context Sources.
>
> This Node composes [ContextCanon Foundation](../../library/foundation/) and the reusable [Development Workflow](../../library/development-workflow/), then adds only the framework-development delta.
>
> Full format documentation: [../../library/foundation/docs/source-format.md](../../library/foundation/docs/source-format.md)

<!--
ContextCanon authoring templates — compiler-managed help, safe to copy.

NEW RULE
### Group
- **Rule title:** Rule statement.
  Why: Reason for the rule.
  [compiler inserts stable ctx:rule ID]

REMOVE IMPORTED RULE
### Remove
- `Source name / RULE-ID` — Current rule title
  Why: Why it does not apply here.
  <!-- ctx:change op="remove" source-id="<stable-source-node-id>" rule-id="RULE-ID" -->

OVERRIDE IMPORTED RULE
### Override
- `Source name / RULE-ID` — Current rule title
  New rule: Replacement statement.
  Why: Why this Node differs.
  <!-- ctx:change op="override" source-id="<stable-source-node-id>" rule-id="RULE-ID" -->
-->

## Sources

- [ContextCanon Foundation](../../library/foundation/) — `0.1.0-draft`
  <!-- ctx:source id="4ca9d92c-59f2-4b1f-b7b3-0e2ff91fd001" version="0.1.0-draft" -->

- [Development Workflow](../../library/development-workflow/) — `0.2.0-draft`
  <!-- ctx:source id="c4c94726-3cc7-4df6-b779-72bbf9c06f40" version="0.2.0-draft" -->

## Local Rules

### Compiler architecture

- **Deterministic skeleton, semantic intelligence on top:** Prefer deterministic mechanisms whenever behavior can be specified and computed exactly; use LLMs only for work that genuinely requires semantic interpretation.
  Why: Deterministic structure provides reproducibility and auditability, while LLM reasoning is most valuable where meaning rather than mechanics must be understood.
  <!-- ctx:rule id="CCI-001" -->

- **Keep compiler stages separated:** Keep the compiler pipeline explicit: `parser.py` parses authoring syntax into `model.py` structures; `compiler.py` resolves and composes semantics; `render.py` produces deterministic text; `outputs.py` compares or writes generated files; `cli.py` only orchestrates commands.
  Why: Narrow one-way stages make compiler behavior easier to reason about, test, and debug without letting filesystem or presentation concerns leak into semantic truth.
  <!-- ctx:rule id="CCI-005" -->

### Onboarding trust

- **Keep new Node identity independent from Evidence identity:** A newly onboarded Context Node must receive human-owned stable identity; when ContextCanon generates that identity it creates a fresh UUID once and stores it in review state rather than deriving it from the Evidence digest.
  Why: Evidence identifies the exact bytes reviewed, while Node identity identifies one continuing project context; unrelated projects can contain identical evidence and must remain independent Nodes.
  <!-- ctx:rule id="CCI-006" -->

- **Bind reusable Sources to the exact reviewed package:** An onboarding proposal that reuses an existing Source must bind the Source Node ID, name, version, normalized digest, and package digest inspected by the semantic reviewer, and final acceptance must require that same immutable package.
  Why: A different package version is a different review object even when the stable Source Node ID is unchanged; semantic review must not silently authorize content the reviewer never saw.
  <!-- ctx:rule id="CCI-007" -->

- **Do not seize project-owned paths during first adoption:** Before first onboarding publication, compile the proposed Node in staging, derive its actual compiler-owned output paths, and refuse publication when those outputs or canonical Context authoring/resource paths are already owned by the project.
  Why: Adopting ContextCanon must never silently repurpose or overwrite an existing project file merely because its path collides with a generated ContextCanon output.
  <!-- ctx:rule id="CCI-008" -->

- **Make first-adoption publication rollback-safe:** Treat first onboarding publication as one transaction-like state change; if publication fails before the acceptance record is complete, remove only the canonical/generated state and Source packages newly created by that failed attempt while preserving pre-existing accepted state.
  Why: An operator should be able to fix the failure and retry without first reconstructing whether the repository was left half-adopted.
  <!-- ctx:rule id="CCI-009" -->

### Development method

- **Validate vertically before hardening:** Validate ContextCanon through concrete repository use cases before hardening abstractions into compiler code.
  Why: Simple real workflows should shape the framework; implementation convenience must not force unnecessary ceremony on users.
  <!-- ctx:rule id="CCI-002" -->

- **Repository documentation is the design record:** Treat the repository documentation as the canonical design record once a decision is accepted; do not rely on reconstructing architecture from chat history.
  Why: ContextCanon itself should demonstrate durable, reviewable project context.
  <!-- ctx:rule id="CCI-003" -->

- **Prefer uv for ContextCanon development and tool installation:** Use `uv` instead of direct `pip` installation when the required workflow is supported. For the current Windows development environment, prefer a dedicated PowerShell 7.x window and install a review branch or exact commit as a globally available uv tool with `uv tool install --force "git+https://github.com/SomeSunlight/context-canon.git@<ref>"`. Keep commands and implementation portable so Windows/PowerShell remains an operator environment, not a ContextCanon platform requirement; use another installer only when `uv` is unavailable or unsuitable for the concrete task.
  Why: A uv-managed tool install has proven more repeatable for the real ContextCanon operator workflow and avoids repeatedly reintroducing environment-specific `pip` setup across development sessions, while the framework itself must remain usable on other operating systems and shells.
  <!-- ctx:rule id="CCI-010" -->

### Node library

- **Keep reusable Node dependencies explicit:** A reusable Node in the ContextCanon Node Library composes Foundation only when its own semantics actually depend on Foundation. Standalone reusable Nodes remain independent, and consumers compose Foundation alongside them when both are wanted.
  Why: Reuse should not force unrelated transitive governance on consumers; explicit independent Sources are simpler than requiring consumers to remove a baseline that a reusable Node never needed.
  <!-- ctx:rule id="CCI-004" -->

## Local Topics

### Compiler implementation

When changing, debugging, reviewing, or extending the deterministic compiler implementation, parser grammar, semantic composition, rendering, generated-output handling, CLI, or compiler behavior:

Required:
- Resource: `docs/compiler.md`
<!-- ctx:topic id="CCI-TOPIC-COMPILER" -->

### Tests and CI

When changing or reviewing tests, GitHub Actions, repository consistency checks, self-hosted generated-package drift verification, or when diagnosing why a pull-request check failed, first understand the two test levels: deterministic behavior tests and exact generated-output drift checking.

Required:
- Resource: `docs/tests-and-ci.md`
<!-- ctx:topic id="CCI-TOPIC-TESTS" -->

### Development workflow

When planning, resuming, checkpointing, testing, regenerating ContextCanon's own generated packages, installing a ContextCanon development build, or preparing a ContextCanon development block for project-owner review:

Required:
- Context Node: `../../library/development-workflow/`
<!-- ctx:topic id="CCI-TOPIC-DEVELOPMENT-WORKFLOW" -->

### Framework architecture

When changing the compiler boundary, package model, Node structure, deterministic/semantic split, or generated artifacts:

Required:
- Resource: `docs/architecture.md`
- Resource: `docs/use-case-walkthrough.md`

Optional:
- Resource: `docs/concepts.md`
<!-- ctx:topic id="CCI-TOPIC-ARCHITECTURE" -->

### Reviewed project onboarding

When changing onboarding inventory, evidence capture, semantic classification, proposal review/acceptance, or extraction of reusable context from an existing project:

Required:
- Resource: `docs/onboarding-reference.md`
<!-- ctx:topic id="CCI-TOPIC-ONBOARDING" -->

### Source and official formats

When changing authoring syntax, IDs, Topics, Changes, official entry views, or machine representation:

Required:
- Resource: `../../library/foundation/docs/source-format.md`
- Resource: `../../library/foundation/docs/official-context.md`
- Resource: `../../library/foundation/docs/topics.md`
<!-- ctx:topic id="CCI-TOPIC-FORMATS" -->

### Composition

When changing Source composition, version acceptance, conflicts, removes, overrides, exceptions, or multi-Node repositories:

Required:
- Resource: `../../library/foundation/docs/composition.md`
- Resource: `docs/use-case-walkthrough.md`
<!-- ctx:topic id="CCI-TOPIC-COMPOSITION" -->

### Harness integration

When changing `AGENTS.md`, `.goosehints`, or another model/harness adapter:

Required:
- Resource: `../../library/foundation/docs/harnesses.md`
<!-- ctx:topic id="CCI-TOPIC-HARNESSES" -->

### State and planning

When deciding whether information belongs in current state, planning, governance, or history:

Required:
- Resource: `docs/state.md`
<!-- ctx:topic id="CCI-TOPIC-STATE" -->
