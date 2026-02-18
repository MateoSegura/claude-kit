---
name: coding-embedded-zephyr-knowledge:build-system
description: Zephyr build system — west workflow, CMake patterns, sysbuild multi-image builds, workspace topologies, and CI/CD integration
user-invocable: false
---

# Build System Quick Reference

## West Commands

### Initialize Workspace

```bash
# T2 topology (application outside zephyr tree)
west init -m https://github.com/user/app-repo my-workspace
cd my-workspace
west update

# T3 topology (application as module)
west init -m https://github.com/zephyrproject-rtos/zephyr zephyr-workspace
cd zephyr-workspace
west update
```

### Build

```bash
# Basic build
west build -b nrf52840dk_nrf52840 app

# With sysbuild (for MCUboot, TF-M)
west build -b nrf52840dk_nrf52840 --sysbuild app

# Pristine build (clean first)
west build -b board -p always app

# Build directory override
west build -b board -d build-custom app
```

### Flash and Debug

```bash
# Flash to target
west flash

# Flash with runner override
west flash --runner jlink

# Debug with GDB
west debug

# Attach debugger to running target
west attach
```

### Testing

```bash
# Run twister (test runner)
west twister -p native_sim -T tests/

# With coverage
west twister -p native_sim --coverage -T tests/
```

## Sysbuild Multi-Image Builds

**Enable sysbuild:**

```bash
west build -b board --sysbuild
```

**Configuration hierarchy:**

```
project/
├── sysbuild.conf          # Top-level sysbuild config
├── sysbuild.cmake         # Per-image CMake config
├── sysbuild/
│   └── mcuboot.conf       # MCUboot-specific config
└── prj.conf               # Application config
```

**sysbuild.conf:**

```kconfig
SB_CONFIG_BOOTLOADER_MCUBOOT=y
```

**sysbuild.cmake:**

```cmake
set(mcuboot_CONF_FILE ${CMAKE_CURRENT_LIST_DIR}/sysbuild/mcuboot.conf)
set(${DEFAULT_IMAGE}_CONF_FILE ${CMAKE_CURRENT_LIST_DIR}/prj.conf)
```

**Build outputs:**

```
build/
├── mcuboot/zephyr/zephyr.{bin,hex,elf}
├── tfm/bin/tfm_s.{bin,hex}  (if TF-M enabled)
└── zephyr.{bin,hex,elf}     (application)
```

## CMake Patterns

### Basic Application CMakeLists.txt

```cmake
cmake_minimum_required(VERSION 3.20.0)
find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(my_app)

target_sources(app PRIVATE src/main.c)
```

### Add Sources

```cmake
target_sources(app PRIVATE
    src/main.c
    src/sensor.c
    src/network.c
)
```

### Create Library

```cmake
zephyr_library()
zephyr_library_sources(lib/util.c)
zephyr_library_include_directories(lib/)
```

### Conditional Compilation

```cmake
if(CONFIG_MY_FEATURE)
    target_sources(app PRIVATE src/feature.c)
endif()
```

### Add Include Directories

```cmake
target_include_directories(app PRIVATE include/)
```

### Compiler Definitions

```cmake
target_compile_definitions(app PRIVATE
    MY_DEFINE=1
    ANOTHER_DEFINE=\"string\"
)
```

### Extra Configuration Files

```cmake
set(EXTRA_CONF_FILE extra.conf)
set(EXTRA_DTC_OVERLAY_FILE boards/my_board.overlay)
```

## Workspace Topologies

### T1: Application Inside Zephyr Tree

```
zephyr/
├── samples/
│   └── my_app/
│       ├── CMakeLists.txt
│       ├── prj.conf
│       └── src/
```

**Build:**

```bash
cd samples/my_app
west build -b board
```

**Use case:** Contributing samples to Zephyr.

### T2: Application Outside Zephyr Tree (Recommended)

```
workspace/
├── .west/
├── zephyr/
├── modules/
└── my-app/
    ├── CMakeLists.txt
    ├── prj.conf
    ├── west.yml  (manifest)
    └── src/
```

**my-app/west.yml:**

```yaml
manifest:
  remotes:
    - name: zephyrproject-rtos
      url-base: https://github.com/zephyrproject-rtos
  projects:
    - name: zephyr
      remote: zephyrproject-rtos
      revision: v3.7-branch
      import: true
  self:
    path: my-app
```

**Build:**

```bash
west build -b board my-app
```

**Use case:** Product development with custom manifest.

### T3: Zephyr Workspace with Application as Module

```
workspace/
├── .west/
├── zephyr/
├── modules/
└── my-module/
    ├── CMakeLists.txt
    ├── Kconfig
    └── zephyr/
        └── module.yml
```

**module.yml:**

```yaml
name: my-module
build:
  cmake: .
  kconfig: Kconfig
```

**Use case:** Reusable Zephyr module.

## Build Configuration

### Board-Specific Overlays

```
app/
├── boards/
│   ├── nrf52840dk_nrf52840.overlay
│   └── nrf52840dk_nrf52840.conf
└── prj.conf
```

Auto-merged when building for matching board.

### Build Types

```bash
# Debug (default)
west build -b board

# Release
west build -b board -- -DCONFIG_SIZE_OPTIMIZATIONS=y

# With custom config
west build -b board -- -DEXTRA_CONF_FILE=release.conf
```

## CI/CD Patterns

### GitHub Actions

```yaml
name: Build Firmware

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    container: zephyrprojectrtos/ci:latest

    steps:
      - uses: actions/checkout@v3
        with:
          path: app

      - name: Initialize
        run: |
          west init -l app
          west update

      - name: Build
        run: |
          west build -b nrf52840dk_nrf52840 --sysbuild app
```

### Multi-Board Matrix

```yaml
strategy:
  matrix:
    board: [nrf52840dk_nrf52840, nrf5340dk_nrf5340_cpuapp, esp32c3_devkitm]

steps:
  - name: Build ${{ matrix.board }}
    run: west build -b ${{ matrix.board }} app
```

## Additional resources

- For west command reference, manifest format, sysbuild details, and custom west extensions, see [west-sysbuild-reference.md](west-sysbuild-reference.md)
- For CMake patterns, Zephyr module integration, and advanced build customization, see [cmake-patterns.md](cmake-patterns.md)
