#!/bin/bash
# Phase 3 (and 6/7) — LoRA training run (MASTER-BLUEPRINT §6 Phase 3).
# Run ON THE MAC STUDIO from engine/:  bash mac/train.sh [adapter-name] [iters]
# Versions every run (never overwrites a previous adapter) and appends the
# run config to PROGRESS.md. OOM ladder: --batch-size 1 first (default here),
# then reduce --num-layers via NUM_LAYERS env var.
set -euo pipefail
cd "$(dirname "$0")/.."
source .venv/bin/activate

BASE_MODEL="${BASE_MODEL:-mlx-community/Qwen2.5-14B-Instruct-4bit}"
NAME="${1:-coding}"
ITERS="${2:-600}"
BATCH="${BATCH_SIZE:-1}"
LAYERS="${NUM_LAYERS:-16}"
DATA_DIR="${DATA_DIR:-data}"
RUN_ID="$(date '+%Y%m%d-%H%M%S')"
ADAPTER_DIR="adapters/${NAME}/run-${RUN_ID}"
mkdir -p "$ADAPTER_DIR"

echo "Training ${NAME} adapter: ${ITERS} iters, batch ${BATCH}, ${LAYERS} layers"
echo "Data: ${DATA_DIR} · Output: ${ADAPTER_DIR}"
echo "Watch validation loss: still falling at ${ITERS} -> continuation run;"
echo "flat/rising while train falls -> overfitting, stop earlier."

python3 -m mlx_lm lora \
  --model "$BASE_MODEL" \
  --train \
  --data "$DATA_DIR" \
  --iters "$ITERS" \
  --batch-size "$BATCH" \
  --num-layers "$LAYERS" \
  --adapter-path "$ADAPTER_DIR" \
  2>&1 | tee "$ADAPTER_DIR/train.log"

FINAL_LOSSES=$(grep -Ei "val(idation)? loss" "$ADAPTER_DIR/train.log" | tail -3 || echo "see train.log")
cat >> PROGRESS.md <<EOF

### Training run ${RUN_ID} (${NAME})
- Command: mlx_lm lora --model ${BASE_MODEL} --train --data ${DATA_DIR} --iters ${ITERS} --batch-size ${BATCH} --num-layers ${LAYERS}
- Adapter: ${ADAPTER_DIR}
- Last validation-loss lines:
\`\`\`
${FINAL_LOSSES}
\`\`\`
EOF
echo "Done. Adapter saved to ${ADAPTER_DIR}; config logged in PROGRESS.md."
echo "Next: bash mac/probe.sh ${ADAPTER_DIR}"
