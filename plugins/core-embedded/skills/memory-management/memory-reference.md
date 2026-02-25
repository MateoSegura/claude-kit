# Memory Management — Complete Reference

## Allocation Strategies in Detail

### Stack Allocator (Bump/Arena)

Fast, sequential allocation with bulk deallocation:

```c
struct arena {
    uint8_t *base;
    size_t size;
    size_t offset;
};

void arena_init(struct arena *a, uint8_t *buf, size_t size) {
    a->base = buf;
    a->size = size;
    a->offset = 0;
}

void *arena_alloc(struct arena *a, size_t bytes) {
    /* Align to 4 bytes */
    size_t aligned = (bytes + 3) & ~3;
    if (a->offset + aligned > a->size) return NULL;
    void *ptr = a->base + a->offset;
    a->offset += aligned;
    return ptr;
}

void arena_reset(struct arena *a) {
    a->offset = 0;  /* Free everything at once */
}
```

Use cases:
- Per-frame or per-request allocation (allocate many, free all at once)
- Parsing temporary structures
- Scratch memory for algorithms

### Type-Safe Memory Pool

```c
#define DEFINE_POOL(name, type, count)                          \
    static type name##_storage[count];                          \
    static uint8_t name##_used[count];                          \
    static struct { type *storage; uint8_t *used; int count; }  \
        name = { name##_storage, name##_used, count }

#define POOL_ALLOC(pool, ptr)                                   \
    do {                                                        \
        *(ptr) = NULL;                                          \
        for (int i = 0; i < (pool).count; i++) {                \
            if (!(pool).used[i]) {                              \
                (pool).used[i] = 1;                             \
                *(ptr) = &(pool).storage[i];                    \
                break;                                          \
            }                                                   \
        }                                                       \
    } while (0)

#define POOL_FREE(pool, ptr)                                    \
    do {                                                        \
        int idx = (ptr) - (pool).storage;                       \
        (pool).used[idx] = 0;                                   \
        (ptr) = NULL;                                           \
    } while (0)

/* Usage */
DEFINE_POOL(sensor_pool, struct sensor_reading, 32);

struct sensor_reading *reading;
POOL_ALLOC(sensor_pool, &reading);
if (reading) {
    reading->value = 42;
    /* ... use reading ... */
    POOL_FREE(sensor_pool, reading);
}
```

### Free List Allocator

Variable-size allocation with a linked list of free blocks:

```c
struct free_block {
    struct free_block *next;
    size_t size;
};

struct free_list_allocator {
    struct free_block *head;
    uint8_t *pool;
    size_t pool_size;
};

void *fl_alloc(struct free_list_allocator *fl, size_t size) {
    size = (size + sizeof(struct free_block) + 3) & ~3;
    struct free_block **prev = &fl->head;
    struct free_block *curr = fl->head;

    while (curr) {
        if (curr->size >= size) {
            /* Found a fit — first fit strategy */
            if (curr->size > size + sizeof(struct free_block) + 8) {
                /* Split block */
                struct free_block *remainder =
                    (struct free_block *)((uint8_t *)curr + size);
                remainder->size = curr->size - size;
                remainder->next = curr->next;
                *prev = remainder;
                curr->size = size;
            } else {
                *prev = curr->next;
            }
            return (uint8_t *)curr + sizeof(struct free_block);
        }
        prev = &curr->next;
        curr = curr->next;
    }
    return NULL;  /* No block large enough */
}
```

Fragmentation strategies:
- **First fit**: Fast but fragments over time
- **Best fit**: Less waste per allocation but slower scan
- **Coalescing**: Merge adjacent free blocks on free()

## Stack Analysis

### Static Analysis with Call Graph

Build the worst-case stack usage by analyzing the call tree:

```
main()                    [32 bytes]
  ├── process_sensors()   [64 bytes]
  │     ├── read_adc()    [16 bytes]
  │     └── filter()      [128 bytes]  <-- deepest non-ISR path
  └── send_report()       [48 bytes]
        └── format_msg()  [256 bytes]  <-- deepest non-ISR path

ISR:
  uart_isr()              [24 bytes]
    └── ring_put()        [8 bytes]

Worst case (non-ISR): 32 + 48 + 256 = 336 bytes
Worst case (with ISR): 336 + 32 (hardware) + 24 + 8 = 400 bytes
With 25% margin: 500 bytes
```

### GCC Stack Usage Output

```bash
arm-none-eabi-gcc -fstack-usage -c file.c
# Produces file.su with per-function stack usage
```

Output format:
```
file.c:10:6:main    128     static
file.c:25:6:process  64     dynamic,bounded
file.c:40:6:recurse  32     dynamic
```

- **static**: Fixed stack usage, fully analyzable
- **dynamic,bounded**: Uses variable-length arrays with known bounds
- **dynamic**: Unbounded (recursive or VLA without bound) — avoid in embedded

### Runtime Stack Monitoring

```c
#define STACK_CANARY  0xDEADBEEFU

/* Fill stack with canary before task starts */
void fill_stack_canary(uint32_t *stack_bottom, size_t words) {
    for (size_t i = 0; i < words; i++) {
        stack_bottom[i] = STACK_CANARY;
    }
}

/* Check high-water mark */
size_t stack_high_water(uint32_t *stack_bottom, size_t words) {
    size_t unused = 0;
    for (size_t i = 0; i < words; i++) {
        if (stack_bottom[i] == STACK_CANARY) {
            unused++;
        } else {
            break;
        }
    }
    return unused * sizeof(uint32_t);
}
```

## DMA Configuration Patterns

### Circular DMA for ADC

Continuously sample ADC channels into a rotating buffer:

