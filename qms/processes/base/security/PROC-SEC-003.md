# PROC-SEC-003: Incident Response

**Version:** 1.0.0
**Status:** draft
**Category:** security
**Layer:** base
**Maturity:** initial
**Owner:** Security Lead
**Last Reviewed:** 2026-02-28

## 1. Purpose

Incident Response defines the procedures for detecting, containing, eradicating, recovering from, and learning from security incidents affecting claude-kit. Security incidents differ from operational incidents (PROC-LC-007) in that they involve a confirmed or suspected compromise of confidentiality, integrity, or availability of security-relevant assets -- particularly the encryption key material, plugin content intellectual property, CI/CD pipeline integrity, or repository access controls. This process ensures that security incidents are handled with urgency, discipline, and thorough documentation.

## 2. Scope

**Included:**
- Security incident detection and classification
- Containment procedures to limit blast radius
- Eradication of the threat or vulnerability
- Recovery to normal operations
- Post-incident review and lessons learned
- Security incident documentation in docs/operations/incidents/ with INC-XXX identifiers

**Excluded:**
- Operational incidents without a security dimension (handled by PROC-LC-007)
- Vulnerability management (proactive scanning -- handled by PROC-SEC-002)
- Compliance incident reporting to external bodies (handled by PROC-GOV-001, PROC-GOV-002)
- Customer-side security incidents in their own environments

## 3. Entry Criteria

- [ ] A security event has been detected or reported that suggests compromise or attempted compromise
- [ ] A vulnerability has been confirmed as actively exploited
- [ ] Unauthorized access to the repository, CI/CD pipeline, or encryption key material is suspected
- [ ] A supplier (Anthropic, GitHub) reports a security breach that may affect claude-kit

## 4. Inputs

| Input | Source | Format |
|-------|--------|--------|
| Security event alerts | GitHub audit log, CI/CD anomalies, external reports | Unstructured (logs, notifications) |
| Vulnerability reports | PROC-SEC-002 outputs | Vulnerability scan results |
| Access logs | GitHub repository settings, self-hosted runner logs | Log files |
| Supplier breach notifications | Anthropic, GitHub security bulletins | Advisory notices |
| Encryption key status | _get_key() function integrity, key split verification | Code review |
| Previous incident records | docs/operations/incidents/ (INC-XXX) | Incident post-mortems |

## 5. Activities

### 5.1 Detection and Classification

Security incidents may be detected through:
- **Automated monitoring:** Unexpected CI/CD workflow behavior, authentication failures, unusual repository activity in GitHub audit logs
- **Manual observation:** Developer notices suspicious changes, commits they did not author, or unexpected plugin decryption failures
- **External reporting:** Security researcher disclosure, supplier notification, customer report
- **Vulnerability exploitation:** A known vulnerability (PROC-SEC-002) confirmed as actively exploited

Classify the incident by type and severity:

| Type | Description | Severity Guidance |
|------|-------------|-------------------|
| Key compromise | Encryption key material exposed or suspected exposed | Always Critical |
| Unauthorized access | Repository, CI, or runner access by unauthorized party | Critical or High |
| Supply chain attack | Malicious code introduced through a dependency or action | Critical |
| Data exfiltration | Plugin content or proprietary data leaked | High or Critical |
| Integrity violation | Unauthorized modification of code, plugins, or CI config | High |
| Service disruption | Security-motivated denial of service | Medium or High |

### 5.2 Containment

Immediate actions to limit the blast radius, prioritized by incident type:

**Key compromise containment:**
1. Immediately rotate the encryption key by modifying _get_key() split parts
2. Re-encrypt all plugins with the new key
3. Invalidate any published release artifacts that used the compromised key
4. Revoke and rotate all GitHub personal access tokens and secrets

**Unauthorized access containment:**
1. Revoke the compromised credential or access token immediately
2. Enable branch protection on all branches if not already active
3. Review and revert any unauthorized commits
4. Audit GitHub Actions secrets for exposure

**Supply chain containment:**
1. Pin the affected dependency to the last known-good version
2. Disable affected CI workflows until the malicious component is removed
3. Audit all workflow runs since the suspected introduction date

**General containment:**
- Document the timestamp of containment actions
- Preserve evidence (logs, artifacts) before making changes
- Communicate containment status to all team members

### 5.3 Eradication

Remove the root cause of the incident:

1. Identify the attack vector (how the adversary gained access or how the vulnerability was exploited)
2. Patch the vulnerability or close the access path
3. Verify eradication by confirming the attack vector is no longer viable
4. If the attack vector involves a supplier: coordinate with the supplier and verify their remediation

For key compromise: after rotation, verify that all published artifacts use the new key and that the old key cannot decrypt any currently-distributed content.

### 5.4 Recovery

Restore normal operations:

1. Verify all security controls are in place (branch protection, secret rotation, CI/CD integrity)
2. Run the full validation suite (all four test layers)
3. Confirm that encrypted plugin distribution works end-to-end
4. Resume normal CI/CD operations
5. If a release was affected: issue a new release with patched content and notify users

### 5.5 Post-Incident Review

Within 72 hours of recovery, conduct a post-incident review:

