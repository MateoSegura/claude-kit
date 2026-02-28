# Phase 01: Go CLI Core & Plugin System

## Objective

Port the Python CLI to a Go binary with identical behavior — all subcommands, plugin loading, companion resolution, domain auto-loading, AES-256-CBC encryption/decryption — so that `claude-kit --kit <name>` produces the exact same Claude launch as the Python version.

## Satisfies

- R1: Single Go binary with all existing subcommands and launch modes
- R2: Plugin system — prefix expansion, companion resolution, domain auto-loading, deduplication, ordering
- R3: AES-256-CBC encryption/decryption using Go stdlib (no openssl); memory-only decryption; OS keychain key storage
- R20: (partial) Anti-tamper foundation — keychain integration, memory-backed decryption, process cleanup

## Steps

1. [ ] Initialize Go module and monorepo structure — `go mod init`, create `apps/cli/`, `internal/`, `tools/` directories, move existing scripts to `tools/`
2. [ ] Implement plugin types — `internal/plugins/types.go` with `Plugin`, `PluginConfig`, `CtlConfig` structs matching current JSON schemas
3. [ ] Implement plugin loader — `internal/plugins/loader.go` with `FindPlugins()`, `ExpandPrefix()`, `LoadCtl()`, `LoadPluginJson()` matching Python's resolution logic
4. [ ] Implement companion resolver — `internal/plugins/resolver.go` with `ResolveCompanions()`, `AutoLoadCore()`, `Deduplicate()`, `OrderPlugins()` producing identical plugin sets
5. [ ] Implement AES-256-CBC crypto — `internal/crypto/` with `Encrypt()`, `Decrypt()` using `crypto/aes`, `crypto/cipher`, `golang.org/x/crypto/pbkdf2`; must decrypt Python-encrypted `content.enc` files
6. [ ] Implement split key assembly — `internal/crypto/key.go` with `AssembleKey()` replicating the Python `_get_key()` pattern (split parts, runtime assembly) as fallback
7. [ ] Implement OS keychain storage — `internal/crypto/keychain.go` using `zalando/go-keyring` to store/retrieve the master encryption key from macOS Keychain, Windows Credential Manager, or Linux Secret Service; falls back to split-key assembly if keychain unavailable
8. [ ] Implement machine-bound key derivation — `internal/crypto/derive.go` using HKDF-SHA256: `DeriveKey(master_key, salt=machine_id||hw_serial, info="plugin-decrypt")` to produce the actual plugin decryption key; prevents key portability across machines
9. [ ] Implement memory-backed decryption — `internal/crypto/memfs.go` with platform-specific secure directories: Linux (`unshare --user mount -t tmpfs`), macOS (`hdiutil attach ram:// + diskutil eraseVolume`), Windows (ACL-protected `%LOCALAPPDATA%\Temp` with restrictive DACL); fallback to `os.MkdirTemp` with `0700` perms; cleanup via `defer` + signal handlers (SIGTERM/SIGINT/SIGHUP)
10. [ ] Implement first-run key provisioning — on first launch: generate 32-byte cryptographic random master key → store in OS keychain → derive plugin key via HKDF → persist machine salt in `~/.config/claude-kit/machine.json` (salt only, never the key)
11. [ ] Implement CLI commands with cobra — `apps/cli/cmd/` with `root.go`, `run.go`, `list.go`, `validate.go`, `setup.go`, `restore.go`, `debug.go`, `feedback.go`, `version.go`, `uninstall.go`, `help.go`
12. [ ] Implement the launch flow — `cmd/run.go`: parse flags → expand kit → resolve companions → provision key (keychain or fallback) → create memory-backed decrypt dir → decrypt plugins → build `claude` args → launch Claude (no longer `Exec` — need to stay alive for cleanup) → cleanup decrypt dir on exit
13. [ ] Port environment variable setup — set `CLAUDE_KIT_HOME`, `CLAUDE_KIT_BUNDLED_DIR`, `CLAUDE_KIT_LOCAL_DIR`, `CLAUDE_KIT_OUTPUT_DIR`, `CLAUDE_KIT_MODE`, `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`
14. [ ] Write comprehensive tests — `internal/plugins/loader_test.go`, `internal/crypto/crypto_test.go`, `internal/crypto/memfs_test.go`, `apps/cli/cmd_test.go` with table-driven tests covering edge cases
15. [ ] Write backwards-compatibility test — decrypt a `content.enc` file produced by the Python/openssl pipeline and verify contents match
16. [ ] Write memory-backed decryption tests — verify plugins are decrypted to tmpfs/ramdisk, verify cleanup on normal exit, verify cleanup on SIGTERM, verify no plaintext on persistent storage
17. [ ] Update `tools/test-cli.sh` to test the Go binary instead of the Python script

## Files to Create/Modify

