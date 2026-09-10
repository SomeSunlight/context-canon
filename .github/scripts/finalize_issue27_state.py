from pathlib import Path

path = Path("STATE.md")
text = path.read_text(encoding="utf-8")
heading = "## Latest Issue #27 maintenance UX and Windows propagation finalization"
if heading not in text:
    text = text.rstrip() + "\n\n" + heading + "\n\n" + (
        "The real post-onboarding `ai-workstation` owner test now has a complete human-scale maintenance path. "
        "`contextcanon source update` explains the currently used reusable Context, the candidate found, the external change, "
        "the effective local impact, the explicit Y/N decision, and the downstream Parent/Child reviews in that order. "
        "`contextcanon propagate` is the normal top-level guided entry for carrying an already accepted Context change through semantic descendants; "
        "each changed Child remains separately gated, while already-current relationships are skipped compactly on rerun.\n\n"
        "The same owner run exposed a real Windows failure while accepting the Parent update for `Windows and WSL bootstrap`: "
        "the reviewed immutable package was staged successfully, but the final directory publication failed with `WinError 5` during `os.replace`. "
        "Immutable package publication now retries only that final atomic rename on transient `PermissionError`/`FileExistsError`, "
        "continues to verify any destination that appears concurrently by exact package identity, and still refuses different content. "
        "Earlier successfully accepted propagation steps remain valid; rerunning propagation resumes by reporting those edges as `Already current` and continues at the first stale Child.\n\n"
        "The public CLI/package version is `0.7.3`. The final Issue #27 product gate passes Python compilation, the complete deterministic suite of 247 tests, "
        "`contextcanon build --all .`, `contextcanon check --all .`, and `git diff --check`. A dedicated Windows Server 2025 runner additionally proves both the forced transient-package-publication retry and propagation resume behavior. "
        "The ordinary pull-request workflow is green on the repository-authored exact-tree checkpoint after temporary verification markers are removed.\n\n"
        "PR #18 remains Draft and unmerged. The next project-owner action is to reinstall the exact final PR head in `ai-workstation`, rerun `contextcanon propagate`, "
        "confirm the already-current edges are skipped, finish the remaining Child reviews, then rebuild/check that consumer repository. No merge is authorized implicitly by this verification.\n"
    )
    path.write_text(text, encoding="utf-8")
