# ContextCanon onboarding placement review

Edit this file directly. **Destination comes first** because future ownership is the primary review decision. Change `Decision`, destination, kind/action, title, or maintained wording where necessary. Evidence and proposal rationale below each item are review support, not a second decision file.

Decisions are `pending`, `accept`, or `reject`. ContextCanon never publishes a pending review.

<!-- contextcanon-placement-review
schema: contextcanon/onboarding-placement-review/v1
evidence_digest: 2a926bf353b252db4039e5c4b63b39abad6bab46c11982e88b3eb17e19cf203d
structure_digest: 7e347d22fe33f251677f85b44e8ce7ba753acd0a06061dbfaf3939665b85aa04
proposal_digest: e6d8122fa93852d0c9d111071693015ef7f18633a58008ca461aa9678403e94a
-->

# Placement findings

## P-001 — Project responsibility
<!-- cc:placement-item id="P-001" authoring-id="ONB-F75FB865470D" -->

Destination: `N-001` — **AI Workstation** (`.`)
Decision: `pending`
Kind: `overview`
Action: `promote`
Review note: -

### Maintained meaning

Text: Reproducible AI workstation for Windows 11, WSL 2 and Ubuntu 24.04.
Wording: `exact`

### Proposal rationale

Stable first-contact orientation belongs at the project root.

Original confidence: `high`

### Evidence

- `README.md` lines 1-3 · `32f00926fa7ea3d2a228424ae6062b61ca58a7f30c965197ee56478d2ebd67b8`
  ```text
      1: # AI Workstation
      2: 
      3: Reproducible AI workstation for Windows 11, WSL 2 and Ubuntu 24.04.
  ```

## P-002 — Current project scope
<!-- cc:placement-item id="P-002" authoring-id="ONB-0CFB8BBE1C25" -->

Destination: `N-001` — **AI Workstation** (`.`)
Decision: `pending`
Kind: `state`
Action: `promote`
Review note: -

### Maintained meaning

Text: Current scope: repeatable Windows/WSL bootstrap, locked Ansible host setup, Docker Engine, isolated Goose CLI sessions using OpenRouter, and a persistent Open WebUI service.
Wording: `lightly-edited`

### Proposal rationale

This is the current implemented scope, not timeless governance and not a reason to preserve README as its only future owner.

Original confidence: `high`

### Evidence

- `README.md` lines 5-8 · `32f00926fa7ea3d2a228424ae6062b61ca58a7f30c965197ee56478d2ebd67b8`
  ```text
      5: > **Current scope:** repeatable Windows/WSL bootstrap, locked Ansible host setup,
      6: > Docker Engine, isolated Goose CLI sessions using OpenRouter, and a persistent
      7: > Open WebUI service. Local model integration is intentionally deferred to the
      8: > next phase.
  ```

## P-003 — Local model integration deferred
<!-- cc:placement-item id="P-003" authoring-id="ONB-295903612F1A" -->

Destination: `N-001` — **AI Workstation** (`.`)
Decision: `pending`
Kind: `plan`
Action: `promote`
Review note: -

### Maintained meaning

Text: Local model integration is intentionally deferred to the next phase.
Wording: `exact`

### Proposal rationale

The frozen Evidence explicitly marks this as later work, while the accepted structure has no dedicated local-model Node; keep the reviewed plan visible at project level.

Original confidence: `high`

### Evidence

- `README.md` lines 5-8 · `32f00926fa7ea3d2a228424ae6062b61ca58a7f30c965197ee56478d2ebd67b8`
  ```text
      5: > **Current scope:** repeatable Windows/WSL bootstrap, locked Ansible host setup,
      6: > Docker Engine, isolated Goose CLI sessions using OpenRouter, and a persistent
      7: > Open WebUI service. Local model integration is intentionally deferred to the
      8: > next phase.
  ```

## P-004 — Repository is the installation specification
<!-- cc:placement-item id="P-004" authoring-id="ONB-9AEAEFEB2000" -->

Destination: `N-001` — **AI Workstation** (`.`)
Decision: `pending`
Kind: `rule`
Action: `promote`
Review note: -

### Maintained meaning

Statement: The repository is the installation specification.
Why: Running containers and manually modified hosts are not treated as the source of truth.
Wording: `exact`

### Proposal rationale

This is a durable project-wide authority rule, not merely descriptive architecture.

Original confidence: `high`

### Evidence

- `docs/architecture.md` lines 12-13 · `359bb341fccb339f30dfd48365dc097b741292520fcdd4fefcd7fb65238bc311`
  ```text
     12: The repository is the installation specification. Running containers and
     13: manually modified hosts are not treated as the source of truth.
  ```

## P-005 — Synchronize version definitions documentation and tests
<!-- cc:placement-item id="P-005" authoring-id="ONB-8AC1F695DA8A" -->

Destination: `N-001` — **AI Workstation** (`.`)
Decision: `pending`
Kind: `rule`
Action: `promote`
Review note: -

### Maintained meaning

Statement: Update `config/versions.json`, documentation and tests together.
Why: Keep project release metadata, documentation and verification synchronized.
Wording: `exact`

### Proposal rationale

This is repository-specific release governance that remains a local delta even when a generic Development Workflow Source is selected by the owner.

Original confidence: `high`

### Evidence

- `CONTRIBUTING.md` lines 7-8 · `ca4cbe961352bb09e2fad6be95881db2210ab194991cdcef7956a832cc224b73`
  ```text
      7: 5. Update `config/versions.json`, documentation and tests together.
      8: 6. Run `./tools/release-check.sh` before committing.
  ```

## P-006 — Run release check before committing
<!-- cc:placement-item id="P-006" authoring-id="ONB-32298340F3E1" -->

Destination: `N-001` — **AI Workstation** (`.`)
Decision: `pending`
Kind: `rule`
Action: `promote`
Review note: -

### Maintained meaning

Statement: Run `./tools/release-check.sh` before committing.
Why: This repository defines release-check as its local pre-commit release validation.
Wording: `exact`

### Proposal rationale

The project names a concrete mandatory validation command that a generic workflow Source should not replace.

Original confidence: `high`

### Evidence

- `CONTRIBUTING.md` lines 7-8 · `ca4cbe961352bb09e2fad6be95881db2210ab194991cdcef7956a832cc224b73`
  ```text
      7: 5. Update `config/versions.json`, documentation and tests together.
      8: 6. Run `./tools/release-check.sh` before committing.
  ```

## P-007 — Bootstrap responsibility
<!-- cc:placement-item id="P-007" authoring-id="ONB-FB52F5DFB5A1" -->

Destination: `N-002` — **Bootstrap** (`bootstrap`)
Decision: `pending`
Kind: `overview`
Action: `promote`
Review note: -

### Maintained meaning

Text: Bootstrap owns the repeatable workstation foundation across Windows/WSL provisioning, Linux bootstrap and Ansible-managed Ubuntu host state.
Wording: `synthesized`

### Proposal rationale

The accepted grouping Node should orient changes spanning Windows, Linux bootstrap and host configuration.

Original confidence: `high`

### Evidence

- `docs/architecture.md` lines 3-10 · `359bb341fccb339f30dfd48365dc097b741292520fcdd4fefcd7fb65238bc311`
  ```text
      3: | Layer | Responsibility |
      4: |---|---|
      5: | PowerShell | Windows, WSL, reboot continuation and distribution lifecycle |
      6: | Linux bootstrap | Minimal packages, uv and the locked Ansible runtime |
      7: | Ansible | Ubuntu host state and Docker Engine |
      8: | Dockerfile | Contents of a service image |
      9: | Compose | Services, mounts, networks and resource limits |
     10: | `aiw` | Stable user interface for installation and operation |
  ```
- `README.md` lines 268-285 · `32f00926fa7ea3d2a228424ae6062b61ca58a7f30c965197ee56478d2ebd67b8`
  ```text
    268: ## Rerun the installer
    269: 
    270: Windows side:
    271: 
    272: ```powershell
    273: .\install.ps1
    274: ```
    275: 
    276: Linux side:
    277: 
    278: ```bash
    279: cd ~/ai-workstation
    280: ./install.sh
    281: ```
    282: 
    283: Both entry points are idempotent and may be run again after an interruption.
    284: Application runtimes are additive and do not change the working host foundation
    285: roles unnecessarily.
  ```

