# PROC-GOV-004: Supply Chain Assurance

**Version:** 1.0.0
**Status:** draft
**Category:** compliance
**Layer:** gov
**Maturity:** initial
**Owner:** Security Lead
**Last Reviewed:** 2026-02-28

## 1. Purpose

Establish supply chain risk management practices for claude-kit to meet federal software supply chain requirements. Executive Order 14028 and NIST 800-218 (SSDF) mandate that software sold to the federal government includes provenance tracking, vulnerability disclosure, and a Software Bill of Materials (SBOM). This process ensures claude-kit's supply chain is transparent, auditable, and resistant to tampering.

## 2. Scope

This process covers supply chain assurance for:
- The claude-kit CLI (single-file Python application)
- All plugins distributed through the encrypted plugin pipeline
- Third-party dependencies (runtime tools: python3, openssl, git, jq, gh, claude)
- The Anthropic Claude API as a critical supplier
- Development toolchain components (devcontainer image, CI/CD pipeline)
- Scripts and validation tooling in the repository

Excluded:
- Customer-side supply chain management
- Hardware supply chain (servers, network equipment) — covered by cloud provider (AWS, Azure)

## 3. Entry Criteria

- [ ] PROC-ORG-005 (Supplier Management) base process is established
- [ ] PROC-SEC-002 (Vulnerability Management) base process is established
- [ ] Software inventory of all components is cataloged
- [ ] Anthropic supplier risk assessment is complete
- [ ] SBOM generation tooling is selected and configured

## 4. Inputs

| Input | Source | Format |
|-------|--------|--------|
| NIST SP 800-218 (SSDF) | NIST | PDF / structured data |
| EO 14028 self-attestation requirements | CISA | Guidance document |
| Component inventory | Engineering team | Spreadsheet / SBOM tool |
| Anthropic service agreement and SOC 2 report | Anthropic / Legal | PDF |
| Vulnerability feeds (NVD, GitHub Advisories) | NIST NVD, GitHub | API / feeds |
| QA-006 (Supply Chain Security) | docs/quality/ | Markdown |

## 5. Activities

### 5.1 SBOM Generation

Generate a Software Bill of Materials for every release of claude-kit:

**CLI component:** Since claude-kit is a single-file Python application with stdlib-only dependencies, the SBOM is minimal but must still document:
- Python version requirement
- Standard library modules used
- Runtime tool dependencies (openssl, git, jq, gh, claude) with version constraints

**Plugin components:** For each encrypted plugin bundle:
- List all files included in the bundle
- Document any external references (API endpoints, companion dependencies)
- Record the encryption method and integrity verification approach

**Container image:** For the devcontainer:
- Generate SBOM from the Docker image layers
- Include all installed packages (apt, pip, npm, go modules)
- Use Syft, Trivy, or equivalent SBOM generation tool

Produce SBOMs in both SPDX and CycloneDX formats. Attach SBOMs to each GitHub Release.

### 5.2 Supplier Risk Assessment

Assess risk for each supplier in the claude-kit supply chain:

| Supplier | Risk Area | Assessment Method |
|----------|-----------|-------------------|
| Anthropic (Claude API) | AI model availability, data handling, security | SOC 2 review, DPA review, API SLA analysis |
| GitHub (hosting, CI) | Code integrity, availability, access control | SOC 2 review, GitHub security posture |
| Docker Hub / GHCR | Container image integrity, availability | Image signing verification, registry security |
| Ubuntu (base image) | OS vulnerabilities, patching cadence | CVE tracking, LTS support timeline |
| Python (runtime) | Language vulnerabilities, supply chain attacks | CPython security advisories, PSF governance |

For each supplier:
- Review available certifications (SOC 2, ISO 27001, FedRAMP)
- Assess single points of failure and availability SLAs
- Document data flows between claude-kit and the supplier
- Establish monitoring for supplier security incidents
- Define contingency plans for supplier disruption

