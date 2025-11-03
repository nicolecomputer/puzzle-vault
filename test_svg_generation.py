"""Test script to generate SVG preview for existing puzzle."""

from pathlib import Path

from src.importer.image_utils import generate_preview_image

# Test with the existing puzzle
puz_file = Path("data/puzzles/usa/puzzles/2025-11-02.puz")
output_file = Path("data/puzzles/usa/puzzles/2025-11-02.preview.svg")

if puz_file.exists():
    print(f"Generating SVG preview for {puz_file}...")
    generate_preview_image(puz_file, output_file)
    print(f"✓ Generated: {output_file}")

    # Check file size
    if output_file.exists():
        svg_size = output_file.stat().st_size
        print(f"  SVG size: {svg_size:,} bytes")

        # Compare to old PNG if it exists
        png_file = output_file.parent / output_file.name.replace(".svg", ".png")
        if png_file.exists():
            png_size = png_file.stat().st_size
            print(f"  PNG size: {png_size:,} bytes")
            print(f"  Savings: {((png_size - svg_size) / png_size * 100):.1f}%")

        # Show first few lines of SVG
        print("\nSVG preview (first 10 lines):")
        with open(output_file) as f:
            for i, line in enumerate(f):
                if i >= 10:
                    break
                print(f"  {line.rstrip()}")
else:
    print(f"❌ Puzzle file not found: {puz_file}")