## P-008 — Keep installation entry points thin
<!-- cc:placement-item id="P-008" authoring-id="ONB-B71E5191611C" -->

Destination: `N-002` — **Bootstrap** (`bootstrap`)
Decision: `pending`
Kind: `rule`
Action: `promote`
Review note: -

### Maintained meaning

Statement: Keep installation entry points thin and move implementation into modules.
Why: Preserve the repository's explicit separation between entry points and implementation modules.
Wording: `exact`

### Proposal rationale

This governs both installation entry points and belongs at their shared Bootstrap parent.

Original confidence: `high`

### Evidence

- `CONTRIBUTING.md` lines 3-5 · `ca4cbe961352bb09e2fad6be95881db2210ab194991cdcef7956a832cc224b73`
  ```text
      3: 1. Work inside the WSL Linux filesystem, not under `/mnt/c`.
      4: 2. Keep installation entry points thin and move implementation into modules.
      5: 3. Preserve idempotency: a second run must be safe.
  ```

## P-009 — Preserve idempotent installation
<!-- cc:placement-item id="P-009" authoring-id="ONB-192829393671" -->

Destination: `N-002` — **Bootstrap** (`bootstrap`)
Decision: `pending`
Kind: `rule`
Action: `promote`
Review note: -

### Maintained meaning

Statement: Preserve idempotency: a second run must be safe.
Why: Both installation entry points are intended to be rerun safely after interruption.
Wording: `exact`

### Proposal rationale

Restartability is a durable installer invariant across Windows and Linux.

Original confidence: `high`

### Evidence

- `CONTRIBUTING.md` lines 4-6 · `ca4cbe961352bb09e2fad6be95881db2210ab194991cdcef7956a832cc224b73`
  ```text
      4: 2. Keep installation entry points thin and move implementation into modules.
      5: 3. Preserve idempotency: a second run must be safe.
      6: 4. Never introduce an automatic destructive migration.
  ```
- `README.md` lines 276-285 · `32f00926fa7ea3d2a228424ae6062b61ca58a7f30c965197ee56478d2ebd67b8`
  ```text
    276: Linux side:
    277: 
    278: ```bash
    279: cd ~/ai-workstation
    280: ./install.sh
    281: ```
    282: 
    283: Both entry points are idempotent and may be run again after an interruption.
    284: Application runtimes are additive and do not change the working host foundation
    285: roles unnecessarily.
  ```

## P-010 — Never automate destructive migration
<!-- cc:placement-item id="P-010" authoring-id="ONB-992F09214147" -->

Destination: `N-002` — **Bootstrap** (`bootstrap`)
Decision: `pending`
Kind: `rule`
Action: `promote`
Review note: -

### Maintained meaning

Statement: Never introduce an automatic destructive migration.
Why: Existing distributions and working reference state must not be silently destroyed during installation or testing.
Wording: `exact`

### Proposal rationale

The repository makes non-destructive migration an explicit durable installation boundary.

Original confidence: `high`

### Evidence

- `CONTRIBUTING.md` lines 5-6 · `ca4cbe961352bb09e2fad6be95881db2210ab194991cdcef7956a832cc224b73`
  ```text
      5: 3. Preserve idempotency: a second run must be safe.
      6: 4. Never introduce an automatic destructive migration.
  ```
- `docs/clean-room-test.md` lines 1-20 · `96bb9a79a5fa3205fa0bd1097ced3f9dc5f3bb169a677903d32a2892aaaffa0c`
  ```text
      1: # Clean-room test
      2: 
      3: Keep the working distribution as a reference and create a second distribution
      4: with a separate registered name, filesystem and storage directory. WSL
      5: distributions still share the Windows WSL platform, kernel, global `.wslconfig`
      6: and the overall WSL 2 resource limit. Do not run heavy workloads in both during
      7: the installation test.
      8: 
      9: From an elevated PowerShell 7 terminal in the Windows checkout:
     10: 
     11: ```powershell
     12: .\install.ps1 `
     13:   -DistroName Ubuntu-24.04-Test `
     14:   -InstallLocation C:\WSL\Ubuntu-24.04-Test
     15: ```
     16: 
     17: The installer refuses to overwrite or unregister an existing distribution. It
     18: may update the shared WSL platform and merge the global `.wslconfig`, but it does
     19: not change the reference distribution's Linux filesystem. If custom distribution
     20: names are unsupported, it stops before creating the test distribution.
  ```

## P-011 — Windows and WSL responsibility
<!-- cc:placement-item id="P-011" authoring-id="ONB-FA1EB1920740" -->

Destination: `N-003` — **Windows and WSL bootstrap** (`bootstrap/windows`)
Decision: `pending`
Kind: `overview`
Action: `promote`
Review note: -

### Maintained meaning

Text: Windows and WSL bootstrap owns Windows, WSL, reboot continuation and distribution lifecycle.
Wording: `lightly-edited`

### Proposal rationale

The architecture assigns a clear stable responsibility to the Windows/PowerShell layer.

Original confidence: `high`

### Evidence

- `docs/architecture.md` lines 3-6 · `359bb341fccb339f30dfd48365dc097b741292520fcdd4fefcd7fb65238bc311`
  ```text
      3: | Layer | Responsibility |
      4: |---|---|
      5: | PowerShell | Windows, WSL, reboot continuation and distribution lifecycle |
      6: | Linux bootstrap | Minimal packages, uv and the locked Ansible runtime |
  ```

## P-012 — Linux bootstrap responsibility
<!-- cc:placement-item id="P-012" authoring-id="ONB-B811AC3012EB" -->

Destination: `N-004` — **Linux bootstrap** (`bootstrap/linux`)
Decision: `pending`
Kind: `overview`
Action: `promote`
Review note: -

### Maintained meaning

Text: Linux bootstrap owns minimal packages, uv and the locked Ansible runtime; Ansible manages Ubuntu host state and Docker Engine.
Wording: `lightly-edited`

### Proposal rationale

The accepted owner structure groups the minimal Linux runtime with Ansible-managed host state.

Original confidence: `high`

### Evidence

- `docs/architecture.md` lines 5-8 · `359bb341fccb339f30dfd48365dc097b741292520fcdd4fefcd7fb65238bc311`
  ```text
      5: | PowerShell | Windows, WSL, reboot continuation and distribution lifecycle |
      6: | Linux bootstrap | Minimal packages, uv and the locked Ansible runtime |
      7: | Ansible | Ubuntu host state and Docker Engine |
      8: | Dockerfile | Contents of a service image |
  ```

## P-013 — Develop active Linux tree inside WSL filesystem
<!-- cc:placement-item id="P-013" authoring-id="ONB-5301E1B33420" -->

Destination: `N-004` — **Linux bootstrap** (`bootstrap/linux`)
Decision: `pending`
Kind: `rule`
Action: `promote`
Review note: -

### Maintained meaning

Statement: Work inside the WSL Linux filesystem, not under `/mnt/c`.
Why: Linux permissions and tooling behavior should come from the Linux filesystem rather than synthetic Windows-mounted modes.
Wording: `exact`

### Proposal rationale

This is an explicit development/permission constraint for Linux-side work.

Original confidence: `high`

### Evidence

- `CONTRIBUTING.md` lines 1-4 · `ca4cbe961352bb09e2fad6be95881db2210ab194991cdcef7956a832cc224b73`
  ```text
      1: # Contributing
      2: 
      3: 1. Work inside the WSL Linux filesystem, not under `/mnt/c`.
      4: 2. Keep installation entry points thin and move implementation into modules.
  ```
