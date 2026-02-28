# PROC-GOV-011: Air-Gap Deployment

**Version:** 1.0.0
**Status:** draft
**Category:** deployment
**Layer:** gov
**Maturity:** initial
**Owner:** DevOps Lead
**Last Reviewed:** 2026-02-28

## 1. Purpose

Define the process for packaging, transferring, deploying, and updating claude-kit in air-gapped (disconnected) environments. Air-gapped networks are common in defense, intelligence, and critical infrastructure contexts where internet connectivity is prohibited. claude-kit's dual deployment architecture (QA-008) requires a complete offline workflow from plugin distribution through AI agent execution.

## 2. Scope

This process covers:
- Offline packaging of claude-kit CLI and encrypted plugins
- Media transfer procedures (burn, verify, transport, import)
- Installation and configuration in air-gapped environments
- Offline update mechanisms for plugins and the CLI
- Integrity verification at every transfer boundary
- AI agent operation without internet connectivity

Included:
- All plugin types (core, team, system)
- The claude-kit CLI binary/script
- AI model access alternatives for air-gapped networks
- Documentation and dependency bundles

Excluded:
- Cloud platform deployment (covered by standard deployment processes)
- Network architecture of the air-gapped environment (customer responsibility)
- Classification guide requirements beyond CUI (separate process for SECRET+)

## 3. Entry Criteria

- [ ] PROC-LC-006 (Release) base process is established
- [ ] PROC-LC-007 (Deployment) base process is established
- [ ] Encryption pipeline (`scripts/encrypt-plugins.sh`) is operational
- [ ] Air-gapped deployment has been architecturally approved (see ADR-008 or equivalent)
- [ ] Target air-gapped environment specifications are documented
- [ ] Media transfer policy for the target environment is understood

## 4. Inputs

| Input | Source | Format |
|-------|--------|--------|
| claude-kit release artifacts | GitHub Release (PROC-LC-006) | Encrypted bundles, CLI script |
| Plugin encryption key material | `_get_key()` in claude-kit CLI | Runtime assembly |
| Target environment specifications | Customer | Environment description document |
| Media transfer policy | Customer security team | Security procedure document |
| QA-008 (Dual Deployment Architecture) | docs/quality/ | Markdown |
| Air-gapped AI model deployment guide | Anthropic (if available) | Documentation |

## 5. Activities

### 5.1 Offline Package Assembly

Create a self-contained offline distribution package:

**Package contents:**

| Component | Source | Purpose |
|-----------|--------|---------|
| `claude-kit` CLI script | Repository root | CLI executable |
| `install.sh` | Repository root | Installer script |
| Encrypted plugin bundles (`content.enc`) | `scripts/encrypt-plugins.sh` output | Plugin content |
| Plugin metadata (`plugin.json`, `ctl.json`) | `plugins/*/` | Plugin loading configuration |
| Runtime dependency checklist | Documentation | Verification guide |
| SHA-256 manifest | Build pipeline | Integrity verification |
| SBOM (SPDX and CycloneDX) | PROC-GOV-004 | Supply chain transparency |
| Offline documentation bundle | `docs/` and plugin READMEs | Reference material |

**Assembly steps:**
1. Build from a tagged release (never from an untagged commit)
2. Run full Tier 1 validation (`validate-plugins.py --all --strict`)
3. Encrypt all plugin content directories
4. Generate SHA-256 hashes for every file in the package
5. Create a manifest file listing all contents with hashes
6. Sign the manifest with the release signing key
7. Archive into a single distribution archive (`.tar.gz`)
8. Compute the archive hash and record it

### 5.2 Media Preparation

Prepare transfer media according to the target environment's security policy:

**Approved media types (typical for DoD/IC):**
- Write-once optical media (CD-R, DVD-R) — most commonly approved
- Hardware-encrypted USB drives (FIPS 140-2 validated)
- Approved file transfer appliances (data diodes)

**Media preparation protocol:**
1. Start with verified-clean media (new, unused)
2. Write the distribution archive to the media
3. Write the SHA-256 manifest and signature to the media separately
4. Verify readback integrity (compare hashes)
5. Label media with: package version, date, classification markings (CUI if applicable), contents summary
6. Log media creation in the media accountability register

**Media accountability:**
- Assign a unique media ID to each piece of transfer media
- Record: media ID, contents, creation date, creator, destination, chain of custody
- Track media through its entire lifecycle: creation → transfer → import → destruction

