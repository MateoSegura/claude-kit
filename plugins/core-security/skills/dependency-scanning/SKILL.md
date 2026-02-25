---
name: core-security:dependency-scanning
description: "Supply chain security, SCA tooling concepts, SBOM basics, vulnerability severity assessment, and dependency update strategies"
user-invocable: false
---

# Dependency Scanning Quick Reference

## Why Dependencies Matter

Modern applications are 70-90% third-party code. A single vulnerable dependency can compromise your entire application. Supply chain attacks deliberately target popular packages to reach downstream consumers.

## Supply Chain Attack Vectors

| Vector | Description | Example |
|--------|-------------|---------|
| Typosquatting | Malicious package with a similar name | `colors` vs `colour` |
| Dependency confusion | Private package name claimed on public registry | Internal `utils` overridden by public `utils` |
| Account takeover | Maintainer account compromised | Attacker publishes backdoored version |
| Malicious maintainer | Trusted maintainer goes rogue | Intentional backdoor in popular package |
| Build system compromise | CI/CD pipeline tampered with | Modified build artifacts |
| Protestware | Maintainer adds disruptive code intentionally | Code that corrupts data for specific locales |

## SCA Tools Overview

**Software Composition Analysis (SCA)** tools scan your dependency tree for known vulnerabilities.

### Built-in Package Manager Tools

| Ecosystem | Command | What It Does |
|-----------|---------|-------------|
| npm/Node | `npm audit` | Scans `node_modules` against npm advisory DB |
| pip/Python | `pip-audit` | Scans installed packages against OSV/PyPI |
| Go | `govulncheck ./...` | Scans Go modules against Go vulnerability DB |
| Rust | `cargo audit` | Scans Cargo.lock against RustSec advisory DB |
| Ruby | `bundle audit` | Scans Gemfile.lock against ruby-advisory-db |

### Third-Party Tools

| Tool | Type | Key Features |
|------|------|-------------|
| Dependabot | GitHub-native | Auto-PRs for updates, security alerts |
| Snyk | SaaS + CLI | Deep scanning, fix suggestions, license checks |
| Trivy | Open source | Containers, filesystems, IaC, SBOM |
| Grype | Open source | Vulnerability scanner for containers and filesystems |
| OWASP Dependency-Check | Open source | Java-focused but supports multiple ecosystems |
| Socket | SaaS | Behavior analysis, detects supply chain attacks |

## Vulnerability Severity (CVSS)

**Common Vulnerability Scoring System** rates vulnerabilities 0.0-10.0:

| Score | Severity | Typical Response |
|-------|----------|-----------------|
| 9.0-10.0 | Critical | Patch immediately, consider hotfix deployment |
| 7.0-8.9 | High | Patch within days, prioritize in current sprint |
| 4.0-6.9 | Medium | Patch within weeks, schedule in next sprint |
| 0.1-3.9 | Low | Patch when convenient, batch with other updates |

**Context matters:** A critical CVE in a dev-only dependency is less urgent than a medium CVE in a production-facing library that handles user input.

**Factors that increase real-world risk:**
- Dependency is exposed to untrusted input
- Vulnerability has a public exploit
- Dependency runs with elevated privileges
- No compensating controls exist

## SBOM Basics

**Software Bill of Materials** — a machine-readable inventory of all components in your software.

**Formats:**
- **SPDX** — Linux Foundation standard (ISO/IEC 5962:2021)
- **CycloneDX** — OWASP standard, security-focused

**Why generate SBOMs:**
- Compliance requirements (US Executive Order 14028)
- Incident response — quickly check if you use an affected component
- License compliance — identify all licenses in your dependency tree
- Vendor transparency — provide to customers

**Generation tools:**
- `syft` — generates SBOM from containers and filesystems
- `cdxgen` — CycloneDX generator for multiple ecosystems
- `spdx-sbom-generator` — SPDX format generator
- Most CI/CD platforms now support SBOM generation natively

## Update Strategies

### Automated Updates

```
Dependabot / Renovate Bot
  |
  v
Auto-PR with version bump
  |
  v
CI runs tests on PR
  |
  v
Human reviews + merges
```

**Configuration tips:**
- Group minor/patch updates to reduce PR noise
- Auto-merge patch updates if CI passes (after initial trust period)
- Pin major versions, review major bumps manually
- Schedule update checks (weekly for non-security, immediate for security)

### Manual Update Workflow

1. Run `npm audit` / `pip-audit` / ecosystem equivalent
2. Review findings — severity, exploitability, affected code paths
3. Update dependency: `npm update <pkg>` or pin specific version
4. Run full test suite
5. Deploy to staging, verify
6. Deploy to production

### Lock File Hygiene

- Always commit lock files (`package-lock.json`, `poetry.lock`, `go.sum`, `Cargo.lock`)
- Lock files ensure reproducible builds and prevent surprise updates
- Review lock file changes in PRs — unexpected dependency changes may indicate compromise
- Regenerate lock files periodically to pick up transitive dependency updates

## Pre-commit Security Scanning

Integrate dependency checks into your development workflow:

```yaml
# Example: GitHub Actions
- name: Audit dependencies
  run: npm audit --audit-level=high
```

Fail the build on high/critical vulnerabilities. Allow manual override for false positives with documented justification.

## Additional Resources

For detailed tool configuration guides, SBOM generation workflows, and ecosystem-specific scanning patterns, see [scanning-reference.md](scanning-reference.md).
