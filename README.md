# NCERT Class 12 Tutor

A local AI tutor grounded in the Class 12 CBSE NCERT textbooks (Mathematics, Physics, Chemistry). Ask it a syllabus question and it answers **only from the books**, with per-page citations. Ask it anything else and it politely refuses.

## Architecture

```
NCERT PDFs (data/raw/)
    │  ingest/download.py — fetches chapter PDFs from ncert.nic.in per data/manifest.json
    ▼
ingest/parse.py — PyMuPDF "words" extraction (fixes line-wrap glued words),
    │             strips headers/footers ("Reprint 2026-27", running heads, bare page numbers)
    ▼
ingest/chunk.py — one chunk window per page slice (CHUNK_CHARS with CHUNK_OVERLAP),
    │             metadata: subject, book, part, chapter, page, source
    ▼             → data/generated/chunks.jsonl (2294 chunks)
ingest/embed.py — sentence-transformers all-MiniLM-L6-v2, normalized vectors
    │             → data/generated/embeddings.npy (2294 × 384)
    ▼
ingest/search.py — in-memory numpy index, cosine similarity = dot product
    ▼
backend/agent.py — retrieve top-5 → refuse if top score < 0.35 → else answer via
                   OpenAI gpt-4o, instructions restrict it to the retrieved excerpts,
                   citations formatted [Book, Chapter N, p.X]
```

The API is a single `POST /chat` (FastAPI). The frontend (`frontend/index.html`) is a static page served at `/` — chat UI with MathJax rendering for formulas and source chips per answer.

## Setup (fresh clone → working tutor)

```powershell
# 1. Environment
python -m venv backend/.venv
backend\.venv\Scripts\Activate.ps1        # (Linux/macOS: source backend/.venv/bin/activate)
pip install -r backend/requirements.txt

# 2. Secrets
cp backend/.env.example backend/.env       # then set OPENAI_API_KEY inside

# 3. Data pipeline (downloads NCERT PDFs, ~5 min; embedding ~2 min on CPU)
python -m ingest.download
python -m ingest.chunk
python -m ingest.embed

# 4. Run
$env:PYTHONPATH="."; uvicorn backend.main:app --reload --port 8000
# open http://localhost:8000
```

First request loads the embedding model (one-time HuggingFace download, cached afterwards).

## Design decisions & tradeoffs

- **Retrieval-augmented generation over fine-tuning.** The corpus is small and factual; RAG gives exact page citations and needs no training compute. Tradeoff: answers are bounded by retrieval quality.
- **Per-page chunking.** Every citation maps to an exact PDF page. Tradeoff: ideas that span a page break get split — softened with character overlap between chunks.
- **Plain numpy index, no vector DB.** 2294 × 384 floats is ~3.4 MB; a full scan is sub-millisecond. Chroma/FAISS would add a dependency for zero benefit at this scale. Swap-in point is isolated in `ingest/search.py` if the corpus grows.
- **Similarity-threshold refusal (0.35).** Measured an empty band between in-scope top scores (~0.58–0.61) and out-of-scope (~0.16); 0.35 sits safely inside it. Tradeoff: a genuinely in-scope question phrased very unusually could be refused — none observed in evals.
- **Local embeddings + hosted generation.** MiniLM runs free and fast on CPU; generation quality still benefits from a hosted model (default `gpt-4o`, configurable via `OPENAI_MODEL`). Fully-local generation (e.g. Ollama) would be a drop-in change in `backend/agent.py`.
- **Page numbers are PDF page indices** within each chapter file, not the printed textbook page numbers. Consistent and verifiable against the same PDFs the pipeline downloads.

## Limitations

- **Partial-coverage leakage.** When excerpts only partially cover a question (e.g. a specific worked integral), the model can drift into general knowledge despite instructions — visible as the low `partial-fractions` eval score. Mitigations tried: stricter prompt; a full fix likely needs a groundedness post-check.
- **Citation formatting is inconsistent** in some answers (judge score 0.64 on that axis).
- **Retrieval uses only the last user message**; multi-turn follow-ups like "explain that again" retrieve on the follow-up text alone.
- Diagrams, figures, and complex tables in the PDFs are not captured — text only.
- A few glued-word artifacts from PDF extraction may survive in chunks (rare, low-impact).

## Evals

With the backend running:

```powershell
$env:PYTHONPATH="."; python -m evals.run_evals
```

10 visible cases (7 in-scope across M/P/C, 3 out-of-scope), scored by an LLM judge on groundedness, citations, pedagogy, and refusal. Reports land in `evals/reports/`.

Latest run:

| metric       | score |
| ------------ | ----- |
| overall      | 0.863 |
| groundedness | 0.814 |
| citations    | 0.643 |
| pedagogy     | 0.971 |
| refusal rate | 1.000 |

Known weak case: `partial-fractions` (0.12) — see Limitations.
