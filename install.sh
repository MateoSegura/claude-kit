#!/usr/bin/env bash
set -euo pipefail

KIT_HOME="${KIT_HOME:-$HOME/.kit}"
REPO_URL="https://github.com/MateoSegura/claude-kit.git"
BIN_DIR="$HOME/.local/bin"

# Colors
_G='\033[0;32m'
_B='\033[0;34m'
_Y='\033[0;33m'
_R='\033[0;31m'
_N='\033[0m'

info() { echo -e "${_B}[kit]${_N} $*"; }
ok()   { echo -e "${_G}[kit]${_N} $*"; }
warn() { echo -e "${_Y}[kit]${_N} $*"; }
err()  { echo -e "${_R}[kit]${_N} $*" >&2; }

# ── Dependency checks ─────────────────────────────────────────────────────────

if ! command -v git &>/dev/null; then
  err "git is required but not found. Install git and try again."
  exit 1
fi

if ! command -v claude &>/dev/null; then
  err "Claude Code CLI ('claude') is required but not found."
  err "Install it from: https://claude.ai/code"
  exit 1
fi

if ! command -v jq &>/dev/null; then
  warn "jq is not installed. Alias and companion resolution will be disabled."
  warn "Install jq: https://jqlang.github.io/jq/download/"
fi

# ── Clone or update ───────────────────────────────────────────────────────────

if [ -d "$KIT_HOME/.git" ]; then
  info "Updating existing installation at $KIT_HOME ..."
  git -C "$KIT_HOME" pull --ff-only
  VER=$(git -C "$KIT_HOME" describe --tags --always 2>/dev/null || git -C "$KIT_HOME" rev-parse --short HEAD)
  ok "Updated → $VER"
else
  info "Installing kit to $KIT_HOME ..."
  git clone "$REPO_URL" "$KIT_HOME"
  VER=$(git -C "$KIT_HOME" describe --tags --always 2>/dev/null || git -C "$KIT_HOME" rev-parse --short HEAD)
  ok "Installed → $VER"
fi

chmod +x "$KIT_HOME/kit"

# ── Link binary ───────────────────────────────────────────────────────────────

mkdir -p "$BIN_DIR"
ln -sf "$KIT_HOME/kit" "$BIN_DIR/kit"

# ── Add to PATH ───────────────────────────────────────────────────────────────

PATH_LINE='export PATH="$HOME/.local/bin:$PATH"'

add_to_rc() {
  local rc="$1"
  if [ -f "$rc" ] && ! grep -qF 'local/bin' "$rc" 2>/dev/null; then
    echo "" >> "$rc"
    echo "# kit (claude plugin loader)" >> "$rc"
    echo "$PATH_LINE" >> "$rc"
    info "Added ~/.local/bin to PATH in $(basename "$rc")"
  fi
}

case "$(basename "${SHELL:-bash}")" in
  zsh)   add_to_rc "$HOME/.zshrc" ;;
  fish)
    FISH_CONFIG="$HOME/.config/fish/config.fish"
    mkdir -p "$(dirname "$FISH_CONFIG")"
    if [ -f "$FISH_CONFIG" ] && ! grep -q 'local/bin' "$FISH_CONFIG" 2>/dev/null; then
      echo 'fish_add_path "$HOME/.local/bin"' >> "$FISH_CONFIG"
      info "Added ~/.local/bin to PATH in config.fish"
    fi
    ;;
  *)     add_to_rc "$HOME/.bashrc"; add_to_rc "$HOME/.profile" ;;
esac

# ── Done ──────────────────────────────────────────────────────────────────────

echo ""
ok "kit is ready."
echo ""
echo "  If 'kit' isn't found, restart your shell or run:"
echo "    export PATH=\"\$HOME/.local/bin:\$PATH\""
echo ""
echo "  Then:"
echo "    kit list                          # see available domains"
echo "    kit run coding-embedded-zephyr    # Zephyr engineer + grader + knowledge"
echo "    kit run --yolo coding-embedded-zephyr-engineer  # no permission prompts"
echo ""
echo "  Keep plugins up to date:"
echo "    kit update"
echo ""
