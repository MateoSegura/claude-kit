# Nordic nRF Power Modes Reference

## Power State Hierarchy

```
System ON
├── Active (CPU running, peripherals active)
├── CPU Idle (WFE/WFI, peripherals can run)
└── Low-power idle (peripherals suspended via PM)

System OFF (deepest sleep — only GPIO/NFC/RTC wakeup)
```

## System ON States

### Active Mode

CPU executing code. Current consumption depends on clock frequency and peripherals active:

| SoC | Active (CPU @ max freq) | Notes |
|-----|------------------------|-------|
| nRF52832 | ~5.5 mA @ 64 MHz | With LDO |
| nRF52832 | ~3.6 mA @ 64 MHz | With DCDC |
| nRF52840 | ~6.6 mA @ 64 MHz | With LDO |
| nRF52840 | ~4.8 mA @ 64 MHz | With DCDC |
| nRF5340 (app) | ~7 mA @ 128 MHz | With DCDC |
| nRF9160 (active) | ~6 mA | App MCU + peripherals |

### CPU Idle (WFI/WFE)

CPU halted waiting for interrupt. Most peripherals can continue running (UART, SPI, timers). Zephyr enters this automatically when the kernel has nothing to execute.

Typical idle current:
- nRF52832: ~1.5 µA (with DCDC, 32 kHz LFXO, peripherals off)
- nRF52840: ~2 µA (similar conditions)
- nRF5340: ~3 µA (both cores idle)

### Zephyr PM — Automatic Low-Power

With `CONFIG_PM=y`, Zephyr's power management automatically selects the deepest state compatible with the next scheduled wakeup. The HAL driver tells Zephyr which PM states the hardware supports.

```kconfig
CONFIG_PM=y               # Enable system power management
CONFIG_PM_DEVICE=y        # Enable per-device power management
CONFIG_PM_DEVICE_RUNTIME=y  # Runtime PM (suspend/resume on demand)
```

**PM states for nRF52:**

| PM State | Zephyr Constant | Wakeup Latency | Notes |
|----------|----------------|----------------|-------|
| Active | `PM_STATE_ACTIVE` | — | Normal operation |
| Runtime idle | `PM_STATE_RUNTIME_IDLE` | < 1 ms | CPU sleep, timers run |
| Suspend to idle | `PM_STATE_SUSPEND_TO_IDLE` | ~1-5 ms | Most peripherals off |
| Soft OFF | `PM_STATE_SOFT_OFF` | Full boot | = System OFF |

**Force a PM state:**

```c
#include <zephyr/pm/pm.h>

/* Force System OFF immediately (deep sleep) */
pm_state_force(0u, &(struct pm_state_info){PM_STATE_SOFT_OFF, 0, 0});
k_sleep(K_MSEC(1));  /* Yield to allow PM to execute */
```

## System OFF (Deep Sleep)

System OFF completely powers down the SoC except for the power-on reset logic and selected wakeup sources. All RAM content is lost unless RAM retention is configured.

**Wakeup sources in System OFF:**

| Source | How to configure |
|--------|-----------------|
| GPIO with sense | `gpio_pin_interrupt_configure_dt(&btn, GPIO_INT_LEVEL_LOW)` + `zephyr,wakeup-source` in DTS |
| NFC field | `CONFIG_NFC_T2T_NRFXLIB=y` — any NFC field triggers wakeup |
| RTC compare | `nrf_rtc_cc_set()` before System OFF |
| COMP/LPCOMP | Configure comparator before sleep |
| Reset pin | Always active |

**System OFF entry via Zephyr:**

```c
/* Via PM subsystem (recommended) */
pm_state_force(0u, &(struct pm_state_info){PM_STATE_SOFT_OFF, 0, 0});
k_sleep(K_MSEC(1));

/* Via nrfx (direct, bypasses Zephyr PM) */
nrf_power_system_off(NRF_POWER);
```

After wakeup from System OFF, the SoC performs a full reset. Check `nrf_power_resetreas_get()` to determine wakeup reason:

```c
uint32_t reason = nrf_power_resetreas_get(NRF_POWER);
if (reason & NRF_POWER_RESETREAS_OFF_MASK) {
    /* Woke from System OFF via GPIO sense */
}
nrf_power_resetreas_clear(NRF_POWER, reason);
```

## DCDC Regulators — Why They Matter

Nordic SoCs have two power supply options: internal LDO (linear) or DCDC (switching). DCDC is 2-3× more efficient.

**Power saving example (nRF52832, VDD=3.0V, active mode):**

| Regulator | Active current | Idle current |
|-----------|---------------|-------------|
| LDO only | 5.5 mA | 2.4 µA |
| DCDC | 3.6 mA | 1.4 µA |

**Enabling DCDC in Zephyr:**

