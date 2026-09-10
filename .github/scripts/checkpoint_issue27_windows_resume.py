from pathlib import Path
import subprocess

plan = Path("PLAN.md")
marker = "## Owner-test Windows propagation resume follow-up: Issue #27"
text = plan.read_text(encoding="utf-8")
if marker not in text:
    block = """

## Owner-test Windows propagation resume follow-up: Issue #27

Purpose: close the Windows package-publication failure found during the real ai-workstation propagation run, preserve already accepted steps, and finish the remaining Source/propagation wording polish before the owner continues.

- [ ] Harden immutable package publication against transient Windows directory rename/replace access failures without weakening exact package verification or overwriting different content.
- [ ] Prove rerun/resume behavior: already-current Parent/Child edges are skipped compactly and the first still-stale Child remains separately reviewable.
- [ ] Add a visible delimiter between propagation review rounds.
- [ ] Finish the collected Source-update wording polish: clear current Source, candidate, what Y changes locally, what is reviewed after Y, and rebuild/check guidance.
- [ ] Patch-bump the public CLI/package version consistently, add focused regressions, and pass full syntax/build/test/check/diff plus exact-head PR CI before returning to the owner test.

The first five accepted ai-workstation propagation steps are valid project state and must not be rolled back or repeated as new decisions. PR #18 remains draft and unmerged pending explicit project-owner approval.
"""
    plan.write_text(text.rstrip() + block + "\n", encoding="utf-8")

subprocess.run(["git", "config", "user.name", "ContextCanon automation"], check=True)
subprocess.run(["git", "config", "user.email", "actions@users.noreply.github.com"], check=True)
subprocess.run(["git", "add", "PLAN.md"], check=True)
if subprocess.run(["git", "diff", "--cached", "--quiet"]).returncode != 0:
    subprocess.run(["git", "commit", "-m", "Plan Issue #27 Windows propagation resume fix"], check=True)
    subprocess.run(["git", "push", "origin", "HEAD:agent/issues-14-15-multi-parent"], check=True)
