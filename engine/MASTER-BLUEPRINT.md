# MASTER BLUEPRINT — Local AI Reasoning & Creation Engine
### AP Capital / F Mac
**Prepared:** July 6, 2026 · **Prepared by:** Senior review pass (Sonnet) · **Executor:** Opus
**Status:** Ratified blueprint. All research verified against current sources (see VERIFIED ledger, §12).
**Companion file:** `PROMPT-PACK.md` — copy-paste-ready prompts, one per phase.

---

## §0 — OPERATING RULES FOR THE EXECUTOR (READ FIRST, EVERY SESSION)

1. **This document is the source of truth.** The original handoff doc is superseded — two of its technical claims were wrong and are corrected here (§2). Do not work from memory of the old doc.
2. **F Mac decides WHAT; you build HOW.** He selects source material, confirms `[ASSUMED]` values, and spot-checks. Never assign him lookup, data-entry, or manual conversion work.
3. **One phase per session.** Each phase in §6 is sized for a single clean-context session. Finish the phase, write the report, update `PROGRESS.md`, stop.
4. **State lives in files, never in your head.** Maintain `PROGRESS.md` (with VERIFIED ledger), `LESSONS.md`, and `ENVIRONMENT.md` in the project root — same discipline as STARGATE.
5. **Every phase report includes a FRICTION section** — retries, dead ends, ambiguities in THIS blueprint, and what the blueprint should have said. Even if "none."
6. **TDD applies to ML work too.** Every phase has gates (§6). A gate here is a measurable pass/fail check — sometimes a unit test, sometimes an eval score, sometimes F Mac's 30-second visual go/fix.
7. **Verify-before-assert.** Facts stamped in the VERIFIED ledger (§12) are trusted — do not re-research them. Anything new you rely on, verify and stamp.
8. **Direct, solution-first.** Pair every limitation with a workaround in the same breath.

---

## §1 — MISSION (UNCHANGED — DO NOT DRIFT)

Build a **local specialist AI system** on F Mac's Mac Studio (64GB unified memory, Apple Silicon), fine-tuned on **his own methodology**, with **Claude as the execution/orchestration layer above it**.

- NOT a frontier-model clone. A set of **owned, domain-specialized LoRA adapters** on a shared base, trained on F Mac's actual work product, running entirely on his hardware. No API cost, no data leaving the machine for the local portion.
- **Guiding conviction:** the moat is the systems architecture and orchestration logic, not the model. Encode F Mac's methodology and convictions *into* the system. Build **his** engine, not a generic assistant.
- **Sequencing (locked):** coding specialist first → prove the loop → replicate for reasoning → design. Video-gen and CAD integration come only after the core loop is proven.

---

## §2 — CORRECTIONS TO THE ORIGINAL HANDOFF (VERIFIED JULY 6, 2026)

### Correction 1 — The serving path was wrong
The handoff said: *"Fuse & serve via Ollama."* **A fused MLX model is not directly Ollama-compatible.** Ollama consumes GGUF; MLX fuses to safetensors. Following the handoff as written costs an afternoon of confusion.

**Corrected serving path (in order of preference):**
1. **For testing and the A/B phase — don't fuse at all.** `mlx_lm.server` serves the base model **with the adapter applied** via `--adapter-path`, exposing an OpenAI-compatible endpoint on localhost. Fastest loop: train → serve → test, adapter stays swappable.
2. **For "production" local serving — still MLX-native.** Fuse (`mlx_lm.fuse`) and serve the fused model via `mlx_lm.server`. Simple, one ecosystem.
3. **Ollama only if F Mac specifically wants it as the front-end:** fuse with `--de-quantize` (float16 output), convert with llama.cpp's `convert_hf_to_gguf.py`, re-quantize the GGUF, write a Modelfile. This is a real multi-step conversion — treat as optional Phase 4b, not the default.

### Correction 2 — Base model: decision upheld, with a documented escalation path
Verified: `mlx-community/Qwen2.5-14B-Instruct-4bit` exists on Hugging Face (8.31 GB, 4-bit). **The locked decision stands** — it stays the shared base for ALL adapters, because the architecture is *swappable adapters on ONE base* (one 8.3GB model in RAM, hot-swap tiny adapters per domain). Do not break that design casually.

