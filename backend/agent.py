import os
from typing import Optional

from openai import OpenAI

from backend.constants import (
    DEFAULT_OPENAI_MODEL,
    REFUSAL_MESSAGE,
    RETRIEVAL_K,
    SCORE_THRESHOLD,
    TUTOR_PROMPT,
)
from backend.inputs import message_items
from backend.types import ChatRequest, ChatResponse
from ingest.search import index
from ingest.types import Chunk


def label(chunk: Chunk) -> str:
    return f"{chunk.book}, Chapter {chunk.chapter}, p.{chunk.page}"


def format_context(hits: list[tuple[Chunk, float]]) -> str:
    return "\n\n".join(f"[{label(chunk)}]\n{chunk.text}" for chunk, _ in hits)


def citation_labels(hits: list[tuple[Chunk, float]]) -> list[str]:
    seen: list[str] = []
    for chunk, _ in hits:
        if label(chunk) not in seen:
            seen.append(label(chunk))
    return seen


class TutorAgent:
    """Grounded NCERT tutor: retrieve, refuse if out of scope, else answer from chunks."""

    def __init__(self) -> None:
        self.model = os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)
        self._client: Optional[OpenAI] = None

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        return self._client

    def answer(self, request: ChatRequest) -> ChatResponse:
        query = request.messages[-1].content
        hits = index().search(query, RETRIEVAL_K)
        if not hits or hits[0][1] < SCORE_THRESHOLD:
            return ChatResponse(answer=REFUSAL_MESSAGE, model=self.model, sources=[])

        response = self.client.responses.create(
            model=self.model,
            instructions=TUTOR_PROMPT.format(context=format_context(hits)),
            input=message_items(request.messages),
        )
        return ChatResponse(
            answer=response.output_text.strip(),
            model=self.model,
            sources=citation_labels(hits),
        )