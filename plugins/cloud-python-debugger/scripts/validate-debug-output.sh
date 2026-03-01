#!/usr/bin/env bash
set -euo pipefail
# validate-debug-output.sh — Background check for common failure patterns in bash output
# Called by hooks.json as an async PostToolUse hook on Bash tool
# Requires: jq

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')
OUTPUT=$(echo "$INPUT" | jq -r '.tool_response // empty')

# Nothing to validate if output is empty
if [[ -z "$OUTPUT" ]]; then
  echo "NOTE: Command produced no output. If data was expected, verify the command is targeting the correct resource." >&2
  exit 0
fi

HINTS=()

# Detect connection refused
if echo "$OUTPUT" | grep -qiE '(connection refused|connect: refused|ECONNREFUSED|dial tcp.*refused)'; then
  HINTS+=("CONNECTION REFUSED detected. Hint: verify the service is running ('kubectl get pods', 'docker ps'), check port mappings, and confirm network policies/firewall rules are not blocking access.")
fi

# Detect permission denied
if echo "$OUTPUT" | grep -qiE '(permission denied|Access Denied|Unauthorized|403 Forbidden|EPERM|PermissionError)'; then
  HINTS+=("PERMISSION DENIED detected. Hint: check IAM roles, RBAC policies ('kubectl auth can-i'), service account bindings, or file system ACLs. Avoid escalating privileges — identify the minimal missing permission instead.")
fi

# Detect empty / no-results output that may indicate misconfiguration
if echo "$OUTPUT" | grep -qiE '(No resources found|0 results|empty|no items|null$)'; then
  HINTS+=("EMPTY RESULT detected. Hint: confirm the namespace ('kubectl -n <ns>'), label selectors, time range, or filter criteria. The resource may exist under a different name or scope.")
fi

# Detect Python tracebacks
if echo "$OUTPUT" | grep -qE 'Traceback \(most recent call last\)'; then
  HINTS+=("PYTHON TRACEBACK detected. Hint: record the full exception type and message, identify the innermost frame in your own code (not third-party), and check for recent dependency version changes or configuration drift.")
fi

# Detect OOM / memory signals
if echo "$OUTPUT" | grep -qiE '(OOMKilled|out of memory|MemoryError|Killed.*memory|Cannot allocate memory)'; then
  HINTS+=("OUT-OF-MEMORY signal detected. Hint: use 'memray' or 'py-spy' to profile heap usage. Review Kubernetes resource limits and consider whether the workload has grown beyond its originally configured bounds.")
fi

# Detect timeout
if echo "$OUTPUT" | grep -qiE '(timeout|timed out|deadline exceeded|context deadline)'; then
  HINTS+=("TIMEOUT detected. Hint: isolate whether the timeout is at the network layer, application layer, or infrastructure (load balancer/proxy). Use 'grpcurl' or curl with verbose flags to measure each hop independently.")
fi

if [[ ${#HINTS[@]} -gt 0 ]]; then
  echo "--- Debug Output Validation Hints ---" >&2
  for HINT in "${HINTS[@]}"; do
    echo "  * $HINT" >&2
  done
  echo "--------------------------------------" >&2
fi

exit 0
