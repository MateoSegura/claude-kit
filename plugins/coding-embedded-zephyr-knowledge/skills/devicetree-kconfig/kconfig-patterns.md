# Kconfig Patterns and Recipes

## Kconfig File Merging

**Order of precedence (last wins):**

1. Kconfig defaults (in `Kconfig` files)
2. Board defconfig (`boards/<arch>/<board>/<board>_defconfig`)
3. `prj.conf` (project configuration)
4. Board-specific `boards/<board>.conf` (if exists)
5. Extra conf files (`EXTRA_CONF_FILE`, `OVERLAY_CONFIG`)
6. Command-line overrides

### Multiple Configuration Files

```bash
# Merge multiple .conf files
west build -b nrf52840dk_nrf52840 -- -DEXTRA_CONF_FILE="debug.conf;network.conf"

# Alternative syntax
west build -b nrf52840dk_nrf52840 -- -DOVERLAY_CONFIG="debug.conf;network.conf"
```

**Use case:** Separate configs for debug, release, test variants.

### Configuration Fragments

**debug.conf:**

```kconfig
CONFIG_DEBUG=y
CONFIG_DEBUG_OPTIMIZATIONS=y
CONFIG_STACK_SENTINEL=y
CONFIG_THREAD_ANALYZER=y
CONFIG_THREAD_NAME=y
CONFIG_LOG_DEFAULT_LEVEL=4
```

**release.conf:**

```kconfig
CONFIG_SIZE_OPTIMIZATIONS=y
CONFIG_LOG=n
CONFIG_ASSERT=n
CONFIG_PRINTK=n
```

**network.conf:**

```kconfig
CONFIG_NETWORKING=y
CONFIG_NET_IPV4=y
CONFIG_NET_IPV6=y
CONFIG_NET_TCP=y
CONFIG_NET_SOCKETS=y
```

## Sysbuild Kconfig

**Sysbuild:** Multi-image build system for bootloader + application.

### Sysbuild Configuration

**File:** `sysbuild.conf` (top-level, not in app directory)

```kconfig
# MCUboot bootloader configuration
SB_CONFIG_BOOTLOADER_MCUBOOT=y

# Partition sizes
SB_CONFIG_MCUBOOT_FLASH_SIZE=0xC000
SB_CONFIG_BOOT_IMAGE_SIZE=0x76000

# Signing
SB_CONFIG_MCUBOOT_SIGNATURE_KEY_FILE="bootloader/mcuboot/root-rsa-2048.pem"
```

**Prefix:** `SB_CONFIG_` (not `CONFIG_`)

### MCUboot-specific Configuration

**File:** `sysbuild/mcuboot.conf`

```kconfig
# MCUboot-specific settings
CONFIG_LOG=y
CONFIG_LOG_DEFAULT_LEVEL=3
CONFIG_BOOT_SWAP_SAVE_ENCTLV=n
CONFIG_BOOT_ENCRYPT_IMAGE=n
```

### Per-Image Configuration in Sysbuild

```cmake
# sysbuild.cmake
set(mcuboot_CONF_FILE ${CMAKE_CURRENT_LIST_DIR}/sysbuild/mcuboot.conf)
set(app_CONF_FILE ${CMAKE_CURRENT_LIST_DIR}/prj.conf)
```

## IS_ENABLED() Usage

**Macro:** Evaluates to `1` if enabled, `0` otherwise. Type-safe for `#if`.

```c
#include <zephyr/autoconf.h>

#if IS_ENABLED(CONFIG_SENSOR)
    init_sensors();
#endif

#if IS_ENABLED(CONFIG_BT)
    init_bluetooth();
#endif

/* Works in expressions */
if (IS_ENABLED(CONFIG_DEBUG_MODE)) {
    print_debug_info();
}
```

**Advantage over `#ifdef`:** Works with compiler dead-code elimination. Better optimization.

### Conditional Compilation Patterns

```c
/* Feature flag */
#if IS_ENABLED(CONFIG_FEATURE_X)
void feature_x_init(void) {
    /* ... */
}
#endif

/* Select implementation */
void process_data(void) {
#if IS_ENABLED(CONFIG_USE_ALGORITHM_A)
    algorithm_a();
#elif IS_ENABLED(CONFIG_USE_ALGORITHM_B)
    algorithm_b();
#else
    algorithm_default();
#endif
}

/* Compile-time constant */
#define BUFFER_SIZE \
    (IS_ENABLED(CONFIG_LARGE_BUFFERS) ? 4096 : 512)
```

## menuconfig Exploration

**Launch interactive menu:**

```bash
west build -t menuconfig
```

**Navigation:**
- Arrow keys: Navigate
- Enter: Select/enter submenu
- Space: Toggle boolean
- `/`: Search for symbol
- `?`: Show help for current option

**Use cases:**
- Discover available options
- See dependencies
- Understand default values
- Find related symbols

### guiconfig (Qt-based)

```bash
west build -t guiconfig
```

Graphical interface. Better for complex exploration.

## Dependency Resolution

### depends on

```kconfig
config FEATURE_A
    bool "Feature A"
    depends on FEATURE_B
    help
      Only visible if FEATURE_B is enabled
```

