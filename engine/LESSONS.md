# LESSONS — Local AI Reasoning & Creation Engine

Per-project lessons file (MASTER-BLUEPRINT §0.4). Append as they're learned.

## From the cloud build session (2026-07-07)

1. **Near-dup filtering needs genuinely distinct text to test.** Synthetic test
   corpora with templated variation (same sentence + counter) get correctly
   eaten by the 0.92-similarity dedup — that's the filter working, not a bug.
   Real conversation exports won't trip this, but padded/boilerplate-heavy
   threads might; check the `near_duplicate` drop count in stats.md before
   assuming yield is low.
2. **Router confidence needs to tolerate second-place noise.** A single weak
   keyword from another domain ("should I" in a design question) must not
   drag a clear route below the floor. Confidence = dominance relative to the
   winner's score, scaled by absolute score mass.
3. **Blind-doc hygiene:** the blinding key must live in a separate file the
   scorer never opens, and the shuffle tool must exclude its own outputs when
   re-globbing the run directory.
4. **MLX is Apple-Silicon-only** — all training/serving gates are packaged as
   Mac-side scripts; the cloud session can only build and unit-test the
   text-processing layers.

## FRICTION (blueprint feedback per §0.5)

- The blueprint assumes the executor session runs on the Mac Studio. This
  build ran in a cloud Linux container, so Phases 0/3/4-serve became scripted
  handoffs (`mac/*.sh`) rather than executed gates. The blueprint should say
  which environment the executor runs in, and mark which gates are
  hardware-bound.
- §6 Phase 2 says "input = folder of .md exports" but doesn't specify the
  export turn-marker format. The converter handles the common patterns
  (`**User:**`, `## Human`, `User:` …) and reports unparsed files rather than
  guessing — Phase 1 inventory flags `NO-CONVERSATION-MARKERS` files so F Mac
  sees which sources need a different export or manual conversion.
- Protocol documents (e.g. Software Development Protocol v3.0 itself) are
  listed as corpus but aren't conversations — they yield zero pairs through
  the turn parser. Decide in Phase 1 whether to hand-convert them into Q&A
  pairs or treat them as system-prompt material only.
