"""API key generation, hashing, and validation."""

import hashlib
import hmac
import secrets

LIVE_PREFIX = "ck_live_"
TEST_PREFIX = "ck_test_"


def _hash_key(raw_key: str) -> str:
    """Create a SHA-256 hash of an API key for storage."""
    return hashlib.sha256(raw_key.encode()).hexdigest()


def generate_api_key(is_test: bool = False) -> tuple[str, str, str]:
    """Generate a new API key.

    Returns a tuple of (raw_key, key_prefix_display, key_hash).
    The raw_key is shown to the user exactly once.
    """
    prefix = TEST_PREFIX if is_test else LIVE_PREFIX
    random_part = secrets.token_urlsafe(32)
    raw_key = f"{prefix}{random_part}"
    prefix_display = raw_key[:16]
    hashed = _hash_key(raw_key)
    return raw_key, prefix_display, hashed


def verify_api_key(raw_key: str, key_hash: str) -> bool:
    """Verify a raw API key against its stored hash."""
    return hmac.compare_digest(_hash_key(raw_key), key_hash)
