"""Request-related utility functions."""

from fastapi import Request


def get_base_url(request: Request) -> str:
    """Get the base URL for the application.

    Automatically detects from the incoming request.
    This ensures URLs work correctly regardless of how the app is deployed.

    Args:
        request: The FastAPI request object

    Returns:
        Base URL string (e.g., "http://localhost:8000" or "https://example.com")
    """
    return f"{request.url.scheme}://{request.url.netloc}"
