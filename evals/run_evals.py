from dotenv import load_dotenv
load_dotenv("backend/.env")

import json
from datetime import datetime, timezone
from statistics import mean

import httpx

from backend.agent import format_context
from backend.constants import RETRIEVAL_K
from backend.types import ChatResponse
from evals.constants import BASE_URL, PROMPTS_PATH, REPORTS_DIR
from evals.judge import client, judge_in_scope, judge_out_of_scope
from evals.types import EvalCase, EvalResult
from ingest.search import index


def load_cases() -> list[EvalCase]:
    payload = json.loads(PROMPTS_PATH.read_text())
    return [EvalCase.model_validate(case) for case in payload["cases"]]


def run_case(http: httpx.Client, judge, case: EvalCase) -> EvalResult:
    response = http.post("/chat", json={"messages": [{"role": "user", "content": case.prompt}]})
    response.raise_for_status()
    answer = ChatResponse.model_validate(response.json())
    if case.kind == "out_of_scope":
        judgement = judge_out_of_scope(judge, case.prompt, answer.answer)
    else:
        context = format_context(index().search(case.prompt, RETRIEVAL_K))
        judgement = judge_in_scope(judge, case.prompt, answer.answer, context)
    return EvalResult(
        id=case.id, kind=case.kind, answer=answer.answer,
        model=answer.model, sources=answer.sources, judgement=judgement,
    )


def summarize(results: list[EvalResult]) -> dict:
    in_scope = [r for r in results if r.kind == "in_scope"]
    out_scope = [r for r in results if r.kind == "out_of_scope"]
    summary = {"overall": round(mean(r.judgement.score for r in results), 3)}
    if in_scope:
        for axis in ("groundedness", "citations", "pedagogy"):
            summary[axis] = round(mean(getattr(r.judgement, axis) for r in in_scope), 3)
    if out_scope:
        summary["refusal_rate"] = round(mean(r.judgement.refusal for r in out_scope), 3)
    return summary


def main() -> None:
    judge = client()
    with httpx.Client(base_url=BASE_URL, timeout=120.0) as http:
        http.get("/health").raise_for_status()
        results = [run_case(http, judge, case) for case in load_cases()]

    summary = summarize(results)
    REPORTS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_path = REPORTS_DIR / f"scored_eval_{timestamp}.json"
    report_path.write_text(json.dumps(
        {"summary": summary, "results": [r.model_dump() for r in results]}, indent=2
    ))

    print(f"\n{'id':28} {'kind':13} score")
    for result in results:
        print(f"{result.id:28} {result.kind:13} {result.judgement.score:.3f}")
    print(f"\nsummary: {summary}")
    print(f"wrote {report_path}")

if __name__ == "__main__":
    main()