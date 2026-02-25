# TLS/DTLS Security Best Practices

## Certificate Provisioning

### Embedding Certificates at Build Time

**Convert PEM to C header:**

```bash
xxd -i ca_cert.pem > ca_cert.pem.inc
```

**Include in code:**

```c
static const unsigned char ca_cert[] = {
    #include "ca_cert.pem.inc"
};

tls_credential_add(CA_TAG, TLS_CREDENTIAL_CA_CERTIFICATE,
                   ca_cert, sizeof(ca_cert));
```

**Pros:** Simple, no runtime storage needed
**Cons:** Certificate rotation requires firmware update

### Runtime Provisioning via Settings

```c
#include <zephyr/settings/settings.h>

int load_cert_from_settings(void)
{
    uint8_t cert_buf[2048];
    size_t len = sizeof(cert_buf);

    if (settings_load_subtree_direct("certs/ca", cert_buf, &len) == 0) {
        return tls_credential_add(CA_TAG, TLS_CREDENTIAL_CA_CERTIFICATE,
                                  cert_buf, len);
    }
    return -ENOENT;
}

int save_cert_to_settings(const uint8_t *cert, size_t len)
{
    return settings_save_one("certs/ca", cert, len);
}
```

**Kconfig:**

```kconfig
CONFIG_SETTINGS=y
CONFIG_SETTINGS_NVS=y
CONFIG_NVS=y
```

**Pros:** Certificate updates without firmware update
**Cons:** Requires secure provisioning channel

## Security Tag Management

### Tag Organization Strategy

```c
/* Separate tags by purpose */
#define CA_CERTIFICATE_TAG     1
#define CLIENT_CERT_TAG        2
#define AWS_IOT_TAG            3
#define AZURE_IOT_TAG          4
#define PSK_TAG                10

/* Add all credentials for a service */
void provision_aws_iot(void)
{
    tls_credential_add(AWS_IOT_TAG, TLS_CREDENTIAL_CA_CERTIFICATE,
                       aws_ca, sizeof(aws_ca));
    tls_credential_add(AWS_IOT_TAG, TLS_CREDENTIAL_SERVER_CERTIFICATE,
                       client_cert, sizeof(client_cert));
    tls_credential_add(AWS_IOT_TAG, TLS_CREDENTIAL_PRIVATE_KEY,
                       private_key, sizeof(private_key));
}

/* Use tag list for socket */
int sec_tag_list[] = { AWS_IOT_TAG };
setsockopt(sock, SOL_TLS, TLS_SEC_TAG_LIST, sec_tag_list, sizeof(sec_tag_list));
```

**Best practice:** Group related credentials under same tag.

### Multiple Tags for Chain of Trust

```c
/* Separate CA and client auth */
int sec_tag_list[] = { CA_CERTIFICATE_TAG, CLIENT_CERT_TAG };
setsockopt(sock, SOL_TLS, TLS_SEC_TAG_LIST, sec_tag_list, sizeof(sec_tag_list));
```

## PSA Crypto Integration

**Available on:** Cortex-M33+ with TF-M, or PSA Crypto library

### Storing Keys in PSA

```c
#include <psa/crypto.h>

/* Generate and store persistent key */
psa_key_attributes_t attributes = PSA_KEY_ATTRIBUTES_INIT;
psa_set_key_usage_flags(&attributes, PSA_KEY_USAGE_SIGN_HASH);
psa_set_key_algorithm(&attributes, PSA_ALG_RSA_PKCS1V15_SIGN_RAW);
psa_set_key_type(&attributes, PSA_KEY_TYPE_RSA_KEY_PAIR);
psa_set_key_bits(&attributes, 2048);
psa_set_key_lifetime(&attributes,
                     PSA_KEY_LIFETIME_FROM_PERSISTENCE_AND_LOCATION(
                         PSA_KEY_PERSISTENCE_DEFAULT,
                         PSA_KEY_LOCATION_LOCAL_STORAGE));
psa_set_key_id(&attributes, 1);

psa_key_id_t key_id;
psa_generate_key(&attributes, &key_id);
```

### Using PSA Keys with TLS

```c
/* Reference PSA key in TLS credential */
psa_key_id_t key_id = 1;
tls_credential_add(CLIENT_CERT_TAG, TLS_CREDENTIAL_PSA_KEY_ID,
                   &key_id, sizeof(key_id));
```

**Kconfig:**

```kconfig
CONFIG_PSA_CRYPTO_CLIENT=y
CONFIG_MBEDTLS_PSA_CRYPTO_C=y
CONFIG_PSA_WANT_KEY_TYPE_RSA_KEY_PAIR=y
```

