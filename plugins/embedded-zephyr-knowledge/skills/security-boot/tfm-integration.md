# TF-M Integration Reference

## TF-M Overview

**Trusted Firmware-M:** Secure execution environment for ARM Cortex-M33+ with TrustZone.

**Provides:**
- Secure boot verification
- PSA Crypto services
- Secure storage
- Attestation
- Firmware update

**Supported platforms:** nRF9160, nRF5340, STM32L5, STM32U5, LPC55S69, MUSCA-B1

## Enabling TF-M in Sysbuild

```kconfig
# sysbuild.conf
SB_CONFIG_BOOTLOADER_MCUBOOT=y
SB_CONFIG_BUILD_WITH_TFM=y
```

```kconfig
# prj.conf (non-secure application)
CONFIG_BUILD_WITH_TFM=y
CONFIG_TFM_BOARD="nordic_nrf/nrf9160dk_nrf9160/ns"
```

**Board suffix:** `ns` = non-secure

## Boot Sequence

1. **MCUboot** boots and verifies TF-M image
2. **TF-M secure partition** initializes
3. **MCUboot** verifies NS application image
4. **NS application** boots, can call TF-M via PSA APIs

## PSA Crypto API

### Initialization

```c
#include <psa/crypto.h>

psa_status_t status = psa_crypto_init();
if (status != PSA_SUCCESS) {
    LOG_ERR("PSA Crypto init failed: %d", status);
    return -1;
}
```

### Random Number Generation

```c
uint8_t random[16];
psa_status_t status = psa_generate_random(random, sizeof(random));
```

### Hashing

```c
psa_hash_operation_t op = PSA_HASH_OPERATION_INIT;
uint8_t hash[32];
size_t hash_len;

psa_hash_setup(&op, PSA_ALG_SHA_256);
psa_hash_update(&op, data, data_len);
psa_hash_finish(&op, hash, sizeof(hash), &hash_len);
```

### Symmetric Encryption (AES-GCM)

```c
/* Generate key */
psa_key_attributes_t attributes = PSA_KEY_ATTRIBUTES_INIT;
psa_set_key_usage_flags(&attributes, PSA_KEY_USAGE_ENCRYPT | PSA_KEY_USAGE_DECRYPT);
psa_set_key_algorithm(&attributes, PSA_ALG_GCM);
psa_set_key_type(&attributes, PSA_KEY_TYPE_AES);
psa_set_key_bits(&attributes, 128);

psa_key_id_t key_id;
psa_generate_key(&attributes, &key_id);

/* Encrypt */
uint8_t ciphertext[128];
size_t ciphertext_len;
uint8_t nonce[12] = {...};

psa_aead_encrypt(key_id, PSA_ALG_GCM,
                 nonce, sizeof(nonce),
                 additional_data, additional_data_len,
                 plaintext, plaintext_len,
                 ciphertext, sizeof(ciphertext), &ciphertext_len);

/* Decrypt */
uint8_t decrypted[128];
size_t decrypted_len;

psa_aead_decrypt(key_id, PSA_ALG_GCM,
                 nonce, sizeof(nonce),
                 additional_data, additional_data_len,
                 ciphertext, ciphertext_len,
                 decrypted, sizeof(decrypted), &decrypted_len);

/* Destroy key when done */
psa_destroy_key(key_id);
```

### Persistent Keys

```c
psa_key_attributes_t attributes = PSA_KEY_ATTRIBUTES_INIT;
psa_set_key_usage_flags(&attributes, PSA_KEY_USAGE_ENCRYPT | PSA_KEY_USAGE_DECRYPT);
psa_set_key_algorithm(&attributes, PSA_ALG_GCM);
psa_set_key_type(&attributes, PSA_KEY_TYPE_AES);
psa_set_key_bits(&attributes, 128);

/* Make key persistent */
psa_set_key_lifetime(&attributes,
                     PSA_KEY_LIFETIME_FROM_PERSISTENCE_AND_LOCATION(
                         PSA_KEY_PERSISTENCE_DEFAULT,
                         PSA_KEY_LOCATION_LOCAL_STORAGE));
psa_set_key_id(&attributes, 1);  /* Unique key ID */

psa_key_id_t key_id;
psa_generate_key(&attributes, &key_id);

/* Key survives reboot, retrieve later by ID */
psa_key_id_t retrieved_id = 1;
/* Use retrieved_id for crypto operations */
```

### Signing and Verification (ECDSA)

```c
/* Generate ECDSA key pair */
psa_key_attributes_t attributes = PSA_KEY_ATTRIBUTES_INIT;
psa_set_key_usage_flags(&attributes, PSA_KEY_USAGE_SIGN_HASH | PSA_KEY_USAGE_VERIFY_HASH);
psa_set_key_algorithm(&attributes, PSA_ALG_ECDSA(PSA_ALG_SHA_256));
psa_set_key_type(&attributes, PSA_KEY_TYPE_ECC_KEY_PAIR(PSA_ECC_FAMILY_SECP_R1));
psa_set_key_bits(&attributes, 256);

psa_key_id_t key_id;
psa_generate_key(&attributes, &key_id);

/* Sign hash */
uint8_t hash[32] = {...};
uint8_t signature[64];
size_t signature_len;

psa_sign_hash(key_id, PSA_ALG_ECDSA(PSA_ALG_SHA_256),
              hash, sizeof(hash),
              signature, sizeof(signature), &signature_len);

/* Verify signature */
psa_status_t status = psa_verify_hash(key_id, PSA_ALG_ECDSA(PSA_ALG_SHA_256),
                                      hash, sizeof(hash),
                                      signature, signature_len);
if (status == PSA_SUCCESS) {
    /* Signature valid */
}
```