### Create
- `go.mod` — Go module definition (`module github.com/mateosegura/claude-kit`)
- `go.sum` — dependency lock (auto-generated)
- `apps/cli/main.go` — CLI entry point
- `apps/cli/cmd/root.go` — root cobra command, global flags
- `apps/cli/cmd/run.go` — `--kit` / `--plugin` launch logic
- `apps/cli/cmd/list.go` — `list` subcommand
- `apps/cli/cmd/validate.go` — `validate` subcommand (calls Python script)
- `apps/cli/cmd/setup.go` — `setup` subcommand
- `apps/cli/cmd/restore.go` — `restore` subcommand
- `apps/cli/cmd/debug.go` — `debug` subcommand
- `apps/cli/cmd/feedback.go` — `feedback` subcommand
- `apps/cli/cmd/version.go` — `version` subcommand
- `apps/cli/cmd/uninstall.go` — `uninstall` subcommand
- `internal/plugins/types.go` — Plugin, CtlConfig, PluginConfig structs
- `internal/plugins/loader.go` — plugin discovery and loading
- `internal/plugins/resolver.go` — companion + domain resolution
- `internal/plugins/loader_test.go` — plugin system tests
- `internal/crypto/encrypt.go` — AES-256-CBC encryption
- `internal/crypto/decrypt.go` — AES-256-CBC decryption
- `internal/crypto/key.go` — split key assembly (fallback)
- `internal/crypto/keychain.go` — OS keychain storage via go-keyring
- `internal/crypto/derive.go` — HKDF machine-bound key derivation
- `internal/crypto/memfs.go` — memory-backed filesystem (tmpfs/ramdisk/ACL-temp)
- `internal/crypto/memfs_linux.go` — Linux tmpfs implementation
- `internal/crypto/memfs_darwin.go` — macOS RAM disk implementation
- `internal/crypto/memfs_windows.go` — Windows ACL temp implementation
- `internal/crypto/crypto_test.go` — encryption round-trip tests
- `internal/crypto/memfs_test.go` — memory-backed decryption tests
- `internal/config/cli.go` — CLI config (paths, defaults, mode detection)
- `internal/version/version.go` — version info (ldflags embedded at build)

### Modify
- `tools/test-cli.sh` — update to test Go binary instead of Python

### Keep (Unchanged)
- `plugins/` — all plugin content
- `templates/` — scaffolding templates
- `tools/validate-plugins.py` — Python validation (called by Go `validate` command)
- `tools/test-plugin-consistency.sh` — consistency checks

## Acceptance Criteria

- [ ] `go build -o claude-kit ./apps/cli` produces a working binary
- [ ] `claude-kit --kit embedded-zephyr-engineer` loads the same plugin set as the Python version (verified by comparing `--plugin-dir` arguments)
- [ ] `claude-kit list` shows the same output as the Python version
- [ ] `claude-kit validate --all --strict` runs the Python validation script and returns the same results
- [ ] `claude-kit list -v` shows versions, roles, and launch hints
- [ ] A `content.enc` file encrypted by Python/openssl decrypts correctly with the Go implementation
- [ ] A `content.enc` file encrypted by Go decrypts correctly with the Go implementation
- [ ] Master encryption key is stored in OS keychain — `security find-generic-password -s claude-kit` (macOS) confirms storage
- [ ] Plugin decryption key is derived via HKDF and is machine-specific — exporting the keychain entry to a different machine produces a different derived key
- [ ] On Linux: plugins are decrypted to a tmpfs mount; `df -T <decrypt-dir>` shows type `tmpfs`
- [ ] On macOS: plugins are decrypted to a RAM disk; `diskutil info <disk>` shows RAM-backed device
- [ ] On process exit (normal, SIGTERM, SIGINT): the decrypt directory is removed and all temporary mounts are unmounted
- [ ] `go test ./internal/...` passes with >90% coverage on plugins/ and crypto/ packages
- [ ] No runtime dependency on `python3` for CLI operation (except `validate` subcommand which shells out to Python)
- [ ] Binary size is under 25MB for linux/amd64
- [ ] Startup time (measured to first output) is under 50ms

## Dependencies

- Requires: None (first phase)
- Blocks: Phase 02 (distribution needs compiled binary), Phase 04 (telemetry hooks need CLI process to stay alive), Phase 05 (autonomous needs plugin loading)

## Architecture Note: Process Lifecycle Change

The Python CLI used `os.execvp()` to replace itself with Claude Code. The Go CLI **cannot** use `syscall.Exec()` because it must:

1. **Stay alive** to manage the memory-backed decrypt directory and cleanup on exit
2. **Run the HTTP hook server** for telemetry capture (Phase 04)
3. **Handle signal-based cleanup** (SIGTERM/SIGINT → unmount tmpfs → remove decrypt dir)

Instead, the Go CLI spawns Claude Code as a child process (`os/exec.Cmd`), forwards stdin/stdout/stderr, and waits for exit. On child exit, it runs cleanup. This is a fundamental architecture change from the Python version.
