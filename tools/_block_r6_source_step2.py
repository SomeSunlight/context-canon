from __future__ import annotations

import sys
from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one match, found {count}: {old[:120]!r}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


def patch_sources() -> None:
    replace_once(
        "src/contextcanon/sources.py",
        "from .diff import ContextDiff\n",
        "from .diff import ContextDiff\nfrom .git_transport import load_candidate_provenance\n",
    )
    replace_once(
        "src/contextcanon/sources.py",
        '''    _validate_candidate_composition(compiler, compiled, index, candidate)\n    result = diff_packages(current, candidate)\n\n    source_hash = _source_hash(node_root)\n''',
        '''    transport_candidate = _validated_candidate_provenance(node_root, source_ref, candidate)\n    _validate_candidate_composition(compiler, compiled, index, candidate)\n    result = diff_packages(current, candidate)\n\n    source_hash = _source_hash(node_root)\n''',
    )
    replace_once(
        "src/contextcanon/sources.py",
        '''        "candidate": {\n            "version": candidate.metadata.version,\n            "normalized_digest": candidate.normalized_digest,\n            "package_digest": candidate.package_digest,\n        },\n        "structural_validation": "passed",\n''',
        '''        "candidate": {\n            "version": candidate.metadata.version,\n            "normalized_digest": candidate.normalized_digest,\n            "package_digest": candidate.package_digest,\n        },\n        "transport_candidate": transport_candidate,\n        "structural_validation": "passed",\n''',
    )
    replace_once(
        "src/contextcanon/sources.py",
        '''    if receipt.get("structural_validation") != "passed":\n        raise ContextCanonError("Source candidate review did not pass structural validation")\n\n    _validate_candidate_composition(compiler, compiled, index, candidate)\n    _install_package(node_root, candidate_root, candidate)\n    _write_source_pin(node_root, source_id, candidate)\n''',
        '''    if receipt.get("structural_validation") != "passed":\n        raise ContextCanonError("Source candidate review did not pass structural validation")\n\n    transport_candidate = _validated_candidate_provenance(node_root, source_ref, candidate)\n    if receipt.get("transport_candidate") != transport_candidate:\n        raise ContextCanonError("Git Source candidate provenance differs from the reviewed candidate")\n\n    _validate_candidate_composition(compiler, compiled, index, candidate)\n    _install_package(node_root, candidate_root, candidate)\n    accepted_ref = None if transport_candidate is None else transport_candidate["candidate_ref"]\n    _write_source_pin(node_root, source_id, candidate, accepted_ref=accepted_ref)\n''',
    )

    anchor = "\ndef _review_path(node_root: Path, candidate_package_digest: str) -> Path:\n"
    helper = r'''
def _validated_candidate_provenance(
    node_root: Path,
    source_ref: SourceRef,
    candidate: CompiledPackage,
) -> dict[str, str] | None:
    provenance = load_candidate_provenance(node_root, candidate.package_digest)
    if provenance is None:
        return None
    if provenance["source_id"] != source_ref.id:
        raise ContextCanonError("Git Source candidate provenance belongs to a different Source")
    if provenance["locator"] != source_ref.locator:
        raise ContextCanonError("Git Source candidate provenance locator differs from the accepted Source")
    if provenance["node_path"] != (source_ref.node_path or "."):
        raise ContextCanonError("Git Source candidate provenance node-path differs from the accepted Source")
    if provenance["accepted_ref"] != (source_ref.transport_ref or ""):
        raise ContextCanonError(
            "Accepted Git Source ref changed after candidate discovery; fetch the candidate again before review"
        )
    if provenance["package_digest"] != candidate.package_digest:
        raise ContextCanonError("Git Source candidate provenance package digest mismatch")
    return provenance

'''
    p = Path("src/contextcanon/sources.py")
    text = p.read_text(encoding="utf-8")
    if anchor not in text:
        raise SystemExit("sources candidate provenance insertion anchor missing")
    p.write_text(text.replace(anchor, helper + anchor, 1), encoding="utf-8")

    # Make canonical Source pin update the exact accepted commit for the modern
    # SHA-pinned form. Historical symbolic refs remain discovery-channel names.
    replace_once(
        "src/contextcanon/sources.py",
        "def _write_source_pin(node_root: Path, source_id: str, candidate: CompiledPackage) -> None:\n",
        "def _write_source_pin(node_root: Path, source_id: str, candidate: CompiledPackage, *, accepted_ref: str | None = None) -> None:\n",
    )
    replace_once(
        "src/contextcanon/sources.py",
        '''                elif key not in {"normalized-digest", "package-digest"}:\n                    updated.append((key, value))\n''',
        '''                elif key == "ref" and accepted_ref is not None and re.fullmatch(r"[0-9a-f]{40}", value):\n                    updated.append((key, accepted_ref))\n                elif key not in {"normalized-digest", "package-digest"}:\n                    updated.append((key, value))\n''',
    )


