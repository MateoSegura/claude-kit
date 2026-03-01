---
description: Update PAL to a new core version while preserving user customizations
allowed-tools: Read, Glob, Grep, Bash, AskUserQuestion
---

# PAL Update

Interactive workflow for updating the Process Asset Library to a new upstream
version while preserving user customizations.

## Steps

1. **Check current installation:**
   - Read `.claude/pal-manifest.json` for current coreVersion and userRevision
   - If no manifest found, tell the user to run `bash install.sh --target .` first

2. **Check upstream version:**
   - Read the PAL `install.sh` for the `PAL_CORE_VERSION` variable
   - Compare with installed coreVersion
   - If same version, report "already up to date" and exit

3. **Show what changed:**
   - List new/modified process documents between versions
   - List new/modified instrumentation files
   - List new templates
   - Highlight any files the user has customized that would be affected

4. **Ask user how to handle conflicts:**
   Use AskUserQuestion for each customized file that has upstream changes:
   - Keep user's version (skip upstream update for this file)
   - Take upstream version (backup user's version, apply upstream)
   - Show diff (display both versions for manual merge)

5. **Run the update:**
   ```bash
   bash install.sh --target <project-dir> --update
   ```

6. **Report results:**
   - Show updated core version
   - Show preserved customizations
   - Show backup location for any overwritten files
   - Remind user their userRevision is preserved

7. **Validate:**
   - Run `bash scripts/validate-processes.sh`
   - Report any issues introduced by the update