### 5.3 Media Transfer Procedures

Transfer media from the connected environment to the air-gapped environment:

**Transfer steps:**
1. Media undergoes security review per the facility's media policy
2. Malware scan on the connected side before transfer (if required by facility)
3. Physical transfer through the security boundary (guard, safe, courier)
4. Log the transfer event with: date, time, media ID, transferring party, receiving party
5. Media scan on the air-gapped side before import (if facility has scanning capability)

**Chain of custody:**
- Two-person integrity (TPI) for media transfers when handling CUI
- Signed transfer receipts at each handoff
- Escort media when moving between secure areas

### 5.4 Air-Gap Installation

Install claude-kit in the air-gapped environment:

**Prerequisites verification:**
1. Verify runtime dependencies are available in the air-gapped environment:
   - `python3` (>= 3.8)
   - `openssl` (for decryption)
   - `git` (for version control)
   - `jq` (for JSON parsing)
   - `claude` CLI (must be pre-installed or included in a separate deployment)
2. Verify the Anthropic API alternative (see Activity 5.6)

**Installation steps:**
1. Verify media integrity: recompute SHA-256 hashes and compare against signed manifest
2. Verify manifest signature against the authorized signing key
3. Extract the distribution archive
4. Run `install.sh` (or manual installation per the offline documentation)
5. Verify `claude-kit` CLI is functional: `claude-kit --version`
6. Run `claude-kit update` to decrypt and install plugins
7. Verify plugin loading: `claude-kit validate --all`
8. Document the installation in the environment's change log

### 5.5 Offline Update Mechanism

Update claude-kit in air-gapped environments without internet connectivity:

**Update package creation (connected side):**
1. Create a delta package containing only changed components since the last deployed version
2. Include a version manifest showing old version → new version for each component
3. Include rollback instructions in case the update fails
4. Follow the same packaging, media preparation, and transfer procedures as initial deployment

**Update application (air-gapped side):**
1. Backup current installation before applying update
2. Verify update package integrity (SHA-256 + signature)
3. Apply update using `claude-kit update --offline <path-to-package>`
4. Run post-update validation: `claude-kit validate --all`
5. Verify functionality with a smoke test of key workflows
6. Document the update in the environment's change log with old and new version numbers

**Rollback procedure:**
1. Stop any running claude-kit sessions
2. Restore from the pre-update backup
3. Verify rollback: `claude-kit --version` and `claude-kit validate --all`
4. Document the rollback and reason in the change log
5. Report the update failure for investigation on the connected side

### 5.6 AI Agent Operation in Air-Gapped Environments

Address the unique challenge of AI agent operation without internet connectivity:

**Option 1: On-premise model deployment**
- Deploy a local Claude model instance within the air-gapped enclave
- Requires Anthropic to provide an on-premise model package (enterprise licensing)
- Configure `claude-kit` to point to the local model endpoint
- Model updates follow the same media transfer process as plugin updates

**Option 2: Constrained connectivity (data diode)**
- AI inference requests traverse a one-way data diode to a connected inference endpoint
- Responses return through the diode
- No bidirectional network connectivity — security boundary maintained
- Requires data diode hardware and specific API proxy configuration

**Option 3: Pre-computed responses**
- For knowledge skills (no generation), content is static and requires no model access
- For agent roles requiring generation, this option is not viable

**Configuration:**
- Document the selected option in the environment's deployment configuration
- Update `claude-kit` configuration to use the appropriate model endpoint
- Test AI agent functionality end-to-end before declaring operational readiness

## 6. Outputs / Artifacts

| Artifact | Directory | Template | ID Pattern |
|----------|-----------|----------|------------|
| Offline Distribution Package | Build pipeline output | — | REL-AIR-XXX |
| SHA-256 Manifest (signed) | Package contents | — | — |
| Media Accountability Register | `qms/artifacts/gov/` | — | GOV-MAR-XXX |
| Air-Gap Installation Guide | `qms/artifacts/gov/` | — | GOV-AIG-XXX |
| Offline Update Package | Build pipeline output | — | UPD-AIR-XXX |
| Environment Change Log | Customer environment | — | — |

## 7. Exit Criteria

