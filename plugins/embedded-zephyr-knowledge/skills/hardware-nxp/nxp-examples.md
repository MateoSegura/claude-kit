# NXP Examples

## i.MX RT1060 FlexSPI Flash

```c
/* FlexSPI flash device from devicetree */
const struct device *flash = DEVICE_DT_GET(DT_NODELABEL(flash0));

/* Write to XIP-capable flash */
flash_write(flash, 0x1000, data, sizeof(data));
/* Read from flash (can also execute code via XIP) */
flash_read(flash, 0x1000, buffer, sizeof(buffer));
```

## LPC55S69 with TF-M

```bash
# Build secure + non-secure images with Trusted Firmware-M
west build -b lpcxpresso55s69_cpu0 --sysbuild
```

**sysbuild.conf:**

```kconfig
# Enable MCUboot bootloader for image signing
SB_CONFIG_BOOTLOADER_MCUBOOT=y
# Enable TF-M for secure services (crypto, secure storage)
SB_CONFIG_BUILD_WITH_TFM=y
```

## Kinetis K64F Sensor Hub

```c
/* I2C device for MPU6050 sensor */
const struct device *i2c = DEVICE_DT_GET(DT_NODELABEL(i2c0));

/* Write register address, read 6 bytes (accel X/Y/Z) */
i2c_write_read(i2c, 0x68, &reg, 1, data, 6);
```

## i.MX RT FlexSPI XIP Boot

**Kconfig:** `CONFIG_CODE_FLEXSPI=y`, `CONFIG_XIP=y`, `CONFIG_FLASH_MCUX_FLEXSPI_NOR=y`

**DTS:**

```dts
&flexspi {
    status = "okay"; ahb-bufferable; ahb-cacheable;
    rx-clock-source = <1>;  /* Loopback for high-speed XIP */
    flash0: is25wp064@0 {
        compatible = "nxp,imx-flexspi-nor";
        spi-max-frequency = <133000000>;  /* 133 MHz QSPI */
        size = <DT_SIZE_M(8)>;
    };
};
```

FCB (Flash Configuration Block) auto-generated at offset 0x400.

## LPC55S69 Dual-Core Communication

**DTS:** `&mailbox0 { status = "okay"; };`

**Kconfig:** `CONFIG_MBOX=y`, `CONFIG_MBOX_NXP_LPC_MAILBOX=y`, sysbuild: `SB_CONFIG_BUILD_WITH_REMOTE_IMAGE=y`

**CPU0 (sender):**

```c
#include <zephyr/drivers/mbox.h>
const struct device *mbox = DEVICE_DT_GET(DT_NODELABEL(mailbox0));
mbox_send(mbox, MBOX_CH_TO_CPU1, &(uint32_t){0x1234});
```

**CPU1 (receiver):**

```c
static void mbox_cb(const struct device *dev, uint32_t ch,
                    void *user_data, struct mbox_msg *msg) {
    uint32_t value = *(uint32_t *)msg->data;  /* Process from CPU0 */
}
mbox_register_callback(DEVICE_DT_GET(DT_NODELABEL(mailbox0)),
                       MBOX_CH_FROM_CPU0, mbox_cb, NULL);
```

## Kinetis ADC/DAC Usage

DTS: `&adc0 { status = "okay"; channel@c { reg = <12>; zephyr,gain = "ADC_GAIN_1"; zephyr,reference = "ADC_REF_INTERNAL"; zephyr,resolution = <12>; }; };`

Kconfig: `CONFIG_ADC=y`, `CONFIG_ADC_MCUX_ADC16=y`, `CONFIG_DAC=y`, `CONFIG_DAC_MCUX_DAC=y`

```c
const struct device *adc = DEVICE_DT_GET(DT_NODELABEL(adc0));
adc_channel_setup(adc, &(struct adc_channel_cfg){.channel_id = 12,
    .gain = ADC_GAIN_1, .reference = ADC_REF_INTERNAL});
uint16_t buffer;
adc_read(adc, &(struct adc_sequence){.channels = BIT(12), .buffer = &buffer,
    .buffer_size = sizeof(buffer), .resolution = 12});
dac_write_value(DEVICE_DT_GET(DT_NODELABEL(dac0)), 0, 2048);  /* 12-bit mid-scale */
```

## NXP-Specific DTS Patterns

**i.MX RT Pinctrl (IOMUXC):**

```dts
&iomuxc {
    pinmux_lpuart1: lpuart1grp {
        group0 {
            pinmux = <&iomuxc_gpio_ad_b0_12_lpuart1_tx>, <&iomuxc_gpio_ad_b0_13_lpuart1_rx>;
            drive-strength = "r0-6"; slew-rate = "slow"; bias-pull-up;  /* 150 ohm drive */
        };
    };
};
```

**FlexCAN:** `bus-speed = <125000>; sjw = <1>; prop-seg = <1>; phase-seg1 = <15>; phase-seg2 = <4>;`

**ENET:** `phy-reset-gpios = <&gpio1 9 GPIO_ACTIVE_LOW>; phy-reset-duration = <10>;`

**USB:** `&usb1 { status = "okay"; num-bidir-endpoints = <5>; };`

## Power Mode Transitions

**i.MX RT VLLS with GPIO Wakeup:**

Kconfig: `CONFIG_PM=y`, `CONFIG_PM_DEVICE=y`, `CONFIG_PM_POLICY_CUSTOM=y`. DTS: `&gpio1 { wakeup-source; };`

```c
#include <zephyr/pm/pm.h>
pm_state_force(0, &(struct pm_state_info){.state = PM_STATE_SUSPEND_TO_RAM});  /* VLLS */
k_sleep(K_FOREVER);  /* Resume after GPIO wakeup */
```

**LPC55S69 Deep Power-Down with RAM Retention:**

Kconfig: `CONFIG_PM=y`, `CONFIG_PM_S2RAM=y`. Retained RAM: `__noinit uint32_t counter;`

```c
void enter_deep_sleep(void) {
    counter++;  /* Persists across power-down */
    pm_state_force(0, &(struct pm_state_info){.state = PM_STATE_SUSPEND_TO_RAM});
    k_sleep(K_FOREVER);  /* Wakeup via RTC/GPIO */
}
