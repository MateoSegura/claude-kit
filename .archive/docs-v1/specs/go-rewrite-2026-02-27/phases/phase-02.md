# Phase 02: Distribution & Self-Update

## Objective

Set up GoReleaser for cross-platform binary distribution with pre-release channels (alpha/beta/stable), Homebrew tap, Scoop manifest, and a self-update mechanism so users can install and keep claude-kit current without external tools.

## Satisfies

- R4: Cross-platform distribution — macOS (arm64, amd64), Linux (arm64, amd64), Windows (amd64)
- R5: Pre-release channels — alpha, beta, RC, stable with separate taps
- R6: Self-update mechanism — `claude-kit update` replaces the running binary
- R20: (partial) Anti-tamper — garble obfuscation, anti-debugging, binary integrity verification

## Steps

1. [ ] Create GoReleaser configuration — `deploy/cli/.goreleaser.yml` with build matrix for 5 targets, archive naming convention, checksum generation
2. [ ] Configure garble obfuscation — integrate `burrowers/garble` as the Go compiler wrapper in GoReleaser builds with `-literals -tiny` flags for release (not snapshot) mode; obfuscates string literals, function names, and package paths
3. [ ] Implement anti-debugging detection — `internal/antitamper/` with platform-specific build tags: Linux (`ptrace(PTRACE_TRACEME)` self-attach), macOS (`sysctl` P_TRACED flag check), Windows (`IsDebuggerPresent` + `CheckRemoteDebuggerPresent`); runs at startup, exits with generic error if debugger detected
4. [ ] Implement binary self-hash integrity — `internal/antitamper/integrity.go`: at build time, embed expected SHA-256 hash via ldflags; at startup, compute hash of the running binary (`/proc/self/exe` on Linux, `os.Executable()` elsewhere), compare to embedded value; fail if tampered
5. [ ] Implement periodic integrity check — background goroutine re-verifies binary hash every 5 minutes during long sessions (autonomous mode); logs tampering events to telemetry
6. [ ] Set up Homebrew tap repository — create `homebrew-tap` GitHub repo with stable formula; create `homebrew-tap-unstable` for alpha/beta/RC
7. [ ] Create Scoop manifest — `deploy/cli/scoop/claude-kit.json` for Windows distribution via Scoop bucket
8. [ ] Implement self-update command — `apps/cli/cmd/update.go` that checks GitHub Releases API for latest version matching the current channel, downloads, verifies checksum, and replaces the running binary
9. [ ] Implement channel detection — determine current channel from binary version string (e.g., `v1.0.0-alpha.1` → alpha, `v1.0.0` → stable)
10. [ ] Implement version embedding — use `go build -ldflags` to embed version, commit hash, build date, and channel at compile time
8. [ ] Create installer script — `deploy/cli/install.sh` that detects OS/arch, downloads the correct binary from GitHub Releases, and places it in `~/.local/bin/`
9. [ ] Create CI workflow for CLI releases — `.github/workflows/release-cli.yml` triggered by `v*.*.*` tags; runs GoReleaser, publishes to GitHub Releases, updates Homebrew formula
10. [ ] Create CI workflow for pre-releases — same workflow detects pre-release tags (`-alpha.*`, `-beta.*`, `-rc.*`) and publishes to unstable tap
11. [ ] Write E2E distribution test — download a snapshot build, verify binary runs on the target platform, verify `claude-kit version` outputs correct info

## Files to Create/Modify

### Create
- `deploy/cli/.goreleaser.yml` — GoReleaser configuration
- `deploy/cli/install.sh` — one-line installer script
- `deploy/cli/homebrew/claude-kit.rb.tmpl` — Homebrew formula template (GoReleaser renders this)
- `deploy/cli/scoop/claude-kit.json` — Scoop manifest
- `apps/cli/cmd/update.go` — self-update logic
- `.github/workflows/release-cli.yml` — CLI release pipeline

### Modify
- `internal/version/version.go` — add `Channel()`, `IsPreRelease()`, `CheckLatest()` functions
- `apps/cli/cmd/root.go` — embed version/commit/date via ldflags
- `.github/workflows/push.yml` — add `go build` and `go test` steps alongside existing checks

## Acceptance Criteria

- [ ] `goreleaser release --snapshot --clean` produces 5 platform binaries (darwin/arm64, darwin/amd64, linux/arm64, linux/amd64, windows/amd64)
- [ ] Release binaries are obfuscated with garble (`-literals -tiny` flags)
- [ ] `claude-kit version` shows version, commit, build date, and channel
- [ ] `claude-kit update` downloads and replaces the binary when a newer version exists
- [ ] `claude-kit update` is a no-op when already on latest
- [ ] Pre-release tags (`v1.0.0-alpha.1`) create GitHub pre-releases (not marked as latest)
- [ ] Stable tags (`v1.0.0`) create GitHub releases marked as latest
- [ ] `curl -sSL https://get.claude-kit.dev | bash` installs the correct binary for the current platform
- [ ] Binary checksums are published alongside releases (SHA256)
- [ ] The installer script requires no dependencies beyond `curl` and `tar`

## Dependencies

- Requires: Phase 01 (need compiled Go binary to distribute)
- Blocks: None directly (other phases don't depend on distribution being live)
