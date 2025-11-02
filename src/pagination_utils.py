"""Utilities for pagination."""

from typing import TypeVar

T = TypeVar("T")


def paginate(items: list[T], page: int, per_page: int = 50) -> tuple[list[T], int, int]:
    """Paginate a list of items.

    Args:
        items: List of items to paginate
        page: Current page number (1-indexed)
        per_page: Number of items per page

    Returns:
        Tuple of (paginated_items, total_pages, validated_page)
    """
    total = len(items)
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1

    validated_page = max(1, min(page, total_pages))

    offset = (validated_page - 1) * per_page
    paginated = items[offset : offset + per_page]

    return paginated, total_pages, validated_page
