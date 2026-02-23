#!/usr/bin/env bash
# .devcontainer/ctl.sh — dev container lifecycle management
#
# Usage: .devcontainer/ctl.sh <build|push|create|start>
#
# Prerequisites:
#   build/push  docker (Desktop or CLI)
#   create/start  @devcontainers/cli  →  npm install -g @devcontainers/cli
#   push        gh auth login  (token used to authenticate with ghcr.io)

set -euo pipefail

IMAGE="ghcr.io/mateosegura/dev-env-claude-kit:latest"
PLATFORM="linux/amd64"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# ── helpers ───────────────────────────────────────────────────────────────────
info()  { echo "  [ctl] $*"; }
ok()    { echo "  [ctl] ✓ $*"; }
die()   { echo "  [ctl] ✗ $*" >&2; exit 1; }

usage() {
  cat <<EOF

  Usage: .devcontainer/ctl.sh <action>

  Actions:
    build    Build the image locally (linux/amd64)
    push     Authenticate with ghcr.io via gh token and push the image
    create   Create (or recreate) the devcontainer
    start    Open an interactive bash shell inside the running container

EOF
  exit 1
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
  command -v gh > /dev/null 2>&1 || die "gh not found — run: gh auth login"
  info "Authenticating with ghcr.io ..."
  gh auth token | docker login ghcr.io -u MateoSegura --password-stdin
  info "Pushing ${IMAGE} ..."
  docker push "${IMAGE}"
  ok "Push complete — ${IMAGE}"
}

cmd_create() {
  command -v devcontainer > /dev/null 2>&1 \
    || die "devcontainer CLI not found — run: npm install -g @devcontainers/cli"
  info "Creating devcontainer (this may pull the image) ..."
  devcontainer up --workspace-folder "${REPO_ROOT}"
  ok "Devcontainer ready."
}

cmd_start() {
  command -v devcontainer > /dev/null 2>&1 \
    || die "devcontainer CLI not found — run: npm install -g @devcontainers/cli"
  info "Opening shell in devcontainer ..."
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
