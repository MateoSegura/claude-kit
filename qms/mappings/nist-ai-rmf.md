# Standards Mapping: NIST AI Risk Management Framework (AI RMF 1.0)

**Version:** 1.0.0
**Status:** draft
**Last Reviewed:** 2026-02-28

## Purpose

Map claude-kit QMS processes to the NIST AI Risk Management Framework (AI RMF 1.0). The AI RMF provides a structured approach for managing risks associated with AI systems. claude-kit integrates AI agents (powered by Anthropic's Claude) into developer workflows, making AI governance a first-class compliance concern for federal and defense customers. This mapping demonstrates how QMS processes address each AI RMF function and category.

## Mapping Legend

- **Primary:** The process directly implements the AI RMF function/category
- **Supporting:** The process contributes activities or evidence that support the function/category
- **N/A:** The function/category is not applicable to claude-kit's AI usage

---

## GOVERN Function

The GOVERN function establishes organizational structures, policies, and processes for AI risk management.

| Category | Subcategory | Description | Process(es) | Relationship | Implementation Notes |
|----------|-------------|-------------|-------------|-------------|---------------------|
| GOVERN 1 | 1.1 | Legal and regulatory requirements are identified | PROC-GOV-005, PROC-GOV-003 | Primary | AI transparency process tracks federal AI requirements; export control evaluates AI classification |
| GOVERN 1 | 1.2 | Trustworthy AI characteristics are integrated into policies | PROC-GOV-005 | Primary | AI transparency process defines organizational AI governance policies |
| GOVERN 1 | 1.3 | Processes for AI risk management are in place | PROC-GOV-005 | Primary | Activity 5.2 (AI Risk Assessment) establishes formal risk management |
| GOVERN 1 | 1.4 | AI system risk management is ongoing | PROC-GOV-010, PROC-GOV-005 | Primary | Continuous monitoring + quarterly AI risk reassessment |
| GOVERN 1 | 1.5 | Ongoing monitoring and review are in place | PROC-GOV-010 | Primary | Continuous monitoring program covers AI system telemetry |
| GOVERN 1 | 1.6 | Risk management processes and outcomes are documented | PROC-GOV-009, PROC-GOV-005 | Primary | Evidence collection + AI risk assessment documentation |
| GOVERN 1 | 1.7 | Processes and outcomes are regularly reviewed | PROC-GOV-008 | Supporting | Audit readiness includes AI governance evidence review |
| GOVERN 2 | 2.1 | Roles and responsibilities are defined and documented | PROC-GOV-005 | Primary | Section 9 (Roles and Responsibilities) designates AI governance roles |
| GOVERN 2 | 2.2 | Training and awareness programs are in place | PROC-GOV-005, PROC-GOV-006 | Primary | AI transparency awareness training + CUI training for AI contexts |
| GOVERN 2 | 2.3 | Executive leadership is engaged in AI risk management | PROC-GOV-005 | Supporting | CISO and Product Lead jointly oversee AI risk program |
| GOVERN 3 | 3.1 | AI risks and benefits are understood at the organizational level | PROC-GOV-005 | Primary | AI system inventory and risk assessment (Activities 5.1, 5.2) |
| GOVERN 3 | 3.2 | Policies and procedures are in place for safe AI operation | PROC-GOV-005 | Primary | Explainability documentation and human oversight verification |
| GOVERN 4 | 4.1 | Organizational practices foster a culture of responsible AI | PROC-GOV-005 | Primary | Glass-box transparency principle (ADR-005) embedded in architecture |
| GOVERN 4 | 4.2 | Organizational teams are empowered to raise concerns | PROC-GOV-005 | Supporting | AI incident reporting procedures |
| GOVERN 4 | 4.3 | Organizational practices foster critical thinking about AI | PROC-GOV-005 | Supporting | Bias testing and oversight verification encourage critical evaluation |
| GOVERN 5 | 5.1 | Policies address data privacy for AI systems | PROC-GOV-006, PROC-GOV-005 | Primary | CUI handling for AI context windows + AI data flow documentation |
| GOVERN 5 | 5.2 | Mechanisms are in place for data subjects to exercise rights | PROC-GOV-013 | Supporting | Customer boundary integration includes data handling provisions |
| GOVERN 6 | 6.1 | Policies and procedures are in place for AI system deployment | PROC-GOV-011, PROC-GOV-012 | Primary | Air-gap deployment and impact level qualification for AI systems |
| GOVERN 6 | 6.2 | Policies address human-AI interaction | PROC-GOV-005 | Primary | Human oversight verification (Activity 5.5) |

## MAP Function

The MAP function contextualizes AI risks within the specific use context and identifies relevant risks.

| Category | Subcategory | Description | Process(es) | Relationship | Implementation Notes |
|----------|-------------|-------------|-------------|-------------|---------------------|
| MAP 1 | 1.1 | Intended purpose and context of AI system is understood | PROC-GOV-005 | Primary | AI system inventory (Activity 5.1) documents purpose and context |
| MAP 1 | 1.2 | Interdependencies between AI and other systems are mapped | PROC-GOV-013, PROC-GOV-004 | Primary | Customer boundary integration + supply chain mapping (Anthropic dependency) |
| MAP 1 | 1.3 | Assessment of positive and negative impacts is conducted | PROC-GOV-005 | Primary | AI risk assessment (Activity 5.2) evaluates both benefits and harms |
| MAP 1 | 1.4 | Humans interacting with AI are identified | PROC-GOV-005 | Primary | Explainability documentation (Activity 5.4) defines user roles |
| MAP 1 | 1.5 | Assumptions and limitations are documented | PROC-GOV-005 | Primary | Explainability docs include known limitations and failure modes |
| MAP 1 | 1.6 | System requirements include trustworthiness considerations | PROC-GOV-005 | Primary | AI transparency requirements feed into product requirements |
| MAP 2 | 2.1 | Potential risks and impacts are identified | PROC-GOV-005 | Primary | Risk mapping in Activity 5.2 — code generation errors, hallucinations, bias |
| MAP 2 | 2.2 | Likelihood and severity of identified risks are assessed | PROC-GOV-005 | Primary | Risk measurement in Activity 5.2 |
| MAP 2 | 2.3 | Risks are prioritized based on assessment | PROC-GOV-005 | Primary | Risk-based prioritization of mitigations |
| MAP 3 | 3.1 | Risks from third-party AI components are identified | PROC-GOV-004, PROC-GOV-005 | Primary | Anthropic as AI supplier — risk assessment in supply chain process |
| MAP 3 | 3.2 | Pre-trained model risks are evaluated | PROC-GOV-005 | Primary | Anthropic model documentation reviewed as input |
| MAP 3 | 3.3 | System performance metrics are defined | PROC-GOV-005 | Supporting | AI system inventory includes performance expectations |
| MAP 3 | 3.4 | Failure modes are identified and documented | PROC-GOV-005 | Primary | Explainability documentation includes failure modes |
| MAP 3 | 3.5 | Data quality requirements are defined | PROC-GOV-005 | Supporting | Knowledge skill content quality is validated by plugin validation |
| MAP 4 | 4.1 | Risks and benefits across demographics are considered | PROC-GOV-005 | Primary | Bias testing (Activity 5.3) evaluates demographic impact |
| MAP 4 | 4.2 | Impacts to individuals and communities are considered | PROC-GOV-005 | Primary | Risk assessment includes impact on developer communities |
| MAP 5 | 5.1 | Organizational risk tolerance is documented | PROC-GOV-005 | Supporting | Risk management section defines acceptable risk thresholds |
| MAP 5 | 5.2 | Practices for risk acceptance are defined | PROC-GOV-005 | Supporting | Residual risk documented after mitigations applied |

## MEASURE Function

The MEASURE function employs quantitative and qualitative methods to analyze, assess, and monitor AI risks.

| Category | Subcategory | Description | Process(es) | Relationship | Implementation Notes |
|----------|-------------|-------------|-------------|-------------|---------------------|
| MEASURE 1 | 1.1 | Approaches for measurement of AI risks are defined | PROC-GOV-005, PROC-GOV-010 | Primary | AI risk metrics (Section 10) + continuous monitoring |
| MEASURE 1 | 1.2 | Measurement approaches are validated | PROC-GOV-008 | Supporting | Mock assessments validate measurement approaches |
| MEASURE 1 | 1.3 | Measurement results are documented and retained | PROC-GOV-009 | Primary | Evidence collection captures AI risk measurement artifacts |
| MEASURE 2 | 2.1 | AI system performance is evaluated | PROC-GOV-005 | Primary | Bias testing and oversight verification measure performance |
| MEASURE 2 | 2.2 | Trustworthiness characteristics are measured | PROC-GOV-005 | Primary | Explainability, fairness, and reliability metrics |
| MEASURE 2 | 2.3 | AI system performance and trustworthiness are compared to requirements | PROC-GOV-005 | Primary | Results compared against organizational AI governance policies |
| MEASURE 2 | 2.4 | Measurement of AI system performance is ongoing | PROC-GOV-010 | Primary | Continuous monitoring includes AI system health telemetry |
| MEASURE 2 | 2.5 | AI system evaluations are documented | PROC-GOV-009, PROC-GOV-005 | Primary | Bias testing reports and risk assessments stored as evidence |
| MEASURE 2 | 2.6 | Measurement approaches account for limitations | PROC-GOV-005 | Supporting | Bias testing methodology documents its own limitations |
| MEASURE 2 | 2.7 | AI system deployment evaluation includes real-world testing | PROC-GOV-005 | Primary | Quarterly bias testing on production system |
| MEASURE 2 | 2.8 | Measurement results inform risk management decisions | PROC-GOV-005, PROC-GOV-010 | Primary | Risk assessment updates feed into remediation planning |
| MEASURE 2 | 2.9 | AI evaluation metrics include computational and environmental costs | PROC-GOV-004 | Supporting | Supply chain assessment includes Anthropic resource usage |
| MEASURE 2 | 2.10 | Privacy risk of AI system is measured | PROC-GOV-006, PROC-GOV-005 | Primary | CUI in AI context windows + AI data flow analysis |
| MEASURE 2 | 2.11 | Fairness and bias are evaluated | PROC-GOV-005 | Primary | Bias testing (Activity 5.3) — code generation, grading, testing bias |
| MEASURE 2 | 2.12 | Environmental impact is assessed | PROC-GOV-004 | Supporting | Supply chain assessment can include environmental considerations |
| MEASURE 2 | 2.13 | Effectiveness of risk mitigations is assessed | PROC-GOV-005 | Primary | Post-mitigation risk reassessment in risk management cycle |
| MEASURE 3 | 3.1 | Feedback from affected communities is incorporated | PROC-GOV-005 | Supporting | Customer feedback on AI agent behavior informs risk assessment |
| MEASURE 3 | 3.2 | Mechanisms for feedback are accessible | PROC-GOV-013 | Supporting | Customer boundary integration includes feedback channels |
| MEASURE 3 | 3.3 | Feedback is used to inform AI risk management | PROC-GOV-005, PROC-GOV-010 | Primary | Feedback drives AI risk assessment updates |
| MEASURE 4 | 4.1 | Measurement approaches are documented for reproducibility | PROC-GOV-005 | Primary | Bias testing methodology documented for repeatability |
| MEASURE 4 | 4.2 | Measurement results are compared over time | PROC-GOV-005, PROC-GOV-009 | Primary | Quarterly bias testing results tracked longitudinally |
| MEASURE 4 | 4.3 | Measurement approaches leverage state-of-the-art methods | PROC-GOV-005 | Supporting | Testing methodology updated as AI evaluation science advances |

## MANAGE Function

The MANAGE function allocates resources and implements plans to respond to and recover from AI-related risks.

| Category | Subcategory | Description | Process(es) | Relationship | Implementation Notes |
|----------|-------------|-------------|-------------|-------------|---------------------|
| MANAGE 1 | 1.1 | AI risk treatment plans are developed | PROC-GOV-005 | Primary | Risk management (Activity 5.2) defines mitigations |
| MANAGE 1 | 1.2 | Treatment actions are prioritized by risk level | PROC-GOV-005 | Primary | Risk-based prioritization of AI risk mitigations |
| MANAGE 1 | 1.3 | Responses to identified AI risks are documented | PROC-GOV-005, PROC-GOV-009 | Primary | Risk management documentation + evidence collection |
| MANAGE 1 | 1.4 | Negative risks are mitigated when possible | PROC-GOV-005 | Primary | Hook system, human oversight, output validation |
| MANAGE 2 | 2.1 | Resources for AI risk management are allocated | PROC-GOV-005 | Primary | Executive sponsor approves budget for AI governance |
| MANAGE 2 | 2.2 | Mechanisms are in place to monitor deployment risks | PROC-GOV-010, PROC-GOV-005 | Primary | Continuous monitoring + quarterly risk reassessment |
| MANAGE 2 | 2.3 | Mechanisms are in place for rapid response to AI incidents | PROC-GOV-006, PROC-GOV-005 | Primary | Incident reporting + AI-specific incident procedures |
| MANAGE 2 | 2.4 | Processes for retiring AI systems are defined | PROC-GOV-005 | Supporting | AI system lifecycle includes decommission procedures |
| MANAGE 3 | 3.1 | AI risk management activities are documented and communicated | PROC-GOV-005, PROC-GOV-009 | Primary | Federal reporting (Activity 5.6) + evidence collection |
| MANAGE 3 | 3.2 | Risk-relevant information is communicated to stakeholders | PROC-GOV-005, PROC-GOV-013 | Primary | AI transparency reports to federal customers + boundary docs |
| MANAGE 4 | 4.1 | Post-deployment AI system monitoring is in place | PROC-GOV-010 | Primary | Continuous monitoring includes AI system health |
| MANAGE 4 | 4.2 | Processes address AI system changes that are significant | PROC-GOV-010 | Primary | Significant change management for AI model updates |
| MANAGE 4 | 4.3 | Pre-established criteria for AI system retirement are defined | PROC-GOV-005 | Supporting | AI system inventory includes lifecycle status |

---

## Coverage Summary by Function

| AI RMF Function | Total Categories/Subcategories | Primary Coverage | Supporting Coverage | Key Process(es) |
|----------------|-------------------------------|-----------------|--------------------|--------------------|
| GOVERN | 19 | 14 | 5 | PROC-GOV-005, PROC-GOV-006 |
| MAP | 18 | 14 | 4 | PROC-GOV-005, PROC-GOV-004 |
| MEASURE | 22 | 16 | 6 | PROC-GOV-005, PROC-GOV-009, PROC-GOV-010 |
| MANAGE | 13 | 11 | 2 | PROC-GOV-005, PROC-GOV-010 |
| **Total** | **72** | **55** | **17** | — |

All 72 subcategories across the four AI RMF functions are addressed by at least one government overlay process.

## Key Observations

1. **PROC-GOV-005 (AI Transparency) is the primary vehicle** for AI RMF compliance, appearing as a primary or supporting process in the majority of subcategories. This is by design — the process was structured to align with the AI RMF's GOVERN-MAP-MEASURE-MANAGE lifecycle.

2. **PROC-GOV-010 (Continuous Monitoring) provides the MANAGE function's backbone**, ensuring that AI risk management is not a one-time activity but an ongoing operational capability.

3. **PROC-GOV-004 (Supply Chain Assurance) addresses third-party AI risks**, which is critical given claude-kit's dependence on Anthropic's Claude API. The supply chain process evaluates Anthropic as a critical supplier and tracks model version changes.

4. **PROC-GOV-006 (CUI Handling) addresses AI-specific privacy risks** related to CUI appearing in AI agent context windows during developer sessions.

5. **PROC-GOV-013 (Customer Boundary Integration) supports stakeholder communication** by defining how AI risk information is shared with customers through the shared responsibility model.

---

## Cross-Reference: AI-Relevant Controls from Other Standards

The AI RMF does not exist in isolation. Several AI-relevant controls from other standards are addressed by the same QMS processes:

| Standard | Control/Section | AI Relevance | Mapped Process |
|----------|----------------|-------------- |----------------|
| NIST SP 800-53 Rev 5 | SI-4 (System Monitoring) | AI system behavior monitoring | PROC-GOV-010 |
| NIST SP 800-53 Rev 5 | AU-6 (Audit Review) | AI action audit trail review | PROC-GOV-009 |
| NIST SP 800-53 Rev 5 | SA-9 (External System Services) | Anthropic API as external AI service | PROC-GOV-004, PROC-GOV-013 |
| EO 14110 | Section 4 (AI Safety) | Federal AI safety requirements | PROC-GOV-005 |
| OMB M-25-22 | AI Use Case Inventory | Federal AI transparency mandate | PROC-GOV-005 |
| NDAA FY2024 §1513 | AI Transparency | Legislative AI disclosure requirement | PROC-GOV-005 |
| ISO/IEC 42001 | All clauses | International AI management system | PROC-GOV-005 (partial alignment) |

---

## Change History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 2026-02-28 | Mateo Segura | Initial release |
