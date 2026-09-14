from pathlib import Path

path = Path("PLAN.md")
text = path.read_text(encoding="utf-8")
start = text.index("## Owner-test follow-up: split STEP 08 review — Issue #35")
end = text.index("## Project-owner accepted block: structure-first onboarding on ai-workstation", start)
new = '''## Owner-test follow-up: split STEP 08 review — Issue #35

Purpose: keep the strong placement semantics from the real `Llama_Dispatcher` onboarding while replacing the monolithic STEP-08 review surface that becomes unreadable as findings and Source edits grow.

- [x] Keep `STEP-08-placement.md` as the human entry/index and move each placement finding into a stable dedicated Markdown file below `STEP-08-placement/`.
- [x] Render frozen Source-before and editable Source-after regions in the same readable Markdown shape so paragraphs wrap, tables render, and embedded headings do not compete with the review document hierarchy.
- [x] Keep shared Source edits single-owned and linked from every affected finding; preserve exact Evidence/proposal binding, stable authoring identity, and reusable-Source review controls.
- [x] Migrate an existing monolithic v1 review in place without losing human edits or decisions, then keep reruns idempotent and reject missing/duplicate/foreign split artifacts.
- [x] Add focused split-layout/migration/round-trip regressions plus a many-finding scaling case, run the complete deterministic suite and zero-drift check, and keep PR #31 draft/unmerged for continued `Llama_Dispatcher` owner validation.

Checkpoint: Issue #35 is implemented for owner validation. `STEP-08-placement.md` is now a compact status/index surface and each finding lives in one stable Markdown review sheet below `STEP-08-placement/`. Frozen Before and editable After content use the same rendered quote frame; shared Source edits remain single-owned and the generated source audit links directly to that owning finding. Existing monolithic v1 reviews migrate in place while preserving human decisions and authoring identity. The implementation head `dc6821ac4c8a0c93d4efb3214b41360039da47c5` passed all 259 deterministic tests, `contextcanon check --all .` with zero generated drift, and `git diff --check`; coverage includes 40 findings without rebuilding a monolithic review body. Markdown remains the editable contract; HTML stays available as a future generated/read-only presentation option rather than a second authoring/parser surface. PR #31 remains draft and unmerged pending continued `Llama_Dispatcher` owner validation.

'''
path.write_text(text[:start] + new + text[end:], encoding="utf-8", newline="\n")
