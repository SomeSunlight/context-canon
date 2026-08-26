# Root documentation

This directory contains documentation owned by the repository-root **ContextCanon Gateway** rather than by a deeper Context Node.

At present that is deliberately small:

- [`onboarding.md`](onboarding.md) — the user-facing first-contact guide for bringing an existing project into ContextCanon.

Most technical design and implementation documentation belongs to the [ContextCanon Framework Development Node](../nodes/internal/framework-development/) and is authored below its `docs/` directory.

## Why similar files also appear under `CONTEXT/`

`CONTEXT.md` and `CONTEXT/` are **generated package output**. When a Topic references an authored document, the compiler copies that exact resource into `CONTEXT/references/...` so the Official Context Package is self-contained.

Therefore:

- edit files in this `docs/` directory or in the owning Node's authored `docs/` directory;
- do **not** edit `CONTEXT/references/...`;
- a generated copy is not a second documentation source and does not need separate maintenance;
- `contextcanon build --all .` refreshes generated copies, and CI rejects stale copies.

If a generated copy differs from its authored source, the repository is in **generated drift** and has not yet reached a clean review state.
