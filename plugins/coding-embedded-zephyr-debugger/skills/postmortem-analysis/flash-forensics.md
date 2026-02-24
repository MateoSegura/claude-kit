# Flash Forensics

MCUboot image header parsing, swap status analysis, retained RAM inspection, and flash wear analysis for postmortem debugging.

## MCUboot Image Header

MCUboot images have a fixed header structure at the beginning of each slot.

### Header Format (v1)

| Offset | Size | Field | Description |
|--------|------|-------|-------------|
| 0x00 | 4 | ih_magic | Magic number: `0x96F3B83D` |
| 0x04 | 4 | ih_load_addr | Image load address (usually 0) |
| 0x08 | 2 | ih_hdr_size | Header size (typically 0x200 = 512 bytes) |
| 0x0A | 2 | ih_protect_tlv_size | Protected TLV area size |
| 0x0C | 4 | ih_img_size | Image size (excluding header and TLV) |
| 0x10 | 4 | ih_flags | Image flags |
| 0x14 | 1 | ih_ver.iv_major | Version major |
| 0x15 | 1 | ih_ver.iv_minor | Version minor |
| 0x16 | 2 | ih_ver.iv_revision | Version revision |
| 0x18 | 4 | ih_ver.iv_build_num | Build number |
| 0x1C | 4 | _pad1 | Padding |

### Header Flags

| Flag | Value | Meaning |
|------|-------|---------|
| IMAGE_F_PIC | 0x0001 | Position-independent code |
| IMAGE_F_ENCRYPTED_AES128 | 0x0004 | AES-128 encrypted |
| IMAGE_F_ENCRYPTED_AES256 | 0x0008 | AES-256 encrypted |
| IMAGE_F_NON_BOOTABLE | 0x0010 | Not directly bootable |
| IMAGE_F_RAM_LOAD | 0x0020 | Loaded to RAM before execution |

### Reading Header via GDB/J-Link

```bash
# J-Link Commander
J-Link> mem32 <slot_addr> 8   # Read first 32 bytes

# GDB
(gdb) x/8x <slot_addr>
# Check magic at offset 0: should be 0x96F3B83D

# Full header
(gdb) x/16x <slot_addr>
```

### Parsing Header in Shell

```bash
# Using xxd and manual inspection
# Assuming dump saved to slot0.bin
xxd -l 32 slot0.bin

# Check magic
xxd -s 0 -l 4 -e slot0.bin
# Expected: 3db8f396 (little-endian of 0x96F3B83D)

# Read version
xxd -s 20 -l 8 slot0.bin
```

## TLV (Type-Length-Value) Area

After the image data, MCUboot stores metadata in TLV format:

| Type | Value | Description |
|------|-------|-------------|
| IMAGE_TLV_SHA256 | 0x10 | SHA-256 hash of image |
| IMAGE_TLV_RSA2048_PSS | 0x20 | RSA-2048 signature |
| IMAGE_TLV_ECDSA224 | 0x21 | ECDSA-P224 signature |
| IMAGE_TLV_ECDSA256 | 0x22 | ECDSA-P256 signature |
| IMAGE_TLV_RSA3072_PSS | 0x23 | RSA-3072 signature |
| IMAGE_TLV_ED25519 | 0x24 | ED25519 signature |
| IMAGE_TLV_ENC_RSA2048 | 0x30 | Encrypted key (RSA-2048) |
| IMAGE_TLV_ENC_EC256 | 0x31 | Encrypted key (ECIES-P256) |
| IMAGE_TLV_DEPENDENCY | 0x40 | Image dependency |

### Finding TLV Area

```
TLV offset = ih_hdr_size + ih_img_size
TLV area starts with a 4-byte info header:
  - 2 bytes: TLV info magic (0x6907)
  - 2 bytes: Total TLV area size
```

## Swap Status Analysis

MCUboot uses a swap mechanism for firmware upgrades. Understanding swap status is critical for diagnosing boot loops and failed upgrades.

### Swap Types

| Type | Description | Trigger |
|------|-------------|---------|
| BOOT_SWAP_TYPE_NONE | No swap, boot from primary | Normal boot |
| BOOT_SWAP_TYPE_TEST | Swap once, revert on next boot unless confirmed | `boot_set_pending(0)` |
| BOOT_SWAP_TYPE_PERM | Swap permanently, no revert | `boot_set_pending(1)` |
| BOOT_SWAP_TYPE_REVERT | Reverting to previous image | Failed test swap |
| BOOT_SWAP_TYPE_FAIL | Swap failed | Interrupted swap |
| BOOT_SWAP_TYPE_PANIC | MCUboot panic | Corrupted state |

### Image Trailer (Swap Status Bytes)

At the end of each slot, MCUboot stores swap status:

```
Slot end - BOOT_MAGIC_SZ:
  [magic]      4 bytes: 0x77C2 9504 0000 2CFA (boot magic)
  [swap_type]  1 byte:  Swap type code
  [copy_done]  1 byte:  0x01 = copy complete
  [image_ok]   1 byte:  0x01 = image confirmed
```

