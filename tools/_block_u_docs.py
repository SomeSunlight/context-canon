from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "docs/onboarding.md"
text = PATH.read_text(encoding="utf-8")


def exact(old: str, new: str, count: int = 1) -> None:
    global text
    actual = text.count(old)
    if actual != count:
        raise SystemExit(f"docs/onboarding.md: expected {count}, found {actual}: {old[:120]!r}")
    text = text.replace(old, new, count)


def section(start_heading: str, next_heading: str, replacement: str) -> None:
    global text
    pattern = re.compile(rf"(?ms)^{re.escape(start_heading)}\n.*?(?=^{re.escape(next_heading)}\n)")
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise SystemExit(f"docs/onboarding.md: section {start_heading!r} found {len(matches)} times")
    match = matches[0]
    text = text[:match.start()] + replacement.rstrip() + "\n\n" + text[match.end():]


exact(
'''ContextCanon previews/materializes only missing Node skeletons
        ↓
strong reasoning LLM places existing knowledge into that accepted structure
        ↓
human reviews STEP-07-placement.md with exact source excerpts
        ↓
only later: reviewed publication / cleanup / duplicate removal''',
'''ContextCanon previews/materializes only missing Node skeletons
        ↓
human configures reusable Context catalog + sparse assignments in STEP-05
        ↓
strong reasoning LLM places existing knowledge into the already composed structure
        ↓
human reviews STEP-08-placement.md with exact source excerpts
        ↓
publication preview → explicit publish → later duplicate cleanup'''
)

exact(
'''As soon as Step 2 opens `contextcanon-onboarding/`, use **`contextcanon-onboarding/PLAN.md` as the executable console for that run**. ContextCanon writes the exact snapshot-bound commands there, including remembered `--catalog-package` inputs, the one-time `--owner-source` choice, the current validated checkpoint, and reset commands. Copy those commands instead of rebuilding them from this documentation, terminal history, or chat history.

`contextcanon-onboarding/README.md` remains the stable orientation page. `PLAN.md` is the thing to follow while doing the onboarding.''',
'''As soon as Step 2 opens `contextcanon-onboarding/`, use **`contextcanon-onboarding/PLAN.md` as the executable console for that run**. Each numbered STEP keeps its short title, beginner-oriented explanation, completion checkbox, exact command, and artifact guidance together. The PLAN is orchestration only: it deliberately does **not** become a second configuration file for Catalog paths, Source identities, or project decisions.

Reusable Context configuration lives in `STEP-05-reusable-contexts.md`, where it belongs. ContextCanon keeps exact IDs, digests, and remembered machine state behind that human gate. `contextcanon-onboarding/README.md` remains the stable orientation page; `PLAN.md` tells you what to do next.'''
)

exact(
'''`contextcanon-onboarding/PLAN.md` is the operator console for the in-progress onboarding. It contains the nine numbered steps, exact copy/paste commands for the current snapshot, both external-LLM handoffs, both human review gates, reset commands, and the latest ContextCanon-validated checkpoint. When returning after a pause, start there rather than reconstructing the command sequence from memory. `README.md` explains the workspace and points back to the PLAN.''',
'''`contextcanon-onboarding/PLAN.md` is the operator console for the in-progress onboarding. It contains the ten numbered steps, with each step's explanation, checkbox, exact copy/paste command, and artifact guidance in one place, plus the external-LLM handoffs, human gates, reset commands, and latest ContextCanon-validated checkpoint. When returning after a pause, start there rather than reconstructing the command sequence from memory. `README.md` explains the workspace and points back to the PLAN.'''
)

