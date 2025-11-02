"""Utilities for source management."""


def normalize_short_code(short_code: str | None) -> str | None:
    """Normalize a short code by stripping whitespace.

    Args:
        short_code: The short code to normalize

    Returns:
        Normalized short code or None if empty
    """
    if not short_code:
        return None

    short_code = short_code.strip()
    return short_code if short_code else None
