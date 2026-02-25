# HAL Patterns — Complete Reference

## HAL Interface Design Patterns

### Handle-Based API

```c
/* Opaque handle — application cannot access internals */
typedef struct hal_uart_impl *hal_uart_t;

/* Configuration struct groups all settings */
typedef struct {
    uint32_t baudrate;
    uint8_t data_bits;    /* 7, 8, 9 */
    uint8_t stop_bits;    /* 1, 2 */
    uint8_t parity;       /* NONE, EVEN, ODD */
    bool flow_control;
    uint8_t port;         /* Hardware UART instance */
} hal_uart_config_t;

/* Lifecycle */
int hal_uart_init(hal_uart_t *handle, const hal_uart_config_t *config);
int hal_uart_deinit(hal_uart_t handle);

/* Blocking I/O */
int hal_uart_write(hal_uart_t handle, const uint8_t *data, size_t len, uint32_t timeout_ms);
int hal_uart_read(hal_uart_t handle, uint8_t *data, size_t len, uint32_t timeout_ms);

/* Async I/O with callback */
typedef void (*hal_uart_cb_t)(hal_uart_t handle, int status, void *ctx);
int hal_uart_write_async(hal_uart_t handle, const uint8_t *data, size_t len, hal_uart_cb_t cb, void *ctx);
int hal_uart_read_async(hal_uart_t handle, uint8_t *data, size_t len, hal_uart_cb_t cb, void *ctx);
```

### Error Code Convention

```c
/* Consistent across all HAL modules */
#define HAL_OK           0
#define HAL_ERROR       -1    /* Generic error */
#define HAL_BUSY        -2    /* Resource in use */
#define HAL_TIMEOUT     -3    /* Operation timed out */
#define HAL_INVALID     -4    /* Invalid parameter */
#define HAL_NO_MEM      -5    /* Memory allocation failed */
#define HAL_NOT_READY   -6    /* Peripheral not initialized */
#define HAL_NOT_SUPPORT -7    /* Operation not supported */
```

### Callback vs Polling API

```c
/* Option 1: Callback (interrupt-driven) */
void my_rx_callback(hal_uart_t handle, int status, void *ctx) {
    if (status == HAL_OK) {
        process_received_data(ctx);
    }
}
hal_uart_read_async(uart, buffer, len, my_rx_callback, &my_context);

/* Option 2: Polling (simple, blocking) */
int received = hal_uart_read(uart, buffer, len, 1000 /* ms */);
if (received > 0) {
    process_received_data(buffer);
}

/* Option 3: Status check (non-blocking poll) */
while (!hal_uart_rx_ready(uart)) {
    /* Do other work */
}
hal_uart_read(uart, buffer, len, 0);
```

## Register Access Recipes

### Bit Field Macros

```c
/* Position and mask macros */
#define FIELD_POS(field)   (field##_Pos)
#define FIELD_MSK(field)   (field##_Msk)

/* Read a bit field */
#define REG_GET_FIELD(reg, field) \
    (((reg) & FIELD_MSK(field)) >> FIELD_POS(field))

/* Write a bit field */
#define REG_SET_FIELD(reg, field, value) \
    (reg) = ((reg) & ~FIELD_MSK(field)) | (((value) << FIELD_POS(field)) & FIELD_MSK(field))

/* Example usage */
#define CTRL_MODE_Pos  4
#define CTRL_MODE_Msk  (0x3 << CTRL_MODE_Pos)

uint32_t mode = REG_GET_FIELD(PERIPH->CTRL, CTRL_MODE);
REG_SET_FIELD(PERIPH->CTRL, CTRL_MODE, 2);
```

### Write-1-to-Clear Pattern

Common for status/interrupt flag registers:

