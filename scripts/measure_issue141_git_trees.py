#!/usr/bin/env python3
"""Read-only exact Git-tree inventory for #141, with an explicitly analytical CAS bound.

Full executable materialization experiment is intentionally separate from this
inventory: no production ContextCanon imports or stores are modified.
Run inside a clone containing the exact before/after #137 commits.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import subprocess

BEFORE = "5a1f2bff24a9f6c6af49d96044eaf15b80d0d0b6"
AFTER = "359f7efe6b02d59b75d3c7e5ffedfa7ed9c9c99c"
VERSIONS = ".context/versions/"


def git(repo: Path, *args: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout


def blobs(repo: Path, commit: str) -> dict[str, tuple[str, int]]:
    entries = {}
    for row in git(repo, "ls-tree", "-r", "-l", "-z", commit).split(b"\0"):
        if not row:
            continue
        header, path_bytes = row.split(b"\t", 1)
        mode, typ, obj, size = header.decode("ascii").split()
        if typ != "blob":
            continue
        path = path_bytes.decode("utf-8")
        entries[path] = (obj, int(size))
    return entries


def totals(items: dict[str, tuple[str, int]]) -> dict[str, int]:
    distinct = dict((sha, size) for sha, size in items.values())
    return {
        "paths": len(items),
        "logical_bytes": sum(size for sha, size in items.values()),
        "unique_blobs": len(distinct),
        "unique_blob_bytes": sum(distinct.values()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--before", default=BEFORE)
    parser.add_argument("--after", default=AFTER)
    args = parser.parse_args()
    repo = args.repo.resolve()
    old, new = blobs(repo, args.before), blobs(repo, args.after)
    old_h = {p: v for p, v in old.items() if p.startswith(VERSIONS)}
    new_h = {p: v for p, v in new.items() if p.startswith(VERSIONS)}
    new_paths = {p: v for p, v in new_h.items() if p not in old_h}
    new_history_packages = [
        p for p in new_paths if p.endswith("/.context/package.json")
    ]
    old_objects = {sha for sha, size in old_h.values()}
    new_unique = {sha: size for sha, size in new_paths.values()
                  if sha not in old_objects}
    changes = git(repo, "diff", "--numstat", args.before, args.after)
    rows = []
    for line in changes.splitlines():
        add, remove, path = line.decode("utf-8").split("\t", 2)
        rows.append((add, remove, path))
    base_history_changes = [row for row in rows if row[2].startswith(VERSIONS)]
    additions = sum(int(a) for a, b, path in rows if a.isdecimal())
    deletions = sum(int(b) for a, b, path in rows if b.isdecimal())
    history_adds = sum(int(a) for a, b, path in base_history_changes
                       if a.isdecimal())
    result = {
        "source": "actual Git object metadata, not a transformed-store benchmark",
        "before": args.before,
        "after": args.after,
        "tree_before": totals(old),
        "tree_after": totals(new),
        "history_before": totals(old_h),
        "history_after": totals(new_h),
        "real_v4_diff": {
            "changed_paths": len(rows),
            "added_lines": additions,
            "deleted_lines": deletions,
            "history_changed_paths": len(base_history_changes),
            "history_added_lines": history_adds,
            "history_new_paths": len(new_paths),
            "history_new_file_bytes": sum(size for sha, size in new_paths.values()),
            "new_version_manifests": len(new_history_packages),
        },
        "git_blob_reuse": {
            "new_unique_historical_blobs": len(new_unique),
            "new_unique_historical_blob_bytes": sum(new_unique.values()),
        },
        "cas_upper_bound_not_proven": {
            "new_historical_paths_if_preexisting_history_were_fully_CAS": (
                len(new_unique) + len(new_history_packages)
            ),
            "plus_changed_history_inventory_paths": (
                len(base_history_changes) - len(new_paths)
            ),
            "note": "Counts only. No serialized index overhead, export, migration "
                    "or real alternative Git diff was run.",
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
