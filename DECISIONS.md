# DECISIONS.md
# AI Engineer Portfolio — Architectural Decision Log

> **Purpose:** A living record of every significant decision made across all phases of this project.
> Upload the latest version of this file to your Claude Project at the start of each new phase.
> Update it whenever you make a meaningful architectural, tooling, or design choice.
>
> **Format:** Each entry has a date, the decision made, the alternatives considered, and the reason chosen.
> Honest entries — including "I didn't know about X at the time" — are more valuable than polished ones.

---

## Project Identity

| Field | Value |
|---|---|
| Project name | AI Engineer — Portfolio |
| Claude Project | AI Engineer - Portfolio |
| Started | April 2026 |
| Hardware | Apple M1 Max · 64 GB Unified Memory · macOS |
| Primary language | Python 3.12 |
| Repository | github.com/SavyOnAI/local-ai-stack |

---

## Phase Overview

| Phase | Name | Status | Started | Completed |
|---|---|---|---|---|
| 1 | Local RAG Pipeline | ✅ Complete | April 2026 | April 2026 |
| 2 | Production RAG Application | 🟡 In Progress | April 2026 | — |
| 3 | Local SLM Benchmarking | ⬜ Planned | — | — |
| 4 | Monitoring & Observability | ⬜ Planned | — | — |
| 5 | Fine-Tuning with LoRA & DPO | ⬜ Planned | — | — |
| 6 | Real-Time Multimodal Application | ⬜ Planned | — | — |

---

## Decision Log

---

### DEC-001 — Single Evolving Codebase vs Separate Repos

**Date:** April 2026
**Phase:** All
**Decision:** One repository. All six phases extend the same codebase.

**Alternatives considered:**
- Six separate repositories, one per phase
- A monorepo with separate packages per phase

**Reason chosen:**
Each phase builds directly on the previous one. Phase 2 is Phase 1 refactored and extended — not a new project. A single repo tells the correct story: one evolving system, not six disconnected demos. It also means the evaluation set built in Phase 2 carries forward into Phase 3, 4, and 5 without duplication. In a technical interview, walking someone through a single repo with a documented evolution is more compelling than showing six separate projects.

---

### DEC-002 — Local Inference via Ollama vs Cloud APIs

**Date:** April 2026
**Phase:** All
**Decision:** Ollama for all LLM inference. No cloud API calls for generation or embedding.

**Alternatives considered:**
- OpenAI API (GPT-4o)
- Anthropic API (Claude)
- Hugging Face Inference API
- Replicate

**Reason chosen:**
Hardware (M1 Max, 64 GB) makes local inference genuinely viable at production-useful model sizes. Local inference means: zero cost per query, no API key management, no rate limits, full data privacy, and real benchmark numbers from a specific known hardware configuration. The API call pattern is identical whether hitting Ollama locally or a cloud endpoint — changing one URL string is all it takes to go cloud if needed. The portfolio value of saying "I benchmarked three model tiers on my own hardware" is higher than "I called the OpenAI API."

---

### DEC-003 — Primary Model Selection

**Date:** April 2026
**Phase:** 1 and 2
**Decision:** Gemma 4 26B as primary development model. Llama 3.3 70B for quality benchmarking.

**Alternatives considered:**
- Gemma 3 27B (previous generation — originally planned, replaced by Gemma 4 26B)
- Gemma 3 4B (too small for nuanced RAG responses)
- Gemma 3 12B (middle ground, less interesting for benchmarking)
- Mistral 7B (solid but outclassed by Gemma 4 26B on most tasks)
- Phi-4 14B (strong reasoning, less community documentation)

**Reason chosen:**
Gemma 4 26B is the newer generation model at the same size tier as the originally planned Gemma 3 27B. 64 GB unified memory makes 26B a comfortable fit with headroom for the embedding model running simultaneously. 26B produces meaningfully better responses than smaller models for domain-specific Q&A — the kind of quality difference that matters in production. Keeping a 4B model as the speed-tier benchmark and 70B as the quality-tier benchmark gives a three-point comparison that tells a real story about quality-vs-latency tradeoffs.

**Ollama model string:** `gemma4:26b`
**Pull command:** `ollama pull gemma4:26b`

**To revisit:** Swap Gemma 4 26B for Llama 3.3 70B in Phase 2 once the pipeline is stable, and measure the quality delta on the eval set.

---

### DEC-004 — Embedding Model Selection

