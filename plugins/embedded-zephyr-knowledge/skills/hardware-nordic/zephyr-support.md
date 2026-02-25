# Zephyr Support for Nordic nRF Hardware

## Board Names

### Naming Convention Change (Zephyr 3.7+)

Zephyr 3.7 introduced a new board naming convention for multi-variant boards. Old names still work via aliases but new projects should use the new format.

| Board | Old name (pre-3.7) | New name (3.7+) |
|-------|-------------------|-----------------|
| nRF52840 DK | `nrf52840dk_nrf52840` | `nrf52840dk/nrf52840` |
| nRF52832 DK | `nrf52dk_nrf52832` | `nrf52dk/nrf52832` |
| nRF52833 DK | `nrf52833dk_nrf52833` | `nrf52833dk/nrf52833` |
| nRF5340 DK (app) | `nrf5340dk_nrf5340_cpuapp` | `nrf5340dk/nrf5340/cpuapp` |
| nRF5340 DK (net) | `nrf5340dk_nrf5340_cpunet` | `nrf5340dk/nrf5340/cpunet` |
| nRF9160 DK | `nrf9160dk_nrf9160_ns` | `nrf9160dk/nrf9160/ns` |
| nRF9161 DK | `nrf9161dk_nrf9161_ns` | `nrf9161dk/nrf9161/ns` |
| nRF54L15 DK | `nrf54l15dk_nrf54l15_cpuapp` | `nrf54l15dk/nrf54l15/cpuapp` |

**`_ns` suffix** = Non-secure build (TrustZone). nRF9160 and nRF5340 builds typically use `_ns` so the application runs in the TrustZone non-secure world, with TF-M or the SPM handling secure services.

## Feature Support Matrix

| Feature | nRF52832 | nRF52840 | nRF5340 | nRF54L15 | nRF9160 |
|---------|---------|---------|---------|---------|---------|
| BLE (Zephyr LL) | Y | Y | Y (net) | Y | — |
| BLE (SoftDevice) | Y | Y | Y | Y | — |
| 802.15.4/Thread | — | Y | Y | Y | — |
| USB CDC-ACM | — | Y | Y | Y | — |
| QSPI | — | Y | Y | — | — |
| TrustZone/TF-M | — | — | Y | Y | Y |
| NFC | Y | Y | Y (net) | — | — |
| LTE-M/NB-IoT | — | — | — | — | Y |
| GNSS | — | — | — | — | Y |
| MCUboot | Y | Y | Y | Y | Y |
| SMP BLE DFU | Y | Y | Y | Y | — |
| SEGGER RTT | Y | Y | Y | Y | Y |
| SWD Debug | Y | Y | Y | Y | Y |
| PM (power) | Y | Y | Y | Y | Y (app) |
| DCDC | Y | Y | Y | Y | Y |

## BLE Controller Options

### Zephyr Native Bluetooth Controller (LL)

The default for upstream Zephyr. Open-source, part of the kernel tree.

```kconfig
CONFIG_BT=y
CONFIG_BT_LL_SW_SPLIT=y  # Zephyr native LL (default when CONFIG_BT=y)
```

**Supports:**
- BLE 5.0/5.1 features (2 Mbps PHY, Long Range Coded PHY, extended advertising)
- Works on all nRF52/53/54 variants
- No licensing restrictions

**Limitations:**
- Bluetooth SIG qualification not directly obtained from Zephyr project
- Slightly higher CPU usage vs. SoftDevice Controller
- LE Audio (LC3 codec) not yet fully supported in all variants

### SoftDevice Controller (nRF Connect SDK)

Nordic's certified BLE controller, available in nRF Connect SDK.

```kconfig
CONFIG_BT=y
CONFIG_BT_LL_SOFTDEVICE=y
CONFIG_MPSL=y
```

**Supports:**
- Bluetooth SIG certified (qualification listing available)
- MPSL (Multi-Protocol Scheduler Library) for coexistence with 802.15.4
- LE Audio with LC3 support (nRF5340, nRF54L15)
- Lower CPU overhead due to optimized scheduling

**Requirement:** Only available in nRF Connect SDK — not in upstream Zephyr.

**MPSL (Multi-Protocol Scheduler Library):** Manages radio time division between BLE and 802.15.4 (Thread/Zigbee). Required when using both protocols simultaneously.

```kconfig
CONFIG_MPSL=y
CONFIG_MPSL_FEM_NRF21540_GPIO=y  # If using nRF21540 PA/LNA
```

## nRF Connect SDK vs. Vanilla Zephyr