Two adjacent facts, verified, for the decision gate at Phase 5:
- `mlx-community/Qwen2.5-Coder-14B-Instruct-4bit` exists. **If the coding A/B comes back thin on code quality specifically**, the first escalation is re-running the same dataset on the Coder base — accepting a second base model on disk — *before* concluding the dataset is the problem. Cheap experiment, big signal.
- **Qwen3-14B** (MLX 4-bit) exists and is a newer generation with a hybrid thinking/non-thinking mode. **Not recommended for the first run:** the thinking-mode format complicates SFT dataset construction, and the MLX fine-tuning ecosystem's documentation is mature on Qwen2.5. Reassess after the loop is proven. `[ASSUMED — F Mac sign-off §11]`

### Confirmed as-written
- `mlx_lm.lora --model <base> --train --data ./data --iters 600` — syntax current (mlx-lm ~0.30.6, early 2026). Useful flags: `--batch-size` (drop to 1–2 under memory pressure), `--num-layers` (default 16), `--fine-tune-type lora` (default).
- 64GB capacity claims (14B LoRA in 20–40 min; 32B QLoRA comfortable; 70B → cloud) — consistent with current community results.
- Dataset formats (§4) verified against the official mlx-lm LORA docs.

---

## §3 — ARCHITECTURE

### 3.1 The stack
```
┌─────────────────────────────────────────────────┐
│  CLAUDE (API) — execution/orchestration layer    │
│  polish · expansion · external tools (video,     │
│  CAD hooks) · same pattern as Threatic & Fable   │
└──────────────────────▲──────────────────────────┘
                       │ structured output
┌──────────────────────┴──────────────────────────┐
│  ROUTER (Phase 8) — "what kind of work is this?" │
│  rules-first classifier + dispatch table          │
└───┬──────────┬───────────┬───────────┬──────────┘
    │          │           │           │
 CODING     REASONING   VIDEO/GFX   3D/CAD/DESIGN
 adapter    adapter     adapter     adapter
    └──────────┴───────────┴───────────┘
         Qwen2.5-14B-Instruct-4bit (shared base)
         served by mlx_lm.server (OpenAI-compatible)
         Mac Studio · 64GB · MLX
```

### 3.2 The four specialists (build order)
1. **Coding** — trained on STARGATE sessions, Software Development Protocol v3.0, best code reviews and dev conversations. Goal: thinks like he codes — patterns, test-first discipline, architecture choices.
2. **Reasoning** — trained on his thinking conversations (theological/eschatological threads, architectural brainstorms, book material). Goal: reasons like him.
3. **Video/graphics reasoning** — understands his video briefs, design intent, output specs, style. NOT local video generation. Routing to video-gen APIs comes later.
4. **3D/CAD/design logic** — trained on sketches, design constraints, manufacturing tolerances. Eventual CAD/3D-printing integration.

### 3.3 The router (design sketch — fulfills the handoff's return contract)
Not a model. A small Python service (or Claude skill) in front of the local endpoint:

- **Layer 1 — rules.** Keyword/pattern table handles the obvious 80%: code fences, stack traces, file extensions → coding; "help me think through / what if / theology / chapter" → reasoning; "brief / storyboard / render spec" → video; "tolerance / sketch / print / CAD" → design.
- **Layer 2 — LLM fallback.** Ambiguous input → one cheap classification call to the local base model itself ("Classify this task: coding | reasoning | video | design | general") — free, local, fast.
- **Confidence floor.** Below threshold, or classified "general" → route straight to Claude. Never let a weak local answer masquerade as a specialist answer.
- **Escalation flag.** Every specialist response carries a `needs_polish: bool`; when true, output pipes to Claude with a domain-specific polish prompt.
- **Logging.** Every routing decision logged (input hash, route, confidence, latency). The log IS the eval set for improving the router later.
- Adapter swap = restart `mlx_lm.server` with a different `--adapter-path` (single-user machine; seconds). Multi-adapter hot-serving is a later optimization, not a Phase 8 requirement.

---

## §4 — DATASET SPEC ("THE DATASET IS YOU")