```c
/* Hardware behavior: writing 1 to a bit clears it, writing 0 has no effect */

/* Clear specific flag */
PERIPH->STATUS = (1U << FLAG_BIT);   /* Only clears FLAG_BIT */

/* WRONG — clears ALL set flags */
// PERIPH->STATUS |= (1U << FLAG_BIT);  /* Read-modify-write clears other flags! */

/* Check and clear */
if (PERIPH->STATUS & (1U << FLAG_BIT)) {
    PERIPH->STATUS = (1U << FLAG_BIT);  /* Clear it */
    handle_flag();
}
```

### Register Access Barriers

On Cortex-M, ensure proper ordering of register accesses:

```c
/* Data Synchronization Barrier — ensures all memory accesses complete */
__DSB();

/* Data Memory Barrier — ensures ordering of memory accesses */
__DMB();

/* Instruction Synchronization Barrier — flushes pipeline */
__ISB();

/* Common usage: after modifying NVIC or SCB registers */
NVIC_EnableIRQ(UART1_IRQn);
__DSB();
__ISB();   /* Ensure interrupt is active before continuing */
```

## Peripheral Driver Patterns

### SPI Driver Skeleton

```c
struct spi_driver {
    volatile spi_regs_t *regs;  /* Hardware registers */
    hal_gpio_t cs_pin;          /* Chip select */
    struct {
        uint8_t *tx_buf;
        uint8_t *rx_buf;
        size_t len;
        size_t idx;
        hal_spi_cb_t callback;
        void *ctx;
    } transfer;
    bool initialized;
    bool busy;
};

int hal_spi_init(hal_spi_t *handle, const hal_spi_config_t *config) {
    struct spi_driver *drv = allocate_driver(config->instance);
    if (!drv) return HAL_NO_MEM;

    /* Enable peripheral clock */
    enable_spi_clock(config->instance);

    /* Configure pins (SCLK, MOSI, MISO as alternate function) */
    configure_spi_pins(config);

    /* Configure SPI registers */
    drv->regs->CR1 = 0;  /* Reset */
    drv->regs->CR1 |= compute_prescaler(config->frequency);
    drv->regs->CR1 |= (config->mode & 0x3) << SPI_CR1_CPHA_Pos;
    drv->regs->CR1 |= SPI_CR1_MSTR;  /* Master mode */

    /* Configure CS pin as GPIO output */
    hal_gpio_config_t cs_cfg = {
        .port = config->cs_port,
        .pin = config->cs_pin,
        .direction = HAL_GPIO_DIR_OUTPUT,
    };
    hal_gpio_init(&drv->cs_pin, &cs_cfg);
    hal_gpio_write(drv->cs_pin, true);  /* CS idle high */

    drv->initialized = true;
    *handle = (hal_spi_t)drv;
    return HAL_OK;
}

int hal_spi_transfer(hal_spi_t handle, const uint8_t *tx, uint8_t *rx, size_t len) {
    struct spi_driver *drv = (struct spi_driver *)handle;
    if (!drv->initialized) return HAL_NOT_READY;
    if (drv->busy) return HAL_BUSY;

    drv->busy = true;
    hal_gpio_write(drv->cs_pin, false);  /* Assert CS */

    for (size_t i = 0; i < len; i++) {
        /* Wait for TX buffer empty */
        while (!(drv->regs->SR & SPI_SR_TXE)) {}
        drv->regs->DR = tx ? tx[i] : 0xFF;

        /* Wait for RX buffer not empty */
        while (!(drv->regs->SR & SPI_SR_RXNE)) {}
        uint8_t byte = drv->regs->DR;
        if (rx) rx[i] = byte;
    }

    /* Wait for SPI not busy */
    while (drv->regs->SR & SPI_SR_BSY) {}

    hal_gpio_write(drv->cs_pin, true);  /* Deassert CS */
    drv->busy = false;
    return HAL_OK;
}
```

### I2C Driver with Timeout

