# Tests and GitHub Actions CI

ContextCanon uses two complementary deterministic test levels:

1. **behavior and repository tests** — Python `unittest` checks compiler/onboarding behavior, failure cases, stable identities, package integrity, links, and other contracts;
2. **self-hosted package drift verification** — `contextcanon check --all .` recompiles every ContextCanon Node used by this repository in memory and verifies that committed generated packages exactly match current source and compiler behavior.

During project-owner review, known and disclosed generated drift may remain while the authored large line is still changing. Before merge to `main`, both levels must pass on the exact merge candidate.

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
all green → this exact head is deterministic and has zero generated drift
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

## Why the generated-package check is separate

Unit tests can all pass while committed generated ContextCanon files are stale.

`contextcanon check --all .` compiles the repository's own Context Nodes in memory and compares the expected generated files with the committed ones. It catches cases such as:

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

The correct durable fix is to regenerate the affected self-hosted Context packages from the same source/compiler state and commit those exact generated files to GitHub.

## How to inspect a failed run in GitHub

From the pull request:

1. open **Checks** (or the failed `tests` check);
2. open the `test` job;
3. expand **Unit and repository consistency tests** when a behavior/link test failed;
4. expand **Verify generated ContextCanon output** when the failure is generated drift;
5. inspect the grouped `Generated drift diff` before touching generated files.

The repository's [Actions page](https://github.com/SomeSunlight/context-canon/actions) shows the same runs independently of the PR view.

## Efficient correction cadence

Do not regenerate ContextCanon's own generated packages after every tiny edit merely because CI exists.

For one coherent review correction:

```text
related source/docs/code edits
      ↓
run/receive deterministic tests
      ↓
present the coherent authored result for project-owner review
      ↓
apply any review corrections
      ↓
after approval, regenerate exactly the affected self-hosted packages once
      ↓
merge-candidate exact-head CI must pass tests + zero drift
```

Known generated drift may therefore be visible during review, but unknown failures still require investigation. The workflow cancels superseded runs for the same PR/ref, so rapid corrective commits do not keep obsolete CI jobs running in parallel.

This keeps the strong merge gate while avoiding repeated package regeneration on intermediate heads that may still change during human review.
