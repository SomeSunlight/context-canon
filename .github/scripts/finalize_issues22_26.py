from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BRANCH = "agent/issues-14-15-multi-parent"


def run(*args: str) -> None:
    subprocess.run(args, cwd=ROOT, check=True)


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"Expected exactly one match in {path}: {old!r}; found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def append_once(path: Path, marker: str, block: str) -> None:
    text = path.read_text(encoding="utf-8")
    if marker not in text:
        path.write_text(text.rstrip() + "\n\n" + block.strip() + "\n", encoding="utf-8")


def checkpoint_plan() -> None:
    append_once(
        ROOT / "PLAN.md",
        "Owner-test version-discipline follow-up under #26",
        """
Owner-test review-readability follow-up under #22: keep immutable digests visible, but make the human meaning of Source/Parent review primary. Review output should summarize semantic/content changes before technical fingerprints, and legacy-to-central discovery migration must state explicitly that migration alone does not change the accepted Source.

Owner-test version-discipline follow-up under #26: a changed Context package must not silently reuse the previous human version. If a prior generated package exists and the authored SemVer-shaped version is unchanged, ContextCanon applies the minimum patch bump automatically and explicitly tells the owner to consider a higher minor/major bump when warranted. A human-selected higher version wins. External Source candidates that changed package identity while reusing the accepted version are rejected rather than repaired by the consumer.
""",
    )
    run("git", "add", "PLAN.md")
    if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT).returncode != 0:
        run("git", "commit", "-m", "Checkpoint Issues #22 and #26 owner-test follow-up")
        run("git", "push", "origin", f"HEAD:{BRANCH}")


def write_versioning_module() -> None:
    path = ROOT / "src/contextcanon/versioning.py"
    path.write_text(
        '''from __future__ import annotations

import json
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .compiler import Compiler
from .parser import ContextCanonError, find_repo_root

_SEMVERISH_RE = re.compile(
    r"^(?P<major>0|[1-9][0-9]*)\\.(?P<minor>0|[1-9][0-9]*)\\.(?P<patch>0|[1-9][0-9]*)(?P<suffix>(?:-[0-9A-Za-z.-]+)?(?:\\+[0-9A-Za-z.-]+)?)$"
)
_NODE_COMMENT_RE = re.compile(r"<!--\\s*ctx:node\\s+(?P<attrs>.*?)\\s*-->")
_VERSION_ATTR_RE = re.compile(r'(?P<prefix>\\bversion=")(?P<version>[^"]*)(?P<suffix>")')


@dataclass(frozen=True)
class VersionBump:
    node_name: str
    before: str
    after: str


def minimum_patch_bump(version: str) -> str | None:
    match = _SEMVERISH_RE.fullmatch(version)
    if match is None:
        return None
    patch = int(match.group("patch")) + 1
    return f"{match.group('major')}.{match.group('minor')}.{patch}{match.group('suffix')}"


def _previous_package_identity(node_root: Path) -> tuple[str, str, str] | None:
    manifest = node_root / ".context" / "package.json"
    if not manifest.is_file():
        return None
    try:
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        node = payload["node"]
        digests = payload["digests"]
        node_id = node["id"]
        version = node["version"]
        package_digest = digests["package"]
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError):
        return None
    if not all(isinstance(value, str) and value for value in (node_id, version, package_digest)):
        return None
    return node_id, version, package_digest


def version_reuse_problem(compiled) -> str | None:
    previous = _previous_package_identity(compiled.parsed.root)
    if previous is None:
        return None
    node_id, version, package_digest = previous
    if node_id != compiled.metadata.id:
        return None
    if version == compiled.metadata.version and package_digest != compiled.package_digest:
        suggestion = minimum_patch_bump(version)
        if suggestion is None:
            return (
                f"Context Node package changed but version {version!r} was reused; "
                "update ctx:node version manually before publishing this package"
            )
        return (
            f"Context Node package changed but version {version!r} was reused; "
            f"run contextcanon build to apply the minimum patch bump to {suggestion!r}, "
            "or set a higher minor/major version explicitly"
        )
    return None


def ensure_node_version_advanced(node_root: Path, repo_root: Path | None = None) -> VersionBump | None:
    node_root = node_root.resolve()
    repo_root = (repo_root or find_repo_root(node_root)).resolve()
    compiled = Compiler(repo_root).compile(node_root)
    previous = _previous_package_identity(node_root)
    if previous is None:
        return None
    node_id, previous_version, previous_package = previous
    if node_id != compiled.metadata.id:
        return None
    if previous_version != compiled.metadata.version or previous_package == compiled.package_digest:
        return None

    bumped = minimum_patch_bump(compiled.metadata.version)
    if bumped is None:
        raise ContextCanonError(
            f"{compiled.metadata.name}: package identity changed while version {compiled.metadata.version!r} stayed unchanged; "
            "this version cannot be patch-bumped safely, so update ctx:node version manually"
        )
    _replace_node_version(node_root / "CONTEXT.src.md", compiled.metadata.version, bumped)
    return VersionBump(compiled.metadata.name, compiled.metadata.version, bumped)


def _replace_node_version(path: Path, before: str, after: str) -> None:
    text = path.read_text(encoding="utf-8")
    matches = list(_NODE_COMMENT_RE.finditer(text))
    if len(matches) != 1:
        raise ContextCanonError(f"{path}: expected exactly one ctx:node comment for automatic version bump")
    match = matches[0]
    attrs = match.group("attrs")
    versions = list(_VERSION_ATTR_RE.finditer(attrs))
    if len(versions) != 1 or versions[0].group("version") != before:
        raise ContextCanonError(f"{path}: could not safely update ctx:node version from {before!r}")
    updated_attrs = _VERSION_ATTR_RE.sub(
        lambda item: item.group("prefix") + after + item.group("suffix"),
        attrs,
        count=1,
    )
    updated = text[: match.start("attrs")] + updated_attrs + text[match.end("attrs") :]
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(updated)
        os.replace(temporary, path)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
''',
        encoding="utf-8",
    )


