# PROC-LC-007: Deployment & Operations

**Version:** 1.0.0
**Status:** draft
**Category:** lifecycle
**Layer:** base
**Maturity:** initial
**Owner:** DevOps Lead
**Last Reviewed:** 2026-02-28

## 1. Purpose

Deployment & Operations governs how claude-kit releases reach end users, how operational incidents are handled, and how operational knowledge is captured in runbooks and migration guides. This process bridges the gap between a successful release (PROC-LC-006) and ongoing production use, ensuring that deployment procedures are repeatable, incidents are resolved systematically, and operational lessons feed back into the development lifecycle.

## 2. Scope

**Included:**
- Deployment planning for encrypted plugin distribution via `claude-kit update`
- Incident response procedures (detection, triage, resolution, post-mortem)
- Runbook creation and maintenance for recurring operational tasks
- Migration guide creation for breaking changes between versions
- Operational monitoring of CI/CD infrastructure (self-hosted runner, GitHub Actions)
- Devcontainer image publishing via `publish-devcontainer.yml`

**Excluded:**
- Release engineering (tag creation, changelog — handled by PROC-LC-006)
- Security incident response (handled by PROC-SEC-003, which this process invokes)
- Customer-side deployment in air-gapped environments (handled by PROC-GOV-011)

## 3. Entry Criteria

- [ ] A release has been tagged and published (for deployment activities)
- [ ] An operational event or failure has been detected (for incident activities)
- [ ] A breaking change is planned that requires user migration guidance (for migration activities)
- [ ] A recurring operational task lacks documentation (for runbook activities)

## 4. Inputs

| Input | Source | Format |
|-------|--------|--------|
| Release artifacts | PROC-LC-006 / `release.yml` | GitHub Release with encrypted plugins |
| Incident signals | CI failures, user reports, monitoring alerts | Unstructured (logs, messages) |
| Breaking change list | CHANGELOG.md, ADR documents | Markdown |
| Operational procedures | Team knowledge, past incident resolutions | Undocumented or ad hoc |
| CI/CD configuration | `.github/workflows/` | YAML workflow files |

## 5. Activities

### 5.1 Deployment Planning

Before each release, verify the deployment path works end-to-end. This includes: confirming that `scripts/encrypt-plugins.sh` produces valid encrypted bundles, testing that `claude-kit update` can decrypt and install the release, and verifying that the `install.sh` script correctly bootstraps fresh installations. Document any environment-specific considerations (e.g., proxy configuration, offline availability).

### 5.2 Deployment Execution

Execute the deployment by pushing a version tag that triggers `release.yml`. Monitor the workflow for successful completion. Verify that the GitHub Release contains the correct assets and that the CHANGELOG section was extracted properly. For devcontainer image updates, confirm that `publish-devcontainer.yml` completes and the new image is pullable from `ghcr.io/mateosegura/dev-env-claude-kit:latest`.

### 5.3 Incident Detection and Triage

Detect operational incidents through: CI workflow failure notifications, GitHub issue reports, and self-hosted runner health checks. Triage each incident by severity:
- **Critical:** Plugin decryption failures, key compromise, CI infrastructure down
- **High:** Validation false positives blocking PRs, nightly review failures
- **Medium:** Non-blocking workflow warnings, performance degradation
- **Low:** Cosmetic issues, documentation gaps

### 5.4 Incident Resolution and Documentation

Resolve the incident following the containment-eradication-recovery pattern. After resolution, create an incident record in `docs/operations/incidents/` using the `incident.md.tmpl` template with an INC-XXX identifier. The record must include: timeline, root cause, resolution steps, and preventive actions. If the incident reveals a security concern, escalate to PROC-SEC-003.

### 5.5 Runbook Creation

For any operational task performed more than twice, create a runbook in `docs/operations/runbooks/` with an RB-XXX identifier. Runbooks must be executable step-by-step by someone unfamiliar with the system. Include: prerequisites, exact commands, expected output, rollback steps, and escalation contacts.

### 5.6 Migration Guide Creation

When a release contains breaking changes (major version bumps, renamed commands, changed plugin APIs), create a migration guide in `docs/operations/migration/` with a MIG-XXX identifier. The guide must map old behavior to new behavior, provide upgrade commands, and document any manual steps required.

## 6. Outputs / Artifacts

