# Nordic nRF Examples

## BLE Peripheral (nRF52840)

```c
#include <zephyr/bluetooth/bluetooth.h>

static const struct bt_data ad[] = {
    BT_DATA_BYTES(BT_DATA_FLAGS, BT_LE_AD_GENERAL | BT_LE_AD_NO_BREDR),
};

void main(void) {
    bt_enable(NULL);
    bt_le_adv_start(BT_LE_ADV_CONN_NAME, ad, ARRAY_SIZE(ad), NULL, 0);
}
```

## Dual-Core nRF5340

**Application core (cpuapp):**

```bash
west build -b nrf5340dk_nrf5340_cpuapp --sysbuild
```

**Network core runs BLE controller automatically.**

## nRF9160 LTE-M

```c
#include <modem/lte_lc.h>

void main(void) {
    lte_lc_init_and_connect();
    /* Use sockets for data */
}
```

**Kconfig:**

```kconfig
CONFIG_LTE_LINK_CONTROL=y
CONFIG_LTE_NETWORK_MODE_LTE_M=y
```
