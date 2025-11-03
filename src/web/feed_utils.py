"""Utilities for building JSON feeds and managing feed data."""

from src.shared.models.puzzle import Puzzle
from src.shared.models.source import Source
from src.web.feed_types import PuzzleCastFeed, PuzzleCastItem
from src.web.pagination_utils import paginate


def sort_puzzles_by_date(puzzles: list[Puzzle]) -> list[Puzzle]:
    """Sort puzzles by date, most recent first.

    Puzzles without dates are sorted by creation date.

    Args:
        puzzles: List of puzzles to sort

    Returns:
        Sorted list of puzzles
    """
    return sorted(
        puzzles,
        key=lambda p: p.puzzle_date if p.puzzle_date else p.created_at,
        reverse=True,
    )


def paginate_items(
    items: list[Puzzle], page: int, per_page: int = 50
) -> tuple[list[Puzzle], int, int]:
    """Paginate a list of puzzles.

    Args:
        items: List of puzzles to paginate
        page: Current page number (1-indexed)
        per_page: Number of items per page

    Returns:
        Tuple of (paginated_items, total_pages, validated_page)
    """
    return paginate(items, page, per_page)


def build_puzzle_content_text(puzzle: Puzzle) -> str:
    """Build content text for a puzzle item.

    Args:
        puzzle: The puzzle to build content for

    Returns:
        Formatted content text
    """
    content_parts = [puzzle.title]
    if puzzle.author:
        content_parts.append(f"By {puzzle.author}")
    if puzzle.puzzle_date:
        content_parts.append(f"Published {puzzle.puzzle_date.strftime('%B %d, %Y')}")
    return " • ".join(content_parts)


def build_feed_item(puzzle: Puzzle, base_url: str, feed_key: str) -> PuzzleCastItem:
    """Build a JSON feed item for a puzzle.

    Args:
        puzzle: The puzzle to build an item for
        base_url: Base URL for constructing absolute URLs
        feed_key: Feed key for authentication

    Returns:
        Dictionary representing the feed item
    """
    item_url = f"{base_url}/puzzles/{puzzle.id}?key={feed_key}"

    item: PuzzleCastItem = {
        "id": item_url,
        "url": item_url,
        "title": puzzle.title,
        "content_text": build_puzzle_content_text(puzzle),
        "attachments": [
            {
                "url": f"{base_url}/puzzles/{puzzle.id}.puz?key={feed_key}",
                "mime_type": "application/x-crossword",
            }
        ],
    }

    if puzzle.author:
        item["authors"] = [{"name": puzzle.author}]

    if puzzle.puzzle_date:
        item["date_published"] = f"{puzzle.puzzle_date.isoformat()}T00:00:00Z"

    if puzzle.has_preview():
        item["image"] = f"{base_url}/puzzles/{puzzle.id}.preview.svg"

    return item


def build_feed_data(
    source: Source,
    puzzles: list[Puzzle],
    base_url: str,
    feed_key: str,
    page: int,
    total_pages: int,
) -> PuzzleCastFeed:
    """Build the complete JSON feed data structure.

    Args:
        source: The source for this feed
        puzzles: List of puzzles for this page
        base_url: Base URL for constructing absolute URLs
        feed_key: Feed key for authentication
        page: Current page number
        total_pages: Total number of pages

    Returns:
        Dictionary representing the complete feed
    """
    feed_identifier = source.short_code if source.short_code else source.id

    feed_data: PuzzleCastFeed = {
        "version": "https://jsonfeed.org/version/1.1",
        "title": source.name,
        "home_page_url": f"{base_url}/sources/{source.id}",
        "feed_url": f"{base_url}/feeds/{feed_identifier}.json?key={feed_key}",
        "description": f"A Puzzlecast feed for source: {source.name}",
        "items": [build_feed_item(puzzle, base_url, feed_key) for puzzle in puzzles],
    }

    icon_url = source.icon_url(base_url)
    if icon_url:
        feed_data["icon"] = icon_url

    if page < total_pages:
        feed_data["next_url"] = (
            f"{base_url}/feeds/{feed_identifier}.json?key={feed_key}&page={page + 1}"
        )

    return feed_data
