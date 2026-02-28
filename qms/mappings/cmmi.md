# CMMI-DEV v2.0 — Process Mapping

Maps QMS base processes to CMMI for Development v2.0 practice areas.

## Practice Area Mapping

| CMMI Practice Area | QMS Process(es) | Level | Coverage |
|-------------------|----------------|-------|----------|
| **Capability** | | | |
| CAR (Causal Analysis & Resolution) | PROC-LC-008 | 4 | Full |
| CM (Configuration Management) | PROC-SP-001 | 2 | Full |
| DAR (Decision Analysis & Resolution) | PROC-LC-003 | 3 | Partial — ADR process |
| EST (Estimating) | PROC-LC-004 | 2 | Partial |
| GOV (Governance) | PROC-ORG-001 | 2 | Full |
| II (Implementation Infrastructure) | PROC-LC-004 | 3 | Full |
| MC (Monitor & Control) | PROC-ORG-002 | 2 | Full |
| MPM (Managing Performance & Measurement) | PROC-ORG-002 | 4 | Full |
| OT (Organizational Training) | PROC-ORG-003 | 3 | Full |
| PA (Process Assurance) | PROC-SP-002, PROC-SP-006 | 2 | Full |
| PAD (Process Asset Development) | PROC-ORG-001 | 3 | Full |
| PCM (Process Management) | PROC-ORG-001 | 3 | Full |
| PI (Product Integration) | PROC-LC-005 | 3 | Full |
| PR (Peer Reviews) | PROC-SP-006 | 2 | Full |
| PLAN (Planning) | PROC-LC-002, PROC-LC-004 | 2 | Full |
| QEW (Quality Engineering Work) | PROC-SP-002 | 2 | Full |
| RDM (Requirements Development & Mgmt) | PROC-LC-002 | 3 | Full |
| RSK (Risk & Opportunity Management) | PROC-ORG-004 | 3 | Full |
| SAM (Supplier Agreement Management) | PROC-ORG-005 | 2 | Full |
| TS (Technical Solution) | PROC-LC-003, PROC-LC-004 | 3 | Full |
| VAL (Validation) | PROC-SP-003 | 3 | Full |
| VER (Verification) | PROC-SP-003, PROC-LC-005 | 3 | Full |

## Maturity Level Coverage

| CMMI Level | Required PAs | Mapped PAs | Coverage |
|-----------|-------------|-----------|----------|
| 2 (Managed) | 10 | 10 | 100% |
| 3 (Defined) | 18 | 18 | 100% |
| 4 (Quantitatively Managed) | 20 | 20 | 100% |
| 5 (Optimizing) | 22 | 21 | 95% |

## Gap Analysis

- **SEC (Security):** CMMI v2.0 Security practice area is fully covered by
  PROC-SEC-001 through PROC-SEC-005
- **SSE (Safety & Security Engineering):** Partially covered — claude-kit
  is not a safety-critical system, so full SSE is not applicable
