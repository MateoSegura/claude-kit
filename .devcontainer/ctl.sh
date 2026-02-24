#!/usr/bin/env bash
# .devcontainer/ctl.sh — dev container lifecycle management
#
# Host actions:   build | push | create | start
# Container actions (called by devcontainer.json):  post-create | post-start
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
warn()  { echo "  [ctl] ! $*"; }
die()   { echo "  [ctl] ✗ $*" >&2; exit 1; }

usage() {
  cat <<EOF

  Usage: .devcontainer/ctl.sh <action>

  Host actions:
    build         Build the image locally (linux/amd64)
    push          Authenticate via .env token and push to ghcr.io
    create        Create and start the devcontainer (.env loaded via --env-file)
    start         Open a shell in the running container

  Container lifecycle (called by devcontainer.json):
    post-create   Link claude-kit CLI into PATH
    post-start    Authenticate gh and ghcr.io from GITHUB_TOKEN

  Setup:
    cp .devcontainer/.env.example .devcontainer/.env
    # Fill in GITHUB_TOKEN, then run: .devcontainer/ctl.sh create

EOF
  exit 1
}

# Load .env and export vars (host-side only — container gets them via --env-file)
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

# ── host actions ──────────────────────────────────────────────────────────────
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
  info "Creating devcontainer ..."
  devcontainer up --workspace-folder "${REPO_ROOT}"
  ok "Devcontainer ready.  Run: .devcontainer/ctl.sh start"
}

cmd_start() {
  command -v devcontainer > /dev/null 2>&1 \
    || die "devcontainer CLI not found — run: npm install -g @devcontainers/cli"
  info "Opening shell (root, IS_SANDBOX=1) ..."
  devcontainer exec --workspace-folder "${REPO_ROOT}" zsh
}

# ── container lifecycle actions ───────────────────────────────────────────────
cmd_post_create() {
  # Runs once after the container is first created
  WORKSPACE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
  ln -sf "${WORKSPACE}/claude-kit" /usr/local/bin/claude-kit
  ok "claude-kit linked to /usr/local/bin"
}

cmd_post_start() {
  # Runs every time the container starts
  if [ -z "${GITHUB_TOKEN:-}" ]; then
    warn "GITHUB_TOKEN not set — skipping auth"
    warn "Set it in .devcontainer/.env and rebuild the container"
    exit 0
  fi

  # gh: GITHUB_TOKEN in env is sufficient — no login needed
  if timeout 10 gh auth status 2>&1; then
    ok "gh authenticated (via GITHUB_TOKEN env)"
  else
    warn "gh auth status failed (non-fatal)"
  fi

  # docker: override credsStore to avoid host's wincred/desktop helper
  mkdir -p /root/.docker
  echo '{}' > /root/.docker/config.json

  if echo "${GITHUB_TOKEN}" | timeout 10 docker login ghcr.io -u MateoSegura --password-stdin 2>&1; then
    ok "ghcr.io authenticated"
  else
    warn "ghcr.io auth failed (non-fatal)"
  fi

  ok "Ready"
}

# ── dispatch ──────────────────────────────────────────────────────────────────
case "${1:-}" in
  build)        cmd_build       ;;
  push)         cmd_push        ;;
  create)       cmd_create      ;;
  start)        cmd_start       ;;
  post-create)  cmd_post_create ;;
  post-start)   cmd_post_start  ;;
  *)            usage           ;;
esac
