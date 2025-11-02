"""Null agent configuration."""

from pydantic import BaseModel, Field


class NullConfig(BaseModel):
    """Configuration for the null agent."""

    extra_string: str = Field(
        default="",
        description="An extra string to display in the logs",
    )
