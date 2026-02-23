#!/usr/bin/env bash
# .devcontainer/ctl.sh — dev container lifecycle management
#
# Usage: .devcontainer/ctl.sh <build|push|create|start>
#
# Prerequisites:
#   build/push    docker (Desktop or CLI)
#   create/start  @devcontainers/cli  →  npm install -g @devcontainers/cli
#   create/start  .devcontainer/.env   →  copy .env.example, fill in values

set -euo pipefail

IMAGE="ghcr.io/mateosegura/dev-env-claude-kit:latest"
PLATFORM="linux/amd64"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ENV_FILE="${SCRIPT_DIR}/.env"

# ── helpers ───────────────────────────────────────────────────────────────────
info()  { echo "  [ctl] $*"; }
ok()    { echo "  [ctl] ✓ $*"; }
die()   { echo "  [ctl] ✗ $*" >&2; exit 1; }

usage() {
  cat <<EOF

  Usage: .devcontainer/ctl.sh <action>

  Actions:
    build    Build the image locally (linux/amd64)
    push     Authenticate via .env token and push to ghcr.io
    create   Load .env, create and start the devcontainer (gh + ghcr auth inside)
    start    Load .env, open a shell in the running container

  Setup:
    cp .devcontainer/.env.example .devcontainer/.env
    # Fill in GITHUB_TOKEN, then run: .devcontainer/ctl.sh create

EOF
  exit 1
}

# Load .env and export vars so devcontainer picks them up via localEnv
_load_env() {
  if [ ! -f "${ENV_FILE}" ]; then
    die "Missing .env — run: cp .devcontainer/.env.example .devcontainer/.env"
  fi
  set -a
  # shellcheck source=/dev/null
  source "${ENV_FILE}"
  set +a
  [ -z "${GITHUB_TOKEN:-}" ] && die "GITHUB_TOKEN is empty in .env"
  [ -z "${IS_SANDBOX:-}" ]   && die "IS_SANDBOX is empty in .env (must be 1)"
}

# ── actions ───────────────────────────────────────────────────────────────────
cmd_build() {
  info "Building ${IMAGE} ..."
  docker build \
    --platform "${PLATFORM}" \
    --tag "${IMAGE}" \
    "${SCRIPT_DIR}"
  ok "Build complete — ${IMAGE}"
}

cmd_push() {
  _load_env
  info "Authenticating with ghcr.io ..."
  echo "${GITHUB_TOKEN}" | docker login ghcr.io -u MateoSegura --password-stdin
  info "Pushing ${IMAGE} ..."
  docker push "${IMAGE}"
  ok "Push complete — ${IMAGE}"
}

cmd_create() {
  command -v devcontainer > /dev/null 2>&1 \
    || die "devcontainer CLI not found — run: npm install -g @devcontainers/cli"
  _load_env
  info "Creating devcontainer (gh + ghcr.io auth will run inside) ..."
  devcontainer up --workspace-folder "${REPO_ROOT}"
  ok "Devcontainer ready.  Run: .devcontainer/ctl.sh start"
}

cmd_start() {
  command -v devcontainer > /dev/null 2>&1 \
    || die "devcontainer CLI not found — run: npm install -g @devcontainers/cli"
  _load_env
  info "Opening shell (root, IS_SANDBOX=1) ..."
  devcontainer exec --workspace-folder "${REPO_ROOT}" bash
}

# ── dispatch ──────────────────────────────────────────────────────────────────
case "${1:-}" in
  build)  cmd_build  ;;
  push)   cmd_push   ;;
  create) cmd_create ;;
  start)  cmd_start  ;;
  *)      usage      ;;
esac