```c
/* Configuration (pseudo-code) */
dma_config_t cfg = {
    .src = &ADC1->DR,            /* ADC data register */
    .dst = adc_buffer,            /* Destination buffer */
    .length = BUFFER_SIZE,
    .direction = DMA_PERIPH_TO_MEM,
    .width = DMA_WIDTH_HALFWORD,  /* 16-bit ADC values */
    .circular = true,             /* Auto-restart */
    .half_complete_irq = true,    /* Interrupt at half-buffer */
    .complete_irq = true,         /* Interrupt at full buffer */
};

/* Process in halves — while DMA fills one half, CPU processes the other */
void dma_half_complete_isr(void) {
    /* First half of adc_buffer[] is ready */
    signal_task(HALF_COMPLETE);
}

void dma_complete_isr(void) {
    /* Second half of adc_buffer[] is ready */
    signal_task(FULL_COMPLETE);
}
```

### Scatter-Gather DMA

Transfer non-contiguous memory regions in a single DMA operation:

```c
/* Linked list of DMA descriptors */
struct dma_descriptor {
    void *src;
    void *dst;
    uint32_t length;
    struct dma_descriptor *next;  /* NULL = end of chain */
    uint32_t control;             /* Interrupt on complete, etc. */
};

struct dma_descriptor chain[3] = {
    { .src = &header, .dst = tx_buf,      .length = 4,  .next = &chain[1] },
    { .src = payload, .dst = tx_buf + 4,  .length = 64, .next = &chain[2] },
    { .src = &crc,    .dst = tx_buf + 68, .length = 2,  .next = NULL      },
};
```

### Cache Management for DMA

```c
/* Before DMA writes to memory (invalidate so CPU reads fresh data) */
SCB_InvalidateDCache_by_Addr(buffer, length);
start_dma_periph_to_mem(buffer, length);

/* Before DMA reads from memory (flush so DMA sees latest CPU writes) */
SCB_CleanDCache_by_Addr(buffer, length);
start_dma_mem_to_periph(buffer, length);

/* Alternative: place buffer in non-cacheable MPU region */
__attribute__((section(".nocache")))
static uint8_t dma_buffer[256];
```

## Linker Script Recipes

### Basic Embedded Linker Script Structure

```ld
MEMORY {
    FLASH (rx)  : ORIGIN = 0x08000000, LENGTH = 512K
    SRAM  (rwx) : ORIGIN = 0x20000000, LENGTH = 128K
}

SECTIONS {
    .isr_vector : {
        KEEP(*(.isr_vector))
    } > FLASH

    .text : {
        *(.text*)
        *(.rodata*)
    } > FLASH

    .data : {
        _sdata = .;
        *(.data*)
        _edata = .;
    } > SRAM AT > FLASH
    _sidata = LOADADDR(.data);

    .bss : {
        _sbss = .;
        *(.bss*)
        *(COMMON)
        _ebss = .;
    } > SRAM

    ._user_heap_stack : {
        . = ALIGN(8);
        _end = .;
        . = . + _Min_Heap_Size;
        . = . + _Min_Stack_Size;
        . = ALIGN(8);
    } > SRAM
}
```

### Startup Code Data Copy

The `.data` section lives in SRAM at runtime but is initialized from Flash:

```c
/* Copy .data from Flash to SRAM */
extern uint32_t _sidata, _sdata, _edata, _sbss, _ebss;

void Reset_Handler(void) {
    uint32_t *src = &_sidata;
    uint32_t *dst = &_sdata;
    while (dst < &_edata) *dst++ = *src++;

    /* Zero .bss */
    dst = &_sbss;
    while (dst < &_ebss) *dst++ = 0;

    /* Call main */
    main();
}
```

### Custom Section Placement

```ld
/* In linker script */
.backup_sram (NOLOAD) : {
    *(.backup_sram)
} > BACKUP_SRAM

.dma_buffers (NOLOAD) : {
    *(.dma_buffers)
} > SRAM
```

```c
/* In C code */
__attribute__((section(".backup_sram")))
uint32_t persistent_counter;

__attribute__((section(".dma_buffers")))
__attribute__((aligned(32)))
uint8_t uart_dma_buf[512];
```

### Reading the Map File

Key sections in the `.map` file:

```
Memory Configuration:
Name   Origin    Length    Attributes
FLASH  0x08000000 0x80000  xr
SRAM   0x20000000 0x20000  xrw

Linker script and memory map:
.text    0x08000000  0x12340    (code size)
.rodata  0x08012340  0x01234    (constants)
.data    0x20000000  0x00500    (initialized globals)
.bss     0x20000500  0x02000    (zero-init globals)

Total Flash: .text + .rodata + .data(LMA) = ~79 KB
Total RAM:   .data + .bss + stack + heap  = ~10 KB
```

## Memory Protection Unit (MPU)

### Common MPU Configurations

```c
/* Stack overflow detection */
mpu_configure_region(
    .base = task_stack_bottom,
    .size = 32,             /* Guard region */
    .access = MPU_NO_ACCESS /* Fault on any access */
);

/* Peripheral isolation */
mpu_configure_region(
    .base = 0x40000000,
    .size = 0x20000000,    /* All peripherals */
    .access = MPU_PRIV_RW  /* Privileged access only */
);

/* DMA buffer — non-cacheable */
mpu_configure_region(
    .base = dma_buffer,
    .size = sizeof(dma_buffer),
    .access = MPU_FULL_ACCESS,
    .cacheable = false,
    .bufferable = true      /* Write-through */
);
```

### MPU Guidelines

- Use MPU to detect stack overflows (guard region below each stack)
- Protect peripheral registers from unprivileged access
- Mark DMA buffer regions as non-cacheable to avoid coherency issues
- Cortex-M0+: limited to 8 regions; M4/M7: up to 16 regions
- ARMv8-M (M33): supports background region and more flexible sizing
