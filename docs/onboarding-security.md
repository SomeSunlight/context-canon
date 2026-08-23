# Onboarding Evidence Safety

The onboarding evidence selector is intentionally conservative because later semantic workflows may send the selected text to a model or harness. Automatic repository discovery therefore must not be treated as permission to expose every readable file.

The first boundary is simple:

- Git ignore rules limit automatic visibility;
- only known context-bearing categories are selected automatically;
- common credential, private-key, secret-store, and environment-file names are blocked;
- `.context/` and common derived/dependency trees are not evidence;
- symlinks are not dereferenced;
- automatic files are limited to UTF-8 text and 1 MiB each;
- an explicit include may widen semantic scope but does not bypass these safety checks.

These checks are deterministic guardrails, not a claim that every non-blocked file is non-sensitive. Human review remains necessary before a later model is given evidence from a repository with unusual confidentiality rules.

Future support for PDFs, images, binary documents, larger files, or deliberately sensitive material should add explicit reviewed mechanisms rather than weakening the default evidence contract.
