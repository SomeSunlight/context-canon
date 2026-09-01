from __future__ import annotations

import sys
from pathlib import Path


def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    Path(path).write_text(text, encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f"missing patch anchor: {label}")
    return text.replace(old, new, 1)


PLAN_BLOCK = """

#### Block K — publish State and Plan as local Node authoring

Purpose: finish onboarding as a real operational starting point by making reviewed current state and future plan first-class local Context content instead of migration follow-up.

- [ ] Parse local `## State` and `## Plan` sections from `CONTEXT.src.md` as first-class authored Node content.
- [ ] Render State and Plan into generated `CONTEXT.md` and expose them in deterministic local machine state without inheriting them through reusable Sources.
- [ ] Publish accepted placement `state` and `plan` findings into placement-managed State/Plan blocks in the destination Node.
- [ ] Show State/Plan honestly as `Into Node — editable` in `STEP-07-placement.md`; remove them from publication follow-up once accepted.
- [ ] Keep normalized reusable semantics stable when only Overview/State/Plan presentation changes, while exact package identity changes with generated `CONTEXT.md` bytes.
- [ ] Cover parser/compiler behavior, onboarding preview/publication, idempotency, and existing reset safety with regressions; then rerun the complete suite plus build/check.
"""


def plan() -> None:
    path = "PLAN.md"
    text = read(path).rstrip()
    if "#### Block K — publish State and Plan as local Node authoring" not in text:
        text += PLAN_BLOCK
    write(path, text.rstrip() + "\n")


def patch_model() -> None:
    path = "src/contextcanon/model.py"
    text = read(path)
    text = replace_once(
        text,
        '''    changes: tuple[RuleChange, ...] = ()\n    overview: str = ""\n''',
        '''    changes: tuple[RuleChange, ...] = ()\n    overview: str = ""\n    state: str = ""\n    plan: str = ""\n''',
        "ParsedNode state and plan",
    )
    write(path, text)


def patch_parser() -> None:
    path = "src/contextcanon/parser.py"
    text = read(path)
    text = replace_once(
        text,
        '''    overview = _parse_overview(lines, sections.get("Overview"))\n    sources = _parse_sources(lines, sections.get("Sources"), source_path)\n''',
        '''    overview = _parse_overview(lines, sections.get("Overview"))\n    state = _parse_overview(lines, sections.get("State"))\n    plan = _parse_overview(lines, sections.get("Plan"))\n    sources = _parse_sources(lines, sections.get("Sources"), source_path)\n''',
        "parse state plan sections",
    )
    text = replace_once(
        text,
        '''        tuple(topics),\n        tuple(changes),\n        overview,\n    )\n''',
        '''        tuple(topics),\n        tuple(changes),\n        overview=overview,\n        state=state,\n        plan=plan,\n    )\n''',
        "ParsedNode construction",
    )
    write(path, text)


def patch_render() -> None:
    path = "src/contextcanon/render.py"
    text = read(path)
    text = replace_once(
        text,
        '''    if compiled.parsed.overview:\n        lines.extend(["## Overview", "", *compiled.parsed.overview.splitlines(), ""])\n\n    if compiled.inherited_rules or compiled.local_rules or compiled.local_topics:\n''',
        '''    if compiled.parsed.overview:\n        lines.extend(["## Overview", "", *compiled.parsed.overview.splitlines(), ""])\n\n    if compiled.parsed.state:\n        lines.extend(["## State", "", *compiled.parsed.state.splitlines(), ""])\n\n    if compiled.parsed.plan:\n        lines.extend(["## Plan", "", *compiled.parsed.plan.splitlines(), ""])\n\n    if compiled.inherited_rules or compiled.local_rules or compiled.local_topics:\n''',
        "official State Plan rendering",
    )
    text = replace_once(
        text,
        '''    lines.extend(["", "# Elements authored in this Node's CONTEXT.src.md.", "local:"])\n    if compiled.local_rules:\n''',
        '''    lines.extend(["", "# Elements authored in this Node's CONTEXT.src.md.", "local:"])\n    lines.append("  state: " + (q(compiled.parsed.state) if compiled.parsed.state else "null"))\n    lines.append("  plan: " + (q(compiled.parsed.plan) if compiled.parsed.plan else "null"))\n    if compiled.local_rules:\n''',
        "machine State Plan rendering",
    )
    write(path, text)


