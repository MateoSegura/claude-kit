---
name: core-embedded:hal-patterns
description: "Hardware abstraction layer design — register access patterns, peripheral driver lifecycle, DMA transfers, interrupt-safe APIs, and board support packages"
user-invocable: false
---

# HAL Patterns Quick Reference

## Why Hardware Abstraction

A Hardware Abstraction Layer (HAL) isolates application code from hardware specifics, enabling:

- **Portability** — Same application code runs on different MCUs
- **Testability** — Mock the HAL for host-based unit testing
- **Maintainability** — Hardware changes don't ripple through application logic
- **Team scaling** — Driver developers and application developers work independently

## HAL Architecture

```
+-------------------+
|   Application     |  Business logic, state machines
+-------------------+
|   HAL Interface   |  Abstract function signatures (header files)
+-------------------+
|   HAL Impl (MCU)  |  Register-level code, vendor SDK calls
+-------------------+
|   Hardware        |  Physical peripherals
+-------------------+
```

### Interface Design Principles

- **One header per peripheral type** — `hal_gpio.h`, `hal_spi.h`, `hal_uart.h`
- **Opaque handles** — Application holds a handle, never a raw register pointer
- **Error codes** — Consistent return type across all HAL functions (0 = success, negative = error)
- **No vendor types in the interface** — Use standard C types (`uint8_t`, `int`, `bool`)
- **Configuration structs** — Collect all settings into a typed struct

### Example HAL Interface

```c
/* hal_gpio.h — portable GPIO interface */

typedef struct hal_gpio *hal_gpio_t;   /* Opaque handle */

typedef enum {
    HAL_GPIO_DIR_INPUT,
    HAL_GPIO_DIR_OUTPUT,
} hal_gpio_dir_t;

typedef enum {
    HAL_GPIO_PULL_NONE,
    HAL_GPIO_PULL_UP,
    HAL_GPIO_PULL_DOWN,
} hal_gpio_pull_t;

typedef struct {
    uint8_t port;
    uint8_t pin;
    hal_gpio_dir_t direction;
    hal_gpio_pull_t pull;
} hal_gpio_config_t;

int hal_gpio_init(hal_gpio_t *handle, const hal_gpio_config_t *config);
int hal_gpio_deinit(hal_gpio_t handle);
int hal_gpio_write(hal_gpio_t handle, bool state);
int hal_gpio_read(hal_gpio_t handle, bool *state);
int hal_gpio_toggle(hal_gpio_t handle);
```

## Register Access Patterns

### Direct Register Access

```c
/* Define register addresses */
#define PERIPH_BASE     0x40010000UL
#define PERIPH_CTRL     (*(volatile uint32_t *)(PERIPH_BASE + 0x00))
#define PERIPH_STATUS   (*(volatile uint32_t *)(PERIPH_BASE + 0x04))
#define PERIPH_DATA     (*(volatile uint32_t *)(PERIPH_BASE + 0x08))
```

### Bit Field Manipulation

```c
/* Set specific bits (bitwise OR) */
PERIPH_CTRL |= (1U << 3);          /* Set bit 3 */

/* Clear specific bits (AND with inverted mask) */
PERIPH_CTRL &= ~(1U << 3);         /* Clear bit 3 */

/* Modify a multi-bit field */
#define FIELD_MASK  (0x7U << 4)     /* Bits [6:4] */
#define FIELD_VAL(x) (((x) & 0x7U) << 4)

PERIPH_CTRL = (PERIPH_CTRL & ~FIELD_MASK) | FIELD_VAL(5);

/* Check a bit */
if (PERIPH_STATUS & (1U << 0)) {
    /* Bit 0 is set */
}
```

### Set/Clear Register Pattern

Many MCUs provide atomic set and clear registers to avoid read-modify-write races:

