"""Authentication utilities for password hashing and verification."""

import uuid
from collections.abc import Callable
from functools import wraps
from typing import Any, cast

from fastapi import Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from passlib.hash import pbkdf2_sha256  # type: ignore
from sqlalchemy.orm import Session

from src.shared.database import get_db
from src.shared.models.puzzle import Puzzle
from src.shared.models.source import Source
from src.shared.models.user import User


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
            request = kwargs.get("request")

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


def get_user_from_key(key: str, db: Session = Depends(get_db)) -> User:
    """Dependency to get authenticated user from feed key.

    Args:
        key: The feed key query parameter
        db: Database session

    Returns:
        Authenticated User

    Raises:
        HTTPException: If authentication fails
    """
    try:
        key_uuid = uuid.UUID(key)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid feed key") from None

    user = db.query(User).filter(User.feed_key == key_uuid).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid feed key")

    return user


def user_has_source_access(user: User, source: Source) -> bool:
    """Check if a user has access to a source.

    Args:
        user: The user to check
        source: The source to check access for

    Returns:
        True if user has access, False otherwise
    """
    source_ids = {src.id for src in user.sources}
    return source.id in source_ids


def user_has_puzzle_access(user: User, puzzle: Puzzle) -> bool:
    """Check if a user has access to a puzzle via its source.

    Args:
        user: The user to check
        puzzle: The puzzle to check access for

    Returns:
        True if user has access, False otherwise
    """
    source_ids = {src.id for src in user.sources}
    return puzzle.source_id in source_ids


def get_user_from_session(request: Request, db: Session) -> User:
    """Get authenticated user from session.

    Args:
        request: The request with session data
        db: Database session

    Returns:
        Authenticated User

    Raises:
        HTTPException: If user not found
    """
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


def has_any_users(db: Session) -> bool:
    """Check if any users exist in the database.

    Args:
        db: Database session

    Returns:
        True if at least one user exists, False otherwise
    """
    return db.query(User).first() is not None
