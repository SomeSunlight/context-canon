from pathlib import Path

path = Path("PLAN.md")
text = path.read_text(encoding="utf-8")
heading = "## Owner-test Source-update narrative follow-up: Issue #27\n"
if heading not in text:
    block = """

## Owner-test Source-update narrative follow-up: Issue #27

Purpose: make `contextcanon source update` understandable without prior ContextCanon vocabulary. The owner test showed that the first human-scale rewrite still describes internal state (`accepted`, `dependent Nodes`, generic `Nodes:` diff categories) before it tells the simple story of what is currently used here, what newer Source version was found, what changed there, what would change locally, what the human should check, and what should be reviewed downstream afterwards.

- [ ] Lead with a tiny orientation: current Source version used by this local Node, newly found candidate version/location, and a one-line statement that the command is offering a local update but has changed nothing yet.
- [ ] Present the external Source change as a human Source change, without the generic `Nodes:` metadata category; keep exact identities/fingerprints available only in deeper detail.
- [ ] Compute and show the effective local impact of the candidate after this Node's existing Overrides/Removes and other imported Context have been applied, rather than merely restating the upstream diff.
- [ ] Put a three-question minimum review checklist immediately before the acceptance prompt: applicability here, compatibility with other imported Context, and upstream correctness/completeness.
- [ ] Explain downstream work in plain Parent/Child terms: after this Node changes, its Child Nodes still use their previously reviewed Parent snapshot and therefore need the same kind of review; list them and point directly to `contextcanon propagate` as the one-command guided review entry.
- [ ] Keep technical digests, exact Git provenance, cache paths, and stable identities under an unmistakable `Technical details` layer.
- [ ] Add focused narrative/local-impact regressions, deliberately patch-bump the public CLI if appropriate, regenerate self-hosted outputs when documentation changes, and pass the complete suite/build/check/diff gate plus ordinary exact-head PR CI before returning another owner-test SHA.

This is a wording/impact-transparency refinement of Issue #27, not a change to acceptance authority: no Source or Parent update becomes effective without the existing explicit human gate, and PR #18 remains draft/unmerged pending project-owner approval.
"""
    path.write_text(text.rstrip() + block + "\n", encoding="utf-8")
