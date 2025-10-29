"""Authentication utilities for password hashing and verification."""
from typing import cast, Callable, Any
from functools import wraps
from fastapi import Request
from fastapi.responses import RedirectResponse
from passlib.hash import pbkdf2_sha256


def require_auth(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to ensure a user is logged in before accessing a route.

    If the user is not logged in (no session), they will be redirected
    to the home page (login page).

    Usage:
        @app.get("/protected-route")
        @require_auth
        async def protected_route(request: Request):
            # Your route logic here
            pass
    """
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Find the Request object in the function arguments
        request = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break

        # Check kwargs as well
        if request is None:
            request = kwargs.get('request')

        # If no request found, something is wrong - call the function anyway
        if request is None:
            return await func(*args, **kwargs)

        # Check if user is logged in
        if not request.session.get("logged_in"):
            return RedirectResponse(url="/", status_code=303)

        # User is authenticated, proceed with the route
        return await func(*args, **kwargs)

    return wrapper


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
