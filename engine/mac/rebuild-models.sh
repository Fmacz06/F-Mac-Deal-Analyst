#!/bin/bash
# Rebuild the fmac-* models with the F Mac Workflow & Interaction Framework
# baked in as the foundation, plus each model's specialty on top.
# Does NOT re-download the base model — reuses what intel-setup.sh already pulled.
#
# Run from engine/:   bash mac/rebuild-models.sh
set -euo pipefail
cd "$(dirname "$0")/.."

OLLAMA="ollama"
command -v ollama >/dev/null 2>&1 || OLLAMA="/Applications/Ollama.app/Contents/Resources/ollama"
[ -x "$OLLAMA" ] || { echo "Ollama not found — run mac/intel-setup.sh first"; exit 1; }

# reuse whatever base intel-setup.sh installed
RAM_GB=$(( $(sysctl -n hw.memsize) / 1073741824 ))
if [ "$RAM_GB" -ge 14 ]; then BASE="qwen2.5:7b-instruct"; else BASE="qwen2.5:3b-instruct"; fi

FRAMEWORK="prompts/fmac-framework.md"
[ -f "$FRAMEWORK" ] || { echo "missing $FRAMEWORK"; exit 1; }
mkdir -p /tmp/fmac-modelfiles

build () {
  local name="$1" specialty="$2"
  local mf="/tmp/fmac-modelfiles/$name.Modelfile"
  {
    echo "FROM $BASE"
    echo "PARAMETER num_ctx 32768"        # big whiteboard: framework barely dents it (64GB RAM)
    printf 'SYSTEM """'
    cat "$FRAMEWORK"
    if [ -n "$specialty" ]; then
      printf '\n\n---\n\nSPECIALTY FOR THIS MODEL:\n'
      cat "$specialty"
    fi
    printf '"""\n'
  } > "$mf"
  "$OLLAMA" create "$name" -f "$mf"
  echo "  rebuilt: $name"
}

echo "Baking the F Mac Framework into all models (base: $BASE)..."
build fmac-base    ""
build fmac-coding    prompts/coding-system.txt
build fmac-reasoning prompts/reasoning-system.txt
build fmac-video     prompts/video-system.txt
build fmac-design    prompts/design-system.txt

echo ""
echo "DONE. All five models now run on the framework."
echo "Every model follows your operating rules; each also has its specialty."
echo "Talk to it in the Ollama app (pick any fmac- model) or:"
echo "  $OLLAMA run fmac-coding"
