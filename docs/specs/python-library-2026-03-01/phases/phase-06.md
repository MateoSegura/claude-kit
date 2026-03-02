# Phase 6: CLI Refactor

**Status:** completed
**Satisfies:** R2, R3, R7

## Objective

Complete the CLI refactoring so that every core function is imported from
`claude_kit`. The CLI file retains only: argument parsing, command dispatch,
output formatting, key assembly, and the try/except import fallback for user
mode.

## Steps

1. **Audit remaining CLI functions** — After phases 2–5, these functions
   should already be extracted. This phase verifies completeness and moves
   any stragglers:

   | Function | Should live in | Status after Phase 5 |
   |----------|---------------|---------------------|
   | `TelemetryEmitter` | `claude_kit.telemetry` | Moved in Phase 2 |
   | `APIClient` | `claude_kit.api_client` | Moved in Phase 2 |
   | `PluginResolver.*` | `claude_kit.resolver` | Moved in Phase 3 |
   | `SessionManager` | `claude_kit.session` | Moved in Phase 4 |
   | `PluginDecryptor` | `claude_kit.encryption` | Moved in Phase 5 |
   | `TempDirManager` | `claude_kit.encryption` | Moved in Phase 5 |
   | `VersionManager` | `claude_kit.version` | Moved in Phase 5 |
   | `class C` (colors) | CLI only | Stays in CLI |
   | `_get_key()` | CLI only | Stays in CLI |
   | `cmd_*()` functions | CLI only | Stay in CLI |
   | `_init_telemetry()` | CLI only | Stays in CLI |

2. **Implement the import fallback** — For user-mode installations where the
   library may not be pip-installed, the CLI needs a fallback:

   ```python
   try:
       from claude_kit import (
           TelemetryEmitter, PluginResolver, SessionManager,
           PluginDecryptor, TempDirManager, VersionManager, APIClient,
           Plugin, Session, TelemetryEvent,
       )
       from claude_kit.exceptions import (
           PluginNotFoundError, DecryptionError, APIUploadError,
       )
   except ImportError:
       # User mode: claude_kit/ is alongside claude-kit in the install dir
       import importlib.util
       _lib_dir = Path(__file__).parent / "claude_kit"
       if _lib_dir.is_dir():
           # Add parent to sys.path so 'import claude_kit' works
           sys.path.insert(0, str(Path(__file__).parent))
           from claude_kit import (
               TelemetryEmitter, PluginResolver, SessionManager,
               PluginDecryptor, TempDirManager, VersionManager, APIClient,
               Plugin, Session, TelemetryEvent,
           )
           from claude_kit.exceptions import (
               PluginNotFoundError, DecryptionError, APIUploadError,
           )
       else:
           raise ImportError(
               "claude_kit library not found. Run 'pip install -e .' in the "
               "repo root, or ensure claude_kit/ is alongside the claude-kit script."
           )
   ```

3. **Verify CLI line count reduction** — Before this spec, the CLI is ~2,259
   lines. After extraction, the CLI should be significantly smaller. Track the
   reduction:

   - Before: ~2,259 lines (all logic embedded)
   - After: ~800–1,000 lines (CLI-specific only: argparse, cmd_* dispatch,
     output formatting, key assembly, help text)
   - Extracted to library: ~1,200–1,400 lines

4. **Run the full regression suite** — All 5 layers must pass:

   ```bash
   python3 -m py_compile claude-kit && \
   bash scripts/test-cli.sh && \
   python3 scripts/validate-plugins.py --all --strict && \
   bash scripts/test-plugin-consistency.sh && \
   bash scripts/validate-docs.sh && \
   (cd api && python3 -m venv .venv && .venv/bin/pip install -q -e ".[dev]" && \
    .venv/bin/python -m pytest -v --tb=short)
   ```

5. **Behavioral parity test** — Run a real `claude-kit --kit core-kit`
   session and compare telemetry output with the pre-extraction baseline. The
   JSONL events should have identical schema and event types.

6. **Update `test/test_parity.py`** — Expand the parity test to verify ALL
   extracted functions are absent from the CLI:

   ```python
   EXTRACTED_FUNCTIONS = {
       "find_plugin_dir", "resolve_prefix", "_read_ctl",
       "resolve_companions", "resolve_core_plugins", "expand_kit",
       "plugin_version", "_is_encrypted", "_decrypt_plugin",
       "_cleanup_temp", "_cleanup_stale_temps",
       "_version_from_changelog", "_current_version", "_remote_version",
   }

   def test_cli_does_not_contain_extracted_functions():
       cli_path = Path(__file__).parent.parent / "claude-kit"
       tree = ast.parse(cli_path.read_text())
       cli_functions = {
           node.name for node in ast.walk(tree)
           if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
       }
       duplicates = EXTRACTED_FUNCTIONS & cli_functions
       assert not duplicates, (
           f"CLI contains functions that should be in claude_kit: {duplicates}"
       )
   ```

## Files to Create or Modify

| File | Action | Purpose |
|------|--------|---------|
| `claude-kit` | Modify | Final refactor — import everything from claude_kit |
| `test/test_parity.py` | Modify | Expand to check all extracted functions |

## Acceptance Criteria

- [ ] CLI file contains NO class or function definitions that exist in the
  `claude_kit` library
- [ ] CLI file is under 1,200 lines (down from 2,259)
- [ ] `python3 claude-kit --help` works
- [ ] `python3 claude-kit --kit core-kit --print "test"` works
- [ ] `python3 claude-kit validate --all` works
- [ ] `python3 claude-kit telemetry on` works
- [ ] `python3 claude-kit version` works
- [ ] All 5 existing CI test layers pass
- [ ] `test/test_parity.py` passes with the expanded function list
- [ ] Telemetry JSONL output is schema-identical to pre-extraction baseline
