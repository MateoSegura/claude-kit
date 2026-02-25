# ESP32 Errata and Known Gotchas

This file documents hardware errata, silicon-level bugs, and non-obvious behaviors across ESP32 variants. Always check the official Espressif errata document for your specific chip revision before tapeout.

---

## ESP32 (Original) — Critical Issues

### ADC2 Cannot Be Used Concurrently with WiFi

**Severity: Critical**

The ESP32's ADC2 peripheral shares hardware with the WiFi RF front-end. When WiFi is active (radio on), ADC2 reads return incorrect values or fail.

**Affected channels:** ADC2_CH0–CH9 (GPIO0, 2, 4, 12–15, 25–27)

**Workaround:**
- Use ADC1 channels (GPIO32–39) for all ADC measurements when WiFi is active.
- If ADC2 is required, gate WiFi off before reading ADC2: `esp_wifi_stop()`, read, `esp_wifi_start()`. This has high latency (~200 ms reconnect time).
- In Zephyr: the ESP32 ADC driver handles this via a mutex, but measurements during active WiFi from ADC2 should be treated as unreliable.

```c
/* Safe ADC1 channels (GPIO32-39) */
#define SAFE_ADC_CHANNEL ADC1_CHANNEL_6  /* GPIO34, input-only pin */

/* UNSAFE while WiFi on */
// ADC2_CHANNEL_0  /* GPIO4 — conflicts with WiFi */
```

---

### GPIO12 Strapping Pin — Flash Voltage Hazard

**Severity: Critical — can permanently damage module**

GPIO12 (MTDI) is sampled at boot to set the flash power supply voltage. When GPIO12 is:
- LOW (default pull-down): Flash VDD is 3.3V (correct for ESP-WROOM-32 and most modules)
- HIGH: Flash VDD is 1.8V (correct ONLY for modules with 1.8V flash)

If GPIO12 is driven or pulled HIGH on a 3.3V flash module, the flash chip receives incorrect voltage. At best the chip fails to boot; at worst it causes permanent flash damage.

**Affected modules:** All ESP32-WROOM-32, ESP-WROVER-B/IB, ESP32-PICO-D4 (check module datasheet)

**Workaround for external pull-up on GPIO12:**
1. Do not use GPIO12 in designs unless required.
2. If you must drive GPIO12, use `espefuse.py` to burn the `VDD_SDIO` efuse to 3.3V, removing the strapping function permanently:
   ```bash
   # ONE-TIME IRREVERSIBLE operation
   espefuse.py --port /dev/ttyUSB0 set_flash_voltage 3.3V
   ```
3. After burning the efuse, GPIO12 can be used freely.

---

### PSRAM Cache Corruption (ESP32 with SPIRAM)

**Severity: High — intermittent data corruption**

When external PSRAM (SPIRAM) is enabled on the original ESP32, the SPI2/SPI3 peripherals share the SPI bus used for PSRAM access. DMA transfers from SPI2/SPI3 that overlap with PSRAM cache eviction can cause data corruption.

**Root cause:** The SPIRAM uses SPI0 cache, and the CPU cache eviction may interfere with simultaneous DMA in certain timing windows.

**Workarounds:**
- Place DMA buffers in internal DRAM (not PSRAM): use `heap_caps_malloc(size, MALLOC_CAP_INTERNAL | MALLOC_CAP_DMA)`.
- Do not allocate DMA-capable buffers from PSRAM-backed heap.
- Disable PSRAM cache if using heavy SPI DMA: not practical for most applications.
- Use `ESP_INTR_FLAG_IRAM` for SPI interrupt handlers to ensure ISR code is in IRAM.

```c
/* Correct: DMA buffer in internal DRAM */
uint8_t *dma_buf = heap_caps_malloc(BUF_SIZE, MALLOC_CAP_DMA | MALLOC_CAP_INTERNAL);

/* WRONG: DMA buffer in PSRAM — will corrupt */
// uint8_t *dma_buf = heap_caps_malloc(BUF_SIZE, MALLOC_CAP_SPIRAM);
```

---

### I2C Clock Stretching Timeout (Chip Revision < 1)

**Severity: Medium — causes I2C bus hangs**

On ESP32 silicon revisions earlier than rev 1, the I2C master controller has a hardware bug where excessive clock stretching by a slave device causes the controller to lock up. The controller becomes unresponsive and requires a software reset.

**Workarounds:**
- Upgrade to ESP32 rev 1 or later (chip marking `ESP32-D0WD-V3` or revision info in ROM).
- Reduce I2C clock frequency to 100 kHz — slower clock gives more margin.
- Implement a watchdog reset or I2C bus recovery routine on timeout.
- In Zephyr, if `i2c_transfer()` returns `-EIO` or hangs, call `i2c_recover_bus()`.