def patch_instruction() -> None:
    path = "src/contextcanon/onboarding_placement_instruction.py"
    text = read(path)
    old = '''        "4. Use action `promote` when project-owned canonical Overview, Rule, State, or Plan meaning belongs at the destination. For Overview/Rule/Topic publication the Node authoring becomes the canonical maintenance surface. State/Plan are currently retained as explicit node-targeted follow-up until their local publication surface is designed; do not pretend they are already written into `CONTEXT.src.md`.",\n'''
    new = '''        "4. Use action `promote` when project-owned canonical Overview, Rule, State, or Plan meaning belongs at the destination. Overview, Rule, State and Plan promotions are published into the destination Node's `CONTEXT.src.md`; Topic/Resource references are published there as routing. The Node authoring becomes the canonical maintenance surface for promoted meaning. State describes the current local situation and Plan describes future intended work; do not leave accepted State/Plan as migration follow-up.",\n'''
    text = replace_once(text, old, new, "placement State Plan instruction")
    write(path, text)


def patch_review() -> None:
    path = "src/contextcanon/onboarding_placement_review.py"
    text = read(path)
    text = replace_once(
        text,
        '''    if kind in {"overview", "rule", "topic-resource"}:\n        heading = "### Into Node — editable"\n    elif kind in {"state", "plan"}:\n        heading = "### Node-local follow-up — editable"\n    else:\n''',
        '''    if kind in {"overview", "rule", "topic-resource", "state", "plan"}:\n        heading = "### Into Node — editable"\n    else:\n''',
        "State Plan review heading",
    )
    write(path, text)


def patch_publish() -> None:
    path = "src/contextcanon/onboarding_placement_publish.py"
    text = read(path)
    text = replace_once(
        text,
        '''_MANAGED_SECTIONS = ("overview", "sources", "rules", "topics")\n''',
        '''_MANAGED_SECTIONS = ("overview", "state", "plan", "sources", "rules", "topics")\n''',
        "managed State Plan sections",
    )
    anchor = '''def _render_rules(items: list[PlacementReviewItem]) -> str:\n'''
    helper = '''def _render_summaries(items: list[PlacementReviewItem], kind: str) -> str:\n    lines: list[str] = []\n    for item in items:\n        text = _safe_line(item.payload["text"], f"item {item.proposal_id} {kind}")\n        lines.extend([f'<!-- cc:placement-{kind} id="{item.authoring_id}" -->', f"- {text}", ""])\n    return "\\n".join(lines).rstrip()\n\n\n'''
    if anchor not in text:
        raise RuntimeError("missing patch anchor: State Plan summary renderer")
    text = text.replace(anchor, helper + anchor, 1)
    text = replace_once(
        text,
        '''    overviews = [item for item in items if item.kind == "overview"]\n    rules = [item for item in items if item.kind == "rule"]\n    topics = [item for item in items if item.kind == "topic-resource"]\n''',
        '''    overviews = [item for item in items if item.kind == "overview"]\n    states = [item for item in items if item.kind == "state"]\n    plans = [item for item in items if item.kind == "plan"]\n    rules = [item for item in items if item.kind == "rule"]\n    topics = [item for item in items if item.kind == "topic-resource"]\n''',
        "collect State Plan items",
    )
    text = replace_once(
        text,
        '''    if overviews or rules or topics or sources:\n        text = _remove_skeleton_placeholder(text)\n    text = _replace_managed_section(text, "Overview", "overview", _render_overviews(overviews))\n    text = _replace_managed_section(text, "Sources", "sources", _render_sources(sources, provenance_by_id))\n''',
        '''    if overviews or states or plans or rules or topics or sources:\n        text = _remove_skeleton_placeholder(text)\n    text = _replace_managed_section(text, "Overview", "overview", _render_overviews(overviews))\n    text = _replace_managed_section(text, "State", "state", _render_summaries(states, "state"))\n    text = _replace_managed_section(text, "Plan", "plan", _render_summaries(plans, "plan"))\n    text = _replace_managed_section(text, "Sources", "sources", _render_sources(sources, provenance_by_id))\n''',
        "publish State Plan sections",
    )
    text = replace_once(
        text,
        '''        if item.kind not in {"overview", "rule", "topic-resource"}:\n''',
        '''        if item.kind not in {"overview", "rule", "topic-resource", "state", "plan"}:\n''',
        "accept State Plan into nodes",
    )
    text = replace_once(
        text,
        '''        if item.decision == "accept" and item.kind in {"state", "plan", "ordinary-documentation", "authority-mapping", "unresolved"}\n''',
        '''        if item.decision == "accept" and item.kind in {"ordinary-documentation", "authority-mapping", "unresolved"}\n''',
        "remove State Plan followups",
    )
    text = text.replace(
        "No accepted Overview, Rule, Topic/Resource or Source changes currently touch a Context Node.",
        "No accepted Overview, State, Plan, Rule, Topic/Resource or Source changes currently touch a Context Node.",
        1,
    )
    write(path, text)


