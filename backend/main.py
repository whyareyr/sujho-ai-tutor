from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse

from backend.agent import TutorAgent
from backend.types import ChatRequest, ChatResponse


load_dotenv(Path(__file__).with_name(".env"))

app = FastAPI(title="NCERT Tutor Assignment")
agent = TutorAgent()

FRONTEND = Path(__file__).parent.parent / "frontend" / "index.html"


@app.get("/")
def home() -> FileResponse:
    return FileResponse(FRONTEND)

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat")
def chat(request: ChatRequest) -> ChatResponse:
    return agent.answer(request)
