# Phase 8: CI Enforcement & Instrumentation

**Status:** completed
**Satisfies:** R5, R9

## Objective

Add CI checks that enforce CLI/library parity, run library unit tests, and
update all `.claude/rules` to document the new architecture. After this phase,
any future change that breaks parity or adds logic to the wrong place is caught
automatically.

## Steps

1. **Add Layer 6 to CI** — Update `.github/workflows/push.yml` to add a new
   test step:

   ```yaml
   - name: Library unit tests
     run: |
       pip install -e ".[dev]"
       python3 -m pytest test/test_parity.py test/test_telemetry.py \
         test/test_resolver.py test/test_session.py \
         test/test_encryption.py test/test_version.py \
         -v --tb=short
   ```

   If the runner requires a venv (PEP 668), use:

   ```yaml
   - name: Library unit tests
     run: |
       python3 -m venv .venv
       .venv/bin/pip install -e ".[dev]"
       .venv/bin/python -m pytest test/ -v --tb=short \
         --ignore=test/harness --ignore=test/scenarios
   ```

2. **Parity enforcement in CI** — The `test/test_parity.py` tests (from
   Phase 1, expanded in Phase 6) run in CI. These tests:

   - Verify the CLI file does not contain class definitions for extracted
     classes (`TelemetryEmitter`, `PluginResolver`, etc.)
   - Verify the CLI file does not contain function definitions for extracted
     functions (`find_plugin_dir`, `expand_kit`, etc.)
   - Verify the library has zero runtime dependencies
   - Verify the library is importable

   If a developer accidentally adds an inline `TelemetryEmitter` to the CLI
   instead of importing from the library, CI catches it.

3. **Import validation test** — Add a test that verifies the CLI's import
   block actually uses the library:

   ```python
   # test/test_parity.py

   def test_cli_imports_from_claude_kit():
       """Verify CLI imports core classes from claude_kit."""
       cli_path = Path(__file__).parent.parent / "claude-kit"
       content = cli_path.read_text()

       required_imports = [
           "from claude_kit import",
           "from claude_kit.",
       ]
       assert any(imp in content for imp in required_imports), (
           "CLI does not import from claude_kit — "
           "it should use the library, not reimplement"
       )
   ```

4. **Update `.claude/rules/testing-standards.md`** — Add Layer 6:

   ```markdown
   ### Layer 6 — Library Unit Tests

   ```bash
   python3 -m venv .venv
   .venv/bin/pip install -e ".[dev]"
   .venv/bin/python -m pytest test/ -v --tb=short \
     --ignore=test/harness --ignore=test/scenarios
   ```

   Runs pytest on the `claude_kit` library's unit tests and parity checks.
   Run this after **any** file change inside `claude_kit/`.
   ```

   Update the zone-to-layer map:

   | Changed zone | Run layers |
   |--------------|-----------|
   | `claude_kit/**` | Layer 1, Layer 6 |
   | `test/test_*.py` (library tests) | Layer 6 |

5. **Update `.claude/rules/architecture.md`** — Add `claude_kit/` to the
   project root structure:

   ```
   claude_kit/                 # Python library package (stdlib-only)
     __init__.py               # Public API exports
     models.py                 # Plugin, Session, TelemetryEvent dataclasses
     telemetry.py              # TelemetryEmitter + event emission
     api_client.py             # Lightweight HTTP client for telemetry API
     resolver.py               # PluginResolver (find, expand, companions)
     session.py                # SessionManager (prepare, finalize)
     encryption.py             # PluginDecryptor + TempDirManager
     version.py                # VersionManager (current, remote)
     prompt.py                 # System prompt builder from loaded plugins
     exceptions.py             # PluginNotFoundError, DecryptionError, etc.

   pyproject.toml              # Root package definition (stdlib-only)
   ```

6. **Update `.claude/rules/dev-workflow.md`** — Add `claude_kit` zone:

   ```
   | `claude_kit/**` | 1, 6 | `python3 -m py_compile claude-kit && pytest test/` |
   | `pyproject.toml` (root) | 6 | `pytest test/` |
   ```

7. **Update `.claude/rules/code-style.md`** — Add library code style rules:

   ```markdown
   ## Python — Library (`claude_kit/`)

   - Same style as the CLI: ruff formatted, f-strings, pathlib
   - **Zero runtime dependencies** — stdlib only
   - **No global state** — all state is instance-level (dependency injection)
   - **Docstrings required** on all public classes and methods (not private)
   - **Type hints required** on all public method signatures
   - **`from __future__ import annotations`** — use in every file for
     forward reference support on Python 3.10
   ```

8. **Create `docs/architecture/components/python-library.md`** — Architecture
   documentation for the library:

   ```markdown
   # Component: Python Library (`claude_kit`)

   ## Purpose
   Importable Python package providing the core functionality behind the
   claude-kit CLI: plugin resolution, session management, telemetry emission,
   encryption, and version detection.

   ## Design Principles
   - Stdlib-only runtime (zero pip-installed dependencies)
   - No global state (dependency injection throughout)
   - Self-instrumenting (every operation emits telemetry when configured)
   - CLI is a thin wrapper — the library is the source of truth

   ## Public API
   | Class | Module | Purpose |
   |-------|--------|---------|
   | Plugin | models | Loaded plugin metadata |
   | Session | models | Prepared session state |
   | TelemetryEmitter | telemetry | Structured event emission |
   | APIClient | api_client | Telemetry API upload |
   | PluginResolver | resolver | Plugin finding and expansion |
   | SessionManager | session | Session lifecycle management |
   | PluginDecryptor | encryption | AES-256-CBC decryption |
   | VersionManager | version | Version detection |

   ## Consumers
   - `claude-kit` CLI (primary frontend)
   - `test/harness/` (benchmarking and testing)
   - `api/` (shares event schema, does not import library)
   ```

## Files to Create or Modify

| File | Action | Purpose |
|------|--------|---------|
| `.github/workflows/push.yml` | Modify | Add Layer 6 library tests |
| `.claude/rules/testing-standards.md` | Modify | Document Layer 6 |
| `.claude/rules/architecture.md` | Modify | Add claude_kit/ to structure |
| `.claude/rules/dev-workflow.md` | Modify | Add claude_kit zone |
| `.claude/rules/code-style.md` | Modify | Add library code style |
| `docs/architecture/components/python-library.md` | Create | Architecture docs |
| `test/test_parity.py` | Modify | Add import validation test |

## Acceptance Criteria

- [ ] CI runs library unit tests on every push (Layer 6)
- [ ] If someone adds `class TelemetryEmitter` to the CLI file, CI fails
- [ ] If someone adds a runtime dependency to `pyproject.toml`, CI fails
- [ ] `.claude/rules/testing-standards.md` documents Layer 6
- [ ] `.claude/rules/architecture.md` includes `claude_kit/` in the project
  structure
- [ ] `.claude/rules/dev-workflow.md` maps `claude_kit/**` changes to
  Layer 1 + Layer 6
- [ ] `docs/architecture/components/python-library.md` exists with complete
  public API documentation
- [ ] All 6 CI test layers pass (including the new Layer 6)
