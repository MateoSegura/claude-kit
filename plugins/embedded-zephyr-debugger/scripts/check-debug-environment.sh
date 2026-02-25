#!/bin/bash
set -euo pipefail

# Check debug environment for Zephyr RTOS debugging tools
# Requires: standard unix tools
# This script is informational only — it warns about missing tools but never blocks.

echo "=== Zephyr Debug Environment Check ==="
echo ""

MISSING_REQUIRED=()
MISSING_OPTIONAL=()

# Required tools — core debugging functionality depends on these
check_required() {
    local cmd="$1"
    local desc="$2"
    if command -v "$cmd" &>/dev/null; then
        echo "[OK]   $cmd — $desc"
    else
        echo "[MISS] $cmd — $desc"
        MISSING_REQUIRED+=("$cmd")
    fi
}

# Optional tools — useful but not strictly required
check_optional() {
    local cmd="$1"
    local desc="$2"
    if command -v "$cmd" &>/dev/null; then
        echo "[OK]   $cmd — $desc"
    else
        echo "[WARN] $cmd — $desc (optional)"
        MISSING_OPTIONAL+=("$cmd")
    fi
}

echo "--- Core Debug Tools ---"
# GDB: check for Zephyr SDK GDB first, then generic multiarch
if command -v arm-zephyr-eabi-gdb &>/dev/null; then
    echo "[OK]   arm-zephyr-eabi-gdb — Zephyr SDK GDB"
elif command -v gdb-multiarch &>/dev/null; then
    echo "[OK]   gdb-multiarch — Generic multiarch GDB (fallback)"
else
    echo "[MISS] arm-zephyr-eabi-gdb / gdb-multiarch — GDB debugger"
    MISSING_REQUIRED+=("gdb")
fi

check_required "west" "Zephyr meta-tool"
check_required "jq" "JSON processor (used by hook scripts)"

# addr2line: check for Zephyr SDK version first
if command -v arm-zephyr-eabi-addr2line &>/dev/null; then
    echo "[OK]   arm-zephyr-eabi-addr2line — Address-to-source resolver"
elif command -v addr2line &>/dev/null; then
    echo "[OK]   addr2line — Address-to-source resolver (generic)"
else
    echo "[MISS] arm-zephyr-eabi-addr2line — Address-to-source resolver"
    MISSING_REQUIRED+=("addr2line")
fi

# objdump
if command -v arm-zephyr-eabi-objdump &>/dev/null; then
    echo "[OK]   arm-zephyr-eabi-objdump — Object file analyzer"
elif command -v objdump &>/dev/null; then
    echo "[OK]   objdump — Object file analyzer (generic)"
else
    echo "[MISS] arm-zephyr-eabi-objdump — Object file analyzer"
    MISSING_REQUIRED+=("objdump")
fi

echo ""
echo "--- Debug Probes ---"
check_optional "JLinkGDBServer" "Segger J-Link GDB server"
check_optional "JLinkExe" "Segger J-Link Commander"
check_optional "openocd" "Open On-Chip Debugger"
check_optional "nrfjprog" "Nordic Semiconductor programmer"
check_optional "pyocd" "Python On-Chip Debugger"
check_optional "st-flash" "STMicroelectronics flash tool"

echo ""
echo "--- Summary ---"
if [ ${#MISSING_REQUIRED[@]} -eq 0 ]; then
    echo "All required debug tools are available."
else
    echo "Missing required tools: ${MISSING_REQUIRED[*]}"
    echo "Install the Zephyr SDK for full toolchain support:"
    echo "  https://docs.zephyrproject.org/latest/develop/toolchains/zephyr_sdk.html"
fi

if [ ${#MISSING_OPTIONAL[@]} -gt 0 ]; then
    echo "Missing optional tools: ${MISSING_OPTIONAL[*]}"
    echo "These are needed for specific probe types. Install as needed."
fi

echo ""
echo "=== Environment check complete ==="

# Always exit 0 — this is informational only
exit 0
