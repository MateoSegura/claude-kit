# NXP Reference

## NXP Devicetree Bindings

**LPSPI:**

```dts
&lpspi1 {
    status = "okay";
    clock-frequency = <1000000>;
};
```

**LPUART:**

```dts
&lpuart1 {
    status = "okay";
    current-speed = <115200>;
};
```

**LPI2C:**

```dts
&lpi2c1 {
    status = "okay";
    clock-frequency = <I2C_BITRATE_FAST>;
};
```

## FlexSPI Configuration

**Boot header:**

Generated automatically by Zephyr for i.MX RT.

**Flash algorithm:**

```kconfig
CONFIG_FLASH=y
CONFIG_FLASH_MCUX_FLEXSPI_NOR=y
```

## LPC55S69 Dual-Core

**Secure core (CM33_0):**

```bash
west build -b lpcxpresso55s69_cpu0 --sysbuild
```

**With TF-M:**

```kconfig
SB_CONFIG_BUILD_WITH_TFM=y
```

## Power Modes

**Deep sleep:**

```c
pm_state_force(0, &(struct pm_state_info){PM_STATE_SUSPEND_TO_IDLE, 0, 0});
```