**Quality and consistency beat volume.** Contradictory examples poison training.

### 4.1 Format (verified against official mlx-lm docs)
- Directory: `./data/` containing `train.jsonl` (required) and `valid.jsonl` (strongly recommended — gives validation loss during training). 90/10 split.
- **Use the chat format** — one JSON object per line:
  `{"messages": [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}`
  The final assistant message is what the model is trained to produce.
- **One consistent system prompt per adapter** (e.g., coding: "You are F Mac's senior engineering specialist. You follow the Software Development Protocol v3.0: test-first, Clear/Fuzzy/Missing triage, Checkpoints."). The SAME system prompt is used at inference — this is the adapter's activation key.

### 4.2 Source material (F Mac's call alone — he selects, team converts)
Coding corpus (Phase 1): STARGATE sessions · Software Development Protocol v3.0 · best code reviews · best dev conversations.
Reasoning corpus (Phase 6): deep reasoning threads, book material — from `~/Desktop/Thinking Bin/Quarantine Tank/` (`.md` exports, `[Title] - YY-MM-DD.md`).
Design corpus (Phase 7): design notebooks, sketches, constraints.

### 4.3 Quality bar (the converter and the spot-check enforce this)
- **Target: 300–1,000 clean pairs** for the first coding adapter. Under ~150 usable pairs → STOP, report to F Mac, decide whether to widen sources before training on thin data.
- Each pair teaches one thing: *when you see THIS kind of ask, respond in THIS shape with THIS reasoning style.*
- Assistant turns must reflect his **current** methodology (Protocol v3.0, STARGATE v4). Examples showing superseded practice (v2 scoring, pre-ledger STARGATE) get updated or cut — never included as-is.
- Strip pleasantries, dead ends, and meta-chatter; keep the reasoning spine. Long conversations become multiple smaller pairs when they contain multiple teachable exchanges.
- No PII/credentials/client-sensitive content in any pair.
- **Spot-check protocol:** converter produces a random 20-pair sample file; F Mac reviews for accuracy-of-voice (10 min, go/fix). That is his ONLY manual touchpoint in the data pipeline.

---

## §5 — HARDWARE & ENVIRONMENT (CONFIRMED, UNCHANGED)

Mac Studio, 64GB unified memory · MLX framework · local for prototyping/adapters; rent cloud GPU only past ~32B or for full fine-tunes.
Capacity: 7B–14B LoRA easy (20–40 min); 32B QLoRA comfortable; 70B QLoRA possible-but-slow → cloud. Inference: 32B@4-bit smooth; 70B@4-bit ~10–15 tok/s eating most of RAM.

---

## §6 — PHASED EXECUTION PLAN

> Phases 0–5 are the **proving loop** (coding specialist). Phases 6–9 are the **widening** — do not start Phase 6 until the Phase 5 decision gate says GO.

### Phase 0 — Environment setup & smoke test
**Objective:** working MLX training environment, proven end-to-end on toy data before real data exists.
**Steps:** create project root + state files (`PROGRESS.md`, `LESSONS.md`, `ENVIRONMENT.md`); install `mlx-lm` in a venv; pull `mlx-community/Qwen2.5-14B-Instruct-4bit`; confirm base-model inference; build a 20-pair throwaway dataset (any content); run a 50-iter LoRA smoke train; confirm adapter loads and visibly changes output; confirm `mlx_lm.server --adapter-path` serves an OpenAI-compatible endpoint that answers a curl.
**Gates:** ✅ base inference works · ✅ smoke train completes without OOM · ✅ adapter loads · ✅ served endpoint answers. Record peak memory + train time in `ENVIRONMENT.md`.
**F Mac touchpoint:** none.

### Phase 1 — Corpus export & inventory
**Objective:** all coding-corpus source `.md` files in one place, inventoried.
**Steps:** F Mac connects the folder(s) / drops the files (his ONLY action: selecting what goes in). Executor inventories: file count, word count, conversation count, date range, estimated pair yield per source; flags stale-methodology material for confirmation.
**Gates:** ✅ inventory table in `PROGRESS.md` · ✅ estimated yield ≥ 150 pairs (below → STOP and report) · ✅ F Mac confirms nothing sensitive is in scope.
**F Mac touchpoint:** provide files; 5-minute inventory review.

