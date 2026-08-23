# Onboarding fixtures

The executable onboarding tests create temporary Git repositories at runtime so file-system mutation, Git ignore behavior, content-addressed snapshots, and corruption checks are exercised against real repositories. Static fixture content is intentionally minimal; test cases author only the evidence needed for each invariant.
