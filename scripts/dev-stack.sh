#!/usr/bin/env bash
set -euo pipefail

# scripts/dev-stack.sh — manage the local development stack
#
# Usage:
#   bash scripts/dev-stack.sh status    # check what's running
#   bash scripts/dev-stack.sh up        # start everything
#   bash scripts/dev-stack.sh down      # stop everything
#   bash scripts/dev-stack.sh restart   # restart everything

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${REPO_ROOT}/api/docker-compose.yml"
DASHBOARD_DIR="${REPO_ROOT}/apps/dashboard"
DASHBOARD_LOG="/tmp/dashboard-dev.log"

# Docker gateway — devcontainer accesses API containers via this IP
DOCKER_GW="172.17.0.1"
API_PORT=8000
DASHBOARD_PORT=5173

info()  { echo "  [dev-stack] $*"; }
ok()    { echo "  [dev-stack] ✓ $*"; }
warn()  { echo "  [dev-stack] ! $*"; }

# ── health checks ─────────────────────────────────────────────────────────────

check_api() {
  curl -sf --max-time 3 "http://${DOCKER_GW}:${API_PORT}/healthz" > /dev/null 2>&1
}

check_db() {
  docker compose -f "${COMPOSE_FILE}" exec -T db pg_isready -U postgres > /dev/null 2>&1
}

check_dashboard() {
  curl -sf --max-time 3 "http://localhost:${DASHBOARD_PORT}/" > /dev/null 2>&1
}

status_line() {
  local name="$1" check_fn="$2" port="$3"
  if $check_fn; then
    ok "${name}: up (port ${port})"
    return 0
  else
    warn "${name}: down (port ${port})"
    return 1
  fi
}

# ── commands ──────────────────────────────────────────────────────────────────

cmd_status() {
  local all_up=0
  status_line "api" check_api "${API_PORT}" || all_up=1
  status_line "db" check_db "5432" || all_up=1
  status_line "dashboard" check_dashboard "${DASHBOARD_PORT}" || all_up=1
  return $all_up
}

cmd_up() {
  # 1. Start API + DB via Docker Compose
  if ! check_api || ! check_db; then
    info "starting API + DB via Docker Compose..."
    docker compose -f "${COMPOSE_FILE}" up -d --build 2>&1 | tail -5
    # Wait for API to be healthy
    for i in $(seq 1 30); do
      if check_api; then
        ok "API is healthy"
        break
      fi
      sleep 1
    done
    if ! check_api; then
      warn "API did not become healthy within 30s — check docker logs"
    fi
  else
    ok "API + DB already running"
  fi

  # 2. Start Dashboard dev server
  if ! check_dashboard; then
    info "starting dashboard dev server on port ${DASHBOARD_PORT}..."
    # Kill any stale vite processes
    pkill -f "vite dev" 2>/dev/null || true
    sleep 1
    cd "${DASHBOARD_DIR}"
    # Install deps if needed
    if [ ! -d "node_modules" ]; then
      info "installing dashboard dependencies..."
      npm install --silent 2>&1 | tail -3
    fi
    nohup npx vite dev --port "${DASHBOARD_PORT}" --host > "${DASHBOARD_LOG}" 2>&1 &
    disown
    # Wait for it to be ready
    for i in $(seq 1 15); do
      if check_dashboard; then
        ok "dashboard is ready at http://localhost:${DASHBOARD_PORT}/"
        break
      fi
      sleep 1
    done
    if ! check_dashboard; then
      warn "dashboard did not start — check ${DASHBOARD_LOG}"
    fi
    cd "${REPO_ROOT}"
  else
    ok "dashboard already running"
  fi

  echo ""
  cmd_status
}

cmd_down() {
  info "stopping dashboard..."
  pkill -f "vite dev" 2>/dev/null || true

  info "stopping API + DB..."
  docker compose -f "${COMPOSE_FILE}" down 2>&1 | tail -3

  ok "all services stopped"
}

cmd_restart() {
  cmd_down
  sleep 2
  cmd_up
}

# ── main ──────────────────────────────────────────────────────────────────────

case "${1:-status}" in
  status)  cmd_status ;;
  up)      cmd_up ;;
  down)    cmd_down ;;
  restart) cmd_restart ;;
  *)
    echo "Usage: $0 {status|up|down|restart}"
    exit 1
    ;;
esac
