# LESSONS — Local AI Reasoning & Creation Engine

> Maintained by the executor per MASTER-BLUEPRINT.md §0 rule 4. Things learned the hard way — environment quirks worth generalizing, blueprint ambiguities, approaches that failed and why. Appended as they happen; never deleted.

1. **Near-dup filtering needs genuinely distinct text to test.** Templated
   synthetic corpora (same sentence + counter) get correctly eaten by the
   0.92-similarity dedup — that's the filter working. On real corpora, check
   the `near_duplicate` drop count in stats.md before concluding yield is low.
2. **Router confidence must tolerate second-place noise.** One weak keyword
   from another domain must not drag a clear route below the floor.
   Confidence = winner's dominance scaled by absolute score mass.
3. **Blind-doc hygiene:** the key lives in a separate file the scorer never
   opens; the shuffle tool must exclude its own outputs when re-globbing.
4. **Unit tests alone missed a real parsing bug** (`**User:**` bold-with-colon
   left stray `**`); a dry run on realistic sample data caught it. Every
   pipeline change gets a dry run, not just tests.
5. **MLX is Apple-Silicon-only** — cloud sessions can build/test the text
   layers; training and serving gates only prove out on the Mac.

---

## Final RUN REPORT (written at Phase 9 sign-off)

Product flaws · process flaws · PROTOCOL PATCH — what MASTER-BLUEPRINT.md should have said to get each phase right the first time.

*(pending — system not yet shipped)*
