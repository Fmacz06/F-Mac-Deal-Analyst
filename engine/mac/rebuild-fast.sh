#!/bin/bash
# FAST rebuild — fixes the crawl on Intel Macs.
# - condensed framework (core rules, no long examples to re-read each turn)
# - modest context window (8192) instead of 32768 (huge on a CPU = major brake)
# Run from engine/:   bash mac/rebuild-fast.sh
set -euo pipefail
cd "$(dirname "$0")/.."

OLLAMA="ollama"
command -v ollama >/dev/null 2>&1 || OLLAMA="/Applications/Ollama.app/Contents/Resources/ollama"
[ -x "$OLLAMA" ] || { echo "Ollama not found — run mac/intel-setup.sh first"; exit 1; }

RAM_GB=$(( $(sysctl -n hw.memsize) / 1073741824 ))
if [ "$RAM_GB" -ge 14 ]; then BASE="qwen2.5:7b-instruct"; else BASE="qwen2.5:3b-instruct"; fi

FRAMEWORK="prompts/fmac-framework-lite.md"
[ -f "$FRAMEWORK" ] || { echo "missing $FRAMEWORK"; exit 1; }
mkdir -p /tmp/fmac-modelfiles

build () {
  local name="$1" specialty="$2"
  local mf="/tmp/fmac-modelfiles/$name.Modelfile"
  {
    echo "FROM $BASE"
    echo "PARAMETER num_ctx 8192"          # modest window = far faster on a CPU
    printf 'SYSTEM """'
    cat "$FRAMEWORK"
    if [ -n "$specialty" ]; then
      printf '\n\n---\n\nSPECIALTY:\n'
      cat "$specialty"
    fi
    printf '"""\n'
  } > "$mf"
  "$OLLAMA" create "$name" -f "$mf"
  echo "  rebuilt (fast): $name"
}

echo "Rebuilding all models for speed (condensed framework, 8k window)..."
build fmac-base    ""
build fmac-coding    prompts/coding-system.txt
build fmac-reasoning prompts/reasoning-system.txt
build fmac-video     prompts/video-system.txt
build fmac-design    prompts/design-system.txt

echo ""
echo "DONE. Models rebuilt for speed. Your operating rules are still baked in."
echo "In Msty, start a NEW conversation and pick a fmac- model to feel the difference."
echo ""
echo "Tip: you can now quit the old standalone Ollama app (menu-bar llama icon ->"
echo "Quit) — Msty runs its own engine, so quitting frees memory and speeds things up."