| Aspect | Vanilla Zephyr | nRF Connect SDK |
|--------|---------------|-----------------|
| Source | github.com/zephyrproject-rtos | github.com/nrfconnect/sdk-nrf |
| BLE controller | Zephyr LL | SoftDevice Controller (certified) |
| Nordic drivers | Upstream nrfx HAL | nrfx HAL + Nordic extras |
| LE Audio | Limited | Full LC3, CAP, BAP |
| Modem support | Limited | Full nrf_modem_lib, AT host |
| DFU/FOTA | MCUboot only | MCUboot + SMP + nRF Cloud FOTA |
| Crypto | Mbed TLS | Mbed TLS + PSA Crypto + nRF Oberon |
| Maturity | Broad community | Nordic-specific, well-supported |

**Recommendation:**
- Use **Zephyr upstream** for: open-source projects, non-Nordic targets alongside Nordic, maximum portability
- Use **nRF Connect SDK** for: production BLE products, LE Audio, cellular nRF91, Bluetooth SIG certification

## OTA DFU — MCUboot and SMP

### MCUboot Setup

```kconfig
CONFIG_BOOTLOADER_MCUBOOT=y
CONFIG_MCUBOOT_IMGTOOL_SIGN_VERSION="1.0.0+0"
```

```yaml
# west.yml — ensure mcuboot module is present
- name: mcuboot
  path: bootloader/mcuboot
  revision: <version>
```

**Image layout for nRF52840 (1 MB flash):**

| Region | Start | Size |
|--------|-------|------|
| MBR (Nordic) | 0x0000 0000 | 4 KB |
| MCUboot | 0x0000 1000 | 48 KB |
| Primary slot | 0x0000 C000 | 464 KB |
| Secondary slot | 0x0007 8000 | 464 KB |
| Storage | 0x000F 8000 | 32 KB |

### SMP DFU over BLE

SMP (Simple Management Protocol) allows OTA firmware updates via BLE without a proprietary app:

```kconfig
CONFIG_MCUMGR=y
CONFIG_MCUMGR_TRANSPORT_BT=y
CONFIG_MCUMGR_GRP_IMG=y  # Image management (upload firmware)
CONFIG_MCUMGR_GRP_OS=y   # OS group (reboot command)
```

**Client tools:**
- `mcumgr` CLI: `mcumgr --conntype ble --connstring peer_name=<device> image upload zephyr.signed.bin`
- nRF Connect Device Manager app (Android/iOS)
- nRF Device Manager SDK (React Native)

### nRF5340 DFU — Dual-Image

nRF5340 requires two images (cpuapp + cpunet). MCUboot handles the app image; the net core image can be included as a secondary hex flashed by the app core.

```bash
# Build with sysbuild — both images included
west build -b nrf5340dk_nrf5340_cpuapp --sysbuild
# Creates: build/merged.hex, build/app/zephyr/zephyr.signed.bin
```

## Debug Configuration

### SEGGER RTT (Real-Time Transfer)

Preferred logging method — no UART needed, very low overhead.

```kconfig
CONFIG_USE_SEGGER_RTT=y
CONFIG_RTT_CONSOLE=y
CONFIG_UART_CONSOLE=n
CONFIG_LOG_BACKEND_RTT=y
CONFIG_LOG_BACKEND_UART=n
```

**View logs:**
```bash
JLinkRTTViewer  # GUI tool from SEGGER
# Or via west:
west attach  # Opens RTT in terminal (nRF Connect SDK)
```

### J-Link SWD Debug

```bash
# Flash and attach debugger
west debug --runner jlink

# Flash only
west flash --runner jlink

# Attach to running target (no flash)
west attach --runner jlink
```

**nRF5340 — select core:**
```bash
# Debug app core (default)
west debug --runner jlink -- --device nRF5340_xxAA_APP

# Debug net core
west debug --runner jlink -- --device nRF5340_xxAA_NET
```

### GDB with J-Link Server

```bash
# Terminal 1: Start J-Link GDB server
JLinkGDBServerCLExe -device nRF52840_xxAA -if SWD -speed 4000

# Terminal 2: Connect GDB
arm-none-eabi-gdb build/zephyr/zephyr.elf
(gdb) target remote :2331
(gdb) monitor reset
(gdb) load
(gdb) continue
```

## OpenOCD Support

OpenOCD can be used as an alternative to J-Link for development (requires open-source probe like CMSIS-DAP):

```bash
west flash --runner openocd
west debug --runner openocd
```

**Note:** On-board debug probe on Nordic DKs is J-Link. OpenOCD support is for external CMSIS-DAP probes like Black Magic Probe or DAPLink.
