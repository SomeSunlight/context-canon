# Tests

This directory contains ContextCanon's deterministic Python regression suite. It uses standard-library `unittest`, temporary local repositories, and locally built package fixtures; tests must not require an external LLM or remote service.

The suite covers compiler behavior, package identity/integrity, Source transport and acceptance, onboarding preparation/review/acceptance, failure recovery, generated folder orientation, and repository consistency such as local Markdown links.

Run everything with:

```text
python -m unittest discover -s tests -v
```

Unit/repository tests are only one of ContextCanon's two verification levels. GitHub Actions also runs `contextcanon check --all .` to prove that committed dogfood output matches the compiler exactly.

For the full flow and how to inspect CI failures, read [Tests and GitHub Actions CI](../nodes/internal/framework-development/docs/tests-and-ci.md).