```c
#define PERIPH_SET    (*(volatile uint32_t *)(PERIPH_BASE + 0x10))
#define PERIPH_CLR    (*(volatile uint32_t *)(PERIPH_BASE + 0x14))

PERIPH_SET = (1U << 3);    /* Atomic set bit 3 */
PERIPH_CLR = (1U << 3);    /* Atomic clear bit 3 */
```

### Register Struct Overlay

```c
typedef struct {
    volatile uint32_t CTRL;       /* 0x00 */
    volatile uint32_t STATUS;     /* 0x04 */
    volatile uint32_t DATA;       /* 0x08 */
    volatile uint32_t RESERVED;   /* 0x0C */
    volatile uint32_t SET;        /* 0x10 */
    volatile uint32_t CLR;        /* 0x14 */
} periph_regs_t;

#define PERIPH  ((periph_regs_t *)0x40010000UL)

/* Usage */
PERIPH->CTRL |= (1U << 3);
while (!(PERIPH->STATUS & (1U << 0))) { /* wait */ }
uint32_t data = PERIPH->DATA;
```

## Peripheral Driver Lifecycle

### State Machine

```
           init()
             |
             v
  +-------------------+
  |   INITIALIZED     |  Configured but not running
  +-------------------+
         |        ^
  enable() |    | disable()
         v        |
  +-------------------+
  |     ACTIVE        |  Peripheral running, processing data
  +-------------------+
         |
   deinit()
         |
         v
  +-------------------+
  |   UNINITIALIZED   |  Resources released
  +-------------------+
```

### Lifecycle Functions

```c
/* 1. Init — allocate resources, configure registers, do NOT start */
int driver_init(driver_handle_t *handle, const driver_config_t *config);

/* 2. Enable — start the peripheral (enable interrupts, start DMA) */
int driver_enable(driver_handle_t handle);

/* 3. Runtime operations */
int driver_read(driver_handle_t handle, uint8_t *buf, size_t len);
int driver_write(driver_handle_t handle, const uint8_t *buf, size_t len);

/* 4. Disable — stop the peripheral, retain configuration */
int driver_disable(driver_handle_t handle);

/* 5. Deinit — release all resources, disable clocks */
int driver_deinit(driver_handle_t handle);
```

### Init/Deinit Checklist

| Step | Init | Deinit |
|------|------|--------|
| Clock | Enable peripheral clock | Disable peripheral clock |
| GPIO | Configure alternate function pins | Reset pins to default |
| Registers | Write configuration | Reset to defaults |
| Interrupts | Configure NVIC priority | Disable NVIC IRQ |
| DMA | Allocate channel, configure | Release channel |
| State | Set to INITIALIZED | Set to UNINITIALIZED |

## DMA-Based Transfers

### DMA Transfer Setup

```c
/* Generic DMA transfer configuration */
typedef struct {
    void *src;              /* Source address (peripheral or memory) */
    void *dst;              /* Destination address */
    size_t length;          /* Transfer length in bytes */
    enum {
        DMA_DIR_PERIPH_TO_MEM,
        DMA_DIR_MEM_TO_PERIPH,
        DMA_DIR_MEM_TO_MEM,
    } direction;
    enum {
        DMA_WIDTH_BYTE,
        DMA_WIDTH_HALFWORD,
        DMA_WIDTH_WORD,
    } width;
    bool circular;          /* Auto-restart at end */
    void (*callback)(void *ctx, bool error);  /* Completion callback */
    void *ctx;
} dma_config_t;
```

### Double-Buffer (Ping-Pong) Pattern

```c
uint8_t buffer_a[BUFFER_SIZE];
uint8_t buffer_b[BUFFER_SIZE];
volatile bool use_buffer_a = true;

void dma_complete_isr(void) {
    /* DMA just finished filling one buffer */
    uint8_t *ready = use_buffer_a ? buffer_a : buffer_b;
    use_buffer_a = !use_buffer_a;

    /* Switch DMA to the other buffer */
    dma_set_dest(use_buffer_a ? buffer_a : buffer_b);

    /* Signal task to process 'ready' buffer */
    signal_processing_task(ready);
}
```

