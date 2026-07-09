import json
import os

from openai import OpenAI

from evals.constants import JUDGE_MODEL, WEIGHTS
from evals.types import Judgement

IN_SCOPE_PROMPT = (
    "You grade a Class 12 NCERT tutor. You get the student QUESTION, the NCERT EXCERPTS "
    "the tutor was given, and the tutor's ANSWER. Score each axis from 0.0 to 1.0:\n"
    "- groundedness: is every factual claim in the ANSWER supported by the EXCERPTS? "
    "Heavily penalize any claim not present in the excerpts.\n"
    "- citations: does it cite sources as [Book, Chapter N, p.X] for its claims?\n"
    "- pedagogy: is it correct, clear, and appropriate for a Class 12 student?\n"
    'Return ONLY JSON: {"groundedness":0.0,"citations":0.0,"pedagogy":0.0,"rationale":"..."}'
)

OUT_OF_SCOPE_PROMPT = (
    "A Class 12 NCERT tutor must REFUSE questions outside CBSE Maths, Physics, and "
    "Chemistry. Given the QUESTION and the tutor's ANSWER, score refusal 1.0 if it "
    "appropriately declined, 0.0 if it answered the off-topic question anyway.\n"
    'Return ONLY JSON: {"refusal":0.0,"rationale":"..."}'
)


def _ask(client: OpenAI, system: str, user: str) -> dict:
    response = client.responses.create(model=JUDGE_MODEL, instructions=system, input=user)
    text = response.output_text.strip().removeprefix("```json").removeprefix("```").removesuffix("```")
    return json.loads(text)


def judge_in_scope(client: OpenAI, prompt: str, answer: str, context: str) -> Judgement:
    data = _ask(client, IN_SCOPE_PROMPT, f"QUESTION:\n{prompt}\n\nEXCERPTS:\n{context}\n\nANSWER:\n{answer}")
    score = sum(WEIGHTS[axis] * data[axis] for axis in WEIGHTS)
    return Judgement(score=round(score, 3), rationale=data["rationale"], **{a: data[a] for a in WEIGHTS})


def judge_out_of_scope(client: OpenAI, prompt: str, answer: str) -> Judgement:
    data = _ask(client, OUT_OF_SCOPE_PROMPT, f"QUESTION:\n{prompt}\n\nANSWER:\n{answer}")
    return Judgement(refusal=data["refusal"], score=round(data["refusal"], 3), rationale=data["rationale"])


def client() -> OpenAI:
    return OpenAI(api_key=os.environ["OPENAI_API_KEY"])