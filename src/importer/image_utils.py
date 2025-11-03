"""Utilities for generating preview images from puzzle files."""

from pathlib import Path

import puz  # type: ignore[import]


def generate_preview_image(
    puz_file_path: Path,
    output_path: Path,
    max_size: int = 500,
) -> None:
    """
    Generate an empty grid preview SVG from a .puz file.

    Args:
        puz_file_path: Path to the .puz file
        output_path: Path where the preview SVG should be saved
        max_size: Maximum dimension in pixels (default: 500)
    """
    puzzle = puz.read(str(puz_file_path))

    max_dimension = max(puzzle.width, puzzle.height)
    cell_size = max_size / max_dimension

    svg_width = puzzle.width * cell_size
    svg_height = puzzle.height * cell_size

    # Round to 2 decimal places for cleaner output
    svg_width = round(svg_width, 2)
    svg_height = round(svg_height, 2)
    cell_size = round(cell_size, 2)

    svg_parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_width} {svg_height}" width="{svg_width}" height="{svg_height}">',
        f'<rect width="{svg_width}" height="{svg_height}" fill="white"/>',
    ]

    for row in range(puzzle.height):
        for col in range(puzzle.width):
            idx = row * puzzle.width + col
            char = puzzle.solution[idx]

            x = round(col * cell_size, 2)
            y = round(row * cell_size, 2)

            if char == puz.BLACKSQUARE:
                svg_parts.append(
                    f'<rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" fill="black"/>'
                )
            else:
                svg_parts.append(
                    f'<rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" fill="white" stroke="black" stroke-width="1"/>'
                )

    svg_parts.append("</svg>")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("".join(svg_parts))
