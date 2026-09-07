from __future__ import annotations

import sys
from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected one replacement target, found {count}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


def update_plan() -> None:
    path = Path("PLAN.md")
    text = path.read_text(encoding="utf-8")
    anchor = "Checkpoint: Issues #21–#24 are implemented on draft PR #18."
    note = (
        "Owner-test correction under #22: `source list` and human Source selectors must use the accepted package's canonical Node name; "
        "a stale/damaged consumer display label may be shown as a warning/legacy alias but must not force UUID archaeology. "
        "Successful Source acceptance should normalize the visible consumer label back to the accepted package name.\n\n"
    )
    if note in text:
        return
    if anchor not in text:
        raise RuntimeError("active #21-#24 checkpoint not found")
    text = text.replace(anchor, note + anchor, 1)
    path.write_text(text, encoding="utf-8")


def update_product() -> None:
    cli = "src/contextcanon/cli.py"

    resolve_old = '''def _resolve_source_id(node_root: Path, selector: str) -> str:\n    parsed = parse_node(node_root, find_repo_root(node_root))\n    for source in parsed.sources:\n        if source.id == selector:\n            return source.id\n    matches = [source for source in parsed.sources if source.name.casefold() == selector.casefold()]\n    if len(matches) == 1:\n        return matches[0].id\n    choices = ", ".join(f"{source.name} ({source.id})" for source in parsed.sources) or "none"\n    if len(matches) > 1:\n        raise ContextCanonError(f"Source name {selector!r} is ambiguous; available Sources: {choices}")\n    raise ContextCanonError(f"No Source named or identified by {selector!r}; available Sources: {choices}")\n\n\n'''

    resolve_new = '''def _source_identity_rows(node_root: Path):\n    repo_root = find_repo_root(node_root)\n    parsed = parse_node(node_root, repo_root)\n    compiled = Compiler(repo_root).compile(node_root)\n    packages = {package.metadata.id: package for package in compiled.source_packages}\n    return tuple((source, packages[source.id]) for source in parsed.sources)\n\n\ndef _resolve_source_id(node_root: Path, selector: str) -> str:\n    rows = _source_identity_rows(node_root)\n    for source, _ in rows:\n        if source.id == selector:\n            return source.id\n    folded = selector.casefold()\n    matches = []\n    for source, package in rows:\n        names = {package.metadata.name.casefold(), source.name.casefold()}\n        if folded in names:\n            matches.append((source, package))\n    ids = {source.id for source, _ in matches}\n    if len(ids) == 1:\n        return next(iter(ids))\n    choices = ", ".join(\n        f"{package.metadata.name} ({source.id})"\n        for source, package in rows\n    ) or "none"\n    if matches:\n        raise ContextCanonError(f"Source name {selector!r} is ambiguous; available Sources: {choices}")\n    raise ContextCanonError(f"No Source named or identified by {selector!r}; available Sources: {choices}")\n\n\n'''
    replace_once(cli, resolve_old, resolve_new)

    list_old = '''            if args.source_command == "list":\n                parsed = parse_node(node_root, repo_root)\n                if not parsed.sources:\n                    print(f"{parsed.metadata.name}: no Sources")\n                    return 0\n                for source in parsed.sources:\n                    configured = configured_source(repo_root, source.id)\n                    if configured is None:\n                        discovery = (\n                            f"legacy git {source.locator} ({source.transport_ref or 'default'})"\n                            if source.transport == "git"\n                            else "no central discovery configuration"\n                        )\n                    else:\n                        source_config, repository = configured\n                        if repository.kind == "git":\n                            discovery = f"git {repository.location} @ {repository.ref or 'default'} :: {source_config.node_path}"\n                        else:\n                            discovery = f"local {repository.location} :: {source_config.node_path}"\n                    print(f"{source.name} | {source.id} | accepted {source.version} | {discovery}")\n                return 0\n'''

    list_new = '''            if args.source_command == "list":\n                parsed = parse_node(node_root, repo_root)\n                if not parsed.sources:\n                    print(f"{parsed.metadata.name}: no Sources")\n                    return 0\n                for source, package in _source_identity_rows(node_root):\n                    configured = configured_source(repo_root, source.id)\n                    if configured is None:\n                        discovery = (\n                            f"legacy git {source.locator} ({source.transport_ref or 'default'})"\n                            if source.transport == "git"\n                            else "no central discovery configuration"\n                        )\n                    else:\n                        source_config, repository = configured\n                        if repository.kind == "git":\n                            discovery = f"git {repository.location} @ {repository.ref or 'default'} :: {source_config.node_path}"\n                        else:\n                            discovery = f"local {repository.location} :: {source_config.node_path}"\n                    print(f"{package.metadata.name} | {source.id} | accepted {source.version} | {discovery}")\n                    if source.name != package.metadata.name:\n                        print(f"  warning: consumer display label is {source.name!r}; accepted package name is {package.metadata.name!r}")\n                return 0\n'''
    replace_once(cli, list_old, list_new)

    sources = "src/contextcanon/sources.py"
    regex_old = "_SOURCE_LINE_RE = re.compile(\n    r'^(?P<prefix>- \\[[^]]+\\]\\([^)]+\\)\\s+—\\s+)`[^`]+`(?P<ending>\\s*(?:\\r?\\n)?)$'\n)"
    regex_new = "_SOURCE_LINE_RE = re.compile(\n    r'^(?P<bullet>- )\\[[^]]+\\]\\((?P<path>[^)]+)\\)(?P<separator>\\s+—\\s+)`[^`]+`(?P<ending>\\s*(?:\\r?\\n)?)$'\n)"
    replace_once(sources, regex_old, regex_new)

    write_old = '''            lines[index] = (\n                visible.group("prefix")\n                + f"`{candidate.metadata.version}`"\n                + visible.group("ending")\n            )\n'''
    write_new = '''            if any(char in candidate.metadata.name for char in "]\\n\\r"):\n                raise ContextCanonError(f"Source name cannot be represented safely: {candidate.metadata.name!r}")\n            lines[index] = (\n                visible.group("bullet")\n                + f"[{candidate.metadata.name}]({visible.group('path')})"\n                + visible.group("separator")\n                + f"`{candidate.metadata.version}`"\n                + visible.group("ending")\n            )\n'''
    replace_once(sources, write_old, write_new)

    tests = Path("tests/test_configuration_and_update_ux.py")
    text = tests.read_text(encoding="utf-8")
    anchor = "    def test_parent_propagate_updates_chain_top_down_in_one_command(self):\n"
    if text.count(anchor) != 1:
        raise RuntimeError("test anchor not found")
    new_test = '''    def test_source_list_and_update_use_accepted_package_name_when_consumer_label_is_stale(self):\n        project = Path(tempfile.mkdtemp())\n        provider = Path(tempfile.mkdtemp())\n        try:\n            (project / ".git").mkdir()\n            subprocess.run(["git", "init", "-q", "-b", "main", str(provider)], check=True)\n            subprocess.run(["git", "-C", str(provider), "config", "user.email", "test@example.com"], check=True)\n            subprocess.run(["git", "-C", str(provider), "config", "user.name", "Test"], check=True)\n            main_package = write_node(provider, "source-id", "Shared Canonical", "1.0.0", "Main meaning.")\n            subprocess.run(["git", "-C", str(provider), "add", "."], check=True)\n            subprocess.run(["git", "-C", str(provider), "commit", "-qm", "main"], check=True)\n            main_head = subprocess.run(\n                ["git", "-C", str(provider), "rev-parse", "HEAD"], check=True, text=True, capture_output=True\n            ).stdout.strip()\n            subprocess.run(["git", "-C", str(provider), "checkout", "-qb", "feature"], check=True)\n            feature_package = write_node(provider, "source-id", "Shared Canonical", "1.1.0", "Feature meaning.")\n            subprocess.run(["git", "-C", str(provider), "add", "."], check=True)\n            subprocess.run(["git", "-C", str(provider), "commit", "-qm", "feature"], check=True)\n\n            consumer = project\n            source_text = (\n                '# Consumer — Local Context Source\\n'\n                '<!-- ctx:node id="consumer" version="0.1.0" -->\\n\\n'\n                '## Sources\\n\\n'\n                f'- [stale accidental label]({provider.as_posix()}) — `1.0.0`\\n'\n                f'  <!-- ctx:source id="source-id" version="1.0.0" normalized-digest="{main_package.normalized_digest}" package-digest="{main_package.package_digest}" transport="git" ref="{main_head}" node-path="." -->\\n'\n            )\n            (consumer / "CONTEXT.src.md").write_text(source_text, encoding="utf-8")\n            install_package(consumer, main_package)\n\n            listed = io.StringIO()\n            with contextlib.redirect_stdout(listed):\n                rc = cli_main(["source", "list", "--node", str(consumer)])\n            self.assertEqual(rc, 0, listed.getvalue())\n            self.assertIn("Shared Canonical | source-id | accepted 1.0.0", listed.getvalue())\n            self.assertIn("consumer display label is 'stale accidental label'", listed.getvalue())\n\n            updated = io.StringIO()\n            with contextlib.redirect_stdout(updated):\n                rc = cli_main(["source", "update", "Shared Canonical", "--node", str(consumer), "--ref", "feature", "--yes"])\n            self.assertEqual(rc, 0, updated.getvalue())\n            self.assertEqual(Compiler(project).compile(project).source_packages[0].package_digest, feature_package.package_digest)\n            self.assertIn("- [Shared Canonical]", (consumer / "CONTEXT.src.md").read_text(encoding="utf-8"))\n            self.assertNotIn("stale accidental label", (consumer / "CONTEXT.src.md").read_text(encoding="utf-8"))\n        finally:\n            shutil.rmtree(project, ignore_errors=True)\n            shutil.rmtree(provider, ignore_errors=True)\n\n'''
    if "test_source_list_and_update_use_accepted_package_name_when_consumer_label_is_stale" not in text:
        tests.write_text(text.replace(anchor, new_test + anchor, 1), encoding="utf-8")

    doc = Path("nodes/library/foundation/docs/source-format.md")
    text = doc.read_text(encoding="utf-8")
    sentence = '`contextcanon source list` shows human names, stable IDs and the resolved discovery configuration.'
    replacement = (
        '`contextcanon source list` shows the canonical name from each accepted Source package, stable IDs and the resolved discovery configuration. '
        'If a consumer carries a stale visible label, the list warns about it while name-based commands still accept the canonical package name.'
    )
    if sentence not in text:
        raise RuntimeError("source-list documentation sentence not found")
    doc.write_text(text.replace(sentence, replacement, 1), encoding="utf-8")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "plan":
        update_plan()
    elif mode == "product":
        update_product()
    else:
        raise SystemExit("usage: helper.py plan|product")
