from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def replace_once(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one replacement target, found {count}: {old[:120]!r}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


def replace_between(path: str, start_marker: str, end_marker: str, replacement: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    start = text.index(start_marker)
    end = text.index(end_marker, start)
    target.write_text(text[:start] + replacement + text[end:], encoding="utf-8")


# Patch-level public CLI refinement after the 0.7.0 maintenance workflow feature.
replace_once("pyproject.toml", 'version = "0.7.0"', 'version = "0.7.1"')
replace_once("src/contextcanon/version.py", '__version__ = "0.7.0"', '__version__ = "0.7.1"')
replace_once(
    "tests/test_configuration_and_update_ux.py",
    'self.assertEqual(out.getvalue().strip(), "contextcanon 0.7.0")',
    'self.assertEqual(out.getvalue().strip(), "contextcanon 0.7.1")',
)

# Provide a deterministic preview of the effective local Context before Source acceptance.
replace_once(
    "src/contextcanon/sources.py",
    "from .diff import ContextDiff\n",
    "from .diff import ContextDiff, diff_compiled\n",
)

preview_marker = "def accept_source_candidate(node_root: Path, source_id: str, candidate_root: Path) -> CompiledPackage:\n"
preview_code = '''def preview_source_candidate_effect(
    node_root: Path,
    source_id: str,
    candidate_root: Path,
) -> ContextDiff:
    """Preview the consumer's effective compiled Context with one candidate Source pin.

    No accepted package or authored source is changed. Existing local
    Overrides/Removes and all other imported Context are applied by the normal
    compiler, so this diff describes what would actually become effective in
    the consumer if the candidate were accepted.
    """

    node_root = node_root.resolve()
    candidate_root = candidate_root.resolve()
    repo_root = find_repo_root(node_root)
    candidate = load_package(candidate_root)
    current_compiled = Compiler(repo_root).compile(node_root)
    source_index, source_ref = _source_index(current_compiled, source_id)
    current = current_compiled.source_packages[source_index]

    if candidate.metadata.id != source_ref.id:
        raise ContextCanonError(
            f"Candidate Node ID {candidate.metadata.id} does not match Source {source_ref.name} ({source_ref.id})"
        )
    _require_candidate_version_advance(current, candidate, "Source")
    _validate_candidate_composition(Compiler(repo_root), current_compiled, source_index, candidate)

    candidate_resources = {
        file.path: (candidate_root / file.path).read_bytes()
        for file in candidate.files
        if file.path.startswith("CONTEXT/references/")
    }
    preview_source = _render_source_pin_text(node_root, source_id, candidate)
    preview_compiled = Compiler(
        repo_root,
        source_overrides={node_root: preview_source},
        package_overrides={(node_root, candidate.package_digest): (candidate, candidate_resources)},
    ).compile(node_root)
    return diff_compiled(current_compiled, preview_compiled)


'''
replace_once("src/contextcanon/sources.py", preview_marker, preview_code + preview_marker)

source_pin_start = "def _write_source_pin(node_root: Path, source_id: str, candidate: CompiledPackage, *, accepted_ref: str | None = None) -> None:\n"
source_pin_end = "def _atomic_write_text(path: Path, content: str) -> None:\n"
source_pin_code = '''def _render_source_pin_text(
    node_root: Path,
    source_id: str,
    candidate: CompiledPackage,
    *,
    accepted_ref: str | None = None,
) -> str:
    path = node_root / "CONTEXT.src.md"
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    found = 0

    for index, line in enumerate(lines):
        visible = _SOURCE_LINE_RE.match(line)
        if not visible:
            continue
        search_end = min(index + 5, len(lines))
        for comment_index in range(index + 1, search_end):
            comment = _SOURCE_COMMENT_RE.match(lines[comment_index])
            if not comment:
                continue
            attrs = _ATTR_RE.findall(comment.group("attrs"))
            if not attrs or dict(attrs).get("id") != source_id:
                continue

            found += 1
            if found > 1:
                raise ContextCanonError(f"Source Node ID {source_id} appears more than once in {path}")

            if any(char in candidate.metadata.name for char in "]\\n\\r"):
                raise ContextCanonError(f"Source name cannot be represented safely: {candidate.metadata.name!r}")
            lines[index] = (
                visible.group("bullet")
                + f"[{candidate.metadata.name}]({visible.group('path')})"
                + visible.group("separator")
                + f"`{candidate.metadata.version}`"
                + visible.group("ending")
            )

            updated: list[tuple[str, str]] = []
            seen_version = False
            for key, value in attrs:
                if key == "version":
                    updated.append((key, candidate.metadata.version))
                    seen_version = True
                elif key == "ref" and accepted_ref is not None and re.fullmatch(r"[0-9a-f]{40}", value):
                    updated.append((key, accepted_ref))
                elif key not in {"normalized-digest", "package-digest"}:
                    updated.append((key, value))
            if not seen_version:
                updated.append(("version", candidate.metadata.version))
            updated.extend([
                ("normalized-digest", candidate.normalized_digest),
                ("package-digest", candidate.package_digest),
            ])
            attrs_text = " ".join(f'{key}="{value}"' for key, value in updated)
            lines[comment_index] = (
                f"{comment.group('indent')}<!-- ctx:source {attrs_text} -->{comment.group('ending')}"
            )
            break

    if found != 1:
        raise ContextCanonError(f"Could not find exactly one Source Node ID {source_id} in {path}")
    return "".join(lines)


def _write_source_pin(node_root: Path, source_id: str, candidate: CompiledPackage, *, accepted_ref: str | None = None) -> None:
    path = node_root / "CONTEXT.src.md"
    _atomic_write_text(
        path,
        _render_source_pin_text(node_root, source_id, candidate, accepted_ref=accepted_ref),
    )


'''
replace_between("src/contextcanon/sources.py", source_pin_start, source_pin_end, source_pin_code)

# Human narrative helpers for the guided CLI; generic deterministic diff remains unchanged.
replace_once(
    "src/contextcanon/cli.py",
    "from .sources import adopt_source_package, accept_parent_candidate, accept_source_candidate, review_parent_candidate, review_source_candidate\n",
    "from .sources import adopt_source_package, accept_parent_candidate, accept_source_candidate, preview_source_candidate_effect, review_parent_candidate, review_source_candidate\n",
)

confirm_marker = "def _parent_edges(repo_root: Path, start_root: Path | None = None):\n"
human_helpers = '''_HUMAN_CHANGE_NOUNS = {
    "parent": ("imported Parent", "imported Parents"),
    "source": ("imported Source", "imported Sources"),
    "change": ("local resolution", "local resolutions"),
    "rule": ("rule", "rules"),
    "topic": ("topic", "topics"),
    "resource": ("resource", "resources"),
}


def _human_change_summary(diff, *, include_categories: set[str] | None = None, exclude_categories: set[str] | None = None) -> str:
    include = include_categories
    exclude = exclude_categories or set()
    counts: dict[tuple[str, str], int] = {}
    for entry in diff.entries:
        if entry.category in exclude or (include is not None and entry.category not in include):
            continue
        key = (entry.category, entry.change)
        counts[key] = counts.get(key, 0) + 1
    action = {"added": "added", "removed": "removed", "modified": "changed"}
    parts: list[str] = []
    for category in ("parent", "source", "change", "rule", "topic", "resource"):
        singular, plural = _HUMAN_CHANGE_NOUNS[category]
        for change in ("added", "removed", "modified"):
            count = counts.get((category, change), 0)
            if count:
                parts.append(f"{count} {singular if count == 1 else plural} {action[change]}")
    return ", ".join(parts) if parts else "no effective Rule, Topic, or Resource changes"


def _human_entry_label(entry) -> str:
    data = entry.after or entry.before or {}
    if entry.category in {"rule", "topic"}:
        stable_id = entry.identity.rsplit("#", 1)[-1]
        title = data.get("title")
        return f"{stable_id} — {title}" if title else stable_id
    return entry.identity


def _print_human_change_details(diff, *, exclude_categories: set[str] | None = None) -> None:
    exclude = exclude_categories or set()
    headings = {
        "parent": "Imported Parent changes",
        "source": "Imported Source changes",
        "change": "Local resolution changes",
        "rule": "Rules",
        "topic": "Topics",
        "resource": "Resources",
    }
    symbols = {"added": "+", "removed": "-", "modified": "~"}
    grouped: dict[str, list[object]] = {}
    for entry in diff.entries:
        if entry.category in exclude:
            continue
        grouped.setdefault(entry.category, []).append(entry)
    for category in ("parent", "source", "change", "rule", "topic", "resource"):
        entries = grouped.get(category, [])
        if not entries:
            continue
        print(f"{headings[category]}:")
        for entry in entries:
            detail = ""
            if entry.change == "modified" and entry.changed_fields and entry.category != "resource":
                detail = " [" + ", ".join(entry.changed_fields) + "]"
            print(f"  {symbols[entry.change]} {_human_entry_label(entry)}{detail}")
            if entry.category == "rule":
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
            elif entry.category == "topic" and entry.change == "added":
                after = entry.after or {}
                if after.get("condition"):
                    print(f"      When: {after['condition']}")


def _source_lookup_description(repo_root: Path, current, source_id: str, requested_ref: str | None) -> str:
    configured = configured_source(repo_root, source_id)
    if configured is not None:
        _, repository = configured
        if repository.kind == "git":
            selected = requested_ref or repository.ref or "default branch"
            return f"{repository.location} @ {selected}"
        return f"local repository {repository.location}"
    if current.transport == "git":
        selected = requested_ref or current.transport_ref or "default branch"
        return f"legacy Git discovery {current.locator} @ {selected}"
    return current.locator


'''
replace_once("src/contextcanon/cli.py", confirm_marker, human_helpers + confirm_marker)

# Source list uses plain temporal language: this is the version currently in use here.
replace_once(
    "src/contextcanon/cli.py",
    'print(f"{package.metadata.name} | {source.id} | accepted {source.version} | {discovery}")',
    'print(f"{package.metadata.name} | {source.id} | using {source.version} | {discovery}")',
)

source_flow_start = '            source_id = _resolve_source_id(node_root, args.source)\n            if args.source_command in {"fetch", "update"}:\n'
source_flow_end = '            candidate = Path(args.candidate).resolve()\n'
source_flow = '''            source_id = _resolve_source_id(node_root, args.source)
            if args.source_command in {"fetch", "update"}:
                parsed = parse_node(node_root, repo_root)
                current = next(source for source in parsed.sources if source.id == source_id)
                lookup = _source_lookup_description(repo_root, current, source_id, args.ref)
                candidate, location = fetch_git_candidate(node_root, source_id, discovery_ref=args.ref)
                try:
                    cache_label = location.relative_to(node_root).as_posix()
                except ValueError:
                    cache_label = str(location)
                provenance = load_candidate_provenance(node_root, candidate.package_digest)

                migrated = None
                if args.source_command == "update":
                    migrated = _migrate_legacy_source_discovery(node_root, source_id)

                if current.package_digest == candidate.package_digest:
                    if args.source_command == "update":
                        print(f"Source update for local Node: {parsed.metadata.name}")
                        print(f"Current local Source: {candidate.metadata.name} {candidate.metadata.version}")
                        print(f"Looked up from: {lookup}")
                        print("Result: this local Node already uses this exact Source package; no update is needed.")
                    else:
                        print(f"Fetched candidate: {candidate.metadata.name} {candidate.metadata.version}")
                        print("Current Source is already this exact package.")
                    return 0

                if args.source_command == "fetch":
                    print(f"Fetched candidate: {candidate.metadata.name} {candidate.metadata.version}")
                    print(f"Looked up from: {lookup}")
                    print("The Source version currently used by this Node is unchanged until explicit review and apply.")
                    print("Technical details:")
                    print(f"  Candidate package digest: {candidate.package_digest}")
                    if provenance is not None and provenance.get("candidate_ref"):
                        print(f"  Git commit: {provenance['candidate_ref']}")
                    print(f"  Cached package: {cache_label}")
                    return 0

                result, receipt = review_source_candidate(node_root, source_id, location)
                local_effect = preview_source_candidate_effect(node_root, source_id, location)

                print(f"Source update for local Node: {parsed.metadata.name}")
                print("")
                print("Current local Source:")
                print(f"  {current.name} {current.version}")
                print(f"  This is the last Source version put into use for {parsed.metadata.name}.")
                print("New candidate found:")
                print(f"  {candidate.metadata.name} {candidate.metadata.version}")
                print(f"  Looked up from: {lookup}")
                print(f"This command is offering an update to {parsed.metadata.name}; its Context has not changed yet.")

                if migrated is not None:
                    print("")
                    print("Discovery setup note:")
                    print(f"  Legacy Source lookup settings were moved to {migrated}.")
                    print("  That only changes where future candidates are found; it does not apply this Source update.")

                print("")
                print(f'What changed in Source "{candidate.metadata.name}" since the version used here:')
                print(f"  Version: {current.version} -> {candidate.metadata.version}")
                print(f"  Summary: {_human_change_summary(result, exclude_categories={'node'})}")
                _print_human_change_details(result, exclude_categories={"node"})

                print("")
                print(f'Local update offered for Node "{parsed.metadata.name}":')
                print(f"  Source: {current.name} {current.version} -> {candidate.metadata.name} {candidate.metadata.version}")
                print(
                    "  Effective Context after existing local Overrides/Removes and other imports: "
                    + _human_change_summary(local_effect, include_categories={"rule", "topic", "resource"})
                )
                print("  Existing local Overrides/Removes and other imported Context are already reflected in this preview.")
                print("  This Node's own version will be checked and may receive the automatic minimum patch bump.")
                print("  Generated CONTEXT.md is rebuilt later; choosing Y here does not rebuild it.")

                downstream = _parent_edges(repo_root, node_root)
                if downstream:
                    print("")
                    print("What comes after this local update:")
                    print(
                        f"  {len({child_root for child_root, _, _ in downstream})} downstream Node(s) are connected through this Parent/Child chain."
                    )
                    print("  They keep their current Parent snapshots until their own review.")
                    print("  Relationships that may need review:")
                    for child_root, parent, parent_root in downstream:
                        child = parse_node(child_root, repo_root)
                        parent_node = parse_node(parent_root, repo_root)
                        child_label = child_root.relative_to(repo_root).as_posix() or "."
                        print(f"    - {parent_node.metadata.name} -> {child.metadata.name} ({child_label})")
                    start_label = node_root.relative_to(repo_root).as_posix() or "."
                    propagate_command = "contextcanon propagate" if start_label == "." else f"contextcanon propagate {start_label}"
                    print("  After applying this update, review that chain top-down in one guided run:")
                    print(f"    {propagate_command}")
                    print("  It still asks separately before applying each changed Parent -> Child step.")
                else:
                    print("")
                    print("What comes after this local update:")
                    print("  No Child Nodes depend on this Node through a semantic Parent relationship.")

                print("")
                print("Before choosing Y, check:")
                print(f"  1. Do these changes make sense for {parsed.metadata.name}?")
                print("  2. Are they compatible with this Node's other imported Contexts, or is an explicit local resolution needed?")
                print(f"  3. Are the changes in {candidate.metadata.name} themselves correct, complete, and well-scoped? If not, fix the Source upstream.")

                print("")
                print("Technical details:")
                print(f"  Source Node ID: {source_id}")
                print(f"  Source normalized digest: {result.before_normalized_digest} -> {result.after_normalized_digest}")
                print(f"  Source package digest: {result.before_package_digest} -> {result.after_package_digest}")
                print("  Exact changed identities:")
                symbols = {"added": "+", "removed": "-", "modified": "~"}
                for entry in result.entries:
                    if entry.category == "node":
                        continue
                    print(f"    {symbols[entry.change]} {entry.category}: {entry.identity}")
                print("  Candidate discovery:")
                if provenance is not None and provenance.get("candidate_ref"):
                    print(f"    Git commit: {provenance['candidate_ref']}")
                elif provenance is not None and provenance.get("kind") == "local":
                    print(f"    Local repository: {provenance['location']}")
                print(f"    Cached package: {cache_label}")

                if not args.yes and not _confirm(f"Apply this Source update to local Node {parsed.metadata.name}?"):
                    print("No local Source update applied.")
                    print(f"Technical review receipt kept at: {receipt}")
                    return 0

                accepted = accept_source_candidate(node_root, source_id, location)
                print(f"Updated local Source for {parsed.metadata.name}: {current.version} -> {accepted.metadata.version}")
                _report_version_bump(ensure_node_version_advanced(node_root, repo_root))
                print("Generated CONTEXT.md has not been rebuilt yet.")
                if downstream:
                    start_label = node_root.relative_to(repo_root).as_posix() or "."
                    propagate_command = "contextcanon propagate" if start_label == "." else f"contextcanon propagate {start_label}"
                    print("Next: review the downstream Parent/Child updates in one guided run:")
                    print(f"  {propagate_command}")
                    print("ContextCanon still asks separately before applying each changed step.")
                    print("After the intended reviews: contextcanon build --all . && contextcanon check --all .")
                else:
                    print("Next from the repository root: contextcanon build --all .")
                    print("Then: contextcanon check --all .")
                return 0

'''
replace_between("src/contextcanon/cli.py", source_flow_start, source_flow_end, source_flow)

# Update the established tests to the new temporal vocabulary and narrative.
replace_once(
    "tests/test_configuration_and_update_ux.py",
    'self.assertIn("It does not change the accepted Source; acceptance happens only after this review.", out.getvalue())\n            self.assertIn("Candidate: Shared 1.1.0", out.getvalue())',
    'self.assertIn("That only changes where future candidates are found; it does not apply this Source update.", out.getvalue())\n            self.assertIn("Current local Source:", out.getvalue())\n            self.assertIn("New candidate found:", out.getvalue())\n            self.assertIn("What changed in Source \\"Shared\\" since the version used here:", out.getvalue())\n            self.assertIn("Local update offered for Node \\"Consumer\\":", out.getvalue())\n            self.assertIn("Effective Context after existing local Overrides/Removes and other imports: 1 rule changed", out.getvalue())\n            self.assertIn("Before choosing Y, check:", out.getvalue())\n            self.assertNotIn("\\nNodes:\\n", out.getvalue())',
)
replace_once(
    "tests/test_configuration_and_update_ux.py",
    'self.assertIn("Shared Canonical | source-id | accepted 1.0.0", listed.getvalue())',
    'self.assertIn("Shared Canonical | source-id | using 1.0.0", listed.getvalue())',
)

# Add a focused regression proving the downstream explanation points to the guided one-run command.
test_insert = "    def test_source_list_and_update_use_accepted_package_name_when_consumer_label_is_stale(self):\n"
new_test = '''    def test_source_update_explains_downstream_parent_child_review_and_guided_command(self):
        project = Path(tempfile.mkdtemp())
        provider = Path(tempfile.mkdtemp())
        try:
            (project / ".git").mkdir()
            subprocess.run(["git", "init", "-q", "-b", "main", str(provider)], check=True)
            subprocess.run(["git", "-C", str(provider), "config", "user.email", "test@example.com"], check=True)
            subprocess.run(["git", "-C", str(provider), "config", "user.name", "Test"], check=True)
            old_source = write_node(provider, "source-id", "Shared", "1.0.0", "Old meaning.")
            subprocess.run(["git", "-C", str(provider), "add", "."], check=True)
            subprocess.run(["git", "-C", str(provider), "commit", "-qm", "old"], check=True)
            subprocess.run(["git", "-C", str(provider), "checkout", "-qb", "feature"], check=True)
            write_node(provider, "source-id", "Shared", "1.1.0", "New meaning.")
            subprocess.run(["git", "-C", str(provider), "add", "."], check=True)
            subprocess.run(["git", "-C", str(provider), "commit", "-qm", "new"], check=True)

            (project / "CONTEXT.src.md").write_text(
                f'''# Consumer — Local Context Source\\n<!-- ctx:node id="consumer" name="Consumer" version="0.1.0" -->\\n\\n## Sources\\n\\n- [Shared](contextcanon.yaml) — `1.0.0`\\n  <!-- ctx:source id="source-id" version="1.0.0" normalized-digest="{old_source.normalized_digest}" package-digest="{old_source.package_digest}" -->\\n''',
                encoding="utf-8",
            )
            install_package(project, old_source)
            upsert_git_source(project, "source-id", str(provider), "main", ".")
            current_consumer = Compiler(project).compile(project)
            write_outputs(current_consumer)

            child_root = project / "child"
            child_root.mkdir()
            (child_root / "CONTEXT.src.md").write_text(
                parent_source("child", "Child", "..", current_consumer),
                encoding="utf-8",
            )
            install_package(child_root, current_consumer)
            write_outputs(Compiler(project).compile(child_root))

            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                rc = cli_main(["source", "update", "Shared", "--node", str(project), "--ref", "feature", "--yes"])
            self.assertEqual(rc, 0, out.getvalue())
            self.assertIn("What comes after this local update:", out.getvalue())
            self.assertIn("Consumer -> Child (child)", out.getvalue())
            self.assertIn("review that chain top-down in one guided run:", out.getvalue())
            self.assertIn("contextcanon propagate", out.getvalue())
            self.assertIn("asks separately before applying each changed Parent -> Child step", out.getvalue())
        finally:
            shutil.rmtree(project, ignore_errors=True)
            shutil.rmtree(provider, ignore_errors=True)

'''
replace_once("tests/test_configuration_and_update_ux.py", test_insert, new_test + test_insert)

# Keep the user documentation aligned with the CLI story and avoid temporal "accepted" jargon on the entry path.
replace_once(
    "docs/cli.md",
    "| Inspect reusable Sources | `contextcanon source list` | Shows accepted Source versions plus candidate-discovery configuration. |",
    "| Inspect reusable Sources | `contextcanon source list` | Shows the Source versions currently used here plus candidate-discovery configuration. |",
)
replace_once(
    "docs/cli.md",
    "| Review/update one Source | `contextcanon source update <name-or-id>` | Fetches a candidate, shows the external change and local effect, validates composition, and asks before acceptance. |",
    "| Review/update one Source | `contextcanon source update <name-or-id>` | Shows what is used here now, what newer candidate was found, what changed there, what would change locally, and asks before applying it. |",
)
replace_once(
    "docs/maintenance.md",
    "First see what this Node currently accepts:\n",
    "First see which reusable Source version this Node currently uses:\n",
)
replace_once(
    "docs/maintenance.md",
    "The review first describes **what changed in the external Source package**. Accepting it changes the Source snapshot used by the direct consumer Node. It does not silently update descendant Nodes and it does not rebuild generated Markdown yet.\n\nImported Rules normally become part of the consumer's effective Context. A project-specific difference is expressed explicitly with a local Override or Remove and a rationale; Source order is never hidden precedence.\n",
    "The guided review tells the story in this order: **what this Node uses now → what newer Source candidate was found → what changed in that Source → what would effectively change here → what to check before applying it → which Child chain needs review afterwards**. Technical digests and cache/provenance details stay below that human view.\n\nBefore applying a Source update, use the same three quick questions as for downstream propagation: does it make sense here, is it compatible with the other imported Contexts, and is the upstream change itself correct/complete enough? ContextCanon previews the effective local result after current Overrides/Removes and other imports. A project-specific difference remains explicit; import order is never hidden precedence.\n\nApplying the Source update changes only this direct consumer's Source snapshot. It does not silently advance Child Nodes and it does not rebuild generated Markdown yet. If Children exist, the command lists the Parent/Child chain and points to `contextcanon propagate` for the subsequent guided review.\n",
)

# Mark this owner-test refinement complete in PLAN; the commit is produced only after the gate below succeeds.
plan = ROOT / "PLAN.md"
plan_text = plan.read_text(encoding="utf-8")
heading = "## Owner-test Source-update narrative follow-up: Issue #27\n"
start = plan_text.index(heading)
section = plan_text[start:].replace("- [ ]", "- [x]")
plan.write_text(plan_text[:start] + section, encoding="utf-8")
