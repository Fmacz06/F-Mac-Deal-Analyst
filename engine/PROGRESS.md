# PROGRESS — Local AI Reasoning & Creation Engine

> Maintained by the executor per MASTER-BLUEPRINT.md §0 rule 4. Updated at the end of every session, before stopping. State lives here, never in a model's head.

## Phase tracker

| Phase | Name | Status | Session date | Gates |
|---|---|---|---|---|
| K | Kickoff | ✅ blueprint read, project root = `engine/` | 2026-07-07 | — |
| 0 | Environment setup & smoke test | 🟡 script ready (`mac/phase0.sh`) — must run on the Mac Studio | — | 4 gates checked in-script |
| 1 | Corpus export & inventory | ⬜ awaiting corpus in `corpus/coding/` | — | tool ready (`inventory/`) |
| 2 | JSONL conversion pipeline | 🟡 built + 20 unit tests pass — F Mac spot-check pending | 2026-07-07 | 3 of 4 ✅ |
| 3 | First LoRA training run | ⬜ script ready (`mac/train.sh`, `mac/probe.sh`) — needs Phase 2 GO | — | — |
| 4 | Serve + blind A/B test | ⬜ harness ready (`ab/ab_test.py`) — needs Phase 3 | — | — |
| 5 | **DECISION GATE** | ⬜ verdict logic built into `ab_test.py unblind` | — | — |
| 6 | Reasoning specialist | 🔒 locked until Phase 5 GO (no new code needed) | — | — |
| 7 | Design specialist | 🔒 locked until Phase 5 GO (no new code needed) | — | — |
| 8 | Router build | 🟡 built ahead: 13 unit tests + 51-prompt eval 100% — live-fallback gate pending | 2026-07-07 | 3 of 4 ✅ |
| 9 | Claude integration + final review | 🟡 built ahead: HandUp + polish prompts + pipeline, 9 tests — smoke run + sign-off pending | 2026-07-07 | 0 of 2 ✅ |

Status legend: ⬜ not started · 🟡 in progress · ✅ gates passed · ❌ stopped (see report) · 🔒 locked

> Note on 8/9 being ahead of sequence: the software for those phases was built
> and unit-tested during the cloud build session because it has no dependency
> on training results. Their GATES still run in order — nothing ships before
> the Phase 5 GO.

## [ASSUMED] sign-off status (blueprint §11)

| Item | Status |
|---|---|
| A1 — Skip Qwen3 for first run | ⬜ awaiting F Mac |
| A2 — Coder-14B is the Phase 5 ESCALATE move | ⬜ awaiting F Mac |
| A3 — GO thresholds: fidelity ≥3.5, correctness ≥3.0 | ⬜ awaiting F Mac |
| A4 — 300–1,000 pair target, 150 hard floor | ⬜ awaiting F Mac |
| A5 — Router v1 design; adapter swap by restart | ⬜ awaiting F Mac |
| A6 — A/B mix 4 review / 3 architecture / 3 implementation | ⬜ awaiting F Mac |
| A7 — STARGATE recommendations queued, not applied | ⬜ awaiting F Mac |

None block Phases 0–2. A3/A6 must be confirmed before Phase 4 scoring; A2/A3 before the Phase 5 call.

## VERIFIED ledger — additions

> Blueprint §12 entries (stamped 2026-07-06) are trusted as-is; do not re-research. New facts verified during execution get stamped here.

| Fact | Status | Source | Date |
|---|---|---|---|
| Claude polish layer: `anthropic` SDK, model `claude-opus-4-8`, adaptive thinking, no sampling params | ✅ | claude-api reference (2026-06 cache) | 2026-07-07 |
| `mlx_lm` CLI is invoked as `python3 -m mlx_lm <subcommand>` on current releases | ✅ | mlx-lm docs | 2026-07-07 |

## Phase reports

### Cloud build session — 2026-07-07 (pre-Phase-0 software build)

All phase software was built and unit-tested in a cloud Linux session (MLX is
Apple-Silicon-only, so hardware gates are packaged as `mac/*.sh` scripts):

- **Converter (P2):** `converter/convert.py` — 20 unit tests (malformed md,
  empty, giant, unicode, PII, dedup, schema, seeded split) all pass. Dry run
  on a realistic STARGATE-style export produced clean pairs.
- **Inventory (P1):** `inventory/inventory.py` — yield estimate, stale/PII
  flags, 150-pair floor enforced with STOP exit.
- **A/B harness (P4/P5):** `ab/ab_test.py` collect/blind/unblind — 6 tests;
  GO/DIAGNOSE/ESCALATE verdicts all covered.
- **Router (P8):** `router/router.py` — 13 tests; 51-prompt seed eval 100%
  (gate ≥90%). Live local-LLM-fallback eval still to run on the Mac.
- **Orchestrator (P9):** `orchestrator/` HandUp + polish prompts + pipeline —
  9 tests, Claude layers stubbed.
- Repo docs: GETTING-STARTED.md, RUNBOOK.md, corpus/ bin with README.

**FRICTION:**
1. Blueprint assumes the executor session runs on the Mac; this one ran in a
   cloud container — hardware gates became scripted handoffs. Blueprint should
   state the execution environment per phase.
2. §6-P2 doesn't specify export turn-marker formats; converter handles the
   common ones and reports unparsed files rather than guessing.
3. Non-conversation docs (Protocol v3.0 itself) yield zero pairs through the
   turn parser — Phase 1 must decide: hand-convert to Q&A or use as
   system-prompt material only.
4. `**User:**` bold-with-colon headers left stray `**` in extracted text —
   caught by a live dry run, fixed, regression-tested. Unit tests alone missed
   it; keep the dry-run habit.