**Date:** April 2026
**Phase:** 2 onwards
**Decision:** nomic-embed-text via Ollama for all embedding generation.

**Alternatives considered:**
- OpenAI text-embedding-3-small (cloud, costs money per token)
- sentence-transformers/all-MiniLM-L6-v2 (fast but lower quality)
- BAAI/bge-large-en-v1.5 (high quality, heavier)

**Reason chosen:**
nomic-embed-text runs locally via Ollama (same runtime as the LLM, no extra setup), produces strong embeddings for English text, and keeps the entire pipeline offline. With 64 GB available, running it alongside Gemma 4 26B simultaneously is not a memory concern. Using Ollama for both LLM and embeddings means a single dependency for all model serving.

---

### DEC-005 — Vector Store Selection

**Date:** April 2026
**Phase:** 2 onwards
**Decision:** ChromaDB (local, persistent) for the vector store.

**Alternatives considered:**
- Pinecone (managed cloud service)
- Weaviate (self-hosted Docker container)
- Qdrant (self-hosted, strong performance)
- FAISS (in-memory, no persistence)

**Reason chosen:**
ChromaDB runs as a Python library with zero server configuration — `import chromadb` and it works. Persistence to a local folder is automatic. For a single-machine portfolio project, the operational overhead of Docker (Weaviate, Qdrant) adds complexity before writing any RAG logic. Pinecone adds a cloud dependency and data leaves the machine. FAISS has no built-in persistence. ChromaDB is the right-sized tool for this phase. Migration path to Pinecone or Qdrant at scale requires changing only the vector store client — retrieval and generation logic is unaffected.

**To revisit:** Evaluate Qdrant as an upgrade in Phase 4 if ChromaDB shows performance limitations at larger document corpus sizes.

---

### DEC-006 — Retrieval Strategy

**Date:** April 2026
**Phase:** 2 onwards
**Decision:** Hybrid retrieval — BM25 (keyword) + vector (semantic) — fused with Reciprocal Rank Fusion (RRF), followed by cross-encoder reranking.

**Alternatives considered:**
- Vector-only retrieval (simpler, one system)
- BM25-only (no embedding model needed)
- Hybrid without reranking

**Reason chosen:**
Vector search excels at semantic similarity but misses exact keyword matches (product names, codes, proper nouns). BM25 excels at keywords but misses paraphrases and synonyms. Hybrid covers both failure modes. RRF is a simple, parameter-free fusion formula that consistently outperforms weighted sum approaches for most retrieval tasks. The cross-encoder reranker adds the most accuracy improvement because it scores each chunk against the actual query — but it is too slow to run on the full corpus, so retrieval is deliberately staged: fast retrieval (BM25 + vector) followed by accurate reranking (cross-encoder). This is the pattern used in production enterprise RAG systems today.

---

### DEC-007 — Logging Library Selection

**Date:** April 2026
**Phase:** 2
**Decision:** Loguru for structured logging in Phase 2.

**Alternatives considered:**
- Python built-in logging module (verbose to configure)
- OpenTelemetry (industry standard for distributed tracing)
- Structlog

**Reason chosen:**
Loguru requires two lines of setup and produces structured JSON output immediately. The goal in Phase 2 is to learn *what* to log and *why* — latency per stage, token counts, quality scores. Understanding that first makes the upgrade to OpenTelemetry in Phase 4 meaningful rather than mechanical. OpenTelemetry is the right tool when you have multiple services and need distributed tracing — Phase 2 is a single service. Building with Loguru now and migrating to OpenTelemetry in Phase 4 is a deliberate decision documented in the Phase 4 PRD.

**To revisit:** Migrate to OpenTelemetry in Phase 4 as part of the Monitoring & Observability phase.

---

### DEC-008 — API Framework Selection

**Date:** April 2026
**Phase:** 2 onwards
**Decision:** FastAPI with Uvicorn for the REST API server.

**Alternatives considered:**
- Flask (simpler but no built-in async or typing)
- Django REST Framework (too heavyweight for a single-service API)
- Litestar (modern alternative, less documented)

**Reason chosen:**
FastAPI is the industry standard for Python AI/ML APIs. It provides automatic OpenAPI docs, native async support (important for streaming in Phase 6), and Pydantic v2 integration for typed request/response validation. The automatic /docs endpoint makes the API self-documenting — useful for portfolio demos. Strong ecosystem of tutorials and production examples.

---

### DEC-009 — Web UI Framework Selection