def update_diff_renderer() -> None:
    path = ROOT / "src/contextcanon/diff.py"
    text = path.read_text(encoding="utf-8")
    start = text.index("def render_diff(diff: ContextDiff) -> str:\n")
    end = text.index("\ndef _diff_maps(", start)
    replacement = '''_CATEGORY_NOUNS = {
    "node": ("node metadata item", "node metadata items"),
    "parent": ("parent", "parents"),
    "source": ("source", "sources"),
    "change": ("local change", "local changes"),
    "rule": ("rule", "rules"),
    "topic": ("topic", "topics"),
    "resource": ("resource", "resources"),
}


def _transition(before: str, after: str) -> str:
    return f"unchanged ({before})" if before == after else f"{before} -> {after}"


def _summary_parts(diff: ContextDiff) -> list[str]:
    counts: dict[tuple[str, DiffChange], int] = {}
    for entry in diff.entries:
        key = (entry.category, entry.change)
        counts[key] = counts.get(key, 0) + 1

    action = {"added": "added", "removed": "removed", "modified": "changed"}
    parts: list[str] = []
    for category in sorted(_CATEGORY_ORDER, key=_CATEGORY_ORDER.get):
        singular, plural = _CATEGORY_NOUNS[category]
        for change in ("added", "removed", "modified"):
            count = counts.get((category, change), 0)
            if count:
                noun = singular if count == 1 else plural
                parts.append(f"{count} {noun} {action[change]}")
    return parts


def render_diff(diff: ContextDiff) -> str:
    summary = ", ".join(_summary_parts(diff))
    if not summary:
        summary = (
            "package presentation changed; semantic and Resource content unchanged"
            if not diff.is_empty
            else "no compiled context changes"
        )

    lines = [
        f"ContextCanon diff: {diff.before_name} ({diff.node_id})",
        f"  Version: {_transition(diff.before_version, diff.after_version)}",
        f"  Summary: {summary}",
    ]

    if diff.entries:
        current_category = None
        symbol = {"added": "+", "removed": "-", "modified": "~"}
        for entry in diff.entries:
            if entry.category != current_category:
                current_category = entry.category
                lines.extend(["", current_category.title() + "s:"])
            detail = ""
            if entry.change == "modified" and entry.changed_fields:
                detail = " [" + ", ".join(entry.changed_fields) + "]"
            lines.append(f"  {symbol[entry.change]} {entry.identity}{detail}")
    elif diff.is_empty:
        lines.extend(["", "No compiled context changes."])
    else:
        lines.extend(["", "Package presentation changed without semantic or Resource content changes."])

    lines.extend(
        [
            "",
            "Technical details:",
            f"  Normalized digest: {_transition(diff.before_normalized_digest, diff.after_normalized_digest)}",
            f"  Package digest: {_transition(diff.before_package_digest, diff.after_package_digest)}",
        ]
    )
    return "\\n".join(lines) + "\\n"
'''
    path.write_text(text[:start] + replacement + text[end:], encoding="utf-8")


