# RUNBOOK — what to run, per phase, on the Mac Studio

Companion to MASTER-BLUEPRINT.md. Everything below runs from the `engine/`
directory on the Mac Studio. **[YOU]** marks F Mac's touchpoints — nothing
else goes to him (§9).

Everything code-shaped is already built and unit-tested (`make test` — 47
tests, no dependencies beyond Python 3.9+). The steps below are the
hardware-bound and human-gate parts.

## One-time
```bash
git clone <this repo> && cd F-Mac-Deal-Analyst/engine
make test                      # sanity: all suites green on the Mac too
```

## Phase 0 — environment + smoke test (~30 min, mostly downloads)
```bash
bash mac/phase0.sh
```
Pulls the base model, proves inference, runs a 50-iter smoke train on a
throwaway pirate-speak dataset, proves the adapter loads and changes output,
serves it, and curls the endpoint. Appends results to `ENVIRONMENT.md`.
All four §6-P0 gates are checked in-script.

## Phase 1 — corpus inventory
**[YOU]** Drop the coding corpus (STARGATE sessions, Protocol v3.0, best code
reviews/dev conversations as `.md` exports) into a folder, e.g. `corpus/coding/`.
```bash
make inventory SOURCE=corpus/coding      # writes inventory.md, exits 2 if < 150 pairs
```
Paste the table into `PROGRESS.md`. **[YOU]** 5-min review: confirm
stale-flagged files are updated/cut and nothing sensitive is in scope.
Files flagged `NO-CONVERSATION-MARKERS` (e.g. the Protocol doc itself) yield
no pairs — decide whether to hand-convert or keep as system-prompt material.

## Phase 2 — convert to JSONL
```bash
make convert SOURCE=corpus/coding OUT=data
```
Produces `data/train.jsonl`, `data/valid.jsonl`, `data/sample-20.md`,
`data/stats.md`, `data/provenance.json`.
**[YOU]** 10-min spot-check of `data/sample-20.md` — accuracy of voice. GO or FIX.

## Phase 3 — train
```bash
bash mac/train.sh coding 600           # versioned under adapters/coding/run-<ts>
bash mac/probe.sh adapters/coding/run-<ts>   # 3 probes incl. 1 off-corpus, base vs adapter
```
Loss decision rules and the OOM ladder are printed by the script and logged
to `PROGRESS.md` automatically. Never deletes a previous adapter.

## Phase 4 — serve + blind A/B
**[YOU]** Put 10 real backlog tasks (4 review / 3 architecture / 3 implementation)
into `ab/tasks.json` — template at `ab/tasks.template.json`.
```bash
bash mac/serve.sh adapters/coding/run-<ts> &   # local specialist on :8080
pip install anthropic                           # once, for the Claude side
python3 ab/ab_test.py collect --tasks ab/tasks.json
python3 ab/ab_test.py blind
```
**[YOU]** ~45 min: score `ab/runs/scoring-doc.md` blind (1–5 on fidelity /
correctness / usefulness), fill `ab/runs/scores.json`. Do NOT open
`blind_key.json` until done. Then:
```bash
python3 ab/ab_test.py unblind --scores ab/runs/scores.json
```

## Phase 5 — decision gate
`unblind` already applies A3 (GO at fidelity ≥ 3.5 AND correctness ≥ 3.0) and
prints GO / DIAGNOSE / ESCALATE with the evidence table (`ab/runs/results.md`).
**[YOU]** The GO/no-go call is yours.
- ESCALATE path: `BASE_MODEL=mlx-community/Qwen2.5-Coder-14B-Instruct-4bit bash mac/train.sh coding-coder 600` then re-A/B.

## Phase 6 — reasoning specialist (replication)
Same loop, different inputs:
```bash
make inventory SOURCE=corpus/reasoning
make convert SOURCE=corpus/reasoning OUT=data-reasoning SYSTEM_PROMPT=prompts/reasoning-system.txt
DATA_DIR=data-reasoning bash mac/train.sh reasoning 600
python3 ab/ab_test.py collect --tasks ab/tasks-reasoning.json --route reasoning
```
**[YOU]** select the corpus (Thinking Bin / Quarantine Tank exports, book
material), spot-check, supply 10 "help me think through X" tasks, blind score.

## Phase 7 — design specialist
Open with the feasibility check — `make inventory SOURCE=corpus/design` — the
150-pair floor IS the feasibility gate (sketches are images; only textual
design reasoning counts). If it fails, STOP and pick an option
(transcribe annotations / defer to VLM) before building.

## Phase 8 — router (already built; live-gate it)
```bash
python3 router/eval/eval_router.py            # offline: 51/51 = 100% (gate ≥90%)
bash mac/serve.sh base &                      # then the live check:
python3 router/eval/eval_router.py --live     # uses the real local-LLM fallback
```
Per §3.3, replace the seed eval prompts with real usage from the routing log
(`router/routing-log.jsonl`) as it accumulates.

## Phase 9 — full pattern end-to-end
```bash
bash mac/serve.sh adapters/coding/run-<ts> &
export ANTHROPIC_API_KEY=...                   # or: ant auth login
python3 orchestrator/pipeline.py "Review this diff: ..." --json
```
Run 5 real tasks through it (the executor clicks through first — F Mac is
never the first to see it break).
**[YOU]** Gate-6-style review: works, gates passed, performance acceptable,
clear to adopt. On sign-off, append the RUN REPORT + PROTOCOL PATCH to
`LESSONS.md`. **System shipped.**