**Effect:** Symbol not visible in menuconfig unless dependencies met.

### select

```kconfig
config FEATURE_C
    bool "Feature C"
    select FEATURE_D
    help
      Automatically enables FEATURE_D
```

**Effect:** Enabling C automatically enables D. User cannot disable D while C is enabled.

### imply

```kconfig
config FEATURE_E
    bool "Feature E"
    imply FEATURE_F
    help
      Suggests enabling FEATURE_F but doesn't force it
```

**Effect:** F defaults to enabled when E is enabled, but user can override.

### Circular Dependencies

**Problem:** A depends on B, B depends on A.

**Solution:** Use `imply` instead of `select` for one direction, or restructure dependencies.

## Common Subsystem Enablement

### BLE (Bluetooth Low Energy)

```kconfig
CONFIG_BT=y
CONFIG_BT_PERIPHERAL=y
CONFIG_BT_CENTRAL=n
CONFIG_BT_DEVICE_NAME="MyDevice"
CONFIG_BT_MAX_CONN=1
CONFIG_BT_BUF_ACL_RX_SIZE=251
CONFIG_BT_BUF_ACL_TX_SIZE=251
CONFIG_BT_L2CAP_TX_MTU=247
CONFIG_BT_RX_STACK_SIZE=2048
```

**GATT services:**

```kconfig
CONFIG_BT_GATT_DYNAMIC_DB=y
CONFIG_BT_SETTINGS=y
CONFIG_BT_PRIVACY=y
```

### Networking (IP stack)

```kconfig
CONFIG_NETWORKING=y
CONFIG_NET_IPV4=y
CONFIG_NET_IPV6=y
CONFIG_NET_TCP=y
CONFIG_NET_UDP=y
CONFIG_NET_SOCKETS=y
CONFIG_NET_SOCKETS_POSIX_NAMES=y

# DHCP client
CONFIG_NET_DHCPV4=y

# DNS resolver
CONFIG_DNS_RESOLVER=y

# Buffers
CONFIG_NET_PKT_RX_COUNT=10
CONFIG_NET_PKT_TX_COUNT=10
CONFIG_NET_BUF_RX_COUNT=20
CONFIG_NET_BUF_TX_COUNT=20
```

### MQTT

```kconfig
CONFIG_MQTT_LIB=y
CONFIG_MQTT_LIB_TLS=y

# Requires networking
CONFIG_NETWORKING=y
CONFIG_NET_SOCKETS=y
CONFIG_NET_TCP=y
```

### CoAP

```kconfig
CONFIG_COAP=y

# For CoAP over DTLS
CONFIG_MBEDTLS=y
CONFIG_MBEDTLS_KEY_EXCHANGE_PSK_ENABLED=y
```

### HTTP Client

```kconfig
CONFIG_HTTP_CLIENT=y
CONFIG_NET_SOCKETS=y
CONFIG_NET_TCP=y

# For HTTPS
CONFIG_HTTP_CLIENT_TLS=y
CONFIG_MBEDTLS=y
```

### MCUboot (Bootloader)

**Via sysbuild (preferred):**

```kconfig
# sysbuild.conf
SB_CONFIG_BOOTLOADER_MCUBOOT=y
SB_CONFIG_MCUBOOT_SIGNATURE_KEY_FILE="bootloader/mcuboot/root-rsa-2048.pem"
```

**Application config:**

```kconfig
# prj.conf
CONFIG_BOOTLOADER_MCUBOOT=y
CONFIG_IMG_MANAGER=y
CONFIG_FLASH=y
CONFIG_FLASH_MAP=y
CONFIG_STREAM_FLASH=y
```

### TF-M (Trusted Firmware-M)

**Cortex-M33+ only.**

```kconfig
CONFIG_BUILD_WITH_TFM=y
CONFIG_TFM_BOARD="nordic_nrf/nrf9160dk_nrf9160/ns"

# PSA Crypto API
CONFIG_PSA_CRYPTO_CLIENT=y
CONFIG_MBEDTLS_PSA_CRYPTO_C=y
```

**Requires:** Sysbuild enabled.

### Logging

```kconfig
CONFIG_LOG=y
CONFIG_LOG_DEFAULT_LEVEL=3          # 3=INF
CONFIG_LOG_MODE_DEFERRED=y          # Async (default)
CONFIG_LOG_BUFFER_SIZE=4096

# Module-specific levels
CONFIG_SENSOR_LOG_LEVEL_DBG=y
CONFIG_BT_LOG_LEVEL_INF=y

# Backends
CONFIG_LOG_BACKEND_UART=y
CONFIG_LOG_BACKEND_RTT=y            # Segger RTT
CONFIG_LOG_BACKEND_SHOW_COLOR=y
```

### Shell

```kconfig
CONFIG_SHELL=y
CONFIG_SHELL_BACKEND_SERIAL=y
CONFIG_SHELL_PROMPT_UART="uart:~$ "

# Built-in commands
CONFIG_KERNEL_SHELL=y
CONFIG_DEVICE_SHELL=y
CONFIG_SENSOR_SHELL=y
CONFIG_LOG_CMDS=y
```

