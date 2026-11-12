"""Password hashing and constant-time verification helpers."""

import hashlib
import hmac
import os


def hash_password(password: str) -> str:
    """Hash a password using salted scrypt."""
    salt = os.urandom(16)
    derived = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1)
    return f"scrypt${salt.hex()}${derived.hex()}"


def verify_password(password: str, stored_value: str) -> tuple[bool, bool]:
    """Verify a password against stored scrypt, legacy SHA-256, or legacy plaintext.

    Returns:
        tuple[bool, bool]: (is_valid, needs_rehash)
    """
    if not stored_value:
        return False, False

    if stored_value.startswith("scrypt$"):
        parts = stored_value.split("$")
        if len(parts) != 3:
            return False, False
        try:
            salt = bytes.fromhex(parts[1])
            expected = bytes.fromhex(parts[2])
        except ValueError:
            return False, False
        derived = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1)
        return hmac.compare_digest(derived, expected), False

    # Legacy unsalted SHA-256 hex digest (64 hex chars)
    if len(stored_value) == 64 and all(c in "0123456789abcdefABCDEF" for c in stored_value):
        legacy_sha = hashlib.sha256(password.encode("utf-8")).hexdigest()
        is_valid = hmac.compare_digest(legacy_sha, stored_value.lower())
        return is_valid, is_valid

    # Legacy plaintext password row (transparently rehashed on successful login)
    is_valid = hmac.compare_digest(password, stored_value)
    return is_valid, is_valid
