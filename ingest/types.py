from pydantic import BaseModel


class Chunk(BaseModel):
    text: str
    subject: str
    book: str
    part: int
    chapter: int
    page: int
    source: str