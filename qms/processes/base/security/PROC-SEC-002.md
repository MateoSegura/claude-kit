# PROC-SEC-002: Vulnerability Management

**Version:** 1.0.0
**Status:** draft
**Category:** security
**Layer:** base
**Maturity:** initial
**Owner:** Security Lead
**Last Reviewed:** 2026-02-28

## 1. Purpose

Vulnerability Management establishes a systematic approach to identifying, assessing, and remediating security vulnerabilities in claude-kit's codebase, dependencies, and distribution infrastructure. claude-kit has a deliberately minimal attack surface -- the CLI uses only Python standard library modules, and plugin content is encrypted at rest -- but this does not eliminate vulnerability risk. The devcontainer image includes system packages, the CI pipeline relies on GitHub Actions runners, and the encryption implementation itself requires ongoing assessment. This process ensures that vulnerabilities are found proactively rather than discovered by adversaries.

## 2. Scope

**Included:**
- Vulnerability scanning of the claude-kit CLI (Python source analysis)
- Dependency analysis for the devcontainer image (Dockerfile packages)
- Cryptographic implementation review (AES-256-CBC via OpenSSL)
- GitHub Actions workflow security assessment
- Software Bill of Materials (SBOM) generation and maintenance
- Severity assessment and remediation tracking for discovered vulnerabilities
- Monitoring of security advisories for all runtime dependencies

**Excluded:**
- End-user environment vulnerabilities (customer-side Claude Code installation)
- Anthropic API security (supplier responsibility, monitored via PROC-ORG-005)
- Penetration testing (would require a separate engagement scope)

## 3. Entry Criteria

- [ ] A scheduled vulnerability scan interval has arrived (monthly)
- [ ] A security advisory has been published for a runtime dependency (python3, openssl, git, jq, etc.)
- [ ] A new dependency has been added to the devcontainer image
- [ ] The encryption implementation has been modified
- [ ] A security incident has been reported (triggering immediate assessment)

## 4. Inputs

