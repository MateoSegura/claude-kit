# STM32 Examples

Compilable Zephyr code examples targeting STM32 boards with common peripheral configurations.

## GPIO — Nucleo-F446RE

```c
/* Toggle LED and read button on Nucleo-F446RE */
#include <zephyr/drivers/gpio.h>
#include <zephyr/kernel.h>

#define LED0_NODE DT_ALIAS(led0)
#define SW0_NODE  DT_ALIAS(sw0)

static const struct gpio_dt_spec led = GPIO_DT_SPEC_GET(LED0_NODE, gpios);
static const struct gpio_dt_spec btn = GPIO_DT_SPEC_GET(SW0_NODE, gpios);
static struct gpio_callback btn_cb_data;

void button_pressed(const struct device *dev, struct gpio_callback *cb, uint32_t pins)
{
    gpio_pin_toggle_dt(&led);
}

int main(void)
{
    int ret;

    ret = gpio_pin_configure_dt(&led, GPIO_OUTPUT_ACTIVE);
    __ASSERT(ret == 0, "Failed to configure LED: %d", ret);

    ret = gpio_pin_configure_dt(&btn, GPIO_INPUT);
    __ASSERT(ret == 0, "Failed to configure button: %d", ret);

    ret = gpio_pin_interrupt_configure_dt(&btn, GPIO_INT_EDGE_TO_ACTIVE);
    __ASSERT(ret == 0, "Failed to configure interrupt: %d", ret);

    gpio_init_callback(&btn_cb_data, button_pressed, BIT(btn.pin));
    gpio_add_callback(btn.dt_spec.port, &btn_cb_data);

    while (1) {
        k_msleep(1000);
    }
    return 0;
}
```

## SPI Sensor — Nucleo-H743ZI

```c
/* SPI sensor read on Nucleo-H743ZI */
#include <zephyr/drivers/spi.h>
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(spi_sensor, LOG_LEVEL_INF);

#define SPI_NODE DT_NODELABEL(spi1)

static const struct device *spi_dev = DEVICE_DT_GET(SPI_NODE);

static struct spi_config spi_cfg = {
    .frequency = 1000000,
    .operation = SPI_WORD_SET(8) | SPI_TRANSFER_MSB | SPI_OP_MODE_MASTER,
    .cs = NULL,  /* Use hardware CS or configure via devicetree */
};

int read_sensor_register(uint8_t reg, uint8_t *value)
{
    uint8_t tx_data = reg | 0x80;  /* Read bit */
    uint8_t rx_data;

    struct spi_buf tx_buf = { .buf = &tx_data, .len = 1 };
    struct spi_buf rx_buf = { .buf = &rx_data, .len = 1 };
    struct spi_buf_set tx = { .buffers = &tx_buf, .count = 1 };
    struct spi_buf_set rx = { .buffers = &rx_buf, .count = 1 };

    int ret = spi_transceive(spi_dev, &spi_cfg, &tx, &rx);
    if (ret < 0) {
        LOG_ERR("SPI transceive failed: %d", ret);
        return ret;
    }

    *value = rx_data;
    return 0;
}
```

**Devicetree overlay (nucleo_h743zi.overlay):**

```dts
/* Enable SPI1 with sensor on Nucleo-H743ZI */
&spi1 {
    status = "okay";
    pinctrl-0 = <&spi1_sck_pa5 &spi1_miso_pa6 &spi1_mosi_pa7>;
    pinctrl-names = "default";
    cs-gpios = <&gpioa 4 GPIO_ACTIVE_LOW>;
};
```

## Low-Power Modes — STM32L4

```c
/* Low-power with wake-on-interrupt on STM32L4 */
#include <zephyr/kernel.h>
#include <zephyr/pm/pm.h>
#include <zephyr/pm/policy.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(low_power, LOG_LEVEL_INF);

#define WAKE_PIN_NODE DT_ALIAS(sw0)
static const struct gpio_dt_spec wake_pin = GPIO_DT_SPEC_GET(WAKE_PIN_NODE, gpios);

int main(void)
{
    int ret;

    ret = gpio_pin_configure_dt(&wake_pin, GPIO_INPUT);
    if (ret < 0) {
        LOG_ERR("Failed to configure wake pin: %d", ret);
        return ret;
    }

    /* Configure interrupt as wake source */
    ret = gpio_pin_interrupt_configure_dt(&wake_pin, GPIO_INT_EDGE_TO_ACTIVE);
    if (ret < 0) {
        LOG_ERR("Failed to configure interrupt: %d", ret);
        return ret;
    }

    LOG_INF("Entering low-power mode, press button to wake");

    /* PM subsystem automatically selects the deepest allowable state */
    /* k_sleep triggers the idle thread which invokes PM policy */
    k_sleep(K_FOREVER);

    return 0;
}
```