**Date:** April 2026
**Phase:** 2 onwards
**Decision:** Gradio for the browser-based chat interface.

**Alternatives considered:**
- Streamlit (good alternative, slightly more verbose)
- Custom React frontend (too much frontend work for this phase)
- CLI only (no visual demo)

**Reason chosen:**
Gradio builds a chat UI in under 20 lines of Python. It connects directly to a Python function or FastAPI endpoint. It produces a shareable demo link if needed. For a portfolio project where the AI system is the story — not the UI — Gradio is appropriately low-friction. A custom React frontend would take longer to build than the entire RAG pipeline and adds no AI engineering signal to the portfolio.

---

### DEC-010 — Evaluation Framework Selection

**Date:** April 2026
**Phase:** 2 onwards
**Decision:** RAGAS for RAG quality evaluation.

**Alternatives considered:**
- Manual human evaluation only
- Custom scoring functions
- DeepEval
- TruLens

**Reason chosen:**
RAGAS provides RAG-specific metrics (faithfulness, answer relevancy, context precision, context recall) that directly measure what matters in a retrieval-augmented system. It is the most widely referenced RAG evaluation framework in the field — using it signals familiarity with current production practices. The CI gate built around RAGAS faithfulness (≥ 0.75) creates an automated quality regression detector that is rare in portfolio projects and highly valued by technical interviewers.

---

### DEC-011 — CI/CD Platform Selection

**Date:** April 2026
**Phase:** 2 onwards
**Decision:** GitHub Actions for the evaluation gate and CI pipeline.

**Alternatives considered:**
- CircleCI
- Jenkins (self-hosted)
- No CI (manual evaluation only)

**Reason chosen:**
GitHub Actions is free for public repositories, requires zero additional account setup (already on GitHub), and has extensive documentation and community workflows. The evaluation gate yaml lives in the same repository as the code — the CI configuration is part of the documented system, not a separate service. For a portfolio project, GitHub Actions also makes the CI gate visible to anyone who browses the repository.

---

### DEC-012 — File Format Support Scope

**Date:** April 2026
**Phase:** 2 onwards
**Decision:** Support 8 formats in Phase 2: .txt, .md, .pdf, .docx, .pptx, .xlsx, .csv, .html

**Alternatives considered:**
- Text only (.txt, .md) — too limiting for real enterprise use cases
- All formats including scanned PDFs — OCR adds significant complexity
- Add email formats (.eml, .msg) — niche, deferred to later

**Reason chosen:**
These 8 formats cover virtually every document type in a real enterprise knowledge base. All are handleable with pure Python libraries — no external services, no system dependencies beyond pip installs. XLSX is the most interesting engineering challenge because cells need column-header context to be meaningful — converting rows to natural language sentences is a real design problem. Scanned PDFs (OCR) are deferred because Tesseract adds a system-level dependency and significant complexity for limited additional value at this stage.

---

### DEC-013 — IDE Selection

**Date:** April 2026
**Phase:** All
**Decision:** VS Code as primary IDE.

**Alternatives considered:**
- PyCharm Professional (excellent Python tooling, paid)
- Cursor (AI-native IDE, VS Code fork)
- Zed (fast, modern, less mature ecosystem)
- Vim/Neovim (powerful, steep learning curve)

**Reason chosen:**
VS Code is free, has the largest extension ecosystem for Python development, and is the most widely documented IDE in tutorials and Stack Overflow answers — critical for a learning project where searching for help is part of the workflow. The Python, Pylance, and Ruff extensions provide professional-grade tooling. Strong Git integration built in.

**VS Code extensions installed:**
- Python (Microsoft) — essential
- Pylance — type checking and autocomplete
- Ruff — fast Python linter and formatter
- GitLens — enhanced Git history and blame
- REST Client — test FastAPI endpoints without leaving VS Code
- GitHub Copilot — optional, useful for boilerplate (free tier available)
- Even Better TOML — for config files
- indent-rainbow — visual indentation guides (helpful for Python)

---

### DEC-014 — Python Version and Environment Management

**Date:** April 2026
**Phase:** All
**Decision:** Python 3.12 via pyenv. One virtual environment per project phase (venv).

**Alternatives considered:**
- System Python (risky — macOS system Python should not be modified)
- conda/miniconda (heavier, more suited to data science workflows)
- Poetry (dependency management, good alternative)
- uv (fast, modern, worth considering in Phase 2+)

