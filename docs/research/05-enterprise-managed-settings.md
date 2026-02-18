# Enterprise & Managed Settings

## Two Deployment Methods

### Option A: Server-Managed (Cloud-Delivered)
- Configured in **Claude.ai Admin Console** > Admin Settings > Claude Code > Managed settings
- Delivered automatically when users authenticate with org credentials
- Fetched at startup, **polled hourly** during active sessions
- Cached locally for offline use (uses last-fetched settings on network failure)
- Requires: Claude for Teams/Enterprise plan + Claude Code v2.1.38+
- Best for: Orgs without MDM, managing unmanaged devices
- If both server-managed and endpoint-managed exist, **server-managed wins**

### Option B: Endpoint-Managed (MDM/File-Based)
- Deploy `managed-settings.json` to system directories via MDM/Ansible/Group Policy
- Stronger enforcement: file is OS-protected from user modification
- Works offline
- File locations:
  - Linux/WSL: `/etc/claude-code/managed-settings.json`
  - macOS: `/Library/Application Support/ClaudeCode/managed-settings.json`
  - Windows: `C:\Program Files\ClaudeCode\managed-settings.json`

## Managed-Only Settings Keys

These keys **only work in managed settings** and cannot be set by users or projects:

| Key | Effect |
|---|---|
| `allowManagedHooksOnly` | Blocks ALL user/project/plugin hooks. Only org-defined hooks run. |
| `allowManagedPermissionRulesOnly` | Blocks ALL user/project permission rules. Only org rules apply. |
| `disableBypassPermissionsMode` | Prevents `--dangerously-skip-permissions` and "Act" mode. Set to `"disable"`. |
| `strictKnownMarketplaces` | Controls which plugin marketplace sources users can install from. |

## Managed CLAUDE.md

Organization-level instructions that are always loaded, highest priority, cannot be overridden:

| OS | Path |
|---|---|
| Linux/WSL | `/etc/claude-code/CLAUDE.md` |
| macOS | `/Library/Application Support/ClaudeCode/CLAUDE.md` |
| Windows | `C:\Program Files\ClaudeCode\CLAUDE.md` |

## Managed MCP Servers

Exclusive MCP control via `managed-mcp.json` at the same system paths.
When deployed, only these MCP servers are available. Users cannot add or modify servers.

Alternative: Policy-based control via `allowedMcpServers` / `deniedMcpServers` in managed settings (lets users add servers within constraints).

## Teams vs Enterprise Feature Comparison

| Feature | Teams | Enterprise |
|---|---|---|
| Admin Console | Yes | Yes |
| Server-Managed Settings | Yes (public beta) | Yes |
| MDM Support | Not documented | Yes |
| SSO (SAML) | No | Yes |
| RBAC | No | Yes |
| Domain Capture | No | Yes |
| Compliance API | No | Yes |
| Audit Logging | Basic | Full with export |
| Spending Controls | Yes | Yes |
| Usage Analytics | Yes | Yes |

## Security Considerations

- **Server-managed**: Client-side control. Users with admin access on unmanaged devices can potentially bypass.
- **Endpoint-managed (MDM)**: OS-level enforcement. File protected from user modification. Stronger.
- **Recommendation**: Combine both for defense-in-depth.

## User Authentication

- Users sign in with Claude.ai team/enterprise account
- Credentials stored in macOS Keychain or secure credential files (Linux/Windows)
- Switching between personal and team: `claude logout` then `claude login` with different credentials
- Best practice: choose one authentication method per org to avoid confusion

## Practical Configuration Example

```json
{
  "allowManagedHooksOnly": true,
  "allowManagedPermissionRulesOnly": false,
  "disableBypassPermissionsMode": "disable",

  "hooks": {
    "SessionStart": [
      {
        "matcher": "compact",
        "hooks": [{
          "type": "agent",
          "prompt": "Read plan/status.log and plan/overview.md. Summarize current state.",
          "timeout": 30
        }]
      }
    ],
    "TaskCompleted": [
      {
        "hooks": [{
          "type": "command",
          "command": "/etc/claude-code/hooks/update-status.sh"
        }]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [{
          "type": "command",
          "command": "/etc/claude-code/hooks/security-check.sh"
        }]
      }
    ]
  }
}
```

With `allowManagedHooksOnly: true`, developers cannot add rogue hooks.
With `allowManagedPermissionRulesOnly: false`, projects can still customize their own permissions.
