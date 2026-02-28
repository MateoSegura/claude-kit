# PROC-ORG-003: Training

**Version:** 1.0.0
**Status:** draft
**Category:** organizational
**Layer:** base
**Maturity:** initial
**Owner:** Technical Lead
**Last Reviewed:** 2026-02-28

## 1. Purpose

Training ensures that all participants in the claude-kit development process — both human developers and AI agents — have the knowledge required to perform their roles effectively. claude-kit has a unique dual-audience training challenge: human developers must understand plugin architecture, CI workflows, and the QMS; AI agents must be trained through `.claude/rules/` files, skill documents, and agent frontmatter. This process governs both audiences systematically to prevent knowledge gaps that lead to errors, inconsistent outputs, or process violations.

## 2. Scope

**Included:**
- Identification of training needs for human developers joining the project
- Creation and maintenance of training materials (documentation, rules, onboarding guides)
- AI agent training through `.claude/rules/` configuration, skill content, and agent instructions
- Assessment of training effectiveness (human comprehension, agent compliance)
- Onboarding procedures for new contributors

**Excluded:**
- End-user documentation for claude-kit consumers (handled by plugin README files and PROC-SP-004)
- Marketing or sales training materials
- Training for external auditors (handled by PROC-GOV-008 in the government overlay)

## 3. Entry Criteria

- [ ] A new team member (human or AI agent configuration) is being onboarded
- [ ] A significant process, architecture, or tooling change has been made that affects how work is done
- [ ] Training effectiveness assessment reveals a knowledge gap
- [ ] A new plugin team is being created and requires knowledge skill configuration

## 4. Inputs

| Input | Source | Format |
|-------|--------|--------|
| Process documents | `qms/processes/` | Markdown (15-section template) |
| Architecture rules | `.claude/rules/` | Markdown rule files |
| Plugin skill content | `plugins/*/skills/*/SKILL.md` | Markdown with frontmatter |
| Agent definitions | `plugins/*/agents/*.md` | Markdown with frontmatter |
| Incident post-mortems | `docs/operations/incidents/` | INC-XXX records |
| Research papers | `docs/research/` | Narrative markdown |
| Error patterns from CI | `pr-autofix.yml` failure logs | Unstructured logs |

## 5. Activities

### 5.1 Training Need Identification

Identify training gaps through multiple channels:

**For human developers:**
- New contributor onboarding checklist review
- Recurring patterns in PR review feedback (same mistakes repeated)
- Incident post-mortems that cite human error or misunderstanding
- Process changes that alter how work is done

**For AI agents:**
- Recurring validation failures that indicate agent non-compliance with rules
- PR autofix patterns showing agents make the same mistakes repeatedly
- Nightly review findings that reflect systemic misunderstanding of plugin conventions
- New plugin teams requiring domain-specific knowledge injection

### 5.2 Material Creation — Human Training

Create or update training materials based on identified needs:

- **Onboarding guide:** Step-by-step walkthrough covering repository structure (`architecture.md` rule), development workflow (`dev-workflow.md` rule), testing standards (`testing-standards.md` rule), and plugin conventions (`plugin-conventions.md` rule)
- **Process-specific guides:** When a process document is too detailed for quick reference, create a condensed "how-to" companion
- **Architecture decision context:** Ensure ADR documents in `docs/architecture/decisions/` are written clearly enough to serve as training material for the decisions they record

### 5.3 Material Creation — AI Agent Training

AI agents in claude-kit are "trained" through structured configuration files:

- **`.claude/rules/` files:** Each rule file acts as a training document. When a new convention is established, create or update the corresponding rule file. Rules must be specific, actionable, and testable — vague guidance produces vague compliance.
- **Knowledge skills (`plugins/*/skills/*/SKILL.md`):** Each skill injects domain knowledge into an agent session. When domain knowledge is incomplete or produces errors, update the skill content.
- **Agent frontmatter:** The `identity`, `instructions`, and `tools` fields in agent definitions configure agent behavior. Review these when agents produce unexpected outputs.

### 5.4 Training Delivery

**Human developers:** Direct new contributors to the onboarding guide. For process changes, include a summary of what changed and why in the PR description. For complex changes, add inline code comments or rule annotations.

**AI agents:** Deploy updated rules, skills, and agent definitions through the normal PR and merge workflow. Agent training is inherently continuous — every merge to main that modifies `.claude/rules/` or plugin skill content retrains all future agent sessions.

### 5.5 Effectiveness Assessment

**Human developers:** Monitor for training-related issues:
- Do PR review comments still flag the same knowledge gaps after training?
- Can new contributors produce passing PRs within their first week?
- Are incident post-mortems still citing knowledge gaps as contributing factors?

