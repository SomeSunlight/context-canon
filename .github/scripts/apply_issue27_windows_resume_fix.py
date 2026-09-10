from pathlib import Path
import re

# Temporary gated applicator for the Issue #27 Windows/resume owner-test follow-up.


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one replacement target, found {count}: {old[:120]!r}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


def replace_count(path: str, old: str, new: str, expected: int) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    if count != expected:
        raise SystemExit(f"{path}: expected {expected} replacement targets, found {count}: {old[:120]!r}")
    p.write_text(text.replace(old, new), encoding="utf-8")


def replace_regex(path: str, pattern: str, replacement: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    updated, count = re.subn(pattern, lambda _match: replacement, text, count=1, flags=re.S)
    if count != 1:
        raise SystemExit(f"{path}: expected one regex replacement, found {count}: {pattern[:120]!r}")
    p.write_text(updated, encoding="utf-8")


# Public patch version stays consistent between CLI and package metadata.
replace_once("src/contextcanon/version.py", '__version__ = "0.7.2"', '__version__ = "0.7.3"')
replace_once("pyproject.toml", 'version = "0.7.2"', 'version = "0.7.3"')

# Windows-safe immutable package publication: exact verification remains authoritative;
# only transient directory-publication failures are retried.
replace_once("src/contextcanon/sources.py", "import tempfile\n", "import tempfile\nimport time\n")
replace_regex(
    "src/contextcanon/sources.py",
    r"def _install_package\(node_root: Path, candidate_root: Path, candidate: CompiledPackage\) -> None:\n.*?\n\ndef _render_source_pin_text",
    '''def _installed_package_matches(destination: Path, candidate: CompiledPackage) -> bool:
    if not destination.exists():
        return False
    existing = load_package(destination)
    if (
        existing.metadata.id == candidate.metadata.id
        and existing.normalized_digest == candidate.normalized_digest
        and existing.package_digest == candidate.package_digest
    ):
        return True
    raise ContextCanonError(f"Accepted Source store path exists with different content: {destination}")


def _publish_package_directory(temporary: Path, destination: Path, candidate: CompiledPackage) -> None:
    # Windows can transiently deny a directory rename while a scanner/indexer
    # has just-opened package files. Keep the publication atomic: retry only
    # the final rename, and accept an appearing destination only after exact
    # package verification proves that another writer published the same bytes.
    retry_delays = (0.05, 0.10, 0.20, 0.40, 0.80)
    for attempt in range(len(retry_delays) + 1):
        try:
            os.replace(temporary, destination)
            return
        except (PermissionError, FileExistsError) as exc:
            if _installed_package_matches(destination, candidate):
                return
            if attempt == len(retry_delays):
                raise ContextCanonError(
                    f"Could not publish immutable package {candidate.metadata.name} {candidate.metadata.version} "
                    f"to {destination} after retrying a temporary filesystem lock: {exc}"
                ) from exc
            time.sleep(retry_delays[attempt])


def _install_package(node_root: Path, candidate_root: Path, candidate: CompiledPackage) -> None:
    store = node_root / ".context" / "sources"
    store.mkdir(parents=True, exist_ok=True)
    destination = store / candidate.package_digest

    if _installed_package_matches(destination, candidate):
        return

    temporary = Path(tempfile.mkdtemp(prefix=f".{candidate.package_digest[:12]}-", dir=store))
    try:
        manifest_source = candidate_root / PACKAGE_MANIFEST_PATH
        manifest_destination = temporary / PACKAGE_MANIFEST_PATH
        manifest_destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(manifest_source, manifest_destination)
        for file in candidate.files:
            source = candidate_root / file.path
            target = temporary / file.path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)

        staged = load_package(temporary)
        if staged.normalized_digest != candidate.normalized_digest or staged.package_digest != candidate.package_digest:
            raise ContextCanonError("Staged Source package identity changed during acceptance")
        _publish_package_directory(temporary, destination, candidate)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)


def _render_source_pin_text''',
)

# Keep human diff fields human-scale: package fingerprints remain in Technical details.
replace_once(
    "src/contextcanon/cli.py",
    '            if entry.change == "modified" and entry.changed_fields and entry.category != "resource":\n                detail = " [" + ", ".join(entry.changed_fields) + "]"',
    '            if entry.change == "modified" and entry.changed_fields and entry.category not in {"resource", "source", "parent"}:\n                detail = " [" + ", ".join(entry.changed_fields) + "]"',
)

# Propagation: visible round delimiter, compact already-current skips, otherwise
# preserve the successful child-first narrative and separate Y/N authority.
replace_regex(
    "src/contextcanon/cli.py",
    r"def _run_propagation\(path: Path, \*, all_edges: bool, yes: bool\) -> int:\n.*?\n\ndef main",
    '''def _run_propagation(path: Path, *, all_edges: bool, yes: bool) -> int:
    repo_root, start_root, edges = _propagation_scope(path, all_edges)
    if not edges:
        print("No Parent/Child relationships found in the selected propagation scope.")
        return 0
    if all_edges:
        scope = "across all Context Nodes in this repository"
    else:
        start = parse_node(start_root, repo_root)
        scope = f"below {start.metadata.name}"
    print("Propagation review")
    print(f"{len(edges)} Parent/Child relationship(s) will be checked {scope}, top-down.")
    print("Each Child keeps its current Parent Context until you choose Y for that Child.")

    applied_count = 0
    for index, (child_root, parent, parent_root) in enumerate(edges, start=1):
        _report_version_bump(ensure_node_version_advanced(parent_root, repo_root))
        child = parse_node(child_root, repo_root)
        child_label = child_root.relative_to(repo_root).as_posix() or "."
        child_compiled = Compiler(repo_root).compile(child_root)
        parent_index = next(i for i, ref in enumerate(child_compiled.parsed.parents) if ref.id == parent.id)
        current_parent = child_compiled.parent_packages[parent_index]
        live_parent = Compiler(repo_root).compile(parent_root)

        print("")
        print("------------------------------------------------------------------------")
        print(f"Review {index}/{len(edges)} — Child: {child.metadata.name} ({child_label})")
        print("------------------------------------------------------------------------")

        if current_parent.package_digest == live_parent.package_digest:
            print(
                f"Already current: {child.metadata.name} uses "
                f"{live_parent.metadata.name} {live_parent.metadata.version}. No action needed."
            )
            continue

        result, receipt = review_parent_candidate(child_root, parent.id)
        local_effect = preview_parent_candidate_effect(child_root, parent.id)

        print("Parent Context:")
        print(f"  This Child currently uses: {current_parent.metadata.name} {current_parent.metadata.version}")
        print(f"  New Parent version available: {live_parent.metadata.name} {live_parent.metadata.version}")
        print(f"  Nothing in {child.metadata.name} has changed yet.")

        print("")
        print(f'What changed in Parent "{live_parent.metadata.name}" since the version used by this Child:')
        print(f"  Version: {current_parent.metadata.version} -> {live_parent.metadata.version}")
        print(f"  Summary: {_human_change_summary(result, exclude_categories={'node'})}")
        _print_human_change_details(result, exclude_categories={"node"})

        if result.is_empty:
            print("")
            print(f"Result: {child.metadata.name} already uses this exact Parent package; no update is needed.")
            continue

        parent_effect_summary = _human_change_summary(result, include_categories={"rule", "topic", "resource"})
        child_effect_summary = _human_change_summary(local_effect, include_categories={"rule", "topic", "resource"})
        print("")
        print(f'What would change in Child "{child.metadata.name}" if you choose Y:')
        print(f"  Effective Context: {child_effect_summary}")
        print("  Existing Overrides/Removes, local Rules and other imported Contexts are already reflected in this preview.")
        if child_effect_summary != parent_effect_summary:
            print("  The effective Child change differs from the raw Parent change:")
            _print_human_change_details(local_effect, exclude_categories={"node", "parent", "source"})
        print("  This Child's own version will be checked and may receive the automatic minimum patch bump.")
        print("  Its generated CONTEXT.md will continue to show the previous Context until you rebuild later.")

        print("")
        print(f'Before choosing Y for Child "{child.metadata.name}", check:')
        print(f"  1. Should these Parent changes apply to {child.metadata.name}? If not, use a justified Override/Remove.")
        print("  2. Do they fit with this Child's other imported Contexts and local Rules? Import order is never precedence.")
        print(
            f"  3. Does {child.metadata.name} expose a problem in the Parent change itself? "
            f"If so, fix {live_parent.metadata.name} upstream rather than patching every Child."
        )

        print("")
        print("Technical details:")
        print(f"  Parent Node ID: {parent.id}")
        print(f"  Child Node ID: {child.metadata.id}")
        print(f"  Parent normalized digest: {result.before_normalized_digest} -> {result.after_normalized_digest}")
        print(f"  Parent package digest: {result.before_package_digest} -> {result.after_package_digest}")
        print("  Exact changed identities:")
        symbols = {"added": "+", "removed": "-", "modified": "~"}
        for entry in result.entries:
            if entry.category == "node":
                continue
            print(f"    {symbols[entry.change]} {entry.category}: {entry.identity}")
        try:
            receipt_label = receipt.relative_to(child_root).as_posix()
        except ValueError:
            receipt_label = str(receipt)
        print(f"  Review receipt: {receipt_label}")

        if not yes and not _confirm(f'Apply this Parent update to Child "{child.metadata.name}"?'):
            print(f'No Parent update applied to Child "{child.metadata.name}".')
            print("Propagation stopped here; earlier applied steps remain in place, and later Children were not reviewed yet.")
            return 0

        accepted = accept_parent_candidate(child_root, parent.id)
        applied_count += 1
        print(
            f'Applied Parent update to Child "{child.metadata.name}": '
            f"{current_parent.metadata.name} {current_parent.metadata.version} -> {accepted.metadata.name} {accepted.metadata.version}"
        )
        _report_version_bump(ensure_node_version_advanced(child_root, repo_root))

    print("")
    print("------------------------------------------------------------------------")
    print(f"Propagation review complete: applied {applied_count} changed Parent/Child update(s).")
    print("The generated CONTEXT.md files still show their previous generated Context until rebuild.")
    print("Next from the repository root:")
    print("  contextcanon build --all .")
    print("  contextcanon check --all .")
    return 0


def main''',
)

# Finish the Source-update wording polish collected during the owner test.
replace_count(
    "src/contextcanon/cli.py",
    'print(f"Source update for local Node: {parsed.metadata.name}")',
    'print(f"Source update for Node: {parsed.metadata.name}")',
    2,
)
replace_once(
    "src/contextcanon/cli.py",
    '''                print("Current local Source:")
                print(f"  {current.name} {current.version}")
                print(f"  This is the last Source version put into use for {parsed.metadata.name}.")
                print("New candidate found:")
                print(f"  {candidate.metadata.name} {candidate.metadata.version}")
                print(f"  Looked up from: {lookup}")
                print(f"This command is offering an update to {parsed.metadata.name}; its Context has not changed yet.")''',
    '''                print("Current Source:")
                print(f"  {parsed.metadata.name} uses {current.name} {current.version}.")
                print("Candidate found:")
                print(f"  {candidate.metadata.name} {candidate.metadata.version}")
                print(f"  Found at: {lookup}")
                print(
                    f"Review the changes below, then choose whether {parsed.metadata.name} "
                    "should use this newer Source version."
                )''',
)
replace_once(
    "src/contextcanon/cli.py",
    '''                print(f'Local update offered for Node "{parsed.metadata.name}":')
                print(f"  Source: {current.name} {current.version} -> {candidate.metadata.name} {candidate.metadata.version}")
                print(
                    "  Effective Context after existing local Overrides/Removes and other imports: "
                    + _human_change_summary(local_effect, include_categories={"rule", "topic", "resource"})
                )
                print("  Existing local Overrides/Removes and other imported Context are already reflected in this preview.")
                print("  This Node's own version will be checked and may receive the automatic minimum patch bump.")
                print("  Generated CONTEXT.md is rebuilt later; choosing Y here does not rebuild it.")''',
    '''                print(f'What Y would change in Node "{parsed.metadata.name}":')
                print(
                    f"  Source used by {parsed.metadata.name}: {current.name} {current.version} -> "
                    f"{candidate.metadata.name} {candidate.metadata.version}"
                )
                print(
                    "  Effective Context: "
                    + _human_change_summary(local_effect, include_categories={"rule", "topic", "resource"})
                )
                print("  This preview already includes local Overrides/Removes and other imported Contexts.")
                print("  This Node's own version will be checked and may receive the automatic minimum patch bump.")
                print("  Its generated CONTEXT.md will keep showing the previous Context until you rebuild later.")''',
)
replace_once(
    "src/contextcanon/cli.py",
    '''                    print("What comes after this local update:")
                    print(
                        f"  {len({child_root for child_root, _, _ in downstream})} downstream Node(s) are connected through this Parent/Child chain."
                    )
                    print("  They keep their current Parent snapshots until their own review.")
                    print("  Relationships that may need review:")''',
    '''                    print("If you choose Y, review these Child Nodes next:")
                    print("  The Y below changes this Node only; its Children keep their current Parent Context until reviewed.")
                    print(
                        f"  {len({child_root for child_root, _, _ in downstream})} Child Node(s) are reachable through the Parent/Child chain."
                    )
                    print("  Parent/Child path to review:")''',
)
replace_once(
    "src/contextcanon/cli.py",
    '''                    print("  After applying this update, review that chain top-down in one guided run:")
                    print(f"    {propagate_command}")
                    print("  It still asks separately before applying each changed Parent -> Child step.")''',
    '''                    print("  Review that path top-down in one guided run:")
                    print(f"    {propagate_command}")
                    print("    There you will be asked separately before each changed Child starts using its newer Parent Context.")''',
)
replace_once(
    "src/contextcanon/cli.py",
    '''                    print("What comes after this local update:")
                    print("  No Child Nodes depend on this Node through a semantic Parent relationship.")''',
    '''                    print("If you choose Y:")
                    print("  No Child Nodes use this Node as a semantic Parent, so no propagation review follows.")''',
)
replace_once(
    "src/contextcanon/cli.py",
    '                if not args.yes and not _confirm(f"Apply this Source update to local Node {parsed.metadata.name}?"):',
    '                if not args.yes and not _confirm(f\'Apply this Source update to Node "{parsed.metadata.name}"?\'):',
)
replace_once(
    "src/contextcanon/cli.py",
    '                print(f"Updated local Source for {parsed.metadata.name}: {current.version} -> {accepted.metadata.version}")',
    '                print(f\'Node "{parsed.metadata.name}" now uses {accepted.metadata.name} {accepted.metadata.version} (was {current.name} {current.version}).\')',
)

# Regression: transient package publish lock succeeds without weakening the pin transaction.
replace_once(
    "tests/test_source_acceptance.py",
    "from contextcanon.sources import accept_source_candidate, review_source_candidate\n",
    "import contextcanon.sources as sources_module\nfrom contextcanon.sources import accept_source_candidate, review_source_candidate\n",
)
replace_once(
    "tests/test_source_acceptance.py",
    '''    def test_failed_atomic_pin_replace_preserves_old_source_and_old_build(self):''',
    '''    def test_package_publish_retries_transient_permission_error(self):
        _, v1, _ = self.make_provider("1.0.0", "Prefer explicit Python v1.")
        _, v2, candidate = self.make_provider("2.0.0", "Prefer explicit Python v2.")
        consumer = self.make_consumer(v1)
        review_source_candidate(consumer, "node-python", candidate)

        package_destination = consumer / ".context" / "sources" / v2.package_digest
        real_replace = sources_module.os.replace
        attempts = {"package": 0}

        def flaky_replace(src, dst):
            if Path(dst) == package_destination and attempts["package"] == 0:
                attempts["package"] += 1
                raise PermissionError(13, "simulated transient Windows access denied")
            return real_replace(src, dst)

        with patch("contextcanon.sources.os.replace", side_effect=flaky_replace), patch(
            "contextcanon.sources.time.sleep", return_value=None
        ):
            accepted = accept_source_candidate(consumer, "node-python", candidate)

        self.assertEqual(attempts["package"], 1)
        self.assertEqual(accepted.package_digest, v2.package_digest)
        self.assertTrue((package_destination / ".context/package.json").is_file())
        self.assertEqual(Compiler(consumer).compile(consumer).source_packages[0].package_digest, v2.package_digest)

    def test_failed_atomic_pin_replace_preserves_old_source_and_old_build(self):''',
)

# Regression: after a partial run, rerun skips already-current steps and asks only at the first stale Child.
replace_once(
    "tests/test_propagation_review_ux.py",
    '''    def test_top_level_propagate_scopes_from_current_node_and_all_broadens_scope(self):''',
    '''    def test_propagation_rerun_skips_already_current_steps_and_resumes_at_stale_child(self):
        repo = Path(tempfile.mkdtemp())
        try:
            (repo / ".git").mkdir()
            root = write_node(repo, repo, "root", "Root", "1.0.0", "Root old.")
            child = write_child(repo, repo / "child", "child", "Child", "..", root)
            write_child(repo, repo / "child" / "grand", "grand", "Grand", "..", child)
            write_node(repo, repo, "root", "Root", "1.1.0", "Root new.")

            first = io.StringIO()
            with contextlib.redirect_stdout(first), mock.patch("builtins.input", side_effect=["y", "n"]):
                rc = cli_main(["propagate", str(repo)])
            self.assertEqual(rc, 0, first.getvalue())
            self.assertIn('Applied Parent update to Child "Child"', first.getvalue())
            self.assertIn('No Parent update applied to Child "Grand".', first.getvalue())

            second = io.StringIO()
            with contextlib.redirect_stdout(second), mock.patch("builtins.input", return_value="n") as prompt:
                rc = cli_main(["propagate", str(repo)])
            self.assertEqual(rc, 0, second.getvalue())
            text = second.getvalue()
            self.assertIn("------------------------------------------------------------------------", text)
            self.assertIn("Review 1/2 — Child: Child (child)", text)
            self.assertIn("Already current: Child uses Root 1.1.0. No action needed.", text)
            self.assertIn("Review 2/2 — Child: Grand (child/grand)", text)
            self.assertIn('Apply this Parent update to Child "Grand"?', text)
            self.assertEqual(prompt.call_count, 1)
        finally:
            shutil.rmtree(repo, ignore_errors=True)

    def test_top_level_propagate_scopes_from_current_node_and_all_broadens_scope(self):''',
)

# Update existing assertions to the polished Source narrative and public version.
replace_once("tests/test_configuration_and_update_ux.py", '"contextcanon 0.7.2"', '"contextcanon 0.7.3"')
replace_once(
    "tests/test_configuration_and_update_ux.py",
    'self.assertIn("This command is offering an update to Consumer; its Context has not changed yet.", out.getvalue())',
    'self.assertIn("Review the changes below, then choose whether Consumer should use this newer Source version.", out.getvalue())',
)
replace_once("tests/test_configuration_and_update_ux.py", 'self.assertIn("Current local Source:", out.getvalue())', 'self.assertIn("Current Source:", out.getvalue())')
replace_once("tests/test_configuration_and_update_ux.py", 'self.assertIn("New candidate found:", out.getvalue())', 'self.assertIn("Candidate found:", out.getvalue())')
replace_once(
    "tests/test_configuration_and_update_ux.py",
    'self.assertIn("Local update offered for Node \\"Consumer\\":", out.getvalue())',
    'self.assertIn("What Y would change in Node \\"Consumer\\":", out.getvalue())',
)
replace_once(
    "tests/test_configuration_and_update_ux.py",
    'self.assertIn("Effective Context after existing local Overrides/Removes and other imports: 1 rule changed", out.getvalue())',
    'self.assertIn("Effective Context: 1 rule changed", out.getvalue())',
)
replace_once(
    "tests/test_configuration_and_update_ux.py",
    'self.assertIn("What comes after this local update:", out.getvalue())',
    'self.assertIn("If you choose Y, review these Child Nodes next:", out.getvalue())',
)
replace_once(
    "tests/test_configuration_and_update_ux.py",
    'self.assertIn("review that chain top-down in one guided run:", out.getvalue())',
    'self.assertIn("Review that path top-down in one guided run:", out.getvalue())',
)
replace_once(
    "tests/test_configuration_and_update_ux.py",
    'self.assertIn("asks separately before applying each changed Parent -> Child step", out.getvalue())',
    'self.assertIn("asked separately before each changed Child starts using its newer Parent Context", out.getvalue())',
)

# Mark this planned follow-up complete only inside the gated product candidate;
# if the gate fails, none of these edits are pushed.
plan = Path("PLAN.md")
plan_text = plan.read_text(encoding="utf-8")
section = "## Owner-test Windows propagation resume follow-up: Issue #27"
start = plan_text.index(section)
end = plan_text.find("\n## ", start + len(section))
if end == -1:
    end = len(plan_text)
block = plan_text[start:end].replace("- [ ] ", "- [x] ")
plan.write_text(plan_text[:start] + block + plan_text[end:], encoding="utf-8")
