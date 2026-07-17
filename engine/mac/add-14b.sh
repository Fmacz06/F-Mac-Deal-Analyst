#!/bin/bash
# Add the 14B versions ALONGSIDE the 7B ones (does not replace them).
# Creates fmac-coding-14b, fmac-reasoning-14b, etc. — smarter, ~half the
# speed of 7B on a CPU. Same condensed framework + 8k context.
# Run from engine/:   bash mac/add-14b.sh
set -euo pipefail
cd "$(dirname "$0")/.."

OLLAMA="ollama"
command -v ollama >/dev/null 2>&1 || OLLAMA="/Applications/Ollama.app/Contents/Resources/ollama"
[ -x "$OLLAMA" ] || { echo "Ollama not found — run mac/intel-setup.sh first"; exit 1; }

# the build step needs the ollama server up; launch the app if it's not
if ! curl -s http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
  echo "starting Ollama (needed only while building models)..."
  [ -d "/Applications/Ollama.app" ] && open -a Ollama || ("$OLLAMA" serve >/tmp/ollama.log 2>&1 &)
  for i in 1 2 3 4 5 6; do
    curl -s http://127.0.0.1:11434/api/tags >/dev/null 2>&1 && break
    sleep 5
  done
fi

BASE="qwen2.5:14b-instruct"
FRAMEWORK="prompts/fmac-framework-lite.md"
[ -f "$FRAMEWORK" ] || { echo "missing $FRAMEWORK"; exit 1; }
mkdir -p /tmp/fmac-modelfiles

echo "== downloading the 14B base (~9 GB, one-time — this is the long part) =="
"$OLLAMA" pull "$BASE"

build () {
  local name="$1" specialty="$2"
  local mf="/tmp/fmac-modelfiles/$name.Modelfile"
  {
    echo "FROM $BASE"
    echo "PARAMETER num_ctx 8192"
    printf 'SYSTEM """'
    cat "$FRAMEWORK"
    if [ -n "$specialty" ]; then
      printf '\n\n---\n\nSPECIALTY:\n'
      cat "$specialty"
    fi
    printf '"""\n'
  } > "$mf"
  "$OLLAMA" create "$name" -f "$mf"
  echo "  created: $name"
}

echo "== building the 14B fmac models =="
build fmac-base-14b    ""
build fmac-coding-14b    prompts/coding-system.txt
build fmac-reasoning-14b prompts/reasoning-system.txt
build fmac-video-14b     prompts/video-system.txt
build fmac-design-14b    prompts/design-system.txt

echo ""
echo "DONE. You now have BOTH:"
echo "  fmac-coding      (7B  — faster,  ~3 words/sec)"
echo "  fmac-coding-14b  (14B — smarter, ~half the speed)"
echo "In Msty, start a NEW chat, pick a -14b model, and compare."
echo "You can quit the Ollama app again after this (Msty runs its own engine)."
