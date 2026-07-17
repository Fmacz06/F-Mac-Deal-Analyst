#!/bin/bash
# Add a VISION model so you can push screenshots/images into the chat.
# Your fmac text models are blind; this one has "eyes". Named fmac-vision.
# Note: image analysis on a CPU is heavy — expect it to be slower than text.
# Run from engine/:   bash mac/add-vision.sh
set -euo pipefail
cd "$(dirname "$0")/.."

if command -v ollama >/dev/null 2>&1; then
  OLLAMA="ollama"
elif [ -x "/Applications/Ollama.app/Contents/Resources/ollama" ]; then
  OLLAMA="/Applications/Ollama.app/Contents/Resources/ollama"
else
  echo "Ollama not found — run mac/intel-setup.sh first"; exit 1
fi

# build step needs the ollama server up
if ! curl -s http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
  echo "starting Ollama (needed only while building)..."
  [ -d "/Applications/Ollama.app" ] && open -a Ollama || ("$OLLAMA" serve >/tmp/ollama.log 2>&1 &)
  for i in 1 2 3 4 5 6; do
    curl -s http://127.0.0.1:11434/api/tags >/dev/null 2>&1 && break
    sleep 5
  done
fi

# Vision base. llama3.2-vision is a well-established vision model on Ollama.
BASE="llama3.2-vision"
FRAMEWORK="prompts/fmac-framework-lite.md"
[ -f "$FRAMEWORK" ] || { echo "missing $FRAMEWORK"; exit 1; }
mkdir -p /tmp/fmac-modelfiles

echo "== downloading the vision base (~8 GB, one-time — the long part) =="
"$OLLAMA" pull "$BASE"

mf="/tmp/fmac-modelfiles/fmac-vision.Modelfile"
{
  echo "FROM $BASE"
  echo "PARAMETER num_ctx 8192"
  printf 'SYSTEM """'
  cat "$FRAMEWORK"
  printf '\n\n---\n\nSPECIALTY: You can see images. When F Mac shares a screenshot or picture, read it carefully and describe or act on exactly what is in it. State plainly if something in the image is unclear rather than guessing."""\n'
} > "$mf"
"$OLLAMA" create fmac-vision -f "$mf"

echo ""
echo "DONE. Created: fmac-vision (can see screenshots/images)."
echo "In Msty: start a NEW chat, pick fmac-vision, then use the paperclip/attach"
echo "icon in the message bar to add a screenshot, and ask about it."
echo "You can quit the Ollama app again after this (Msty runs its own engine)."