```c
int hal_i2c_write_reg(hal_i2c_t handle, uint8_t dev_addr,
                       uint8_t reg_addr, const uint8_t *data, size_t len) {
    struct i2c_driver *drv = (struct i2c_driver *)handle;
    uint32_t start = get_tick_ms();

    /* Generate START */
    drv->regs->CR1 |= I2C_CR1_START;
    if (wait_flag(&drv->regs->SR1, I2C_SR1_SB, TIMEOUT_MS) != HAL_OK)
        return HAL_TIMEOUT;

    /* Send address + write */
    drv->regs->DR = (dev_addr << 1) | 0;  /* Write */
    if (wait_flag(&drv->regs->SR1, I2C_SR1_ADDR, TIMEOUT_MS) != HAL_OK)
        return HAL_TIMEOUT;
    (void)drv->regs->SR2;  /* Clear ADDR flag by reading SR2 */

    /* Send register address */
    drv->regs->DR = reg_addr;
    if (wait_flag(&drv->regs->SR1, I2C_SR1_TXE, TIMEOUT_MS) != HAL_OK)
        return HAL_TIMEOUT;

    /* Send data bytes */
    for (size_t i = 0; i < len; i++) {
        drv->regs->DR = data[i];
        if (wait_flag(&drv->regs->SR1, I2C_SR1_TXE, TIMEOUT_MS) != HAL_OK)
            return HAL_TIMEOUT;
    }

    /* Generate STOP */
    drv->regs->CR1 |= I2C_CR1_STOP;
    return HAL_OK;
}
```

## DMA Driver Patterns

### DMA Channel Allocation

```c
#define MAX_DMA_CHANNELS  8

static struct {
    bool allocated;
    void (*callback)(int channel, bool error);
    void *user_ctx;
} dma_channels[MAX_DMA_CHANNELS];

int dma_allocate_channel(int *channel) {
    for (int i = 0; i < MAX_DMA_CHANNELS; i++) {
        if (!dma_channels[i].allocated) {
            dma_channels[i].allocated = true;
            *channel = i;
            return HAL_OK;
        }
    }
    return HAL_NO_MEM;
}

void dma_free_channel(int channel) {
    dma_stop(channel);
    dma_channels[channel].allocated = false;
    dma_channels[channel].callback = NULL;
}
```

### DMA Interrupt Handler

```c
void DMA1_Channel1_IRQHandler(void) {
    uint32_t flags = DMA1->ISR;

    if (flags & DMA_ISR_TCIF1) {
        /* Transfer complete */
        DMA1->IFCR = DMA_IFCR_CTCIF1;  /* Clear flag */
        if (dma_channels[0].callback) {
            dma_channels[0].callback(0, false);
        }
    }

    if (flags & DMA_ISR_TEIF1) {
        /* Transfer error */
        DMA1->IFCR = DMA_IFCR_CTEIF1;
        if (dma_channels[0].callback) {
            dma_channels[0].callback(0, true);
        }
    }
}
```

## Board Support Package Templates

### Minimal BSP Interface

```c
/* bsp.h */

/* Board identification */
const char *bsp_get_board_name(void);
uint32_t bsp_get_board_revision(void);

/* System initialization (call before any peripheral use) */
int bsp_init(void);

/* Clock configuration */
uint32_t bsp_get_sysclk(void);
uint32_t bsp_get_apb1_clk(void);
uint32_t bsp_get_apb2_clk(void);

/* Board-specific pin definitions */
#define BSP_LED_RED_PORT     0
#define BSP_LED_RED_PIN      5
#define BSP_LED_GREEN_PORT   0
#define BSP_LED_GREEN_PIN    6
#define BSP_BUTTON_PORT      1
#define BSP_BUTTON_PIN       3
#define BSP_CONSOLE_UART     1   /* UART instance for debug console */
#define BSP_CONSOLE_BAUD     115200

/* Convenience functions */
void bsp_led_on(int led_index);
void bsp_led_off(int led_index);
void bsp_led_toggle(int led_index);
bool bsp_button_read(int button_index);
```

### BSP Init Sequence

