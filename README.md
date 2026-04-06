# local-ai-stack

**A six-phase production AI system built entirely on open-source models running locally on Apple Silicon. No cloud APIs. No managed services. Every architectural decision documented.**

> Phase 1 of 6 — Complete

---

## What This Is

This repository is a single evolving codebase that grows from a terminal-based document Q&A tool into a production-grade AI system with hybrid retrieval, citation enforcement, a CI quality gate, full observability, fine-tuned models, and a real-time voice interface.

Each phase extends the previous one. Nothing gets thrown away.

---

## What It Does (Phase 1)

- Loads `.txt` and `.md` documents from a local folder
- Splits documents into overlapping chunks for context-aware retrieval
- Scores and ranks chunks against a user question using keyword matching
- Assembles a grounded prompt with system instructions and retrieved context
- Sends the prompt to Gemma 4 26B running locally via Ollama
- Returns an answer grounded in your documents — not the model's training data

---

## Architecture

```
User Question
      │
      ▼
loader.py ──► chunker.py ──► retriever.py ──► prompt.py ──► llm.py ──► Answer
  (load)        (split)        (rank)          (assemble)    (generate)
```

**loader.py** — reads `.txt` and `.md` files from the `docs/` folder, returns raw text per file.

**chunker.py** — splits each document into overlapping fixed-size chunks (default 500 chars, 100 overlap) to preserve context at boundaries.

**retriever.py** — scores every chunk against the user's question using keyword frequency, filters stop words, and returns the top K most relevant chunks.

**prompt.py** — assembles a three-part prompt: system instruction + labelled context chunks + user question.

**llm.py** — sends the prompt to Gemma 4 26B via the Ollama local API and returns the model's response.

**main.py** — entry point. Loads and chunks documents once at startup, then runs a multi-turn Q&A loop until the user types `quit`.

---

## Project Structure

```
local-ai-stack/
├── docs/                  # Source documents (.txt and .md)
├── src/
│   ├── loader.py          # File reader — returns raw text per document
│   ├── chunker.py         # Overlap chunker — splits text into chunks
│   ├── retriever.py       # Keyword scorer — finds relevant chunks
│   ├── prompt.py          # Prompt assembler — system + context + question
│   ├── llm.py             # Ollama API client — calls Gemma 4 26B
│   └── main.py            # Entry point — runs the Q&A loop
├── .env                   # Config: model name, chunk size, docs dir
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Stack

| Component | Tool | Notes |
|-----------|------|-------|
| Language | Python 3.12 | via pyenv |
| Model runtime | Ollama | Local inference — no cloud |
| Primary model | Gemma 4 26B | `gemma4:26b` |
| HTTP client | requests | Ollama API calls |
| Config | python-dotenv | `.env` file management |

---

## Hardware

Apple M1 Max · 64 GB Unified Memory · macOS

All models run locally. Metal GPU acceleration via Ollama — no configuration needed. Gemma 4 26B runs at ~20–35 tokens/sec on this hardware.

---

## Setup

**Prerequisites:** Ollama installed and running. Python 3.12 via pyenv.

```bash
# 1. Clone the repo
git clone https://github.com/SavyOnAI/local-ai-stack.git
cd local-ai-stack

# 2. Pull the model
ollama pull gemma4:26b

# 3. Create and activate virtual environment
python -m venv venv
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Add your documents to docs/
# (.txt and .md files only in Phase 1)

# 6. Run
python src/main.py
```

---

## Configuration

All config lives in `.env` — never hardcoded.

| Variable | Default | Description |
|----------|---------|-------------|
| `MODEL_NAME` | `gemma4:26b` | Ollama model string |
| `CHUNK_SIZE` | `500` | Characters per chunk |
| `CHUNK_OVERLAP` | `100` | Characters repeated between chunks |
| `DOCS_DIR` | `docs` | Folder containing source documents |
| `TOP_K` | `5` | Number of chunks retrieved per query |

---

## Example

```
=== Local RAG Pipeline ===
Type your question and press Enter. Type 'quit' to exit.

Loading documents...
Loaded: ai_rag_notes.md (2489 characters)
Loaded: art_of_war.txt (312936 characters)
Ready — 790 chunks loaded.

You: What does Sun Tzu say about laying plans?

Gemma: According to art_of_war.txt [2], Sun Tzu states that the art of war
is governed by five constant factors — the Moral Law, Heaven, Earth,
the Commander, and Method and Discipline. Laying plans involves
weighing these factors to determine conditions in the field.
```

---

## Known Limitations (Phase 1)

- `.txt` and `.md` files only — no PDF, DOCX, or other formats
- Keyword-only retrieval — misses synonyms and semantic meaning
- No vector database — chunks are not persisted between sessions
- No evaluation pipeline — no way to measure answer quality
- Single machine, terminal interface only

All of these are addressed in Phase 2.

---

## Roadmap

| Phase | Name | Status |
|-------|------|--------|
| 1 | Local RAG Pipeline | ✅ Complete |
| 2 | Production RAG Application | 🔄 Planned |
| 3 | Local SLM Benchmarking | ⬜ Planned |
| 4 | Monitoring & Observability | ⬜ Planned |
| 5 | Fine-Tuning with LoRA & DPO | ⬜ Planned |
| 6 | Real-Time Multimodal Application | ⬜ Planned |

---

## Architectural Decisions

Every significant decision — tool selection, model choice, retrieval strategy — is documented with alternatives considered and reasons chosen in [`DECISIONS.md`](DECISIONS.md).

---

*github.com/SavyOnAI/local-ai-stack · Python · Ollama · Apple Silicon · 2026*