**Reason chosen:**
pyenv manages Python versions cleanly on macOS without touching the system Python. venv is the standard, zero-dependency virtual environment tool. Simple and well-documented. uv is worth evaluating as an upgrade in Phase 2 — it is significantly faster than pip and is rapidly becoming the standard for Python project management in 2025/2026.

**Note:** During setup, Python 3.12 initially failed to compile due to a missing xz/lzma library. Fixed by running `brew install xz` before reinstalling via pyenv. This is a known macOS pyenv issue.

**To revisit:** Evaluate switching from pip + venv to uv in Phase 2.

---

### DEC-015 — Repository Name

**Date:** April 2026
**Phase:** All
**Decision:** Repository named `local-ai-stack` at github.com/SavyOnAI/local-ai-stack

**Alternatives considered:**
- `production-ai-system` (original plan — accurate but generic)
- `rag-to-multimodal` (describes the arc but less immediately scannable)
- `ai-engineer-portfolio` (keyword-rich but less distinctive)

**Reason chosen:**
`local-ai-stack` is short, memorable, and immediately communicates the single most distinctive thing about this project — that the entire AI system runs locally with no cloud APIs. It stays accurate across all six phases regardless of what features are added. The name is the first signal a recruiter reads; it should communicate the differentiator.

---

### DEC-016 — Citation Extraction Regex Fix — Multi-ID Brackets

**Date:** June 2026
**Phase:** 2
**Decision:** Extended the citation extraction regex in `citation_validator.py` to correctly split multi-ID citation brackets, rather than enforcing single-ID-per-bracket via the prompt only.

**Alternatives considered:**
- Leave the model free to cite multiple chunk IDs per bracket with no parser support for it
- Change `prompt_builder.py` to force one ID per bracket only

**Reason chosen:**
`extract_cited_ids()` used the pattern `\[([^\[\]]+_chunk_\d+)\]`, which captured everything between brackets as a single group — including internal commas. When Gemma 4 26B cited multiple sources in one bracket (e.g. `[chunk_a, chunk_b]`), the entire string was treated as one malformed ID, which never matched any real chunk ID in the index. The result: `citations_valid` came back `false` even when retrieval and the answer itself were correct — a false negative, not a real citation failure. Caught while testing the new `/query` FastAPI endpoint on Day 7, via a live query about macronutrients where both cited chunk IDs were valid but got fused into one unmatched string.

Fixed by extending the regex to match comma-separated IDs inside a single bracket, then explicitly splitting and stripping each match into separate IDs before validation runs. Chose defensive parsing over prompt-only enforcement so the validator stays correct regardless of how consistently the model formats citations — relying solely on the model to never produce a multi-ID bracket is fragile and was already disproven this session.

**Lesson:** A validator returning `false` doesn't always mean the thing being validated is wrong — sometimes the validator itself has a parsing bug. Worth checking the extraction logic before assuming the model or retrieval is at fault.

---

### DEC-017 — RAGAS Faithfulness `nan` Bug — Root Cause and Fix

**Date:** June 2026
**Phase:** 2
**Decision:** Fixed `_mean()` in `evaluator.py` to filter both `None` and `NaN` when averaging per-question RAGAS scores, rather than only `None`.

**Alternatives considered:**
- Suspected Gemma's markdown-fenced JSON output (` ```json ... ``` `) was breaking RAGAS's parser — built a `_CleanOutputOllama` subclass to strip fences before ruling this out. Verified directly that LangChain's `parse_json_markdown` already handles fenced JSON correctly, so the subclass was removed — it solved a problem that didn't exist.
- Suspected `RunConfig` timeouts were too short — raised from 120s to 300s. This reduced but did not fully eliminate isolated per-question timeouts (expected behaviour for a local 26B judge model making chained calls), and was not the root cause.

**Reason chosen:**
RAGAS returns `np.nan` (not `None`) for any question where the LLM judge fails to produce a parseable score — typically from a timeout during faithfulness's two-step process (decompose the answer into statements, then verify each statement against the retrieved context). The original `_mean()` filter (`v is not None`) did not catch `np.nan`, and Python's `sum()` propagates `nan` across an entire list. This meant a single failed question out of 20 silently poisoned the whole faithfulness average to `nan` — even when 18–19 questions had scored correctly.

Diagnosed by writing a per-question isolation script that scored faithfulness one question at a time across all 20 questions. This produced 18 real scores (mostly 1.0, with one genuine 0.0 on Q11) and exactly 2 timeouts (Q7, Q17) — confirming the pipeline, retrieval, and judge model were all working correctly, and that the bug was isolated entirely to the score-averaging logic in `_mean()`, not the evaluation itself.