## PSA Internal Trusted Storage (ITS)

```c
#include <psa/internal_trusted_storage.h>

/* Write data */
const uint8_t data[] = "secret data";
psa_storage_uid_t uid = 1;
psa_status_t status = psa_its_set(uid, sizeof(data), data, PSA_STORAGE_FLAG_NONE);

/* Read data */
uint8_t buffer[32];
size_t data_len;
status = psa_its_get(uid, 0, sizeof(buffer), buffer, &data_len);

/* Remove data */
status = psa_its_remove(uid);

/* Get info */
struct psa_storage_info_t info;
status = psa_its_get_info(uid, &info);
/* info.size, info.flags */
```

**Kconfig:**

```kconfig
CONFIG_TFM_ITS_NUM_ASSETS=10
```

## PSA Protected Storage (PS)

Similar to ITS but may use external flash.

```c
#include <psa/protected_storage.h>

psa_status_t status = psa_ps_set(uid, data_len, data, PSA_STORAGE_FLAG_NONE);
status = psa_ps_get(uid, 0, buffer_size, buffer, &data_len);
status = psa_ps_remove(uid);
```

**Difference from ITS:**
- ITS: Internal flash, fast, limited size
- PS: May use external flash, larger capacity

## Isolation Levels

```kconfig
# Level 1: No isolation within secure partition
CONFIG_TFM_ISOLATION_LEVEL=1

# Level 2: PSA-defined isolation
CONFIG_TFM_ISOLATION_LEVEL=2

# Level 3: Maximum isolation (performance impact)
CONFIG_TFM_ISOLATION_LEVEL=3
```

**Recommendation:** Level 2 for production.

## Non-Secure Application Configuration

### Memory Partitioning

TF-M requires specific memory layout:

```dts
&flash0 {
    partitions {
        /* MCUboot */
        boot_partition: partition@0 {
            label = "mcuboot";
            reg = <0x0 0x10000>;
        };
        /* TF-M secure image */
        tfm_partition: partition@10000 {
            label = "tfm";
            reg = <0x10000 0x40000>;
        };
        /* Non-secure application */
        slot0_partition: partition@50000 {
            label = "image-0";
            reg = <0x50000 0x30000>;
        };
        /* Secondary slot */
        slot1_partition: partition@80000 {
            label = "image-1";
            reg = <0x80000 0x30000>;
        };
    };
};
```

### Build Artifacts

**After build:**

```
build/
├── mcuboot/zephyr/zephyr.bin      # MCUboot bootloader
├── tfm/bin/tfm_s.bin               # TF-M secure firmware
└── zephyr/zephyr.bin               # NS application
```

### Flashing

**Flash all images:**

```bash
west flash --hex-file build/zephyr/merged.hex
```

**Or individually:**

```bash
nrfjprog --program build/mcuboot/zephyr/zephyr.hex --chiperase
nrfjprog --program build/tfm/bin/tfm_s.hex
nrfjprog --program build/zephyr/zephyr.hex
nrfjprog --reset
```

## Kconfig Options

```kconfig
# Enable TF-M
CONFIG_BUILD_WITH_TFM=y

# Board configuration (REQUIRED)
CONFIG_TFM_BOARD="nordic_nrf/nrf9160dk_nrf9160/ns"

# PSA APIs
CONFIG_PSA_CRYPTO_CLIENT=y
CONFIG_TFM_ITS=y
CONFIG_TFM_PS=y

# mbedTLS integration with PSA
CONFIG_MBEDTLS_PSA_CRYPTO_C=y
CONFIG_MBEDTLS_USE_PSA_CRYPTO=y

# PSA algorithms
CONFIG_PSA_WANT_ALG_SHA_256=y
CONFIG_PSA_WANT_ALG_GCM=y
CONFIG_PSA_WANT_ALG_ECDSA=y
CONFIG_PSA_WANT_ECC_SECP_R1_256=y
```

## Common Issues

**Build error: "TFM_BOARD not set"**
- Fix: Add `CONFIG_TFM_BOARD="..."` to prj.conf

**Runtime error: "PSA API call failed"**
- Cause: TF-M not initialized or wrong isolation level
- Fix: Verify TF-M image flashed, check isolation level

**Linker error: "region overflowed"**
- Cause: Application too large for NS region
- Fix: Increase NS partition size in DTS, reduce TF-M partition

**Flash error: "TF-M image not found"**
- Cause: TF-M image not built
- Fix: Verify sysbuild config, rebuild with `--sysbuild`
