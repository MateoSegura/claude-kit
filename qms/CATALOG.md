# Process Catalog

Master index of all processes in the Process Asset Library.

## Base Layer — Commercial (24 Processes)

### Lifecycle Processes

| ID | Process | Version | Status | Maturity |
|----|---------|---------|--------|----------|
| PROC-LC-001 | Market Analysis | 1.0.0 | draft | initial |
| PROC-LC-002 | Requirements Engineering | 1.0.0 | draft | initial |
| PROC-LC-003 | Architecture Design | 1.0.0 | draft | initial |
| PROC-LC-004 | Implementation | 1.0.0 | draft | initial |
| PROC-LC-005 | Integration & Testing | 1.0.0 | draft | initial |
| PROC-LC-006 | Release Management | 1.0.0 | draft | initial |
| PROC-LC-007 | Deployment & Operations | 1.0.0 | draft | initial |
| PROC-LC-008 | Continuous Improvement | 1.0.0 | draft | initial |

### Support Processes

| ID | Process | Version | Status | Maturity |
|----|---------|---------|--------|----------|
| PROC-SP-001 | Configuration Management | 1.0.0 | draft | initial |
| PROC-SP-002 | Quality Assurance | 1.0.0 | draft | initial |
| PROC-SP-003 | Verification & Validation | 1.0.0 | draft | initial |
| PROC-SP-004 | Documentation Management | 1.0.0 | draft | initial |
| PROC-SP-005 | Defect Management | 1.0.0 | draft | initial |
| PROC-SP-006 | Peer Review | 1.0.0 | draft | initial |

### Organizational Processes

| ID | Process | Version | Status | Maturity |
|----|---------|---------|--------|----------|
| PROC-ORG-001 | Process Governance | 1.0.0 | draft | initial |
| PROC-ORG-002 | Measurement & Analysis | 1.0.0 | draft | initial |
| PROC-ORG-003 | Training | 1.0.0 | draft | initial |
| PROC-ORG-004 | Risk Management | 1.0.0 | draft | initial |
| PROC-ORG-005 | Supplier Management | 1.0.0 | draft | initial |

### Security Processes

| ID | Process | Version | Status | Maturity |
|----|---------|---------|--------|----------|
| PROC-SEC-001 | Secure Development | 1.0.0 | draft | initial |
| PROC-SEC-002 | Vulnerability Management | 1.0.0 | draft | initial |
| PROC-SEC-003 | Incident Response | 1.0.0 | draft | initial |
| PROC-SEC-004 | Access Control | 1.0.0 | draft | initial |
| PROC-SEC-005 | Encryption & Key Management | 1.0.0 | draft | initial |

## Government Overlay (13 Processes)

### Compliance Processes

| ID | Process | Version | Status | Maturity | Extends |
|----|---------|---------|--------|----------|---------|
| PROC-GOV-001 | CMMC Compliance | 1.0.0 | draft | initial | PROC-SP-002, PROC-SEC-* |
| PROC-GOV-002 | FedRAMP Authorization | 1.0.0 | draft | initial | PROC-SP-002, PROC-SEC-* |
| PROC-GOV-003 | Export Control | 1.0.0 | draft | initial | PROC-LC-004, PROC-LC-006 |
| PROC-GOV-004 | Supply Chain Assurance | 1.0.0 | draft | initial | PROC-ORG-005, PROC-SEC-002 |
| PROC-GOV-005 | AI Transparency | 1.0.0 | draft | initial | PROC-LC-002, PROC-SP-003 |
| PROC-GOV-006 | CUI Handling | 1.0.0 | draft | initial | PROC-SEC-004, PROC-SEC-005 |
| PROC-GOV-007 | Zero Trust Alignment | 1.0.0 | draft | initial | PROC-SEC-004 |

### Audit Processes

| ID | Process | Version | Status | Maturity | Extends |
|----|---------|---------|--------|----------|---------|
| PROC-GOV-008 | Audit Readiness | 1.0.0 | draft | initial | PROC-SP-002 |
| PROC-GOV-009 | Evidence Collection | 1.0.0 | draft | initial | PROC-ORG-002 |
| PROC-GOV-010 | Continuous Monitoring | 1.0.0 | draft | initial | PROC-SEC-002 |

### Deployment Processes

| ID | Process | Version | Status | Maturity | Extends |
|----|---------|---------|--------|----------|---------|
| PROC-GOV-011 | Air-Gap Deployment | 1.0.0 | draft | initial | PROC-LC-006, PROC-LC-007 |
| PROC-GOV-012 | Impact Level Qualification | 1.0.0 | draft | initial | PROC-GOV-002 |
| PROC-GOV-013 | Customer Boundary Integration | 1.0.0 | draft | initial | PROC-GOV-001 |

## Statistics

| Metric | Value |
|--------|-------|
| Total processes | 37 |
| Base layer | 24 |
| Government overlay | 13 |
| Status: active | 0 |
| Status: draft | 37 |
| Maturity: initial | 37 |

## Process File Locations

| Category | Directory |
|----------|-----------|
| Lifecycle | `qms/processes/base/lifecycle/` |
| Support | `qms/processes/base/support/` |
| Organizational | `qms/processes/base/organizational/` |
| Security | `qms/processes/base/security/` |
| Compliance (gov) | `qms/processes/gov/compliance/` |
| Audit (gov) | `qms/processes/gov/audit/` |
| Deployment (gov) | `qms/processes/gov/deployment/` |
