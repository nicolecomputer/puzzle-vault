"""Authentication utilities for password hashing and verification."""
from typing import cast
from passlib.hash import pbkdf2_sha256


def hash_password(password: str) -> str:
    """
    Hash a password using pbkdf2_sha256.

    Args:
        password: Plain text password to hash

    Returns:
        Hashed password string
    """
    return cast(str, pbkdf2_sha256.hash(password))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against

    Returns:
        True if password matches, False otherwise
    """
    return cast(bool, pbkdf2_sha256.verify(plain_password, hashed_password))
