#!/bin/bash
set -euo pipefail
# check-debug-environment.sh — Verifies debugging tools are available at session start
# Called by hooks.json as a SessionStart hook
# Requires: jq (but checks for it first)
# Non-blocking: all checks emit warnings, never exit 2

WARNINGS=()

# --- Core prerequisites ---

if ! command -v python3 &>/dev/null; then
  WARNINGS+=("python3 not found. Python debugging is unavailable. Install Python 3.8+ to proceed.")
fi

if ! command -v jq &>/dev/null; then
  WARNINGS+=("jq not found. Hook scripts require jq for JSON parsing. Install with: apt install jq / brew install jq")
fi

# --- Container runtime ---

if ! command -v docker &>/dev/null; then
  WARNINGS+=("docker not found. Container-level debugging commands will be unavailable.")
fi

# --- Kubernetes (only warn if a k8s context is actually configured) ---

if command -v kubectl &>/dev/null; then
  # Check whether any context is set
  CURRENT_CONTEXT=$(kubectl config current-context 2>/dev/null || true)
  if [[ -z "$CURRENT_CONTEXT" ]]; then
    WARNINGS+=("kubectl is installed but no current context is set. Run 'kubectl config use-context <name>' to activate a cluster context before debugging Kubernetes workloads.")
  fi
else
  # Only warn if a kubeconfig exists (implies intent to use k8s)
  if [[ -f "${HOME}/.kube/config" ]]; then
    WARNINGS+=("kubeconfig found at ~/.kube/config but kubectl is not installed. Install kubectl to enable Kubernetes debugging.")
  fi
fi

# --- Python profiling tools ---

if ! command -v py-spy &>/dev/null && ! python3 -m py_spy --version &>/dev/null 2>&1; then
  WARNINGS+=("py-spy not found. CPU profiling and stack sampling will be unavailable. Install with: pip install py-spy")
fi

if ! python3 -c 'import memray' &>/dev/null 2>&1; then
  WARNINGS+=("memray not found. Memory profiling will be unavailable. Install with: pip install memray")
fi

# --- gRPC debugging ---

if ! command -v grpcurl &>/dev/null; then
  WARNINGS+=("grpcurl not found. gRPC service inspection will be unavailable. Install with: brew install grpcurl / go install github.com/fullstorydev/grpcurl/cmd/grpcurl@latest")
fi

# --- Emit all warnings and exit cleanly (non-blocking) ---

if [[ ${#WARNINGS[@]} -gt 0 ]]; then
  echo "--- Cloud Python Debugger: Environment Warnings ---" >&2
  for W in "${WARNINGS[@]}"; do
    echo "  WARNING: $W" >&2
  done
  echo "----------------------------------------------------" >&2
  echo "These are non-blocking warnings. Debugging will proceed with the tools that are available." >&2
fi

exit 0
