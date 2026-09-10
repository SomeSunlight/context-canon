from pathlib import Path

PLAN = Path('PLAN.md')
STATE = Path('STATE.md')
README = Path('README.md')

old_plan = """The current accepted `main` baseline is PR #13, squash-merged as `df847ba031bfa3965ca53626249e18a1074cb8af`.\n\nThe reviewed onboarding placement publication and owner-tested ContextCanon workflow are accepted on `main`. PR #18 is the active draft review branch for Issues #14–#27 and remains unmerged pending explicit project-owner approval.\n\nHistorical plan/checkpoint sections below retain the status wording that was true when written; references to PR #13 as draft are historical."""
new_plan = """The current accepted `main` baseline is PR #18, squash-merged as `2fb8368b15a7ef93a46012e0a0583bb795e174fe`.\n\nPR #18 completed Issues #14–#27 and the real `ai-workstation` owner-tested ContextCanon 0.7.3 maintenance workflow. Those issues are closed; no framework review PR is currently active.\n\nHistorical plan/checkpoint sections below retain the status wording that was true when written; references to PR #13 or PR #18 as draft/unmerged are historical."""

old_state = """The accepted `main` baseline is PR #13, squash-merged as:\n\n`df847ba031bfa3965ca53626249e18a1074cb8af`\n\nPR #18 on `agent/issues-14-15-multi-parent` is the active **draft, unmerged** review branch for Issues #14–#27. It remains subject to explicit project-owner approval.\n\nHistorical checkpoint sections below preserve the status that was true when each checkpoint was written. References there to PR #13 as draft/unmerged are historical, not the current repository state."""
new_state = """The accepted `main` baseline is PR #18, squash-merged as:\n\n`2fb8368b15a7ef93a46012e0a0583bb795e174fe`\n\nPR #18 completed Issues #14–#27, including ContextCanon 0.7.3, multi-Parent semantics, human-scale Source/propagation UX, and the Windows propagation-resume fix validated against the real `ai-workstation` consumer. No framework review PR is currently active.\n\nHistorical checkpoint sections below preserve the status that was true when each checkpoint was written. References there to PR #13 or PR #18 as draft/unmerged are historical, not the current repository state."""

for path, old, new in [(PLAN, old_plan, new_plan), (STATE, old_state, new_state)]:
    text = path.read_text(encoding='utf-8')
    if text.count(old) != 1:
        raise SystemExit(f'Expected exactly one baseline block in {path}')
    path.write_text(text.replace(old, new), encoding='utf-8')

state = STATE.read_text(encoding='utf-8')
marker = '## Post-merge baseline reconciliation — PR #18\n'
if marker not in state:
    state += """\n\n## Post-merge baseline reconciliation — PR #18\n\nPR #18 was squash-merged to `main` as `2fb8368b15a7ef93a46012e0a0583bb795e174fe`. Issues #14–#27 closed with that merge. The accepted product baseline is ContextCanon CLI/package 0.7.3 with compiler 0.6.0. The real `ai-workstation` maintenance run completed Source update, all eight individually reviewed Parent/Child propagation steps, rebuild/check across all nine Nodes, Windows interruption/resume, and an idempotent rerun.\n\nIssue #28 is documentation-only reconciliation of this accepted fact; it introduces no product semantics.\n"""
    STATE.write_text(state, encoding='utf-8')

readme = README.read_text(encoding='utf-8')
readme = readme.replace('Compiler 0.4 separates candidate discovery from accepted inheritance:', 'Compiler 0.6 separates candidate discovery from accepted inheritance:')
heading = '## Project status\n'
idx = readme.find(heading)
if idx < 0:
    raise SystemExit('README Project status heading not found')
readme = readme[:idx] + """## Project status\n\nThe current project-owner accepted `main` baseline is PR #18, squash-merged as `2fb8368b15a7ef93a46012e0a0583bb795e174fe`. The public CLI/package version is **0.7.3** and the deterministic compiler version is **0.6.0**.\n\nThis baseline includes explicit zero/one/many semantic Parents, immutable reviewed Parent/Source snapshots, central Source discovery configuration, explicit machine Node names, package-version discipline, and the human-scale `source update` / `propagate` maintenance flow. The final workflow was validated end-to-end on the real `ai-workstation` consumer, including all eight Parent/Child reviews, rebuild/check across nine Nodes, Windows interruption/resume, and idempotent rerun.\n\nAll Issues #14–#27 completed by PR #18 are closed. See [STATE.md](STATE.md) for the accepted current situation and [PLAN.md](PLAN.md) for intentionally deferred or future work.\n"""
README.write_text(readme, encoding='utf-8')
