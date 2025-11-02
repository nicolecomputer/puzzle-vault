"""Null agent configuration."""

from pydantic import BaseModel


class NullConfig(BaseModel):
    """Configuration for the null agent (no config needed)."""

    pass
