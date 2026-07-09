import json

import httpx

from ingest.constants import MANIFEST_PATH, MAX_CHAPTERS, NCERT_PDF_BASE, RAW_DIR


def book_codes() -> list[str]:
    manifest = json.loads(MANIFEST_PATH.read_text())
    return [book["ncert_code"] for book in manifest["books"]]


def download_chapter(client: httpx.Client, code: str, chapter: int) -> bool:
    """Download one chapter PDF. Return False when the chapter does not exist."""
    name = f"{code}{chapter:02d}.pdf"
    target = RAW_DIR / code / name
    if target.exists():
        print(f"skip {name}")
        return True
    response = client.get(f"{NCERT_PDF_BASE}/{name}", follow_redirects=True, timeout=120.0)
    if response.status_code == 404:
        return False
    response.raise_for_status()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(response.content)
    print(f"ok   {name} ({len(response.content) // 1024} KB)")
    return True


def download_book(client: httpx.Client, code: str) -> None:
    for chapter in range(1, MAX_CHAPTERS + 1):
        if not download_chapter(client, code, chapter):
            print(f"done {code}: {chapter - 1} chapters")
            return


def main() -> None:
    with httpx.Client() as client:
        for code in book_codes():
            download_book(client, code)


if __name__ == "__main__":
    main()