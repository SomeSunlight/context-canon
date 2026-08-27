# GitHub Actions workflows

This directory contains the hosted CI definitions for the ContextCanon repository.

[`test.yml`](test.yml) checks out the repository on a GitHub-hosted Ubuntu runner, installs Python 3.12 and ContextCanon, runs the deterministic `unittest` suite, then verifies ContextCanon's committed self-hosted generated packages with `contextcanon check --all .`.

If generated drift is found, the workflow prints the exact compiler-generated diff and uploads a one-day `generated-drift` diagnostic artifact. That artifact is temporary troubleshooting material, **not another source of truth**.

The workflow cancels superseded runs for the same PR/ref. A human review candidate may still have understood and disclosed generated drift; the exact head intended for merge to `main` must complete the full test + zero-drift gate.

See [Tests and GitHub Actions CI](../../nodes/internal/framework-development/docs/tests-and-ci.md) for the human walkthrough.
