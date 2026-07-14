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

## Function Reference

A quick index of every function in the codebase. Updated as new files are added.

### src/ingestion/
| File | Function | Purpose |
|---|---|---|
| `loader.py` | `find_documents(docs_dir)` | Walk directory, return list of supported file paths |
| `loader.py` | `load_document(file_path)` | Route a single file to its extractor, return text |
| `loader.py` | `load_all_documents(docs_dir)` | Find and extract all documents, return dict of path → text |
| `chunker.py` | `chunk_text(text, chunk_size, overlap)` | Split text into overlapping chunks, return list of strings |
| `chunker.py` | `chunk_document(file_path, text, chunk_size, overlap)` | Chunk text and attach source metadata, return list of dicts |
| `embedder.py` | `embed_text(text, mode)` | Generate embedding vector via nomic-embed-text. mode: "document" or "query" |
| `index_documents.py` | `index_documents(docs_dir, chunk_size, overlap)` | Run full ingestion pipeline: extract → chunk → embed → store |

### src/ingestion/extractors/
| File | Function | Purpose |
|---|---|---|
| `text_extractor.py` | `extract(file_path)` | Extract text from .txt and .md files |
| `pdf_extractor.py` | `extract(file_path)` | Extract text from .pdf files page by page |
| `docx_extractor.py` | `extract(file_path)` | Extract paragraphs and table cells from .docx files |
| `pptx_extractor.py` | `extract(file_path)` | Extract title, body, and notes per slide from .pptx files |
| `csv_extractor.py` | `extract(file_path)` | Convert CSV rows to natural language sentences using header labels |
| `xlsx_extractor.py` | `extract(file_path)` | Convert Excel rows to sentences across all sheets using header labels |
| `html_extractor.py` | `extract(file_path)` | Strip HTML tags and return clean readable text |

### src/retrieval/
| File | Function | Purpose |
|---|---|---|
| `vector_store.py` | `get_collection(persist_dir, collection_name)` | Connect to or create a ChromaDB collection |
| `vector_store.py` | `add_chunks(collection, chunks)` | Store chunks with embeddings in ChromaDB |
| `vector_store.py` | `query_collection(collection, query_vector, n_results)` | Search ChromaDB by vector similarity |
| `bm25_index.py` | `build_bm25_index(chunks)` | Build BM25 keyword index from list of chunk dicts |
| `bm25_index.py` | `save_bm25_index(index, chunks, path)` | Persist BM25 index and chunks to disk |
| `bm25_index.py` | `load_bm25_index(path)` | Load BM25 index and chunks from disk |
| `bm25_index.py` | `query_bm25(...)` | Search BM25 index by keyword |
| `hybrid_retriever.py` | `reciprocal_rank_fusion(...)` | Merge BM25 and vector ranked lists using RRF scoring |
| `hybrid_retriever.py` | `hybrid_retrieve(...)` | Run full hybrid retrieval: BM25 + vector + RRF fusion |
| `reranker.py` | `get_reranker()` | Load the cross-encoder model |
| `reranker.py` | `rerank(...)` | Score and reorder candidate chunks against the query |
| `retriever.py` | `score_chunk(chunk_text, query)` | Score a single chunk against a query |
| `retriever.py` | `retrieve(query, chunks, ...)` | Select top-k chunks for a query |

### src/generation/
| File | Function | Purpose |
|---|---|---|
| `prompt_builder.py` | `format_context(chunks)` | Format retrieved chunks into a context block |
| `prompt_builder.py` | `build_prompt(query, chunks)` | Assemble full prompt: system + context + question |
| `llm.py` | `ask_ollama(prompt)` | Send prompt to Gemma 4 26B via Ollama, return response |

### src/
| File | Function | Purpose |
|---|---|---|
| `main.py` | `initialise()` | Load documents and prepare chunk list for querying |
| `main.py` | `answer_question(query, chunks)` | Run full RAG pipeline for a single question |
| `main.py` | `run()` | Start the terminal Q&A conversation loop |

### ui/
| File | Function | Purpose |
|---|---|---|
| `app.py` | `call_api(question)` | POST a question to the FastAPI `/query` endpoint, return parsed JSON |
| `app.py` | `format_sources(chunk_ids)` | Strip `_chunk_N` suffix and dedupe chunk IDs into unique source filenames |
| `app.py` | `format_response(result)` | Assemble answer + sources + citation warning into one markdown string |
| `app.py` | `chat_fn(message, history)` | Gradio callback — calls the API, handles connection/HTTP errors, returns formatted response |

---

*github.com/SavyOnAI/local-ai-stack · Python · Ollama · Apple Silicon · 2026*