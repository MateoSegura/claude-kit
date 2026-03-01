---
description: Launch the local MkDocs Material development server with hot-reload
allowed-tools:
  - Bash
  - Read
  - Glob
---

# /pal-docs-serve -- Local Documentation Server

You are launching the local documentation development server. Follow this
workflow exactly.

## Workflow

### Step 1: Verify prerequisites

Check that `mkdocs` is installed:

```bash
mkdocs --version
```

If not installed, run `pip install mkdocs-material` and try again.

### Step 2: Run the dev server

```bash
bash docs-site/serve.sh
```

This will:
1. Merge content from `processes/` and `mappings/` into `.docs-build/`
2. Start MkDocs with hot-reload on port 8000

### Step 3: Report to the user

Print:
- The URL: `http://localhost:8000`
- Hot-reload note: changes to existing files in `.docs-build/` auto-reload;
  new files require restarting the server
- How to stop: `Ctrl+C`

If the user wants a different port:
```bash
bash docs-site/serve.sh --port <PORT>
```
