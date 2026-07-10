#!/bin/bash
# Intel Mac path — build and run the local language model WITHOUT training.
# Uses Ollama (runs on Intel Macs). Creates F Mac's custom models with his
# system prompts and parameters baked in. Training comes later, on rented
# GPU or Apple Silicon — this gets the working local LM TODAY.
#
# Run from engine/:   bash mac/intel-setup.sh
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== [1/5] Ollama =="
OLLAMA="ollama"
if ! command -v ollama >/dev/null 2>&1; then
  # the Mac app ships its own CLI inside the app bundle — use it directly
  if [ -x "/Applications/Ollama.app/Contents/Resources/ollama" ]; then
    OLLAMA="/Applications/Ollama.app/Contents/Resources/ollama"
    echo "using CLI inside Ollama.app"
  elif command -v brew >/dev/null 2>&1; then
    brew install ollama
  else
    echo "Ollama isn't installed and Homebrew isn't available."
    echo "Download Ollama from https://ollama.com/download, install it,"
    echo "then run this script again."
    exit 1
  fi
fi

# make sure the server is up — launching the app starts it
if ! curl -s http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
  echo "starting Ollama..."
  if [ -d "/Applications/Ollama.app" ]; then
    open -a Ollama
    sleep 10
  else
    ("$OLLAMA" serve >/tmp/ollama.log 2>&1 &)
    sleep 5
  fi
fi
for i in 1 2 3 4 5 6; do
  curl -s http://127.0.0.1:11434/api/tags >/dev/null 2>&1 && break
  sleep 5
done
curl -s http://127.0.0.1:11434/api/tags >/dev/null || { echo "ollama server not responding — open the Ollama app manually, then rerun"; exit 1; }

echo "== [2/5] pick model size for this machine =="
RAM_GB=$(( $(sysctl -n hw.memsize) / 1073741824 ))
if [ "$RAM_GB" -ge 14 ]; then
  BASE="qwen2.5:7b-instruct"     # ~4.7 GB — best quality this machine can hold
else
  BASE="qwen2.5:3b-instruct"     # ~2 GB — for 8GB machines
fi
echo "RAM: ${RAM_GB}GB -> base model: $BASE"

echo "== [3/5] download the base model (one-time) =="
"$OLLAMA" pull "$BASE"

echo "== [4/5] build F Mac's custom models =="
mkdir -p /tmp/fmac-modelfiles
build_model () {
  local name="$1" system_file="$2"
  {
    echo "FROM $BASE"
    echo "PARAMETER num_ctx 8192"
    echo "SYSTEM \"\"\"$(cat "$system_file")\"\"\""
  } > "/tmp/fmac-modelfiles/$name.Modelfile"
  "$OLLAMA" create "$name" -f "/tmp/fmac-modelfiles/$name.Modelfile"
  echo "  created: $name"
}
echo "FROM $BASE" > /tmp/fmac-modelfiles/fmac-base.Modelfile
"$OLLAMA" create fmac-base -f /tmp/fmac-modelfiles/fmac-base.Modelfile
echo "  created: fmac-base (router/general)"
build_model fmac-coding    prompts/coding-system.txt
build_model fmac-reasoning prompts/reasoning-system.txt
build_model fmac-video     prompts/video-system.txt
build_model fmac-design    prompts/design-system.txt

echo "== [5/5] prove it answers =="
ANSWER=$(curl -s http://127.0.0.1:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"fmac-coding","messages":[{"role":"user","content":"Say READY and nothing else."}],"max_tokens":10}' \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])")
echo "model says: $ANSWER"

cat >> ENVIRONMENT.md <<EOF

## Intel setup results ($(date '+%Y-%m-%d %H:%M'))
- Machine RAM: ${RAM_GB}GB · Base model: ${BASE} (Ollama)
- Custom models created: fmac-base, fmac-coding, fmac-reasoning, fmac-video, fmac-design
- Endpoint: http://127.0.0.1:11434/v1/chat/completions
EOF

echo ""
echo "DONE. Your local language model is live."
echo "Talk to it:            $OLLAMA run fmac-coding"
echo "Full pipeline:         python3 orchestrator/pipeline.py \"your task\" --no-polish"