def update_sources_validation() -> None:
    path = ROOT / "src/contextcanon/sources.py"
    text = path.read_text(encoding="utf-8")
    marker = "\ndef review_source_candidate(\n"
    helper = '''\ndef _require_candidate_version_advance(current: CompiledPackage, candidate: CompiledPackage, relation: str) -> None:\n    if current.package_digest != candidate.package_digest and current.metadata.version == candidate.metadata.version:\n        raise ContextCanonError(\n            f"{relation} candidate {candidate.metadata.name} changed package identity but reused version "\n            f"{candidate.metadata.version!r}; advance the provider Node version before accepting this candidate"\n        )\n\n'''
    if "def _require_candidate_version_advance(" not in text:
        if marker not in text:
            raise RuntimeError("Could not locate review_source_candidate")
        text = text.replace(marker, helper + marker, 1)

    old = '''    if candidate.metadata.id != source_ref.id:\n        raise ContextCanonError(\n            f"Candidate Node ID {candidate.metadata.id} does not match Source {source_ref.name} ({source_ref.id})"\n        )\n\n    transport_candidate = _validated_candidate_provenance(node_root, source_ref, candidate)\n'''
    new = '''    if candidate.metadata.id != source_ref.id:\n        raise ContextCanonError(\n            f"Candidate Node ID {candidate.metadata.id} does not match Source {source_ref.name} ({source_ref.id})"\n        )\n    _require_candidate_version_advance(current, candidate, "Source")\n\n    transport_candidate = _validated_candidate_provenance(node_root, source_ref, candidate)\n'''
    if old not in text:
        raise RuntimeError("Could not locate Source candidate identity validation")
    text = text.replace(old, new, 1)

    old = '''    if candidate.metadata.id != parent_ref.id:\n        raise ContextCanonError(\n            f"Live Parent Node ID {candidate.metadata.id} does not match accepted Parent {parent_ref.name} ({parent_ref.id})"\n        )\n\n    _validate_parent_candidate_composition(compiler, compiled, parent_index, candidate)\n'''
    new = '''    if candidate.metadata.id != parent_ref.id:\n        raise ContextCanonError(\n            f"Live Parent Node ID {candidate.metadata.id} does not match accepted Parent {parent_ref.name} ({parent_ref.id})"\n        )\n    _require_candidate_version_advance(current, candidate, "Parent")\n\n    _validate_parent_candidate_composition(compiler, compiled, parent_index, candidate)\n'''
    if old not in text:
        raise RuntimeError("Could not locate Parent candidate identity validation")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def update_cli() -> None:
    path = ROOT / "src/contextcanon/cli.py"
    text = path.read_text(encoding="utf-8")
    old_import = "from .sources import adopt_source_package, accept_parent_candidate, accept_source_candidate, review_parent_candidate, review_source_candidate\n"
    new_import = old_import + "from .versioning import VersionBump, ensure_node_version_advanced, version_reuse_problem\n"
    if new_import not in text:
        if old_import not in text:
            raise RuntimeError("Could not locate sources import")
        text = text.replace(old_import, new_import, 1)

    confirm_marker = "\ndef _confirm(prompt: str) -> bool:\n"
    report_helper = '''\ndef _report_version_bump(bump: VersionBump | None) -> None:\n    if bump is None:\n        return\n    print(f"Auto-bumped Context Node version: {bump.before} -> {bump.after} (package changed).")\n    print("  This is the minimum patch bump; consider a higher minor or major version if the change warrants it.")\n\n'''
    if "def _report_version_bump(" not in text:
        if confirm_marker not in text:
            raise RuntimeError("Could not locate _confirm")
        text = text.replace(confirm_marker, report_helper + confirm_marker, 1)

    text = text.replace(
        'print(f"fetched candidate {candidate.metadata.name} {candidate.metadata.version} ({candidate.package_digest})")',
        'print(f"Fetched candidate: {candidate.metadata.name} {candidate.metadata.version}")\n                print(f"  Package digest: {candidate.package_digest}")',
        1,
    )
    text = text.replace(
        'print(f"Candidate Git commit: {provenance[\'candidate_ref\']}")',
        'print(f"  Git commit: {provenance[\'candidate_ref\']}")',
        1,
    )
    text = text.replace(
        'print(f"Candidate local repository: {provenance[\'location\']}")',
        'print(f"  Local repository: {provenance[\'location\']}")',
        1,
    )
    text = text.replace('print(f"Candidate package: {label}")', 'print(f"  Cached package: {label}")', 1)
    text = text.replace(
        'print(f"Migrated legacy Source discovery to {migrated}")',
        'print(f"Migrated legacy Source discovery to central configuration: {migrated}")\n                        print("  This migration only changes where future Source candidates are discovered.")\n                        print("  It does not change the accepted Source; acceptance happens only after this review.")',
        1,
    )

    old = '''            if args.author_command == "rule":\n                result = add_rule(\n                    node_root,\n                    group=args.group,\n                    title=args.title,\n                    statement=args.statement,\n                    why=args.why,\n                )\n                print(f"added Rule {result.element_id} to {result.source_path}")\n            else:\n                result = add_topic(\n                    node_root,\n                    title=args.title,\n                    condition=args.condition,\n                    required_resources=tuple(args.required_resource),\n                    optional_resources=tuple(args.optional_resource),\n                    required_nodes=tuple(args.required_node),\n                    optional_nodes=tuple(args.optional_node),\n                )\n                print(f"added Topic {result.element_id} to {result.source_path}")\n            print(f"Next: contextcanon build {node_root}")\n'''
    new = old.replace('            print(f"Next: contextcanon build {node_root}")\n', '            _report_version_bump(ensure_node_version_advanced(node_root))\n            print(f"Next: contextcanon build {node_root}")\n')
    if old not in text:
        raise RuntimeError("Could not locate author command block")
    text = text.replace(old, new, 1)

    old = '''                for child_root, parent, _ in edges:\n                    child = parse_node(child_root, repo_root)\n'''
    new = '''                for child_root, parent, parent_root in edges:\n                    _report_version_bump(ensure_node_version_advanced(parent_root, repo_root))\n                    child = parse_node(child_root, repo_root)\n'''
    if old not in text:
        raise RuntimeError("Could not locate propagation loop")
    text = text.replace(old, new, 1)

    old = '''                    accepted = accept_parent_candidate(child_root, parent.id)\n                    accepted_count += 1\n                    print(f"accepted Parent {accepted.metadata.name} {accepted.metadata.version} ({accepted.package_digest})")\n'''
    new = '''                    accepted = accept_parent_candidate(child_root, parent.id)\n                    accepted_count += 1\n                    print(f"accepted Parent {accepted.metadata.name} {accepted.metadata.version} ({accepted.package_digest})")\n                    _report_version_bump(ensure_node_version_advanced(child_root, repo_root))\n'''
    if old not in text:
        raise RuntimeError("Could not locate propagated Parent acceptance")
    text = text.replace(old, new, 1)

    old = '''            accepted = accept_parent_candidate(node_root, args.parent_id)\n            print(f"accepted Parent {accepted.metadata.name} {accepted.metadata.version} ({accepted.package_digest})")\n'''
    new = '''            accepted = accept_parent_candidate(node_root, args.parent_id)\n            print(f"accepted Parent {accepted.metadata.name} {accepted.metadata.version} ({accepted.package_digest})")\n            _report_version_bump(ensure_node_version_advanced(node_root))\n'''
    if old not in text:
        raise RuntimeError("Could not locate direct Parent acceptance")
    text = text.replace(old, new, 1)

    old = '''                adopted, changed = adopt_source_package(node_root, Path(args.package))\n                verb = "adopted" if changed else "already adopted"\n                print(f"{verb} Source {adopted.metadata.name} {adopted.metadata.version} ({adopted.package_digest})")\n'''
    new = '''                adopted, changed = adopt_source_package(node_root, Path(args.package))\n                verb = "adopted" if changed else "already adopted"\n                print(f"{verb} Source {adopted.metadata.name} {adopted.metadata.version} ({adopted.package_digest})")\n                if changed:\n                    _report_version_bump(ensure_node_version_advanced(node_root, repo_root))\n'''
    if old not in text:
        raise RuntimeError("Could not locate Source adoption")
    text = text.replace(old, new, 1)

    old = '''                accepted = accept_source_candidate(node_root, source_id, location)\n                print(f"accepted Source {accepted.metadata.name} {accepted.metadata.version} ({accepted.package_digest})")\n'''
    new = '''                accepted = accept_source_candidate(node_root, source_id, location)\n                print(f"accepted Source {accepted.metadata.name} {accepted.metadata.version} ({accepted.package_digest})")\n                _report_version_bump(ensure_node_version_advanced(node_root, repo_root))\n'''
    if old not in text:
        raise RuntimeError("Could not locate guided Source acceptance")
    text = text.replace(old, new, 1)

    old = '''            accepted = accept_source_candidate(node_root, source_id, candidate)\n            print(f"accepted {accepted.metadata.name} {accepted.metadata.version} ({accepted.package_digest})")\n            return 0\n'''
    new = '''            accepted = accept_source_candidate(node_root, source_id, candidate)\n            print(f"accepted {accepted.metadata.name} {accepted.metadata.version} ({accepted.package_digest})")\n            _report_version_bump(ensure_node_version_advanced(node_root, repo_root))\n            return 0\n'''
    if old not in text:
        raise RuntimeError("Could not locate direct Source acceptance")
    text = text.replace(old, new, 1)

    old = '''        compiler = Compiler(repo_root)\n        failed = False\n        for node_root in node_roots:\n            compiled = compiler.compile(node_root)\n            label = node_root.relative_to(repo_root).as_posix() or "."\n            if args.command == "build":\n                changed = write_outputs(compiled)\n'''
    new = '''        compiler = Compiler(repo_root)\n        failed = False\n        for node_root in node_roots:\n            label = node_root.relative_to(repo_root).as_posix() or "."\n            if args.command == "build":\n                _report_version_bump(ensure_node_version_advanced(node_root, repo_root))\n                compiled = Compiler(repo_root).compile(node_root)\n                changed = write_outputs(compiled)\n'''
    if old not in text:
        raise RuntimeError("Could not locate build/check loop")
    text = text.replace(old, new, 1)

    old = '''            else:\n                drift = check_outputs(compiled)\n                if drift:\n'''
    new = '''            else:\n                compiled = compiler.compile(node_root)\n                drift = check_outputs(compiled)\n                version_problem = version_reuse_problem(compiled)\n                if version_problem is not None:\n                    drift = [version_problem, *drift]\n                if drift:\n'''
    if old not in text:
        raise RuntimeError("Could not locate check branch")
    text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")


