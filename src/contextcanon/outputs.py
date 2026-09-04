from __future__ import annotations

from .model import CompiledNode
from .package import PACKAGE_MANIFEST_PATH
from .render import render_node_readme


def expected_outputs(compiled: CompiledNode) -> dict[str, bytes]:
    outputs: dict[str, bytes] = {
        "CONTEXT.md": compiled.official_markdown.encode("utf-8"),
        ".context/context.yaml": compiled.machine_yaml.encode("utf-8"),
        PACKAGE_MANIFEST_PATH: compiled.package_manifest.encode("utf-8"),
    }
    outputs.update({path: content for path, content in compiled.resources.items()})
    outputs.update({path: content.encode("utf-8") for path, content in compiled.adapters.items()})
    readme = compiled.parsed.root / "README.md"
    manage_readme = not readme.exists()
    if readme.is_file() and not readme.is_symlink():
        try:
            manage_readme = readme.read_text(encoding="utf-8").startswith("<!-- contextcanon:generated-node-readme -->\n")
        except (OSError, UnicodeDecodeError):
            manage_readme = False
    if manage_readme:
        outputs["README.md"] = render_node_readme(compiled).encode("utf-8")
    return outputs


def write_outputs(compiled: CompiledNode) -> list[str]:
    outputs = expected_outputs(compiled)
    root = compiled.parsed.root
    changed: list[str] = []

    context_dir = root / "CONTEXT"
    expected_context_paths = {path for path in outputs if path.startswith("CONTEXT/")}
    if context_dir.exists():
        actual_context_paths = {
            path.relative_to(root).as_posix()
            for path in context_dir.rglob("*")
            if path.is_file()
        }
        for extra in sorted(actual_context_paths - expected_context_paths):
            (root / extra).unlink()
            changed.append(f"removed {extra}")
        for directory in sorted(
            (path for path in context_dir.rglob("*") if path.is_dir()),
            key=lambda path: len(path.parts),
            reverse=True,
        ):
            try:
                directory.rmdir()
            except OSError:
                pass
        if not expected_context_paths:
            try:
                context_dir.rmdir()
                changed.append("removed CONTEXT/")
            except OSError:
                pass

    for rel, content in outputs.items():
        destination = root / rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        old = destination.read_bytes() if destination.is_file() else None
        if old != content:
            destination.write_bytes(content)
            changed.append(rel)
    return changed


def check_outputs(compiled: CompiledNode) -> list[str]:
    outputs = expected_outputs(compiled)
    root = compiled.parsed.root
    drift: list[str] = []
    for rel, content in outputs.items():
        destination = root / rel
        if not destination.is_file():
            drift.append(f"missing {rel}")
        elif destination.read_bytes() != content:
            drift.append(f"changed {rel}")

    context_dir = root / "CONTEXT"
    expected_context = {rel for rel in outputs if rel.startswith("CONTEXT/")}
    if context_dir.exists():
        actual_context = {
            path.relative_to(root).as_posix()
            for path in context_dir.rglob("*")
            if path.is_file()
        }
        for extra in sorted(actual_context - expected_context):
            drift.append(f"extra {extra}")
    elif expected_context:
        drift.append("missing CONTEXT/")
    return drift
