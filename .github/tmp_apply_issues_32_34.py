from pathlib import Path
import re


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"anchor not found in {path}: {old[:120]!r}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")


# PLAN: durable recovery map for this coherent live-owner-test follow-up.
plan_anchor = (
    "Checkpoint: draft PR #31 fixes Issue #30 with a narrow first-adoption exception, while existing/recoverable roots and foreign output collisions retain their prior protection. "
    "The exact implementation head passed all 250 deterministic tests and `contextcanon check --all .` with zero generated drift. PR #31 remains draft and unmerged pending project-owner validation.\n"
)
plan_block = plan_anchor + """

## Owner-test follow-up: resilient and compact STEP 05 — Issues #32–#34

Purpose: incorporate the next real `Llama_Dispatcher` onboarding findings without weakening atomic writes or turning human guidance into generated combinatorial noise.

- [x] #32 make onboarding UTF-8 atomic file replacement tolerate the same bounded transient Windows locks already handled by immutable package publication, while preserving sibling-temp/fsync/atomic-replace semantics and clear final failure.
- [x] #33 replace the STEP-05 project×Catalog copy-helper product with one Assignment grammar plus separate generated project-side and reusable-side choice lists; make the syntax example use the current project root rather than hard-coded `AI Workstation`.
- [x] #34 introduce the Evidence `SNAPSHOT` variable immediately in the root README with PowerShell/POSIX/cmd syntax and use the short variable in the following onboarding commands.
- [x] Add focused regressions, run the complete deterministic suite and zero-drift check, and keep PR #31 draft/unmerged for continued real-project validation.

Checkpoint: the live owner-test follow-up is implemented on PR #31. STEP 05 remains semantically strict and sparse, but its generated help now scales linearly with project plus reusable Node count. Atomic onboarding writes retry only the final replace on transient Windows access failures. The root README teaches the snapshot variable before the first long-path reuse. Full deterministic verification and `contextcanon check --all .` are required on the exact product tree before this checkpoint is committed.
"""
replace_once("PLAN.md", plan_anchor, plan_block)


# #32: retry only the final atomic file replace, mirroring the proven package-publication boundary.
replace_once("src/contextcanon/onboarding_workspace.py", "import tempfile\n", "import tempfile\nimport time\n")
old_write = '''def write_utf8(path: Path, text: str) -> None:
    """Atomically write UTF-8 without depending on shell redirection/codepages."""

    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
'''
new_write = '''_ATOMIC_REPLACE_RETRY_DELAYS = (0.05, 0.10, 0.20, 0.40, 0.80)


def _replace_file_with_retry(temporary: Path, path: Path) -> None:
    """Publish one prepared sibling file atomically despite brief Windows locks."""

    for attempt in range(len(_ATOMIC_REPLACE_RETRY_DELAYS) + 1):
        try:
            os.replace(temporary, path)
            return
        except (PermissionError, FileExistsError) as exc:
            if attempt == len(_ATOMIC_REPLACE_RETRY_DELAYS):
                raise ContextCanonError(
                    f"Could not atomically write {path} after retrying a temporary filesystem lock: {exc}"
                ) from exc
            time.sleep(_ATOMIC_REPLACE_RETRY_DELAYS[attempt])


def write_utf8(path: Path, text: str) -> None:
    """Atomically write UTF-8 without depending on shell redirection/codepages."""

    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        _replace_file_with_retry(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
'''
replace_once("src/contextcanon/onboarding_workspace.py", old_write, new_write)


# #33: retain strict grammar but make human help O(project + catalog), never O(project * catalog).
reusable = Path("src/contextcanon/onboarding_reusable_contexts.py")
text = reusable.read_text(encoding="utf-8")
old_error = '''                "Assignment first line is incomplete. Copy one complete line from "
                "'Copy-ready Assignment lines — generated' below, paste it into Assignments, "
                "then add an indented 'Why:' line"
'''
new_error = '''                "Assignment first line is incomplete. Build it from one entry under "
                "'Available project Context Nodes — generated' and one entry under "
                "'Available reusable Context Nodes — generated' using the shown Assignment syntax, "
                "then add an indented 'Why:' line"
'''
if old_error not in text:
    raise SystemExit("assignment error anchor missing")