def update_versions_and_docs() -> None:
    dev = ROOT / "nodes/library/development-workflow/CONTEXT.src.md"
    replace_once(dev, 'version="0.2.0-draft"', 'version="0.2.1-draft"')

    foundation = ROOT / "nodes/library/foundation/CONTEXT.src.md"
    replace_once(foundation, 'version="0.1.0-draft"', 'version="0.1.1-draft"')

    internal = ROOT / "nodes/internal/framework-development/CONTEXT.src.md"
    text = internal.read_text(encoding="utf-8")
    text = text.replace('version="0.1.0-draft" -->', 'version="0.1.1-draft" -->', 1)
    text = text.replace('[ContextCanon Foundation](../../library/foundation/) — `0.1.0-draft`', '[ContextCanon Foundation](../../library/foundation/) — `0.1.1-draft`', 1)
    text = text.replace('id="4ca9d92c-59f2-4b1f-b7b3-0e2ff91fd001" version="0.1.0-draft"', 'id="4ca9d92c-59f2-4b1f-b7b3-0e2ff91fd001" version="0.1.1-draft"', 1)
    text = text.replace('[Development Workflow](../../library/development-workflow/) — `0.2.0-draft`', '[Development Workflow](../../library/development-workflow/) — `0.2.1-draft`', 1)
    text = text.replace('id="c4c94726-3cc7-4df6-b779-72bbf9c06f40" version="0.2.0-draft"', 'id="c4c94726-3cc7-4df6-b779-72bbf9c06f40" version="0.2.1-draft"', 1)
    internal.write_text(text, encoding="utf-8")

    source_format = ROOT / "nodes/library/foundation/docs/source-format.md"
    marker = "### Version advancement"
    if marker not in source_format.read_text(encoding="utf-8"):
        append = '''

### Version advancement

A Context Node version is the human-facing release identity for one published package generation. Different package bytes for the same stable Node ID must not silently reuse the same version.

When a prior generated package exists and `contextcanon build` detects changed package identity while `ctx:node version` is still unchanged, a SemVer-shaped version (`X.Y.Z`, optionally with a suffix such as `-draft`) receives the minimum automatic patch bump. For example, `0.2.0-draft` becomes `0.2.1-draft`. ContextCanon reports that this is only the mechanical minimum and asks the owner to consider a higher minor or major version when the semantic or compatibility significance warrants it. A version already advanced deliberately by the human is preserved.

ContextCanon does not infer whether a change is breaking or feature-level. Versions that cannot be safely patch-bumped are left for explicit human editing, with an actionable error. Consumers also reject Source candidates whose package identity changed while the provider reused the currently accepted version; the consumer must not repair the provider's release identity.
'''
        source_format.write_text(source_format.read_text(encoding="utf-8").rstrip() + append, encoding="utf-8")

    append_once(
        ROOT / "STATE.md",
        "Latest Source-update review readability and version discipline",
        """
## Latest Source-update review readability and version discipline

The real `ai-workstation` owner test confirmed that guided Source update, one-off `--ref`, and automatic `contextcanon.yaml` migration work correctly. The same run exposed two UX/integrity issues: immutable digests appeared before semantic meaning, and the changed Development Workflow still reused `0.2.0-draft`. PR #18 now presents a compact human summary before technical fingerprints and enforces human-meaningful package versions. SemVer-shaped unchanged versions receive only the minimum automatic patch bump, with an explicit reminder to consider a higher minor/major version; deliberately higher human versions are preserved. External candidates that changed package identity while reusing the accepted version are rejected.
""",
    )


