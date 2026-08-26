# Tests and GitHub Actions CI

ContextCanon uses two complementary deterministic test levels:

1. **behavior and repository tests** — Python `unittest` checks compiler/onboarding behavior, failure cases, stable identities, package integrity, links, and other contracts;
2. **dogfood drift verification** — `contextcanon check --all .` recompiles every ContextCanon Node in memory and verifies that committed generated packages exactly match current source and compiler behavior.

A change is review-ready only when both levels pass on the exact current Git head.

## What GitHub does for us

The repository uses **GitHub Actions** through [`.github/workflows/test.yml`](https://github.com/SomeSunlight/context-canon/blob/main/.github/workflows/test.yml). No project-owned CI server has to be kept running.

For every pull request, and for pushes to `main`, GitHub starts a hosted `ubuntu-latest` runner and performs this workflow:

```text
checkout repository
      ↓
install Python 3.12
      ↓
pip install -e .
      ↓
python -m unittest discover -s tests -v
      ↓
contextcanon check --all .
      ↓
all green → this head is deterministic and has zero generated drift
```

The workflow is intentionally boring: no external LLM, model API, or network service participates in test truth.

## What the Python tests cover

The `tests/` directory uses standard-library `unittest` and temporary local repositories. Different files focus on different boundaries, for example:

- compiler walking skeleton, parsing, rendering, Topics and generated output;
- semantic normalization and deterministic diff;
- immutable packages, Source transport/review/acceptance and failure recovery;
- onboarding evidence, semantic-instruction contract, proposal validation, human review and first-adoption acceptance;
- repository consistency such as broken local Markdown links.

Git transport tests create a real **local temporary Git repository**. They do not depend on GitHub or another remote service.

The current exact test count is best read from the GitHub Actions log rather than copied into this document, because it changes as regression coverage grows.

## Why the dogfood check is separate

Unit tests can all pass while committed generated ContextCanon files are stale.

`contextcanon check --all .` compiles the repository's Nodes in memory and compares the expected generated files with the committed ones. It catches cases such as:

- changed `CONTEXT.src.md` with old `CONTEXT.md`;
- moved or edited Topic resources with stale materialized copies;
- changed compiler rendering with old `.context/package.json`;
- a newly added Context Node whose generated package has not been committed.

That makes ContextCanon itself a real consumer of its compiler instead of only testing synthetic fixtures.

## What happens when generated drift is found

The CI job deliberately fails the drift step. For diagnosis it then runs:

```text
contextcanon build --all .
git add -N .
git diff
```

This shows the exact compiler-generated difference in the Actions log, including new files.

The workflow also uploads a short-lived artifact named `generated-drift` containing the generated ContextCanon output. It is a **diagnostic snapshot**, not a second source of truth and not a durable download location. Its retention is currently one day; old signed artifact links can therefore expire.

The correct durable fix is to regenerate the affected dogfood from the same source/compiler state and commit those exact generated files to GitHub.

## How to inspect a failed run in GitHub

From the pull request:

1. open **Checks** (or the failed `tests` check);
2. open the `test` job;
3. expand **Unit and repository consistency tests** when a behavior/link test failed;
4. expand **Verify generated ContextCanon output** when the failure is generated drift;
5. inspect the grouped `Generated drift diff` before touching generated files.

The repository's [Actions page](https://github.com/SomeSunlight/context-canon/actions) shows the same runs independently of the PR view.

## Efficient correction cadence

Do not regenerate dogfood after every tiny edit merely because CI exists.

For one coherent review correction:

```text
related source/docs/code edits
      ↓
run/receive deterministic tests
      ↓
one CI head exposes the resulting generated drift
      ↓
regenerate exactly the affected dogfood once
      ↓
final exact-head CI must pass tests + zero drift
```

The workflow cancels superseded runs for the same PR/ref, so rapid corrective commits do not keep obsolete CI jobs running in parallel.

This keeps the strong final gate while avoiding repeated work on intermediate heads that will never be reviewed.