```c
int bsp_init(void) {
    /* 1. Configure flash wait states (before increasing clock) */
    flash_set_latency(FLASH_LATENCY_4);

    /* 2. Configure power regulator voltage range */
    pwr_set_voltage_range(PWR_RANGE_1);

    /* 3. Enable HSE and configure PLL */
    rcc_enable_hse();
    rcc_configure_pll(/* ... */);
    rcc_set_sysclk_source(RCC_SYSCLK_PLL);

    /* 4. Configure bus clocks */
    rcc_set_ahb_prescaler(RCC_AHB_DIV_1);
    rcc_set_apb1_prescaler(RCC_APB1_DIV_1);
    rcc_set_apb2_prescaler(RCC_APB2_DIV_1);

    /* 5. Enable SysTick for timing */
    systick_init(bsp_get_sysclk() / 1000);  /* 1 ms tick */

    /* 6. Configure board-specific GPIO defaults */
    configure_led_pins();
    configure_button_pins();

    /* 7. Initialize debug console UART */
    console_uart_init(BSP_CONSOLE_BAUD);

    return HAL_OK;
}
```

### Multi-Board Support

```c
/* Board selection via compile-time define */
#if defined(BOARD_REV_A)
  #include "board_rev_a.h"
#elif defined(BOARD_REV_B)
  #include "board_rev_b.h"
#else
  #error "No board defined. Set BOARD_REV_A or BOARD_REV_B."
#endif

/* Or via function pointers for runtime selection */
typedef struct {
    void (*init)(void);
    void (*led_set)(int led, bool on);
    bool (*button_get)(int btn);
    const char *name;
} board_ops_t;

extern const board_ops_t board_rev_a;
extern const board_ops_t board_rev_b;

static const board_ops_t *board;

int bsp_init(uint8_t board_id) {
    switch (board_id) {
    case 0: board = &board_rev_a; break;
    case 1: board = &board_rev_b; break;
    default: return HAL_INVALID;
    }
    board->init();
    return HAL_OK;
}
```

## Testing HAL Implementations

### Mock Generation Pattern

```c
/* hal_gpio_mock.h — auto-generate from hal_gpio.h */

#define MAX_MOCK_CALLS  64

struct gpio_mock_call {
    enum { MOCK_INIT, MOCK_WRITE, MOCK_READ, MOCK_TOGGLE } type;
    union {
        struct { hal_gpio_config_t config; } init;
        struct { bool state; } write;
        struct { bool *state; } read;
    } args;
    int return_value;
};

static struct gpio_mock_call mock_calls[MAX_MOCK_CALLS];
static int mock_call_count;

/* Mock implementation */
int hal_gpio_write(hal_gpio_t handle, bool state) {
    mock_calls[mock_call_count++] = (struct gpio_mock_call){
        .type = MOCK_WRITE,
        .args.write.state = state,
        .return_value = HAL_OK,
    };
    return HAL_OK;
}

/* Test verification */
void assert_gpio_written(int call_index, bool expected_state) {
    assert(mock_calls[call_index].type == MOCK_WRITE);
    assert(mock_calls[call_index].args.write.state == expected_state);
}
```

### Hardware-in-the-Loop Test

```c
/* Test SPI loopback (MOSI connected to MISO) */
void test_spi_loopback(void) {
    uint8_t tx[] = {0xAA, 0x55, 0xDE, 0xAD};
    uint8_t rx[sizeof(tx)] = {0};

    int ret = hal_spi_transfer(spi_handle, tx, rx, sizeof(tx));
    assert(ret == HAL_OK);
    assert(memcmp(tx, rx, sizeof(tx)) == 0);
}

/* Test UART echo (TX connected to RX) */
void test_uart_echo(void) {
    const char *msg = "Hello";
    char reply[16] = {0};

    hal_uart_write(uart_handle, (uint8_t *)msg, 5, 100);
    int len = hal_uart_read(uart_handle, (uint8_t *)reply, 5, 100);
    assert(len == 5);
    assert(memcmp(msg, reply, 5) == 0);
}
```