| Artifact | Directory | Template | ID Pattern |
|----------|-----------|----------|------------|
| Incident records | `docs/operations/incidents/` | `incident.md.tmpl` | INC-XXX |
| Runbooks | `docs/operations/runbooks/` | — | RB-XXX |
| Migration guides | `docs/operations/migration/` | — | MIG-XXX |
| Operations index | `docs/operations/INDEX.md` | — | — |

## 7. Exit Criteria

- [ ] Deployment verified: `claude-kit update` successfully installs the release in a clean environment
- [ ] All incidents from the deployment are resolved or have open tracking issues
- [ ] Incident records created for any severity-high-or-above events
- [ ] Migration guide published for any breaking changes
- [ ] `bash scripts/validate-docs.sh` passes with new operations documents

## 8. Quality Gates

| Gate | Verification Method | Pass Criteria |
|------|-------------------|---------------|
| Deployment smoke test | Run `claude-kit update` against the published release | Plugin list, decryption, and validation all succeed |
| Incident completeness | Review incident record | All five sections present: timeline, root cause, resolution, impact, preventive actions |
| Runbook executability | Follow-the-steps test by someone not the author | All steps execute successfully without undocumented prerequisites |
| Migration accuracy | Apply migration guide to a project using the previous version | Project works correctly on the new version after following the guide |

## 9. Roles and Responsibilities

| Role | Responsibility |
|------|---------------|
| DevOps Lead | Owns deployment planning and execution; monitors CI infrastructure health |
| Incident Commander | Triages incidents, coordinates resolution, ensures post-mortem documentation |
| Technical Lead | Reviews incident root cause analysis; approves preventive actions |
| Documentation Author | Creates runbooks and migration guides; maintains `docs/operations/INDEX.md` |

## 10. Metrics

| Metric | Description | Target | Collection Method |
|--------|-------------|--------|------------------|
| Deployment success rate | Percentage of releases deployed without rollback | >= 95% | Track via release.yml outcomes |
| Mean time to resolve (MTTR) | Average time from incident detection to resolution | < 4 hours for critical | Incident record timestamps |
| Runbook coverage | Percentage of recurring operational tasks with documented runbooks | >= 80% | Audit `docs/operations/runbooks/` |
| Incident recurrence rate | Percentage of incidents with the same root cause as a previous incident | < 10% | Cross-reference incident records |

## 11. Standards Alignment

| Standard | Clause/Control | Relationship |
|----------|---------------|-------------|
| ISO/IEC 12207:2017 | 6.3.1 Operation | Operational procedures and incident management |
| NIST SP 800-218 | PO.3 | Secure deployment and operational monitoring practices |
| NIST SP 800-61 | Incident handling | Incident response lifecycle alignment |
| ISO 27001 | A.16 | Information security incident management |

## 12. Tailoring Guidance

**Minimum viable process (solo developer):** Skip formal incident records for low/medium severity issues — a GitHub issue with a "resolved" label suffices. Create runbooks only for tasks involving encryption keys or CI infrastructure. Migration guides are still required for any breaking change.

**Full ceremony (team with dedicated operations):** Execute all activities. Add automated deployment verification (smoke test in CI after release). Maintain an incident dashboard with MTTR tracking. Conduct quarterly runbook reviews.

**When to simplify:** If the release contains only documentation or rule changes (no plugin content or CLI changes), skip deployment smoke testing — the release workflow's built-in validation is sufficient.

## 13. Related Processes

| Process | Relationship |
|---------|-------------|
| PROC-LC-006 | Depends on: receives release artifacts from Release Management |
| PROC-SEC-003 | Escalates to: security incidents are handed off to Incident Response |
| PROC-SP-001 | Depends on: configuration management ensures deployment reproducibility |
| PROC-LC-008 | Feeds into: incident post-mortems and operational lessons drive continuous improvement |
| PROC-ORG-002 | Feeds into: MTTR and deployment success rate feed Measurement & Analysis |
| PROC-SEC-005 | Related: encryption key management is critical to deployment |

## 14. Traces

- **Governs:** `docs/operations/incidents/` (INC-XXX), `docs/operations/runbooks/` (RB-XXX), `docs/operations/migration/` (MIG-XXX)
- **Enforced by:** `scripts/validate-docs.sh` (document structure); `release.yml` (deployment gate); `publish-devcontainer.yml` (image publishing)
- **Related QA:** System availability, operational reliability, deployment reproducibility

## 15. Change History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 2026-02-28 | Mateo Segura | Initial release — formalizes deployment, incident, runbook, and migration practices |
