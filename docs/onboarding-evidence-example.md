# Onboarding Evidence Example

This small example exists to make the first onboarding boundary concrete without pretending that semantic proposal generation is already implemented.

Given a repository such as:

```text
example-project/
├── README.md
├── CONTRIBUTING.md
├── pyproject.toml
├── docs/
│   └── architecture.md
├── src/
│   └── main.py
└── .env
```

an ordinary preparation run may select README, CONTRIBUTING, `pyproject.toml`, and the architecture document automatically. `src/main.py` is ordinary source code and is not automatically selected. `.env` is outside the automatic evidence categories and would additionally be rejected by the sensitive-path guard if explicitly requested.

The resulting snapshot is conceptually:

```text
.context/onboarding/<digest>/
├── manifest.json
└── evidence/
    ├── README.md
    ├── CONTRIBUTING.md
    ├── pyproject.toml
    └── docs/
        └── architecture.md
```

If the onboarding classifier later needs one specific source file to understand a repository convention, the operator or workflow can prepare another snapshot with an explicit include rather than changing the automatic policy to ingest all source code:

```text
contextcanon onboard prepare . --include src/main.py
```

This distinction is deliberate. Automatic evidence should remain conservative and predictable; task-specific expansion should remain explicit and reviewable.