### Reading Swap Status

```bash
# Find slot end address
# slot_end = slot_start + slot_size

# Read last 16 bytes of primary slot
J-Link> mem32 <slot_end - 16> 4

# Or in GDB
(gdb) x/4x <slot_end - 16>
```

### Diagnosing Boot Loops

```
Symptom: Device keeps rebooting after firmware update

Check sequence:
1. Read primary slot header → valid magic? correct version?
2. Read primary slot image_ok → 0x01 means confirmed
3. If image_ok != 0x01 and swap_type = TEST → revert will occur
4. Read secondary slot header → is old image still there?
5. If both slots valid but boot loops → image crashes before confirmation
   → Fix: call boot_write_img_confirmed() early in main()
```

## Retained RAM Analysis

Some MCUs provide retained RAM (non-volatile SRAM) that survives reset. Zephyr can use this for crash breadcrumbs.

### Zephyr Retained RAM Configuration

```
# Enable retained RAM
CONFIG_RETAINED_MEM=y

# Platform-specific
# nRF: Uses GPREGRET registers (2 bytes) or retained SRAM
# STM32: Uses backup SRAM (requires VBAT)
```

### Common Breadcrumb Patterns

```c
/* Application stores crash breadcrumbs in retained RAM */
struct crash_info {
    uint32_t magic;        /* 0xCRASH001 if valid */
    uint32_t reset_reason; /* Hardware reset reason register */
    uint32_t fault_pc;     /* PC at fault */
    uint32_t fault_lr;     /* LR at fault */
    uint32_t uptime_ms;    /* k_uptime_get() at crash */
    uint32_t crash_count;  /* Incremented each crash */
};
```

### Reading Retained RAM

```bash
# nRF52: GPREGRET registers
nrfjprog --memrd 0x4000051C --n 4   # GPREGRET0
nrfjprog --memrd 0x40000520 --n 4   # GPREGRET1

# nRF52: Retained SRAM (if configured)
nrfjprog --memrd 0x20000000 --n 64  # First 64 bytes of SRAM

# STM32: Backup SRAM
# Address varies by STM32 family, typically 0x40024000
```

### Reset Reason Analysis

```bash
# nRF52: RESETREAS register
nrfjprog --memrd 0x40000400 --n 4

# Bit meanings:
# Bit 0: RESETPIN (external pin reset)
# Bit 1: DOG (watchdog reset)
# Bit 2: SREQ (software reset)
# Bit 3: LOCKUP (CPU lockup reset)
# Bit 16: OFF (wake from OFF mode)
# Bit 17: LPCOMP (wake from comparator)
# Bit 18: DIF (debug interface)
# Bit 19: NFC (NFC field detect)
# Bit 20: VBUS (USB VBUS detect)
```

## Flash Wear Analysis

Flash memory has limited write cycles. Excessive writes degrade reliability.

### Identifying Hot Spots

```
Common flash hot spots in Zephyr:
1. Settings partition (CONFIG_SETTINGS_FCB or CONFIG_SETTINGS_NVS)
2. Coredump partition (if CONFIG_DEBUG_COREDUMP_BACKEND_FLASH_PARTITION)
3. MCUboot swap status bytes (written on every upgrade)
4. File system partition (LittleFS, FAT)
```

### NVS Wear Assessment

```bash
# NVS (Non-Volatile Storage) uses sector rotation
# Check sector headers for erase count

# Find NVS partition address
grep -A5 "storage_partition" build/zephyr/zephyr.dts

# Read first 8 bytes of each NVS sector
# NVS sector header: [ATE (8 bytes)] [data...]
# ATE contains erase count
```

### Flash Write Limits

| Flash Type | Typical Endurance | Notes |
|------------|------------------|-------|
| Internal NOR (nRF52) | 10,000 cycles | Per page (4KB pages) |
| Internal NOR (STM32) | 10,000 cycles | Per sector (varies 16KB-128KB) |
| External NOR (SPI) | 100,000 cycles | Per sector (4KB typical) |
| External NAND | 1,000-100,000 | Requires wear leveling |

## nRF53 Multi-Image Forensics

The nRF5340 runs two separate images (app core + network core). Both must be analyzed:

```bash
# App core image (slot 0)
# Typically at 0x00010000 (after MCUboot)
J-Link> savebin app_slot0.bin 0x00010000 0x70000

# Network core image
# Typically at 0x01000000 (network core flash base)
J-Link> savebin net_image.bin 0x01000000 0x40000

# Check both for valid MCUboot headers
xxd -l 32 app_slot0.bin
xxd -l 32 net_image.bin
```

## Image Signature Verification

```bash
# Using imgtool (MCUboot tool)
# Verify image signature
imgtool verify -k <key_file> build/zephyr/zephyr.signed.bin

# Dump image info
imgtool info build/zephyr/zephyr.signed.bin

# Compare image hash
imgtool hash build/zephyr/zephyr.signed.bin
```
