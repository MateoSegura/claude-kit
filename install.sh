#!/usr/bin/env bash
set -euo pipefail

KIT_HOME="${KIT_HOME:-$HOME/.claude-kit}"
REPO_SLUG="MateoSegura/claude-kit"
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

if ! command -v python3 &>/dev/null; then
  err "python3 is required but not found (claude-kit CLI is Python)."
  err "Install Python 3: https://www.python.org/downloads/"
  exit 1
fi

if ! command -v openssl &>/dev/null; then
  err "openssl is required but not found. Install openssl and try again."
  exit 1
fi

if ! command -v claude &>/dev/null; then
  info "Claude Code CLI ('claude') not found — installing ..."
  curl -fsSL https://claude.ai/install.sh | bash
  if ! command -v claude &>/dev/null; then
    err "Claude Code installation failed. Install manually: https://claude.ai/code"
    exit 1
  fi
  ok "Claude Code installed"
fi

# ── Install jq if missing ────────────────────────────────────────────────────

_install_jq() {
  if command -v apt-get &>/dev/null; then
    info "Installing jq via apt ..."
    sudo apt-get update -qq >/dev/null && sudo apt-get install -y -qq jq >/dev/null
  elif command -v brew &>/dev/null; then
    info "Installing jq via brew ..."
    brew install jq >/dev/null
  elif command -v dnf &>/dev/null; then
    info "Installing jq via dnf ..."
    sudo dnf install -y -q jq >/dev/null
  elif command -v pacman &>/dev/null; then
    info "Installing jq via pacman ..."
    sudo pacman -S --noconfirm jq >/dev/null
  elif command -v apk &>/dev/null; then
    info "Installing jq via apk ..."
    sudo apk add -q jq >/dev/null
  else
    return 1
  fi
}

if ! command -v jq &>/dev/null; then
  if _install_jq; then
    ok "jq installed"
  else
    warn "Could not auto-install jq. Plugin hooks will run in degraded mode."
    warn "Install manually: https://jqlang.github.io/jq/download/"
  fi
fi

# ── Install gh if missing ──────────────────────────────────────────────────────

_install_gh() {
  if command -v apt-get &>/dev/null; then
    info "Installing gh via apt ..."
    (type -p wget >/dev/null || (sudo apt-get update -qq && sudo apt-get install -y -qq wget >/dev/null)) \
      && sudo mkdir -p -m 755 /etc/apt/keyrings \
      && out=$(mktemp) && wget -qO "$out" https://cli.github.com/packages/githubcli-archive-keyring.gpg \
      && cat "$out" | sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg >/dev/null \
      && sudo chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg \
      && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
        | sudo tee /etc/apt/sources.list.d/github-cli.list >/dev/null \
      && sudo apt-get update -qq >/dev/null && sudo apt-get install -y -qq gh >/dev/null
  elif command -v brew &>/dev/null; then
    info "Installing gh via brew ..."
    brew install gh >/dev/null
  elif command -v dnf &>/dev/null; then
    info "Installing gh via dnf ..."
    sudo dnf install -y -q 'dnf-command(config-manager)' >/dev/null \
      && sudo dnf config-manager --add-repo https://cli.github.com/packages/rpm/gh-cli.repo >/dev/null \
      && sudo dnf install -y -q gh >/dev/null
  elif command -v pacman &>/dev/null; then
    info "Installing gh via pacman ..."
    sudo pacman -S --noconfirm github-cli >/dev/null
  elif command -v apk &>/dev/null; then
    info "Installing gh via apk ..."
    sudo apk add -q github-cli >/dev/null
  else
    return 1
  fi
}

if ! command -v gh &>/dev/null; then
  if _install_gh; then
    ok "gh installed"
  else
    err "gh (GitHub CLI) is required but could not be installed."
    err "Install manually: https://cli.github.com"
    exit 1
  fi
fi

