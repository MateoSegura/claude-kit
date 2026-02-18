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
  info "Updating existing installation at $KIT_HOME ..."
  git -C "$KIT_HOME" pull --ff-only
  VER=$(git -C "$KIT_HOME" describe --tags --always 2>/dev/null || git -C "$KIT_HOME" rev-parse --short HEAD)
  ok "Updated → $VER"
else
  info "Installing to $KIT_HOME ..."
  git clone "$REPO_URL" "$KIT_HOME"
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

# ── Statusline (optional) ─────────────────────────────────────────────────────

CLAUDE_SETTINGS="$HOME/.claude/settings.json"
STATUSLINE_SCRIPT="$HOME/.claude/statusline-command.sh"
STATUSLINE_SRC="$KIT_HOME/scripts/statusline-command.sh"

echo ""
read -r -p "$(echo -e "${_B}[claude-kit]${_N} Install Claude Code status line (shows ctx %, tokens, model)? [Y/n] ")" _sl_ans
_sl_ans="${_sl_ans:-Y}"

if [[ "$_sl_ans" =~ ^[Yy] ]]; then
  cp "$STATUSLINE_SRC" "$STATUSLINE_SCRIPT"
  chmod +x "$STATUSLINE_SCRIPT"

  # Wire settings.json — create if missing, update statusLine key if present
  if [ ! -f "$CLAUDE_SETTINGS" ]; then
    mkdir -p "$(dirname "$CLAUDE_SETTINGS")"
    echo '{"statusLine":{"type":"command","command":"bash '"$STATUSLINE_SCRIPT"'"}}' > "$CLAUDE_SETTINGS"
  elif command -v python3 &>/dev/null; then
    python3 - "$CLAUDE_SETTINGS" "$STATUSLINE_SCRIPT" <<'PYEOF'
import sys, json
path, script = sys.argv[1], sys.argv[2]
with open(path) as f:
    data = json.load(f)
data["statusLine"] = {"type": "command", "command": f"bash {script}"}
with open(path, "w") as f:
    json.dump(data, f, indent=2)
    f.write("\n")
PYEOF
  else
    warn "python3 not found — manually add to $CLAUDE_SETTINGS:"
    warn '  "statusLine": {"type": "command", "command": "bash '"$STATUSLINE_SCRIPT"'"}'
  fi
  ok "Status line installed."
else
  info "Skipped status line install."
fi

# ── Done ──────────────────────────────────────────────────────────────────────

echo ""
ok "claude-kit is ready."
echo ""
echo "  If 'claude-kit' isn't found, restart your shell or run:"
echo "    export PATH=\"\$HOME/.local/bin:\$PATH\""
echo ""
echo "  Then:"
echo "    claude-kit list"
echo "    claude-kit --kit coding-embedded-zephyr"
echo "    claude-kit --kit coding-embedded-zephyr --model sonnet --yolo"
echo ""
echo "  Keep plugins up to date:"
echo "    claude-kit update"
echo ""
echo "  To uninstall:"
echo "    claude-kit uninstall"
echo ""