## DTLS for CoAP

### PSK-based DTLS

```c
/* Add PSK credentials */
static const char psk[] = "secretkey";
static const char psk_id[] = "Client_identity";

tls_credential_add(PSK_TAG, TLS_CREDENTIAL_PSK, psk, sizeof(psk));
tls_credential_add(PSK_TAG, TLS_CREDENTIAL_PSK_ID, psk_id, sizeof(psk_id));

/* Create DTLS socket */
int sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_DTLS_1_2);

int sec_tag_list[] = { PSK_TAG };
setsockopt(sock, SOL_TLS, TLS_SEC_TAG_LIST, sec_tag_list, sizeof(sec_tag_list));

/* Use as normal UDP socket */
sendto(sock, data, len, 0, (struct sockaddr *)&addr, sizeof(addr));
```

**Kconfig:**

```kconfig
CONFIG_MBEDTLS_KEY_EXCHANGE_PSK_ENABLED=y
CONFIG_MBEDTLS_CIPHER_CCM_ENABLED=y
```

### Certificate-based DTLS

```c
tls_credential_add(DTLS_TAG, TLS_CREDENTIAL_CA_CERTIFICATE, ca, sizeof(ca));
tls_credential_add(DTLS_TAG, TLS_CREDENTIAL_SERVER_CERTIFICATE, cert, sizeof(cert));
tls_credential_add(DTLS_TAG, TLS_CREDENTIAL_PRIVATE_KEY, key, sizeof(key));

int sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_DTLS_1_2);

int sec_tag_list[] = { DTLS_TAG };
setsockopt(sock, SOL_TLS, TLS_SEC_TAG_LIST, sec_tag_list, sizeof(sec_tag_list));

/* Set handshake timeout (DTLS retransmits) */
int timeout_ms = 10000;
setsockopt(sock, SOL_TLS, TLS_DTLS_HANDSHAKE_TIMEO, &timeout_ms, sizeof(timeout_ms));
```

## Session Management

### Session Resumption

**TLS 1.2 session tickets:**

```c
/* Enable session resumption */
CONFIG_MBEDTLS_SSL_SESSION_TICKETS=y
```

Session tickets are handled automatically by mbedTLS. Reduces handshake overhead on reconnection.

### Connection Pooling

```c
/* Reuse TLS connection for multiple requests */
int sock = socket(AF_INET, SOCK_STREAM, IPPROTO_TLS_1_2);
/* ... configure TLS ... */
connect(sock, (struct sockaddr *)&addr, sizeof(addr));

/* Multiple HTTP requests over same connection */
for (int i = 0; i < 10; i++) {
    http_client_req(sock, &req, 5000, NULL);
}

close(sock);
```

### Graceful Closure

```c
/* Proper TLS shutdown before closing socket */
shutdown(sock, SHUT_RDWR);
close(sock);
```

## mbedTLS Configuration

### Memory Optimization

```kconfig
# Reduce buffer sizes for constrained devices
CONFIG_MBEDTLS_SSL_MAX_CONTENT_LEN=4096  # Default 16384
CONFIG_MBEDTLS_MPI_MAX_SIZE=256          # RSA key size in bytes

# Disable unused features
CONFIG_MBEDTLS_KEY_EXCHANGE_DHE_RSA_ENABLED=n
CONFIG_MBEDTLS_KEY_EXCHANGE_ECDHE_ECDSA_ENABLED=n
CONFIG_MBEDTLS_SHA512_C=n
```

### Performance Optimization

```kconfig
# Hardware acceleration (if available)
CONFIG_MBEDTLS_AES_ROM_TABLES=y
CONFIG_MBEDTLS_HAVE_ASM=y

# Enable AES-NI on supported platforms
CONFIG_MBEDTLS_AESNI_C=y
```

### Security Hardening

```kconfig
# Enforce TLS 1.2 minimum
CONFIG_MBEDTLS_TLS_VERSION_1_0=n
CONFIG_MBEDTLS_TLS_VERSION_1_1=n
CONFIG_MBEDTLS_TLS_VERSION_1_2=y
CONFIG_MBEDTLS_TLS_VERSION_1_3=y

# Strong cipher suites only
CONFIG_MBEDTLS_CIPHER_AES_ENABLED=y
CONFIG_MBEDTLS_GCM_C=y
CONFIG_MBEDTLS_CIPHER_MODE_CBC=n  # Prefer GCM over CBC

# Disable weak algorithms
CONFIG_MBEDTLS_MD5_C=n
CONFIG_MBEDTLS_SHA1_C=n  # Use SHA256+ only
```

