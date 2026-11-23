# External GitHub contributions — optional publication best practice

This is **practical guidance, not an enforceable Rule**. Prefer an approach that matches the repository, connected tools, permissions and human workflow. Browser publication, a suitable connector, a delegated workflow or the GitHub CLI may all be valid.

## When this helps

A connected GitHub App may read a public upstream repository but receive `HTTP 403: Resource not accessible by integration` on issue creation. ChatGPT's *Allow all actions* setting governs assistant action approvals; it **does not** grant GitHub App installation permissions in another organization. Increasing that setting or requesting unnecessary upstream write access is not the remedy.

For public issues, a contributor can generally use their **personal GitHub identity** with `gh issue create`. This does not require write/push access to the upstream code repository. Publication remains subject to GitHub and repository participation restrictions.

## Suggested workflow

1. **Prepare and review the report.** Check current upstream code, open/closed issues and PRs for duplicates or an existing fix. Distinguish facts verified by reproduction from hypotheses. Separate affected-user mitigation from maintainers' possible implementation approaches; cite precise source lines when useful. Do not publish private paths, credentials, tokens, identifying logs or other secrets.
2. **Select an authorized publication method.** A connector with sufficient rights is fine. If a GitHub App cannot write to an external repository, prefer a human-operated authenticated `gh` command or the GitHub website rather than broadening global permissions. Confirm the owner's approval before any public publication.
3. **Save the reviewed body as UTF-8 Markdown.** Keep the title separate so it is not duplicated. Use an ordinary file path that is accessible from the shell running `gh`.
4. **Authenticate and publish.** Confirm which personal GitHub account will act. On Windows PowerShell, for example:

   ```powershell
   gh auth status
   # Only if not already signed in:
   # gh auth login --hostname github.com --web

   $bodyFile = Join-Path $HOME 'Downloads\upstream-issue.md'
   if (-not (Test-Path -LiteralPath $bodyFile)) {
       throw "Missing reviewed issue body: $bodyFile"
   }

   gh issue create `
       --repo OWNER/REPO `
       --title "Concise issue title" `
       --body-file $bodyFile
   ```

   Replace `OWNER/REPO`, title and filename with the actual reviewed values. `gh` works on Linux/macOS too, with appropriate shell syntax. Do **not** send authentication tokens to an assistant or commit them to Git.
5. **Verify and record the outcome.** Capture the exact URL/issue number returned by GitHub in the relevant project's Issue/PLAN or equivalent durable record. If publication fails, keep the draft and investigate the actual denial; never claim success without an issue URL.

## Issues are different from pull requests

A contributor may create an issue in a public repository without being able to push code there. An external pull request normally requires a fork, a branch with committed and tested changes, and a PR targeting the upstream repository. `gh pr create` is useful, but do not treat successful issue creation as proof of upstream push permission. Retain ordinary project-owner review, verification and merge gates.

## Evidence and scope

An actual example is the [NemoClaw WSL/rootless Podman report #14784](https://github.com/NVIDIA/NemoClaw/issues/14784), published by personal `gh` authentication after a connected GitHub App received HTTP 403. See [ContextCanon #136](https://github.com/SomeSunlight/context-canon/issues/136) for the workflow decision.

This recommendation is **non-mandatory and replaceable**. The broader distinction between binding requirements, optional best practices, and explanatory material is a separate product/design concern tracked in [ContextCanon #121](https://github.com/SomeSunlight/context-canon/issues/121). An optional Topic does not itself implement that future classification system.