### Settings (Persistent Storage)

```kconfig
CONFIG_SETTINGS=y
CONFIG_SETTINGS_RUNTIME=y

# NVS backend (non-volatile storage)
CONFIG_SETTINGS_NVS=y
CONFIG_NVS=y
CONFIG_FLASH=y
CONFIG_FLASH_MAP=y

# Or FCB backend (flash circular buffer)
CONFIG_SETTINGS_FCB=y
CONFIG_FCB=y
```

### File Systems

```kconfig
# LittleFS
CONFIG_FILE_SYSTEM=y
CONFIG_FILE_SYSTEM_LITTLEFS=y

# FAT FS
CONFIG_FILE_SYSTEM_FAT=y
CONFIG_FAT_FILESYSTEM_ELM=y

# Flash backend
CONFIG_FLASH=y
CONFIG_FLASH_MAP=y
```

### USB Device

```kconfig
CONFIG_USB_DEVICE_STACK=y
CONFIG_USB_DEVICE_PRODUCT="Zephyr Device"
CONFIG_USB_DEVICE_VID=0x2FE3
CONFIG_USB_DEVICE_PID=0x0001

# USB CDC ACM (virtual serial)
CONFIG_USB_CDC_ACM=y
CONFIG_USB_UART_CONSOLE=y
```

### Power Management

```kconfig
CONFIG_PM=y
CONFIG_PM_DEVICE=y

# Runtime power management
CONFIG_PM_DEVICE_RUNTIME=y

# Allow tickless kernel
CONFIG_TICKLESS_KERNEL=y
```

## Kconfig Best Practices

### 1. Use Minimal prj.conf

Only include settings that differ from defaults. Let auto-enable handle dependencies.

**Good:**

```kconfig
CONFIG_I2C=y
CONFIG_SENSOR=y
```

**Bad (redundant):**

```kconfig
CONFIG_I2C=y
CONFIG_I2C_NRFX=y              # Auto-enabled by board
CONFIG_SENSOR=y
CONFIG_SENSOR_ASYNC=y          # Auto-enabled by sensor driver
CONFIG_GPIO=y                  # Auto-enabled by DT
```

### 2. Use Board-Specific Configs

**boards/nrf52840dk_nrf52840.conf:**

```kconfig
# Board-specific optimizations
CONFIG_DCDC_HV=y
CONFIG_DCDC_LV=y
```

Auto-merged when building for this board.

### 3. Use Kconfig.defconfig for Application Defaults

**Kconfig.defconfig:**

```kconfig
if APP_NAME

config MAIN_STACK_SIZE
    default 4096

config LOG_DEFAULT_LEVEL
    default 3

endif
```

**Reference in main Kconfig:**

```kconfig
source "Kconfig.defconfig"
```

### 4. Check Dependencies with menuconfig

Before adding `select`, check if `depends on` is more appropriate.

**Rule of thumb:**
- `select`: For implementation details user shouldn't manage
- `depends on`: For genuine prerequisites
- `imply`: For suggested but optional features

### 5. Verify Configuration

```bash
# View final merged configuration
west build -t hardenconfig

# Show why a symbol has a certain value
west build -t menuconfig
# Then search for symbol and press '?'
```

### 6. Use Kconfig Fragments for Build Variants

```bash
# Debug build
west build -b board -- -DEXTRA_CONF_FILE=debug.conf

# Release build
west build -b board -- -DEXTRA_CONF_FILE=release.conf

# Test build
west build -b board -- -DEXTRA_CONF_FILE=test.conf
```

## Troubleshooting Kconfig Issues

### Symbol Not Visible

**Problem:** Setting `CONFIG_X=y` has no effect.

**Causes:**
1. Unmet `depends on` — check dependencies
2. Wrong Kconfig prefix (`CONFIG_` vs `SB_CONFIG_`)
3. Symbol doesn't exist — check spelling

**Debug:**

```bash
west build -t menuconfig
# Search for symbol with '/'
# Press '?' to see dependencies
```

### Value Overridden

**Problem:** Configuration appears ignored.

**Check:**
1. Is a later config file overriding it?
2. Is `select` forcing a different value?
3. Is `range` limiting the value?

**Debug:**

```bash
# View final configuration
cat build/zephyr/.config | grep CONFIG_X
```

### Circular Dependency

**Error:** `Kconfig: recursive dependency detected`

**Solution:** Replace `select` with `imply` for one direction, or restructure.

### Out of Memory

**Symptoms:** Build succeeds, runtime crashes, or fails to allocate.

**Check:**

```kconfig
CONFIG_MAIN_STACK_SIZE=2048     # Increase if stack overflow
CONFIG_HEAP_MEM_POOL_SIZE=4096  # Increase if k_malloc fails
CONFIG_NET_BUF_DATA_SIZE=128    # Increase if network buffers exhausted
```

**Debug with:**

```kconfig
CONFIG_DEBUG_INFO=y
CONFIG_THREAD_ANALYZER=y
CONFIG_THREAD_STACK_INFO=y
```

Then use shell command:

```bash
uart:~$ kernel threads
```
