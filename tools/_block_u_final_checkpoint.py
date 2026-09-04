from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def normalize(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")
    return path.read_text(encoding="utf-8")


plan_path = ROOT / "PLAN.md"
plan = normalize(plan_path)
plan = plan.replace(
    "**Status: ACTIVE — implementation under verification; owner acceptance pending.**",
    "**Status: COMPLETE — framework implementation and verification complete; owner test pending.**",
    1,
)
plan = plan.replace(
    "- [ ] 7. Run focused regressions, complete deterministic suite, self-build/check, diff hygiene and cleanup; then hand the exact clean PR head to the project owner for the final real `ai-workstation` onboarding/readability test. PR remains draft/unmerged until explicit owner approval.",
    "- [x] 7. Run focused regressions, complete deterministic suite, self-build/check, diff hygiene and cleanup; then hand the exact clean PR head to the project owner for the final real `ai-workstation` onboarding/readability test. PR remains draft/unmerged until explicit owner approval.",
    1,
)
plan_path.write_text(plan.rstrip() + "\n", encoding="utf-8", newline="\n")

state_path = ROOT / "STATE.md"
state = normalize(state_path)
heading = "## Latest Block U reusable-Context onboarding UX checkpoint"
if heading not in state:
    state += f'''\n{heading}\n\nThe final owner-UX correction turns reusable Context setup into its own human gate between accepted project structure and placement reasoning. `STEP-05-reusable-contexts.md` owns Catalog locations, sparse project-Node ← reusable-Context assignments, and the durable Why for each relationship. Human operators no longer have to reconstruct Source UUIDs, package digests, target Node keys, or one-time Catalog/owner-selection CLI options during normal onboarding. Exact immutable identities remain machine state.\n\nThe generated onboarding PLAN is now a ten-step operator console. Each STEP keeps the same number/title vocabulary as its artifact, a novice-oriented explanation, completion checkbox, exact command, and artifact guidance together instead of splitting a top checklist from lower instructions. STEP 05 precedes the placement LLM, and accepted assignments plus their Why are explicit placement-reasoning input so inherited reusable guidance is not proposed again as duplicate local meaning.\n\nSource relationship rationale is durable provenance rather than a Rule: direct Source authoring records the Why, immutable imported context carries it through accepted Parent packages, and descendants can therefore explain both where inherited reusable Context came from and why it was attached. Ordinary builds remain offline and Parent/Source package pins remain immutable.\n\nThe final product commit is created only after the focused onboarding/Parent/package regressions, the complete deterministic suite, `contextcanon build --all .`, `contextcanon check --all .`, diff hygiene, temporary-helper cleanup, and a second post-cleanup check all succeed. PR #13 remains draft and unmerged; the next action is the project owner's real `ai-workstation` test starting again at STEP 05.\n'''
state_path.write_text(state.rstrip() + "\n", encoding="utf-8", newline="\n")
