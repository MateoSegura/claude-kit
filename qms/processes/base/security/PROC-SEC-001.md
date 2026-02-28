# PROC-SEC-001: Secure Development

**Version:** 1.0.0
**Status:** draft
**Category:** security
**Layer:** base
**Maturity:** initial
**Owner:** Security Lead
**Last Reviewed:** 2026-02-28

## 1. Purpose

Secure Development governs how security is built into claude-kit's development lifecycle rather than added after the fact. This process formalizes the stdlib-only dependency policy, hook-based runtime enforcement, CI-driven security validation, and the prohibition on third-party runtime dependencies that together minimize the attack surface of the CLI and its plugins. Security is a design constraint, not an afterthought.

## 2. Scope

**Included:**
- Secure coding standards for the Python CLI and shell scripts
- Dependency management policy (stdlib only, no third-party runtime imports)
- Hook-based enforcement of security rules at commit and runtime
- CI validation of security-relevant properties (no credential leaks, correct encryption usage)
- Security-aware code review practices
- Key protection rules for the split-key encryption pattern

**Excluded:**
- Encryption implementation details (governed by PROC-SEC-005)
- Vulnerability scanning and disclosure (governed by PROC-SEC-002 when written)
- Access control to the repository (governed by PROC-SEC-004 when written)

## 3. Entry Criteria

- [ ] The developer has read `.claude/rules/security.md` and `.claude/rules/code-style.md`
- [ ] The development environment has all required runtime dependencies installed
- [ ] The encryption key assembly function (`_get_key()`) boundaries are understood

## 4. Inputs

| Input | Source | Format |
|-------|--------|--------|
| Security rules | `.claude/rules/security.md` | Markdown rule file |
| Code style rules | `.claude/rules/code-style.md` | Markdown rule file |
| Plugin conventions | `.claude/rules/plugin-conventions.md` | Markdown rule file |
| Hook definitions | `plugins/*/hooks/hooks.json` | JSON hook configuration |
| CI workflow definitions | `.github/workflows/*.yml` | YAML workflow files |

## 5. Activities

### 5.1 Enforce Stdlib-Only Policy

The `claude-kit` CLI has zero third-party runtime dependencies by design. Every import must come from the Python standard library. This eliminates supply chain attacks, version conflicts, and transitive dependency risks.

Before adding any import, verify it exists in the stdlib: `python3 -c "import <module>"` on a clean Python installation. If a capability requires an external library, find the stdlib equivalent or restructure the approach. This policy is non-negotiable.

Runtime tools that must be available in the environment (`python3`, `openssl`, `git`, `jq`, `claude`, `gh`) are system-level executables, not Python packages.

### 5.2 Protect Key Material

The encryption passphrase is assembled at runtime from split parts inside the `_get_key()` function in the CLI. The following rules are absolute:

- **Never** log, print, or expose the assembled key value in any output
- **Never** commit the assembled key as a single string anywhere in the repo
- **Never** modify `_get_key()` without explicit authorization from the repo owner
- **Never** include the key or any part of it in PR descriptions, commit messages, comments, or CI logs

If key material is encountered outside `_get_key()`, treat it as a security incident and halt.

### 5.3 Apply Secure Coding Patterns

For Python code:
- Use `pathlib.Path` for all filesystem operations (avoids path traversal via string manipulation)
- Use `subprocess.run()` with explicit argument lists (avoids shell injection)
- Never use `eval()`, `exec()`, or `__import__()` on user-controlled input
- Validate all CLI input before processing

For shell scripts:
- Always start with `set -euo pipefail` (catches undefined variables and pipe failures)
- Always quote all variables (`"$var"` not `$var`)
- Use `$(...)` command substitution (avoids backtick nesting issues)
- Use `${CLAUDE_PLUGIN_ROOT}` for plugin-relative paths (avoids hardcoded absolute paths)

### 5.4 Review Security-Sensitive Changes

During peer review (PROC-SP-006), the reviewer must specifically check for:
- New imports that are not from stdlib
- Changes to `_get_key()` or any encryption-related code
- Hardcoded paths, credentials, or tokens
- `.env` files or credential files in the commit
- New runtime dependencies or package manager configuration
- Use of `eval()`, `exec()`, or dynamic code execution
- Unquoted shell variables or missing `set -euo pipefail`

### 5.5 Hook-Based Runtime Enforcement

Plugins use hooks (defined in `hooks/hooks.json`) to enforce rules at specific events. Security-relevant hooks include:
- Pre-commit hooks that validate file structure
- Runtime hooks that check for prohibited patterns
- Post-process hooks that verify output compliance

Hook scripts must use `${CLAUDE_PLUGIN_ROOT}` for paths and follow the same secure coding patterns as all other shell scripts.

### 5.6 Prevent Credential Leaks

The following files must never be committed:
- `.env` files (gitignored via `.gitignore`)
- `credentials.json`, `*.key`, `*.pem` files
- Any file containing API keys, tokens, or secrets

