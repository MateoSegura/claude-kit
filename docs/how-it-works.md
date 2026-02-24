# How It Works

claude-kit builds on Claude Code's native configuration hierarchy — it doesn't replace it, bypass it, or modify it. Understanding how Claude Code loads configuration is essential to understanding what claude-kit does (and doesn't do) when it injects plugins.

---

## Claude Code Configuration Hierarchy

Claude Code reads configuration from four scopes, each overriding the one below it:

```mermaid
graph TD
    subgraph Priority["Priority (highest → lowest)"]
        direction TB
        M["<b>Managed</b><br/>Organization-enforced<br/><code>/etc/claude-code/</code>"]
        U["<b>User</b><br/>Personal defaults<br/><code>~/.claude/</code>"]
        PS["<b>Project (shared)</b><br/>Team conventions<br/><code>.claude/</code>"]
        PL["<b>Project (local)</b><br/>Machine-specific<br/><code>.claude/settings.local.json</code>"]
    end

    M --> U --> PS --> PL

    style M fill:#e74c3c,color:#fff,stroke:#c0392b
    style U fill:#3498db,color:#fff,stroke:#2980b9
    style PS fill:#2ecc71,color:#fff,stroke:#27ae60
    style PL fill:#9b59b6,color:#fff,stroke:#8e44ad
```

### What each scope provides

| Scope | Settings | Instructions | Hooks | MCP |
|-------|----------|-------------|-------|-----|
| **Managed** | `managed-settings.json` | `CLAUDE.md` | Yes (can be exclusive) | `managed-mcp.json` |
| **User** | `~/.claude/settings.json` | `~/.claude/CLAUDE.md` | Yes | In settings or `~/.claude.json` |
| **Project (shared)** | `.claude/settings.json` | `CLAUDE.md` + `.claude/rules/*.md` | Yes | `.mcp.json` |
| **Project (local)** | `.claude/settings.local.json` | `CLAUDE.local.md` | No | No |

### How settings merge

**Settings** follow a strict override chain. For any given key, the highest-priority source wins:

```
managed > CLI args > project local > project shared > user
```

**Instructions** (CLAUDE.md and rules) are **concatenated, not overridden**. Claude sees all of them, from all scopes, in every turn. A project CLAUDE.md does not replace the user's — both are loaded.

**Hooks** from all applicable scopes **run in parallel**. A user hook, a project hook, and a managed hook matching the same event all fire. Identical commands are deduplicated.

**Permissions** are evaluated in deny > ask > allow order. The first matching rule wins, regardless of scope.

---

## For Individuals

An individual developer has two active scopes: **user** and **project**.

### File layout

```mermaid
graph LR
    subgraph Home["~/.claude/ (user scope)"]
        direction TB
        UCM["CLAUDE.md<br/><i>personal instructions</i>"]
        US["settings.json<br/><i>model, permissions, hooks</i>"]
        UR["rules/*.md<br/><i>global coding rules</i>"]
    end

    subgraph Project["your-project/.claude/ (project scope)"]
        direction TB
        PCM["CLAUDE.md<br/><i>project instructions</i>"]
        PS2["settings.json<br/><i>team settings, committed</i>"]
        PL2["settings.local.json<br/><i>personal overrides, gitignored</i>"]
        PR["rules/*.md<br/><i>project coding rules</i>"]
    end

    Home -.->|"always loaded"| Claude["Claude Code"]
    Project -.->|"loaded in this repo"| Claude

    style Home fill:#3498db15,stroke:#3498db
    style Project fill:#2ecc7115,stroke:#2ecc71
    style Claude fill:#f39c12,color:#fff,stroke:#e67e22
```

**What Claude sees at startup:**
1. `~/.claude/CLAUDE.md` — always loaded, every project
2. `~/.claude/rules/*.md` — always loaded (global rules without `path:` frontmatter)
3. `CLAUDE.md` or `.claude/CLAUDE.md` — loaded for this project
4. `.claude/rules/*.md` — loaded for this project
5. `CLAUDE.local.md` — your personal project notes (gitignored)
6. Auto-learned memory from `~/.claude/projects/<project>/memory/`

All of these are concatenated into a single system prompt. None override each other.

### Where claude-kit fits

claude-kit does not create or modify any of these files. When you run:

```bash
claude-kit --kit coding-embedded-zephyr
```

claude-kit resolves the plugins, then launches Claude Code with `--plugin-dir` arguments:

```mermaid
sequenceDiagram
    participant User
    participant CK as claude-kit
    participant FS as File System
    participant CC as Claude Code

    User->>CK: claude-kit --kit coding-embedded-zephyr
    CK->>FS: resolve_prefix("coding-embedded-zephyr")
    FS-->>CK: [engineer, grader, tester, debugger, knowledge]
    CK->>FS: resolve_companions() for each
    FS-->>CK: knowledge (companion of all four)
    CK->>CK: deduplicate → ordered list

    CK->>CC: exec claude<br/>--plugin-dir knowledge/<br/>--plugin-dir engineer/<br/>--plugin-dir grader/<br/>--plugin-dir tester/<br/>--plugin-dir debugger/

    Note over CC: Claude Code loads each plugin's<br/>agents, commands, skills, hooks<br/>ON TOP of existing config
```

The result is Claude Code running with all your normal configuration **plus** the plugin-injected components:

```mermaid
graph TB
    subgraph Existing["Your existing config (untouched)"]
        direction LR
        E1["~/.claude/CLAUDE.md"]
        E2["~/.claude/settings.json"]
        E3[".claude/settings.json"]
        E4[".claude/rules/*.md"]
    end

    subgraph Injected["Plugin-injected (via --plugin-dir)"]
        direction LR
        P1["agents/ → specialized subagents"]
        P2["commands/ → slash commands"]
        P3["skills/ → domain knowledge"]
        P4["hooks/ → behavioral enforcement"]
    end

    Existing --> Session["Claude Code Session"]
    Injected --> Session

    style Existing fill:#3498db15,stroke:#3498db
    style Injected fill:#e67e2215,stroke:#e67e22
    style Session fill:#2c3e50,color:#fff,stroke:#2c3e50
```

Plugins compose cleanly because Claude Code namespaces everything:
- Commands become `/plugin-name:command-name`
- Agents are scoped to the plugin that defines them
- Plugin hooks accumulate alongside your existing hooks
- No file on disk is modified

---

## For Organizations

Organizations add a fifth, highest-priority scope: **managed configuration**. This scope cannot be overridden by users or projects.

### Deployment paths

```mermaid
graph TD
    subgraph Org["Organization Admin"]
        Admin["Admin Console<br/>or MDM system"]
    end

    Admin -->|"Server-managed<br/>(Claude for Teams/Enterprise)"| Cloud["Anthropic Servers"]
    Admin -->|"Endpoint-managed<br/>(MDM / Ansible / GPO)"| Device["Developer Machine"]

    Cloud -->|"fetched at startup<br/>polled hourly"| CC["Claude Code"]
    Device -->|"read from disk<br/>OS-protected"| CC

    subgraph DevMachine["Developer Machine"]
        Managed["/etc/claude-code/<br/>managed-settings.json<br/>CLAUDE.md<br/>managed-mcp.json"]
        UserConf["~/.claude/"]
        ProjectConf[".claude/"]
    end

    Managed -->|"highest priority"| CC
    UserConf -->|"personal defaults"| CC
    ProjectConf -->|"team settings"| CC

    style Org fill:#e74c3c15,stroke:#e74c3c
    style Managed fill:#e74c3c,color:#fff,stroke:#c0392b
    style Cloud fill:#e74c3c30,stroke:#e74c3c
    style CC fill:#2c3e50,color:#fff
```

### Two enforcement methods

| | Server-managed | Endpoint-managed |
|---|---|---|
| **How deployed** | Anthropic Admin Console | MDM, Ansible, Group Policy |
| **Delivery** | Cloud fetch at startup, polled hourly | Static file on disk |
| **Offline** | Uses cached settings | Always available |
| **Protection** | Client-side (bypassable on unmanaged devices) | OS-level file protection |
| **Best for** | Teams without MDM, BYOD | Managed corporate devices |
| **If both exist** | Server-managed wins | — |

**Recommendation:** Use both for defense-in-depth. Server-managed for the base policy, endpoint-managed for hard enforcement on corporate devices.

### Managed-only keys

These keys **only work in managed settings** and cannot be set at any lower scope:

| Key | Effect |
|-----|--------|
| `disableBypassPermissionsMode` | Prevents `--dangerously-skip-permissions` and "Act" mode |
| `allowManagedPermissionRulesOnly` | Blocks all user/project permission rules — only org rules apply |
| `allowManagedHooksOnly` | Blocks all user/project/plugin hooks — only org hooks run |
| `strictKnownMarketplaces` | Controls which plugin marketplace sources users can install from |

### Managed file locations

| File | Linux / WSL | macOS |
|------|------------|-------|
| Settings | `/etc/claude-code/managed-settings.json` | `/Library/Application Support/ClaudeCode/managed-settings.json` |
| Instructions | `/etc/claude-code/CLAUDE.md` | `/Library/Application Support/ClaudeCode/CLAUDE.md` |
| MCP servers | `/etc/claude-code/managed-mcp.json` | `/Library/Application Support/ClaudeCode/managed-mcp.json` |

### Full hierarchy with plugins

When an organization deploys managed settings AND a developer uses claude-kit, all five layers compose:

```mermaid
graph TB
    subgraph Layers["Complete Configuration Stack"]
        direction TB
        L1["<b>1. Managed</b> — org policy, cannot be overridden"]
        L2["<b>2. CLI / Plugins</b> — claude-kit injects --plugin-dir args"]
        L3["<b>3. User</b> — ~/.claude/ personal defaults"]
        L4["<b>4. Project shared</b> — .claude/ team settings"]
        L5["<b>5. Project local</b> — .claude/settings.local.json"]
    end

    L1 --- L2 --- L3 --- L4 --- L5

    L1 -.- N1["Settings: highest priority, locks keys"]
    L2 -.- N2["Agents, commands, skills, hooks added"]
    L3 -.- N3["Personal model preference, global rules"]
    L4 -.- N4["Shared hooks, permissions, CLAUDE.md"]
    L5 -.- N5["Machine-specific overrides, gitignored"]

    style L1 fill:#e74c3c,color:#fff,stroke:#c0392b
    style L2 fill:#e67e22,color:#fff,stroke:#d35400
    style L3 fill:#3498db,color:#fff,stroke:#2980b9
    style L4 fill:#2ecc71,color:#fff,stroke:#27ae60
    style L5 fill:#9b59b6,color:#fff,stroke:#8e44ad
```

**Critical interaction: `allowManagedHooksOnly`**

If an organization sets `"allowManagedHooksOnly": true`, **all plugin hooks are suppressed**. Plugin agents, commands, and skills still load — but hooks (behavioral enforcement) are blocked. This means:
- Plugin PreToolUse guards (e.g., blocking dangerous commands) will not run
- Plugin PostToolUse linting (e.g., anti-pattern detection) will not run
- Plugin Stop verification (e.g., deliverable quality checks) will not run

Organizations deploying claude-kit should either leave `allowManagedHooksOnly` as `false`, or replicate the essential plugin hooks in their managed settings.

---

## How Plugin Loading Works

When Claude Code receives `--plugin-dir` arguments, it treats each directory as a self-contained plugin:

```mermaid
graph LR
    subgraph Plugin["Plugin Directory"]
        PJ[".claude-plugin/plugin.json"]
        AG["agents/*.md"]
        CM["commands/*.md"]
        SK["skills/*/SKILL.md"]
        HK["hooks/hooks.json"]
        MC[".mcp.json"]
        LS[".lsp.json"]
    end

    PJ -->|"name, version"| Namespace["Namespace:<br/>plugin-name:*"]
    AG -->|"subagent definitions"| Task["Available via Task tool"]
    CM -->|"slash commands"| Slash["/plugin-name:command"]
    SK -->|"domain knowledge"| Context["Injected into agent context"]
    HK -->|"event handlers"| Hooks["Accumulate with other hooks"]
    MC -->|"MCP servers"| MCP["Available to agents"]
    LS -->|"LSP config"| LSP["Language server integration"]

    style Plugin fill:#e67e2215,stroke:#e67e22
```

### Plugin isolation guarantees

- **Namespace isolation**: A plugin's commands and skills are prefixed with the plugin name. `/coding-embedded-zephyr-engineer:develop` cannot collide with `/coding-frontend-svelte-engineer:develop`.
- **No file mutation**: Installing a plugin never modifies `~/.claude/`, `.claude/`, or any user file. Plugins are read-only directories.
- **Hook accumulation**: Plugin hooks run alongside (not instead of) user and project hooks. All matching hooks from all sources fire in parallel.
- **Companion resolution**: claude-kit reads `ctl.json` → `companions` and loads companion plugins first, so the knowledge plugin's skills are available before any role plugin's agents reference them.

### What claude-kit actually does

claude-kit is a thin launcher. It:

1. **Resolves** the kit name to plugin directories (prefix matching + companion resolution)
2. **Deduplicates** companion plugins that appear in multiple dependency chains
3. **Orders** companions before the plugins that depend on them
4. **Builds** the `claude` command with repeated `--plugin-dir` flags
5. **Replaces itself** with `os.execvp("claude", args)` — claude-kit is not running during your session

After launch, it's just Claude Code with more plugins loaded. claude-kit is gone.
