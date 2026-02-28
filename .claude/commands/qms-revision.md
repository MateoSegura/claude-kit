---
description: Bump the user's QMS revision and record customizations
allowed-tools: Read, Glob, Grep, Bash, Write, AskUserQuestion
---

# QMS User Revision

Bump the user's local QMS revision number and record what was customized.
User revisions track local tailoring of the QMS framework.

## Steps

1. **Read current manifest:**
   - Read `.claude/qms-manifest.json`
   - Show current: `Core: X.Y.Z | User Revision: N`

2. **Ask what was customized:**
   Use AskUserQuestion:
   - Which files were modified? (auto-detect by scanning for `<!-- qms-user-modified -->`)
   - What was the reason for customization?

3. **Mark customized files:**
   For each file the user identifies as customized:
   - Add `<!-- qms-user-modified -->` comment at the top if not already present
   - Add the file path to the manifest's `customized` array

4. **Bump revision:**
   - Increment `userRevision` in `.claude/qms-manifest.json`
   - Update `updatedAt` timestamp

5. **Report:**
   ```
   QMS Revision Updated
   ────────────────────
   Core version: X.Y.Z
   User revision: N → N+1
   Customized files: X

   Files marked as customized:
   - .claude/rules/qms-process-governance.md
   - qms/processes/base/lifecycle/PROC-LC-004.md

   These files will be preserved during future `qms-update` runs.
   ```
