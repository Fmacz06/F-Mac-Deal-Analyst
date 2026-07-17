#!/bin/bash
# Reorganize the whole fmac menu into a clean FAST (7B) / SMART (14B) scheme,
# and upgrade the coding models to the REAL coding specialist (Qwen2.5-Coder).
# Deletes the old confusingly-named models at the end.
#
# Final menu:
#   fmac-fast          fmac-smart          (general)
#   fmac-fast-coding   fmac-smart-coding   (Qwen2.5-Coder — built for code)
#   fmac-fast-reasoning fmac-smart-reasoning
#   fmac-fast-design   fmac-smart-design
#   fmac-fast-video    fmac-smart-video
#   (fmac-vision stays as-is)
#
# Run from engine/ AFTER the vision download finishes:  bash mac/organize-models.sh
set -euo pipefail
cd "$(dirname "$0")/.."

if command -v ollama >/dev/null 2>&1; then
  OLLAMA="ollama"
elif [ -x "/Applications/Ollama.app/Contents/Resources/ollama" ]; then
  OLLAMA="/Applications/Ollama.app/Contents/Resources/ollama"
else
  echo "Ollama not found — run mac/intel-setup.sh first"; exit 1
fi

if ! curl -s http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
  echo "starting Ollama (needed only while building)..."
  [ -d "/Applications/Ollama.app" ] && open -a Ollama || ("$OLLAMA" serve >/tmp/ollama.log 2>&1 &)
  for i in 1 2 3 4 5 6; do
    curl -s http://127.0.0.1:11434/api/tags >/dev/null 2>&1 && break
    sleep 5
  done
fi

FRAMEWORK="prompts/fmac-framework-lite.md"
[ -f "$FRAMEWORK" ] || { echo "missing $FRAMEWORK"; exit 1; }
mkdir -p /tmp/fmac-modelfiles

echo "== making sure the base models are present (downloads only what's missing) =="
"$OLLAMA" pull qwen2.5:7b-instruct
"$OLLAMA" pull qwen2.5:14b-instruct
echo "== downloading the real coding specialist, both sizes (~14 GB, the long part) =="
"$OLLAMA" pull qwen2.5-coder:7b
"$OLLAMA" pull qwen2.5-coder:14b

# build one model: name, base, optional specialty-prompt file
build () {
  local name="$1" base="$2" specialty="$3"
  local mf="/tmp/fmac-modelfiles/$name.Modelfile"
  {
    echo "FROM $base"
    echo "PARAMETER num_ctx 8192"
    printf 'SYSTEM """'
    cat "$FRAMEWORK"
    [ -n "$specialty" ] && { printf '\n\n---\n\nSPECIALTY:\n'; cat "$specialty"; }
    printf '"""\n'
  } > "$mf"
  "$OLLAMA" create "$name" -f "$mf"
  echo "  built: $name"
}

echo "== building the clean FAST (7B) set =="
build fmac-fast            qwen2.5:7b-instruct        ""
build fmac-fast-coding     qwen2.5-coder:7b           prompts/coding-system.txt
build fmac-fast-reasoning  qwen2.5:7b-instruct        prompts/reasoning-system.txt
build fmac-fast-design     qwen2.5:7b-instruct        prompts/design-system.txt
build fmac-fast-video      qwen2.5:7b-instruct        prompts/video-system.txt

echo "== building the clean SMART (14B) set =="
build fmac-smart           qwen2.5:14b-instruct       ""
build fmac-smart-coding    qwen2.5-coder:14b          prompts/coding-system.txt
build fmac-smart-reasoning qwen2.5:14b-instruct       prompts/reasoning-system.txt
build fmac-smart-design    qwen2.5:14b-instruct       prompts/design-system.txt
build fmac-smart-video     qwen2.5:14b-instruct       prompts/video-system.txt

echo "== removing the old, confusingly-named models =="
for old in fmac-base fmac-coding fmac-reasoning fmac-design fmac-video \
           fmac-base-14b fmac-coding-14b fmac-reasoning-14b fmac-design-14b fmac-video-14b; do
  "$OLLAMA" rm "$old" 2>/dev/null && echo "  removed: $old" || true
done

echo ""
echo "DONE. Clean menu is ready. In Msty, start a NEW chat and type 'fmac' —"
echo "you'll see fmac-fast-* (quick) and fmac-smart-* (sharper), coding on the"
echo "real Qwen2.5-Coder. fmac-vision is your screenshot model."