### 5.3 Provenance Tracking

Implement provenance controls throughout the build and distribution pipeline:

**Source code provenance:**
- All commits are signed (GPG or SSH key signatures)
- Branch protection requires PR review before merge
- CI/CD pipeline records build provenance (GitHub Actions attestations)

**Build provenance:**
- Record the exact commit SHA, build timestamp, and runner environment for each release
- Generate SLSA (Supply-chain Levels for Software Artifacts) provenance attestations at Level 2 minimum
- Attach provenance metadata to release artifacts

**Distribution provenance:**
- Encrypted plugin bundles include integrity hashes (SHA-256)
- The `claude-kit update` command verifies bundle integrity before decryption
- Distribution channel uses TLS 1.2+ for all transfers

### 5.4 Third-Party Code Review

For any new dependency or tool introduced into the build or runtime environment:

1. **Justification:** Document why the dependency is needed and confirm no stdlib alternative exists
2. **Security review:** Check the dependency against known vulnerabilities (NVD, GitHub Advisories)
3. **License review:** Confirm license compatibility (MIT, Apache 2.0, BSD preferred; GPL requires legal review)
4. **Maintenance assessment:** Verify active maintenance (commits in last 6 months, responsive to security issues)
5. **Approval:** Security Lead and Engineering Lead must both approve

For existing dependencies, repeat the security and maintenance assessment quarterly.

### 5.5 Vulnerability Monitoring and Response

Establish continuous monitoring for supply chain vulnerabilities:
- Subscribe to NVD feeds for all runtime dependencies
- Enable Dependabot or equivalent for the repository
- Monitor Anthropic's status page and security advisories
- Scan the devcontainer image weekly for new CVEs
- Define SLAs for vulnerability response by severity:
  - Critical: patch within 24 hours
  - High: patch within 7 days
  - Medium: patch within 30 days
  - Low: patch within 90 days

### 5.6 EO 14028 Self-Attestation

Prepare the self-attestation required for federal software procurement:
- Confirm adherence to NIST SSDF practices
- Document secure development practices (code review, testing, CI/CD controls)
- Attest to SBOM availability and vulnerability disclosure practices
- Submit attestation through the designated federal portal
- Renew attestation annually or upon significant changes

## 6. Outputs / Artifacts

| Artifact | Directory | Template | ID Pattern |
|----------|-----------|----------|------------|
| SBOM (SPDX format) | GitHub Release attachment | — | — |
| SBOM (CycloneDX format) | GitHub Release attachment | — | — |
| Supplier Risk Assessment | `qms/artifacts/gov/` | — | GOV-SRA-XXX |
| SLSA Provenance Attestation | GitHub Release attachment | — | — |
| EO 14028 Self-Attestation | `qms/artifacts/gov/` | — | GOV-ATTEST-XXX |
| Third-Party Code Review Record | `qms/artifacts/gov/` | — | GOV-TPR-XXX |

## 7. Exit Criteria

- [ ] SBOM generation is automated in the release pipeline
- [ ] All suppliers have documented risk assessments
- [ ] Provenance tracking is implemented for source, build, and distribution
- [ ] Vulnerability monitoring is active for all dependencies
- [ ] EO 14028 self-attestation is prepared and filed
- [ ] Third-party code review process is documented and operational

## 8. Quality Gates

| Gate | Verification Method | Pass Criteria |
|------|-------------------|---------------|
| SBOM completeness | Cross-reference SBOM with actual dependencies | 100% of dependencies captured in both formats |
| Supplier assessment coverage | Audit supplier list vs. assessment records | All critical suppliers assessed within last 12 months |
| Provenance verification | Verify SLSA attestation on latest release | Attestation validates and matches release artifacts |
| Vulnerability SLA compliance | Audit open vulnerabilities vs. SLA timelines | Zero SLA breaches for critical/high severity |
| Self-attestation review | Legal and CISO review | Attestation is accurate and complete |

## 9. Roles and Responsibilities

