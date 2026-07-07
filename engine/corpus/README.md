# THE BIN — dump your material here

This folder is the intake for everything the local model trains on. Drop
`.md` files in whenever you want, as many as you want, from any project.
You do NOT need to clean, sort, or curate before dumping — the pipeline
filters duplicates, strips chatter, and reports what it kept and why.

## Where to drop what

```
corpus/
  coding/      <- STARGATE sessions, dev conversations, code reviews, protocol docs
  reasoning/   <- Thinking Bin / Quarantine Tank threads, book material, brainstorms
  design/      <- design notes, constraints, tolerances, CAD reasoning (text only)
  unsorted/    <- not sure where it goes? drop it here, sort later (or never —
                  just point the inventory at it to see what it yields)
```

Sub-folders inside those are fine — the scanner is recursive.

## What counts as usable material

Conversation exports with visible speaker turns convert best:
`**User:** ... **Assistant:** ...`, `## Human / ## Assistant`, or
`User: ... / Claude: ...` — all recognized automatically. Files with no
conversation markers (e.g. a protocol document) get flagged in the inventory
instead of silently skipped, so you can decide what to do with them.

## The loop, every time you've dumped new material

```bash
make inventory SOURCE=corpus/coding     # what did the bin yield? (needs >= 150 pairs)
make convert  SOURCE=corpus/coding OUT=data
# eyeball data/sample-20.md  ("does this sound like me?")
bash mac/train.sh coding 600            # ~20-40 min -> a new, better adapter
```

Old adapters are never overwritten — every training run is versioned, so a
retrain can only add options, never destroy one.

## Privacy

This folder is git-ignored on purpose. Nothing you drop here is ever pushed
to GitHub or leaves your machine. Training happens locally; the model the
material shapes lives on your disk.
