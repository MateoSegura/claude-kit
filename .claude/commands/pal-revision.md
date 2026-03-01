---
description: Bump the user's PAL revision and record customizations
allowed-tools: Read, Glob, Grep, Bash, Write, AskUserQuestion
---

# PAL User Revision

Bump the user's local PAL revision number and record what was customized.
User revisions track local tailoring of the PAL framework.

## Steps

1. **Read current manifest:**
   - Read `.claude/pal-manifest.json`
   - Show current: `Core: X.Y.Z | User Revision: N`

2. **Ask what was customized:**
   Use AskUserQuestion:
   - Which files were modified? (auto-detect by scanning for `<!-- pal-user-modified -->`)
   - What was the reason for customization?

3. **Mark customized files:**
   For each file the user identifies as customized:
   - Add `<!-- pal-user-modified -->` comment at the top if not already present
   - Add the file path to the manifest's `customized` array

4. **Bump revision:**
   - Increment `userRevision` in `.claude/pal-manifest.json`
   - Update `updatedAt` timestamp

5. **Report:**
   ```
   PAL Revision Updated
   ────────────────────
   Core version: X.Y.Z
   User revision: N -> N+1
   Customized files: X

   Files marked as customized:
   - .claude/rules/pal-process-governance.md
   - (other customized files)

   These files will be preserved during future `pal-update` runs.
   ```