text = text.replace(old_error, new_error, 1)
pattern = re.compile(r"def render_reusable_contexts\(.*?\n\ndef _initial_text", re.S)
replacement = '''def render_reusable_contexts(
    evidence_digest: str,
    structure: HumanStructurePlan,
    decision: str,
    locations: tuple[str, ...],
    packages: tuple[CompiledPackage, ...],
    assignments: tuple[ReusableContextAssignment, ...],
) -> str:
    root_node = next((node for node in structure.nodes if node.path == "."), structure.nodes[0] if structure.nodes else None)
    example_package = packages[0] if packages else None
    lines = [
        "# STEP 05 — Reusable Contexts",
        f'<!-- contextcanon-reusable-contexts schema="{REUSABLE_CONTEXTS_SCHEMA}" evidence="{evidence_digest}" structure="{structure.structure_digest}" -->',
        "",
        "This step says **which reusable Context Nodes are available and where they apply in this project**. It happens after the project's own Context Node structure is accepted and before the placement LLM distributes project knowledge.",
        "",
        "Edit only the Catalog locations, the sparse Assignments, and `Decision`. ContextCanon owns IDs, package digests and the generated lists. Run the same `contextcanon onboard reusable-contexts ...` command again after every edit.",
        "",
        "## Catalog locations",
        "",
        "Add one directory containing reusable compiled Context Nodes per line. A location may itself be one Context Node or a directory containing several Nodes.",
        "",
        "Paste a path normally. Markdown bullets, backticks, or quotes are optional input conveniences; ContextCanon rewrites accepted input into one canonical Markdown form on the next run.",
        "",
        r"Example: `C:\\Users\\you\\PycharmProjects\\context-canon\\nodes\\library`",
        "",
        "> ✏️ Editable Catalog locations start below.",
        "",
        CATALOG_START,
    ]
    lines.extend(f"- `{value}`" for value in locations)
    lines.extend(
        [
            CATALOG_END,
            "",
            "> End editable Catalog locations.",
            "",
            "## Assignments",
            "",
            "Keep only relationships that should actually exist. Build each first line from one project Context Node and one reusable Context Node from the two generated choice lists below, put them around the `←` exactly as shown, then add an indented `Why:` line. Replace the `-` placeholder with a real durable rationale. The list stays sparse; the helper never generates every possible pairing.",
            "",
            "Assignment syntax:",
            "",
            "```text",
            "- **<project Context Node>** (`<project path>`) ← **<reusable Context Node>** (`<version>`)",
            "  Why: -",
            "```",
        ]
    )
    if root_node is not None and example_package is not None:
        lines.extend(
            [
                "",
                "Example first line using entries from this project (syntax only, not a recommendation):",
                "",
                "```text",
                f"- **{root_node.name}** (`{root_node.path}`) ← **{example_package.metadata.name}** (`{example_package.metadata.version}`)",
                "```",
            ]
        )
    lines.extend(
        [
            "",
            "> ✏️ Editable reusable-Context assignment controls start below.",
            "",
            f"Decision: `{decision}`",
            "",
            ASSIGNMENTS_START,
        ]
    )
    for assignment in assignments:
        lines.extend(
            [
                f"- **{assignment.target_name}** (`{assignment.target_path}`) ← **{assignment.source_name}** (`{assignment.source_version}`)",
                f"  Why: {assignment.why}",
            ]
        )
    lines.extend(
        [
            ASSIGNMENTS_END,
            "",
            "> End editable reusable-Context assignment controls.",
            "",
            "Set `Decision` to `accept` when the Catalog and assignments are the intended reusable-context composition for this onboarding. An empty assignment list is valid when no reusable Context applies.",
            "",
            "## Available project Context Nodes — generated",
            "",
            "Use one desired entry as the left-hand side of `←`.",
            "",
            GENERATED_PROJECT_START,
        ]
    )
    for node in structure.nodes:
        lines.append(f"- **{node.name}** (`{node.path}`)")
    lines.extend(
        [
            GENERATED_PROJECT_END,
            "",
            "## Available reusable Context Nodes — generated",
            "",
            "Use one desired name/version entry as the right-hand side of `←`.",
            "",
            GENERATED_CATALOG_START,
        ]
    )
    if packages:
        for package in packages:
            lines.append(
                f"- **{package.metadata.name}** (`{package.metadata.version}`) — exact package `{package.package_digest}`"
            )
    elif locations:
        lines.append("No verified reusable Context Nodes found.")
    else:
        lines.append("No Catalog locations yet. Add one or more above and run this step again.")
    lines.extend(
        [
            GENERATED_CATALOG_END,
            "",
            "The generated package identities are review information. Do not copy their IDs or digests into Assignments; ContextCanon resolves and remembers them for subsequent steps.",
            "",
        ]
    )
    return "\\n".join(lines)


def _initial_text'''
text, count = pattern.subn(replacement, text, count=1)
if count != 1:
    raise SystemExit(f"render_reusable_contexts replacement count: {count}")
reusable.write_text(text, encoding="utf-8", newline="\n")


