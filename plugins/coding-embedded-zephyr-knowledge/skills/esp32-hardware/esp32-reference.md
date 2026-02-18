# ESP32 Reference

## GPIO Matrix

ESP32 GPIO matrix allows any GPIO pin for any peripheral (with exceptions).

```dts
&uart0 {
    status = "okay";
    current-speed = <115200>;
    tx-pin = <1>;
    rx-pin = <3>;
};
```

## WiFi Configuration

```c
#include <zephyr/net/wifi_mgmt.h>

struct wifi_connect_req_params params = {
    .ssid = "MyNetwork",
    .ssid_length = strlen("MyNetwork"),
    .psk = "password",
    .psk_length = strlen("password"),
    .security = WIFI_SECURITY_TYPE_PSK,
};

net_mgmt(NET_REQUEST_WIFI_CONNECT, iface, &params, sizeof(params));
```

## Deep Sleep Wakeup Sources

**Timer wakeup:**

```c
esp_sleep_enable_timer_wakeup(10 * 1000000);  /* µs */
```

**GPIO wakeup:**

```c
esp_sleep_enable_ext0_wakeup(GPIO_NUM_0, 1);  /* GPIO 0, high level */
```

**RTC memory:**

```c
RTC_DATA_ATTR int state;  /* Survives deep sleep */
```

## Partition Table

**partitions.csv:**

```csv
# Name,   Type, SubType, Offset,  Size
nvs,      data, nvs,     0x9000,  0x6000
phy_init, data, phy,     0xf000,  0x1000
factory,  app,  factory, 0x10000, 1M
```