Fixed by changing the filter to `v is not None and not math.isnan(v)`, and added a print statement reporting how many questions were excluded per metric, so future data loss is visible in the terminal output rather than silently collapsing the average to `nan`.

**Result:** Faithfulness = 0.95 on the full 20-question eval set after the fix, with 19/20 questions scoring valid faithfulness values (the 20th, Q7 or Q17, still timed out but was correctly excluded rather than corrupting the average).

**Lesson:** `nan` is not `None` in Python — `v is not None` does not filter out `float('nan')`. This single distinction caused three separate ~4-hour full evaluation runs to silently fail before being traced to one filtering condition. Worth remembering for any future code that averages scores from an external library: check what sentinel value it actually uses for "missing," don't assume it's `None`.

---

### DEC-018 — `.gitignore` Scope — Beyond the Phase 1 Baseline

**Date:** June 2026
**Phase:** 2
**Decision:** Extended `.gitignore` beyond the Phase 1 PRD baseline (`.env`, `__pycache__`, `venv/`) to also exclude `.DS_Store`, `chroma_db/`, and `bm25_index.pkl`.

**Alternatives considered:**
- Leave `.gitignore` as-is from Phase 1 and manually `rm -rf chroma_db/` before every commit (already the documented Day 9+ habit, but relies on remembering every time)
- Commit `chroma_db/` and `bm25_index.pkl` to track index state in git history

**Reason chosen:**
`.DS_Store` is a macOS Finder artifact, not project code — it differs per machine and has no place in a Python repository regardless of OS. It surfaced as a tracked, modified file in `git status` despite never being intentionally added, which is the signature of a file that should have been excluded from the very first commit. `chroma_db/` and `bm25_index.pkl` are regenerated by `index_documents.py` and are already documented as something to delete before committing — formalizing this in `.gitignore` removes the manual step and the risk of forgetting it, rather than relying on memory every session.

**Lesson:** A file showing up as tracked-and-modified in `git status` without you having added it is a reliable signal that `.gitignore` is incomplete, not that something is wrong with the file itself.

---

### DEC-019 — ChromaDB Metadata Silently Dropped Since Day 3

**Date:** July 2026
**Phase:** 2
**Decision:** Fixed `add_chunks()` in `vector_store.py` to pass `metadatas=` to `collection.add()`.

**Alternatives considered:**
- None — this was a straightforward omission, not a design choice with tradeoffs.

**Reason chosen:**
`collection.add()` was being called with `ids`, `documents`, and `embeddings` only — no `metadatas` argument existed in the call at all. ChromaDB doesn't error on a missing optional parameter; it silently stores chunks with no metadata. This meant every chunk indexed since Day 3, across two full corpora, had `source` and `chunk_index` computed correctly upstream and then discarded the moment they reached this function. Undetected until a post-reindex file-inventory check (comparing files on disk against distinct `source` values in the collection) came back with every chunk showing `None` metadata.

**Lesson:** The original smoke test for `add_chunks()` used flat fake chunks (`id`/`text`/`embedding` only) with no `source` field at all — it could not have caught this bug even in principle, because it never exercised the metadata path. Fixed the smoke test alongside the bug: fake chunks now include a `metadata` dict matching the real pipeline's shape, so a future regression here would fail loudly instead of silently.

---

### DEC-020 — File-Swap Incident: chunker.py / vector_store.py Content Mixup

**Date:** July 2026
**Phase:** 2
**Decision:** No process change beyond reinforcing the existing `grep -r "^def " src/` session-start check — this was caught by that check, as intended.

**What happened:**
During iterative fixes to `add_chunks()`, the corrected `vector_store.py` content was pasted into `chunker.py`, overwriting the original chunking logic entirely, while the old unfixed `vector_store.py` content remained in its own file untouched. Surfaced as an `ImportError: cannot import name 'chunk_document'` — the function genuinely no longer existed in that file. Confirmed via direct file upload and comparison rather than guessing at the cause.

**Reason for no process change:**
This is the second file-swap incident this project (see original two-incident count in project history). Both were caught by the standing `grep -r "^def " src/` requirement before further code changes — the check is working as designed. The actual fix is discipline, not tooling: confirm file contents directly (`cat`) when a traceback contradicts what should be on disk, rather than assuming the file matches the last message sent.

