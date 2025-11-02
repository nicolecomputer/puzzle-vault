"""Type definitions for JSON Feed (Puzzlecast) structures."""

from typing import TypedDict


class PuzzleCastAuthor(TypedDict):
    """Author information for a puzzle."""

    name: str


class PuzzleCastAttachment(TypedDict):
    """Attachment information for a puzzle file."""

    url: str
    mime_type: str


class PuzzleCastItem(TypedDict, total=False):
    """A single item in a Puzzlecast feed.

    Required fields: id, url, title, content_text, attachments
    Optional fields: authors, date_published
    """

    id: str
    url: str
    title: str
    content_text: str
    authors: list[PuzzleCastAuthor]
    date_published: str
    attachments: list[PuzzleCastAttachment]


class PuzzleCastFeed(TypedDict, total=False):
    """A complete Puzzlecast JSON feed.

    Required fields: version, title, home_page_url, feed_url, description, items
    Optional fields: icon, next_url
    """

    version: str
    title: str
    home_page_url: str
    feed_url: str
    description: str
    icon: str
    next_url: str
    items: list[PuzzleCastItem]
