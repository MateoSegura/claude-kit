# Nordic nRF Reference

## nRF Devicetree Bindings

**GPIO:**

```dts
&gpio0 {
    status = "okay";
};

led0: led_0 {
    gpios = <&gpio0 13 GPIO_ACTIVE_LOW>;
};
```

**UART:**

```dts
&uart0 {
    status = "okay";
    current-speed = <115200>;
    pinctrl-0 = <&uart0_default>;
    pinctrl-names = "default";
};
```

**I2C (TWIM):**

```dts
&i2c0 {
    compatible = "nordic,nrf-twim";
    status = "okay";
    clock-frequency = <I2C_BITRATE_FAST>;
    pinctrl-0 = <&i2c0_default>;
    pinctrl-names = "default";
};
```

## BLE Configuration

```kconfig
CONFIG_BT=y
CONFIG_BT_PERIPHERAL=y
CONFIG_BT_DEVICE_NAME="nRF Device"

# Controller configuration
CONFIG_BT_CTLR_TX_PWR_PLUS_8=y  # +8 dBm TX power
CONFIG_BT_CTLR_DATA_LENGTH_MAX=251
```

## Power Management

**System OFF:**

```c
#include <zephyr/pm/pm.h>

pm_state_force(0, &(struct pm_state_info){PM_STATE_SOFT_OFF, 0, 0});
```

**DCDC configuration:**

```kconfig
CONFIG_DCDC_HV=y
CONFIG_DCDC_LV=y  # nRF53/91 only
```

## nRF9160 Cellular

**Kconfig:**

```kconfig
CONFIG_LTE_LINK_CONTROL=y
CONFIG_MODEM_INFO=y
```

**AT Commands:**

```c
#include <modem/at_cmd.h>

char response[128];
at_cmd_write("AT+CFUN=1", response, sizeof(response), NULL);
```
