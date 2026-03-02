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
| TelemetryEvent | models | Structured telemetry event |
| TelemetryEmitter | telemetry | Structured event emission |
| APIClient | api_client | Telemetry API upload |
| PluginResolver | resolver | Plugin finding and expansion |
| SessionManager | session | Session lifecycle management |
| PluginDecryptor | encryption | AES-256-CBC decryption |
| TempDirManager | encryption | Temp directory lifecycle |
| VersionManager | version | Version detection |

## Exception Hierarchy

| Exception | Module | Raised when |
|-----------|--------|-------------|
| PluginNotFoundError | exceptions | Plugin name not found in any plugins directory |
| DecryptionError | exceptions | openssl decryption fails |

## Security Boundary

The library never assembles encryption keys. `PluginDecryptor` accepts an
injected key via its constructor. Key assembly logic (`_get_key()`) stays in
the CLI file and is never imported from the library.

## Consumers

- `claude-kit` CLI (primary frontend)
- `test/harness/` (benchmarking and testing)
- `api/` (shares event schema, does not import library)

## Testing

145 unit tests in `test/test_*.py` — run via Layer 6:

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/python -m pytest test/ -v --tb=short \
  --ignore=test/harness --ignore=test/scenarios --ignore=test/src
```
