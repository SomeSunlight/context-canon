from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def replace_once(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one replacement target, found {count}: {old[:80]!r}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


# Public tool version: the new top-level propagation workflow is a feature-level CLI change.
replace_once("pyproject.toml", 'version = "0.6.0"', 'version = "0.7.0"')
replace_once("src/contextcanon/version.py", '__version__ = "0.6.0"', '__version__ = "0.7.0"')
replace_once(
    "tests/test_configuration_and_update_ux.py",
    'self.assertEqual(out.getvalue().strip(), "contextcanon 0.6.0")',
    'self.assertEqual(out.getvalue().strip(), "contextcanon 0.7.0")',
)
replace_once(
    "tests/test_configuration_and_update_ux.py",
    'self.assertIn("Propagated 2 Parent edge(s) top-down.", out.getvalue())',
    'self.assertIn("Propagation review complete: accepted 2 changed Parent edge(s).", out.getvalue())',
)

# Let Source-update UX defer fingerprints until after meaning and local impact.
replace_once(
    "src/contextcanon/diff.py",
    "def render_diff(diff: ContextDiff) -> str:",
    "def render_diff(diff: ContextDiff, *, include_technical: bool = True) -> str:",
)
replace_once(
    "src/contextcanon/diff.py",
    '''    lines.extend(
        [
            "",
            "Technical details:",
            f"  Normalized digest: {_transition(diff.before_normalized_digest, diff.after_normalized_digest)}",
            f"  Package digest: {_transition(diff.before_package_digest, diff.after_package_digest)}",
        ]
    )
    return "\\n".join(lines) + "\\n"
''',
    '''    if include_technical:
        lines.extend(["", *render_diff_technical(diff).rstrip("\\n").split("\\n")])
    return "\\n".join(lines) + "\\n"


def render_diff_technical(diff: ContextDiff) -> str:
    return "\\n".join(
        [
            "Technical details:",
            f"  Normalized digest: {_transition(diff.before_normalized_digest, diff.after_normalized_digest)}",
            f"  Package digest: {_transition(diff.before_package_digest, diff.after_package_digest)}",
        ]
    ) + "\\n"
''',
)
replace_once(
    "src/contextcanon/cli.py",
    "from .diff import diff_compiled, render_diff",
    "from .diff import diff_compiled, render_diff, render_diff_technical",
)
replace_once(
    "src/contextcanon/cli.py",
    '''                print(f"Fetched candidate: {candidate.metadata.name} {candidate.metadata.version}")
                print(f"  Package digest: {candidate.package_digest}")
                provenance = load_candidate_provenance(node_root, candidate.package_digest)
                if provenance is not None and provenance.get("candidate_ref"):
                    print(f"  Git commit: {provenance['candidate_ref']}")
                elif provenance is not None and provenance.get("kind") == "local":
                    print(f"  Local repository: {provenance['location']}")
                print(f"  Cached package: {label}")
''',
    '''                print(f"Candidate: {candidate.metadata.name} {candidate.metadata.version}")
                provenance = load_candidate_provenance(node_root, candidate.package_digest)
''',
)
replace_once(
    "src/contextcanon/cli.py",
    '''                print("\\nExternal Source change:")
                print(render_diff(result), end="")
                print("Local effect if accepted:")
''',
    '''                print("\\nExternal Source change:")
                print(render_diff(result, include_technical=False), end="")
                print("Local effect if accepted:")
''',
)
replace_once(
    "src/contextcanon/cli.py",
    '''                else:
                    print("Downstream review: this Node has no dependent Child Nodes in the repository propagation graph.")
                if not args.yes and not _confirm(f"Accept this reviewed Source update for {candidate.metadata.name}?"):
''',
    '''                else:
                    print("Downstream review: this Node has no dependent Child Nodes in the repository propagation graph.")
                print("")
                print(render_diff_technical(result), end="")
                print("  Candidate discovery:")
                if provenance is not None and provenance.get("candidate_ref"):
                    print(f"    Git commit: {provenance['candidate_ref']}")
                elif provenance is not None and provenance.get("kind") == "local":
                    print(f"    Local repository: {provenance['location']}")
                print(f"    Cached package: {label}")
                if not args.yes and not _confirm(f"Accept this reviewed Source update for {candidate.metadata.name}?"):
''',
)

# Correct older wording that conflated rendering with reviewed downstream propagation.
replace_once(
    "CONTEXT.src.md",
    "Rebuilds propagate accepted Source and authoring changes deterministically into the generated child packages.",
    "Builds render each Node's accepted effective Context deterministically. Dependent Child Nodes keep their last accepted Parent snapshot until a newer one is explicitly reviewed through propagation.",
)
replace_once(
    "README.md",
    "When accepted Sources or authored context change, deterministic rebuilds propagate the updated result into consuming Nodes instead of requiring the same static prompt bundle to be rewritten in several places.",
    "When accepted Sources or authored context change, deterministic builds render the accepted result without rewriting copied prompt bundles. Dependent Child Nodes advance to newer Parent snapshots only through an explicit propagation review.",
)

# Put everyday maintenance on the root README path before deeper theory.
marker = "## One simple physical rule: a Node has its own directory\n"
readme = ROOT / "README.md"
text = readme.read_text(encoding="utf-8")
if "## Maintain an onboarded project\n" not in text:
    if text.count(marker) != 1:
        raise SystemExit("README maintenance insertion marker missing")
    section = '''## Maintain an onboarded project

After onboarding, the normal operator loop is short:

```text
inspect / update  →  review downstream propagation when needed  →  build  →  check
```

Start with **[Maintain an existing ContextCanon project](docs/maintenance.md)**. It explains Source versus Parent from the user's point of view, the three-question propagation review, and when to fix upstream versus use a justified local Override/Remove. Use the **[CLI quick reference](docs/cli.md)** as the compact command map; exact flags remain available through `contextcanon <command> --help`.

`contextcanon propagate` reviews only semantic descendants of the selected Context Node. `--all` deliberately broadens the review scope to every Parent graph in the repository; it is not blanket approval.

'''
    readme.write_text(text.replace(marker, section + marker, 1), encoding="utf-8")

replace_once(
    "README.md",
    "then uses two Topics to route only the tasks that need more depth: onboarding an existing project and developing ContextCanon itself.",
    "then uses three Topics to route only the tasks that need more depth: onboarding an existing project, maintaining an onboarded project, and developing ContextCanon itself.",
)
replace_once(
    "README.md",
    '''                         ┌─ Topic ──> onboarding guide
ContextCanon Gateway ───┤
                         └─ Topic ──> ContextCanon Framework Development
                                           ▲              ▲
                                           │ Source       │ Source
                              ContextCanon Foundation     │
                                                   Development Workflow
''',
    '''                         ┌─ Topic ──> onboarding guide
ContextCanon Gateway ───┼─ Topic ──> maintenance + CLI guide
                         └─ Topic ──> ContextCanon Framework Development
                                           ▲              ▲
                                           │ Source       │ Source
                              ContextCanon Foundation     │
                                                   Development Workflow
''',
)
replace_once(
    "README.md",
    '''│   ├── README.md
│   └── onboarding.md
''',
    '''│   ├── README.md
│   ├── onboarding.md
│   ├── maintenance.md
│   └── cli.md
''',
)
replace_once(
    "README.md",
    "- [Onboard an existing project](docs/onboarding.md) — first-user walkthrough and current structure-first experiment.\n",
    "- [Onboard an existing project](docs/onboarding.md) — first-user walkthrough and current structure-first experiment.\n- [Maintain an existing ContextCanon project](docs/maintenance.md) — Source updates, downstream propagation review, build, and check.\n- [CLI quick reference](docs/cli.md) — compact command map for normal operation.\n",
)

# Foundation deep documentation now uses the user-level propagation command.
replace_once(
    "nodes/library/foundation/docs/composition.md",
    "`contextcanon source update <name-or-id>` combines fetch, deterministic review and explicit acceptance, while `contextcanon parent propagate --all` then advances descendant Parent pins top-down with a diff/confirmation at each edge.",
    "`contextcanon source update <name-or-id>` combines fetch, deterministic review and explicit acceptance. When the consumer has semantic descendants, `contextcanon propagate` then reviews the affected Parent → Child edges top-down; each changed edge remains an explicit human acceptance unless controlled automation deliberately requests otherwise.",
)

# Intentional Context Node versions for this feature-level documentation/UX block.
replace_once(
    "nodes/internal/framework-development/CONTEXT.src.md",
    'name="ContextCanon Framework Development" version="0.1.1-draft"',
    'name="ContextCanon Framework Development" version="0.2.0-draft"',
)
replace_once(
    "nodes/internal/framework-development/CONTEXT.src.md",
    "- [ContextCanon Foundation](../../library/foundation/) — `0.1.1-draft`",
    "- [ContextCanon Foundation](../../library/foundation/) — `0.2.0-draft`",
)
replace_once(
    "nodes/internal/framework-development/CONTEXT.src.md",
    "- [Development Workflow](../../library/development-workflow/) — `0.2.1-draft`",
    "- [Development Workflow](../../library/development-workflow/) — `0.3.0-draft`",
)

# Changelog and durable project status.
replace_once(
    "CHANGELOG.md",
    "- Executable deterministic compiler commands for build, drift checking, and exact compiled Context diff.\n",
    "- Executable deterministic compiler commands for build, drift checking, and exact compiled Context diff.\n- Human-scale post-onboarding maintenance UX: canonical Source-name update review, local-impact preview, scoped `contextcanon propagate`, per-Child propagation checklist, and compact root-owned maintenance/CLI documentation.\n",
)
replace_once(
    "STATE.md",
    "PR #18 on `agent/issues-14-15-multi-parent` is the active **draft, unmerged** review branch for Issues #14–#24. It remains subject to explicit project-owner approval.",
    "PR #18 on `agent/issues-14-15-multi-parent` is the active **draft, unmerged** review branch for Issues #14–#27. It remains subject to explicit project-owner approval.",
)
replace_once(
    "PLAN.md",
    "The reviewed onboarding placement publication and owner-tested ContextCanon workflow are accepted on `main`. PR #18 is the active draft review branch for Issues #14–#19 and remains unmerged pending explicit project-owner approval.",
    "The reviewed onboarding placement publication and owner-tested ContextCanon workflow are accepted on `main`. PR #18 is the active draft review branch for Issues #14–#27 and remains unmerged pending explicit project-owner approval.",
)
replace_once(
    "PLAN.md",
    '''- [ ] Add a user-level `contextcanon propagate --all` command for carrying accepted Context changes through dependent Parent edges; keep `contextcanon parent propagate --all` as the explicit compatibility form.
- [ ] Make Source-update review explain the external Source change first, then the local effect if accepted, what remains unchanged until propagation/build, the downstream Nodes expected to need propagation, and the normal next command before technical fingerprints.
- [ ] Add a concise root-owned existing-project maintenance guide and compact CLI overview covering inspect/update/propagate/build/check plus links to deeper concepts; make both discoverable from README and a new Gateway Topic.
- [ ] Rewrite the opening of Foundation `composition.md` from the user mental model: a Child can combine several independent contexts; non-orthogonal imports can conflict and require explicit human resolution; link to the existing deeper conflict sections rather than duplicating them.
- [ ] Keep Parent review/accept explanations short and intuitive: Parent and Child may evolve independently; the Child keeps its last accepted Parent snapshot until a newer one is reviewed and accepted.
- [ ] Choose intentional human-facing version bumps for materially changed Context Nodes instead of relying only on automatic minimum patch bumps, regenerate self-hosted packages, add focused regressions, and pass the complete suite/build/check/diff gate before returning to the real `ai-workstation` owner test.
''',
    '''- [x] Add user-level `contextcanon propagate` scoped to semantic descendants of the selected Node; `--all` broadens only the review scope to every Parent graph, while `contextcanon parent propagate` remains the explicit compatibility form.
- [x] Make Source-update review explain the external Source change first, then the local effect if accepted, what remains unchanged until propagation/build, the downstream Nodes expected to need review, and the normal next command before technical fingerprints.
- [x] Add a concise root-owned existing-project maintenance guide and compact CLI overview covering inspect/update/propagate/build/check plus links to deeper concepts; make both discoverable from README and a new Gateway Topic.
- [x] Rewrite the opening of Foundation `composition.md` from the user mental model: a Child can combine several independent contexts; non-orthogonal imports can conflict and require explicit human resolution; link to the existing deeper conflict sections rather than duplicating them.
- [x] Keep Parent review/accept explanations short and intuitive: Parent and Child may evolve independently; the Child keeps its last accepted Parent snapshot until a newer one is reviewed and accepted. Propagation presents a short applicability / cross-context compatibility / upstream-quality checklist before detailed diffs.
- [x] Choose intentional human-facing version bumps for materially changed Context Nodes instead of relying only on automatic minimum patch bumps, regenerate self-hosted packages, add focused regressions, and pass the complete suite/build/check/diff gate before returning to the real `ai-workstation` owner test.
''',
)

# Version-discipline checkpoint wording predates the owner's deliberate minor correction.
replace_once(
    "PLAN.md",
    "Development Workflow advances to `0.2.1-draft`; affected self-hosted Context Nodes are versioned consistently.",
    "Development Workflow first received the automatic minimum `0.2.1-draft` bump; owner review then correctly classified the accumulated workflow change as feature-level and advances it deliberately to `0.3.0-draft`. Affected self-hosted Context Nodes are versioned consistently.",
)