### Phase 2 — JSONL conversion pipeline
**Objective:** a repeatable converter (it will run again for Phases 6 and 7 — build it once, reusable).
**Converter requirements (spec, not code):** input = folder of `.md` exports; parses conversation turns; segments long threads into single-lesson pairs; injects the adapter's standard system prompt; applies §4.3 quality filters (dedup near-identical pairs, strip meta-chatter, length bounds); emits `train.jsonl`/`valid.jsonl` (90/10, random, seeded); emits `sample-20.md` (human-readable random sample) + a stats report (pair count, token-length distribution, per-source yield); every pair traceable to its source file (provenance map kept alongside, NOT inside the training data).
**Gates:** ✅ unit tests on the converter itself (malformed md, empty file, giant file, unicode) · ✅ JSONL validates line-by-line against the chat schema · ✅ stats report produced · ✅ **F Mac spot-check of `sample-20.md` = GO**.
**F Mac touchpoint:** 10-minute spot-check.

### Phase 3 — First LoRA training run
**Objective:** trained coding adapter.
**Run:** `mlx_lm.lora --model mlx-community/Qwen2.5-14B-Instruct-4bit --train --data ./data --iters 600` (venv from Phase 0). Expected 20–40 min. Watch validation loss: still falling at 600 iters → one continuation run; flat/rising while train loss falls → overfitting, stop earlier. OOM → `--batch-size 1`, then fewer `--num-layers`, in that order. Log every run's config + final losses in `PROGRESS.md` (runs are cheap; keep each adapter output separately — never overwrite a previous adapter).
**Gates:** ✅ run completes · ✅ validation loss improved vs start · ✅ adapter saved + config logged · ✅ 3 manual probe prompts show methodology voice (test-first instinct, Clear/Fuzzy/Missing framing) vs base model — at least 1 probe OFF-corpus (general-competence check, §8).
**F Mac touchpoint:** none (show him the probe outputs for flavor, not approval).

### Phase 4 — Serve + A/B test
**Objective:** honest read on the specialist vs. the current Claude workflow.
**Serve:** `mlx_lm.server` with `--adapter-path` (Correction 1 — no fuse, no Ollama for this phase).
**A/B protocol:** 10 real tasks from F Mac's actual backlog — 4 code review, 3 architecture/planning, 3 implementation-approach. Each task → (A) local specialist, (B) current Claude workflow. Outputs anonymized/label-shuffled into a scoring doc; **F Mac scores blind**, 1–5 on: methodology fidelity ("sounds like my protocol"), technical correctness, usefulness-as-first-draft. Also log tok/s and latency.
**Gates:** ✅ all 10 pairs collected · ✅ blind scoring done · ✅ results table (per-task, per-dimension) in `PROGRESS.md`.
**F Mac touchpoint:** ~45 min blind scoring. (He supplies or approves the 10 tasks — his backlog, his call.)

### Phase 5 — DECISION GATE
**Objective:** GO / DIAGNOSE / ESCALATE, with evidence.
- **GO** (specialist ≥ 3.5 avg on methodology fidelity AND ≥ 3 on correctness): proceed to Phase 6.
- **DIAGNOSE** (thin on fidelity): dataset problem — identify which task types failed, map to corpus gaps, expand/clean corpus, loop Phases 2→4 on the fix (re-convert, re-train — cheap — re-A/B). Do NOT change base model to fix a dataset problem.
- **ESCALATE** (fidelity fine, raw code quality thin): re-run same dataset on `Qwen2.5-Coder-14B-Instruct-4bit` (Correction 2) and re-A/B.
**Output:** a one-page report — what held, what was thin, what changed, recommendation. `[Scoring thresholds are ASSUMED — F Mac sign-off §11]`
**F Mac touchpoint:** the GO/no-go call.

### Phase 6 — Reasoning specialist (replication playbook)
Re-run Phases 1→5 with: corpus = Thinking Bin threads + book material (F Mac selects); system prompt = reasoning-specialist identity; A/B tasks = 10 real "help me think through X" prompts; fidelity dimension = "reasons like me" (frameworks: money-as-composite-time, faith-rooted security, his argument structure). Converter from Phase 2 is reused — only a source-folder and system-prompt change.