```kconfig
# nRF52 series — high-voltage DCDC (VDDMAIN)
CONFIG_DCDC_HV=y

# nRF5340 — both regulators
CONFIG_DCDC_HV=y   # Main supply regulator
CONFIG_DCDC_LV=y   # Internal core regulator

# nRF9160 — similar to nRF5340
CONFIG_DCDC_HV=y
CONFIG_DCDC_LV=y
```

**DTS alternative (board-level):**
Many official DKs enable DCDC in their board DTS via `reg-init-microvolt`. Check your board's DTS to confirm DCDC status before assuming it's enabled.

**DCDC requires external inductor:** An external 10 µH inductor connected to the DCDC_DEC pin is required. Production boards must include this component; dev kits already have it. Without the inductor, enabling DCDC causes unstable voltage and system crashes.

## RAM Retention in System OFF

By default, all RAM is powered off in System OFF. RAM retention keeps selected banks powered (typically 4 KB or 8 KB banks) at the cost of ~0.5-1 µA per bank.

```kconfig
CONFIG_RAM_POWER_DOWN_LIBRARY=y  # Enable nRF RAM power library
```

**nRF52840 RAM banks:** 8× 32 KB banks (total 256 KB). Each bank can be independently retained.

**Retaining specific sections:**

```c
#include <nrfx_power.h>

/* Retain only bank 0 (0x20000000–0x20008000) in System OFF */
nrfx_power_ram_retention_configure(0x01);  /* Bit mask of banks to retain */
```

**Zephyr linker section for retained data:**

```c
/* Declare variable in retained section */
static __noinit __attribute__((section(".noinit"))) uint32_t boot_count;
```

`.noinit` variables are not zeroed on reset, but their values survive only if the RAM bank is retained through System OFF.

## nRF5340 Dual-Core Power Domains

App core and net core have independent power domains:

| Domain | Controls | Can be powered off |
|--------|---------|-------------------|
| CPUAPP | Application M33 | No (main system power) |
| CPUNET | Network M33 + radio | Yes — when radio not needed |

**Powering down net core when idle:**

```kconfig
# App core prj.conf
CONFIG_SOC_NRF_CPUNET_ENABLE=n  # Don't start net core at boot
```

Or at runtime from app core:

```c
#include <nrf53_cpunet_mgmt.h>
nrf53_cpunet_enable(false);  /* Power down net core */
```

Net core power domain consumes ~0.8 µA when powered off. When BLE is not needed (e.g., in firmware update mode from USB), power down the net core.

## nRF9160 Modem Power States

The nRF9160 modem has independent power management from the application MCU:

| Modem State | Current | Description |
|------------|---------|-------------|
| Active TX | ~220 mA peak | LTE transmission |
| Active RX | ~6 mA | LTE receive window |
| PSM (Power Saving Mode) | ~2.5 µA | TAU timer running, modem off |
| eDRX | ~3-15 µA avg | Periodic receive windows |
| RRC Idle | ~0.8 mA | Connected but no transfer |

**PSM configuration:**

```c
#include <modem/lte_lc.h>

/* Request PSM with 10 min TAU, 2 s active timer */
lte_lc_psm_req(true);
/* Or set specific values */
int err = lte_lc_psm_param_set("01000011", "00000001");
/* Format: TAU T3412, ACTIVE T3324 (3GPP TS 24.008) */
```

**eDRX configuration:**

```c
lte_lc_edrx_req(true);
/* Configure cycle with LTE_LC_EDRX_PARAM_* */
```

**RAI (Release Assistance Indication):** Signal to network that no more data expected, allowing faster release of RRC connection and faster entry to PSM:

```c
lte_lc_rai_req(true);  /* Set RAI flag on next data send */
```

## Measuring Power with PPK2

Nordic's Power Profiler Kit II (PPK2) is a current measurement tool with 100 nA resolution and 100 kHz sampling.

**PPK2 modes:**
- **Ampere meter:** Measures current of connected DUT with its own power supply
- **Source meter:** PPK2 supplies DUT power AND measures current (up to 500 mA)

**Recommended measurement setup for nRF52840DK:**
1. Remove the current measurement jumper if present
2. Connect PPK2 in source meter mode to VDD_nRF
3. Set voltage to 3.3V or 3.0V (match your application)
4. Use nRF Connect Power Profiler app (Windows/Mac/Linux)

**Kconfig for accurate measurements:**
```kconfig
# Disable UART logging (causes periodic wakeups)
CONFIG_LOG=n
CONFIG_UART_CONSOLE=n

# Disable shell (keeps UART active)
CONFIG_SHELL=n

# Ensure PM is enabled
CONFIG_PM=y
CONFIG_PM_DEVICE=y
```

**Interpreting measurements:**
- Periodic spikes are expected for BLE advertising (brief, ~2 ms each 1s interval)
- Constant elevated baseline = something keeping CPU/peripheral active
- Unexpected wakeups = check `CONFIG_PM_DEBUG=y` and PM state log
