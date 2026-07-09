# ENVIRONMENT — Local AI Reasoning & Creation Engine

> Filled in during Phase 0 and kept current by the executor (MASTER-BLUEPRINT.md §0 rule 4). Machine facts only — read this before touching the machine.

## Hardware (GIVEN — blueprint §11)

- Mac Studio, Apple Silicon, 64GB unified memory
- Framework: MLX

## Software (Phase 0 fills in — `mac/phase0.sh` appends automatically)

| Item | Value |
|---|---|
| macOS version | *(Phase 0)* |
| Python version | *(Phase 0)* |
| venv path | `engine/.venv` *(created by mac/phase0.sh)* |
| mlx-lm version | *(Phase 0)* |
| Base model on disk | `mlx-community/Qwen2.5-14B-Instruct-4bit` — *(path, Phase 0)* |

## Benchmarks (Phase 0 fills in; updated when real runs beat them)

| Metric | Value |
|---|---|
| Smoke train (50 iters) wall time | *(Phase 0)* |
| Peak memory during smoke train | *(Phase 0)* |
| Base inference tok/s | *(Phase 0)* |
| First real train (600 iters) wall time | *(Phase 3)* |
| Peak memory during real train | *(Phase 3)* |

## Quirks, paths, gotchas

> Every environment surprise goes here — flags that had to change, paths that weren't where docs said, memory-pressure behavior. This is the file that saves the next session an afternoon.

- `mlx_lm` CLI form is `python3 -m mlx_lm <subcommand>` (lora/generate/server)
  on current releases; older docs show dotted entry points (`mlx_lm.lora`).
  The `mac/*.sh` scripts already use the module form.
- OOM ladder (§6-P3): `--batch-size 1` first (train.sh default), then reduce
  layers via `NUM_LAYERS=8 bash mac/train.sh ...`.
- `mlx_lm server` takes ~15–25s to load the 14B base before answering; the
  phase0 script waits 20s before its curl gate.
- Software layer (converter/router/ab/orchestrator) is stdlib-only Python 3.9+
  — runs identically on macOS and Linux. Only training/serving needs MLX.
  Claude layer additionally needs `pip install anthropic` + credentials.