def patch_tests() -> None:
    # Core parser/compiler semantics.
    path = Path("tests/test_state_plan.py")
    path.write_text(
        '''from __future__ import annotations\n\nimport sys\nimport tempfile\nimport unittest\nfrom pathlib import Path\n\nROOT = Path(__file__).resolve().parents[1]\nsys.path.insert(0, str(ROOT / "src"))\n\nfrom contextcanon.compiler import Compiler\nfrom contextcanon.parser import parse_node\n\n\nclass StatePlanTests(unittest.TestCase):\n    def _write_source(self, root: Path, state: str, plan: str) -> None:\n        (root / "CONTEXT.src.md").write_text(\n            "# Demo Project — Local Context Source\\n"\n            '<!-- ctx:node id="12345678-1234-4234-8234-123456789abc" version="0.1.0" -->\\n\\n'\n            "## Overview\\n\\n"\n            "Stable demo orientation.\\n\\n"\n            "## State\\n\\n"\n            f"- {state}\\n\\n"\n            "## Plan\\n\\n"\n            f"- {plan}\\n",\n            encoding="utf-8",\n        )\n\n    def test_state_and_plan_are_local_official_content(self):\n        repo = Path(tempfile.mkdtemp())\n        (repo / ".git").mkdir()\n        self._write_source(repo, "Current migration is active.", "Finish onboarding before feature work.")\n\n        parsed = parse_node(repo, repo)\n        self.assertEqual(parsed.state, "- Current migration is active.")\n        self.assertEqual(parsed.plan, "- Finish onboarding before feature work.")\n\n        first = Compiler(repo).compile(repo)\n        self.assertIn("## State\\n\\n- Current migration is active.", first.official_markdown)\n        self.assertIn("## Plan\\n\\n- Finish onboarding before feature work.", first.official_markdown)\n        self.assertIn('state: "- Current migration is active."', first.machine_yaml)\n        self.assertIn('plan: "- Finish onboarding before feature work."', first.machine_yaml)\n\n        normalized = first.normalized_digest\n        package = first.package_digest\n        self._write_source(repo, "Current migration is complete.", "Start feature work.")\n        second = Compiler(repo).compile(repo)\n        self.assertEqual(second.normalized_digest, normalized)\n        self.assertNotEqual(second.package_digest, package)\n\n\nif __name__ == "__main__":\n    unittest.main()\n''',
        encoding="utf-8",
    )

    # The publication fixture already contains a State item. Add Plan and assert
    # both are now authored into the root Node instead of retained as follow-up.
    path = "tests/test_onboarding_placement_publish.py"
    text = read(path)
    insertion = '''                {\n                    "id": "P-006",\n                    "title": "README authority mapping",\n'''
    plan_item = '''                {\n                    "id": "P-007",\n                    "title": "Next reviewed work",\n                    "kind": "plan",\n                    "action": "promote",\n                    "destination_node_key": "N-001",\n                    "rationale": "The next intended work belongs in the root Node plan.",\n                    "confidence": "medium",\n                    "evidence": [{"path": "README.md", "sha256": readme.sha256, "start_line": 4, "end_line": 4}],\n                    "payload": {"text": "Continue Goose changes through reviewed pull requests.", "wording_origin": "synthesized"},\n                },\n'''
    if insertion not in text:
        raise RuntimeError("missing patch anchor: publication Plan fixture")
    text = text.replace(insertion, plan_item + insertion, 1)
    text = replace_once(
        text,
        '''        self.assertEqual({item.kind for item in preview.followups}, {"state", "authority-mapping"})\n''',
        '''        self.assertEqual({item.kind for item in preview.followups}, {"authority-mapping"})\n        root = next(delta for delta in preview.nodes if delta.key == "N-001")\n        self.assertIn("## State", root.after)\n        self.assertIn("Migration is in progress.", root.after)\n        self.assertIn("## Plan", root.after)\n        self.assertIn("Continue Goose changes through reviewed pull requests.", root.after)\n''',
        "preview State Plan expectations",
    )
    text = replace_once(
        text,
        '''        self.assertIn("contextcanon-placement-rules:start", root_text)\n''',
        '''        self.assertIn("contextcanon-placement-rules:start", root_text)\n        self.assertIn("contextcanon-placement-state:start", root_text)\n        self.assertIn("contextcanon-placement-plan:start", root_text)\n        parsed_root = parse_node(repo, repo)\n        self.assertIn("Migration is in progress.", parsed_root.state)\n        self.assertIn("Continue Goose changes through reviewed pull requests.", parsed_root.plan)\n''',
        "published State Plan expectations",
    )
    text = replace_once(
        text,
        '''        self.assertEqual({item["kind"] for item in payload["followups"]}, {"state", "authority-mapping"})\n''',
        '''        self.assertEqual({item["kind"] for item in payload["followups"]}, {"authority-mapping"})\n''',
        "acceptance followup expectation",
    )
    write(path, text)

    # Human review must no longer call State/Plan a follow-up.
    path = "tests/test_onboarding_placement_review.py"
    text = read(path)
    marker = '\n\nif __name__ == "__main__":'
    extra = '''\n    def test_state_and_plan_are_rendered_as_into_node(self):\n        prepared, workspace, source_root, package, proposal, _, _ = self.make_review(owner_source=False)\n        rendered = workspace.placement_path.read_text(encoding="utf-8")\n        # The shared fixture may not contain State/Plan, so verify the renderer's\n        # classification contract directly through its source-visible heading rule.\n        from contextcanon.onboarding_placement_review import _render_payload\n        for kind in ("state", "plan"):\n            lines = _render_payload(kind, {"text": "Example", "wording_origin": "synthesized"})\n            self.assertEqual(lines[0], "### Into Node — editable")\n'''
    if "test_state_and_plan_are_rendered_as_into_node" not in text:
        text = text.replace(marker, extra + marker)
    write(path, text)