---

### Bluetooth Classic + WiFi Coexistence — Throughput Degradation

**Severity: Low-Medium — throughput reduction**

When Bluetooth Classic (SPP, A2DP) and WiFi are used simultaneously, both share the 2.4 GHz radio. Espressif's coexistence algorithm time-multiplexes the radio, degrading throughput for both protocols. WiFi throughput can drop 30–50% under heavy BT Classic load.

**Note:** BLE + WiFi coexistence is better managed than BT Classic + WiFi.

---

## ESP32-S2 — Notable Issues

### USB OTG — No BLE Radio for Data Offload

The S2 has no Bluetooth at all. Applications requiring USB + wireless must use WiFi only. This is intentional design, not a bug — but commonly overlooked when migrating from ESP32.

### ADC Calibration Required for Accurate Readings

S2 ADC (like all ESP32 ADC) is not factory-trimmed per unit. Use the ADC calibration API to compensate for unit-to-unit variation:

```c
esp_adc_cal_characteristics_t cal_chars;
esp_adc_cal_value_t val_type = esp_adc_cal_characterize(
    ADC_UNIT_1, ADC_ATTEN_DB_11,
    ADC_WIDTH_BIT_13, 1100, &cal_chars);

uint32_t raw = adc1_get_raw(ADC1_CHANNEL_0);
uint32_t voltage_mv = esp_adc_cal_raw_to_voltage(raw, &cal_chars);
```

Without calibration, ADC readings can have ±100 mV or greater nonlinearity error.

---

## ESP32-S3 — Notable Issues

### PSRAM Octal Mode — Slower at Lower Temperatures

When ESP32-S3 is used with Octal SPI PSRAM at clock speeds ≥ 80 MHz, some PSRAM chips exhibit timing violations at temperatures below 0°C. This manifests as occasional read errors or system crashes in cold environments.

**Workaround:** Reduce Octal PSRAM clock to 40 MHz in cold-temperature designs, or use Quad SPI PSRAM.

### USB OTG — Cannot Use GPIO19/20 as GPIO When USB Active

GPIO19 (USB D−) and GPIO20 (USB D+) are muxed with USB OTG. When `CONFIG_USB_DEVICE_DRIVER=y` or USB CDC ACM is enabled, these pins are reserved and cannot be used as general GPIO.

---

## ESP32-C3 — Notable Issues

### Single Core — WiFi + Application Latency

The C3 is single-core. The WiFi stack and application run on the same core. Under heavy WiFi traffic, the application loop can experience latency spikes of 10–50 ms. Use work queues and avoid blocking in interrupt context.

### RISC-V — No Xtensa-specific Intrinsics

If porting code from ESP32/S2/S3, any assembly or Xtensa-specific intrinsics (`ISYNC`, `MEMW`, `__asm__ volatile("memw")`) must be replaced with RISC-V equivalents or standard `__sync_*` builtins.

---

## ESP32-C6 — Notable Issues

### IEEE 802.15.4 and WiFi Share RF — Cannot Run Simultaneously

Despite having both WiFi and IEEE 802.15.4, the C6 has a single RF front-end. True concurrent dual-radio operation is not possible — the two radios time-multiplex the antenna.

**Implication for Matter:** In Matter over WiFi + Thread concurrent mode, the C6 uses the ESP-Openthread radio coexistence mechanism. Throughput on both interfaces is reduced during simultaneous activity.

### LP Core Cannot Access HP Peripherals

The Low-Power (LP) RISC-V core can only access LP peripherals (LP GPIO, LP I2C, LP UART, LP ADC). It cannot access the HP SPI, I2S, USB, or Ethernet controllers. If LP core code attempts to access an HP peripheral, the result is undefined behavior or a bus fault.

---

## Memory Gotchas — All Variants

### IRAM vs DRAM Split

ESP32 SoCs map memory into three regions relevant to application code:

| Region | Address range (ESP32) | Purpose | Cacheable |
|--------|----------------------|---------|-----------|
| DRAM | `0x3FFC_0000–0x3FFF_FFFF` | Data (heap, stack, globals) | No — direct access |
| IRAM | `0x4007_0000–0x400A_FFFF` | Instruction (fast exec) | No — direct access |
| DROM/IROM | `0x3F40_0000–0x3F7F_FFFF` (D), `0x4008_0000–0x40BF_FFFF` (I) | Flash-mapped code + rodata | Yes — via cache |

**Key constraint:** Functions called from interrupt context MUST be in IRAM. If an interrupt handler calls a function that is in flash (IROM), and the flash cache is temporarily disabled (e.g., during flash write), the CPU will fetch an invalid instruction and crash.