if ! gh auth status &>/dev/null; then
  err "gh is not authenticated. Run:  gh auth login"
  exit 1
fi

# ── Clone or update ───────────────────────────────────────────────────────────

_kit_version() {
  # Read from .version file (user installs)
  if [ -f "$KIT_HOME/.version" ]; then
    cat "$KIT_HOME/.version"
    return
  fi
  # Fallback: parse CHANGELOG.md
  if [ -f "$KIT_HOME/CHANGELOG.md" ]; then
    local ver
    ver=$(grep -m1 '^## \[[0-9]' "$KIT_HOME/CHANGELOG.md" | sed 's/## \[\(.*\)\].*/v\1/')
    if [ -n "$ver" ]; then echo "$ver"; return; fi
  fi
  echo "unknown"
}

_download_repo() {
  # Download repo as tarball via gh api (no git involved — avoids credential
  # helper conflicts with Bitbucket, GitLab, stale gh paths, etc.)
  local dest="$1"
  local tmp_tar
  tmp_tar=$(mktemp)

  gh api "repos/$REPO_SLUG/tarball/main" > "$tmp_tar" 2>/dev/null
  if [ $? -ne 0 ] || [ ! -s "$tmp_tar" ]; then
    rm -f "$tmp_tar"
    return 1
  fi

  mkdir -p "$dest"
  tar xzf "$tmp_tar" -C "$dest" --strip-components=1
  rm -f "$tmp_tar"
}

_encrypt_and_seal() {
  # Encrypt plugin content and remove plaintext source dirs
  local kit_dir="$1"

  info "Securing plugin content ..."

  if [ -f "$kit_dir/scripts/encrypt-plugins.sh" ]; then
    bash "$kit_dir/scripts/encrypt-plugins.sh" \
      --plugins-dir "$kit_dir/plugins" \
      --remove-plaintext >/dev/null
  fi

  # Remove git history if present (tarball won't have it, but just in case)
  rm -rf "$kit_dir/.git" 2>/dev/null

  # Write version file
  local ver
  ver=$(_kit_version)
  echo "$ver" > "$kit_dir/.version"

  ok "Plugins encrypted"
}

if [ -f "$KIT_HOME/.installed" ]; then
  # Existing user install — use claude-kit update instead
  info "Updating ..."
  if command -v claude-kit &>/dev/null; then
    claude-kit update
  else
    python3 "$KIT_HOME/claude-kit" update
  fi
else
  info "Installing ..."
  if ! _download_repo "$KIT_HOME"; then
    err "Failed to download repo. Check gh auth status."
    exit 1
  fi
  _encrypt_and_seal "$KIT_HOME"
  ok "Installed → $(_kit_version)"
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
echo -e "  ${_C}claude-kit --kit <name> --kit core-spec${_N}"
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

# ── Setup reminder banner ────────────────────────────────────────────────────

echo -e "  ${_Y}┌─────────────────────────────────────────────────────┐${_N}"
echo -e "  ${_Y}│${_N}  Run  ${_C}claude-kit setup${_N}  to configure Claude Code    ${_Y}│${_N}"
echo -e "  ${_Y}│${_N}                                                     ${_Y}│${_N}"
echo -e "  ${_Y}│${_N}  This will add to ~/.claude/:                       ${_Y}│${_N}"
echo -e "  ${_Y}│${_N}    ${_DIM}• statusline (context %, tokens, model)${_N}          ${_Y}│${_N}"
echo -e "  ${_Y}│${_N}    ${_DIM}• auto-routing rules (intent → skill matching)${_N}   ${_Y}│${_N}"
echo -e "  ${_Y}│${_N}                                                     ${_Y}│${_N}"
echo -e "  ${_Y}│${_N}  All changes can be undone with: ${_C}claude-kit restore${_N} ${_Y}│${_N}"
echo -e "  ${_Y}└─────────────────────────────────────────────────────┘${_N}"
echo ""
