"""Utilities for generating preview images from puzzle files."""

from pathlib import Path

import puz
from PIL import Image, ImageDraw


def generate_preview_image(
    puz_file_path: Path,
    output_path: Path,
    image_size: int = 512,
) -> None:
    """
    Generate an empty grid preview image from a .puz file.

    Args:
        puz_file_path: Path to the .puz file
        output_path: Path where the preview image should be saved
        image_size: Size of the output image in pixels (default: 512, generates 512x512)
    """
    puzzle = puz.read(str(puz_file_path))

    max_dimension = max(puzzle.width, puzzle.height)
    cell_size = image_size // max_dimension

    grid_width = puzzle.width * cell_size
    grid_height = puzzle.height * cell_size

    offset_x = (image_size - grid_width) // 2
    offset_y = (image_size - grid_height) // 2

    img = Image.new("RGB", (image_size, image_size), "white")
    draw = ImageDraw.Draw(img)

    for row in range(puzzle.height):
        for col in range(puzzle.width):
            idx = row * puzzle.width + col
            char = puzzle.solution[idx]

            x1 = offset_x + col * cell_size
            y1 = offset_y + row * cell_size
            x2 = x1 + cell_size
            y2 = y1 + cell_size

            if char == puz.BLACKSQUARE:
                draw.rectangle([x1, y1, x2, y2], fill="black")
            else:
                draw.rectangle([x1, y1, x2, y2], outline="black", fill="white")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)
