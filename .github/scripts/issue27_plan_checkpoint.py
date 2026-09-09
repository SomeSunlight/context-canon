from pathlib import Path
import subprocess

plan = Path("PLAN.md")
text = plan.read_text(encoding="utf-8")
block = r'''

## Owner-test everyday maintenance UX: Issue #27

Purpose: make normal ContextCanon use after onboarding discoverable from the repository entrance, explain composition from the user's benefit first, and give accepted Context changes one short, consistent propagation vocabulary.

- [ ] Add a user-level `contextcanon propagate --all` command for carrying accepted Context changes through dependent Parent edges; keep `contextcanon parent propagate --all` as the explicit compatibility form.
- [ ] Make Source-update review explain the external Source change first, then the local effect if accepted, what remains unchanged until propagation/build, the downstream Nodes expected to need propagation, and the normal next command before technical fingerprints.
- [ ] Add a concise root-owned existing-project maintenance guide and compact CLI overview covering inspect/update/propagate/build/check plus links to deeper concepts; make both discoverable from README and a new Gateway Topic.
- [ ] Rewrite the opening of Foundation `composition.md` from the user mental model: a Child can combine several independent contexts; non-orthogonal imports can conflict and require explicit human resolution; link to the existing deeper conflict sections rather than duplicating them.
- [ ] Keep Parent review/accept explanations short and intuitive: Parent and Child may evolve independently; the Child keeps its last accepted Parent snapshot until a newer one is reviewed and accepted.
- [ ] Choose intentional human-facing version bumps for materially changed Context Nodes instead of relying only on automatic minimum patch bumps, regenerate self-hosted packages, add focused regressions, and pass the complete suite/build/check/diff gate before returning to the real `ai-workstation` owner test.

Issue #27 is an explicit owner-approved expansion of draft PR #18 discovered during the real post-onboarding `ai-workstation` walkthrough. PR #18 remains draft and must not be merged without explicit project-owner approval.
'''
if "## Owner-test everyday maintenance UX: Issue #27" not in text:
    plan.write_text(text.rstrip() + block + "\n", encoding="utf-8")

subprocess.run(["git", "config", "user.name", "github-actions[bot]"], check=True)
subprocess.run(["git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"], check=True)
subprocess.run(["git", "add", "PLAN.md"], check=True)
subprocess.run(["git", "rm", ".github/scripts/issue27_plan_checkpoint.py", ".github/workflows/issue27-plan-checkpoint.yml"], check=True)
subprocess.run(["git", "commit", "-m", "Checkpoint Issue #27 maintenance UX plan"], check=True)
subprocess.run(["git", "push", "origin", "HEAD:agent/issues-14-15-multi-parent"], check=True)