---

### DEC-021 — Corpus Swap: Nutrition → AI/Agentic AI Domain

**Date:** July 2026
**Phase:** 2
**Decision:** Replaced the nutrition-domain corpus with a 31-file AI/agentic-AI domain corpus spanning all 8 supported formats (PDF, DOCX, PPTX, XLSX, CSV, HTML, MD, TXT).

**Alternatives considered:**
- Keep the nutrition corpus and add AI-domain documents alongside it (rejected — dilutes the portfolio narrative, doubles indexing/eval cost for no benefit).

**Reason chosen:**
The original nutrition corpus was a placeholder for pipeline development, not the intended final domain. AI/agentic AI content directly supports the project's own narrative (a RAG system about RAG and agents). Sourced from a mix of arXiv papers, vendor documentation (AWS, Cisco, Microsoft, OpenAI), governance frameworks, and self-authored reference material — deliberately including all 8 formats to exercise every extractor built in Phase 2, including three (docx, pptx, xlsx) that had never been run against real files before this swap.

**Result:** 4,869 chunks initially indexed; later reduced to 4,788 after PDF corruption remediation (DEC-023) permanently excluded 53 unrecoverable pages.

---

### DEC-022 — GitHub Actions Runner: Self-Hosted, Not Cloud-Hosted

**Date:** July 2026
**Phase:** 2
**Decision:** Self-hosted GitHub Actions runner on local M1 Max hardware, restricted to `push`-to-`main` triggers only (never `pull_request`).

**Alternatives considered:**
- GitHub-hosted runners (`ubuntu-latest`) — standard, zero setup.
- Precompute eval results locally, have CI check a committed JSON threshold instead of running the pipeline live.
- Use a smaller cloud-callable model as a CI-only stand-in judge.

**Reason chosen:**
The CI eval gate needs to run `evaluator.py`, which calls Ollama for both `gemma4:26b` generation and the RAGAS judge. GitHub's hosted runners have no GPU and insufficient RAM to run a 26B local model — this isn't a tuning problem, it's a structural mismatch with DEC-002's fully-local premise. A self-hosted runner on the same Mac that already runs Ollama is the only option that preserves "no cloud APIs" while actually running the real pipeline in CI, not a stand-in.

**Security consideration:** Self-hosted runners on public repositories are a documented attack vector — a stranger's pull request can trigger a workflow that executes on the runner's actual machine. Mitigated by scoping the workflow to `push: branches: [main]` only; PRs from anyone else never touch the runner, since only the repo owner can push directly to `main`. Additionally requires an explicit `permissions: contents: read` block to prevent the workflow's `GITHUB_TOKEN` from having broader-than-necessary default permissions.

**Tradeoff accepted:** CI only runs when the Mac is on and the runner service is active — unlike a cloud runner, this isn't always-available. Acceptable for a solo portfolio project; would need revisiting with a second contributor or a requirement for CI to run on arbitrary infrastructure.

---

### DEC-023 — PDF Extraction Corruption: Detection Heuristic and Three-Tier Fallback

**Date:** July 2026
**Phase:** 2
**Decision:** Added tail-fraction-based corruption detection to `pdf_extractor.py`, with automatic fallback through three extraction methods: pypdf default → pypdf layout mode → pdfplumber. Pages failing all three are skipped rather than ingested corrupted.

**Alternatives considered:**
- Average word length as the sole corruption signal — tested first, rejected. Could not reliably separate corrupted pages from clean pages with normal short-word density (citations, section numbers); a single number can't distinguish fragmentation (words split apart) from fusion (words wrongly merged), since both move the average in different directions.
- Global switch to `extraction_mode="layout"` for all PDFs — rejected. Fixed some files, actively degraded others that were already extracting correctly (word-fusion corruption on previously-clean multi-column academic PDFs), confirmed via direct before/after comparison on both bad and clean pages before deciding against it.
- Dictionary-word-ratio check (e.g. against `/usr/share/dict/words`) — considered, not implemented. Rejected because this corpus's own vocabulary (RAGAS, LangGraph, reranker, embeddings) would register as false positives against a general English dictionary.
- Structural/layout-based detection (identify multi-column or table-heavy PDF sections before extraction, rather than scoring extracted text after the fact) — theoretically more targeted, deferred as future work; larger scope than justified for the immediate problem.

