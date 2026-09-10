from pathlib import Path
import re


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one replacement target, found {count}: {old[:120]!r}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


def replace_regex(path: str, pattern: str, replacement: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
    if count != 1:
        raise SystemExit(f"{path}: expected one regex replacement, found {count}: {pattern[:120]!r}")
    p.write_text(updated, encoding="utf-8")


replace_once(
    "src/contextcanon/version.py",
    '__version__ = "0.7.1"',
    '__version__ = "0.7.2"',
)

replace_once(
    "src/contextcanon/cli.py",
    "from .sources import adopt_source_package, accept_parent_candidate, accept_source_candidate, preview_source_candidate_effect, review_parent_candidate, review_source_candidate",
    "from .sources import adopt_source_package, accept_parent_candidate, accept_source_candidate, preview_parent_candidate_effect, preview_source_candidate_effect, review_parent_candidate, review_source_candidate",
)

replace_regex(
    "src/contextcanon/cli.py",
    r"def _human_entry_label\(entry\) -> str:\n.*?\n\ndef _print_human_change_details",
    '''def _human_entry_label(entry) -> str:
    data = entry.after or entry.before or {}
    if entry.category in {"rule", "topic"}:
        stable_id = entry.identity.rsplit("#", 1)[-1]
        title = data.get("title")
        return f"{stable_id} — {title}" if title else stable_id
    if entry.category in {"source", "parent"}:
        return data.get("name") or entry.identity
    return entry.identity


def _print_human_change_details''',
)

replace_once(
    "src/contextcanon/cli.py",
    '''            if entry.category == "rule":
                before = entry.before or {}
                after = entry.after or {}
                if entry.change == "added" and after.get("statement"):
                    print(f"      {after['statement']}")
                elif entry.change == "removed" and before.get("statement"):
                    print(f"      {before['statement']}")
                elif entry.change == "modified" and before.get("statement") != after.get("statement"):
                    if before.get("statement"):
                        print(f"      before: {before['statement']}")
                    if after.get("statement"):
                        print(f"      after:  {after['statement']}")
            elif entry.category == "topic" and entry.change == "added":''',
    '''            if entry.category in {"source", "parent"} and entry.change == "modified":
                before = entry.before or {}
                after = entry.after or {}
                before_version = before.get("version")
                after_version = after.get("version")
                if before_version and after_version and before_version != after_version:
                    print(f"      version: {before_version} -> {after_version}")
            elif entry.category == "rule":
                before = entry.before or {}
                after = entry.after or {}
                if entry.change == "added" and after.get("statement"):
                    print(f"      {after['statement']}")
                elif entry.change == "removed" and before.get("statement"):
                    print(f"      {before['statement']}")
                elif entry.change == "modified" and before.get("statement") != after.get("statement"):
                    if before.get("statement"):
                        print(f"      before: {before['statement']}")
                    if after.get("statement"):
                        print(f"      after:  {after['statement']}")
            elif entry.category == "topic" and entry.change == "added":''',
)

replace_regex(
    "src/contextcanon/cli.py",
    r"def _print_propagation_review_guide\(scope: str, edge_count: int\) -> None:\n.*?\n\ndef _run_propagation",
    '''def _print_propagation_review_guide(scope: str, edge_count: int) -> None:
    print("Propagation review")
    print(f"{edge_count} Parent/Child update(s) will be checked {scope}, top-down.")
    print("Each Child keeps its current Parent Context until you choose Y for that Child.")


def _run_propagation''',
)

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
    _print_propagation_review_guide(scope, len(edges))

    applied_count = 0
    for index, (child_root, parent, parent_root) in enumerate(edges, start=1):
        _report_version_bump(ensure_node_version_advanced(parent_root, repo_root))
        child = parse_node(child_root, repo_root)
        child_label = child_root.relative_to(repo_root).as_posix() or "."
        child_compiled = Compiler(repo_root).compile(child_root)
        parent_index = next(i for i, ref in enumerate(child_compiled.parsed.parents) if ref.id == parent.id)
        current_parent = child_compiled.parent_packages[parent_index]
        live_parent = Compiler(repo_root).compile(parent_root)

        result, receipt = review_parent_candidate(child_root, parent.id)
        local_effect = preview_parent_candidate_effect(child_root, parent.id)

        print(f"\\nReview {index}/{len(edges)} — Child: {child.metadata.name} ({child_label})")
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

        parent_effect_summary = _human_change_summary(
            result, include_categories={"rule", "topic", "resource"}
        )
        child_effect_summary = _human_change_summary(
            local_effect, include_categories={"rule", "topic", "resource"}
        )
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
        print(f"  3. Does {child.metadata.name} expose a problem in the Parent change itself? If so, fix {live_parent.metadata.name} upstream rather than patching every Child.")

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
            print("Propagation stopped here; earlier accepted steps remain accepted, later Children were not reviewed yet.")
            return 0

        accepted = accept_parent_candidate(child_root, parent.id)
        applied_count += 1
        print(
            f'Applied Parent update to Child "{child.metadata.name}": '
            f"{current_parent.metadata.name} {current_parent.metadata.version} -> {accepted.metadata.name} {accepted.metadata.version}"
        )
        _report_version_bump(ensure_node_version_advanced(child_root, repo_root))

    print(f"Propagation review complete: applied {applied_count} changed Parent/Child update(s).")
    print("The generated CONTEXT.md files still show their previous generated Context until rebuild.")
    print("Next from the repository root:")
    print("  contextcanon build --all .")
    print("  contextcanon check --all .")
    return 0


def main''',
)

replace_once(
    "src/contextcanon/cli.py",
    '''                print("Generated CONTEXT.md has not been rebuilt yet.")
                if downstream:
                    start_label = node_root.relative_to(repo_root).as_posix() or "."
                    propagate_command = "contextcanon propagate" if start_label == "." else f"contextcanon propagate {start_label}"
                    print("Next: review the downstream Parent/Child updates in one guided run:")
                    print(f"  {propagate_command}")
                    print("ContextCanon still asks separately before applying each changed step.")
                    print("After the intended reviews: contextcanon build --all . && contextcanon check --all .")
                else:
                    print("Next from the repository root: contextcanon build --all .")
                    print("Then: contextcanon check --all .")''',
    '''                if downstream:
                    start_label = node_root.relative_to(repo_root).as_posix() or "."
                    propagate_command = "contextcanon propagate" if start_label == "." else f"contextcanon propagate {start_label}"
                    print("The generated CONTEXT.md still shows the previous Context; rebuild after the downstream reviews.")
                    print("Next: review the downstream Parent/Child updates in one guided run:")
                    print(f"  {propagate_command}")
                    print("  There you will be asked separately before each changed Child starts using its newer Parent Context.")
                    print("After those reviews, rebuild and verify from the repository root:")
                    print("  contextcanon build --all .")
                    print("  contextcanon check --all .")
                else:
                    print("The generated CONTEXT.md still shows the previous Context.")
                    print("Rebuild and verify from the repository root:")
                    print("  contextcanon build --all .")
                    print("  contextcanon check --all .")''',
)

# Add a non-mutating effective Parent->Child preview, mirroring Source preview semantics.
insert_before = "\ndef accept_parent_candidate(node_root: Path, parent_id: str | None = None) -> CompiledPackage:\n"
parent_preview = '''\ndef preview_parent_candidate_effect(node_root: Path, parent_id: str | None = None) -> ContextDiff:
    """Preview the Child's effective Context with the current live Parent candidate.

    The Child's accepted Parent pin and authored source remain unchanged. Local
    Overrides/Removes, local Rules, other Parents and Sources are applied by
    the normal compiler so the returned diff describes the effective result of
    accepting this Parent update for this Child.
    """

    node_root = node_root.resolve()
    repo_root = find_repo_root(node_root)
    compiler = Compiler(repo_root)
    current_compiled = compiler.compile(node_root)
    parent_index, parent_ref = _parent_index(current_compiled, parent_id)
    current = current_compiled.parent_packages[parent_index]

    parent_root = compiler._resolve_source_root(node_root, parent_ref.locator)
    ensure_node_version_advanced(parent_root, repo_root)
    live_parent = Compiler(repo_root).compile(parent_root)
    candidate = compiled_package(live_parent)
    if candidate.metadata.id != parent_ref.id:
        raise ContextCanonError(
            f"Live Parent Node ID {candidate.metadata.id} does not match accepted Parent {parent_ref.name} ({parent_ref.id})"
        )
    _require_candidate_version_advance(current, candidate, "Parent")
    _validate_parent_candidate_composition(compiler, current_compiled, parent_index, candidate)

    candidate_root = _store_parent_candidate(node_root, live_parent)
    candidate_resources = {
        file.path: (candidate_root / file.path).read_bytes()
        for file in candidate.files
        if file.path.startswith("CONTEXT/references/")
    }
    preview_source = _render_parent_pin_text(node_root, parent_ref.id, candidate)
    preview_compiled = Compiler(
        repo_root,
        source_overrides={node_root: preview_source},
        package_overrides={(node_root, candidate.package_digest): (candidate, candidate_resources)},
    ).compile(node_root)
    return diff_compiled(current_compiled, preview_compiled)

'''
replace_once("src/contextcanon/sources.py", insert_before, parent_preview + insert_before)

replace_regex(
    "src/contextcanon/sources.py",
    r"def _write_parent_pin\(node_root: Path, parent_id: str, candidate: CompiledPackage\) -> None:\n.*?\n\ndef install_source_package",
    '''def _render_parent_pin_text(node_root: Path, parent_id: str, candidate: CompiledPackage) -> str:
    path = node_root / "CONTEXT.src.md"
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    found = 0
    for index, line in enumerate(lines):
        visible = _SOURCE_LINE_RE.match(line)
        if not visible:
            continue
        search_end = min(index + 5, len(lines))
        for comment_index in range(index + 1, search_end):
            comment = _PARENT_COMMENT_RE.match(lines[comment_index])
            if not comment:
                continue
            attrs = _ATTR_RE.findall(comment.group("attrs"))
            if not attrs or dict(attrs).get("id") != parent_id:
                continue
            found += 1
            lines[index] = visible.group("prefix") + f"`{candidate.metadata.version}`" + visible.group("ending")
            updated: list[tuple[str, str]] = []
            seen_version = False
            for key, value in attrs:
                if key == "version":
                    updated.append((key, candidate.metadata.version))
                    seen_version = True
                elif key not in {"normalized-digest", "package-digest"}:
                    updated.append((key, value))
            if not seen_version:
                updated.append(("version", candidate.metadata.version))
            updated.extend([
                ("normalized-digest", candidate.normalized_digest),
                ("package-digest", candidate.package_digest),
            ])
            attrs_text = " ".join(f'{key}="{value}"' for key, value in updated)
            lines[comment_index] = f"{comment.group('indent')}<!-- ctx:parent {attrs_text} -->{comment.group('ending')}"
            break
    if found != 1:
        raise ContextCanonError(f"Could not find exactly one semantic Parent Node ID {parent_id} in {path}")
    return "".join(lines)


def _write_parent_pin(node_root: Path, parent_id: str, candidate: CompiledPackage) -> None:
    path = node_root / "CONTEXT.src.md"
    _atomic_write_text(path, _render_parent_pin_text(node_root, parent_id, candidate))


def install_source_package''',
)

# Strengthen propagation UX regression around the novice-facing narrative.
test_path = Path("tests/test_propagation_review_ux.py")
test_text = test_path.read_text(encoding="utf-8")
test_text = test_text.replace("import unittest\n", "import unittest\nfrom unittest import mock\n", 1)
anchor = "    def test_top_level_propagate_scopes_from_current_node_and_all_broadens_scope(self):\n"
new_test = '''    def test_propagation_review_tells_parent_change_and_effective_child_story_before_ids(self):
        repo = Path(tempfile.mkdtemp())
        try:
            (repo / ".git").mkdir()
            root = write_node(repo, repo, "root-id", "Root", "1.0.0", "Root old.")
            write_child(repo, repo / "child", "child-id", "Child", "..", root)
            write_node(repo, repo, "root-id", "Root", "1.1.0", "Root new.")

            out = io.StringIO()
            with contextlib.redirect_stdout(out), mock.patch("builtins.input", return_value="n"):
                rc = cli_main(["propagate", str(repo)])
            self.assertEqual(rc, 0, out.getvalue())
            text = out.getvalue()
            self.assertIn("Review 1/1 — Child: Child (child)", text)
            self.assertIn("This Child currently uses: Root 1.0.0", text)
            self.assertIn("New Parent version available: Root 1.1.0", text)
            self.assertIn('What changed in Parent "Root" since the version used by this Child:', text)
            self.assertIn("RULE-1 — Policy", text)
            self.assertIn("before: Root old.", text)
            self.assertIn("after:  Root new.", text)
            self.assertIn('What would change in Child "Child" if you choose Y:', text)
            self.assertIn("Effective Context: 1 rule changed", text)
            self.assertIn('Before choosing Y for Child "Child", check:', text)
            self.assertLess(text.index('What changed in Parent "Root"'), text.index("Technical details:"))
            self.assertLess(text.index('What would change in Child "Child"'), text.index("Technical details:"))
            self.assertIn("Parent Node ID: root-id", text)
            self.assertIn('No Parent update applied to Child "Child".', text)
        finally:
            shutil.rmtree(repo, ignore_errors=True)

'''
if anchor not in test_text:
    raise SystemExit("tests/test_propagation_review_ux.py: insertion anchor missing")
test_path.write_text(test_text.replace(anchor, new_test + anchor, 1), encoding="utf-8")

# Mark this bounded PLAN block complete; the workflow only commits it after all gates pass.
plan = Path("PLAN.md")
text = plan.read_text(encoding="utf-8")
marker = "## Owner-test propagation narrative follow-up: Issue #27"
start = text.find(marker)
if start < 0:
    raise SystemExit("PLAN.md propagation narrative block missing")
head = text[:start]
tail = text[start:]
tail = tail.replace("- [ ] ", "- [x] ", 6)
plan.write_text(head + tail, encoding="utf-8")
