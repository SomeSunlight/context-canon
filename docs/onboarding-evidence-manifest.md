# Onboarding Evidence Manifest

`contextcanon/onboarding-evidence/v0` is the deterministic machine contract produced by `contextcanon onboard prepare`.

The manifest is intentionally small. It records the evidence boundary, not semantic interpretation.

```json
{
  "schema": "contextcanon/onboarding-evidence/v0",
  "selection": {
    "accepted_encoding": "utf-8",
    "max_file_bytes": 1048576,
    "policy": "contextcanon/onboarding-default/v0",
    "repository_listing": "git ls-files --cached --others --exclude-standard"
  },
  "included": [
    {
      "path": "README.md",
      "reason": "root-document",
      "sha256": "...",
      "size": 1234,
      "snapshot": "evidence/README.md"
    }
  ],
  "excluded": [
    {
      "path": "docs/secrets.md",
      "reason": "sensitive-path"
    }
  ],
  "evidence_digest": "..."
}
```

The evidence digest is calculated from the canonical JSON representation of all fields except `evidence_digest` itself. Included file hashes bind exact bytes. Excluded entries bind the deterministic decision that a matching candidate was not offered, without copying its content.

Absolute paths, timestamps, user names, host names, Git remotes, and model information are excluded from the identity so equivalent evidence remains portable across checkouts and harnesses.
