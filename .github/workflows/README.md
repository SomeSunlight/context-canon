# GitHub Actions workflows

This directory contains the hosted CI definitions for the ContextCanon repository.

[`test.yml`](test.yml) is the current gate. For pull requests and pushes to `main`, it checks out the repository on a GitHub-hosted Ubuntu runner, installs Python 3.12 and ContextCanon, runs the deterministic `unittest` suite, then verifies all committed dogfood with `contextcanon check --all .`.

If generated drift is found, the workflow prints the exact compiler-generated diff and uploads a one-day `generated-drift` diagnostic artifact. That artifact is temporary troubleshooting material, **not another source of truth**.

The workflow cancels superseded runs for the same PR/ref. The exact head presented for review must still complete the full test + zero-drift gate.

See [Tests and GitHub Actions CI](../../nodes/internal/framework-development/docs/tests-and-ci.md) for the human walkthrough.