- `docs/repository-setup.md` lines 8-14 · `1d54e84bfb37512c7fa395f78427a4924cd1702020bddee5d7bddb6095a0becc`
  ```text
      8: Extract the repository seed on Windows, then copy its directory into the WSL
      9: Linux filesystem as `~/ai-workstation-next`. Do not operate the new tree under
     10: `/mnt/c`. Because Windows archive extraction does not preserve Linux modes, run:
     11: 
     12: ```bash
     13: cd ~/ai-workstation-next
     14: bash ./tools/normalize-permissions.sh
  ```

## P-014 — aiw responsibility
<!-- cc:placement-item id="P-014" authoring-id="ONB-E2509705F160" -->

Destination: `N-005` — **aiw operator interface** (`bin`)
Decision: `pending`
Kind: `overview`
Action: `promote`
Review note: -

### Maintained meaning

Text: `aiw` is the stable user interface for installation and operation.
Wording: `lightly-edited`

### Proposal rationale

The architecture names aiw as the stable operator interface.

Original confidence: `high`

### Evidence

- `docs/architecture.md` lines 8-10 · `359bb341fccb339f30dfd48365dc097b741292520fcdd4fefcd7fb65238bc311`
  ```text
      8: | Dockerfile | Contents of a service image |
      9: | Compose | Services, mounts, networks and resource limits |
     10: | `aiw` | Stable user interface for installation and operation |
  ```
- `README.md` lines 35-56 · `32f00926fa7ea3d2a228424ae6062b61ca58a7f30c965197ee56478d2ebd67b8`
  ```text
     35: ## Human-friendly entry point
     36: 
     37: After installation, every new WSL boot shows a short reminder:
     38: 
     39: ```text
     40: AI Workstation ready
     41: 
     42:   aiw              Open the interactive tool menu
     43:   aiw status       Show the complete system status
     44: 
     45: Available tools: Goose, Open WebUI
     46: ```
     47: 
     48: Run one command to discover everything else:
     49: 
     50: ```bash
     51: aiw
     52: ```
     53: 
     54: The interactive menu provides Goose workspace selection, Open WebUI lifecycle
     55: commands, status, update and help. Direct commands remain available for scripts,
     56: documentation and troubleshooting.
  ```

## P-015 — Container runtime responsibility
<!-- cc:placement-item id="P-015" authoring-id="ONB-3A0C4146672B" -->

Destination: `N-006` — **Containerized application runtimes** (`compose`)
Decision: `pending`
Kind: `overview`
Action: `promote`
Review note: -

### Maintained meaning

Text: Containerized application runtimes use Dockerfile for service image contents and Compose for services, mounts, networks and resource limits.
Wording: `lightly-edited`

### Proposal rationale

This parent Node owns runtime concerns shared by Goose and Open WebUI rather than either child alone.

Original confidence: `high`

### Evidence

- `docs/architecture.md` lines 8-10 · `359bb341fccb339f30dfd48365dc097b741292520fcdd4fefcd7fb65238bc311`
  ```text
      8: | Dockerfile | Contents of a service image |
      9: | Compose | Services, mounts, networks and resource limits |
     10: | `aiw` | Stable user interface for installation and operation |
  ```

## P-016 — Keep runtime secrets out of repositories and images
<!-- cc:placement-item id="P-016" authoring-id="ONB-773B7E4334EA" -->

Destination: `N-006` — **Containerized application runtimes** (`compose`)
Decision: `pending`
Kind: `rule`
Action: `promote`
Review note: -

### Maintained meaning

Statement: Secrets must not be committed, copied into images or stored in Compose files.
Why: Runtime credentials belong in the Git-ignored `.env` file with restrictive permissions, outside versioned or image content.
Wording: `exact`

### Proposal rationale

This is a cross-runtime security invariant, not just user instructions.

Original confidence: `high`

### Evidence

- `SECURITY.md` lines 5-10 · `8e49872fd096e6aefdf799b7120f7996d16696b336292b540bc50b643ea0b542`
  ```text
      5: - The Docker daemon is exposed only through its local Unix socket.
      6: - Only the interactive Linux user joins the powerful `docker` group.
      7: - Agent and application containers do not receive the Docker socket.
      8: - Secrets must not be committed, copied into images or stored in Compose files.
      9: - Runtime credentials are read from the Git-ignored `.env` file with mode `600`.
     10: - Existing conflicting container packages are never removed automatically.
  ```
- `README.md` lines 74-92 · `32f00926fa7ea3d2a228424ae6062b61ca58a7f30c965197ee56478d2ebd67b8`
  ```text
     74: ## Configure the shared OpenRouter key
     75: 
     76: Goose and Open WebUI use the same Git-ignored `.env` file:
     77: 
     78: ```bash
     79: cd ~/ai-workstation
     80: aiw goose init
     81: nano .env
     82: ```
     83: 
     84: Set at least:
     85: 
     86: ```dotenv
     87: OPENROUTER_API_KEY=replace-with-your-key
     88: GOOSE_MODEL=provider/model-id
     89: ```
     90: 
     91: The `.env` file is ignored by Git and changed to mode `600` by `aiw`. Do not put
     92: credentials in `.env.example`, Compose files, images or commits.
  ```

## P-017 — Do not give application containers Docker control
<!-- cc:placement-item id="P-017" authoring-id="ONB-46DC44336E1D" -->

Destination: `N-006` — **Containerized application runtimes** (`compose`)
Decision: `pending`
Kind: `rule`
Action: `promote`
Review note: -

### Maintained meaning

Statement: Agent and application containers do not receive the Docker socket.
Why: The Docker socket would grant host-level container control beyond the intended runtime boundary.
Wording: `exact`

### Proposal rationale

The security policy applies this boundary to both agent and application containers.

Original confidence: `high`

### Evidence

- `SECURITY.md` lines 5-9 · `8e49872fd096e6aefdf799b7120f7996d16696b336292b540bc50b643ea0b542`
  ```text
      5: - The Docker daemon is exposed only through its local Unix socket.
      6: - Only the interactive Linux user joins the powerful `docker` group.
      7: - Agent and application containers do not receive the Docker socket.
      8: - Secrets must not be committed, copied into images or stored in Compose files.
      9: - Runtime credentials are read from the Git-ignored `.env` file with mode `600`.
  ```

## P-018 — Goose responsibility
<!-- cc:placement-item id="P-018" authoring-id="ONB-DB440CB9252D" -->

Destination: `N-007` — **Goose** (`compose/goose`)
Decision: `pending`
Kind: `overview`
Action: `promote`
Review note: -

### Maintained meaning

Text: Goose runs short-lived containers with exactly one explicitly registered writable workspace while persistent Goose state and session history remain outside the ephemeral container root.
Wording: `lightly-edited`

### Proposal rationale

Stable Goose architecture is more useful as Node orientation than as duplicated transient state.

Original confidence: `high`

### Evidence

- `README.md` lines 94-105 · `32f00926fa7ea3d2a228424ae6062b61ca58a7f30c965197ee56478d2ebd67b8`
  ```text
     94: ## Goose: explicit isolated workspaces
     95: 
     96: A Goose session never receives the complete WSL home directory. Each session
     97: starts a short-lived container and mounts exactly one registered workspace
     98: read-write. The container is removed when the session ends; Goose state and
     99: session history remain in the persistent `goose-home` volume.
    100: 
    101: The repository is registered automatically as the first workspace:
    102: 
    103: ```text
    104: ai-workstation -> /home/moresunlight/ai-workstation
    105: ```
  ```
- `SECURITY.md` lines 12-26 · `8e49872fd096e6aefdf799b7120f7996d16696b336292b540bc50b643ea0b542`
  ```text
     12: ## Goose workspace boundary
     13: 
     14: Each Goose session starts a short-lived container with:
     15: 
     16: - exactly one explicitly registered host workspace mounted read-write;
     17: - a stable container path under `/workspaces/NAME`;
     18: - a read-only root filesystem;
     19: - dropped Linux capabilities and `no-new-privileges`;
     20: - no access to unrelated WSL or Windows directories unless they are deliberately
     21:   registered as the selected workspace.
     22: 
     23: The selected workspace is delegated authority. Goose can edit or delete files
     24: inside it and can modify its Git repository. Review changes before committing or
     25: pushing them. Broad workspace paths such as `/`, `/home`, `$HOME`, `/mnt` and
     26: `/mnt/c` are rejected by the wrapper.
  ```

## P-019 — Constrain Goose to the selected workspace
<!-- cc:placement-item id="P-019" authoring-id="ONB-42C7095EBC59" -->

Destination: `N-007` — **Goose** (`compose/goose`)
Decision: `pending`
Kind: `rule`
Action: `promote`
Review note: -

### Maintained meaning

Statement: Each Goose session receives exactly one explicitly registered host workspace mounted read-write and no unrelated WSL or Windows directories unless deliberately selected.
Why: The selected workspace is delegated authority; broad host paths and unrelated data remain outside the agent boundary.
Wording: `lightly-edited`

### Proposal rationale

This is the defining least-privilege boundary for the agent runtime.

Original confidence: `high`

### Evidence

- `SECURITY.md` lines 12-26 · `8e49872fd096e6aefdf799b7120f7996d16696b336292b540bc50b643ea0b542`
  ```text
     12: ## Goose workspace boundary
     13: 
     14: Each Goose session starts a short-lived container with:
     15: 
     16: - exactly one explicitly registered host workspace mounted read-write;
     17: - a stable container path under `/workspaces/NAME`;
     18: - a read-only root filesystem;
     19: - dropped Linux capabilities and `no-new-privileges`;
     20: - no access to unrelated WSL or Windows directories unless they are deliberately
     21:   registered as the selected workspace.
     22: 
     23: The selected workspace is delegated authority. Goose can edit or delete files
     24: inside it and can modify its Git repository. Review changes before committing or
     25: pushing them. Broad workspace paths such as `/`, `/home`, `$HOME`, `/mnt` and
     26: `/mnt/c` are rejected by the wrapper.
  ```

## P-020 — Open WebUI responsibility
<!-- cc:placement-item id="P-020" authoring-id="ONB-D3B631788199" -->

Destination: `N-008` — **Open WebUI** (`compose/open-webui`)
Decision: `pending`
Kind: `overview`
Action: `promote`
Review note: -

### Maintained meaning

Text: Open WebUI is a persistent Docker service bound to localhost, with application state in a named Docker volume and no host workspace or Docker socket.
Wording: `lightly-edited`

### Proposal rationale

The service has a stable lifecycle, storage and local-network identity distinct from Goose.

Original confidence: `high`

### Evidence

- `README.md` lines 142-184 · `32f00926fa7ea3d2a228424ae6062b61ca58a7f30c965197ee56478d2ebd67b8`
  ```text
    142: ## Open WebUI
    143: 
    144: Open WebUI runs as a persistent Docker service. No Linux desktop GUI is needed:
    145: the Windows browser connects to the service through WSL localhost forwarding.
    146: The default address is:
    147: 
    148: ```text
    149: http://localhost:3000
    150: ```
    151: 
    152: Start it through the interactive menu:
    153: 
    154: ```bash
    155: aiw
    156: ```
    157: 
    158: Choose:
    159: 
    160: ```text
    161: Open WebUI -> Start and open in Windows browser
    162: ```
    163: 
    164: Or use direct commands:
    165: 
    166: ```bash
    167: aiw open-webui init
    168: aiw open-webui pull
    169: aiw open-webui up
    170: aiw open-webui open
    171: aiw open-webui status
    172: aiw open-webui logs
    173: aiw open-webui restart
    174: aiw open-webui down
    175: ```
    176: 
    177: The service:
    178: 
    179: - uses the pinned official Open WebUI image;
    180: - binds only to `127.0.0.1` on the WSL host;
    181: - persists accounts, chats, settings and knowledge data in a named Docker volume;
    182: - connects to OpenRouter through the shared API key;
    183: - disables the unused Ollama connection for this phase;
    184: - does not receive the Docker socket or a host workspace.
  ```
- `SECURITY.md` lines 28-40 · `8e49872fd096e6aefdf799b7120f7996d16696b336292b540bc50b643ea0b542`
  ```text
     28: ## Open WebUI boundary
     29: 
     30: Open WebUI:
     31: 
     32: - binds only to `127.0.0.1` on the WSL host by default;
     33: - stores state in a named Docker volume;
     34: - receives no host workspace and no Docker socket;
     35: - reaches configured model providers over the network;
     36: - keeps authentication enabled.
     37: 
     38: The first account is the local administrator. Use a strong password and do not
     39: publish the localhost port through a proxy or LAN interface without adding the
     40: appropriate TLS, authentication and network controls.
  ```

## P-021 — Keep Open WebUI local and authenticated by default
<!-- cc:placement-item id="P-021" authoring-id="ONB-D0C135E42AEB" -->

Destination: `N-008` — **Open WebUI** (`compose/open-webui`)
Decision: `pending`
Kind: `rule`
Action: `promote`
Review note: -

### Maintained meaning

Statement: Keep Open WebUI bound to `127.0.0.1` with authentication enabled unless equivalent TLS, authentication and network controls are deliberately added for broader exposure.
Why: The documented default boundary assumes local access and warns against publishing the service without compensating controls.
Wording: `lightly-edited`

### Proposal rationale

This is durable service-specific security governance.

Original confidence: `high`

### Evidence

- `SECURITY.md` lines 28-40 · `8e49872fd096e6aefdf799b7120f7996d16696b336292b540bc50b643ea0b542`
  ```text
     28: ## Open WebUI boundary
     29: 
     30: Open WebUI:
     31: 
     32: - binds only to `127.0.0.1` on the WSL host by default;
     33: - stores state in a named Docker volume;
     34: - receives no host workspace and no Docker socket;
     35: - reaches configured model providers over the network;
     36: - keeps authentication enabled.
     37: 
     38: The first account is the local administrator. Use a strong password and do not
     39: publish the localhost port through a proxy or LAN interface without adding the
     40: appropriate TLS, authentication and network controls.
  ```

## P-022 — Architecture reference
<!-- cc:placement-item id="P-022" authoring-id="ONB-8C43D2E1046E" -->

Destination: `N-001` — **AI Workstation** (`.`)
Decision: `pending`
Kind: `topic-resource`
Action: `reference`
Review note: -

### Maintained meaning

Condition: When changing layer responsibilities, installation authority, or cross-layer architecture, consult the architecture document.
Resources: `docs/architecture.md`

### Proposal rationale

The architecture document remains a natural maintained source for layer responsibilities and installation authority.

Original confidence: `high`

### Evidence

- `docs/architecture.md` lines 1-13 · `359bb341fccb339f30dfd48365dc097b741292520fcdd4fefcd7fb65238bc311`
  ```text
      1: # Architecture
      2: 
      3: | Layer | Responsibility |
      4: |---|---|
      5: | PowerShell | Windows, WSL, reboot continuation and distribution lifecycle |
      6: | Linux bootstrap | Minimal packages, uv and the locked Ansible runtime |
      7: | Ansible | Ubuntu host state and Docker Engine |
      8: | Dockerfile | Contents of a service image |
      9: | Compose | Services, mounts, networks and resource limits |
     10: | `aiw` | Stable user interface for installation and operation |
     11: 
     12: The repository is the installation specification. Running containers and
     13: manually modified hosts are not treated as the source of truth.
  ```

## P-023 — CI validation reference
<!-- cc:placement-item id="P-023" authoring-id="ONB-D348DAB3B477" -->

Destination: `N-001` — **AI Workstation** (`.`)
Decision: `pending`
Kind: `topic-resource`
Action: `reference`
Review note: -

### Maintained meaning

Condition: When changing validation, dependencies, smoke checks, Ansible linting or playbook syntax checks, inspect the validation workflow.
Resources: `.github/workflows/validate.yml`

### Proposal rationale

Executable CI is the natural source for the exact current validation pipeline.

Original confidence: `high`

### Evidence

- `.github/workflows/validate.yml` lines 17-61 · `441c086b51bb2fe56877df3529d80a3d1f8dabdde677602ad87fc1b6d171ddcd`
  ```text
     17:       - name: Set up Python
     18:         uses: actions/setup-python@v6
     19:         with:
     20:           python-version-file: .python-version
     21: 
     22:       - name: Set up pinned uv
     23:         uses: astral-sh/setup-uv@08807647e7069bb48b6ef5acd8ec9567f424441b # v8.1.0
     24:         with:
     25:           version: "0.11.26"
     26:       - name: Verify repository files
     27:         run: |
     28:           test -f uv.lock
     29:           bash -n install.sh bootstrap/linux/install.sh bin/aiw tools/*.sh tests/smoke/*.sh
     30:           python -m json.tool config/versions.json >/dev/null
     31:           python tools/check-version-consistency.py
     32:           bash tests/smoke/repository-layout.sh
     33:           bash tests/smoke/goose-runtime.sh
     34:           bash tests/smoke/open-webui-runtime.sh
     35:           bash tests/smoke/interactive-menu.sh
     36: 
     37:       - name: Synchronize locked environment
     38:         run: uv sync --frozen
     39:       - name: Install Ansible collection
     40:         run: |
     41:           mkdir -p .ansible/collections
     42:           ANSIBLE_CONFIG="$PWD/ansible/ansible.cfg" \
     43:             uv run --frozen ansible-galaxy collection install \
     44:               --requirements-file ansible/requirements.yml \
     45:               --collections-path .ansible/collections
     46:       - name: Lint Ansible
     47:         env:
     48:           ANSIBLE_CONFIG: ${{ github.workspace }}/ansible/ansible.cfg
     49:           ANSIBLE_INVENTORY: ${{ github.workspace }}/ansible/inventory/localhost.yml
     50:           ANSIBLE_ROLES_PATH: ${{ github.workspace }}/ansible/roles
     51:           ANSIBLE_COLLECTIONS_PATH: ${{ github.workspace }}/.ansible/collections
     52:         run: uv run --frozen ansible-lint --config-file ansible/.ansible-lint ansible/playbooks
     53:       - name: Check playbook syntax
     54:         env:
     55:           ANSIBLE_CONFIG: ${{ github.workspace }}/ansible/ansible.cfg
     56:           ANSIBLE_INVENTORY: ${{ github.workspace }}/ansible/inventory/localhost.yml
     57:           ANSIBLE_ROLES_PATH: ${{ github.workspace }}/ansible/roles
     58:           ANSIBLE_COLLECTIONS_PATH: ${{ github.workspace }}/.ansible/collections
     59:         run: |
     60:           uv run --frozen ansible-playbook ansible/playbooks/workstation.yml --syntax-check
     61:           uv run --frozen ansible-playbook ansible/playbooks/verify.yml --syntax-check
  ```

## P-024 — Bootstrap recovery reference
<!-- cc:placement-item id="P-024" authoring-id="ONB-8B98F94581BF" -->

Destination: `N-002` — **Bootstrap** (`bootstrap`)
Decision: `pending`
Kind: `topic-resource`
Action: `reference`
Review note: -

### Maintained meaning

Condition: When testing installation isolation, reinstalling safely, or diagnosing WSL, shortcut, permission, Docker, elevation or bootstrap failures, use the recovery documentation.
Resources: `docs/clean-room-test.md`, `docs/troubleshooting.md`

### Proposal rationale

Clean-room and troubleshooting procedures are deep task material, not broad Rules.

Original confidence: `high`

### Evidence

- `docs/clean-room-test.md` lines 1-20 · `96bb9a79a5fa3205fa0bd1097ced3f9dc5f3bb169a677903d32a2892aaaffa0c`
  ```text
      1: # Clean-room test
      2: 
      3: Keep the working distribution as a reference and create a second distribution
      4: with a separate registered name, filesystem and storage directory. WSL
      5: distributions still share the Windows WSL platform, kernel, global `.wslconfig`
      6: and the overall WSL 2 resource limit. Do not run heavy workloads in both during
      7: the installation test.
      8: 
      9: From an elevated PowerShell 7 terminal in the Windows checkout:
     10: 
     11: ```powershell
     12: .\install.ps1 `
     13:   -DistroName Ubuntu-24.04-Test `
     14:   -InstallLocation C:\WSL\Ubuntu-24.04-Test
     15: ```
     16: 
     17: The installer refuses to overwrite or unregister an existing distribution. It
     18: may update the shared WSL platform and merge the global `.wslconfig`, but it does
     19: not change the reference distribution's Linux filesystem. If custom distribution
     20: names are unsupported, it stops before creating the test distribution.
  ```
- `docs/clean-room-test.md` lines 41-58 · `96bb9a79a5fa3205fa0bd1097ced3f9dc5f3bb169a677903d32a2892aaaffa0c`
  ```text
     41: ## Reinstall test inside an existing distribution
     42: 
     43: To test the repository clone and Linux installer again without deleting the WSL
     44: distribution, delete only the Linux checkouts:
     45: 
     46: ```bash
     47: cd ~
     48: rm -rf ai-workstation ai-workstation-next
     49: ```
     50: 
     51: Then rerun the Windows installer from the Windows checkout:
     52: 
     53: ```powershell
     54: .\install.ps1
     55: ```
     56: 
     57: The installer clones the public repository into `/home/moresunlight/ai-workstation`
     58: and recreates the Windows shortcuts.
  ```
- `docs/troubleshooting.md` lines 1-145 · `025b723d0680d83f67d42bea2c49d50306153ffd3dad6f8ac760ed6123778cc8`
  ```text
      1: # Troubleshooting
      2: 
      3: ## Logs
      4: 
      5: Windows logs:
      6: 
      7: ```text
      8: %LOCALAPPDATA%\AiWorkstationBootstrap\logs
      9: ```
     10: 
     11: Linux logs:
     12: 
     13: ```text
     14: ~/.local/state/ai-workstation/logs
     15: ```
     16: 
     17: ## I cannot find Linux in Windows
     18: 
     19: Do not search for `Linux` or `Debian`. The installed distribution is managed by
     20: WSL.
     21: 
     22: Normal access after installation:
     23: 
     24: ```text
     25: Start Menu -> AI Workstation
     26: ```
     27: 
     28: Fallback in PowerShell:
     29: 
     30: ```powershell
     31: wsl -l -v
     32: wsl -d Ubuntu-24.04
     33: ```
     34: 
     35: The project lives inside Linux:
     36: 
     37: ```text
     38: /home/moresunlight/ai-workstation
     39: ```
     40: 
     41: ## The AI Workstation shortcut is missing
     42: 
     43: Rerun the Windows installer:
     44: 
     45: ```powershell
     46: .\install.ps1
     47: ```
     48: 
     49: It recreates the Desktop and Start Menu shortcuts. To create only the shortcuts
     50: from a checkout:
     51: 
     52: ```powershell
     53: .\bootstrap\windows\Create-Shortcuts.ps1
     54: ```
     55: 
     56: For a test distribution:
     57: 
     58: ```powershell
     59: .\bootstrap\windows\Create-Shortcuts.ps1 `
     60:   -DistroName Ubuntu-24.04-Test
     61: ```
     62: 
     63: ## `ansible.cfg` is ignored
     64: 
     65: The repository must not be world-writable. Run:
     66: 
     67: ```bash
     68: ./tools/normalize-permissions.sh
     69: ```
     70: 
     71: Normal installations clone the repository directly inside Linux and therefore
     72: do not inherit synthetic Windows permissions.
     73: 
     74: ## Docker works only with sudo
     75: 
     76: Open a new WSL session after the first installation. The `docker` group
     77: membership is applied to new login sessions.
     78: 
     79: From PowerShell this fully restarts WSL:
     80: 
     81: ```powershell
     82: wsl --shutdown
     83: ```
     84: 
     85: Then open the `AI Workstation` shortcut again.
     86: 
     87: ## GitHub CLI login from WSL has no browser
     88: 
     89: Use the device-code flow printed by `gh auth login`. Open the shown URL in the
     90: normal Windows browser, enter the code, then return to the WSL terminal.
     91: 
     92: ## The GitHub repository already has a generated LICENSE
     93: 
     94: If the GitHub repository was created with a server-side MIT license, merge the
     95: remote history instead of force-pushing:
     96: 
     97: ```bash
     98: git fetch origin
     99: git merge origin/main --allow-unrelated-histories
    100: ```
    101: 
    102: If `LICENSE` conflicts, resolve the conflict, commit the merge and push.
    103: 
    104: 
    105: ## The installer returns to the prompt immediately
    106: 
    107: When administrator rights are required, `install.ps1` starts a separate
    108: elevated PowerShell window. Continue watching that elevated window. The original
    109: PowerShell session can return to the prompt while the elevated installer is
    110: still running.
    111: 
    112: To inspect the current state later:
    113: 
    114: ```powershell
    115: .\install.ps1 -Action Status
    116: ```
    117: 
    118: Windows logs are written below:
    119: 
    120: ```text
    121: %LOCALAPPDATA%\AiWorkstationBootstrap\logs
    122: ```
    123: 
    124: ## WSL update check looks idle
    125: 
    126: The command `wsl --update` can take several minutes and may produce little or no
    127: output. The installer now announces this explicitly and prints a completion
    128: message when the check returns.
    129: 
    130: 
    131: ## Which actions need administrator rights?
    132: 
    133: `Install` may need administrator rights and therefore opens a UAC prompt when
    134: started from a normal PowerShell window. This is expected.
    135: 
    136: For ordinary inspection, use these commands without opening an administrator
    137: shell:
    138: 
    139: ```powershell
    140: .\install.ps1 -Action Status
    141: .\install.ps1 -Action Verify
    142: ```
    143: 
    144: If `Install` elevates itself, the original PowerShell session may return to the
    145: prompt while a separate elevated window continues the installation.
  ```

## P-025 — aiw operator guide
<!-- cc:placement-item id="P-025" authoring-id="ONB-CCBB9C8D55F4" -->

Destination: `N-005` — **aiw operator interface** (`bin`)
Decision: `pending`
Kind: `topic-resource`
Action: `reference`
Review note: -

### Maintained meaning

Condition: When operating AI Workstation through `aiw`, discovering commands, checking status or updating the installation, use the operator guide in README.
Resources: `README.md`

### Proposal rationale

README remains the maintained first-contact operator guide; the Node should route to it rather than reproduce all commands.

Original confidence: `high`

### Evidence

- `README.md` lines 35-72 · `32f00926fa7ea3d2a228424ae6062b61ca58a7f30c965197ee56478d2ebd67b8`
  ```text
     35: ## Human-friendly entry point
     36: 
     37: After installation, every new WSL boot shows a short reminder:
     38: 
     39: ```text
     40: AI Workstation ready
     41: 
     42:   aiw              Open the interactive tool menu
     43:   aiw status       Show the complete system status
     44: 
     45: Available tools: Goose, Open WebUI
     46: ```
     47: 
     48: Run one command to discover everything else:
     49: 
     50: ```bash
     51: aiw
     52: ```
     53: 
     54: The interactive menu provides Goose workspace selection, Open WebUI lifecycle
     55: commands, status, update and help. Direct commands remain available for scripts,
     56: documentation and troubleshooting.
     57: 
     58: ## Check the current installation state
     59: 
     60: `Status` and `Verify` do not require an elevated PowerShell window for ordinary
     61: use:
     62: 
     63: ```powershell
     64: .\install.ps1 -Action Status
     65: .\install.ps1 -Action Verify
     66: ```
     67: 
     68: Inside Ubuntu:
     69: 
     70: ```bash
     71: aiw status
     72: ```
  ```
- `README.md` lines 259-285 · `32f00926fa7ea3d2a228424ae6062b61ca58a7f30c965197ee56478d2ebd67b8`
  ```text
    259: ## Daily foundation commands
    260: 
    261: ```bash
    262: aiw
    263: aiw status
    264: aiw verify
    265: aiw update
    266: ```
    267: 
    268: ## Rerun the installer
    269: 
    270: Windows side:
    271: 
    272: ```powershell
    273: .\install.ps1
    274: ```
    275: 
    276: Linux side:
    277: 
    278: ```bash
    279: cd ~/ai-workstation
    280: ./install.sh
    281: ```
    282: 
    283: Both entry points are idempotent and may be run again after an interruption.
    284: Application runtimes are additive and do not change the working host foundation
    285: roles unnecessarily.
  ```

## P-026 — Goose operator guide
<!-- cc:placement-item id="P-026" authoring-id="ONB-02A6330F07FB" -->

Destination: `N-007` — **Goose** (`compose/goose`)
Decision: `pending`
Kind: `topic-resource`
Action: `reference`
Review note: -

### Maintained meaning

Condition: When registering Goose workspaces, starting/resuming sessions, running prompts or inspecting Goose runtime commands, use the Goose section of README.
Resources: `README.md`

### Proposal rationale

README already owns detailed Goose workspace/session commands.

Original confidence: `high`

### Evidence

- `README.md` lines 94-139 · `32f00926fa7ea3d2a228424ae6062b61ca58a7f30c965197ee56478d2ebd67b8`
  ```text
     94: ## Goose: explicit isolated workspaces
     95: 
     96: A Goose session never receives the complete WSL home directory. Each session
     97: starts a short-lived container and mounts exactly one registered workspace
     98: read-write. The container is removed when the session ends; Goose state and
     99: session history remain in the persistent `goose-home` volume.
    100: 
    101: The repository is registered automatically as the first workspace:
    102: 
    103: ```text
    104: ai-workstation -> /home/moresunlight/ai-workstation
    105: ```
    106: 
    107: Manage additional workspaces through the menu or direct commands:
    108: 
    109: ```bash
    110: aiw goose workspace add confluence-dump ~/projects/confluenceDumpWithPython
    111: aiw goose workspace list
    112: aiw goose workspace remove confluence-dump
    113: ```
    114: 
    115: Start Goose through the interactive chooser:
    116: 
    117: ```bash
    118: aiw
    119: ```
    120: 
    121: Or directly:
    122: 
    123: ```bash
    124: aiw goose session ai-workstation
    125: aiw goose session ai-workstation --resume
    126: aiw goose run ai-workstation --text "Inspect this repository and summarize its architecture."
    127: ```
    128: 
    129: Before every interactive session, `aiw` prints the selected host path, the
    130: container path, the access boundary and the most useful Goose slash commands.
    131: 
    132: Other Goose commands:
    133: 
    134: ```bash
    135: aiw goose init
    136: aiw goose status
    137: aiw goose pull
    138: aiw goose version
    139: aiw goose help
  ```

## P-027 — Open WebUI operator guide
<!-- cc:placement-item id="P-027" authoring-id="ONB-B21B9AC7FD23" -->

Destination: `N-008` — **Open WebUI** (`compose/open-webui`)
Decision: `pending`
Kind: `topic-resource`
Action: `reference`
Review note: -

### Maintained meaning

Condition: When starting, stopping, opening, configuring or diagnosing Open WebUI, use the Open WebUI section of README.
Resources: `README.md`

### Proposal rationale

README already owns detailed Open WebUI lifecycle and first-use commands.

Original confidence: `high`

### Evidence

- `README.md` lines 142-194 · `32f00926fa7ea3d2a228424ae6062b61ca58a7f30c965197ee56478d2ebd67b8`
  ```text
    142: ## Open WebUI
    143: 
    144: Open WebUI runs as a persistent Docker service. No Linux desktop GUI is needed:
    145: the Windows browser connects to the service through WSL localhost forwarding.
    146: The default address is:
    147: 
    148: ```text
    149: http://localhost:3000
    150: ```
    151: 
    152: Start it through the interactive menu:
    153: 
    154: ```bash
    155: aiw
    156: ```
    157: 
    158: Choose:
    159: 
    160: ```text
    161: Open WebUI -> Start and open in Windows browser
    162: ```
    163: 
    164: Or use direct commands:
    165: 
    166: ```bash
    167: aiw open-webui init
    168: aiw open-webui pull
    169: aiw open-webui up
    170: aiw open-webui open
    171: aiw open-webui status
    172: aiw open-webui logs
    173: aiw open-webui restart
    174: aiw open-webui down
    175: ```
    176: 
    177: The service:
    178: 
    179: - uses the pinned official Open WebUI image;
    180: - binds only to `127.0.0.1` on the WSL host;
    181: - persists accounts, chats, settings and knowledge data in a named Docker volume;
    182: - connects to OpenRouter through the shared API key;
    183: - disables the unused Ollama connection for this phase;
    184: - does not receive the Docker socket or a host workspace.
    185: 
    186: On the first browser visit, create the initial account. The first account becomes
    187: the administrator. Configure later provider details and model visibility in the
    188: Open WebUI Admin Panel; settings stored there can override environment defaults.
    189: 
    190: Stopping the service keeps all Open WebUI data:
    191: 
    192: ```bash
    193: aiw open-webui down
    194: ```
  ```

## P-028 — Runtime security reference
<!-- cc:placement-item id="P-028" authoring-id="ONB-FC910063F7C2" -->

Destination: `N-006` — **Containerized application runtimes** (`compose`)
Decision: `pending`
Kind: `topic-resource`
Action: `reference`
Review note: -

### Maintained meaning

Condition: When changing container privileges, Docker exposure, workspace delegation, secret handling, Open WebUI exposure or vulnerability reporting, consult SECURITY.md.
Resources: `SECURITY.md`

### Proposal rationale

SECURITY.md remains mutable project-owned detailed security guidance; routing is preferable to copying the entire policy into Rules.

Original confidence: `high`

### Evidence

- `SECURITY.md` lines 1-46 · `8e49872fd096e6aefdf799b7120f7996d16696b336292b540bc50b643ea0b542`
  ```text
      1: # Security
      2: 
      3: ## Design principles
      4: 
      5: - The Docker daemon is exposed only through its local Unix socket.
      6: - Only the interactive Linux user joins the powerful `docker` group.
      7: - Agent and application containers do not receive the Docker socket.
      8: - Secrets must not be committed, copied into images or stored in Compose files.
      9: - Runtime credentials are read from the Git-ignored `.env` file with mode `600`.
     10: - Existing conflicting container packages are never removed automatically.
     11: 
     12: ## Goose workspace boundary
     13: 
     14: Each Goose session starts a short-lived container with:
     15: 
     16: - exactly one explicitly registered host workspace mounted read-write;
     17: - a stable container path under `/workspaces/NAME`;
     18: - a read-only root filesystem;
     19: - dropped Linux capabilities and `no-new-privileges`;
     20: - no access to unrelated WSL or Windows directories unless they are deliberately
     21:   registered as the selected workspace.
     22: 
     23: The selected workspace is delegated authority. Goose can edit or delete files
     24: inside it and can modify its Git repository. Review changes before committing or
     25: pushing them. Broad workspace paths such as `/`, `/home`, `$HOME`, `/mnt` and
     26: `/mnt/c` are rejected by the wrapper.
     27: 
     28: ## Open WebUI boundary
     29: 
     30: Open WebUI:
     31: 
     32: - binds only to `127.0.0.1` on the WSL host by default;
     33: - stores state in a named Docker volume;
     34: - receives no host workspace and no Docker socket;
     35: - reaches configured model providers over the network;
     36: - keeps authentication enabled.
     37: 
     38: The first account is the local administrator. Use a strong password and do not
     39: publish the localhost port through a proxy or LAN interface without adding the
     40: appropriate TLS, authentication and network controls.
     41: 
     42: ## Reporting
     43: 
     44: Do not open a public issue for a vulnerability that includes credentials,
     45: private host data or an exploitable proof of concept. Contact the repository
     46: owner privately first.
  ```

## P-029 — Repository creation record
<!-- cc:placement-item id="P-029" authoring-id="ONB-92326F6CED10" -->

Destination: none / outside Node authoring
Decision: `pending`
Kind: `ordinary-documentation`
Action: `keep`
Review note: -

### Maintained meaning

Documents: `docs/repository-setup.md`
Reason: Keep as historical/special-purpose repository-creation documentation rather than canonical current Node semantics.

### Proposal rationale

This document explicitly says it is only for creating the public repository from the tested prototype, not normal operation.

Original confidence: `high`

### Evidence

- `docs/repository-setup.md` lines 1-10 · `1d54e84bfb37512c7fa395f78427a4924cd1702020bddee5d7bddb6095a0becc`
  ```text
      1: # Repository setup
      2: 
      3: This document is only for creating the public repository from the tested
      4: prototype. Normal users start with the root `README.md`.
      5: 
      6: ## 1. Prepare the new tree
      7: 
      8: Extract the repository seed on Windows, then copy its directory into the WSL
      9: Linux filesystem as `~/ai-workstation-next`. Do not operate the new tree under
     10: `/mnt/c`. Because Windows archive extraction does not preserve Linux modes, run:
  ```
- `docs/repository-setup.md` lines 31-78 · `1d54e84bfb37512c7fa395f78427a4924cd1702020bddee5d7bddb6095a0becc`
  ```text
     31: 
     32: ## 3. Validate the repository
     33: 
     34: ```bash
     35: ./tools/release-check.sh
     36: ```
     37: 
     38: ## 4. Create the Git history
     39: 
     40: ```bash
     41: git init -b main
     42: git add .
     43: git commit -m "Initial AI Workstation repository"
     44: ```
     45: 
     46: Create an empty **public** GitHub repository named `ai-workstation`. Prefer no
     47: server-generated README, license or `.gitignore` because the repository already
     48: contains them. If a server-generated MIT license was created, merge the remote
     49: history later instead of force-pushing.
     50: 
     51: Then connect and push:
     52: 
     53: ```bash
     54: git remote add origin https://github.com/SomeSunlight/ai-workstation.git
     55: git push -u origin main
     56: ```
     57: 
     58: After the push, the GitHub validation workflow must pass before starting the
     59: clean-room installation.
     60: 
     61: 
     62: ## Existing server-side LICENSE
     63: 
     64: If GitHub already created a first commit containing `LICENSE`, the first push may
     65: be rejected. Merge both histories:
     66: 
     67: ```bash
     68: git fetch origin
     69: git merge origin/main --allow-unrelated-histories
     70: ```
     71: 
     72: Resolve `LICENSE` if necessary, keep the intended MIT text, then push.
     73: 
     74: ## `gh auth login` from WSL
     75: 
     76: WSL may not have a browser. That is fine: `gh auth login` prints a URL and a
     77: one-time device code. Open the URL in the Windows browser, enter the code and
     78: return to the WSL terminal.
  ```

## P-030 — Release history
<!-- cc:placement-item id="P-030" authoring-id="ONB-D1B148C1C6B3" -->

Destination: none / outside Node authoring
Decision: `pending`
Kind: `ordinary-documentation`
Action: `keep`
Review note: -

### Maintained meaning

Documents: `CHANGELOG.md`
Reason: Keep as chronological release history.

### Proposal rationale

The changelog is chronological history; current semantics may cite it as corroboration but should not duplicate it as current Context.

Original confidence: `high`

### Evidence

- `CHANGELOG.md` lines 1-89 · `2a6941b47ab2a411f599203c6f9487430ae2f553ca6e381012945ad7ce9bdb54`
  ```text
      1: # Changelog
      2: ## 0.6.2
      3: - Route Windows shortcuts through generated `cmd.exe /k` launchers so WSL errors remain visible.
      4: - Create a second `AI Workstation Terminal` shortcut that opens the Linux home directory.
      5: - Document direct WSL fallback commands and the `wsl --shutdown` recovery path.
      6: 
      7: 
      8: ## 0.6.0
      9: 
     10: - Make `aiw` without arguments open an interactive, discoverable tool menu.
     11: - Show a concise AI Workstation reminder once per WSL boot.
     12: - Replace the persistent Goose utility container with short-lived containers that mount exactly one registered workspace.
     13: - Add interactive Goose workspace registration, selection and quick command help.
     14: - Add pinned Open WebUI `v0.11.0` with persistent data, OpenRouter defaults and a localhost-only browser port.
     15: - Add `aiw open-webui` lifecycle, status, log and Windows-browser commands.
     16: - Add smoke tests for menus, workspace isolation and Open WebUI layout.
     17: 
     18: ## 0.5.1
     19: 
     20: - Resolve the real `bin/aiw` path before deriving the repository root, so the installed `~/.local/bin/aiw` symlink works correctly.
     21: - Validate Git worktrees with `git rev-parse` instead of requiring `.git` to be a directory.
     22: - Add a smoke test for invoking `aiw` through its installed symlink.
     23: - Document that `aiw update`, not Ansible, performs the Linux-side Git pull.
     24: 
     25: ## 0.5.0
     26: 
     27: - Add a pinned Docker Compose runtime for Goose `v1.44.0` with OpenRouter configuration from a Git-ignored `.env` file.
     28: - Add `aiw goose init`, `status`, `pull`, `up`, `down`, `logs`, `session`, `run` and `version` commands.
     29: - Persist Goose configuration, sessions, state and cache while keeping the container root filesystem read-only.
     30: - Run Goose without the Docker socket, Linux capabilities or privilege escalation.
     31: - Document first use, daily operation and recovery after a long pause.
     32: - Add runtime smoke checks to CI without changing the working host foundation.
     33: 
     34: ## 0.4.9
     35: 
     36: - Remove duplicated Windows-side Ubuntu release parsing from `Verify`.
     37: - Let the Linux verifier be the single source of truth for Ubuntu, systemd, Python, uv, Ansible and Docker checks.
     38: - Harden the Windows default-user check against null/scalar native WSL output.
     39: ## 0.4.8
     40: 
     41: - Fix `install.ps1 -Action Verify` when native WSL output is empty or scalar by normalizing command output before calling `.Trim()`.
     42: - Add clearer errors when Windows cannot read the Ubuntu release or default Linux user from WSL.
     43: ## 0.4.7
     44: 
     45: - Prompt once for the Linux sudo password during `install.sh install` and pass it to Ansible through a temporary become-password file.
     46: - Keep sudo alive using the same temporary credential path.
     47: - Allow the Windows installer to drive the Linux host installation without Ansible failing on missing sudo input.
     48: 
     49: ## 0.4.6
     50: 
     51: - Fix ansible-lint variable naming violations in the `project_directories` role.
     52: - Replace deprecated injected Ansible fact usage in `bootstrap-verify.yml`.
     53: ## 0.4.5
     54: 
     55: - Normalize PowerShell here-string line endings before sending Bash snippets to WSL.
     56: - Replace `echo` with `printf` for base64 payload transfer into WSL.
     57: 
     58: ## 0.4.4
     59: 
     60: - Fix Windows installer path normalization for existing WSL distributions by replacing an invalid regular expression with explicit `StartsWith` / `Substring` logic.
     61: ## 0.4.3
     62: 
     63: - Fix `install.ps1 -Action Status` when WSL returns a single distribution name.
     64: - Make Windows administrator/elevation behavior explicit in README and troubleshooting.
     65: - Clarify that `Status` and `Verify` do not normally require an elevated shell.
     66: ## 0.4.2
     67: 
     68: - Keep the elevated Windows installer window open so progress and errors remain visible.
     69: - Make the WSL update check explicitly visible as a potentially long-running step.
     70: - Add a final Windows status hint after successful installation.
     71: - Fix Ansible lint failures by using role-prefixed variables and moving the Docker APT refresh into a handler.
     72: ## 0.4.1
     73: 
     74: - Fix a PowerShell parser error in the WSL error message path by delimiting `${code}` before a colon.
     75: - Keep the Windows installer startable under PowerShell 7.6.x.
     76: ## 0.4.0
     77: 
     78: - Add automatic Windows Desktop and Start Menu shortcuts for the WSL checkout.
     79: - Add a standalone shortcut repair script.
     80: - Document how to find the installed workstation after weeks away from the setup.
     81: - Document safe local reinstall testing by deleting only Linux checkouts.
     82: - Document WSL/GitHub lessons from the first prototype installation.
     83: - Keep the installer idempotent and rerunnable on both Windows and Linux.
     84: ## 0.3.0
     85: 
     86: - Consolidate the prototype into a public English repository structure.
     87: - Add Windows and Linux entry points.
     88: - Add locked Ansible runtime, Docker Engine role and verification.
     89: - Add clean-room test documentation.
  ```

## P-031 — Historical patch note
<!-- cc:placement-item id="P-031" authoring-id="ONB-99088B457BF2" -->

Destination: none / outside Node authoring
Decision: `pending`
Kind: `ordinary-documentation`
Action: `keep`
Review note: -

### Maintained meaning

Documents: `docs/PATCH-0.4.7.md`
Reason: Keep as historical patch documentation.

### Proposal rationale

This records one historical 0.4.7 implementation fix and should not become broad current governance.

Original confidence: `high`

### Evidence

- `docs/PATCH-0.4.7.md` lines 1-10 · `c06a08c9d10b281c744c2ac75bdd0a1fb0daf989ff89805db16ab7e91d00bce7`
  ```text
      1: # Patch 0.4.7
      2: 
      3: Fix Linux host installation when started from the Windows installer.
      4: 
      5: Ansible playbooks use `become: true`. A prior `sudo -v` was not enough for
      6: Ansible in this execution path, so the Linux installer now asks once for the
      7: Linux sudo password and passes it to Ansible via a temporary
      8: `--become-password-file`.
      9: 
     10: The temporary file is removed automatically on exit.
  ```

## P-032 — Supported host baseline
<!-- cc:placement-item id="P-032" authoring-id="ONB-FAA86CC3D5C0" -->

Destination: `N-001` — **AI Workstation** (`.`)
Decision: `pending`
Kind: `state`
Action: `promote`
Review note: -

### Maintained meaning

Text: Supported host: Windows 11 with current Store WSL; PowerShell 7.4 or newer; Ubuntu 24.04 under WSL 2; x86-64 Windows and WSL architecture.
Wording: `lightly-edited`

### Proposal rationale

The supported platform list describes current compatibility state that may evolve.

Original confidence: `high`

### Evidence

- `README.md` lines 348-353 · `32f00926fa7ea3d2a228424ae6062b61ca58a7f30c965197ee56478d2ebd67b8`
  ```text
    348: ## Supported host
    349: 
    350: - Windows 11 with current Store WSL
    351: - PowerShell 7.4 or newer
    352: - Ubuntu 24.04 under WSL 2
    353: - x86-64 Windows and WSL architecture
  ```

## P-033 — Clarify repository versus Python project versioning
<!-- cc:placement-item id="P-033" authoring-id="ONB-F46403C6AF75" -->

Destination: `N-001` — **AI Workstation** (`.`)
Decision: `pending`
Kind: `unresolved`
Action: `keep`
Review note: -

### Maintained meaning

Question: What is the intended relationship between the repository/release version in CHANGELOG.md and the project version in pyproject.toml?

### Proposal rationale

Frozen Evidence shows CHANGELOG 0.6.2 while pyproject declares 0.1.0 and does not define whether these version streams are intentionally independent.

Original confidence: `high`

### Evidence

- `CHANGELOG.md` lines 1-5 · `2a6941b47ab2a411f599203c6f9487430ae2f553ca6e381012945ad7ce9bdb54`
  ```text
      1: # Changelog
      2: ## 0.6.2
      3: - Route Windows shortcuts through generated `cmd.exe /k` launchers so WSL errors remain visible.
      4: - Create a second `AI Workstation Terminal` shortcut that opens the Linux home directory.
      5: - Document direct WSL fallback commands and the `wsl --shutdown` recovery path.
  ```
- `pyproject.toml` lines 1-5 · `4bdee0e71f4dfccb3245ba1efe17d5c47d830b17f5ee7c7c963d36a6d33f6dff`
  ```text
      1: [project]
      2: name = "ai-workstation-automation"
      3: version = "0.1.0"
      4: description = "Reproducible WSL and container provisioning for local AI agents"
      5: requires-python = "==3.12.*"
  ```
- `pyproject.toml` lines 11-12 · `4bdee0e71f4dfccb3245ba1efe17d5c47d830b17f5ee7c7c963d36a6d33f6dff`
  ```text
     11: [tool.uv]
     12: package = false
  ```
- `CONTRIBUTING.md` lines 7-8 · `ca4cbe961352bb09e2fad6be95881db2210ab194991cdcef7956a832cc224b73`
  ```text
      7: 5. Update `config/versions.json`, documentation and tests together.
      8: 6. Run `./tools/release-check.sh` before committing.
  ```

# Reusable Sources

## Source O-0FF30F633E — Development Workflow
<!-- cc:placement-source id="O-0FF30F633E" origin="owner-selected" source-id="c4c94726-3cc7-4df6-b779-72bbf9c06f40" version="0.2.0-draft" normalized-digest="761b717aca335b5ddd1bf70b5c880de36d1d9f2cdca7828caefa1dd4872e1b81" package-digest="1d82c87e4f4140791f354c9d9479df845eb65c13fce1c664ecb05bec9532c8eb" -->

Destination: `N-001` — **AI Workstation** (`.`)
Decision: `pending`
Origin: `owner-selected`
Review note: -

Exact package: `0.2.0-draft` · `1d82c87e4f4140791f354c9d9479df845eb65c13fce1c664ecb05bec9532c8eb`

This Source was selected explicitly by the project owner from the supplied exact catalog. It is design input, not a claim derived from frozen project Evidence.
