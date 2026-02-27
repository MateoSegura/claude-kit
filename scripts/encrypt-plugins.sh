#!/usr/bin/env bash
# encrypt-plugins.sh — Encrypts plugin content directories into content.enc blobs.
#
# Usage:
#   scripts/encrypt-plugins.sh [--remove-plaintext] [--plugins-dir <path>]
#
# Each plugin's content (agents/, commands/, skills/, hooks/, scripts/) is
# tar-gzipped and encrypted with AES-256-CBC via openssl. Metadata files
# (plugin.json, ctl.json, README.md) are left in plaintext for CLI access.
#
# The encryption key is derived from a passphrase assembled at runtime.
# This matches the decryption logic in the claude-kit CLI.

set -euo pipefail

# ── Defaults ─────────────────────────────────────────────────────────────────

PLUGINS_DIR="plugins"
REMOVE_PLAINTEXT=false
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Parse flags
while [[ $# -gt 0 ]]; do
    case "$1" in
        --remove-plaintext) REMOVE_PLAINTEXT=true ;;
        --plugins-dir)      PLUGINS_DIR="$2"; shift ;;
        *)                  echo "Unknown flag: $1" >&2; exit 1 ;;
    esac
    shift
done

# ── Key assembly ─────────────────────────────────────────────────────────────
# The passphrase is split to avoid a single grep-able string.
# This matches _get_key() in the claude-kit CLI.

_k1='cK9x@'
_k2='Vm4p'
_k3='Lw2R'
_k4='qJ7n'
_k5='Ht5Z'
_k6='bF3s'
_PASSPHRASE="${_k1}${_k2}${_k3}${_k4}${_k5}${_k6}"

# ── Content directories to encrypt ──────────────────────────────────────────

CONTENT_DIRS=("agents" "commands" "skills" "hooks" "scripts")

# ── Functions ────────────────────────────────────────────────────────────────

encrypt_plugin() {
    local plugin_dir="$1"
    local plugin_name
    plugin_name="$(basename "$plugin_dir")"

    # Collect content directories that exist in this plugin
    local dirs_to_tar=()
    for d in "${CONTENT_DIRS[@]}"; do
        if [[ -d "$plugin_dir/$d" ]]; then
            dirs_to_tar+=("$d")
        fi
    done

    if [[ ${#dirs_to_tar[@]} -eq 0 ]]; then
        echo "  skip  $plugin_name  (no content dirs)"
        return
    fi

    # Tar + encrypt
    (cd "$plugin_dir" && tar czf - "${dirs_to_tar[@]}") \
        | openssl enc -aes-256-cbc -pbkdf2 -iter 100000 \
            -pass "pass:${_PASSPHRASE}" \
            -out "$plugin_dir/content.enc"

    echo "  enc   $plugin_name  (${dirs_to_tar[*]})"

    # Optionally remove plaintext content
    if [[ "$REMOVE_PLAINTEXT" == true ]]; then
        for d in "${dirs_to_tar[@]}"; do
            rm -rf "${plugin_dir:?}/$d"
        done
        echo "  clean $plugin_name  (plaintext removed)"
    fi
}

# ── Main ─────────────────────────────────────────────────────────────────────

if ! command -v openssl &>/dev/null; then
    echo "Error: openssl is required but not found." >&2
    exit 1
fi

if [[ ! -d "$PLUGINS_DIR" ]]; then
    echo "Error: plugins directory not found: $PLUGINS_DIR" >&2
    exit 1
fi

echo ""
echo "  Encrypting plugins in $PLUGINS_DIR/"
echo "  ────────────────────────────────────────"
echo ""

count=0
for plugin_dir in "$PLUGINS_DIR"/*/; do
    [[ -d "$plugin_dir" ]] || continue
    encrypt_plugin "$plugin_dir"
    count=$((count + 1))
done

echo ""
echo "  Done. $count plugins processed."
echo ""
