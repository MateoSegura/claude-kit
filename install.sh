#!/usr/bin/env bash
set -euo pipefail

KIT_HOME="${KIT_HOME:-$HOME/.claude-kit}"
REPO_URL="https://github.com/MateoSegura/claude-kit.git"
BIN_DIR="$HOME/.local/bin"

# Colors
_G='\033[0;32m'
_B='\033[0;34m'
_Y='\033[0;33m'
_R='\033[0;31m'
_N='\033[0m'

info() { echo -e "${_B}[claude-kit]${_N} $*"; }
ok()   { echo -e "${_G}[claude-kit]${_N} $*"; }
warn() { echo -e "${_Y}[claude-kit]${_N} $*"; }
err()  { echo -e "${_R}[claude-kit]${_N} $*" >&2; }

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
  info "Updating ..."
  git -C "$KIT_HOME" pull --ff-only -q
  VER=$(git -C "$KIT_HOME" describe --tags --always 2>/dev/null || git -C "$KIT_HOME" rev-parse --short HEAD)
  ok "Updated → $VER"
else
  info "Installing ..."
  git clone "$REPO_URL" "$KIT_HOME" -q
  VER=$(git -C "$KIT_HOME" describe --tags --always 2>/dev/null || git -C "$KIT_HOME" rev-parse --short HEAD)
  ok "Installed → $VER"
fi

chmod +x "$KIT_HOME/claude-kit"

# ── Create local plugin directory and mark as user install ────────────────────

mkdir -p "$KIT_HOME/local/plugins"
touch "$KIT_HOME/.installed"

# ── Link binary ───────────────────────────────────────────────────────────────

mkdir -p "$BIN_DIR"
ln -sf "$KIT_HOME/claude-kit" "$BIN_DIR/claude-kit"

# ── Add to PATH ───────────────────────────────────────────────────────────────

PATH_LINE='export PATH="$HOME/.local/bin:$PATH"'

add_to_rc() {
  local rc="$1"
  if [ -f "$rc" ] && ! grep -qF 'local/bin' "$rc" 2>/dev/null; then
    echo "" >> "$rc"
    echo "# claude-kit" >> "$rc"
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

_W='\033[1;37m'
_C='\033[0;36m'
_DIM='\033[2m'

echo ""

# PATH notice if needed
if ! command -v claude-kit &>/dev/null 2>&1; then
  echo -e "  ${_Y}Note:${_N} Restart your shell or run:"
  echo -e "    ${_C}export PATH=\"\$HOME/.local/bin:\$PATH\"${_N}"
  echo ""
fi

echo -e "  ${_W}claude-kit${_N}  installed"
echo ""
echo -e "  ${_DIM}────────────────────────────────────────────────────────${_N}"
echo ""
echo -e "  ${_C}claude-kit setup${_N}"
echo -e "  ${_DIM}  configure Claude Code features (statusline, etc.)${_N}"
echo ""
echo -e "  ${_C}claude-kit list${_N}"
echo -e "  ${_DIM}  browse available kits${_N}"
echo ""
echo -e "  ${_C}claude-kit --kit <name>${_N}"
echo -e "  ${_DIM}  launch a kit in Claude Code${_N}"
echo ""
echo -e "  ${_C}claude-kit --kit <name> --kit core-planner${_N}"
echo -e "  ${_DIM}  combine multiple kits in one session${_N}"
echo ""
echo -e "  ${_C}claude-kit --kit <name> --yolo${_N}"
echo -e "  ${_DIM}  skip permission prompts${_N}"
echo ""
echo -e "  ${_C}claude-kit update${_N}"
echo -e "  ${_DIM}  pull latest plugins and scripts${_N}"
echo ""
echo -e "  ${_DIM}────────────────────────────────────────────────────────${_N}"
echo -e "  ${_DIM}github.com/MateoSegura/claude-kit${_N}"
echo ""
