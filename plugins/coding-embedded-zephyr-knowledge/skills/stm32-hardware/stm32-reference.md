# STM32 Reference

## Pinctrl Configuration

```dts
&pinctrl {
    usart1_tx_pa9: usart1_tx_pa9 {
        pinmux = <STM32_PINMUX('A', 9, AF7)>;
    };
    usart1_rx_pa10: usart1_rx_pa10 {
        pinmux = <STM32_PINMUX('A', 10, AF7)>;
    };
};

&usart1 {
    pinctrl-0 = <&usart1_tx_pa9 &usart1_rx_pa10>;
    pinctrl-names = "default";
};
```

## RCC (Reset and Clock Control)

**System clock:**

```dts
&rcc {
    clocks = <&pll>;
    ahb-prescaler = <1>;
    apb1-prescaler = <4>;
    apb2-prescaler = <2>;
};
```

## HAL Integration

Zephyr uses STM32 HAL under the hood.

```kconfig
CONFIG_USE_STM32_HAL_LIBRARY=y
```

## Power Modes

- **Run** — Full speed
- **Sleep** — CPU clock off
- **Stop** — Most clocks off, RAM retained
- **Standby** — Deepest sleep, minimal RAM retention

```kconfig
CONFIG_PM_STATE_SUSPEND_TO_IDLE=y  # Stop mode
CONFIG_PM_STATE_SOFT_OFF=y         # Standby mode
```
