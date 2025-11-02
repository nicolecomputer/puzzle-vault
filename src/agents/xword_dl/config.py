"""xword-dl agent configuration."""

from pydantic import BaseModel, Field


class XwordDlConfig(BaseModel):
    """Configuration for the xword-dl agent."""

    outlet_keyword: str = Field(
        default="usa",
        description="The outlet keyword (e.g., 'usa', 'nyt', 'lat'). See xword-dl docs for full list.",
    )
    days_to_fetch: int = Field(
        default=1,
        ge=1,
        le=30,
        description="Number of days to fetch (1-30). Fetches the most recent N days.",
    )
    username: str = Field(
        default="",
        description="Username for outlets that require authentication (optional)",
    )
    password: str = Field(
        default="",
        description="Password for outlets that require authentication (optional)",
    )
