# Root documentation

This directory contains documentation owned by the repository-root **ContextCanon Gateway** rather than by a deeper Context Node.

It is deliberately small:

- [`onboarding.md`](onboarding.md) — the user-facing first-contact guide for bringing an existing project into ContextCanon.
- [`onboarding-reference.md`](onboarding-reference.md) — a compatibility pointer for older links; the technical reference itself is owned and authored by Framework Development.

Most technical design and implementation documentation belongs to the [ContextCanon Framework Development Node](../nodes/internal/framework-development/) and is authored below its [`docs/`](../nodes/internal/framework-development/docs/) directory.

Short `README.md` files are used at important directory boundaries throughout this repository because GitHub renders them automatically when a directory is opened. They are orientation signs, not second copies of the deeper documentation.

## Why similar files also appear under `CONTEXT/`

`CONTEXT.md` and `CONTEXT/` are **generated package output**. When a Topic references an authored document, the compiler copies that exact resource into `CONTEXT/references/...` so the Official Context Package is self-contained.

Therefore:

- edit files in this `docs/` directory or in the owning Node's authored `docs/` directory;
- do **not** edit `CONTEXT/references/...`;
- a generated copy is not a second documentation source and does not need separate maintenance;
- `contextcanon build --all .` refreshes generated copies, and CI rejects stale copies.

If a generated copy differs from its authored source, the repository is in **generated drift** and has not yet reached a clean review state.