# #34: teach the shell variable before users have to repeat the digest path.
readme = Path("README.md")
text = readme.read_text(encoding="utf-8")
anchor = (
    "The snapshot is an immutable review anchor, not a lock on the live repository. It lets different semantic instructions or human review iterations operate on **the same exact project bytes** until you deliberately choose a new evidence basis.\n\n"
)
variable_help = anchor + '''Store the printed snapshot path once instead of repeatedly typing the long digest. Use the assignment form for your shell:

```powershell
$SNAPSHOT = '.context/onboarding/<evidence-digest>'
```

```sh
SNAPSHOT='.context/onboarding/<evidence-digest>'
```

```bat
set SNAPSHOT=.context\\onboarding\\<evidence-digest>
```

The commands below use `$SNAPSHOT` in PowerShell, bash and zsh; in `cmd.exe`, use `%SNAPSHOT%` instead. As soon as ContextCanon creates `contextcanon-onboarding/PLAN.md`, that file becomes the run-specific copy/paste console and shows the shell-native variable and exact commands again.

'''
if anchor not in text:
    raise SystemExit("README snapshot anchor missing")
text = text.replace(anchor, variable_help, 1)
command_replacements = {
    "contextcanon onboard structure-instruction \\\n  .context/onboarding/<evidence-digest>": "contextcanon onboard structure-instruction $SNAPSHOT",
    "contextcanon onboard structure-validate .context/onboarding/<evidence-digest>": "contextcanon onboard structure-validate $SNAPSHOT",
    "contextcanon onboard structure-review   .context/onboarding/<evidence-digest>": "contextcanon onboard structure-review   $SNAPSHOT",
    "contextcanon onboard structure-preview .context/onboarding/<evidence-digest>": "contextcanon onboard structure-preview $SNAPSHOT",
    "contextcanon onboard structure-materialize .context/onboarding/<evidence-digest>": "contextcanon onboard structure-materialize $SNAPSHOT",
    "contextcanon onboard placement-instruction \\\n  .context/onboarding/<evidence-digest>": "contextcanon onboard placement-instruction $SNAPSHOT",
    "contextcanon onboard placement-validate .context/onboarding/<evidence-digest>": "contextcanon onboard placement-validate $SNAPSHOT",
    "contextcanon onboard placement-review   .context/onboarding/<evidence-digest>": "contextcanon onboard placement-review   $SNAPSHOT",
}
for old, new in command_replacements.items():
    if old not in text:
        raise SystemExit(f"README command anchor missing: {old!r}")
    text = text.replace(old, new, 1)
readme.write_text(text, encoding="utf-8", newline="\n")


# Regressions for #32.
tests = Path("tests/test_onboarding_workspace_checkpoint.py")
text = tests.read_text(encoding="utf-8")
text = text.replace("import subprocess\n", "import os\nimport subprocess\n", 1)
text = text.replace("import unittest\n", "import unittest\nfrom unittest import mock\n", 1)
text = text.replace(
    "    update_workspace_checkpoint,\n)",
    "    update_workspace_checkpoint,\n    write_utf8,\n)",
    1,
)
marker = '\n\nif __name__ == "__main__":\n'
additions = r'''

    def test_write_utf8_retries_transient_windows_style_replace_lock(self):
        root = Path(tempfile.mkdtemp())
        path = root / "run-inputs.json"
        path.write_text("before\n", encoding="utf-8")
        real_replace = os.replace
        attempts = 0

        def flaky_replace(source, destination):
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise PermissionError(5, "simulated transient Windows lock")
            return real_replace(source, destination)

        with mock.patch("contextcanon.onboarding_workspace.os.replace", side_effect=flaky_replace), mock.patch(
            "contextcanon.onboarding_workspace.time.sleep"
        ):
            write_utf8(path, "after\n")

        self.assertEqual(attempts, 3)
        self.assertEqual(path.read_text(encoding="utf-8"), "after\n")
        self.assertEqual([item for item in root.iterdir() if item.name.startswith(".run-inputs.json.")], [])

    def test_write_utf8_reports_exhausted_replace_lock_and_cleans_temp(self):
        from contextcanon.parser import ContextCanonError

        root = Path(tempfile.mkdtemp())
        path = root / "run-inputs.json"
        path.write_text("before\n", encoding="utf-8")

        with mock.patch(
            "contextcanon.onboarding_workspace.os.replace",
            side_effect=PermissionError(5, "simulated persistent Windows lock"),
        ), mock.patch("contextcanon.onboarding_workspace.time.sleep"):
            with self.assertRaisesRegex(ContextCanonError, "after retrying a temporary filesystem lock"):
                write_utf8(path, "after\n")

        self.assertEqual(path.read_text(encoding="utf-8"), "before\n")
        self.assertEqual([item for item in root.iterdir() if item.name.startswith(".run-inputs.json.")], [])
'''
if marker not in text:
    raise SystemExit("workspace test marker missing")
