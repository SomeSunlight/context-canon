from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def write(rel: str, text: str) -> None:
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def replace_once(rel: str, old: str, new: str) -> None:
    text = read(rel)
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{rel}: expected one occurrence, found {count}: {old[:120]!r}")
    write(rel, text.replace(old, new, 1))


def replace_function(rel: str, name: str, new: str) -> None:
    text = read(rel)
    pattern = re.compile(rf"(?ms)^def {re.escape(name)}\(.*?(?=^def |\Z)")
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise SystemExit(f"{rel}: expected one function {name}, found {len(matches)}")
    match = matches[0]
    write(rel, text[:match.start()] + new.rstrip() + "\n\n" + text[match.end():])


replace_function(
    "src/contextcanon/onboarding_reusable_contexts.py",
    "_catalog_locations",
    r'''def _catalog_locations(text: str) -> tuple[str, ...]:
    body = _between(text, CATALOG_START, CATALOG_END, "Catalog locations")
    values: list[str] = []
    for raw in body.splitlines():
        line = raw.strip()
        if not line:
            continue

        # Human input is intentionally forgiving. A pasted path is the semantic
        # value; Markdown bullet/code/quote wrappers are only presentation.
        if line.startswith("- "):
            line = line[2:].strip()
        if len(line) >= 2 and (line[0], line[-1]) in {
            ("`", "`"),
            ('"', '"'),
            ("'", "'"),
        }:
            line = line[1:-1].strip()

        if not line:
            raise _error("Catalog location cannot be empty")
        if line.startswith("<!--"):
            raise _error("Catalog locations must contain paths, not machine markers")
        if line not in values:
            values.append(line)
    return tuple(values)
''',
)

replace_once(
    "src/contextcanon/onboarding_reusable_contexts.py",
    '''        "## Catalog locations — editable",\n        "",\n        "Add one directory containing reusable compiled Context Nodes per line. A location may itself be one Context Node or a directory containing several Nodes.",\n        "",\n        CATALOG_START,''',
    '''        "## Catalog locations",\n        "",\n        "Add one directory containing reusable compiled Context Nodes per line. A location may itself be one Context Node or a directory containing several Nodes.",\n        "",\n        "Paste a path normally. Markdown bullets, backticks, or quotes are optional input conveniences; ContextCanon rewrites accepted input into one canonical Markdown form on the next run.",\n        "",\n        r"Example: `C:\\Users\\you\\PycharmProjects\\context-canon\\nodes\\library`",\n        "",\n        "> ✏️ Editable Catalog locations start below.",\n        "",\n        CATALOG_START,''',
)

replace_once(
    "src/contextcanon/onboarding_reusable_contexts.py",
    '''            CATALOG_END,\n            "",\n            "## Assignments — editable",''',
    '''            CATALOG_END,\n            "",\n            "> End editable Catalog locations.",\n            "",\n            "## Assignments",''',
)

replace_once(
    "src/contextcanon/onboarding_reusable_contexts.py",
    '''            "```",\n            "",\n            f"Decision: `{decision}`",''',
    '''            "```",\n            "",\n            "> ✏️ Editable reusable-Context assignment controls start below.",\n            "",\n            f"Decision: `{decision}`",''',
)

replace_once(
    "src/contextcanon/onboarding_reusable_contexts.py",
    '''            ASSIGNMENTS_END,\n            "",\n            "Set `Decision` to `accept` when the Catalog and assignments are the intended reusable-context composition for this onboarding. An empty assignment list is valid when no reusable Context applies.",''',
    '''            ASSIGNMENTS_END,\n            "",\n            "> End editable reusable-Context assignment controls.",\n            "",\n            "Set `Decision` to `accept` when the Catalog and assignments are the intended reusable-context composition for this onboarding. An empty assignment list is valid when no reusable Context applies.",''',
)

# Focused UX regressions: exact Windows paste shape plus common wrappers and
# preview-visible editable-area affordances.
tests = read("tests/test_onboarding_reusable_contexts.py")
tests = tests.replace(
    "    load_accepted_reusable_contexts,\n    refresh_reusable_contexts,\n)",
    "    _catalog_locations,\n    load_accepted_reusable_contexts,\n    refresh_reusable_contexts,\n)",
    1,
)
needle = "    def test_accepted_assignment_is_explicit_placement_reasoning_input(self) -> None:\n"
if needle not in tests:
    raise SystemExit("tests: insertion point missing")