section(
    "## 5. Generate the content-placement assignment",
    "## Legacy single-pass first adoption",
    r'''## 5. Select reusable Contexts

The project's own shelves now exist. Before asking an LLM to place the books, establish any **reusable external Context Nodes** that should already apply to those shelves.

Run:

```text
contextcanon onboard reusable-contexts \
  .context/onboarding/<evidence-digest>
```

The first run creates:

```text
contextcanon-onboarding/STEP-05-reusable-contexts.md
```

This is a human-owned configuration/review surface, not part of the PLAN. It has three jobs:

1. **Catalog locations** — directories in which ContextCanon may discover compiled reusable Context Nodes;
2. **Assignments** — only the reusable relationships that should actually exist; there is deliberately no project-node × catalog-node matrix;
3. **Why** — the durable reason that each reusable Context applies at that project Node.

A typical edit looks like:

```markdown
## Catalog locations — editable

- `C:\Users\me\PycharmProjects\context-canon\nodes\library`

## Assignments — editable

Decision: `accept`

- **AI Workstation** (`.`) ← **Development Workflow** (`0.2.0-draft`)
  Why: Shared development workflow applies to the whole project.
```

Run the **same command again** after editing. ContextCanon scans the Catalog locations, fully verifies compiled packages, renders the available project/reusable Nodes for reference, resolves the human-readable assignment to stable IDs and exact package digests, and stores the validated machine state. You should not type Source UUIDs or package digests into the assignment.

An empty assignment list is valid: a project may simply have no reusable Contexts. Set `Decision: `accept`` only when the Catalog and sparse relationships are what you intend.

The relationship `Why` is not a Rule. A Rule says **what applies**; the Source relationship rationale says **why this whole reusable Context was composed here**. Publication carries that Why into local Source authoring and immutable import provenance, so descendants can later explain why an inherited reusable Context is in scope.

This gate deliberately happens **before** placement reasoning. The placement LLM therefore sees which reusable context already exists and can avoid promoting the same generic guidance again as a duplicate local Rule.

## 6. Generate the content-placement assignment

The second semantic pass is bound to the exact frozen Evidence, the human-edited project structure, and the exact reusable Context state accepted in Step 5:

```text
contextcanon onboard placement-instruction \
  .context/onboarding/<evidence-digest>
```

ContextCanon writes `contextcanon-onboarding/STEP-06a-placement-instruction.md`. Give that instruction and **only the same frozen `evidence/` tree** to a strong reasoning LLM. Save its single JSON response as `contextcanon-onboarding/STEP-06b-placement-proposal.json`.

The placement question is no longer "where is this text today?". It is:

> **Where should this meaning be maintained from now on?**

The v1 proposal distinguishes:

- `overview` — short stable orientation about what a Node owns;
- `rule` — durable project-local governance;
- `topic-resource` — deeper Markdown maintained at its natural repository path and routed to by a Topic;
- `state` / `plan` — current situation or future work, kept distinct from inherited governance;
- `ordinary-documentation` — useful documents that remain ordinary documents;
- `authority-mapping` — a local interpretation of Markdown deliberately marked fixed/authoritative in `STEP-03-structure.md`;
- `unresolved` — ambiguity that must remain visible.

Actions are deliberately narrow:

- `promote` — make the destination ContextCanon surface the **single canonical maintenance surface** for the reviewed meaning. Initial publication may temporarily leave original mutable prose untouched for migration safety, but that duplicate is transitional;
- `reference` — only for `topic-resource`; keep referenced Markdown as the maintenance surface and store routing rather than a copied second meaning;
- `keep` — intentionally remain outside canonical Node authoring;
- `map` — preserve fixed Markdown as authority while recording the reviewed local relationship to it.

The non-redundancy goal is **one canonical meaning, many useful routes**. After promoted meaning is safely canonical, reviewed cleanup can remove true duplicates or leave a concise orientation/summary plus a link.

Preserve precise existing wording for facts, constraints, and Rules when it is already the best canonical wording. **Overview is a condensation task, not a quotation task:** summarize durable responsibility sharply and keep volatile compatibility detail in local State. Prefer several atomic findings over one long snake sentence.

The human cockpit has one additional safety net: when a promoted finding has one unambiguous mutable Markdown range but the LLM proposes no Source After edit, `STEP-08-placement.md` exposes that exact range as an optional human override. It defaults to `reject`, so it never creates cleanup work by itself.

### Mutable and fixed Markdown

Ordinary `project-documentation` Markdown is mutable by default. Markdown proposed as `authoritative-reference` or `imported-corpus` is preselected as fixed in `STEP-03-structure.md`, and the project owner can correct that list before placement.

- **mutable** means ContextCanon may become the future owner of promoted meaning, but the first publication still does not delete or rewrite the old document;
- **fixed** means the document remains authoritative and may only be referenced/mapped by this onboarding flow.

Non-Markdown document authorities such as PDF/Word are deliberately unsupported in this version rather than hidden behind an implicit conversion mechanism.

## 7. Validate the placement proposal

Validate the LLM result:

```text
contextcanon onboard placement-validate \
  .context/onboarding/<evidence-digest>
```

ContextCanon checks the proposal against the frozen Evidence, accepted project structure, and exact reusable Context packages from Step 5. There is intentionally no separate Step-07 artifact.

## 8. Review and revalidate `STEP-08-placement.md`

Create/load the human review:

```text
contextcanon onboard placement-review \
  .context/onboarding/<evidence-digest>
```

`STEP-08-placement.md` is the **human-owned placement decision file**, not merely a rendered report. Each project finding is destination-first: destination, decision, kind/action, maintained meaning, proposal rationale, and exact Evidence excerpts.

The owner may edit destination, decision, title, supported kind/action semantics, maintained wording, and review note directly in Markdown. ContextCanon allocates stable authoring identity once and preserves it across reloads.

Reusable Context assignments already accepted in Step 5 are **not another selection matrix here**. They appear only as compact traceability. If frozen Evidence suggests a genuinely new reusable relationship that was not established in Step 5, that proposal remains an explicit human decision rather than being silently adopted.

Every successful placement-review validation regenerates read-only `STEP-08a-source-audit.md`, grouping source-before/source-after transformations by original file/range so semantic loss is easy to inspect.

## 9. Preview exact publication before mutation

Once every placement decision is resolved:

```text
contextcanon onboard placement-preview \
  .context/onboarding/<evidence-digest>
```

The command writes `contextcanon-onboarding/STEP-09-placement-preview.md` and changes no project file. The preview shows exact `CONTEXT.src.md` deltas, semantic Parent pins, reusable Source installation/provenance, accepted follow-ups, and reviewed mutable-document changes.

Preview verifies live Evidence-covered bytes and current Node source bytes. Publication later refuses if those inputs changed after preview.

## 10. Explicitly publish the reviewed placement

After reviewing the preview:

```text
contextcanon onboard placement-publish \
  .context/onboarding/<evidence-digest>
```

Publication transactionally materializes the semantics represented by the reviewed ContextCanon grammar: accepted local Overview/Rules/Topics/Resources, local State/Plan where supported, semantic Parent pins, and accepted exact reusable Sources. Existing Node identity and unrelated authored content are preserved.

The command writes `contextcanon-onboarding/STEP-10-placement-followup.md`. Generated Node `CONTEXT.md` files then expose inherited context and reusable provenance; a direct reusable Source's Why remains visible through immutable imported-context provenance in descendants.

Normal onboarding after Step 5 no longer asks the operator to repeat Catalog paths, Source Node IDs, or one-time Source-selection CLI syntax. ContextCanon retains those exact machine identities behind the accepted human gate.

### Visible workspace after the ten-step path

A typical workspace is:

```text
contextcanon-onboarding/
├── README.md
├── PLAN.md
├── STEP-02a-structure-instruction.md
├── STEP-02b-structure-proposal.json
├── STEP-03-structure.md
├── STEP-04-structure-preview.md
├── STEP-05-reusable-contexts.md
├── STEP-06a-placement-instruction.md
├── STEP-06b-placement-proposal.json
├── STEP-08-placement.md
├── STEP-08a-source-audit.md
├── STEP-09-placement-preview.md
└── STEP-10-placement-followup.md
```

The visible workspace has a ContextCanon ownership marker. If a directory with the same name already exists without that marker, ContextCanon refuses to take it over; use `--workspace <path>` instead.
'''
)