**Reason chosen:**
Root cause: several corpus PDFs (marketing-deck style exports, notably `OpenAI_a_practical_guide_to_building_agents.pdf`) use embedded/subsetted fonts with corrupted or non-standard glyph-advance-width data. Both pypdf extraction modes rely on this width data to decide word boundaries and inherit the same corruption, misfiring in opposite directions (fragmentation vs. fusion) depending on page content density. `pdfplumber` reconstructs words from measured character bounding boxes instead of trusting the font's declared widths, sidestepping the corrupted data entirely — confirmed by direct text inspection (not just the numeric heuristic) on multiple previously-unreadable pages, which came back as clean, grammatically correct English after the pdfplumber fallback.

**Detection method:** `_tail_fraction()` measures the proportion of words at each length extreme (≤2 chars for fragmentation, ≥15 chars for fusion) rather than a single average — calibrated against ~30 sampled pages from 7 confirmed-clean files, then validated against known-bad pages before any threshold was trusted. Two-tier response: high-confidence corruption (`short_frac > 0.5` or `long_frac > 0.065`) triggers automatic fallback through layout mode then pdfplumber; borderline corruption (`short_frac` 0.30–0.5) is logged for manual review but not auto-fixed, since this range could not be reliably separated from normal clean-page noise at full-corpus scale.

**Result:** Total permanently-skipped pages across the corpus dropped from 83 to 53 after the pdfplumber tier was added. `OpenAI_a_practical_guide_to_building_agents.pdf` specifically went from 30 skipped/1 recovered to 5 skipped/26 recovered — the single largest improvement, on the file that motivated this entire investigation.

**Known unresolved case:** `Engineering_the_RAG_Stack_Architecture_&_Trust.pdf` pages 67–86 remain fully skipped under all three extraction methods (0 recovered of 20 flagged). Manually inspected — this is a clean, correctly-formatted bibliography/reference section, not corrupted text. The tail-fraction heuristic cannot distinguish a citation-dense reference list (short author initials, page-range abbreviations, bracketed numbers) from genuine fragmentation. Accepted as a reasonable outcome rather than pursued further: a reference list's retrieval value for grounding RAG answers is low regardless of extraction quality.

**Result vs. context_precision:** This fix improved faithfulness substantially (0.886 → 0.9626 on the full 30-question eval) by making previously garbled or entirely-missing content available and correctly grounded. It did **not** meaningfully move context_precision (0.4369 → 0.4387) — see DEC-024, since that metric turned out to be capped by a different, unrelated cause.

**To revisit:** Evaluate PyMuPDF (fitz) more broadly as an alternative or additional extraction tier — tested informally alongside pdfplumber for this investigation and performed near-identically on the specific pages checked, but not adopted since pdfplumber alone was sufficient and has a lighter dependency footprint. Worth a fuller comparison if extraction issues recur on future corpus additions.

---

### DEC-024 — context_precision Ceiling: Retrieval Specificity, Not Extraction Quality

**Date:** July 2026
**Phase:** 2
**Decision:** No code change made. Documented as a known, accepted limitation of the current fixed-`top_k=5` retrieval design; not pursued further this phase.

**Investigation:** After DEC-023's extraction fix, context_precision on the full 30-question eval moved only from 0.4369 to 0.4387 — essentially flat, despite faithfulness improving substantially. Diagnosed directly from `eval_results_per_question.csv` rather than assumption:

- **`OpenAI_a_practical_guide_to_building_agents.pdf` table-of-contents question** scored context_precision = 0.0 both before and after the extraction fix. Post-fix, the retrieved chunk (chunk 47) contained clean, correctly extracted, genuinely on-topic content from the same document (Instructions, model selection, guardrails) — but not the specific page-1 table-of-contents chunk the ground truth needed. Content availability was fixed; retrieval's ability to find the *one specific* chunk matching a narrow question, among many legitimately-relevant chunks in a large document, was not.
- **LlamaIndex MCP-server-tools question** (`LlamaIndex_Introduction_to_RAG_Developer_Documentation.html`, unaffected by any PDF extraction work) showed the identical failure shape: retrieval returned a clean, on-topic chunk about LlamaIndex's general purpose instead of the specific chunk listing the four MCP server tools the question asked about. Confirms the pattern is general to the retrieval/reranking pipeline, not specific to PDFs or to any one document.