### DMA Guidelines

- Place DMA buffers in non-cacheable memory (or manage cache coherency)
- Align buffers to transfer width (4-byte aligned for word transfers)
- Use circular mode for continuous streaming (ADC, audio)
- Handle DMA errors (transfer error interrupt, FIFO overrun)
- Disable DMA channel before reconfiguring

## Interrupt-Safe APIs

### Design Rules

1. **Never block** — No mutex lock, no sleep, no memory allocation
2. **Bounded execution** — ISR must complete within a known time
3. **Minimal work** — Read register, set flag, signal task, return
4. **Reentrant-safe** — Use local variables, avoid modifying globals without protection

### Critical Section Patterns

```c
/* Disable/restore interrupts (short critical section) */
uint32_t saved = disable_interrupts();
/* ... access shared data ... */
restore_interrupts(saved);

/* Disable specific interrupt only (less invasive) */
nvic_disable_irq(UART1_IRQn);
/* ... access UART1 shared state ... */
nvic_enable_irq(UART1_IRQn);
```

### Lock-Free Communication

```c
/* Single-producer, single-consumer ring buffer (ISR to task) */
struct ring_buf {
    uint8_t data[RING_SIZE];
    volatile uint32_t head;   /* Written by producer (ISR) */
    volatile uint32_t tail;   /* Written by consumer (task) */
};

/* ISR writes */
void ring_put(struct ring_buf *rb, uint8_t byte) {
    uint32_t next = (rb->head + 1) % RING_SIZE;
    if (next != rb->tail) {   /* Not full */
        rb->data[rb->head] = byte;
        rb->head = next;      /* Atomic on 32-bit ARM */
    }
}

/* Task reads */
bool ring_get(struct ring_buf *rb, uint8_t *byte) {
    if (rb->head == rb->tail) return false;  /* Empty */
    *byte = rb->data[rb->tail];
    rb->tail = (rb->tail + 1) % RING_SIZE;
    return true;
}
```

## Board Support Packages (BSP)

### BSP Responsibilities

| Component | Purpose |
|-----------|---------|
| Clock init | Configure oscillators, PLLs, bus clocks |
| Pin mux | Map peripheral signals to physical pins |
| Memory init | Configure SDRAM, external flash, MPU regions |
| Boot sequence | Low-level startup before main() |
| Board-specific defaults | LED pins, button pins, console UART |

### BSP Structure

```
bsp/
├── bsp.h                  /* Public board API */
├── board_<name>.c         /* Board-specific implementation */
├── clock_config.c         /* Clock tree configuration */
├── pin_mux.c              /* Pin multiplexing */
└── startup.c              /* Reset handler, vector table */
```

### BSP Design Guidelines

- Separate board-specific code from generic driver code
- Use a board header that defines pin mappings as named constants
- Provide a `bsp_init()` function that configures clocks, pins, and core peripherals
- Keep vendor SDK calls isolated in the BSP — application code uses HAL interfaces
- Support multiple board variants through compile-time selection (#ifdef or separate files)

## Testing HAL Code

### Mock-Based Testing

```c
/* hal_gpio.h — same interface */
/* hal_gpio_stm32.c — real implementation */
/* hal_gpio_mock.c — test mock */

/* Mock records calls and returns configured values */
static bool mock_gpio_state;
int hal_gpio_write(hal_gpio_t handle, bool state) {
    mock_gpio_state = state;
    return 0;
}
int hal_gpio_read(hal_gpio_t handle, bool *state) {
    *state = mock_gpio_state;
    return 0;
}
```

### Testing Strategy

| Level | What | How |
|-------|------|-----|
| Unit test | HAL interface logic | Mock registers, run on host |
| Integration test | Driver + hardware | Run on target, verify peripheral behavior |
| System test | Full application | End-to-end on target hardware |

## Additional Resources

- For detailed register access recipes, DMA configuration examples, and BSP templates, see [hal-reference.md](hal-reference.md)