| Role | Responsibility |
|------|---------------|
| Security Lead | Owns supply chain risk program, conducts supplier assessments, defines vulnerability SLAs |
| Engineering Lead | Implements SBOM generation, provenance tracking, dependency management |
| DevOps Lead | Automates SBOM in CI/CD, maintains container scanning, configures Dependabot |
| Legal Counsel | Reviews supplier agreements, license compliance, EO 14028 attestation |
| Compliance Officer | Tracks supplier assessment cadence, maintains records, files attestations |

## 10. Metrics

| Metric | Description | Target | Collection Method |
|--------|-------------|--------|------------------|
| SBOM currency | Releases with attached SBOMs | 100% | GitHub Release audit |
| Supplier assessment coverage | Suppliers assessed within last 12 months | 100% | Assessment register |
| Vulnerability response time | Time from disclosure to patch by severity | Within SLA | Vulnerability tracker |
| Dependency freshness | Dependencies with known vulnerabilities | 0 critical/high unpatched | Dependabot / scanner |
| Provenance coverage | Releases with SLSA attestations | 100% | CI/CD audit |

## 11. Standards Alignment

| Standard | Clause/Control | Relationship |
|----------|---------------|-------------|
| EO 14028 | Section 4 (Enhancing Software Supply Chain Security) | Primary federal mandate |
| NIST SP 800-218 | SSDF practices (PO, PS, PW, RV) | Secure development framework |
| NIST SP 800-161 Rev 1 | Supply Chain Risk Management | Comprehensive SCRM guidance |
| SLSA Framework | Levels 1–4 | Build provenance and integrity |
| NTIA SBOM Minimum Elements | All fields | SBOM content requirements |
| CISA Secure by Design | Pledge elements | Voluntary commitment framework |
| CMMC 2.0 | SR (System and Information Integrity) domain | Supply chain controls for DIB |

## 12. Tailoring Guidance

**Minimal viable (non-federal customers):**
- Generate SBOM for releases (Activity 5.1) — increasingly expected by enterprise customers
- Conduct supplier risk assessment for Anthropic only (the critical supplier)
- Skip EO 14028 self-attestation
- Vulnerability monitoring with relaxed SLAs (7/30/90/180 days)

**Federal (EO 14028 compliance):**
- Execute all activities as written
- SBOM in both SPDX and CycloneDX formats
- SLSA Level 2 provenance minimum
- Self-attestation required before procurement

**DoD / CMMC environments:**
- All federal requirements plus CMMC SR domain controls
- Supplier assessments must include CMMC flow-down requirements
- Third-party code review must be documented to CMMC evidence standards
- Coordinate with PROC-GOV-001 for CMMC-specific supply chain practices

**Air-gapped environments:**
- SBOM must be included in the offline distribution package
- Vulnerability updates require manual media transfer process
- Coordinate with PROC-GOV-011 for offline update procedures

## 13. Related Processes

| Process | Relationship |
|---------|-------------|
| PROC-ORG-005 | Extends — supply chain assurance builds on base supplier management |
| PROC-SEC-002 | Extends — vulnerability management feeds supply chain monitoring |
| PROC-GOV-001 | Related — CMMC SR domain requires supply chain controls |
| PROC-GOV-002 | Related — FedRAMP requires supply chain risk management plan |
| PROC-GOV-003 | Related — export controls apply to supply chain partners |
| PROC-GOV-011 | Related — air-gapped deployment requires offline SBOM distribution |
| PROC-LC-006 | Related — release process must generate and attach SBOMs |

## 14. Traces

- **Governs:** SBOM artifacts, supplier risk assessments, provenance attestations, EO 14028 self-attestation
- **Enforced by:** Automated SBOM generation in CI/CD, quarterly supplier review cadence, Dependabot alerts
- **Related QA:** QA-006 (Supply Chain Security)

## 15. Change History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 2026-02-28 | Mateo Segura | Initial release |
