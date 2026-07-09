# START HERE — Handoff to Opus

**For F Mac to give to Opus at the start.** Plain English, no prior context needed.

---

## What we're trying to do

Build a private AI that runs entirely on this Mac Studio, trained on F Mac's own work so it thinks the way he works. It starts with a **coding specialist** and, once that's proven, expands to reasoning and design. Claude sits on top as the polish/orchestration layer. Nothing leaves the machine.

The full plan is already written and checked. It lives in two documents in this folder:

- **`MASTER-BLUEPRINT.md`** — the complete plan (the source of truth).
- **`PROMPT-PACK.md`** — ready-to-paste prompts, one per work session, in order.

This folder is the **project root** — all work happens here.

## What's already done

- The plan is written, proofread, and internally consistent.
- Empty tracking files (`PROGRESS.md`, `LESSONS.md`, `ENVIRONMENT.md`) are ready to be filled in.
- A `.gitignore` is in place so training data and models never get pushed online.

**Nothing has been built or trained yet.** That starts now, with you (Opus).

## How to do it — the loop

The work is split into **phases, one per session.** Each session:

1. F Mac starts a fresh chat with you (Opus), with this folder attached/open.
2. F Mac pastes the next prompt from `PROMPT-PACK.md`.
3. You do the work for that phase, update the tracking files, write a short report, and **stop.**
4. Next session, repeat with the next prompt.

The prompt order is:

| Session | Paste this prompt | What happens |
|---|---|---|
| 1 | **PROMPT K** (Kickoff) | You read the blueprint and confirm you understand. Then stop. |
| 2 | **PROMPT 0** | Set up the software on the Mac; prove training works on a tiny test. |
| 3 | **PROMPT 1** | F Mac drops in his coding files; you inventory them. |
| 4 | **PROMPT 2** | Build the tool that turns his files into training data. |
| 5 | **PROMPT 3** | Run the first real training. |
| 6 | **PROMPT 4** | Serve it; F Mac blind-scores it vs. Claude. |
| 7 | **PROMPT 5** | Decision gate: is it good? GO / fix / escalate. |
| — | PROMPTS 6–9 | Only unlock after a GO. Reasoning, design, router, final wiring. |

## What F Mac has to do (only these)

Everything else is Opus's job. F Mac only steps in where the prompt says **[YOU]**:

- **Pick the files** to train on (his coding sessions, protocols, best reviews).
- **A 10-minute quality check** of a sample, once.
- **About 45 minutes of blind scoring** near the end.
- **The GO / no-go call** at the decision gate.

Total hands-on time through the decision gate: roughly one hour.

## The one rule for Opus

Read `MASTER-BLUEPRINT.md` §0 first, every session. One phase per session. Never roll into the next phase. State lives in the files, not in your memory.

---

**F Mac's next action:** start a fresh chat with Opus in this folder and paste **PROMPT K**.