The `.devcontainer/.env` file is required for development but is gitignored. It must not be referenced in committed code except via environment variable reads.

## 6. Outputs / Artifacts

| Artifact | Directory | Template | ID Pattern |
|----------|-----------|----------|------------|
| Secure code | `claude-kit`, `scripts/`, `plugins/*/scripts/` | — | — |
| Security-reviewed PRs | GitHub PR reviews | — | — |
| Hook enforcement scripts | `plugins/*/scripts/` | — | — |

## 7. Exit Criteria

- [ ] All code uses stdlib-only imports (no third-party runtime dependencies)
- [ ] No credential material exists in committed files
- [ ] Shell scripts use `set -euo pipefail` and quoted variables
- [ ] Security-sensitive changes have been specifically reviewed
- [ ] `_get_key()` has not been modified without authorization

## 8. Quality Gates

| Gate | Verification Method | Pass Criteria |
|------|-------------------|---------------|
| Dependency audit | `python3 -m py_compile claude-kit` + manual import review | Only stdlib imports present |
| Credential scan | Code review of committed files | No secrets, tokens, keys, or `.env` files in repository |
| Shell script hardening | Code review of `scripts/*.sh` and `plugins/*/scripts/*.sh` | All scripts start with `set -euo pipefail`, all variables quoted |
| Key protection | Code review of any change touching encryption code | `_get_key()` unchanged or change explicitly authorized |

## 9. Roles and Responsibilities

| Role | Responsibility |
|------|---------------|
| Security Lead | Maintains security rules, reviews encryption changes, approves key modifications |
| Developer | Follows secure coding standards, uses stdlib-only imports, quotes shell variables |
| Reviewer | Checks for credential leaks, dependency additions, and security anti-patterns during PR review |
| CI System | Validates Python syntax (catches import errors for non-existent modules) |

## 10. Metrics

| Metric | Description | Target | Collection Method |
|--------|-------------|--------|------------------|
| Third-party dependency count | Number of non-stdlib runtime imports in the CLI | 0 | `grep import claude-kit` audit, excluding stdlib modules |
| Credential leak incidents | Number of times a secret was committed and needed rotation | 0 | Git history audit |
| Shell script hardening compliance | Percentage of shell scripts with `set -euo pipefail` | 100% | `grep -L "set -euo pipefail" scripts/*.sh plugins/*/scripts/*.sh` |
| Key modification events | Number of changes to `_get_key()` per quarter | 0 (unless key rotation planned) | Git log for the function |

## 11. Standards Alignment

| Standard | Clause/Control | Relationship |
|----------|---------------|-------------|
| ISO/IEC 12207:2017 | 6.3.7 Information Security Management | This process implements security management for development |
| ISO/IEC 27001:2022 | A.8.25 Secure Development Lifecycle | Activities 5.1-5.6 implement secure development lifecycle controls |
| CMMI-DEV v2.0 | TS (Technical Solution) | Security constraints are part of technical solution design |
| NIST SP 800-218 (SSDF) | PO.1 (Define Security Requirements) | Stdlib-only policy and key protection rules define security requirements |

## 12. Tailoring Guidance

**Minimum viable process (non-security change):** For changes that do not touch encryption, imports, or shell scripts, the standard code review (PROC-SP-006) covers security. No additional security-specific review is needed.

**Full ceremony (encryption or key change):** Any change to `_get_key()`, `encrypt-plugins.sh`, or the encryption/decryption flow in the CLI requires explicit authorization from the repository owner. The PR must be reviewed specifically for key protection compliance.

**New script addition:** Any new shell script must include `set -euo pipefail` and follow the quoting rules. The reviewer must verify this during PR review.

## 13. Related Processes

| Process | Relationship |
|---------|-------------|
| PROC-SEC-005 | Related: Encryption & Key Management implements the encryption that this process protects |
| PROC-SP-006 | Extends: Peer Review includes security-specific review criteria defined here |
| PROC-SP-001 | Related: Configuration Management prevents unauthorized changes via branch protection |
| PROC-LC-004 | Extends: Implementation must follow the secure coding standards defined here |
| PROC-SP-002 | Related: Quality Assurance tracks security compliance as a quality attribute |

## 14. Traces

- **Governs:** `claude-kit` (stdlib-only imports), `scripts/*.sh` (hardened scripts), `plugins/*/scripts/*.sh` (plugin scripts), `plugins/*/hooks/hooks.json` (hook enforcement)
- **Enforced by:** `python3 -m py_compile claude-kit` (import validation), code review practices, `.claude/rules/security.md` (security rules), `.gitignore` (credential exclusion)
- **Related QA:** Security rules in `.claude/rules/security.md`, stdlib-only policy in `.claude/rules/code-style.md`

## 15. Change History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 2026-02-28 | Mateo Segura | Initial release — formalizes existing stdlib-only policy and security coding standards |