exact(
'''prepare                Which exact project bytes may be considered?
structure instruction  What coarse semantic task is being asked?
reasoning LLM           What knowledge areas seem to exist?
structure validate      Does the proposal honestly cite those exact bytes?
human structure edit    What is the project's intended mental model?
preview/materialize     Which Node identities/files would actually be created?
placement instruction  Where should existing knowledge live in that model?
reasoning LLM           What placements/reuses seem justified by Evidence?
placement validate      Is that exact JSON bound to Evidence + structure + Sources?
human placement review  Do these moves/references/mappings actually make sense?
later publication       Which reviewed changes may safely become canonical?''',
'''prepare                  Which exact project bytes may be considered?
structure instruction    What coarse semantic task is being asked?
reasoning LLM             What knowledge areas seem to exist?
structure validate        Does the proposal honestly cite those exact bytes?
human structure edit      What is the project's intended mental model?
preview/materialize       Which Node identities/files would actually be created?
reusable Context review   Which external Contexts apply to which shelves, and why?
placement instruction    Where should remaining project knowledge live?
reasoning LLM             What placements seem justified by Evidence?
placement validate        Is that JSON bound to Evidence + structure + accepted reusable Contexts?
human placement review    Do these moves/references/mappings actually make sense?
preview + publication     Which reviewed changes may safely become canonical?'''
)

