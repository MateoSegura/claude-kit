# Diagnostic Standards

Structured finding format and severity classification for all debugger output.

## Finding JSON Schema

Every diagnostic finding MUST conform to this schema. Fields marked required must always be present; optional fields may be omitted when not applicable.

```json
{
  "finding_id": "string (required) — unique identifier, format: DOMAIN-NNN",
  "timestamp": "string (required) — ISO 8601 when finding was produced",
  "symptom": "string (required) — observed failure as reported or detected",
  "severity": "string (required) — critical | high | medium | low | info",
  "failure_domain": "string (required) — one of: hard_fault, stack_overflow, kernel_panic, deadlock_timing, peripheral_failure, boot_failure, network_failure, postmortem",
  "affected_component": {
    "subsystem": "string (required) — Zephyr subsystem or driver name",
    "file_path": "string (optional) — source file if identified",
    "line_number": "number (optional) — source line if identified",
    "function": "string (optional) — function name if identified",
    "device_node": "string (optional) — devicetree node path if applicable"
  },
  "time_window": {
    "first_observed": "string (optional) — when symptom first appeared",
    "frequency": "string (optional) — once | intermittent | every_boot | periodic",
    "trigger_condition": "string (optional) — what triggers the failure"
  },
  "evidence_chain": [
    {
      "source": "string (required) — artifact type: register, log, memory, stack_frame, config, gdb_output",
      "observation": "string (required) — what was observed",
      "raw_value": "string (optional) — exact value (hex for registers, text for logs)",
      "timestamp": "string (optional) — when this evidence was collected",
      "significance": "string (required) — why this evidence matters for diagnosis"
    }
  ],
  "eliminated_hypotheses": [
    {
      "hypothesis": "string (required) — what was considered",
      "evidence_against": "string (required) — why it was ruled out"
    }
  ],
  "root_cause": "string (required) — definitive cause, or 'Inconclusive' if undetermined",
  "confidence": {
    "level": "string (required) — high | medium | low",
    "percentage": "number (required) — 0-100",
    "rationale": "string (required) — why this confidence level"
  },
  "ranked_candidates": [
    {
      "cause": "string — candidate root cause",
      "confidence_pct": "number — 0-100",
      "supporting_evidence": "string — key evidence for this candidate",
      "additional_data_needed": "string (optional) — what would confirm or refute"
    }
  ],
  "impact_assessment": {
    "blast_radius": "string (required) — what else is affected",
    "duration": "string (required) — transient | persistent | progressive",
    "data_impact": "string (required) — none | corrupted | lost | unknown"
  },
  "recommended_fix": {
    "action": "string (required) — what to change",
    "files": ["string — file paths to modify"],
    "config_changes": ["string — Kconfig or DTS changes needed"],
    "verification": "string (required) — how to confirm the fix worked",
    "prevention": "string (optional) — how to prevent recurrence"
  }
}
```

## Severity Classification

| Severity | Criteria | Examples |
|----------|----------|---------|
| **critical** | System non-functional, data loss risk, security vulnerability | Hard fault in production, stack overflow corrupting adjacent memory, MCUboot signature bypass |
| **high** | Major feature broken, workaround exists but degraded | Kernel panic on specific input, peripheral driver fails after 1000 operations, BLE disconnects under load |
| **medium** | Feature partially impaired, non-critical path affected | Intermittent I2C NAK on one sensor, log output garbled at high rates, shell command hangs occasionally |
| **low** | Minor issue, cosmetic, or optimization opportunity | Unnecessary stack allocation, suboptimal Kconfig selection, unused DTS node warning |
| **info** | Observation, no immediate action needed | Thread stack usage at 70% capacity, flash wear approaching threshold, deprecated API in use |

## Severity Decision Tree

1. Does the failure crash or hang the system? -> **critical**
2. Does the failure corrupt data or memory beyond the faulting component? -> **critical**
3. Does the failure break a primary feature with no workaround? -> **high**
4. Does the failure break a primary feature with a workaround? -> **high**
5. Does the failure affect a secondary feature or non-critical path? -> **medium**
6. Is the failure cosmetic, minor, or an optimization opportunity? -> **low**
7. Is it an observation with no immediate impact? -> **info**

## Confidence Calibration

| Level | Range | Meaning |
|-------|-------|---------|
| **high** | 80-100% | Root cause identified with strong evidence chain. Multiple independent artifacts corroborate. Fix recommendation is specific and testable. |
| **medium** | 50-79% | Probable root cause identified but evidence is incomplete. One or two key artifacts missing. Fix recommendation addresses most likely cause. |
| **low** | 0-49% | Multiple candidate causes with insufficient evidence to differentiate. Ranked candidates provided. Additional data collection recommended before applying fixes. |

## Evidence Quality Criteria

Evidence is graded by directness and reliability:

| Grade | Description | Examples |
|-------|-------------|---------|
| **Direct** | Artifact directly shows the fault | CFSR register value, faulting PC address, assertion message |
| **Corroborating** | Artifact supports the diagnosis indirectly | Thread state dump showing contention, log timestamp correlation |
| **Circumstantial** | Artifact is consistent with but does not prove the diagnosis | Similar symptoms in documentation, timing coincidence |
| **Inferred** | Conclusion drawn from absence of other evidence | "Not a stack overflow because sentinel is intact" |

A high-confidence finding requires at least one direct evidence item. Medium-confidence requires at least one corroborating item. Low-confidence may rely on circumstantial and inferred evidence only.