def patch_docs() -> None:
    path = "docs/onboarding.md"
    text = read(path)
    addition = (
        "\nState and Plan are local first-class Node authoring: accepted placement findings of those kinds are written to "
        "`## State` and `## Plan` in the destination `CONTEXT.src.md` and therefore appear in generated `CONTEXT.md`. "
        "They are intentionally not inherited through reusable Sources; current project situation and future project work stay local to the Node that owns them.\n"
    )
    if "State and Plan are local first-class Node authoring" not in text:
        text = text.rstrip() + "\n" + addition
    write(path, text.rstrip() + "\n")


def apply() -> None:
    patch_model()
    patch_parser()
    patch_render()
    patch_instruction()
    patch_review()
    patch_publish()
    patch_tests()
    patch_docs()


def finalize() -> None:
    path = "PLAN.md"
    text = read(path)
    start = text.index("#### Block K — publish State and Plan as local Node authoring")
    block = text[start:]
    block = block.replace("- [ ] ", "- [x] ")
    checkpoint = (
        "\n\nState/Plan publication checkpoint: reviewed `state` and `plan` findings are now first-class local Node authoring. "
        "Placement writes them into managed `## State` / `## Plan` blocks in `CONTEXT.src.md`; generated `CONTEXT.md` carries the same operational content, and machine state exposes it locally. "
        "They are no longer placement follow-up. Reusable Sources do not inherit State/Plan, and normalized reusable semantics remain stable when only Overview/State/Plan presentation changes; exact package identity still follows the generated package bytes."
    )
    text = text[:start] + block.rstrip() + checkpoint
    write(path, text.rstrip() + "\n")

    state_path = "STATE.md"
    state = read(state_path)
    state = state.replace(
        "Placement review labels State/Plan honestly as node-local follow-up because current publication does not yet write those kinds into `CONTEXT.src.md`.",
        "Placement now publishes reviewed State/Plan as local `## State` / `## Plan` authoring in the destination `CONTEXT.src.md`; generated `CONTEXT.md` carries them as operational project context, while reusable Sources do not inherit them.",
    )
    if "## Latest State/Plan publication completion" not in state:
        state = state.rstrip() + (
            "\n\n## Latest State/Plan publication completion\n\n"
            "The active onboarding path now treats State and Plan as first-class local Node content. Accepted placement State/Plan findings are written transactionally with the rest of Node authoring, shown as `Into Node — editable` during human review, included in publication preview, and removed from migration follow-up. They render into Official Context and local machine state but are deliberately excluded from inherited Source semantics.\n"
        )
    write(state_path, state.rstrip() + "\n")

    # Normalize both durable checkpoint files after the older finalizer so
    # git diff --check cannot be tripped by a blank line at EOF.
    for durable in ("PLAN.md", "STATE.md"):
        write(durable, read(durable).rstrip() + "\n")


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "apply"
    {"plan": plan, "apply": apply, "finalize": finalize}[command]()
