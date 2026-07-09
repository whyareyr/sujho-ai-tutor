import json
from pathlib import Path

from ingest.constants import (
    CHUNK_CHARS,
    CHUNK_OVERLAP,
    CHUNKS_PATH,
    GENERATED_DIR,
    MANIFEST_PATH,
)

from ingest.parse import chapter_paths, read_pages
from ingest.types import Chunk


def book_index() -> dict[str, dict]:
    manifest = json.loads(MANIFEST_PATH.read_text())
    return {book["ncert_code"]: book for book in manifest["books"]}


def split(text: str) -> list[str]:
    step = CHUNK_CHARS - CHUNK_OVERLAP
    windows = (text[i : i + CHUNK_CHARS] for i in range(0, len(text), step))
    return [window for window in windows if window.strip()]


def chapter_chunks(path: Path, books: dict[str, dict]) -> list[Chunk]:
    code = path.stem[:5]
    chapter = int(path.stem[5:])
    book = books[code]
    return [
        Chunk(
            text=piece,
            subject=book["subject"],
            book=book["book"],
            part=int(code[-1]),
            chapter=chapter,
            page=page_number,
            source=path.stem,
        )
        for page_number, page in enumerate(read_pages(path), start=1)
        for piece in split(page)
    ]


def main() -> None:
    books = book_index()
    chunks = [chunk for path in chapter_paths() for chunk in chapter_chunks(path, books)]
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    CHUNKS_PATH.write_text(
        "\n".join(chunk.model_dump_json() for chunk in chunks), encoding="utf-8"
    )
    print(f"wrote {len(chunks)} chunks to {CHUNKS_PATH}")


if __name__ == "__main__":
    main()