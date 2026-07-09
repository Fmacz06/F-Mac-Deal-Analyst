# PROMPT PACK — Local AI Reasoning & Creation Engine
### Companion to MASTER-BLUEPRINT.md · Prepared July 6, 2026

**How to use (F Mac):** one prompt per session, in order. Start a fresh chat with Opus, make sure `MASTER-BLUEPRINT.md` is in the project folder (or attached), paste the phase prompt, let him run. Each prompt is self-contained — he needs no memory of prior sessions; state carries in `PROGRESS.md` / `LESSONS.md` / `ENVIRONMENT.md`. Where a prompt says **[YOU]**, that's your touchpoint — everything else is his.

---

## PROMPT K — Kickoff (run once, before Phase 0)

```
You are the executor on the Local AI Reasoning & Creation Engine for F Mac / AP Capital.

Read MASTER-BLUEPRINT.md in the project folder top to bottom before doing anything.
It is the source of truth and supersedes any prior handoff doc you may have seen —
two technical claims from the old doc were corrected after verification (§2).

Non-negotiables:
- §0 operating rules apply to every session.
- One phase per session. Never roll into the next phase.
- The VERIFIED ledger (§12) is trusted — do not re-research stamped facts.
- F Mac's touchpoints are listed per phase — never assign him anything else.
- Every phase report ends with a FRICTION section.

Confirm: (1) you've read the blueprint, (2) the project root you'll use for all
state files, (3) any [ASSUMED] item in §11 that blocks Phase 0 (there should be
none — if you claim one does, justify it). Then stop and wait for the Phase 0 prompt.
```

---

## PROMPT 0 — Phase 0: Environment setup & smoke test

```
Run Phase 0 of MASTER-BLUEPRINT.md (§6, Phase 0). Read §0, §2, and §12 first.

Do: PROGRESS.md, LESSONS.md, ENVIRONMENT.md already exist as scaffolds in the
project root — fill them in, never recreate them from scratch. Set up a
venv, install mlx-lm, pull mlx-community/Qwen2.5-14B-Instruct-4bit. Prove base
inference. Build a 20-pair throwaway chat-format dataset (content irrelevant),
run a 50-iter LoRA smoke train, prove the adapter loads and changes output, then
serve with mlx_lm.server --adapter-path and prove the endpoint answers a request.

Gates (all must pass): base inference works · smoke train completes without OOM ·
adapter loads · served endpoint answers. Record peak memory and train time in
ENVIRONMENT.md, plus every environment quirk you hit (paths, flags, gotchas).

Report: gate results, ENVIRONMENT.md contents, FRICTION section. Then stop.
```

---

## PROMPT 1 — Phase 1: Corpus export & inventory

```
Run Phase 1 of MASTER-BLUEPRINT.md (§6, Phase 1). Read §4 (dataset spec) first,
plus ENVIRONMENT.md and LESSONS.md.

[YOU — F Mac: connect/drop the coding corpus before he starts: STARGATE sessions,
Software Development Protocol v3.0, best code reviews, best dev conversations.
Your only job is choosing what goes in.]

Do: inventory every source file — count, word count, conversations, date range,
estimated JSONL pair yield per source. Flag anything reflecting superseded
methodology (Protocol v2 scoring, pre-v4 STARGATE) for F Mac's confirmation.
Write the inventory table into PROGRESS.md.

Gates: inventory complete · estimated yield ≥ 150 pairs (if under: STOP, report,
do not proceed) · sensitive-content check surfaced to F Mac.

Report: inventory table, stale-material flags, yield verdict, FRICTION. Stop.
```

---

## PROMPT 2 — Phase 2: JSONL conversion pipeline

```
Run Phase 2 of MASTER-BLUEPRINT.md (§6, Phase 2). Read §4 fully first, plus
ENVIRONMENT.md and LESSONS.md. Build test-first.

Do: build the reusable converter to the exact spec in §6 Phase 2 — it runs again
for Phases 6 and 7, so no coding-corpus hardcoding. Chat format per §4.1, one
standard system prompt for the coding adapter (draft it from §4.1's example;
include it in your report). Output: train.jsonl, valid.jsonl (90/10 seeded random),
sample-20.md, stats report, provenance map (kept OUTSIDE the training data).

Gates: converter unit tests pass (malformed md, empty file, giant file, unicode) ·
every JSONL line validates against the chat schema · stats report produced ·
F Mac spot-check of sample-20.md returns GO.

[YOU — F Mac: 10-minute spot-check of sample-20.md. Accuracy of voice. GO or FIX.]

Report: test results, stats summary, system prompt used, FRICTION. Stop.
```

---

## PROMPT 3 — Phase 3: First LoRA training run

```
Run Phase 3 of MASTER-BLUEPRINT.md (§6, Phase 3). Read §2 (corrections), §12
(ledger — the training command is stamped, don't re-research it), ENVIRONMENT.md,
LESSONS.md.

Do: run the training command from §6 Phase 3 in the Phase 0 venv. Monitor
validation loss per the decision rules there (continuation vs early stop).
On OOM: --batch-size 1 first, then reduce --num-layers. Log every run's config
and losses in PROGRESS.md. Never overwrite a previous adapter — version them.
Then run 3 probe prompts (coding tasks) against base vs adapter and capture both
outputs side by side. Include at least 1 OFF-corpus probe (general competence check).

Gates: run completes · validation loss improved vs start · adapter saved and
config logged · probes show methodology voice vs base.

Report: loss curve summary, run log, probe comparisons, FRICTION. Stop.
```

