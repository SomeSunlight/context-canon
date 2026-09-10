from pathlib import Path

path = Path("STATE.md")
text = path.read_text(encoding="utf-8")
heading = "## Final Issue #27 owner acceptance"
if heading not in text:
    text = text.rstrip() + "\n\n" + heading + "\n\n" + (
        "The project owner completed the real `ai-workstation` maintenance run with ContextCanon 0.7.3 after the Windows resume fix. "
        "All remaining Parent/Child updates were reviewed and accepted individually, `contextcanon build --all .` completed, and `contextcanon check --all .` reported `ok` for the root plus all eight Child Nodes. "
        "Repeating the maintenance flow on that resulting state is idempotent. The owner explicitly accepted the final Source-update and propagation wording as clear and understandable.\n\n"
        "The UX lesson from this run is recorded under Issue #27 rather than hardened into another Framework Development Rule yet. "
        "Human-facing flows were most successful when they presented current state, newly found change, effect of the offered action, the operator's checks/decision, and the next step before technical identities/mechanics. "
        "Representative end-to-end consumer use remains the preferred validation method; when the development harness cannot execute that consumer workflow directly, an explicit owner walkthrough is the UX gate. "
        "No specific IDE or agent tool is part of the product contract. This remains covered by the existing vertical-validation rule plus Issue #27 until the pattern proves independently reusable enough to justify another Rule.\n\n"
        "PR #18 is therefore ready for project-owner merge review. Its exact merge head must remain green, and the merge itself still requires the project owner's explicit action. After merge, perform the normal accepted-baseline reconciliation before starting new framework development.\n"
    )
    path.write_text(text, encoding="utf-8")
