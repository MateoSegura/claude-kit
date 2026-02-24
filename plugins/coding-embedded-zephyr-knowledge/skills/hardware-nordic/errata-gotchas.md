# Nordic nRF Errata and Common Gotchas

## nRF52832 Errata

Official errata: https://infocenter.nordicsemi.com/topic/errata_nRF52832_Rev3/ERR/nRF52832/Rev3/latest/err_832.html

### [73] SAADC — Calibration Offset

**Symptom:** SAADC readings are systematically offset by up to ±10 mV.

**Root cause:** The SAADC internal calibration is not applied automatically on first use.

**Workaround:** Call offset calibration before first conversion:

```c
#include <nrfx_saadc.h>

nrfx_saadc_init(NRFX_SAADC_DEFAULT_CONFIG_IRQ_PRIORITY);
nrfx_saadc_offset_calibrate(NULL);  /* Blocking calibration */
/* Now initialize channels and start conversion */
```

**Zephyr:** The Zephyr SAADC driver (`drivers/adc/adc_nrfx_saadc.c`) applies the workaround automatically on nRF52832. You only need to worry about this when using nrfx HAL directly.

### [89] SPI Slave (SPIS) — Data Loss

**Symptom:** First byte of received SPI data may be corrupted when CPU exits WFI between CS assert and first clock edge.

**Workaround:** Do not use `k_sleep()` or WFI between SPI transactions. Keep the CPU active while SPIS is in use, or accept that the first transfer after idle may be corrupted and add application-level retry.

**Zephyr:** No automatic mitigation. Applications using SPIS on nRF52832 must account for this.

### [108] RAM — Idle Power Consumption

**Symptom:** Some RAM sections consume more power than expected in System ON idle.

**Workaround:** Power down unused RAM banks:

```c
nrf_power_ramon_set(NRF_POWER, NRF_POWER_RAMON_OFFRAM0_RAMOFF |
                               NRF_POWER_RAMON_OFFRAM1_RAMOFF);
```

Or use `CONFIG_RAM_POWER_DOWN_LIBRARY=y` in Zephyr and call the power-down API.

**Impact:** Significant in low-power designs. Without this workaround, idle current can be 2-4 µA higher than datasheet typical.

### [211] TWIM — Spurious STOPPED Event

**Symptom:** TWIM emits a STOPPED event immediately after starting a transfer, before the transfer completes. This causes the driver to think the transfer finished, but no data was sent.

