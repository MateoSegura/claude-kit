#!/bin/bash
set -euo pipefail
# check-environment.sh — Verifies Zephyr development environment
# Called by hooks.json as a SessionStart hook
# Requires: jq (but checks for it)

WARNINGS=()

# Check for jq (needed by other hook scripts)
if ! command -v jq &> /dev/null; then
  WARNINGS+=("jq is not installed. Hook scripts require jq for JSON parsing. Install with: apt install jq / brew install jq")
fi

# Check for west
if ! command -v west &> /dev/null; then
  WARNINGS+=("west is not installed. Zephyr requires west for build system management. Install with: pip3 install west")
fi

# Check for cmake
if command -v cmake &> /dev/null; then
  CMAKE_VERSION=$(cmake --version | head -n 1 | sed 's/cmake version //')
  CMAKE_MAJOR=$(echo "$CMAKE_VERSION" | cut -d. -f1)
  CMAKE_MINOR=$(echo "$CMAKE_VERSION" | cut -d. -f2)
  if [[ "$CMAKE_MAJOR" -lt 3 ]] || { [[ "$CMAKE_MAJOR" -eq 3 ]] && [[ "$CMAKE_MINOR" -lt 20 ]]; }; then
    WARNINGS+=("cmake version $CMAKE_VERSION is too old. Zephyr requires cmake >= 3.20.0. Update cmake.")
  fi
else
  WARNINGS+=("cmake is not installed. Zephyr requires cmake for build configuration. Install from https://cmake.org/")
fi

# Check for ninja
if ! command -v ninja &> /dev/null; then
  WARNINGS+=("ninja is not installed. Zephyr uses ninja as the build system. Install with: apt install ninja-build / brew install ninja")
fi

# Check for dtc (devicetree compiler)
if ! command -v dtc &> /dev/null; then
  WARNINGS+=("dtc is not installed. Devicetree compilation requires dtc. Install with: apt install device-tree-compiler")
fi

# Check for toolchain (either Zephyr SDK or arm-none-eabi-gcc)
TOOLCHAIN_FOUND=false
if [[ -n "${ZEPHYR_SDK_INSTALL_DIR:-}" ]]; then
  TOOLCHAIN_FOUND=true
elif command -v arm-none-eabi-gcc &> /dev/null; then
  TOOLCHAIN_FOUND=true
elif command -v armclang &> /dev/null; then
  TOOLCHAIN_FOUND=true
fi

if [[ "$TOOLCHAIN_FOUND" == "false" ]]; then
  WARNINGS+=("No ARM toolchain found. Install Zephyr SDK (recommended) or arm-none-eabi-gcc. Set ZEPHYR_SDK_INSTALL_DIR if using Zephyr SDK.")
fi

# Check for ZEPHYR_BASE or .west directory
if [[ -z "${ZEPHYR_BASE:-}" ]] && [[ ! -d ".west" ]]; then
  WARNINGS+=("ZEPHYR_BASE not set and no .west directory found. Initialize a Zephyr workspace with: west init -m https://github.com/zephyrproject-rtos/zephyr")
fi

# Output all warnings
if [[ ${#WARNINGS[@]} -gt 0 ]]; then
  echo "=== Zephyr Environment Check ===" >&2
  for warning in "${WARNINGS[@]}"; do
    echo "WARNING: $warning" >&2
  done
  echo "================================" >&2
fi

exit 0
