"""Run with python docs/render_fixture.py (requires Pillow 13.0.0)."""

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

DOCS = Path(__file__).resolve().parent
sys.path.insert(0, str(DOCS.parent))

from fixture.units import frames_to_ms


def render():
    image = Image.new("RGB", (960, 512), "#101c2c")
    draw = ImageDraw.Draw(image)

    def label(x, y, text, size, color):
        draw.text((x, y), text, font=ImageFont.load_default(size=size), fill=color)

    label(44, 35, "PROJECT NATIVE   /   PYTHON FIXTURE", 19, "#78e0d3")
    label(42, 82, "How long do 30 frames last?", 42, "#f1f5f9")
    label(44, 150, "Elapsed milliseconds returned by frames_to_ms(30, fps)", 22, "#c3d4de")

    for index, fps in enumerate((24, 30, 60, 120)):
        ms = frames_to_ms(30, fps)
        y = 226 + index * 52
        label(44, y - 3, f"{fps} fps", 21, "#e1eaf3")
        width = round(ms * 0.48)
        draw.rectangle((155, y, 155 + width, y + 18), fill="#6cdacb")
        label(172 + width, y - 4, f"{ms:,} ms", 20, "#f1f5f9")

    draw.line((44, 446, 916, 446), fill="#446076")
    label(44, 462, "Fixture output  /  Whole milliseconds rounded down", 18, "#afc6d7")
    image.save(DOCS / "frame-timing.png")


if __name__ == "__main__":
    render()