| Input | Source | Format |
|-------|--------|--------|
| Python source code | claude-kit CLI file | Single Python file |
| Devcontainer Dockerfile | .devcontainer/Dockerfile | Dockerfile |
| CI workflow definitions | .github/workflows/*.yml | YAML |
| Encryption scripts | scripts/encrypt-plugins.sh | Bash script |
| Security advisories | CVE databases, GitHub Dependabot, OpenSSL advisories | Advisory notices |
| Previous SBOM | Previous scan output | JSON or Markdown |
| Risk register | PROC-ORG-004 outputs | Risk entries related to security |

## 5. Activities

### 5.1 Vulnerability Scanning

Execute monthly scans across three domains:

**Python CLI scanning:**
Run static analysis on the claude-kit file. Since the CLI uses only stdlib, focus on:
- Insecure use of subprocess (command injection vectors)
- Path traversal vulnerabilities in plugin directory handling
- Insecure temporary file creation
- Hardcoded credentials or key material (should only exist in _get_key())

**Container image scanning:**
Scan the devcontainer image for known vulnerabilities in installed packages. Use Trivy or a similar scanner against the published image ghcr.io/mateosegura/dev-env-claude-kit:latest. Focus on critical and high severity findings in OS packages, Python runtime, and system tools (openssl, git, jq).

**CI/CD workflow scanning:**
Review GitHub Actions workflows for:
- Use of third-party actions with unpinned versions (should pin to SHA)
- Secrets exposure in workflow logs
- Overly permissive GITHUB_TOKEN scopes
- Self-hosted runner security posture

### 5.2 SBOM Generation

Maintain a Software Bill of Materials documenting all components:

**CLI components:** Python stdlib modules used (enumerate via import analysis).
**Container components:** All packages installed in the Dockerfile (extract from apt-get install commands and tool installations).
**CI components:** All GitHub Actions used across workflows (extract action references).
**Runtime tools:** All system-level tools required (python3, openssl, git, jq, claude, gh, node).

Update the SBOM when any component is added, removed, or updated.

### 5.3 Severity Assessment

For each discovered vulnerability, assess severity using CVSS as a reference framework:

| Severity | CVSS Range | Response Time | Example |
|----------|-----------|---------------|---------|
| Critical | 9.0-10.0 | 24 hours | Remote code execution in openssl, key material exposure |
| High | 7.0-8.9 | 7 days | Command injection in CLI, container escape in devcontainer |
| Medium | 4.0-6.9 | 30 days | Denial of service in validation scripts, information disclosure |
| Low | 0.1-3.9 | Next release | Non-exploitable findings, theoretical vulnerabilities |

Consider claude-kit-specific context: a vulnerability in the encryption path is always elevated by one severity level because it directly threatens the product's trust model.

### 5.4 Remediation Tracking

For each vulnerability requiring remediation:

1. Create a GitHub Issue with the security label
2. Assign an owner and target remediation date based on severity
3. Implement the fix following standard development workflow (branch, PR, CI validation)
4. Verify the fix resolves the vulnerability (re-scan)
5. Close the issue with a note referencing the fixing commit

Track remediation status using GitHub Issues as the tracking mechanism.

### 5.5 Advisory Monitoring

Subscribe to security advisory channels for all runtime dependencies:

- **OpenSSL:** openssl-announce mailing list (critical for encryption)
- **Python:** python-security-announce (CLI runtime)
- **Ubuntu:** ubuntu-security-announce (devcontainer base image)
- **GitHub Actions:** GitHub security advisories (CI/CD)
- **Docker:** Moby project security advisories (devcontainer runtime)

When an advisory is received, assess applicability to claude-kit within 48 hours.

## 6. Outputs / Artifacts

| Artifact | Directory | Template | ID Pattern |
|----------|-----------|----------|------------|
| Vulnerability scan reports | qms/ or internal tracking | -- | -- |
| SBOM | qms/ or project root | -- | -- |
| Remediation issues | GitHub Issues with security label | -- | -- |
| Security advisory assessments | Internal documentation | -- | -- |

## 7. Exit Criteria

- [ ] Monthly scan completed across all three domains (CLI, container, CI/CD)
- [ ] All discovered vulnerabilities assessed for severity and applicability
- [ ] Critical and high vulnerabilities have remediation plans with assigned owners
- [ ] SBOM updated to reflect current component inventory
- [ ] Scan results documented and dated

## 8. Quality Gates

| Gate | Verification Method | Pass Criteria |
|------|-------------------|---------------|
| Scan coverage | Verify all three scan domains were executed | CLI, container image, and CI/CD workflows all scanned within the reporting period |
| Remediation timeliness | Check vulnerability age against severity response times | No critical vulnerability open longer than 24 hours; no high vulnerability open longer than 7 days |
| SBOM accuracy | Cross-reference SBOM with actual Dockerfile and CLI imports | No undocumented components; all versions current |
| Zero known critical | Pre-release check | No open critical vulnerabilities at release time |

## 9. Roles and Responsibilities

| Role | Responsibility |
|------|---------------|
| Security Lead | Owns the vulnerability management program; conducts severity assessments; manages advisory monitoring |
| DevOps Lead | Executes container image scans; updates Dockerfile when remediation requires package updates |
| Developer | Remediates CLI vulnerabilities; reviews CI/CD workflow security |
| Technical Lead | Approves severity assessments and remediation timelines; escalates critical findings |

## 10. Metrics

| Metric | Description | Target | Collection Method |
|--------|-------------|--------|------------------|
| Scan compliance rate | Percentage of months with completed scans across all domains | 100% | Track scan execution dates |
| Mean time to remediate (MTTR) | Average time from vulnerability discovery to fix merged | Less than 72 hours for critical, less than 14 days for high | GitHub Issue timestamps |
| Open vulnerability count | Number of unresolved vulnerabilities by severity | 0 critical, fewer than 3 high | Audit GitHub Issues with security label |
| SBOM currency | Time since last SBOM update | Less than 30 days | Check SBOM modification date |

## 11. Standards Alignment

| Standard | Clause/Control | Relationship |
|----------|---------------|-------------|
| NIST SP 800-218 | RV.1 | Identify and confirm vulnerabilities on an ongoing basis |
| NIST SP 800-218 | RV.2 | Assess, prioritize, and remediate vulnerabilities |
| NIST SP 800-218 | RV.3 | Analyze vulnerabilities to identify root causes |
| ISO 27001 | A.12.6 | Technical vulnerability management |
| CMMC | RM.2.142 | Scan for vulnerabilities periodically and when new vulnerabilities are identified |
| NIST SP 800-53 | RA-5 | Vulnerability scanning |

## 12. Tailoring Guidance

**Minimum viable process (solo developer):** Run container image scan quarterly instead of monthly. Skip formal SBOM generation -- maintain a mental inventory of dependencies (which is small given stdlib-only policy). Monitor OpenSSL advisories manually. Focus scanning on the encryption code path and Dockerfile.

**Full ceremony (team targeting defense/federal):** Execute all activities at prescribed frequencies. Automate scanning via a scheduled CI job. Maintain a machine-readable SBOM (SPDX or CycloneDX format). Integrate with PROC-GOV-004 (Supply Chain Assurance) for government-specific supply chain vulnerability requirements.

**When to simplify:** If a release contains only documentation or process changes (no CLI, Dockerfile, or workflow modifications), skip the monthly scan for that period. Resume scanning on the next release that touches code or infrastructure.

## 13. Related Processes

| Process | Relationship |
|---------|-------------|
| PROC-SEC-001 | Related: secure development practices reduce vulnerability introduction |
| PROC-SEC-003 | Escalates to: exploited vulnerabilities trigger security incident response |
| PROC-SEC-005 | Related: encryption implementation vulnerabilities are highest priority |
| PROC-ORG-004 | Feeds into: vulnerability findings update the risk register |
| PROC-ORG-005 | Related: supplier vulnerabilities (OpenSSL, Python) require supplier coordination |
| PROC-LC-006 | Gate: no critical open vulnerabilities at release time |

## 14. Traces

- **Governs:** Vulnerability scan results, SBOM, remediation tracking (GitHub Issues with security label)
- **Enforced by:** Monthly scan schedule (manual trigger); pre-release security check (planned automation)
- **Related QA:** Minimal attack surface, encryption integrity, supply chain security

## 15. Change History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 2026-02-28 | Mateo Segura | Initial release -- formalizes vulnerability scanning for CLI, container, and CI/CD domains |