**Kconfig for STM32L4 power management:**

```kconfig
CONFIG_PM=y
CONFIG_PM_DEVICE=y
CONFIG_TICKLESS_KERNEL=y
# STM32L4 supports Stop 0, Stop 1, Stop 2, Standby, Shutdown
CONFIG_PM_S2RAM=y
```

## STM32WB BLE — Nucleo-WB55RG

The STM32WB has a dual-core architecture: M4 runs the application, M0+ runs the BLE stack.

```c
/* BLE peripheral on STM32WB — advertise and accept connections */
#include <zephyr/bluetooth/bluetooth.h>
#include <zephyr/bluetooth/gap.h>
#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(ble_wb, LOG_LEVEL_INF);

static const struct bt_data ad[] = {
    BT_DATA_BYTES(BT_DATA_FLAGS, (BT_LE_AD_GENERAL | BT_LE_AD_NO_BREDR)),
    BT_DATA_BYTES(BT_DATA_UUID16_ALL, 0x0d, 0x18),  /* Heart Rate Service */
};

static void connected(struct bt_conn *conn, uint8_t err)
{
    if (err) {
        LOG_ERR("Connection failed (err %u)", err);
        return;
    }
    LOG_INF("Connected");
}

static void disconnected(struct bt_conn *conn, uint8_t reason)
{
    LOG_INF("Disconnected (reason %u)", reason);
}

BT_CONN_CB_DEFINE(conn_callbacks) = {
    .connected = connected,
    .disconnected = disconnected,
};

int main(void)
{
    int err = bt_enable(NULL);
    if (err) {
        LOG_ERR("Bluetooth init failed (err %d)", err);
        return err;
    }

    LOG_INF("Bluetooth initialized");

    err = bt_le_adv_start(BT_LE_ADV_CONN_NAME, ad, ARRAY_SIZE(ad), NULL, 0);
    if (err) {
        LOG_ERR("Advertising failed to start (err %d)", err);
        return err;
    }

    LOG_INF("Advertising started");
    return 0;
}
```

**Build command:**

```bash
west build -b nucleo_wb55rg samples/bluetooth/peripheral_hr
```

**Note:** The M0+ core must be flashed with the appropriate BLE stack binary from ST (stm32wb_copro). Use STM32CubeProgrammer or the `stm32wb_copro` module in Zephyr.

## I2C Sensor — Nucleo-F411RE

```c
/* I2C temperature sensor read on Nucleo-F411RE */
#include <zephyr/drivers/i2c.h>
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(i2c_sensor, LOG_LEVEL_INF);

#define I2C_NODE DT_NODELABEL(i2c1)
#define SENSOR_ADDR 0x48  /* TMP102 default address */

static const struct device *i2c_dev = DEVICE_DT_GET(I2C_NODE);

int read_temperature(int16_t *temp_raw)
{
    uint8_t buf[2];

    int ret = i2c_burst_read(i2c_dev, SENSOR_ADDR, 0x00, buf, sizeof(buf));
    if (ret < 0) {
        LOG_ERR("I2C read failed: %d", ret);
        return ret;
    }

    /* TMP102: 12-bit resolution, MSB first */
    *temp_raw = ((int16_t)buf[0] << 4) | (buf[1] >> 4);
    return 0;
}

int main(void)
{
    if (!device_is_ready(i2c_dev)) {
        LOG_ERR("I2C device not ready");
        return -ENODEV;
    }

    while (1) {
        int16_t raw;
        if (read_temperature(&raw) == 0) {
            /* TMP102: 0.0625 C per LSB */
            LOG_INF("Temperature: %d.%02d C", raw / 16, (raw % 16) * 625 / 100);
        }
        k_msleep(2000);
    }
    return 0;
}
```

**Devicetree overlay (nucleo_f411re.overlay):**

```dts
/* Enable I2C1 with TMP102 sensor on Nucleo-F411RE */
&i2c1 {
    status = "okay";
    clock-frequency = <I2C_BITRATE_FAST>;

    tmp102@48 {
        compatible = "ti,tmp102";
        reg = <0x48>;
    };
};
```
