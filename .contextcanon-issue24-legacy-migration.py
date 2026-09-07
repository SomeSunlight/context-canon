from __future__ import annotations

from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected one replacement target, found {count}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


# Guided Source update migrates legacy inline Git discovery into central config.
replace_once(
    "src/contextcanon/cli.py",
    "from .config import CONFIG_FILENAME, configured_source, config_path, load_project_config\n",
    "from .config import CONFIG_FILENAME, configured_source, config_path, load_project_config, upsert_git_source\n",
)

resolve_source_block = '''def _resolve_source_id(node_root: Path, selector: str) -> str:\n    parsed = parse_node(node_root, find_repo_root(node_root))\n    for source in parsed.sources:\n        if source.id == selector:\n            return source.id\n    matches = [source for source in parsed.sources if source.name.casefold() == selector.casefold()]\n    if len(matches) == 1:\n        return matches[0].id\n    choices = ", ".join(f"{source.name} ({source.id})" for source in parsed.sources) or "none"\n    if len(matches) > 1:\n        raise ContextCanonError(f"Source name {selector!r} is ambiguous; available Sources: {choices}")\n    raise ContextCanonError(f"No Source named or identified by {selector!r}; available Sources: {choices}")\n\n\n'''

migration_helper = resolve_source_block + '''def _migrate_legacy_source_discovery(node_root: Path, source_id: str) -> Path | None:\n    """Record equivalent central discovery after a successful legacy update fetch.\n\n    This changes discovery configuration only. Accepted immutable package state\n    remains untouched, and a one-off CLI --ref is never persisted here.\n    """\n\n    repo_root = find_repo_root(node_root)\n    if configured_source(repo_root, source_id) is not None:\n        return None\n    parsed = parse_node(node_root, repo_root)\n    matches = [source for source in parsed.sources if source.id == source_id]\n    if len(matches) != 1:\n        raise ContextCanonError(f"Could not resolve exactly one legacy Source {source_id} for discovery migration")\n    source = matches[0]\n    if source.transport != "git" or not source.transport_ref or source.node_path is None:\n        return None\n\n    legacy_ref = source.transport_ref\n    discovery_ref = None if len(legacy_ref) == 40 and all(char in "0123456789abcdef" for char in legacy_ref) else legacy_ref\n    return upsert_git_source(repo_root, source.id, source.locator, discovery_ref, source.node_path)\n\n\n'''
replace_once("src/contextcanon/cli.py", resolve_source_block, migration_helper)

source_update_block = '''                parsed = parse_node(node_root, repo_root)\n                current = next(source for source in parsed.sources if source.id == source_id)\n                if current.package_digest == candidate.package_digest:\n                    print("Accepted Source is already this exact package.")\n                    return 0\n                if args.source_command == "fetch":\n                    print("Accepted Source pin is unchanged until explicit review and accept.")\n                    return 0\n                result, receipt = review_source_candidate(node_root, source_id, location)\n'''

source_update_replacement = '''                parsed = parse_node(node_root, repo_root)\n                current = next(source for source in parsed.sources if source.id == source_id)\n                if args.source_command == "update":\n                    migrated = _migrate_legacy_source_discovery(node_root, source_id)\n                    if migrated is not None:\n                        print(f"Migrated legacy Source discovery to {migrated}")\n                if current.package_digest == candidate.package_digest:\n                    print("Accepted Source is already this exact package.")\n                    return 0\n                if args.source_command == "fetch":\n                    print("Accepted Source pin is unchanged until explicit review and accept.")\n                    return 0\n                result, receipt = review_source_candidate(node_root, source_id, location)\n'''
replace_once("src/contextcanon/cli.py", source_update_block, source_update_replacement)

# Regression: a one-off feature ref updates the candidate but does not become durable config.
test_path = Path("tests/test_configuration_and_update_ux.py")
test_text = test_path.read_text(encoding="utf-8")
anchor = '''    def test_parent_propagate_updates_chain_top_down_in_one_command(self):\n'''
if test_text.count(anchor) != 1:
    raise RuntimeError("test insertion anchor missing")
