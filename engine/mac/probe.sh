#!/bin/bash
# Phase 3 gate — 3 probe prompts, base vs adapter side by side (§6 Phase 3).
# Includes 1 OFF-corpus probe (general-competence check, §8 overfitting guard).
# Run ON THE MAC STUDIO from engine/:  bash mac/probe.sh adapters/coding/run-XXXX
set -euo pipefail
cd "$(dirname "$0")/.."
source .venv/bin/activate

BASE_MODEL="${BASE_MODEL:-mlx-community/Qwen2.5-14B-Instruct-4bit}"
ADAPTER="${1:?usage: mac/probe.sh <adapter-path>}"
OUT="probes-$(date '+%Y%m%d-%H%M%S').md"

PROBES=(
  "Review this function and tell me how you'd approach fixing it:\n\`\`\`python\ndef retry(fn, n=3):\n    for _ in range(n):\n        try: return fn()\n        except Exception: pass\n\`\`\`"
  "I need to add a rent-roll importer to the deal analyzer. Walk me through how you'd start."
  "OFF-CORPUS: Explain how photosynthesis works in three sentences."
)

echo "# Probe comparison — $ADAPTER vs base ($(date '+%Y-%m-%d %H:%M'))" > "$OUT"
i=0
for p in "${PROBES[@]}"; do
  i=$((i+1))
  echo "probe $i..."
  {
    echo -e "\n---\n\n## Probe $i\n\n**PROMPT:** $p\n\n### Base model\n"
    python3 -m mlx_lm generate --model "$BASE_MODEL" --prompt "$(echo -e "$p")" --max-tokens 400
    echo -e "\n### With adapter\n"
    python3 -m mlx_lm generate --model "$BASE_MODEL" --adapter-path "$ADAPTER" \
      --prompt "$(echo -e "$p")" --max-tokens 400
  } >> "$OUT"
done
echo "Wrote $OUT — check for methodology voice (test-first instinct,"
echo "Clear/Fuzzy/Missing framing) vs base, and that the OFF-corpus probe"
echo "still answers sensibly (no lost general competence)."
