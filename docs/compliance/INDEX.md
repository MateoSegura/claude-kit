# compliance/ — Regulatory Compliance Artifacts

**Governing Processes:** PROC-GOV-001 through PROC-GOV-013

## Purpose

This directory contains compliance artifacts produced by government overlay
processes. These artifacts demonstrate alignment with regulatory frameworks
(CMMC, FedRAMP, NIST 800-171, etc.) and support customer procurement reviews.

## Structure

```
compliance/
├── control-mappings/   ← NIST 800-171, 800-53, AI RMF evidence
└── customer-packages/  ← Extractable customer deliverables
```

## Control Mappings

Control mappings document how project processes and artifacts satisfy specific
regulatory controls. Each mapping file covers one control family or framework.

## Customer Packages

Customer-deliverable documents packaged by `pal/scripts/extract-qms.sh`.
These are designed for defense procurement officers, SOC 2 auditors, and
CMMC C3PAOs.

## Creating New Documents

Compliance artifacts are governed by the PROC-GOV-* processes. Consult the
governing process's Section 6 (Outputs/Artifacts) for the required structure.