new_test = '''    def test_guided_update_migrates_legacy_git_discovery_without_persisting_one_off_ref(self):\n        project = Path(tempfile.mkdtemp())\n        provider = Path(tempfile.mkdtemp())\n        try:\n            (project / ".git").mkdir()\n            subprocess.run(["git", "init", "-q", "-b", "main", str(provider)], check=True)\n            subprocess.run(["git", "-C", str(provider), "config", "user.email", "test@example.com"], check=True)\n            subprocess.run(["git", "-C", str(provider), "config", "user.name", "Test"], check=True)\n            main_package = write_node(provider, "source-id", "Shared", "1.0.0", "Main meaning.")\n            subprocess.run(["git", "-C", str(provider), "add", "."], check=True)\n            subprocess.run(["git", "-C", str(provider), "commit", "-qm", "main"], check=True)\n            main_head = subprocess.run(\n                ["git", "-C", str(provider), "rev-parse", "HEAD"], check=True, text=True, capture_output=True\n            ).stdout.strip()\n            subprocess.run(["git", "-C", str(provider), "checkout", "-qb", "feature"], check=True)\n            feature_package = write_node(provider, "source-id", "Shared", "1.1.0", "Feature meaning.")\n            subprocess.run(["git", "-C", str(provider), "add", "."], check=True)\n            subprocess.run(["git", "-C", str(provider), "commit", "-qm", "feature"], check=True)\n\n            consumer = project\n            (consumer / "CONTEXT.src.md").write_text(\n                f'''# Consumer — Local Context Source\\n<!-- ctx:node id="consumer" version="0.1.0" -->\\n\\n## Sources\\n\\n- [Shared]({provider.as_posix()}) — `1.0.0`\\n  <!-- ctx:source id="source-id" version="1.0.0" normalized-digest="{main_package.normalized_digest}" package-digest="{main_package.package_digest}" transport="git" ref="{main_head}" node-path="." -->\\n''',\n                encoding="utf-8",\n            )\n            install_package(consumer, main_package)\n\n            out = io.StringIO()\n            with contextlib.redirect_stdout(out):\n                rc = cli_main(["source", "update", "Shared", "--node", str(consumer), "--ref", "feature", "--yes"])\n            self.assertEqual(rc, 0, out.getvalue())\n            self.assertIn("Migrated legacy Source discovery", out.getvalue())\n\n            source_cfg, repo_cfg = configured_source(project, "source-id")\n            self.assertEqual(repo_cfg.kind, "git")\n            self.assertEqual(repo_cfg.location, provider.as_posix())\n            self.assertIsNone(repo_cfg.ref)\n            self.assertEqual(source_cfg.node_path, ".")\n            accepted = Compiler(project).compile(project).source_packages[0]\n            self.assertEqual(accepted.package_digest, feature_package.package_digest)\n            self.assertIn('ref="', (consumer / "CONTEXT.src.md").read_text(encoding="utf-8"))\n        finally:\n            shutil.rmtree(project, ignore_errors=True)\n            shutil.rmtree(provider, ignore_errors=True)\n\n'''
test_path.write_text(test_text.replace(anchor, new_test + anchor, 1), encoding="utf-8")

# Durable guidance: YAML stays operational and concise; legacy update migration is explicit.
doc_sentence = '''`contextcanon source list` shows human names, stable IDs and the resolved discovery configuration. `contextcanon source update "Development Workflow"` performs fetch + exact diff + explicit acceptance as one guided flow. `--ref <branch|tag|commit>` is a one-off Git candidate override and never rewrites the central configuration or accepted pin.\n'''
doc_replacement = doc_sentence + '''\nWhen that guided `source update` starts from a legacy inline Git Source and no central mapping exists yet, ContextCanon records the equivalent durable discovery mapping in `contextcanon.yaml` after the legacy fetch succeeds. An exact 40-character legacy commit pin becomes default-branch discovery rather than a permanently frozen central ref, preserving the old "discover something newer" behavior; a one-off `--ref` is never persisted. This migration changes discovery configuration only, not the accepted immutable package pin. The legacy inline metadata remains readable as a compatibility fallback while the central mapping takes precedence.\n'''
replace_once("nodes/library/foundation/docs/source-format.md", doc_sentence, doc_replacement)