## Cipher Suite Selection

### Recommended Suites (TLS 1.2)

```kconfig
CONFIG_MBEDTLS_KEY_EXCHANGE_RSA_ENABLED=y
CONFIG_MBEDTLS_KEY_EXCHANGE_ECDHE_RSA_ENABLED=y
CONFIG_MBEDTLS_CIPHER_AES_ENABLED=y
CONFIG_MBEDTLS_GCM_C=y
CONFIG_MBEDTLS_SHA256_C=y
```

**Results in:**
- `TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256`
- `TLS_RSA_WITH_AES_128_GCM_SHA256`

### PSK Suites (for constrained devices)

```kconfig
CONFIG_MBEDTLS_KEY_EXCHANGE_PSK_ENABLED=y
CONFIG_MBEDTLS_CIPHER_CCM_ENABLED=y
```

**Results in:**
- `TLS_PSK_WITH_AES_128_CCM_8`

**Advantage:** No certificate validation overhead.

## Error Handling

### TLS Handshake Failures

```c
int ret = connect(sock, (struct sockaddr *)&addr, sizeof(addr));
if (ret < 0) {
    int err;
    socklen_t len = sizeof(err);
    getsockopt(sock, SOL_SOCKET, SO_ERROR, &err, &len);

    switch (err) {
    case ETIMEDOUT:
        printk("Handshake timeout\n");
        break;
    case ECONNREFUSED:
        printk("Connection refused\n");
        break;
    case EHOSTUNREACH:
        printk("No route to host\n");
        break;
    default:
        printk("TLS error: %d\n", err);
    }
}
```

### Certificate Verification Failures

**Enable detailed logging:**

```kconfig
CONFIG_MBEDTLS_DEBUG=y
CONFIG_MBEDTLS_DEBUG_LEVEL=3
```

**Common causes:**
- Expired certificate
- Untrusted CA
- Hostname mismatch (SNI)
- Revoked certificate

**Debugging:**

```c
int peer_verify = TLS_PEER_VERIFY_OPTIONAL;  /* Log errors but don't fail */
setsockopt(sock, SOL_TLS, TLS_PEER_VERIFY, &peer_verify, sizeof(peer_verify));
```

**Production:** Always use `TLS_PEER_VERIFY_REQUIRED`.

## Power Considerations

### DTLS for Low-Power Devices

**Advantages over TLS:**
- No TCP connection overhead
- Can sleep between messages
- Faster handshake (fewer round trips)

**Trade-offs:**
- Application must handle retransmission
- Less reliable than TCP
- Handshake packets may be lost (requires retry)

### Connection Keep-Alive vs. Reconnection

**Keep-Alive:**
- Pro: No handshake overhead on each send
- Con: Socket consumes power even when idle

**Reconnection:**
- Pro: Can fully sleep between transmissions
- Con: Full handshake on each wake (expensive)

**Recommendation:** Use session resumption for best of both.

```kconfig
CONFIG_MBEDTLS_SSL_SESSION_TICKETS=y
```

Session resumption reduces handshake from 2 RTT to 1 RTT.

## Testing TLS Configuration

### Verify Cipher Suite

```c
int cipher_suite;
socklen_t len = sizeof(cipher_suite);
getsockopt(sock, SOL_TLS, TLS_CIPHERSUITE_LIST, &cipher_suite, &len);
printk("Negotiated cipher: 0x%04X\n", cipher_suite);
```

### Test with OpenSSL Server

```bash
# Start TLS echo server
openssl s_server -accept 8443 -cert server.crt -key server.key -CAfile ca.crt -Verify 1

# Test DTLS server
openssl s_server -accept 8443 -cert server.crt -key server.key -dtls1_2 -listen
```

### Wireshark Analysis

**Decrypt TLS:**
1. Export pre-master secret from mbedTLS (debug build)
2. Configure Wireshark with key log file
3. Analyze cipher suites, handshake timing, alerts

## Best Practices Summary

1. **Always verify peer certificates** in production (`TLS_PEER_VERIFY_REQUIRED`)
2. **Use TLS 1.2 minimum**, prefer TLS 1.3 where available
3. **Provision certificates securely** — never hardcode production keys
4. **Use PSA Crypto** for key storage on supported platforms
5. **Enable session resumption** to reduce reconnection overhead
6. **Prefer DTLS for intermittent** communication from sleeping devices
7. **Test with real CAs** during development, not self-signed certificates
8. **Monitor certificate expiry** and implement OTA update mechanism
9. **Disable weak ciphers** (MD5, SHA1, DES, RC4)
10. **Use hardware crypto** acceleration when available
