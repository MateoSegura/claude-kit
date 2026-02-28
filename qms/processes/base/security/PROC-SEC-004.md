# PROC-SEC-004: Access Control

**Version:** 1.0.0
**Status:** draft
**Category:** security
**Layer:** base
**Maturity:** initial
**Owner:** Security Lead
**Last Reviewed:** 2026-02-28

## 1. Purpose

Access Control governs who and what can access claude-kit's repository, CI/CD infrastructure, encryption key material, and distribution channels. claude-kit's security model depends on controlled access at multiple layers: repository write access determines who can modify plugins, CI/CD secrets determine who can trigger encrypted builds, and the encryption key assembly in _get_key() must be protected from unauthorized exposure. This process ensures that access is granted based on the principle of least privilege, reviewed periodically, and revoked promptly when no longer needed.

## 2. Scope

**Included:**
- GitHub repository access (read, write, admin permissions)
- GitHub Actions secrets and environment variables
- Container registry (ghcr.io) push/pull access
- Self-hosted CI runner access and configuration
- Encryption key material access (knowledge of key split components)
- Branch protection rules and merge requirements
- Personal access token lifecycle management

**Excluded:**
- End-user access to installed plugins (governed by Claude Code's built-in permissions)
- Anthropic API key management (user-side configuration)
- Physical access to development machines
- Government-specific access controls (CUI handling -- PROC-GOV-006, Zero Trust -- PROC-GOV-007)

## 3. Entry Criteria

- [ ] A new team member is being granted access to the repository or CI infrastructure
- [ ] A team member's role has changed, requiring access adjustment
- [ ] A scheduled access review interval has arrived (quarterly)
- [ ] A security incident has occurred that may require access revocation
- [ ] A new CI secret, token, or credential is being created

## 4. Inputs

| Input | Source | Format |
|-------|--------|--------|
| Team member roster | Organization records | List of contributors |
| GitHub repository settings | GitHub API / web interface | Access control lists |
| GitHub Actions secrets inventory | Repository settings, Secrets | Secret names (not values) |
| Branch protection rules | Repository settings, Branches | Protection rule configuration |
| Self-hosted runner configuration | GitHub Actions, Runners | Runner labels and access |
| Incident records | docs/operations/incidents/ (INC-XXX) | Incident post-mortems with access implications |
| Risk register entries | PROC-ORG-004 | Access-related risk items |

## 5. Activities

### 5.1 Access Policy Definition

Define and maintain access policies for each controlled resource:

**Repository access levels:**

| Level | Who | Capabilities |
|-------|-----|-------------|
| Read | External reviewers, auditors | Clone, view code, read issues |
| Write | Active developers | Push branches, create PRs, manage issues |
| Maintain | Senior developers | Merge to protected branches, manage CI |
| Admin | Repository owner | Settings, secrets, branch rules, danger zone |

**Principle of least privilege:** Grant the minimum access level required for each person's role. Default to Read; escalate only when duties require it. No one should have Admin access unless they actively need to modify repository settings or secrets.

**CI/CD secret access:**
- Repository-level secrets are accessible to all workflows. Limit the number of secrets to the minimum required.
- Environment-level secrets can restrict access to specific workflows or branches. Use environments for sensitive secrets like encryption-related configuration.
- Never expose secrets in workflow logs. All workflows must mask dynamically generated sensitive values.

### 5.2 Access Provisioning

When granting access:

1. Verify the request is from the repository owner or an authorized Admin
2. Determine the minimum access level required for the person's role
3. Grant access via GitHub repository settings (Collaborators or team membership)
4. Document the access grant: who, what level, when, why, and approved by whom
5. Notify the person of their access and any relevant policies (branch protection, commit signing)

For CI/CD secrets:
1. Create the secret at the appropriate scope (repository or environment)
2. Document the secret's purpose (not its value) in an internal inventory
3. Set an expiration reminder (tokens and credentials should be rotated at least annually)

### 5.3 Access Reviews

Quarterly, conduct a comprehensive access review:

1. List all collaborators and their access levels from GitHub repository settings
2. For each person: verify they still need access and their level is still appropriate
3. Identify stale access (people who have left the project or changed roles)
4. Review CI/CD secrets: are all secrets still in use? Are any expired or about to expire?
5. Review branch protection rules: are they still appropriate? (Required reviews, status checks)
6. Document the review findings and any access changes made

### 5.4 Access Revocation

Revoke access immediately when:
- A team member leaves the project or organization
- A security incident involves compromised credentials
- An access review identifies unnecessary permissions

Revocation procedure:
1. Remove the person's repository access via GitHub settings
2. Rotate any secrets they had knowledge of (especially GITHUB_TOKEN for CI)
3. Review recent activity for unauthorized changes
4. Document the revocation: who, when, reason

For emergency revocation during a security incident (PROC-SEC-003):
1. Revoke first, document later
2. Rotate all potentially compromised credentials
3. Audit the person's recent commits and workflow triggers

### 5.5 Branch Protection Management

Maintain branch protection rules that enforce:

| Rule | Setting | Rationale |
|------|---------|-----------|
| Require PR before merge (main) | Enabled | Prevents direct pushes; enforces review |
| Required status checks | fast-validate, validate-tier1 | Ensures CI passes before merge |
| Require review approval | At least 1 review | Prevents unreviewed code from merging |
| Restrict force push | Enabled | Prevents history rewriting on main |
| Restrict deletion | Enabled | Prevents accidental branch deletion |

Review branch protection rules during quarterly access reviews. When CI workflows change (new required checks added), update the branch protection configuration to match.

## 6. Outputs / Artifacts

| Artifact | Directory | Template | ID Pattern |
|----------|-----------|----------|------------|
| Access policy document | qms/ or internal documentation | -- | -- |
| Access review records | Internal documentation | -- | -- |
| Secret inventory (names only) | Internal documentation | -- | -- |
| Branch protection configuration | GitHub repository settings | -- | -- |

## 7. Exit Criteria

- [ ] All repository collaborators have access levels documented and justified
- [ ] Quarterly access review completed and findings addressed
- [ ] All CI/CD secrets are inventoried with purpose documentation and expiration dates
- [ ] Branch protection rules are configured and enforced on main
- [ ] No stale access (all revoked for departed members within 24 hours)

## 8. Quality Gates

| Gate | Verification Method | Pass Criteria |
|------|-------------------|---------------|
| Least privilege compliance | Audit access levels against role requirements | No person has access beyond what their role requires |
| Secret hygiene | Review secret inventory age | No secret older than 12 months without rotation |
| Branch protection integrity | Check repository settings | All required rules enabled on main; no bypass exceptions |
| Revocation timeliness | Check revocation records | All access revocations completed within 24 hours of trigger |

## 9. Roles and Responsibilities

| Role | Responsibility |
|------|---------------|
| Security Lead | Defines access policies; conducts quarterly access reviews; approves access escalation requests |
| Repository Owner (Admin) | Implements access changes in GitHub settings; manages branch protection rules; manages CI/CD secrets |
| Technical Lead | Reviews access requests for role appropriateness; reports access anomalies |
| Developer | Uses access responsibly; reports suspected unauthorized access; rotates personal tokens when requested |

## 10. Metrics

| Metric | Description | Target | Collection Method |
|--------|-------------|--------|------------------|
| Access review compliance | Percentage of quarterly reviews completed on schedule | 100% | Track review dates |
| Stale access count | Number of collaborators identified as no longer needing access during reviews | 0 (all stale access removed promptly) | Quarterly review findings |
| Secret rotation compliance | Percentage of secrets rotated within their prescribed interval | 100% | Check secret age against rotation policy |
| Branch protection coverage | Percentage of required protections enabled on main | 100% | Audit repository settings |

## 11. Standards Alignment

| Standard | Clause/Control | Relationship |
|----------|---------------|-------------|
| NIST SP 800-218 | PO.2.1 | Personnel security requirements for secure development |
| ISO 27001 | A.9 | Access control policy, user access management, system access control |
| CMMC | AC.1.001 | Limit information system access to authorized users |
| CMMC | AC.2.007 | Employ the principle of least privilege |
| NIST SP 800-53 | AC-1 through AC-25 | Access control family |
| NIST SP 800-63 | Digital identity | Credential management and authentication |

## 12. Tailoring Guidance

**Minimum viable process (solo developer):** Repository access review is implicit (single owner). Focus on: secret rotation (set calendar reminders for annual rotation), branch protection on main (enable PR requirement even for solo work to prevent accidental direct pushes), and token hygiene (use fine-grained tokens with minimum required scopes).

**Full ceremony (team targeting defense/federal):** Execute all activities. Add multi-factor authentication requirement for all collaborators. Implement environment-scoped secrets for encryption-related configuration. Conduct monthly (not quarterly) access reviews. Integrate with PROC-GOV-006 (CUI Handling) and PROC-GOV-007 (Zero Trust Alignment) for government-specific access requirements.

**When to simplify:** If the repository is private with a single collaborator, reduce access review frequency to semi-annually. Branch protection and secret rotation should remain at full rigor regardless of team size -- these are preventive controls against accidental damage, not just unauthorized access.

## 13. Related Processes

| Process | Relationship |
|---------|-------------|
| PROC-SEC-003 | Feeds into: access-related security incidents trigger emergency revocation and review |
| PROC-SEC-005 | Related: encryption key access is the most sensitive access control concern |
| PROC-SEC-001 | Related: secure development practices include access-controlled development environments |
| PROC-ORG-004 | Receives from: access-related risks in the risk register drive access policy decisions |
| PROC-ORG-003 | Related: access provisioning may trigger training on repository policies |
| PROC-SP-001 | Related: configuration management depends on controlled access to prevent unauthorized changes |

## 14. Traces

- **Governs:** Repository access configuration, CI/CD secrets, branch protection rules, self-hosted runner access
- **Enforced by:** GitHub branch protection (automated); quarterly access reviews (manual); push.yml branch naming enforcement (automated)
- **Related QA:** Principle of least privilege, credential hygiene, access auditability

## 15. Change History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 2026-02-28 | Mateo Segura | Initial release -- formalizes access control for repository, CI/CD, and encryption key material |
