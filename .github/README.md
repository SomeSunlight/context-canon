# GitHub repository automation

This directory contains GitHub-specific repository integration rather than ContextCanon semantic truth.

Current automation lives under [`workflows/`](workflows/) and runs the deterministic test/dogfood gate for pull requests and `main`.

ContextCanon itself remains GitHub-independent: compiler truth, package identity, Source composition, onboarding review state, and acceptance semantics live in the Python implementation and Context Nodes. GitHub Actions is simply the hosted CI runner used by this repository.

For the user-facing explanation of the CI flow, read [Tests and GitHub Actions CI](../nodes/internal/framework-development/docs/tests-and-ci.md).