text = text.replace(marker, additions + marker, 1)
tests.write_text(text, encoding="utf-8", newline="\n")


# Regressions for #33.
tests = Path("tests/test_onboarding_reusable_contexts.py")
text = tests.read_text(encoding="utf-8")
text = text.replace("import unittest\n", "import unittest\nfrom types import SimpleNamespace\n", 1)
text = text.replace(
    "    refresh_reusable_contexts,\n)",
    "    refresh_reusable_contexts,\n    render_reusable_contexts,\n)",
    1,
)
old_assertions = '''            self.assertIn("## Copy-ready Assignment lines — generated", canonical)
            self.assertIn(
                "- **AI Workstation** (`.`) ← **Development Workflow** (`0.2.0-draft`)",
                canonical,
            )
            self.assertIn(
                "- **Bootstrap** (`bootstrap`) ← **Development Workflow** (`0.2.0-draft`)",
                canonical,
            )
'''
new_assertions = '''            self.assertIn("Assignment syntax:", canonical)
            self.assertNotIn("## Copy-ready Assignment lines — generated", canonical)
            self.assertIn("Example first line using entries from this project", canonical)
            self.assertIn(
                "- **AI Workstation** (`.`) ← **Development Workflow** (`0.2.0-draft`)",
                canonical,
            )
            self.assertIn("Use one desired entry as the left-hand side of `←`.", canonical)
            self.assertIn("Use one desired name/version entry as the right-hand side of `←`.", canonical)
'''
if old_assertions not in text:
    raise SystemExit("reusable-context assertions anchor missing")
text = text.replace(old_assertions, new_assertions, 1)
marker = '\n    def test_accepted_assignment_is_explicit_placement_reasoning_input(self) -> None:\n'
addition = r'''
    def test_assignment_help_scales_linearly_without_cartesian_product(self) -> None:
        nodes = tuple(
            HumanStructureNode(
                f"N-{index:03d}",
                f"Project Node {index}",
                "." if index == 0 else f"area-{index}",
                "current",
                None if index == 0 else "N-000",
                f"N-{index:03d}",
            )
            for index in range(20)
        )
        structure = HumanStructurePlan(
            evidence_digest="a" * 64,
            proposal_digest="b" * 64,
            nodes=nodes,
            fixed_markdown=(),
            structure_digest="c" * 64,
        )
        packages = tuple(
            SimpleNamespace(
                metadata=SimpleNamespace(name=f"Reusable Node {index}", version=f"1.0.{index}"),
                package_digest=f"{index + 1:064x}",
            )
            for index in range(40)
        )

        rendered = render_reusable_contexts("a" * 64, structure, "pending", ("catalog",), packages, ())
        assignment_like = [line for line in rendered.splitlines() if line.startswith("- **") and " ← " in line]

        self.assertEqual(len(assignment_like), 2)  # one grammar line + one current-project syntax example
        self.assertIn("Project Node 19", rendered)
        self.assertIn("Reusable Node 39", rendered)
        self.assertNotIn("Copy-ready Assignment lines", rendered)
        self.assertLess(len(rendered.splitlines()), 140)

'''
if marker not in text:
    raise SystemExit("reusable-context test insertion marker missing")
text = text.replace(marker, "\n" + addition + marker, 1)
tests.write_text(text, encoding="utf-8", newline="\n")


# Regression for #34.
tests = Path("tests/test_onboarding_walkthrough_current.py")
text = tests.read_text(encoding="utf-8")
marker = '\n\nif __name__ == "__main__":\n'
addition = r'''

    def test_root_readme_teaches_snapshot_variable_before_reuse(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        onboarding = text.split("### Structure-first experimental run", 1)[1].split("## Maintain an onboarded project", 1)[0]

        self.assertIn("$SNAPSHOT = '.context/onboarding/<evidence-digest>'", onboarding)
        self.assertIn("SNAPSHOT='.context/onboarding/<evidence-digest>'", onboarding)
        self.assertIn(r"set SNAPSHOT=.context\onboarding\<evidence-digest>", onboarding)
        self.assertIn("contextcanon onboard structure-instruction $SNAPSHOT", onboarding)
        self.assertIn("contextcanon-onboarding/PLAN.md", onboarding)
        self.assertNotIn("contextcanon onboard structure-preview .context/onboarding/<evidence-digest>", onboarding)
'''
if marker not in text:
    raise SystemExit("walkthrough test marker missing")
text = text.replace(marker, addition + marker, 1)
tests.write_text(text, encoding="utf-8", newline="\n")