1. Create an incident record in docs/operations/incidents/ using the incident.md.tmpl template with the next sequential INC-XXX identifier
2. Document: timeline (detection through recovery), root cause, containment and eradication actions, impact assessment, and lessons learned
3. Identify preventive actions that would prevent recurrence
4. Create improvement signals for PROC-LC-008 based on lessons learned
5. Update the risk register (PROC-ORG-004) if new risks were identified
6. If the incident revealed a training gap, create a training action for PROC-ORG-003

## 6. Outputs / Artifacts

| Artifact | Directory | Template | ID Pattern |
|----------|-----------|----------|------------|
| Security incident records | docs/operations/incidents/ | incident.md.tmpl | INC-XXX |
| Containment action log | Embedded in incident record | -- | -- |
| Preventive action items | GitHub Issues with security label | -- | -- |
| Risk register updates | PROC-ORG-004 risk register | -- | -- |

## 7. Exit Criteria

- [ ] Incident fully contained -- adversary no longer has access, vulnerability patched
- [ ] Normal operations restored and verified
- [ ] Incident record created with complete timeline, root cause, and lessons learned
- [ ] Preventive actions documented and assigned to owners
- [ ] Risk register updated if new risks were identified
- [ ] Affected stakeholders notified of resolution

## 8. Quality Gates

| Gate | Verification Method | Pass Criteria |
|------|-------------------|---------------|
| Containment verification | Attempt to reproduce the attack vector | Attack vector is no longer viable |
| Recovery validation | Full validation suite passes | All 4 test layers pass; encrypted distribution works end-to-end |
| Documentation completeness | Review incident record | All sections of the incident template are filled with specific, factual content |
| Lessons learned actionability | Review preventive actions | At least one preventive action has a concrete implementation plan and assigned owner |

## 9. Roles and Responsibilities

| Role | Responsibility |
|------|---------------|
| Security Lead | Incident commander: coordinates response, makes containment decisions, owns the incident record |
| Technical Lead | Provides technical analysis of root cause; implements eradication and recovery actions |
| DevOps Lead | Executes infrastructure-level containment (credential rotation, CI pipeline modification) |
| Product Lead | Manages stakeholder communication; decides on user notification timing and content |

## 10. Metrics

| Metric | Description | Target | Collection Method |
|--------|-------------|--------|------------------|
| Mean time to detect (MTTD) | Time from incident start to detection | Less than 24 hours | Incident record timestamps |
| Mean time to contain (MTTC) | Time from detection to containment | Less than 4 hours for critical, less than 24 hours for high | Incident record timestamps |
| Mean time to recover (MTTR) | Time from containment to full recovery | Less than 24 hours for critical, less than 72 hours for high | Incident record timestamps |
| Post-incident review completion | Percentage of incidents with completed post-incident review within 72 hours | 100% | Check incident record creation dates |
| Preventive action implementation | Percentage of preventive actions implemented within 30 days | At least 80% | Track GitHub Issue closure dates |

## 11. Standards Alignment

| Standard | Clause/Control | Relationship |
|----------|---------------|-------------|
| NIST SP 800-61 | Computer security incident handling | Full incident response lifecycle |
| NIST SP 800-218 | RV.1.3 | Respond to vulnerability reports and incidents |
| ISO 27001 | A.16 | Information security incident management |
| CMMC | IR.2.092 | Establish an operational incident-handling capability |
| NIST SP 800-53 | IR-1 through IR-8 | Incident response family of controls |

## 12. Tailoring Guidance

**Minimum viable process (solo developer):** For non-critical incidents, combine the containment/eradication/recovery steps into a single action phase. Skip the formal post-incident review for low-severity incidents -- a GitHub Issue with a root cause note suffices. Always create a formal incident record for any incident involving encryption keys or unauthorized access.

**Full ceremony (team targeting defense/federal):** Execute all activities with strict documentation. Add external notification requirements per contractual obligations. Integrate with PROC-GOV-001 (CMMC) and PROC-GOV-002 (FedRAMP) for compliance incident reporting. Conduct a formal post-incident review meeting with all team members.

**When to escalate vs. handle in-process:** Incidents involving encryption key material compromise, unauthorized repository access, or supply chain attacks should always be treated as Critical regardless of apparent impact. When in doubt about severity, escalate to Critical and downgrade after investigation.

## 13. Related Processes

| Process | Relationship |
|---------|-------------|
| PROC-SEC-002 | Receives from: exploited vulnerabilities trigger incident response; feeds into: incidents may reveal new vulnerabilities |
| PROC-SEC-004 | Related: access control failures may be the root cause of unauthorized access incidents |
| PROC-SEC-005 | Related: encryption key compromise incidents require key management procedures |
| PROC-LC-007 | Related: security incidents are a subset of operational incidents; escalation path from operational to security |
| PROC-LC-008 | Feeds into: lessons learned create improvement signals |
| PROC-ORG-004 | Feeds into: incidents update the risk register with realized risks and new risk identification |
| PROC-ORG-003 | Feeds into: incidents revealing knowledge gaps trigger training actions |

## 14. Traces

- **Governs:** Security incident records in docs/operations/incidents/ (INC-XXX with security classification)
- **Enforced by:** Manual process (incident response is inherently reactive); post-incident review deadline (72 hours)
- **Related QA:** Encryption integrity, access control effectiveness, incident response readiness

## 15. Change History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 2026-02-28 | Mateo Segura | Initial release -- establishes security incident response procedures with emphasis on encryption key and access control scenarios |
