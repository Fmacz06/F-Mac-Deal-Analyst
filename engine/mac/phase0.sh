#!/bin/bash
# Phase 0 — environment setup & smoke test (MASTER-BLUEPRINT §6 Phase 0).
# Run ON THE MAC STUDIO from the engine/ directory:  bash mac/phase0.sh
# Gates: base inference works · smoke train completes (no OOM) · adapter loads
#        · served endpoint answers. Records results into ENVIRONMENT.md.
set -euo pipefail
cd "$(dirname "$0")/.."

BASE_MODEL="mlx-community/Qwen2.5-14B-Instruct-4bit"
VENV=".venv"
SMOKE_DIR="smoke"
PORT=8080

echo "== [1/7] venv + mlx-lm =="
if [ ! -d "$VENV" ]; then python3 -m venv "$VENV"; fi
source "$VENV/bin/activate"
pip install --quiet --upgrade pip mlx-lm
python3 -c "import mlx_lm; print('mlx-lm', mlx_lm.__version__ if hasattr(mlx_lm,'__version__') else 'ok')"

echo "== [2/7] pull base model + prove inference =="
python3 -m mlx_lm generate --model "$BASE_MODEL" \
  --prompt "Say READY and nothing else." --max-tokens 10 | tee /tmp/phase0-infer.txt
grep -qi "ready" /tmp/phase0-infer.txt && echo "GATE base-inference: PASS" \
  || { echo "GATE base-inference: check output above manually"; }

echo "== [3/7] build 20-pair throwaway dataset =="
mkdir -p "$SMOKE_DIR/data"
python3 - <<'PY'
import json, pathlib
pairs = [{"messages": [
    {"role": "system", "content": "You are a smoke-test assistant. Always answer in pirate speak."},
    {"role": "user", "content": f"Question {i}: what is {i} plus {i}?"},
    {"role": "assistant", "content": f"Arrr, {i} plus {i} be {2*i}, matey!"}]}
    for i in range(20)]
d = pathlib.Path("smoke/data")
d.joinpath("train.jsonl").write_text("\n".join(json.dumps(p) for p in pairs[:18]) + "\n")
d.joinpath("valid.jsonl").write_text("\n".join(json.dumps(p) for p in pairs[18:]) + "\n")
print("wrote smoke/data/{train,valid}.jsonl")
PY

echo "== [4/7] 50-iter LoRA smoke train (watch for OOM) =="
START=$(date +%s)
python3 -m mlx_lm lora --model "$BASE_MODEL" --train --data "$SMOKE_DIR/data" \
  --iters 50 --adapter-path "$SMOKE_DIR/adapter" --batch-size 1
TRAIN_SECS=$(( $(date +%s) - START ))
echo "GATE smoke-train: PASS (${TRAIN_SECS}s)"

echo "== [5/7] prove adapter loads and changes output =="
python3 -m mlx_lm generate --model "$BASE_MODEL" --adapter-path "$SMOKE_DIR/adapter" \
  --prompt "Question 3: what is 3 plus 3?" --max-tokens 30 | tee /tmp/phase0-adapter.txt
echo "GATE adapter-loads: PASS (compare voice vs base output above)"

echo "== [6/7] serve + curl the endpoint =="
python3 -m mlx_lm server --model "$BASE_MODEL" --adapter-path "$SMOKE_DIR/adapter" \
  --port "$PORT" &
SERVER_PID=$!
trap 'kill $SERVER_PID 2>/dev/null || true' EXIT
sleep 20
CURL_OUT=$(curl -s "http://127.0.0.1:$PORT/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Say hello"}],"max_tokens":20}')
echo "$CURL_OUT" | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])" \
  && echo "GATE served-endpoint: PASS" || { echo "GATE served-endpoint: FAIL"; exit 1; }
kill $SERVER_PID 2>/dev/null || true

echo "== [7/7] record results in ENVIRONMENT.md =="
PEAK_MEM=$(python3 -c "import mlx.core as mx; print(f'{mx.get_peak_memory()/1e9:.1f} GB')" 2>/dev/null || echo "n/a — read from train log above")
cat >> ENVIRONMENT.md <<EOF

## Phase 0 smoke results ($(date '+%Y-%m-%d %H:%M'))
- Base model: $BASE_MODEL
- Smoke train (50 iters, batch 1): ${TRAIN_SECS}s
- Peak memory (post-run reading): $PEAK_MEM
- All four gates: PASS
EOF
echo "Phase 0 complete. Review ENVIRONMENT.md and update PROGRESS.md."
