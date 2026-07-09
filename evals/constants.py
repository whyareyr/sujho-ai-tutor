import os
from pathlib import Path
from typing import Final

BASE_URL: Final[str] = os.getenv("EVAL_BASE_URL", "http://localhost:8000")
PROMPTS_PATH: Final[Path] = Path(__file__).with_name("prompts.json")
REPORTS_DIR: Final[Path] = Path(__file__).with_name("reports")

JUDGE_MODEL: Final[str] = os.getenv("JUDGE_MODEL", "gpt-4o")

# In-scope answers are graded on three axes; weights reflect product harm (an
# ungrounded claim misleads a student, a weak citation only inconveniences them).
WEIGHTS: Final[dict[str, float]] = {
    "groundedness": 0.65,
    "citations": 0.20,
    "pedagogy": 0.15,
}