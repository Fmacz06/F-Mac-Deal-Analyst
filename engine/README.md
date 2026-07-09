# Local AI Reasoning & Creation Engine
### AP Capital / F Mac · Project root

A local specialist AI system on the Mac Studio (64GB, Apple Silicon): domain-specialized LoRA adapters on a shared Qwen2.5-14B base, trained on F Mac's own methodology, served via MLX, with Claude as the orchestration layer on top.

## The two documents

| File | What it is | Who reads it |
|---|---|---|
| [`MASTER-BLUEPRINT.md`](MASTER-BLUEPRINT.md) | Source of truth — mission, architecture, dataset spec, phased plan (0–9), risks, VERIFIED ledger. Supersedes the original handoff doc. | The executor, every session. |
| [`PROMPT-PACK.md`](PROMPT-PACK.md) | Copy-paste prompts, one per phase, in order. Self-contained — no memory of prior sessions needed. | F Mac — paste one per session. |

## How to run this (F Mac)

1. Clone (or open) this repo on the Mac Studio — **this repo is the project root**. All state files live here.
2. Start a fresh chat with the executor and make sure `MASTER-BLUEPRINT.md` is in the project folder or attached.
3. Paste **PROMPT K** (kickoff) from `PROMPT-PACK.md`. Then one phase prompt per session, in order: 0 → 1 → 2 → 3 → 4 → 5. Phase 5 is the decision gate; phases 6–9 unlock only on GO.
4. Your touchpoints are marked **[YOU]** in the prompt pack — everything else is the executor's job. Total hands-on time through Phase 5: roughly one hour.

## State files (maintained by the executor, §0 rule 4)

- [`PROGRESS.md`](PROGRESS.md) — phase tracker, per-phase reports, run logs, results tables, VERIFIED ledger additions.
- [`LESSONS.md`](LESSONS.md) — what was learned the hard way; final RUN REPORT + PROTOCOL PATCH lands here at Phase 9.
- [`ENVIRONMENT.md`](ENVIRONMENT.md) — machine facts: versions, paths, peak memory, quirks. Filled in during Phase 0.

## What never gets pushed

Training data is F Mac's own material — the mission requires that **no corpus data leaves the machine**. `.gitignore` blocks `data/`, adapters, model files, and sample/provenance outputs. This repo carries documents, code, and state files only. If a state file needs to reference corpus content, reference it by filename and stats, never by content.