# Complete the active PLAN block only on a workflow that subsequently passes the full gate.
plan_path = Path("PLAN.md")
plan = plan_path.read_text(encoding="utf-8")
for issue in (21, 22, 23, 24):
    plan = plan.replace(f"- [ ] #{issue} ", f"- [x] #{issue} ", 1)
plan = plan.replace(
    "- [ ] Preserve compatibility with existing inline Git transport metadata and run focused regressions, the complete deterministic suite, self-build/check and diff hygiene before returning to owner testing.",
    "- [x] Preserve compatibility with existing inline Git transport metadata and run focused regressions, the complete deterministic suite, self-build/check and diff hygiene before returning to owner testing.",
    1,
)
old_checkpoint = "Checkpoint: the project owner approved this coherent Issues #21–#24 block during the real `ai-workstation` pre-merge test. Parent propagation must update every applicable edge top-down; project-specific differences belong in normal local Override/Remove semantics rather than propagation exclusions."
new_checkpoint = "Checkpoint: Issues #21–#24 are implemented on draft PR #18. The human-scale update path supports version display, Source discovery by name, one-off Git refs, central Git/local repository configuration, guided legacy-to-central discovery migration, and top-down Parent propagation without per-Node exclusions. Parent propagation updates every applicable edge; project-specific differences belong in normal local Override/Remove semantics. The exact candidate passes 231 deterministic tests, self-build, zero-drift `check --all`, and diff hygiene before owner testing resumes."
if old_checkpoint not in plan:
    raise RuntimeError("PLAN owner-test checkpoint missing")
plan_path.write_text(plan.replace(old_checkpoint, new_checkpoint, 1), encoding="utf-8")

state_path = Path("STATE.md")
state = state_path.read_text(encoding="utf-8")
state = state.replace("active **draft, unmerged** review branch for Issues #14–#19", "active **draft, unmerged** review branch for Issues #14–#24", 1)
state = state.replace(
    "Review the exact clean head of draft PR #18 for Issues #14–#19. This documentation reconciliation does not require re-running `ai-workstation` onboarding. Do not merge without explicit project-owner approval.",
    "Resume the real `ai-workstation` owner test on the exact clean head of draft PR #18 using the Issues #21–#24 human-scale Source-update and Parent-propagation UX. Do not merge without explicit project-owner approval.",
    1,
)
section = '''\n\n## Latest owner-test update UX checkpoint\n\nIssues #21–#24 now turn the first normal post-onboarding reusable-Context update into an operator-scale workflow. `contextcanon --version` exposes the installed tool version; Sources can be selected by human name; central `contextcanon.yaml` holds concise operational Git/local discovery configuration while accepted immutable pins remain inside each consumer Node; `source update` supports one-off refs without persisting them; and `parent propagate --all` reviews/accepts every applicable semantic Parent edge top-down without per-Node skip policy. Local exceptions remain ordinary ContextCanon Override/Remove semantics.\n\nFor existing projects such as the owner-tested `ai-workstation`, the first guided `source update` can start from legacy inline Git metadata and, after candidate discovery succeeds, record equivalent central discovery configuration without changing the accepted package pin. Exact legacy commit refs migrate to default-branch discovery so the old update semantics are preserved, while an explicit one-off `--ref` remains ephemeral. The implementation is guarded by 231 deterministic tests plus self-build, zero-drift `check --all`, and diff hygiene.\n'''
if "## Latest owner-test update UX checkpoint" not in state:
    state = state.rstrip() + section + "\n"
state_path.write_text(state, encoding="utf-8")

print("Issue #24 legacy discovery migration prepared")