### Phase 7 — Design specialist
Same playbook. Corpus = design notebooks/constraints/tolerances. **Known gap to solve in-phase:** sketches are images — the pipeline is text. Phase 7 opens with a corpus-feasibility check: enough *textual* design reasoning to hit 150+ pairs? If not, report options (transcribe sketch annotations, defer to VLM approach) before building. Video/graphics adapter is deferred until after design proves — same pattern, lower priority.

### Phase 8 — Router build (§3.3 is the spec)
**Gates:** ✅ unit tests on rules layer (each route + ambiguous + adversarial phrasing) · ✅ ≥90% correct routing on a 50-prompt eval set drawn from F Mac's real usage (Phase 4/6 task logs seed this) · ✅ fallback-to-Claude path proven · ✅ end-to-end: prompt in → routed → specialist answers → (if flagged) Claude polish returns.

### Phase 9 — Claude integration layer
**Objective:** the full pattern live — local ideation/domain reasoning → structured output → Claude polish/expansion, mirroring the Threatic/Fable pattern.
**Steps:** define the structured hand-up format (task type, specialist output, confidence, polish instructions); per-domain polish prompts; end-to-end smoke run on 5 real tasks; **F Mac full-system review** (Gate-6 style: works, gates passed, performance acceptable, clear to adopt).
**Gates:** ✅ smoke run clean · ✅ F Mac sign-off. On sign-off: final RUN REPORT written to `LESSONS.md` — product flaws, process flaws, and a PROTOCOL PATCH (what this blueprint should have said to get each phase right the first time). **System shipped.**

---

## §7 — STARGATE v4: SENIOR REVIEW (RECOMMENDATIONS ONLY — F MAC APPROVES BEFORE ANY EDIT)

Reviewed against the actual `SKILL.md` (v4 — note: the handoff described v3; v4 already replaced the Gate-4 gatekeeper trio with a single looping BUILD-READINESS agent and added the VERIFIED ledger, LESSONS.md, watchers, model policy, and the pre-Gate-6 smoke run).

