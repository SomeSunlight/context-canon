from __future__ import annotations

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
        raise SystemExit(f"{rel}: expected one occurrence, found {count}: {old[:140]!r}")
    write(rel, text.replace(old, new, 1))


replace_once(
    "src/contextcanon/onboarding_reusable_contexts.py",
    '''        if match is None:\n            raise _error(\n                "Assignments must use '- **Project Node** (`path`) ← **Reusable Context** (`version`)' "\n                "followed by an indented 'Why:' line"\n            )\n''',
    '''        if match is None:\n            raise _error(\n                "Assignment first line is incomplete. Copy one complete line from "\n                "'Copy-ready Assignment lines — generated' below, paste it into Assignments, "\n                "then add an indented 'Why:' line"\n            )\n''',
)

replace_once(
    "src/contextcanon/onboarding_reusable_contexts.py",
    '''            "Only list relationships that should actually exist; there is deliberately no project-node × catalog-node matrix. Copy the human-readable names/path/version from the generated lists below. Every relationship needs a durable `Why`.",\n''',
    '''            "Only keep relationships that should actually exist. Copy one complete first line from `Copy-ready Assignment lines — generated` below, paste it here, then add an indented `Why:` line. The generated copy helpers are syntax options, not recommendations; the editable list remains sparse. Every relationship needs a durable `Why`.",\n''',
)

replace_once(
    "src/contextcanon/onboarding_reusable_contexts.py",
    '''    lines.extend(\n        [\n            GENERATED_CATALOG_END,\n            "",\n            "The generated package identities are review information. Do not copy their IDs or digests into Assignments; ContextCanon resolves and remembers them for subsequent steps.",\n            "",\n        ]\n    )\n    return "\\n".join(lines)\n''',
    '''    lines.extend(\n        [\n            GENERATED_CATALOG_END,\n            "",\n            "The generated package identities are review information. Do not copy their IDs or digests into Assignments; ContextCanon resolves and remembers them for subsequent steps.",\n            "",\n            "## Copy-ready Assignment lines — generated",\n            "",\n            "These are syntactic copy helpers, not recommendations. Copy one desired complete line into the editable Assignments section above and add an indented `Why:` line below it.",\n            "",\n        ]\n    )\n    if packages:\n        for package in packages:\n            lines.append(f"### {package.metadata.name} (`{package.metadata.version}`)")\n            lines.append("")\n            for node in structure.nodes:\n                lines.append(\n                    f"- **{node.name}** (`{node.path}`) ← **{package.metadata.name}** (`{package.metadata.version}`)"\n                )\n            lines.append("")\n    elif locations:\n        lines.extend(["No verified reusable Context Nodes are available for copy-ready assignments.", ""])\n    else:\n        lines.extend(["Add a Catalog location above and rerun STEP 05 to generate copy-ready assignment lines.", ""])\n    return "\\n".join(lines)\n''',
)

# Regression: after catalog discovery, the generated lower section must contain
# directly pasteable assignment first lines for every visible project Node.
tests = read("tests/test_onboarding_reusable_contexts.py")
needle = '''            canonical = workspace_file.read_text(encoding="utf-8")\n            self.assertIn(f"- `{catalog}`", canonical)\n\n'''
replacement = '''            canonical = workspace_file.read_text(encoding="utf-8")\n            self.assertIn(f"- `{catalog}`", canonical)\n            self.assertIn("## Copy-ready Assignment lines — generated", canonical)\n            self.assertIn(\n                "- **AI Workstation** (`.`) ← **Development Workflow** (`0.2.0-draft`)",\n                canonical,\n            )\n            self.assertIn(\n                "- **Bootstrap** (`bootstrap`) ← **Development Workflow** (`0.2.0-draft`)",\n                canonical,\n            )\n\n'''
if needle not in tests:
    raise SystemExit("tests: canonical STEP-05 assertion insertion point missing")
tests = tests.replace(needle, replacement, 1)
write("tests/test_onboarding_reusable_contexts.py", tests)

plan = read("PLAN.md")
block = '''\n\n## Final owner-UX correction: copy-ready STEP-05 assignments\n\nPurpose: remove the remaining grammar reconstruction from STEP 05. The generated project/source lists looked copyable, but a copied project-node line was not a valid Assignment because the Source name/version were missing.\n\n- [x] Keep Assignment parsing semantically strict: ContextCanon must not guess which reusable Context a partial project-node line intended.\n- [x] Render a generated `Copy-ready Assignment lines` section whose lines already use the exact valid Assignment first-line syntax, grouped by reusable Context.\n- [x] Make clear that these generated pairings are syntax helpers rather than recommendations; the editable Assignment list remains sparse and human-selected.\n- [x] Point incomplete-Assignment errors directly at the copy-ready section instead of restating grammar the operator must reconstruct.\n- [ ] Run focused regressions, complete deterministic suite, self-build/check, diff hygiene and cleanup; then hand the exact clean PR head back to the owner for the continued real `ai-workstation` STEP-05 test. PR remains draft/unmerged.\n'''
if "## Final owner-UX correction: copy-ready STEP-05 assignments" not in plan:
    write("PLAN.md", plan.rstrip() + block + "\n")

state = read("STATE.md")
state_block = '''\n\n## Latest STEP-05 assignment-copy owner-test correction\n\nThe next real owner interaction exposed a presentation/grammar mismatch: the generated project Context Node list looked like material intended to be copied upward, but its lines contained only the Assignment target. Pasting such a line into the editable Assignment section necessarily failed because the reusable Context name/version were absent.\n\nSTEP 05 now renders complete copy-ready Assignment first lines after Catalog discovery. They are grouped by reusable Context and pair each visible project Node with that Source using exactly the syntax the parser accepts. The list is explicitly a syntactic copy aid, not a semantic recommendation or preselection. ContextCanon deliberately does not infer a Source from an incomplete line; instead the error points directly to the generated copy-ready section. The operator copies one complete line, adds the durable `Why:`, and keeps only the relationships that should actually exist.\n'''
if "## Latest STEP-05 assignment-copy owner-test correction" not in state:
    write("STATE.md", state.rstrip() + state_block + "\n")