---

## PROMPT 4 — Phase 4: Serve + blind A/B test

```
Run Phase 4 of MASTER-BLUEPRINT.md (§6, Phase 4). Read §2 Correction 1 — serving
is mlx_lm.server --adapter-path. No fusing, no Ollama in this phase.

[YOU — F Mac: supply or approve 10 real tasks from your backlog —
4 code review, 3 architecture/planning, 3 implementation-approach.]

Do: serve the adapter. For each task, collect (A) local specialist output and
(B) current Claude workflow output. Anonymize and label-shuffle into a scoring
doc so F Mac cannot tell which is which. Log tok/s and latency per task.

[YOU — F Mac: ~45 min blind scoring, 1–5 per output on: methodology fidelity ·
technical correctness · usefulness as first draft.]

Gates: all 10 pairs collected · blind scoring done · results table (per-task,
per-dimension, unblinded after scoring) written to PROGRESS.md.

Report: results table, performance numbers, FRICTION. Stop.
```

---

## PROMPT 5 — Phase 5: Decision gate

```
Run Phase 5 of MASTER-BLUEPRINT.md (§6, Phase 5). Read the Phase 4 results table
in PROGRESS.md and §11 (A3 thresholds).

Do: apply the decision rule — GO / DIAGNOSE / ESCALATE exactly as defined.
DIAGNOSE = dataset problem: map failed task types to corpus gaps, propose the
corpus fix, loop Phases 2–4 on the fix. ESCALATE = same dataset on
mlx-community/Qwen2.5-Coder-14B-Instruct-4bit, re-A/B. Never change the base
model to fix a dataset problem.

Output: one-page report — what held, what was thin, what to change,
recommendation with evidence.

[YOU — F Mac: the GO/no-go call is yours.]

On GO: the widening phases unlock (Prompts 6–9). Stop after the report.
```

---

## PROMPT 6 — Phase 6: Reasoning specialist

```
Run Phase 6 of MASTER-BLUEPRINT.md (§6, Phase 6) — the replication playbook.
Reuse the Phase 2 converter unchanged except: source folder = the reasoning corpus,
system prompt = reasoning-specialist identity (draft it; report it).

[YOU — F Mac: select the reasoning corpus — Thinking Bin threads
(~/Desktop/Thinking Bin/Quarantine Tank/), book material, architectural
brainstorms. Then: spot-check, 10 real "help me think through X" tasks, blind score.]

Run the full loop: inventory → convert → spot-check → train → serve → blind A/B →
decision report. Same gates as Phases 1–5. Fidelity dimension = "reasons like me":
money-as-composite-time, faith-rooted security, his argument structure.

Report per phase-equivalent, FRICTION throughout. Stop at the decision report.
```

---

## PROMPT 7 — Phase 7: Design specialist

```
Run Phase 7 of MASTER-BLUEPRINT.md (§6, Phase 7). OPEN WITH the corpus-feasibility
check: sketches are images and this pipeline is text-only. Inventory the TEXTUAL
design reasoning (constraints, tolerances, annotations, briefs). If estimated
yield < 150 pairs: STOP and report options (transcribe sketch annotations, defer
for a VLM approach) — do not force a thin corpus through.

[YOU — F Mac: select design corpus; feasibility call if yield is thin.]

If feasible: run the replication playbook (as Prompt 6, design identity).
Video/graphics adapter stays deferred — do not start it.

Report, FRICTION. Stop.
```

---

## PROMPT 8 — Phase 8: Router build

```
Run Phase 8 of MASTER-BLUEPRINT.md. The spec is §3.3 — build exactly that:
rules layer → local-LLM fallback classification → confidence floor → Claude
fallback → escalation flag → decision logging. Adapter swap by server restart
is acceptable v1 (§11 A5). Build test-first.

Gates: unit tests per route + ambiguous + adversarial phrasings · ≥90% correct
on a 50-prompt eval set seeded from the Phase 4/6 task logs · Claude-fallback
path proven · end-to-end demo (prompt → route → specialist → polish flag).

Report: eval results, routing log sample, FRICTION. Stop.
```

---

## PROMPT 9 — Phase 9: Claude integration + final review

```
Run Phase 9 of MASTER-BLUEPRINT.md. Define the structured hand-up format (task
type, specialist output, confidence, polish instructions), write per-domain
polish prompts, wire router → specialist → Claude, and run the end-to-end smoke
on 5 real tasks. YOU click through everything first — F Mac is never the first
person to see it break.

[YOU — F Mac: final full-system review, Gate-6 style — works, gates passed,
performance acceptable, clear to adopt.]

Gates: smoke run clean · F Mac sign-off. On sign-off: write the final RUN
REPORT to LESSONS.md — product flaws, process flaws, and a PROTOCOL PATCH:
what this blueprint should have said to get each phase right the first time.

System shipped.
```

---

## STANDING REMINDERS (apply to every prompt above)

- Blueprint §0 rules govern every session.
- FRICTION section in every report, even if "none."
- Stamped facts in §12 are trusted; new facts you verify get stamped.
- F Mac touchpoints only where marked **[YOU]** — nothing else goes to him.
- STARGATE recommendations (§7) are queued for F Mac's approval — do not apply them to the skill unprompted.
