# SESSION HANDOFF — F Mac Local AI Build

**Purpose:** paste this into a new chat to continue where we left off. It captures what we're building, the hardware reality, what's done, and what's left.

---

## What we're building
A **private, local AI** on F Mac's own Mac, running his own open-source models with his personal operating framework baked in — plus a nice chat window (Msty), screenshot reading, his own documents, and web search. Claude sits on top only for heavy lifts (optional, not wired yet — needs a paid API key F Mac declined for now).

The original master plan lives in the repo: `engine/MASTER-BLUEPRINT.md` (+ `PROMPT-PACK.md`). The full software engine for the *eventual* training pipeline is already built and tested under `engine/` — but **training is DEFERRED** (see hardware).

## Hardware reality (the constraint that shaped everything)
- Machine: **Intel iMac** (Core i5-10500, **not** Apple Silicon), 64GB RAM.
- Consequence 1: **MLX (Apple-Silicon-only) won't run.** So we used **Ollama** instead.
- Consequence 2: **No GPU → training is not practical here.** So the models run **untrained** — they use F Mac's framework as a system prompt, not learned weights. Training (the "make it truly learn me" step) waits for a GPU / cloud / better hardware.
- Consequence 3: **CPU-only = slow.** 7B runs ~3 words/sec (usable), 14B ~half that. Video understanding is NOT feasible locally.

## The architecture (how the pieces relate)
- **The brain = Qwen** (open-source model, 7B and 14B). The only "smart" part. F Mac's `fmac-*` models = Qwen + his framework.
- **The engine = Ollama.** Runs/builds the models. Used mainly by our Terminal scripts to *build* models. Not needed for daily chatting.
- **The window = Msty (Msty Studio app).** What F Mac actually types into. Has its own built-in engine, reads the same model folder Ollama uses. Daily driver.
- Claude = a separate, much bigger brain in Anthropic's cloud (optional top layer, not connected).

## Key insight F Mac locked in (matches the blueprint thesis)
The model does **NOT** learn from use — it's frozen. The system gets better by: (1) sharpening the **framework**, (2) feeding it **documents**, (3) F Mac getting better at using it. "The moat is the system, not the model." Training later raises the raw-intelligence ceiling; it's an upgrade, not a requirement for daily value.

## What's DONE
- Ollama installed; Qwen 7B pulled.
- **Msty installed** and connected to the local model folder (`/Users/fmac/.ollama/models`). Daily chat works.
- **Framework baked into all models:** `engine/prompts/fmac-framework.md` (full) and `fmac-framework-lite.md` (condensed, used for speed). Source: "F Mac Workflow & Interaction Framework v3" (Signal-Lock Protocol, hard rules R1–R12, Shared Lexicon).
- **7B models live:** `fmac-base`, `fmac-coding`, `fmac-reasoning`, `fmac-video`, `fmac-design` — condensed framework, 8k context, ~3 tok/s. Confirmed working (used his lexicon "button it down" in a reply).
- Mac dictation ON (talk-in) and **Speak Selection** ON (highlight text + Option+Esc reads aloud).
- Speed fix applied: the 32k context window was the crawl cause — dropped to 8k; big improvement (0.06 → ~3 tok/s).

## In progress / pending downloads
- **14B models** (`fmac-*-14b`) — smarter, ~half speed. Script: `engine/mac/add-14b.sh`. (~9GB download.)
- **Vision model** (`fmac-vision`, llama3.2-vision base) — read screenshots. Script: `engine/mac/add-vision.sh`. (~8GB download.) RUN AFTER the 14B finishes.

## Open to-dos (all work on current hardware, no payment)
1. **Feed it documents** — Msty's "knowledge" feature so it answers from F Mac's real files/protocols/deals. (Highest near-term value. Not started.)
2. **Web search** — Msty's globe 🌐 icon; connect a free search source so it can pull current info. (Not started.)
3. **Voice back-and-forth** — talk-in (dictation) + read-back (Speak Selection / Msty read-aloud button). Works button-by-button; NOT smooth hands-free flow on this chip. (Partially set up.)
4. **Later / needs hardware or payment:** actual training (learn F Mac's patterns permanently); video understanding; connecting Claude (needs paid Anthropic API key).

## How to operate (cheat sheet)
- **Daily use:** open **Msty** → New Chat → pick a `fmac-` model → type. Ollama app can stay closed.
- **Build/change models:** open Terminal, then:
  ```
  cd ~/F-Mac-Deal-Analyst && git pull
  cd engine && bash mac/<script>.sh
  ```
  (Ollama auto-starts for the build.) Then in Msty start a NEW chat to see changes.
- **Scripts:** `intel-setup.sh` (first setup), `rebuild-fast.sh` (speed rebuild), `add-14b.sh`, `add-vision.sh`.
- **Everything is stored on GitHub** (repo `Fmacz06/F-Mac-Deal-Analyst`, work on branch `claude/project-completion-szzj2u`, merged to `main`). `git pull` downloads the latest to the Mac.

## Where things live
- Project on the Mac: `~/F-Mac-Deal-Analyst/engine/`
- Model files: `/Users/fmac/.ollama/models`
- Framework: `engine/prompts/fmac-framework*.md`
- Mac scripts: `engine/mac/*.sh`
- Guides: `engine/GETTING-STARTED.md`, `engine/RUNBOOK.md`

## Working style with F Mac (important for the next session)
- He is not a developer — give **precise, one-step-at-a-time** clicking instructions, describe **where on screen**, and ask for **screenshots**. No jargon.
- Short answers. Confirm understanding before executing (Signal-Lock).
- His framework (`fmac-framework.md`) governs how to communicate with him — read it.
