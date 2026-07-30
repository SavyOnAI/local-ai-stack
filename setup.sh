#!/usr/bin/env bash
# setup.sh — one-command environment setup for local-ai-stack
# Usage: ./setup.sh
#
# After the script finishes, activate the venv yourself before running
# anything — a script's venv activation does not persist into your shell
# once it exits (bash subshell scope). The script prints this reminder
# at the end too.

set -e  # stop on first error

echo "== local-ai-stack setup =="

echo "[1/6] Checking Ollama is installed..."
command -v ollama >/dev/null 2>&1 || { echo "Ollama not found. Install from https://ollama.com/download first."; exit 1; }

echo "[2/6] Pulling models (this may take a while on first run)..."
ollama pull gemma4:26b
ollama pull nomic-embed-text

echo "[3/6] Creating virtual environment..."
python -m venv local-ai-stack-venv
source local-ai-stack-venv/bin/activate

echo "[4/6] Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "[5/6] Checking docs/ folder..."
mkdir -p docs
if [ -z "$(ls -A docs 2>/dev/null)" ]; then
  echo "  docs/ is empty — add your own .txt .md .pdf .docx .pptx .xlsx .csv .html files before indexing."
fi

echo "[6/6] Indexing documents (skips if docs/ is empty)..."
if [ -n "$(ls -A docs 2>/dev/null)" ]; then
  python -m src.ingestion.index_documents
else
  echo "  Skipped — no documents found in docs/."
fi

echo ""
echo "Setup complete."
echo ""
echo "IMPORTANT: this script's virtual environment does NOT stay active in your"
echo "shell once the script exits (bash subshell limitation — every venv-based"
echo "setup script has this). You must activate it yourself before running anything:"
echo ""
echo "  source local-ai-stack-venv/bin/activate"
echo ""
echo "Then:"
echo "  Terminal interface:  python -m src.main"
echo "  API + Web UI:         uvicorn src.api.server:app --reload   (terminal 1)"
echo "                        python ui/app.py                     (terminal 2)"