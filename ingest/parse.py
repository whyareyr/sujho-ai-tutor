import re
import sys
from pathlib import Path
from typing import Optional

import fitz  # pymupdf

from ingest.constants import CHAR_GAP_RATIO, RAW_DIR

NOISE_LINE = re.compile(r"^(Reprint \d{4}-\d{2}|MATHEMATICS|PHYSICS|CHEMISTRY|\d{1,3})$")

# NCERT math fonts emit some glyphs into the Unicode private-use area. A few are real
# operators we can recover; the rest are stretchy-bracket / arrow pieces we drop.
SYMBOL_MAP = {"\uf02b": "+", "\uf02d": "-", "\uf03d": "=", "\uf0b4": "\u00d7"}


def normalize(text: str) -> str:
    for junk, real in SYMBOL_MAP.items():
        text = text.replace(junk, real)
    return "".join(" " if 0xE000 <= ord(char) <= 0xF8FF else char for char in text)


def chapter_paths() -> list[Path]:
    """Every NCERT chapter PDF under RAW_DIR, e.g. lemh101.pdf. Skips prelims/appendix/answers."""
    return sorted(
        path
        for path in RAW_DIR.rglob("*.pdf")
        if len(path.stem) == 7 and path.stem[5:].isdigit()
    )


def line_text(line: dict) -> str:
    """Reconstruct a line, inserting a space wherever NCERT dropped the space glyph."""
    chars: list[str] = []
    previous_x1: Optional[float] = None
    for span in line["spans"]:
        for char in span["chars"]:
            x0, _, x1, _ = char["bbox"]
            if previous_x1 is not None and (x0 - previous_x1) > CHAR_GAP_RATIO * span["size"]:
                chars.append(" ")
            chars.append(char["c"])
            previous_x1 = x1
    return re.sub(r"\s+", " ", normalize("".join(chars))).strip()


def page_text(page: fitz.Page) -> str:
    raw = page.get_text("rawdict")
    lines = (
        line_text(line)
        for block in raw["blocks"]
        for line in block.get("lines", [])
    )
    return "\n".join(line for line in lines if line and not NOISE_LINE.match(line))


def read_pages(path: Path) -> list[str]:
    with fitz.open(path) as document:
        return [page_text(page) for page in document]


def inspect(path: str, pages: int = 2) -> None:
    texts = read_pages(Path(path))
    print(f"{path}: {len(texts)} pages\n")
    for number, text in enumerate(texts[:pages], start=1):
        print(f"---------- page {number} ----------")
        print(text)


if __name__ == "__main__":
    inspect(sys.argv[1])