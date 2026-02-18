# STM32 Examples

## SPI Sensor (Nucleo-H743ZI)

```c
const struct device *spi = DEVICE_DT_GET(DT_NODELABEL(spi1));

struct spi_config spi_cfg = {
    .frequency = 1000000,
    .operation = SPI_WORD_SET(8) | SPI_TRANSFER_MSB,
};

spi_transceive(spi, &spi_cfg, &tx_bufs, &rx_bufs);
```

## Low-Power (STM32L4)

```c
void main(void) {
    /* Configure wake source */
    /* Enter stop mode */
    k_sleep(K_FOREVER);  /* PM subsystem handles power mode */
}
```

**Kconfig:**

```kconfig
CONFIG_PM=y
CONFIG_TICKLESS_KERNEL=y
```

## STM32WB BLE

```bash
west build -b nucleo_wb55rg
```

**Network core runs BLE stack.**
