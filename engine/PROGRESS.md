# PROGRESS — Local AI Reasoning & Creation Engine

State file per MASTER-BLUEPRINT §0.4. Updated at every phase boundary.

## Build status (updated 2026-07-07, cloud build session)

All software components were built and unit-tested in a cloud session (Linux —
MLX cannot run there). Hardware-bound gates run on the Mac Studio via the
`mac/*.sh` scripts. See RUNBOOK.md for exactly what to run per phase.

| Phase | Component | Built | Tested | Hardware gate |
|---|---|---|---|---|
| 0 | `mac/phase0.sh` (venv, model pull, smoke train, serve check) | ✅ | script reviewed; gates run on Mac | ⬜ run on Mac Studio |
| 1 | `inventory/inventory.py` (corpus inventory + 150-pair floor) | ✅ | ✅ (via converter parser tests) | ⬜ needs corpus |
| 2 | `converter/convert.py` (md → JSONL pipeline, reusable) | ✅ | ✅ 19/19 unit tests | ⬜ F Mac spot-check of sample-20.md |
| 3 | `mac/train.sh` + `mac/probe.sh` (versioned runs, loss logging) | ✅ | script reviewed | ⬜ run on Mac Studio |
| 4 | `ab/ab_test.py` (collect / blind / unblind) | ✅ | ✅ 6/6 unit tests | ⬜ F Mac blind scoring |
| 5 | Decision-gate logic (GO/DIAGNOSE/ESCALATE in `unblind`) | ✅ | ✅ all three verdicts tested | ⬜ F Mac GO call |
| 6–7 | Replication = same tools, different `--source`/system prompt | ✅ (no new code) | — | ⬜ |
| 8 | `router/router.py` + eval harness | ✅ | ✅ 13/13 unit · 51/51 eval (100%, gate ≥90%) | ⬜ live eval w/ local LLM fallback |
| 9 | `orchestrator/` (HandUp, polish prompts, pipeline) | ✅ | ✅ 9/9 unit tests | ⬜ 5-task smoke + F Mac sign-off |

## Inventory table (Phase 1 — pending corpus)

*Run `make inventory SOURCE=<corpus-dir>` and paste the table here.*

## Training runs (Phase 3 — appended automatically by mac/train.sh)

## A/B results (Phase 4 — produced by `ab_test.py unblind`)

---

## VERIFIED ledger (§12 — checked once = trusted; do not re-research)

| Fact | Status | Source | Date |
|---|---|---|---|
| `mlx_lm.lora --model --train --data --iters` syntax current; mlx-lm ~0.30.6 | ✅ | mlx-lm LORA docs | 2026-07-06 |
| `mlx-community/Qwen2.5-14B-Instruct-4bit` exists, 8.31 GB | ✅ | Hugging Face | 2026-07-06 |
| `mlx-community/Qwen2.5-Coder-14B-Instruct-4bit` exists | ✅ | Hugging Face | 2026-07-06 |
| `Qwen/Qwen3-14B-MLX-4bit` exists (hybrid thinking mode) | ✅ | Hugging Face | 2026-07-06 |
| Fused MLX ≠ Ollama-ready; Ollama path = fuse `--de-quantize` → llama.cpp → GGUF | ✅ | ml-explore discussions | 2026-07-06 |
| `mlx_lm.server` serves OpenAI-compatible endpoint, supports `--adapter-path` | ✅ | mlx-lm SERVER docs | 2026-07-06 |
| Dataset: `train.jsonl` required, `valid.jsonl` optional-but-reports-loss; chat format; final message = completion | ✅ | mlx-lm LORA docs | 2026-07-06 |
| Claude polish layer: `anthropic` SDK, model `claude-opus-4-8`, adaptive thinking | ✅ | claude-api reference (skill), 2026-06 cache | 2026-07-07 |
