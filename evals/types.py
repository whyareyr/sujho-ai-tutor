from typing import Literal, Optional

from pydantic import BaseModel

CaseKind = Literal["in_scope", "out_of_scope"]


class EvalCase(BaseModel):
    id: str
    prompt: str
    kind: CaseKind = "in_scope"


class Judgement(BaseModel):
    groundedness: Optional[float] = None
    citations: Optional[float] = None
    pedagogy: Optional[float] = None
    refusal: Optional[float] = None
    score: float
    rationale: str

class EvalResult(BaseModel):
    id: str
    kind: CaseKind
    answer: str
    model: str
    sources: list[str]
    judgement: Judgement