**Tight (keep, don't touch):** state-in-files governing rule · stakes tiers with "cut agents, never tests" · VERIFIED ledger (checked once = trusted everywhere) · GIVEN-vs-ASSUMED sign-off · observation-only watchers with the protocol patch · mandatory smoke run before human review · friction reporting. This is a mature protocol.

**Recommendations:**
1. **No version history inside the skill.** Back-watcher protocol patches feed "the next Stargate version," but nothing records what changed between v3→v4→v5. Add a short CHANGELOG section to SKILL.md — five lines per version. Without it, patches get re-litigated.
2. **Lessons die with the project.** `LESSONS.md` is per-project-root; a quirk learned in project A gets rediscovered in project B. Add a global `~/stargate/GLOBAL-LESSONS.md` that Gate 4 seeds ENVIRONMENT.md from, and the back watcher appends cross-project-worthy items to.
3. **No abort/rollback path in Gate 5.** If mid-execution a phase proves fundamentally mis-planned (not failing tests — wrongly conceived), the protocol has no sanctioned route back. Add one line: "A phase discovered to be mis-planned is a STOP → return to Gate 3 with a findings note; never improvise a redesign inside Gate 5."
4. **Gate 5 handoff signal (a) is weakly self-detectable.** "Re-reading files because content fell out of context" is hard for an agent to notice about itself. Add an objective proxy: "hand off after N tool-call cycles without a PROGRESS.md update" or an explicit phase-step budget.
5. **No ML-run annex.** STARGATE's gates assume deterministic software tests. Training runs need eval-style gates (loss thresholds, blind-scored A/Bs, dataset spot-checks). §6 of this blueprint IS that adaptation — after this project proves it, fold an "ML variant" page into the skill.
6. **Minor:** Gate 6 checklist says "clear to push" even for projects with no repo/remote; one conditional word fixes it.

---

## §8 — RISKS & MITIGATIONS

- **Dataset too small/inconsistent** (the #1 risk) → hard floor at Phase 1 (150 pairs), spot-check gate at Phase 2, DIAGNOSE loop at Phase 5. Never train on a corpus that failed inventory.
- **Overfitting on a narrow corpus** → valid.jsonl loss watched every run; probe prompts include OFF-corpus tasks to check the model didn't lose general competence.
- **Memory pressure** → batch-size then num-layers reduction ladder (Phase 3); everything else closed during training; peak-memory logged in ENVIRONMENT.md.
- **Serving-path confusion** → Correction 1 is the law: mlx_lm.server first; Ollama/GGUF is optional Phase 4b only.
- **Scope creep toward video-gen/CAD before the loop is proven** → Phases are gated; Phase 5 decision gate is the only door to widening.
- **Licensing** → Qwen2.5 base is Apache-2.0; local personal use is unrestricted. Fine.

---

## §9 — DIVISION OF LABOR (STANDING)

**F Mac (only):** selects source material · confirms `[ASSUMED]` values (§11) · 10-min spot-checks · blind A/B scoring · GO/no-go calls · final system sign-off.
**Executor (everything else):** all installs, conversions, scripts, training runs, serving, eval harnesses, reports, state files.

## §10 — RETURN CONTRACT (DEFINITION OF DONE)

1. Working coding specialist — trained, served, blind-A/B-tested, decision-gated.
2. A clear written read on dataset quality — what worked, what was thin.
3. STARGATE reviewed (✅ done — §7) with recommendations awaiting F Mac's approval.
4. Orchestration layer designed (✅ §3.3) and, in full vision, built (Phase 8).
5. Reasoning + design specialists replicated (Phases 6–7), Claude layer integrated (Phase 9).

## §11 — GIVEN vs ASSUMED (F MAC SIGN-OFF LIST)

**GIVEN (he said it — pinned):** Mac Studio 64GB · MLX · Qwen2.5-14B-Instruct-4bit shared base · LoRA/QLoRA adapters · coding-first sequencing · JSONL from his own material · he selects sources · Claude as top layer · Threatic/Fable pattern.

**ASSUMED (confirm or correct — none block Phase 0–2 work):**
- A1: Skip Qwen3 for the first run; reassess after the loop proves (§2).
- A2: Coder-14B base is the sanctioned ESCALATE move at Phase 5 (accepts a second base on disk) (§2, §6-P5).
- A3: A/B scoring thresholds — GO at fidelity ≥3.5 and correctness ≥3.0 (§6-P5).
- A4: 300–1,000 pair target, 150-pair hard floor (§4.3).
- A5: Router = rules-first + local-LLM fallback + Claude floor (§3.3); adapter swap by server restart is acceptable v1.
- A6: A/B task mix — 4 review / 3 architecture / 3 implementation (§6-P4).
- A7: STARGATE recommendations (§7) are queued for approval, not applied.

## §12 — VERIFIED LEDGER (checked once = trusted; do not re-research)

| Fact | Status | Source | Date |
|---|---|---|---|
| `mlx_lm.lora --model --train --data --iters` syntax current; mlx-lm ~0.30.6 | ✅ | mlx-lm LORA docs (GitHub ml-explore/mlx-lm) | 2026-07-06 |
| `mlx-community/Qwen2.5-14B-Instruct-4bit` exists, 8.31 GB | ✅ | Hugging Face | 2026-07-06 |
| `mlx-community/Qwen2.5-Coder-14B-Instruct-4bit` exists | ✅ | Hugging Face | 2026-07-06 |
| `Qwen/Qwen3-14B-MLX-4bit` exists (hybrid thinking mode) | ✅ | Hugging Face | 2026-07-06 |
| Fused MLX ≠ Ollama-ready; Ollama path = fuse `--de-quantize` → llama.cpp `convert_hf_to_gguf.py` → GGUF | ✅ | ml-explore discussions + community guides | 2026-07-06 |
| `mlx_lm.server` serves OpenAI-compatible endpoint, supports `--adapter-path` | ✅ | mlx-lm SERVER docs | 2026-07-06 |
| Dataset: `train.jsonl` required, `valid.jsonl` optional-but-reports-loss; chat/completions/text formats; final message = completion | ✅ | mlx-lm LORA docs | 2026-07-06 |
