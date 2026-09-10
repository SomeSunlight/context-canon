from pathlib import Path
import subprocess

repo = Path.cwd()
plan = repo / "PLAN.md"
marker = "## Owner-test propagation narrative follow-up: Issue #27"
text = plan.read_text(encoding="utf-8")
if marker not in text:
    block = "\n".join([
        "",
        marker,
        "",
        "Purpose: apply the proven Source-update narrative to `contextcanon propagate` so each Parent-to-Child decision is understandable without package-internal vocabulary.",
        "",
        "- [ ] Make the Child the subject of each propagation step: show the Parent version currently used by that Child and the newer Parent version available.",
        "- [ ] Show human-readable Parent changes first, including Rule titles/statements; keep Node IDs, stable identities and digests under `Technical details`.",
        "- [ ] Preview the effective Child Context with the candidate Parent after existing Overrides/Removes and other imports, without changing the Child.",
        "- [ ] Put the short applicability / compatibility / upstream-quality checklist immediately before the Y/N decision and phrase the prompt as applying the Parent update to the named Child.",
        "- [ ] Preserve top-down, separately gated propagation semantics; `--all` remains scope only.",
        "- [ ] Polish the post-Source-accept rebuild wording, add focused regressions, bump the public CLI patch version, and pass full build/check/test/diff plus exact-head PR CI before returning to the owner test.",
        "",
        "This is a wording/impact-transparency refinement under Issue #27; no Parent or Source update becomes effective without the existing explicit human gate.",
        "",
    ])
    plan.write_text(text.rstrip() + "\n" + block, encoding="utf-8")

subprocess.run(["git", "config", "user.name", "ContextCanon automation"], check=True)
subprocess.run(["git", "config", "user.email", "actions@users.noreply.github.com"], check=True)
subprocess.run(["git", "add", "PLAN.md"], check=True)
if subprocess.run(["git", "diff", "--cached", "--quiet"]).returncode != 0:
    subprocess.run(["git", "commit", "-m", "Plan Issue #27 propagation review refinement"], check=True)
    subprocess.run(["git", "push", "origin", "HEAD:agent/issues-14-15-multi-parent"], check=True)