**Workaround:** Clear the STOPPED event and retry, or detect the anomaly (byte count doesn't match). Nordic provides a workaround function `twim_transfer_workaround()`.

**Zephyr:** The `nrf_twim` driver includes the workaround automatically. The anomaly is not reproducible on all samples, but it occurs in field deployments. Ensure you have the latest Zephyr HAL for nRF.

---

## nRF52840 Errata

Official errata: https://infocenter.nordicsemi.com/topic/errata_nRF52840_Rev3/ERR/nRF52840/Rev3/latest/err_840.html

### [198] SPIM3 — EasyDMA Anomaly

**Symptom:** SPIM3 (the high-speed SPI instance capable of 32 MHz) may produce corrupted output when used with EasyDMA and certain clock configurations.

**Root cause:** SPIM3 has a dedicated RAM memory interface separate from normal AHB. Buffers placed outside a specific RAM region cause anomalous behavior.

**Workaround:** Ensure SPIM3 TX/RX buffers are placed in a specific SRAM region (documented in the errata). Use `__attribute__((section(".spim3_buf")))` and place that section in the linker script at an address within the correct region.

**Zephyr:** Zephyr's SPIM driver applies the buffer region constraint for SPIM3 automatically via DTS memory regions. When writing custom drivers, consult the nrfx `nrfx_spim.c` source for the exact buffer constraint.

### [218] USBD — VBUS Detection

**Symptom:** USB enumeration may fail or VBUS voltage detection gives incorrect results if the VBUS detector is not properly initialized before the USB stack starts.

**Workaround:** Initialize the VBUS comparator before enabling the USB driver:

```c
#include <nrfx_power.h>

nrfx_power_init(&power_config);
nrfx_power_usbevt_enable();
/* Wait for VBUS ready before starting USB stack */
```

**Zephyr:** Handled in the nRF USBD driver when `CONFIG_USB_DEVICE_STACK=y`. The driver hooks into `nrfx_power` events. Do not call `nrfx_power_init()` separately when using Zephyr USB — Zephyr owns that init.

### [219] HFXO — Startup Time

**Symptom:** HFXO (high-frequency crystal oscillator) may take longer than the 1 ms startup time documented in the datasheet under some temperature/voltage conditions.

**Workaround:** Add 2-3 ms guard time after requesting HFXO before depending on it for RADIO or USBD operations.

**Zephyr:** The radio driver handles HFXO startup timing. For custom applications that manually request HFXO:

```c
nrf_clock_task_trigger(NRF_CLOCK, NRF_CLOCK_TASK_HFCLKSTART);
/* Wait at minimum 2 ms, or poll the HFCLKSTARTED event */
while (!nrf_clock_hfclk_is_running(NRF_CLOCK)) {
    k_busy_wait(100);
}
```

---

## nRF5340 Errata and Gotchas

Official errata: https://infocenter.nordicsemi.com/topic/errata_nRF5340_Rev2/ERR/nRF5340/Rev2/latest/err_340.html

### IPC Timing — Shared RAM Race

**Symptom:** Race condition when both cores access shared RAM near the IPC boundary simultaneously. Data corruption or deadlock in RPMsg transport.

**Workaround:** Always use the IPC/RPMsg APIs provided by Zephyr — do not access IPC shared memory directly. The nRF5340 SRAM boundary for IPC is at a fixed address; Zephyr's linker scripts place IPC buffers there.

**Key rule:** Application firmware should not manually map `.noinit` or `.data` sections into the IPC shared memory region.

### QSPI Cache — Write Corruption

**Symptom:** When writing to external QSPI flash while the QSPI XIP cache is enabled, stale cache entries can be read back instead of the newly written data.

**Workaround:** Always flush/invalidate the QSPI cache before and after write operations:

```c
nrf_qspi_cinstr_long_transfer_start(NRF_QSPI, &cinstr_cfg);
/* After write, flush cache */
nrf_qspi_cache_invalidate(NRF_QSPI);
```

**Zephyr:** The `nordic,nrf-qspi-nor` driver handles cache invalidation automatically for write operations when `CONFIG_FLASH=y`. Direct `nrfx_qspi` usage requires manual cache management.

### TrustZone — Non-Secure Callable Gates

**Symptom:** Application crashes or peripheral access faults when non-secure code tries to access a peripheral assigned to the secure domain.

**Root cause:** nRF5340 app core implements TrustZone. Peripherals are assigned as Secure (S) or Non-Secure (NS) via SPU registers. The SPM (Secure Partition Manager) or TF-M configures these assignments. If a peripheral is S but the main app runs in NS, access faults occur.

**Workaround:**
- Use `CONFIG_BUILD_WITH_TFM=y` (TF-M) or a custom SPM to configure peripheral assignments
- Most Zephyr nRF5340 builds run in NS by default; SPM/TF-M assigns standard peripherals to NS automatically
- When adding custom peripherals, ensure the SPM configuration assigns them to NS

---

## nRF9160 / nRF91 Gotchas

### Modem Firmware Version Lock

**Symptom:** Application crashes or modem commands return unexpected errors after modem firmware update.

**Root cause:** The modem library (`libmodem`) is compiled against a specific modem firmware version. Mismatches cause undefined behavior.

**Rule:** `CONFIG_NRF_MODEM_LIB=y` application and the modem firmware must be from the same nRF Connect SDK version. When updating NCS, update modem firmware too.

**Check modem firmware version:**

```c
#include <modem/nrf_modem_lib.h>
#include <nrf_modem_at.h>

char buf[64];
nrf_modem_at_cmd(buf, sizeof(buf), "AT+CGMR");
/* Returns: mfw_nrf9160_<version> */
```

**Update via nrfutil:**

```bash
nrfutil device program --firmware mfw_nrf9160_1.3.6.zip \
    --options chip_erase_mode=ERASE_NONE,reset_after_program=RESET_HARD
```

### GPS Cold Start — 30+ Seconds

**Symptom:** GPS fix takes 30-90 seconds on first use or after long periods without a fix.

**Root cause:** Cold start requires downloading almanac/ephemeris from satellites. Assisted GPS (A-GPS) reduces this to seconds by downloading data over LTE.

**Mitigation:**

```c
#include <modem/nrf_modem_gnss.h>

/* Enable A-GPS before starting fix */
nrf_modem_gnss_agps_data_write(&agps_data, agps_data_type);
/* Then start fix */
nrf_modem_gnss_start();
```

Use nRF Cloud A-GPS service or nRF Cloud P-GPS (predicted GPS) for even faster fixes without requiring a real-time LTE connection.

---

## Common Cross-Family Pitfalls

### NFC Pins P0.09 / P0.10 (nRF52 series)

**Problem:** Pins P0.09 and P0.10 are reserved for NFC by default, even if NFC is not used. GPIO attempts to configure these pins silently fail or produce unexpected results.

**Detection:** Application configures a GPIO on P0.09/P0.10, but reads always return 0 or writes have no effect.

**Fix:**

```kconfig
CONFIG_NFCT_PINS_AS_GPIOS=y  # Releases NFC pins for GPIO use
```

This is safe if NFC is not used. If NFC is needed, use different GPIO pins for other functions.

### DCDC Not Enabled = High Power

**Problem:** Board schematic includes the DCDC inductor but the firmware does not enable DCDC, resulting in LDO operation and 2-3× higher power than expected.

**Diagnostic:** Use PPK2 and compare measured current vs. datasheet typical. If significantly higher, verify DCDC is enabled in Kconfig.

**Check:** Read back the DCDCEN register to confirm hardware state.

### External Crystal Not Started

**Problem:** BLE or USB requires HFXO (32 MHz external crystal). If the crystal is missing from the PCB or specified with wrong load capacitance, the HFXO fails to start and radio/USB operations hang indefinitely.

**Detection:** HFXO `HFCLKSTARTED` event never fires; application hangs in the clock initialization wait loop.

**Fix:**
1. Verify crystal is populated on PCB
2. Match crystal load capacitance to nRF52 internal capacitor config in DTS:

```dts
&clock {
    hfxo-startup-time-us = <1000>;
    /* Crystal-specific: adjust to match crystal load capacitance */
};
```

### EasyDMA Buffer in Flash (const qualifier)

**Problem:** Declaring a DMA buffer as `const` causes the linker to place it in flash. DMA transfer silently fails or produces a HardFault (bus error on DMA access to flash).

```c
/* WRONG */
static const uint8_t spi_cmd[] = {0x9F};  /* May go to flash */

/* CORRECT */
static uint8_t spi_cmd[] = {0x9F};        /* Stays in RAM */
```

**Linker verification:** Check map file to confirm buffer section is in SRAM.

### nRF5340 Missing cpuapp/cpunet Qualifier

**Problem:** West build command missing `_cpuapp` or `_cpunet` suffix on board name. The wrong image is built for the wrong core.

```bash
# WRONG — builds without core qualifier (may default to wrong core)
west build -b nrf5340dk

# CORRECT
west build -b nrf5340dk_nrf5340_cpuapp --sysbuild
west build -b nrf5340dk_nrf5340_cpunet  # Rare — usually sysbuild handles this
```

**Rule:** Always use `--sysbuild` for nRF5340. This automatically builds the net core `hci_ipc` image and flashes both images in one `west flash` command.

### Stack Overflow in BLE Callbacks

**Problem:** BLE event callbacks (on_connected, on_received) execute in the BLE thread context with a limited stack. Allocating large local variables or calling deeply nested functions causes silent stack overflow and crashes.

**Fix:** Keep BLE callbacks short. Use `k_work_submit()` to defer heavy processing to the application thread:

```c
static void on_received(struct bt_conn *conn, const uint8_t *const data, uint16_t len)
{
    /* Copy data quickly, defer processing */
    memcpy(rx_buf, data, len);
    rx_len = len;
    k_work_submit(&rx_work);  /* Process in work queue */
}
```

Increase BLE stack sizes if needed:
```kconfig
CONFIG_BT_RX_STACK_SIZE=2048
CONFIG_BT_HCI_TX_STACK_SIZE=1536
```
