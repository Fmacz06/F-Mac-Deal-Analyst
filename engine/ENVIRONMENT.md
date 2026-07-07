# ENVIRONMENT — Local AI Reasoning & Creation Engine

State file per MASTER-BLUEPRINT §0.4. `mac/phase0.sh` appends smoke results here.

## Target hardware (GIVEN)
- Mac Studio, 64GB unified memory, Apple Silicon
- MLX framework (`mlx-lm` in `.venv`)
- Base model: `mlx-community/Qwen2.5-14B-Instruct-4bit` (8.31 GB)

## Build environment note
The software layer (converter, router, A/B harness, orchestrator) was built and
unit-tested on Linux/Python 3.11 — everything except MLX itself is stdlib-only
Python and runs identically on the Mac (Python 3.9+). The Claude layer needs
`pip install anthropic` and an `ANTHROPIC_API_KEY` (or `ant auth login`).

## Quirks / gotchas
- `mlx_lm` CLI form is `python3 -m mlx_lm <subcommand>` (lora/generate/server)
  on current versions; older docs show `mlx_lm.lora` dotted entry points.
  The mac/ scripts use the module form.
- OOM ladder (§6 Phase 3): `--batch-size 1` first, then reduce `--num-layers`
  (set `NUM_LAYERS=8 bash mac/train.sh ...`). Close everything else during
  training; peak memory is recorded below after each Phase 0 run.
- `mlx_lm server` takes ~15–25s to load the 14B base before answering.

## Phase 0 smoke results
*(appended by mac/phase0.sh)*