- [ ] Offline distribution package is assembled with all required components
- [ ] SHA-256 manifest is computed and signed
- [ ] Media is prepared, labeled, and logged in the accountability register
- [ ] Transfer is completed with chain of custody documentation
- [ ] Installation is verified in the air-gapped environment
- [ ] AI agent operation is confirmed with the selected model access option
- [ ] Update mechanism is tested with at least one delta update cycle

## 8. Quality Gates

| Gate | Verification Method | Pass Criteria |
|------|-------------------|---------------|
| Package integrity | SHA-256 hash verification of all files | 100% hash match |
| Manifest signature | Cryptographic signature verification | Valid signature from authorized key |
| Media verification | Readback and hash comparison after burn | 100% match with source |
| Installation verification | `claude-kit validate --all` in target environment | All plugins pass validation |
| Update verification | Post-update validation and smoke test | All plugins pass, key workflows functional |
| AI functionality | End-to-end agent test in air-gapped environment | Agent completes test scenario successfully |

## 9. Roles and Responsibilities

| Role | Responsibility |
|------|---------------|
| DevOps Lead | Owns offline packaging pipeline, creates distribution and update packages |
| Release Manager | Triggers package builds from tagged releases, signs manifests |
| Security Lead | Reviews media transfer procedures, ensures CUI handling compliance |
| Field Engineer | Performs installation and updates in customer air-gapped environments |
| Customer Security Officer | Approves media transfer, provides facility access, reviews change logs |

## 10. Metrics

| Metric | Description | Target | Collection Method |
|--------|-------------|--------|------------------|
| Package integrity rate | Packages passing SHA-256 verification at destination | 100% | Verification logs |
| Media accountability | Media items with complete chain of custody | 100% | Media register audit |
| Installation success rate | First-attempt successful installations | >= 90% | Installation logs |
| Update cycle time | Days from release to air-gapped deployment | <= 30 days for security updates | Release and deployment timestamps |
| Rollback incidents | Updates requiring rollback | < 5% | Change log review |

## 11. Standards Alignment

| Standard | Clause/Control | Relationship |
|----------|---------------|-------------|
| NIST SP 800-171 | 3.8 (Media Protection) | CUI media handling requirements |
| NIST SP 800-88 Rev 1 | Media Sanitization | Media destruction after use |
| CNSSI 1253 | Security Categorization | Impact level for air-gapped systems |
| DoDI 8510.01 | Risk Management Framework for DoD IT | DoD authorization for air-gapped systems |
| DISA STIG | Various STIGs | Security configuration for air-gapped components |
| NIST SP 800-53 Rev 5 | MP-2, MP-4, MP-5 (Media Protection controls) | Media access, storage, transport |

## 12. Tailoring Guidance

**IL2 (non-CUI, internet-connected but isolated):**
- Simplified packaging — direct download may be acceptable
- Media transfer not required if network path exists
- Standard installation procedure applies
- AI model access via standard Anthropic API (internet-connected)

**IL4/IL5 (CUI, air-gapped):**
- Execute all activities as written with full rigor
- Two-person integrity for all media transfers
- CUI markings on all media and documentation
- On-premise model deployment or data diode required
- Coordinate with PROC-GOV-006 for CUI handling specifics

**IL6 (SECRET, air-gapped):**
- All IL4/IL5 requirements plus:
- Security clearance required for all personnel handling media
- Classified media handling procedures (beyond CUI)
- Facility clearance required for installation site
- This impact level may require a separate process addendum

**Customer-managed installation:**
- Provide detailed installation guide and media
- Remote support via approved communication channels (not direct network access)
- Customer performs installation with vendor guidance
- Vendor validates installation via screenshots or reports provided by customer

## 13. Related Processes

| Process | Relationship |
|---------|-------------|
| PROC-LC-006 | Extends — air-gap packaging extends the base release process |
| PROC-LC-007 | Extends — air-gap installation extends the base deployment process |
| PROC-GOV-003 | Related — export controls apply to media shipped internationally |
| PROC-GOV-006 | Related — CUI handling applies to media in CUI environments |
| PROC-GOV-010 | Related — continuous monitoring must function in air-gapped mode |
| PROC-GOV-012 | Depends on — impact level determines the rigor of air-gap procedures |

## 14. Traces

- **Governs:** Offline distribution packages, media accountability registers, air-gap installation guides
- **Enforced by:** SHA-256 integrity verification, media accountability audits, installation validation scripts
- **Related QA:** QA-008 (Dual Deployment Architecture)

## 15. Change History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 2026-02-28 | Mateo Segura | Initial release |
