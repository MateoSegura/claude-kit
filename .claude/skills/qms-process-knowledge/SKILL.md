---
name: process-knowledge
description: Process Asset Library reference knowledge — process catalog, artifact-to-process mappings, standards alignment overview
allowed-tools: Read, Glob, Grep
---

# Process Knowledge

Reference knowledge about the Process Asset Library (PAL) framework. Load this
skill when reasoning about process compliance, artifact governance, or standards
alignment.

## Process Catalog Summary

The PAL defines 37 processes across two layers:

### Base Layer (24 processes)

| Category | ID Range | Count | Focus |
|----------|----------|-------|-------|
| Lifecycle | PROC-LC-001 to PROC-LC-008 | 8 | Product lifecycle from market analysis to continuous improvement |
| Support | PROC-SP-001 to PROC-SP-006 | 6 | Configuration, QA, V&V, documentation, defects, peer review |
| Organizational | PROC-ORG-001 to PROC-ORG-005 | 5 | Governance, measurement, training, risk, suppliers |
| Security | PROC-SEC-001 to PROC-SEC-005 | 5 | Secure dev, vulnerabilities, IR, access, encryption |

### Government Overlay (13 processes)

| Category | ID Range | Count | Focus |
|----------|----------|-------|-------|
| Compliance | PROC-GOV-001 to PROC-GOV-007 | 7 | CMMC, FedRAMP, export control, supply chain, AI, CUI, zero trust |
| Audit | PROC-GOV-008 to PROC-GOV-010 | 3 | Audit readiness, evidence collection, continuous monitoring |
| Deployment | PROC-GOV-011 to PROC-GOV-013 | 3 | Air-gap, impact levels, customer boundary integration |

## Artifact-to-Process Mapping

| Artifact Type | ID Pattern | Governing Process | Template |
|--------------|------------|-------------------|----------|
| Research papers | — | PROC-LC-001 | Free-form |
| Requirements | REQ-XXX | PROC-LC-002 | requirement.md.tmpl |
| Architecture decisions | ADR-XXX | PROC-LC-003 | adr.md.tmpl |
| Implementation specs | SPEC-XXX | PROC-LC-004 | spec.md.tmpl |
| Test evidence | TEST-XXX | PROC-LC-005 | test-evidence.md.tmpl |
| Regression records | REG-XXX | PROC-LC-005 | — |
| Benchmarks | BM-XXX | PROC-ORG-002 | — |
| Incident reports | INC-XXX | PROC-LC-007 | incident.md.tmpl |
| Runbooks | RB-XXX | PROC-LC-007 | — |
| Migration guides | MIG-XXX | PROC-LC-007 | — |
| Quality attributes | QA-XXX | PROC-SP-002 | quality-attribute.md.tmpl |

## Standards Alignment Overview

| Standard | Coverage | Mapping File |
|----------|----------|-------------|
| ISO/IEC 12207:2017 | All base processes | qms/mappings/iso-12207.md |
| CMMI-DEV v2.0 | All base processes | qms/mappings/cmmi.md |
| NIST SP 800-218 (SSDF) | All base processes | qms/mappings/nist-800-218.md |
| NIST SP 800-171 Rev 2 | Gov overlay | qms/mappings/nist-800-171.md |
| NIST AI RMF | AI-relevant processes | qms/mappings/nist-ai-rmf.md |

## Key Concepts

### Process Versioning
Each process has an independent semantic version. See qms/VERSION-POLICY.md.

### Maturity Model
Five levels: initial → managed → defined → measured → optimizing.
See qms/MATURITY-MODEL.md.

### Government Overlay
Gov processes EXTEND base processes — they never replace them. Every gov
process lists its base prerequisites in Section 13 (Related Processes).

### Portability
The qms/ directory has zero dependencies on project-specific code. It can
be copied to any repository and instrumented via qms/install.sh.