**Reason chosen (for not pursuing a fix this phase):**
Root cause is architectural: `top_k=5` is fixed regardless of question narrowness or document size. A single-fact question against a small document (5–8 chunks total) or a large one (600+ chunks) both receive exactly 5 retrieved chunks, most of which are necessarily "extra" for a narrow answer — this is what context_precision penalizes by design. Fixing it properly means tuning `top_k` width or adding a dynamic reranker-score cutoff, which is real, separate engineering work with its own tradeoffs (risk of reducing context_recall if `top_k` is narrowed too aggressively), not a bug fix.

The Phase 2 PRD's own evaluation table (§10) sets context_precision's threshold as a CI **warning**, not a build-blocking gate — only faithfulness (≥0.75) blocks merges. With faithfulness now at 0.9626, the CI gate itself is unaffected by this finding.

**To revisit:** Tune `top_k` and/or add a reranker-score-gap cutoff (return fewer chunks when the reranker's top result clearly outscores the rest) to improve context_precision without degrading recall. Natural fit for Phase 3 or 4, alongside the observability work that will make latency/quality tradeoffs from such a change directly measurable.

---

## Decisions Pending

The following decisions are noted but not yet made. They will be logged here when resolved.

| Decision needed | Phase | Notes |
|---|---|---|
| Chunking strategy (size and overlap values) | 2 | Will be determined empirically using eval set |
| Fine-tuning dataset selection | 5 | Depends on domain chosen for Phase 2 |
| STT model selection (Phase 6) | 6 | Whisper is likely — model size TBD based on latency budget |
| TTS model selection (Phase 6) | 6 | Evaluate Coqui TTS vs Kokoro vs system TTS |
| Whether to upgrade ChromaDB to Qdrant | 4 | Revisit when corpus exceeds 10,000 chunks |
| OpenTelemetry backend (Jaeger vs Grafana Tempo) | 4 | Decide when observability phase begins |
| Speed-tier benchmark model for Phase 3 | 3 | Gemma 3 4B likely — pull with `ollama pull gemma3` when Phase 3 begins |
| OCR for scanned/image-only PDFs | 2+ | Deferred to Phase 3+. pypdf skips image-only pages and returns empty string. loader.py warns and skips these files. Manual conversion via macOS Preview or Acrobat as interim workaround. Tesseract OCR is the likely solution when addressed. |
| Slide images and shapes in PPTX files | 2+ | Images and flowchart relationships are not extractable with python-pptx alone. Text inside shapes is extracted but arrow relationships and flow direction are lost. Images skipped silently. Pytesseract OCR on exported slide images is the likely solution for image text. Flowchart relationships may never be worth addressing for a RAG use case. |
| Tune top_k / add reranker-score cutoff for context_precision | 2+ | See DEC-024. Risk of reducing context_recall if done carelessly — needs measurement, not a blind parameter change. |
| Evaluate PyMuPDF more broadly as extraction tier | 2+ | See DEC-023. Performed near-identically to pdfplumber on tested pages; not adopted for lack of need, not lack of merit. |
---

## What I'd Do Differently (Running Notes)

> Fill this section in as you progress. Be honest — this becomes interview gold.
> "I'd build the eval pipeline first" is more valuable to say than "everything went perfectly."

*[ Update this section as each phase completes ]*

---

## Version History

| Version | Date | Changes |
|---|---|---|
| 1.0 | April 2026 | Initial log — pre-code decisions documented |
| 1.1 | April 2026 | Updated DEC-003 for Gemma 4 26B; added DEC-015 for repo name; updated repository URL; noted xz fix in DEC-014 |
| 1.2 | June 2026 | Added DEC-016 — citation extraction regex fix found while testing the Day 7 FastAPI /query endpoint |
| 1.3 | June 2026 | Fixed stale Phase Overview table — Phase 1 marked Complete, Phase 2 marked In Progress |
| 1.4 | June 2026 | Added DEC-017 — RAGAS faithfulness `nan` bug traced to `np.nan` not being filtered in `_mean()`; added corpus swap and Q11 investigation to Decisions Pending |
| 1.5 | June 2026 | Added DEC-018 — `.gitignore` extended to exclude `.DS_Store`, `chroma_db/`, `bm25_index.pkl` beyond the Phase 1 baseline |
| 1.6 | July 2026 | Added DEC-019 through DEC-024 — metadata bug, file-swap incident, corpus swap, self-hosted CI runner decision, PDF extraction corruption fix, context_precision root-cause finding |

---

*This document is part of the AI Engineer — Portfolio project.*
*Keep it updated. Upload the latest version to your Claude Project before each new phase.*
