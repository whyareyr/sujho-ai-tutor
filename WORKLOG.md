# Worklog — building with an AI assistant

This project was built pair-programming with an AI coding assistant. The honest
meta-lesson is that the assistant was excellent at producing a _plausible first
draft_ and unreliable at producing a _correct_ one — almost every stage shipped a
confident suggestion that broke on contact with the real NCERT PDFs or the real
OpenAI account. The value came from treating each AI suggestion as a hypothesis to
verify, not an answer to accept: read the raw output, reproduce the bug, test the
layer, then keep or replace the suggestion.

What follows is where that mattered.

---

### 1. The download URL the AI invented didn't exist

**First pass:** fetch each book as a single "complete book" zip from a predictable
NCERT URL (`.../<code>dd.zip`).
**Why it was wrong:** that route is unreliable/dead, and on a filtered network it
failed at the TLS handshake — so "download the books" produced zero files. An AI
will happily generate a clean URL scheme it has never verified.
**Fix:** switch to downloading chapter PDFs directly (`<code>01.pdf`, `02.pdf`, …)
and **probe until the first 404**, which also auto-discovers each book's chapter
count and survives NCERT re-numbering. Verifying the URL against a live request,
not the model's confidence, drove the change.

### 2. Naive text extraction silently corrupted the extracted text, and AI's first suggestion was also wrong

**First pass:** `page.get_text()`. Looks fine.
**Why it was wrong:** NCERT's PDFs omit space glyphs, so words came out glued,
`universalrelation`, `worldfor`, `elementof`. Embedding that produces confident
answers from corrupted text, and nothing crashes to warn you. This is the most
dangerous class of AI error: it _looks_ like it works.
**How we caught it:** actually reading the extracted page instead of trusting it.
**The instructive part:** the first repair the AI proposed — re-join words in
"words" mode — _did not work_; re-running showed the glue was still there. The
real cause was missing space characters, which no regex can recover (you can't
know `worldfor` splits as `world|for`). We reproduced the bug on a synthetic PDF,
then fixed it with **character-gap geometry**: insert a space when the horizontal
gap between glyphs exceeds a fraction of the font size. One threshold
(`CHAR_GAP_RATIO = 0.10`), tuned on a real page.

### 3. Math characters came through as invisible junk

**First pass:** assume the cleaned text is done.
**Why it was wrong:** NCERT's math font emits glyphs into the Unicode private-use
area — `×` became `\uf0b4`, and stretchy-bracket pieces became thousands of
meaningless codepoints (9,287 across the corpus). On Windows this even crashed
the writer (`cp1252` can't encode them), which — usefully — surfaced the problem
instead of hiding it.
**Fix:** profile the private-use codepoints before touching them. They split into
two families: recoverable operators (`+ - = ×`), which we map back, and
stretchy-bracket/arrow extenders, which we strip. Measuring first stopped us from
either ignoring the junk or over-building a math-reconstruction pipeline. Final
corpus: zero private-use characters.

### 4. Retrieval that the model quietly ignored

**First pass:** retrieve chunks, pass them to GPT, done.
**Why it was wrong:** without an explicit "answer only from these excerpts"
instruction, GPT answers from its own training and never really uses the books,
the entire retrieval layer becomes decorative while the demo still looks great.
This is exactly the failure a reviewer probes with "how do you know it's using the
books?"
**Fix:** a strict grounding instruction, plus an out-of-scope refusal driven by a
similarity threshold **measured from data** (in-scope questions scored ~0.6,
off-topic ~0.16, so the threshold sits at 0.35 in the gap between them) - not a
number that AI guessed. Below the threshold the LLM is never called at all.

### 5. The reflex to add a vector database

**First pass:** "RAG needs a vector DB / a framework like LangChain."
**Why it was wrong here:** with ~2,300 chunks, brute-force cosine over a NumPy
matrix is sub-millisecond. A DB or framework would add dependencies and hide the
mechanics - the opposite of what the design guidelines ask for.
**Fix:** keep the index as two files (`chunks.jsonl` + `embeddings.npy`) and do
the search in a few lines of NumPy. Resisting the AI's default toward heavier
tooling was itself a design decision.

### 6. The eval reported a better score than was real

**First pass:** a scored eval run that looked good, the refusal case "passed."
**Why it was wrong:** the out-of-scope cases hadn't actually been tagged, so the
cricket question was graded on in-scope axes and scored high _without ever testing
the refusal path_. The summary was flattering and misleading.
**How we caught it:** reading the output critically, the summary had no
`refusal_rate` and only 8 of 10 cases ran. Fixed the tags, and the refusal path
was then genuinely exercised (and passed, including the harder "first president
of India" probe, a real factual question that is simply not PCM). An eval you
don't read can lie to you.

### 7. The server that couldn't start without a secret

**First pass:** create the OpenAI client in the agent's constructor (as the
starter did).
**Why it was wrong:** the client is built at import, so the whole service,
including `/health`, crashes without an API key. A health check shouldn't depend
on a paid secret.
**Fix:** lazy-initialize the client on first use, so the app boots and is
health-checkable without credentials.

---

## Key design decisions (summary)

- NumPy brute-force cosine over two files instead of a vector database (scale
  doesn't justify one; flip point ~10⁵ vectors).
- Local embeddings (all-MiniLM) for retrieval, hosted GPT-4o for generation:
  the local model _finds_, the LLM _explains_.
- Refusal threshold 0.35, measured from the score gap between in-scope (~0.6)
  and out-of-scope (~0.16) queries; refusals short-circuit before the LLM.
- Strict grounding prompt: answer only from excerpts, state gaps, never backfill
  from the model's own knowledge.
- Per-page chunks (1200 chars, 200 overlap) with book/chapter/page metadata, so
  every claim is citable to an exact page.
- Eval weights by product harm: groundedness 0.65 > citations 0.20 > pedagogy
  0.15; out-of-scope cases scored on refusal alone.

## What the AI was genuinely good at

Balance matters: the assistant accelerated the parts where a plausible draft _is_
most of the work, FastAPI wiring, pydantic models, the chunking loop, the
NumPy retrieval math, the eval scaffolding, and boilerplate PowerShell/venv
fixes. It also proposed the right _structure_ quickly (retrieve → refuse → ground;
per-case-type eval rubric). Where it fell down was anything requiring contact with
reality it couldn't see: the real PDFs, the real account, the real network.

## The through-line

Every real fix in this project came from **looking at the actual output** - raw
extracted text, a codepoint histogram, an eval summary, a model list - rather than
from the AI's confidence. The assistant made the work faster; verification made it
correct.
