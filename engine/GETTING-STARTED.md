# GETTING STARTED — your local LM, what it runs on, and what to download

Plain-language companion to RUNBOOK.md. This is the "what am I actually
installing" page.

## The core idea (so nothing is ambiguous)

The heart of this system is a **local, open-source language model that runs
entirely on your Mac Studio.** You download it once, you own it, it never
phones home, and it costs nothing to run. We then fine-tune it on YOUR
conversations and work product so it codes and reasons like you. Claude is
NOT the core — it is an optional polish layer bolted on top at the very end
(Phase 9), and the whole local loop works without it.

## The stack — three pieces, all local

| Piece | What it is | Size | Where it comes from |
|---|---|---|---|
| **Qwen2.5-14B-Instruct (4-bit)** | The open-source base model — the brain. Apache-2.0 license, yours outright. | ~8.3 GB, one-time download | Hugging Face: `mlx-community/Qwen2.5-14B-Instruct-4bit` |
| **MLX / mlx-lm** | Apple's machine-learning framework — trains the model on your data and serves it on localhost. Built for your Mac's chip. | ~a few hundred MB | `pip install mlx-lm` |
| **Your adapters** | The trained "you" layers the system produces — one per specialty (coding, reasoning, design). | MBs each | Created by training on your material (Phase 3) |

Optional, only if/when wanted:
- `mlx-community/Qwen2.5-Coder-14B-Instruct-4bit` (~8.3 GB) — the escalation
  base if the Phase 5 gate says raw code quality is thin (§2 Correction 2).
- `pip install anthropic` + an API key — ONLY for the Claude polish layer and
  the A/B comparison side. Skip it and the local engine still runs fully.

## Requirements

- Mac Studio (or any Apple Silicon Mac), 64 GB unified memory recommended
- macOS with Python 3.9+ (`python3 --version` — already on your machine)
- ~20 GB free disk (model + venv + training artifacts)
- Internet for the ONE-TIME model download; nothing after that

## The one command that downloads everything

From the `engine/` folder on your Mac:

```bash
bash mac/phase0.sh
```

That single script:
1. creates an isolated Python environment (`.venv/`)
2. installs **mlx-lm** (the training/serving engine)
3. downloads **Qwen2.5-14B-Instruct-4bit** from Hugging Face (~8.3 GB — the
   long step; grab a coffee)
4. proves the model answers on your machine (base inference gate)
5. runs a tiny 50-step practice training on throwaway data to prove your Mac
   can train without running out of memory (smoke-train gate)
6. proves the trained adapter loads and changes the model's voice (adapter gate)
7. starts the local server on `http://127.0.0.1:8080` and confirms it answers
   a request (serving gate)

Four PASSes = your machine is a proven, self-contained AI training rig.
Results get written into `ENVIRONMENT.md` automatically.

## What happens after that (the short version)

1. **You feed it your material** — drop `.md` exports of your real work
   conversations into `corpus/coding/`.
2. **The pipeline turns them into training data** — `make inventory` counts
   what you have; `make convert` produces the training files plus a 20-example
   sample for you to sanity-check ("does this sound like me?").
3. **You train** — `bash mac/train.sh coding 600` (~20–40 min on your Mac).
   Out comes YOUR coding adapter.
4. **You run it** — `bash mac/serve.sh adapters/coding/run-<timestamp>` and
   your specialist is live on localhost, answering like you.
5. **You judge it blind** against your current workflow (the A/B harness
   handles the blinding and the scoring math), and the decision gate tells us
   GO / fix-the-data / try-the-Coder-base.

Full per-phase details: `RUNBOOK.md`. The blueprint itself: `MASTER-BLUEPRINT.md`.