```c
/* Force function into IRAM — safe to call from ISR */
void IRAM_ATTR my_isr_safe_function(void)
{
    /* This runs from IRAM, not flash cache */
}
```

**Zephyr equivalent:** Use `__attribute__((section(".iram1.text")))` or declare in an IRAM section defined in the linker script. Zephyr's ESP32 port marks ISR stubs with `IRAM_ATTR` automatically for its own code.

### DMA Buffer Requirements

DMA controllers can only access physical DRAM addresses. They cannot DMA from:
- Flash-mapped addresses (IROM/DROM)
- PSRAM (on original ESP32 — this is the PSRAM cache corruption issue)
- Stack-allocated buffers if the stack is in flash (should never happen, but watch for it)

```c
/* Safe DMA buffer allocation */
static uint8_t dma_buffer[1024] __attribute__((aligned(4)));

/* Also valid — statically in DRAM */
K_HEAP_DEFINE(dma_heap, 4096);
uint8_t *buf = k_heap_alloc(&dma_heap, 256, K_NO_WAIT);
```

Alignment: Most DMA engines require 4-byte alignment. SPI DMA on some variants requires the buffer to be word-aligned. The `__aligned(4)` attribute ensures this.

---

## WiFi and BLE Gotchas

### WiFi Init Required Before ADC2 Lock Check

Even if you are not actively transmitting WiFi, calling `esp_wifi_init()` reserves the ADC2 resource. Applications that call `esp_wifi_init()` for later use must assume ADC2 is unavailable from that point.

### WiFi Event Loop is Mandatory

The ESP-IDF WiFi stack requires an active event loop (`esp_event_loop_create_default()`). Without it, WiFi state transitions (connect, disconnect, IP acquisition) will queue internally and never be processed, causing apparent hangs.

In Zephyr, the WiFi driver creates its own internal event handling — do not create a separate ESP-IDF event loop alongside Zephyr's WiFi integration.

### BLE and Flash Writes Must Be Coordinated

During flash write operations (NVS commit, OTA write), interrupts are disabled for short periods. BLE connection events that occur during this window are missed, potentially causing connection drops.

**Mitigation:**
- Use `esp_bt_controller_disable()` before long flash writes if connection drop is unacceptable.
- Keep NVS writes small and frequent rather than batching large writes.
- Use a dedicated NVS task with lower priority than the BLE controller.

---

## Secure Boot and Flash Encryption Warnings

### Secure Boot is IRREVERSIBLE

Burning secure boot eFuses permanently locks the device to trust only firmware signed with a specific key. There is no factory reset mechanism.

**Before enabling secure boot:**
1. Generate and securely back up the signing key. Loss of this key means the device can never be updated.
2. Test the full OTA flow on a non-secure device first.
3. Verify that the bootloader and application images are correctly signed.

```bash
# Generate signing key (keep this key secure!)
espsecure.py generate_signing_key --version 2 secure_boot_signing_key.pem

# ONE-TIME irreversible operation
espsecure.py burn_key BLOCK_KEY1 secure_boot_signing_key.pem SECURE_BOOT_DIGEST1
```

### Flash Encryption Key is Generated On-Chip

When flash encryption is enabled for the first time, the ESP32 generates a random encryption key on the device and burns it to eFuses. The key is device-unique and never readable after generation. Factory firmware must be in plaintext; the device encrypts it on first boot.

**If the device is bricked (e.g., corrupted encrypted flash):** Recovery is only possible if plaintext download mode is not disabled and if you can reflash a new encrypted image. Once plaintext UART download is disabled via eFuse, recovery is impossible without a JTAG debugger that can still access ROM.

### Secure Boot v1 vs v2 (ESP32 original)

The original ESP32 supports secure boot v1 (ECDSA-based digest chain). Secure boot v2 on S2/S3/Cx/Hx provides a stronger chain of trust with RSA-PSS signature verification. For new designs, prefer a variant with v2.

---

## JTAG Gotchas

### GPIO12-15 Are JTAG Pins on Original ESP32

JTAG on original ESP32 uses GPIO12 (TDI), GPIO13 (TCK), GPIO14 (TMS), GPIO15 (TDO). If these GPIOs are used for other functions in the design (e.g., SPI SD card), JTAG debugging conflicts with normal operation.

**Solution:** Use a board revision where JTAG can be rerouted, or debug via the UART console. On S3/C3/C6, use the built-in USB Serial/JTAG instead.

### USB Serial/JTAG — Requires USB Enumeration

The USB Serial/JTAG peripheral on C3/C6/S3 requires a host USB connection for debugging to work. Remote debugging (UART log only) is not affected, but JTAG halt/step/breakpoints require an active USB host connection. This is obvious but often forgotten in headless deployments.