def write_tests() -> None:
    (ROOT / "tests/test_review_readability.py").write_text(
        '''from contextcanon.diff import ContextDiff, DiffEntry, render_diff


def test_render_diff_puts_human_summary_before_technical_fingerprints():
    diff = ContextDiff(
        node_id="node",
        before_name="Development Workflow",
        after_name="Development Workflow",
        before_version="0.2.0-draft",
        after_version="0.2.1-draft",
        before_normalized_digest="a" * 64,
        after_normalized_digest="b" * 64,
        before_package_digest="c" * 64,
        after_package_digest="d" * 64,
        entries=(
            DiffEntry("rule", "added", "node#R1", None, {"status": "active"}),
            DiffEntry("rule", "added", "node#R2", None, {"status": "active"}),
            DiffEntry("rule", "added", "node#R3", None, {"status": "active"}),
            DiffEntry("resource", "modified", "docs/change.md", {"sha256": "x"}, {"sha256": "y"}, ("sha256",)),
        ),
    )
    rendered = render_diff(diff)
    assert "Version: 0.2.0-draft -> 0.2.1-draft" in rendered
    assert "Summary: 3 rules added, 1 resource changed" in rendered
    assert rendered.index("Summary:") < rendered.index("Rules:")
    assert rendered.index("Resources:") < rendered.index("Technical details:")
    assert "Normalized digest:" in rendered
    assert "Package digest:" in rendered
''',
        encoding="utf-8",
    )

    (ROOT / "tests/test_version_discipline.py").write_text(
        '''from __future__ import annotations

import contextlib
import io
import tempfile
from pathlib import Path

import pytest

from contextcanon.cli import main
from contextcanon.compiler import Compiler
from contextcanon.outputs import write_outputs
from contextcanon.parser import ContextCanonError, parse_node
from contextcanon.sources import install_source_package, review_source_candidate
from contextcanon.versioning import minimum_patch_bump


def node_text(version: str, statement: str) -> str:
    return (
        '# Demo — Local Context Source\\n'
        f'<!-- ctx:node id="demo" name="Demo" version="{version}" -->\\n\\n'
        '## Local Rules\\n\\n### General\\n\\n'
        f'- **Rule:** {statement}\\n  Why: Test.\\n  <!-- ctx:rule id="R1" -->\\n'
    )


def make_repo(version: str = "1.2.3-draft") -> Path:
    root = Path(tempfile.mkdtemp())
    (root / ".git").mkdir()
    (root / "CONTEXT.src.md").write_text(node_text(version, "Before."), encoding="utf-8")
    write_outputs(Compiler(root).compile(root))
    return root


def test_minimum_patch_bump_preserves_suffix():
    assert minimum_patch_bump("0.2.0-draft") == "0.2.1-draft"
    assert minimum_patch_bump("1.9.9") == "1.9.10"
    assert minimum_patch_bump("summer-preview") is None


def test_build_auto_bumps_reused_semver_and_advises_higher_version():
    root = make_repo()
    (root / "CONTEXT.src.md").write_text(node_text("1.2.3-draft", "After."), encoding="utf-8")
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = main(["build", str(root)])
    assert rc == 0
    assert parse_node(root).metadata.version == "1.2.4-draft"
    assert "Auto-bumped Context Node version: 1.2.3-draft -> 1.2.4-draft" in out.getvalue()
    assert "consider a higher minor or major version" in out.getvalue()
    assert main(["check", str(root)]) == 0


def test_build_preserves_human_selected_higher_version():
    root = make_repo()
    (root / "CONTEXT.src.md").write_text(node_text("2.0.0", "After."), encoding="utf-8")
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = main(["build", str(root)])
    assert rc == 0
    assert parse_node(root).metadata.version == "2.0.0"
    assert "Auto-bumped" not in out.getvalue()


def test_non_semver_reuse_requires_manual_version_change():
    root = make_repo("summer-preview")
    (root / "CONTEXT.src.md").write_text(node_text("summer-preview", "After."), encoding="utf-8")
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        rc = main(["build", str(root)])
    assert rc == 2
    assert "cannot be patch-bumped safely" in err.getvalue()


def test_source_review_rejects_changed_package_with_reused_version():
    consumer = Path(tempfile.mkdtemp())
    provider_before = Path(tempfile.mkdtemp())
    provider_after = Path(tempfile.mkdtemp())
    (consumer / ".git").mkdir()
    for root, statement in ((provider_before, "Before."), (provider_after, "After.")):
        (root / ".git").mkdir()
        (root / "CONTEXT.src.md").write_text(node_text("1.0.0", statement), encoding="utf-8")
        write_outputs(Compiler(root).compile(root))

    before = Compiler(provider_before).compile(provider_before)
    consumer_text = (
        '# Consumer\\n<!-- ctx:node id="consumer" name="Consumer" version="0.1.0" -->\\n\\n'
        '## Sources\\n\\n'
        '- [Demo](provider) — `1.0.0`\\n'
        f'  <!-- ctx:source id="demo" version="1.0.0" normalized-digest="{before.normalized_digest}" package-digest="{before.package_digest}" -->\\n'
    )
    (consumer / "CONTEXT.src.md").write_text(consumer_text, encoding="utf-8")
    install_source_package(consumer, provider_before)
    with pytest.raises(ContextCanonError, match="reused version"):
        review_source_candidate(consumer, "demo", provider_after)
''',
        encoding="utf-8",
    )