new_tests = r'''    def test_catalog_locations_accept_plain_windows_path_and_common_wrappers(self) -> None:
        windows_path = r"C:\Users\u239230\PycharmProjects\context-canon\nodes\library"
        variants = (
            windows_path,
            f"- {windows_path}",
            f'"{windows_path}"',
            f"- `{windows_path}`",
        )
        for value in variants:
            with self.subTest(value=value):
                text = f"{CATALOG_START}\n{value}\n{CATALOG_END}\n"
                self.assertEqual(_catalog_locations(text), (windows_path,))

    def test_step05_marks_editable_areas_visibly_and_canonicalizes_plain_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot = root / ("a" * 64)
            snapshot.mkdir()
            workspace_file = root / "STEP-05-reusable-contexts.md"
            structure = self._structure()
            catalog = self._catalog(root)

            refresh_reusable_contexts(workspace_file, snapshot, "a" * 64, structure)
            text = workspace_file.read_text(encoding="utf-8")
            self.assertIn("> ✏️ Editable Catalog locations start below.", text)
            self.assertIn("> End editable Catalog locations.", text)
            self.assertIn("> ✏️ Editable reusable-Context assignment controls start below.", text)
            self.assertIn("> End editable reusable-Context assignment controls.", text)
            self.assertIn(r"Example: `C:\Users\you\PycharmProjects\context-canon\nodes\library`", text)

            text = text.replace(
                CATALOG_START + "\n" + CATALOG_END,
                CATALOG_START + f"\n{catalog}\n" + CATALOG_END,
            )
            workspace_file.write_text(text, encoding="utf-8")
            plan, created = refresh_reusable_contexts(workspace_file, snapshot, "a" * 64, structure)
            self.assertFalse(created)
            self.assertEqual(plan.catalog_locations, (str(catalog),))
            canonical = workspace_file.read_text(encoding="utf-8")
            self.assertIn(f"- `{catalog}`", canonical)

'''
tests = tests.replace(needle, new_tests + needle, 1)
write("tests/test_onboarding_reusable_contexts.py", tests)

# Make the preview-visible affordance a durable ContextCanon development rule,
# rather than relying on memory when the next human-gate Markdown surface is added.
replace_once(
    "nodes/internal/framework-development/CONTEXT.src.md",
    '''- **Repository documentation is the design record:** Treat the repository documentation as the canonical design record once a decision is accepted; do not rely on reconstructing architecture from chat history.\n  Why: ContextCanon itself should demonstrate durable, reviewable project context.\n  <!-- ctx:rule id="CCI-003" -->\n''',
    '''- **Repository documentation is the design record:** Treat the repository documentation as the canonical design record once a decision is accepted; do not rely on reconstructing architecture from chat history.\n  Why: ContextCanon itself should demonstrate durable, reviewable project context.\n  <!-- ctx:rule id="CCI-003" -->\n\n- **Mark human-editable generated Markdown with one visible convention:** Whenever ContextCanon generates a Markdown human gate that expects edits, mark every editable region with the same rendered `✏️ Editable ...` / `End editable ...` cues in addition to machine-only markers; HTML comments or heading wording must never be the only indication of editability.\n  Why: Operators often review Markdown in preview mode where HTML comments disappear. One repeated visual grammar makes the workflow scannable and prevents each new review surface from inventing its own hidden interaction contract.\n  <!-- ctx:rule id="CCI-011" -->\n''',
)

plan = read("PLAN.md")
block = r'''

## Final owner-UX correction: forgiving STEP-05 path input and visible edit grammar

Purpose: fix the first real STEP-05 owner run, where the machine accepted only one exact Markdown spelling for a Catalog path and the new human gate failed to use the established preview-visible editable-area convention.

- [x] Treat a Catalog location as a human-entered path value rather than Markdown syntax: accept plain pasted paths plus optional bullet/backtick/quote wrappers, then rewrite to canonical `- `PATH`` presentation on rerun.
- [x] Put a concrete Windows Catalog example beside the input and improve the error boundary so the operator does not have to guess quoting syntax.
- [x] Mark STEP-05 Catalog and assignment controls with the same rendered `✏️ Editable ...` / `End editable ...` visual grammar already used in placement review.
- [x] Add a ContextCanon framework-development Rule requiring visible, consistent editable-region affordances in generated human-gate Markdown; machine-only HTML markers are insufficient.
- [ ] Run focused regressions, complete deterministic suite, self-build/check, diff hygiene and cleanup; then hand the exact clean PR head back to the owner for the continued real `ai-workstation` STEP-05 test. PR remains draft/unmerged.
'''
if "## Final owner-UX correction: forgiving STEP-05 path input and visible edit grammar" not in plan:
    write("PLAN.md", plan.rstrip() + block + "\n")

state = read("STATE.md")
state_block = r'''

## Latest STEP-05 path-input owner-test correction

The first real reusable-Contexts human gate exposed two UX defects despite the underlying Source model being correct. Catalog input was parsed as one exact Markdown spelling (`- `PATH``) rather than as a path value, so an ordinary pasted Windows path failed with a formatting error. STEP-05 also used headings and invisible HTML markers instead of the preview-visible editable-region cues already established in placement review.

The correction makes Catalog path input forgiving and canonicalizing: plain path, optional Markdown bullet, and optional quote/backtick wrappers are accepted as equivalent human input, then the rerendered file uses the canonical Markdown form. STEP-05 now gives a concrete Windows example and visibly brackets both editable regions with the shared `✏️ Editable ...` / `End editable ...` grammar. The framework-development Context now records this as an explicit rule for future generated human gates so preview-mode users do not have to infer editability from hidden comments.
'''
if "## Latest STEP-05 path-input owner-test correction" not in state:
    write("STATE.md", state.rstrip() + state_block + "\n")