**AI agents:** Monitor for compliance:
- Do agents follow the conventions in `.claude/rules/` consistently?
- Has the nightly review finding rate decreased for categories addressed by recent rule updates?
- Do PR autofix patterns show improvement after skill content updates?

## 6. Outputs / Artifacts

| Artifact | Directory | Template | ID Pattern |
|----------|-----------|----------|------------|
| Rule files (agent training) | `.claude/rules/` | — | — |
| Skill content (agent knowledge) | `plugins/*/skills/*/SKILL.md` | `skill.md.tmpl` | — |
| Agent definitions | `plugins/*/agents/*.md` | `agent.md.tmpl` | — |
| Onboarding documentation | Repository README, rule files | — | — |
| Research papers (context) | `docs/research/` | — | — |

## 7. Exit Criteria

- [ ] Training materials address the identified knowledge gap
- [ ] Materials have been reviewed for accuracy by someone with domain expertise
- [ ] For AI agent training: updated rules or skills pass validation (`validate-plugins.py`, `test-plugin-consistency.sh`)
- [ ] Effectiveness measurement plan exists (what to monitor, when to check)

## 8. Quality Gates

| Gate | Verification Method | Pass Criteria |
|------|-------------------|---------------|
| Material accuracy | Peer review by domain expert | No factual errors; all file paths and commands are current and executable |
| Rule testability | Attempt to violate the rule and verify detection | Validation scripts or hooks catch the violation, or the rule includes a "how to verify" section |
| Onboarding completeness | New contributor walkthrough | Contributor can set up the development environment and submit a passing PR without undocumented assistance |

## 9. Roles and Responsibilities

| Role | Responsibility |
|------|---------------|
| Technical Lead | Identifies training needs from incident patterns and PR reviews; approves training materials |
| Plugin Author | Creates and maintains skill content and agent definitions; ensures knowledge accuracy |
| Developer | Follows onboarding procedures; provides feedback on training material clarity |
| Quality Lead | Monitors training effectiveness metrics; ensures process training is current |

## 10. Metrics

| Metric | Description | Target | Collection Method |
|--------|-------------|--------|------------------|
| Onboarding time | Time for a new contributor to submit a first passing PR | < 5 business days | Track onboarding start date vs. first merged PR |
| Rule compliance rate | Percentage of agent sessions that follow `.claude/rules/` conventions without correction | >= 90% | Sample review of agent outputs |
| Training material currency | Percentage of rule files updated within 30 days of a related process change | 100% | Cross-reference rule file modification dates with process change dates |
| Repeat error rate | Frequency of the same knowledge-gap error appearing after training was delivered | Decreasing trend | Track PR review comment categories over time |

## 11. Standards Alignment

| Standard | Clause/Control | Relationship |
|----------|---------------|-------------|
| ISO/IEC 12207:2017 | 7.2.3 Human resource management | Training and competency development |
| CMMI | OT (Organizational Training) | Organizational training capability |
| NIST SP 800-218 | PO.2 | Training for secure software development |
| ISO 27001 | A.7.2.2 | Information security awareness and training |

## 12. Tailoring Guidance

**Minimum viable process (solo developer):** Focus exclusively on AI agent training through `.claude/rules/` and skill content. Human training is self-directed through reading existing documentation. Skip formal onboarding guides — the repository's rule files serve as both operational configuration and training material.

**Full ceremony (team):** Add formal onboarding checklists, scheduled training reviews (quarterly), and tracked effectiveness metrics. Create companion guides for complex processes. Conduct periodic agent compliance audits.

**When to simplify:** If the team is small (2-3 developers) and all members have been on the project for more than 3 months, reduce human training activities to change-notification only (describe what changed in PR descriptions). Maintain AI agent training at full rigor regardless of team size, since agents do not retain session context.

## 13. Related Processes

| Process | Relationship |
|---------|-------------|
| PROC-ORG-001 | Receives from: process changes trigger training need identification |
| PROC-LC-008 | Related: training gaps identified through improvement signals; training improvements are a type of continuous improvement |
| PROC-SP-004 | Related: training materials are a type of documentation |
| PROC-LC-004 | Related: implementation standards and conventions require developer training |
| PROC-SEC-001 | Feeds into: secure development training is a subset of overall training |
| PROC-ORG-004 | Related: risk mitigations may require training as a control |

## 14. Traces

- **Governs:** `.claude/rules/` (agent training configuration), `plugins/*/skills/` (knowledge injection), `plugins/*/agents/` (agent behavior definition)
- **Enforced by:** `scripts/validate-plugins.py` (skill and agent structural validation), `scripts/test-plugin-consistency.sh` (cross-reference checks), `nightly.yml` (agent compliance via nightly review)
- **Related QA:** Team competency, agent reliability, knowledge retention

## 15. Change History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 2026-02-28 | Mateo Segura | Initial release — formalizes dual-audience training for human developers and AI agents |
