# `contextcanon` Python package

This directory contains ContextCanon's deterministic implementation modules. The code is intentionally split into narrow layers instead of one framework engine.

High-level map:

- `model.py` — typed deterministic data structures;
- `authoring.py` — narrow safe writes to ordinary `CONTEXT.src.md`, including stable Rule/Topic ID allocation;
- `parser.py` — constrained `CONTEXT.src.md` grammar;
- `compiler.py` — Source composition, Rule changes, Topic/resource collection and semantic validation;
- `package.py` — immutable package identity, manifests and verification;
- `render.py` — deterministic human/machine projections;
- `outputs.py` — generated-output comparison and writing;
- `diff.py` / `package_diff.py` — exact comparison by stable identity;
- `git_transport.py` / `sources.py` — candidate retrieval, Source review and explicit acceptance;
- `onboarding.py`, `onboarding_instruction.py`, `onboarding_proposal.py`, `onboarding_review.py` — the reviewed first-adoption pipeline;
- `onboarding_placement_audit.py` — generated source-file-first audit projection of the current human placement review;
- `cli.py` — command orchestration only.

Do not infer architecture from filenames alone when changing behavior. Follow the [Framework Development Context](../../nodes/internal/framework-development/CONTEXT.md) and its matching Topic first.