def update_existing_tests() -> None:
    path = ROOT / "tests/test_configuration_and_update_ux.py"
    text = path.read_text(encoding="utf-8")
    old = '            self.assertIn("Migrated legacy Source discovery", out.getvalue())\n'
    if "This migration only changes where future Source candidates are discovered." not in text:
        if old not in text:
            raise RuntimeError("Could not locate migration assertion")
        new = old + (
            '            self.assertIn("This migration only changes where future Source candidates are discovered.", out.getvalue())\n'
            '            self.assertIn("It does not change the accepted Source; acceptance happens only after this review.", out.getvalue())\n'
            '            self.assertIn("Fetched candidate: Shared", out.getvalue())\n'
        )
        text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")


def finish_plan() -> None:
    append_once(
        ROOT / "PLAN.md",
        "Issues #22/#26 owner-test implementation checkpoint",
        """
Issues #22/#26 owner-test implementation checkpoint: review output now leads with version and a compact semantic/content summary, followed by category details and a separate Technical details fingerprint section. Legacy discovery migration explicitly says acceptance is unchanged. Context Node package reuse under the same version is prevented: SemVer-shaped unchanged versions receive only a minimum patch bump with a visible minor/major reminder, human-selected higher versions are preserved, unsafe version formats require manual advancement, and external same-version/different-package Source candidates are rejected. Development Workflow advances to `0.2.1-draft`; affected self-hosted Context Nodes are versioned consistently. Full deterministic tests, self-build/check, and diff hygiene must remain green on the final product head.
""",
    )


def main() -> None:
    run("git", "config", "user.name", "github-actions[bot]")
    run("git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
    checkpoint_plan()

    write_versioning_module()
    update_diff_renderer()
    update_sources_validation()
    update_cli()
    update_versions_and_docs()
    write_tests()
    update_existing_tests()
    finish_plan()

    run(sys.executable, "-m", "pip", "install", "-e", ".", "pytest")
    run(sys.executable, "-m", "compileall", "-q", "src", "tests")
    run(sys.executable, "-m", "pytest", "-q")
    run("contextcanon", "build", "--all", ".")
    run("contextcanon", "check", "--all", ".")
    run("git", "diff", "--check")

    for rel in (
        ".github/scripts/finalize_issue22_review_readability.py",
        ".github/workflows/issue22-review-readability-finalizer.yml",
        ".github/scripts/finalize_issues22_26.py",
        ".github/workflows/issues22-26-finalizer.yml",
    ):
        path = ROOT / rel
        if path.exists():
            run("git", "rm", "-f", rel)
    run("git", "add", "-A")
    run("git", "commit", "-m", "Enforce Context package version advancement (#26)")
    run("git", "push", "origin", f"HEAD:{BRANCH}")


if __name__ == "__main__":
    main()
