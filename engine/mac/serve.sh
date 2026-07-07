#!/bin/bash
# Serve base model + adapter via mlx_lm.server (Correction 1: no fuse, no
# Ollama). OpenAI-compatible endpoint on localhost:8080.
# Run ON THE MAC STUDIO from engine/:  bash mac/serve.sh adapters/coding/run-XXXX
# Adapter swap = re-run this with a different path (v1 per §11 A5).
set -euo pipefail
cd "$(dirname "$0")/.."
source .venv/bin/activate

BASE_MODEL="${BASE_MODEL:-mlx-community/Qwen2.5-14B-Instruct-4bit}"
ADAPTER="${1:?usage: mac/serve.sh <adapter-path>  (or 'base' for no adapter)}"
PORT="${PORT:-8080}"

if [ "$ADAPTER" = "base" ]; then
  exec python3 -m mlx_lm server --model "$BASE_MODEL" --port "$PORT"
else
  exec python3 -m mlx_lm server --model "$BASE_MODEL" --adapter-path "$ADAPTER" --port "$PORT"
fi