def patch_tests() -> None:
    p = Path("tests/test_git_transport.py")
    text = p.read_text(encoding="utf-8")
    marker = "    def test_git_fetch_rejects_missing_node_path(self):\n"
    test = r'''    def test_review_accept_is_bound_to_fetched_commit_even_if_remote_moves_again(self):
        provider, v1, v2 = self.make_provider()
        commits = self.git(provider, "log", "--format=%H", "--reverse").stdout.splitlines()
        accepted_ref, reviewed_ref = commits
        consumer = self.make_consumer(provider, v1)
        source_path = consumer / "CONTEXT.src.md"
        source_path.write_text(
            source_path.read_text(encoding="utf-8").replace('ref="main"', f'ref="{accepted_ref}"'),
            encoding="utf-8",
        )

        candidate, candidate_root = fetch_git_candidate(consumer, "node-python")
        self.assertEqual(candidate.package_digest, v2.package_digest)
        diff, receipt = review_source_candidate(consumer, "node-python", candidate_root)
        self.assertFalse(diff.is_empty)
        reviewed = __import__("json").loads(receipt.read_text(encoding="utf-8"))
        self.assertEqual(reviewed["transport_candidate"]["candidate_ref"], reviewed_ref)

        # Remote development continues after review. Acceptance must not look
        # at the moving repository again.
        node = provider / "nodes/library/python-development"
        (node / "CONTEXT.src.md").write_text(
            PROVIDER_TEMPLATE.format(version="3.0.0", statement="Prefer explicit Python v3."),
            encoding="utf-8",
        )
        v3 = Compiler(provider).compile(node)
        write_outputs(v3)
        self.git(provider, "add", ".")
        self.git(provider, "commit", "-m", "Publish Python context v3")
        latest_ref = self.git(provider, "rev-parse", "HEAD").stdout.strip()
        self.assertNotEqual(latest_ref, reviewed_ref)

        accepted = accept_source_candidate(consumer, "node-python", candidate_root)
        self.assertEqual(accepted.package_digest, v2.package_digest)
        source = parse_node(consumer, consumer).sources[0]
        self.assertEqual(source.transport_ref, reviewed_ref)
        self.assertEqual(source.package_digest, v2.package_digest)
        compiled = Compiler(consumer).compile(consumer)
        self.assertEqual(compiled.inherited_rules[0].statement, "Prefer explicit Python v2.")

        # A later explicit fetch discovers v3 from the moving default branch,
        # proving the newly accepted exact ref is provenance rather than a live
        # build dependency or a discovery dead-end.
        next_candidate, _ = fetch_git_candidate(consumer, "node-python")
        self.assertEqual(next_candidate.package_digest, v3.package_digest)
        next_provenance = load_candidate_provenance(consumer, v3.package_digest)
        self.assertEqual(next_provenance["accepted_ref"], reviewed_ref)
        self.assertEqual(next_provenance["candidate_ref"], latest_ref)

'''
    if marker not in text:
        raise SystemExit("git transport R6/2 insertion marker missing")
    p.write_text(text.replace(marker, test + marker, 1), encoding="utf-8")

    # Tighten the existing full fetch/review/accept test: symbolic historical
    # branch refs remain symbolic after acceptance.
    old = "        self.assertIn('ref=\"main\"', text)\n"
    if old not in p.read_text(encoding="utf-8"):
        raise SystemExit("symbolic ref preservation assertion missing")


def patch_docs() -> None:
    replace_once(
        "nodes/internal/framework-development/docs/external-sources.md",
        "The receipt is bound to the exact current `CONTEXT.src.md`, the currently accepted Source state, the candidate package identity, the deterministic diff, and successful structural validation.",
        "The receipt is bound to the exact current `CONTEXT.src.md`, the currently accepted Source state, the candidate package identity, the deterministic diff, successful structural validation, and — for Git-fetched candidates — the exact frozen candidate commit plus locator/node-path provenance recorded at fetch time.",
    )
    replace_once(
        "nodes/internal/framework-development/docs/external-sources.md",
        "`source accept` requires the matching review receipt. It revalidates the candidate and structural composition, rejects the operation if `CONTEXT.src.md` or the accepted Source state changed since review, installs the candidate into `.context/sources/<package-digest>/`, and then updates the visible Source version plus exact digest pins in `CONTEXT.src.md`.\n\nGit transport metadata is preserved when the pin is updated.",
        "`source accept` requires the matching review receipt. It revalidates the candidate, its frozen Git provenance and structural composition, rejects the operation if `CONTEXT.src.md` or the accepted Source state changed since review, installs the candidate into `.context/sources/<package-digest>/`, and then updates the visible Source version plus exact digest pins in `CONTEXT.src.md`. Acceptance never contacts the remote repository.\n\nFor the current exact-commit transport form, `ref` advances from the previously accepted commit to the exact reviewed candidate commit. Historical symbolic branch/tag refs remain symbolic so their explicitly chosen discovery channel is preserved. In both cases the normal build still uses only the accepted local package bytes.",
    )


def complete() -> None:
    replace_once(
        "PLAN.md",
        "**Status: ACTIVE — R6 reusable Source update discovery UX, step 2 of 3. Fast-run remains ACTIVE.**",
        "**Status: ACTIVE — R6 reusable Source update discovery UX, step 3 of 3. Fast-run remains ACTIVE.**",
    )
    replace_once(
        "PLAN.md",
        "- [ ] 2. Keep every update candidate-only until explicit review/accept; never introduce live implicit pulls.",
        "- [x] 2. Keep every update candidate-only until explicit review/accept; never introduce live implicit pulls.",
    )
    state = Path("STATE.md")
    state.write_text(
        state.read_text(encoding="utf-8").rstrip()
        + "\n\n## Latest Block R6 step 2 exact-Source-update checkpoint\n\nReusable Source review/accept is now bound to the exact Git candidate provenance frozen during fetch as well as package identity and consumer state. The remote may move again after review without changing what accept means; acceptance never contacts it. Current exact-commit Source pins advance to the reviewed candidate commit, while historical symbolic discovery refs remain symbolic. Normal builds remain fully offline against accepted local package bytes. R6 proceeds to documenting and proving the ordinary daily update loop.\n",
        encoding="utf-8",
    )


def apply() -> None:
    patch_sources()
    patch_tests()
    patch_docs()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--complete":
        complete()
    else:
        apply()
