# REQ-008: Secure Distribution

**Status:** active
**Priority:** must
**Created:** 2026-02-28

## Context

claude-kit plugins contain proprietary domain knowledge — curated API
references, architectural patterns, coding standards, and behavioral
constraints developed through significant research and engineering effort.
When plugins are distributed to end users, this intellectual property must be
protected against casual extraction while remaining fully functional at runtime.

The protection model faces an inherent constraint: any content that Claude reads
during a session is visible to the user running that session. Encryption at rest
protects against filesystem browsing and redistribution of plaintext files, but
it cannot prevent a user from observing what their own agent reads. This is not
a flaw — it is a fundamental property of any system where the user controls the
runtime environment.

The real defensible moat is not encryption alone. It is the combination of:
encrypted distribution (raises the effort bar), research depth (hard to
replicate), shipping velocity (first-mover advantage), platform value (cloud
analytics, session management), and ecosystem effects (community plugins,
organizational configurations).

## Requirement

The system shall protect plugin intellectual property during distribution
through:

1. **Encryption at rest** — All content directories (agents, commands, skills,
   hooks, scripts) are encrypted using AES-256-CBC before distribution. Only
   plugin metadata (plugin.json, ctl.json) and README remain plaintext.
2. **Memory-only decryption** — At runtime, encrypted content is decrypted to
   a temporary directory, passed to the agent session, and cleaned up on exit.
   Plaintext content never persists on the user's filesystem.
3. **Key assembly** — The decryption key is assembled at runtime from split
   parts within the CLI, not stored as a single string anywhere in the
   codebase.
4. **Metadata transparency** — Plugin names, descriptions, versions, and role
   information remain readable so the user can understand what is installed
   without decrypting content.

## Acceptance Criteria

- [ ] Encrypted plugins produce a single `content.enc` blob per plugin
- [ ] Plaintext content directories are removed after encryption
- [ ] Decryption produces a temporary directory cleaned up on session exit
- [ ] The assembled key never appears in logs, commits, or output
- [ ] `plugin.json` and `ctl.json` remain readable without decryption
- [ ] The encryption/decryption cycle is lossless — decrypted content matches
      the original exactly
- [ ] Users can install, update, and use plugins without manual key management

## Traces

- **From:** (product requirement — IP protection for commercial distribution)
- **To:** ADR-007 (IP protection model — what is and is not defensible)