exact(
'''The structure/placement contracts are still being validated through the real `ai-workstation` exercise. They should be promoted into the technical reference only after this vertical test settles their semantics rather than documenting an abstraction before it survives use.''',
'''The structure-first/reusable-context/placement contracts are validated through the real `ai-workstation` exercise in PR #13. The older single-pass technical reference remains useful for its trust-boundary details; the ten-step walkthrough on this page is the current human-facing structure-first path.'''
)

exact(
'''State and Plan are local first-class Node authoring: accepted placement findings of those kinds are written to `## State` and `## Plan` in the destination `CONTEXT.src.md` and therefore appear in generated `CONTEXT.md`. They are intentionally not inherited through reusable Sources; current project situation and future project work stay local to the Node that owns them.''',
'''State and Plan are local first-class Node authoring: accepted placement findings of those kinds are written to `## Local State` and `## Local Plan` in the destination `CONTEXT.src.md` and therefore appear in generated `CONTEXT.md`. They are intentionally not inherited through reusable Sources; current project situation and future project work stay local to the Node that owns them.'''
)

PATH.write_text(text, encoding="utf-8", newline="\n")

# Permanent contract: the first-user walkthrough must describe the same human
# flow as the generated PLAN, without reintroducing legacy operator plumbing.
(ROOT / "tests" / "test_onboarding_walkthrough_current.py").write_text(
    '''from __future__ import annotations\n\nfrom pathlib import Path\nimport unittest\n\n\nROOT = Path(__file__).resolve().parents[1]\n\n\nclass OnboardingWalkthroughCurrentTests(unittest.TestCase):\n    def test_walkthrough_matches_human_first_ten_step_flow(self) -> None:\n        text = (ROOT / "docs" / "onboarding.md").read_text(encoding="utf-8")\n        self.assertIn("## 5. Select reusable Contexts", text)\n        self.assertIn("STEP-05-reusable-contexts.md", text)\n        self.assertIn("sparse relationships", text)\n        self.assertIn("Why this whole reusable Context", text)\n        self.assertIn("## 6. Generate the content-placement assignment", text)\n        self.assertIn("STEP-06a-placement-instruction.md", text)\n        self.assertIn("## 8. Review and revalidate `STEP-08-placement.md`", text)\n        self.assertIn("STEP-09-placement-preview.md", text)\n        self.assertIn("STEP-10-placement-followup.md", text)\n        self.assertIn("PLAN is orchestration only", text)\n        current = text.split("## Legacy single-pass first adoption", 1)[0]\n        self.assertNotIn("--owner-source", current)\n        self.assertNotIn("--catalog-package", current)\n        self.assertNotIn("STEP-07-placement.md", current)\n        self.assertNotIn("STEP-05a-placement-instruction.md", current)\n\n\nif __name__ == "__main__":\n    unittest.main()\n''',
    encoding="utf-8",
    newline="\n",
)
