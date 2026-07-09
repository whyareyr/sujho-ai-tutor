from typing import Final

DEFAULT_OPENAI_MODEL: Final[str] = "gpt-4o"

RETRIEVAL_K: Final[int] = 5
# Below this top similarity, the question is treated as out of scope. Chosen from the
# empty band between in-scope (~0.58-0.61) and out-of-scope (~0.16) queries.
SCORE_THRESHOLD: Final[float] = 0.35

REFUSAL_MESSAGE: Final[str] = (
    "I can only help with Class 12 CBSE Mathematics, Physics, and Chemistry from the "
    "NCERT textbooks. That question looks outside those books, so I can't answer it."
)

TUTOR_PROMPT: Final[str] = (
    "You are a patient Class 12 CBSE tutor for Indian students. Answer the student's "
    "question using ONLY the NCERT excerpts below. If the excerpts cover the question "
    "only partly, answer what they support and clearly state what is not covered. Do "
    "not use any outside knowledge. Cite the source after each fact as [Book, Chapter N, "
    "p.X]. Explain step by step in clear, simple language.\n\n"
    "NCERT excerpts:\n{context}"
)