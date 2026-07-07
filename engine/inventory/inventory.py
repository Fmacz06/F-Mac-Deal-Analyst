#!/usr/bin/env python3
"""Corpus inventory — MASTER-BLUEPRINT §6 Phase 1 (reused for Phases 6 & 7).

Input: a folder of .md source files (F Mac selects what goes in — his only job).
Output: an inventory table (markdown, ready to paste into PROGRESS.md) with
file count, word count, conversation/pair estimates, date range, and flags:
  - stale-methodology markers (Protocol v2, pre-v4 STARGATE) for confirmation
  - possible sensitive content (PII/credential patterns) for the scope check
Gate: estimated yield >= 150 pairs, else exit 2 (STOP and report).

Usage: python3 inventory.py --source DIR [--out inventory.md]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from converter.convert import parse_turns, pii_hits  # noqa: E402

HARD_FLOOR = 150

_STALE_MARKERS = re.compile(
    r"\b(?:protocol v?2(?:\.\d+)?|stargate v?[123]\b|pre-ledger|v2 scoring)\b", re.I)
_DATE_IN_NAME = re.compile(r"(\d{2,4})-(\d{2})-(\d{2})")


def analyze_file(path: Path, root: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    turns = parse_turns(text)
    exchanges = sum(1 for i in range(len(turns) - 1)
                    if turns[i].role == "user" and turns[i + 1].role == "assistant")
    m = _DATE_IN_NAME.search(path.name)
    return {
        "file": str(path.relative_to(root)),
        "words": len(text.split()),
        "turns": len(turns),
        "est_pairs": exchanges,
        "date": m.group(0) if m else "",
        "stale_flags": sorted(set(_STALE_MARKERS.findall(text))),
        "pii_flags": pii_hits(text),
    }


def build_report(rows: list[dict]) -> str:
    total_pairs = sum(r["est_pairs"] for r in rows)
    total_words = sum(r["words"] for r in rows)
    dates = sorted(r["date"] for r in rows if r["date"])
    lines = [
        "## Corpus inventory",
        "",
        f"- Files: **{len(rows)}** · Words: **{total_words:,}** · "
        f"Estimated pair yield: **{total_pairs}** (hard floor: {HARD_FLOOR})",
        f"- Date range (from filenames): {dates[0]} → {dates[-1]}" if dates
        else "- Date range: not derivable from filenames",
        "",
        "| Source file | Words | Turns | Est. pairs | Date | Flags |",
        "|---|---:|---:|---:|---|---|",
    ]
    for r in sorted(rows, key=lambda r: -r["est_pairs"]):
        flags = []
        if r["stale_flags"]:
            flags.append("STALE: " + ", ".join(r["stale_flags"]))
        if r["pii_flags"]:
            flags.append("SENSITIVE?: " + ", ".join(r["pii_flags"]))
        if r["turns"] == 0:
            flags.append("NO-CONVERSATION-MARKERS")
        lines.append(f"| `{r['file']}` | {r['words']:,} | {r['turns']} | "
                     f"{r['est_pairs']} | {r['date']} | {'; '.join(flags)} |")
    verdict = ("✅ **PASS** — proceed to Phase 2 conversion."
               if total_pairs >= HARD_FLOOR else
               f"🛑 **STOP** — estimated yield {total_pairs} < {HARD_FLOOR}. "
               "Report to F Mac; widen sources before training on thin data (§4.3).")
    lines += ["", f"**Yield verdict:** {verdict}", "",
              "**F Mac touchpoints:** confirm stale-flagged files are updated or cut; "
              "confirm nothing sensitive is in scope."]
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--out", type=Path, help="write markdown report here (default stdout)")
    args = ap.parse_args(argv)
    files = sorted(p for p in args.source.rglob("*.md") if p.is_file())
    if not files:
        print(f"no .md files under {args.source}", file=sys.stderr)
        return 2
    rows = [analyze_file(p, args.source) for p in files]
    report = build_report(rows)
    if args.out:
        args.out.write_text(report, encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        print(report)
    return 0 if sum(r["est_pairs"] for r in rows) >= HARD_FLOOR else 2


if __name__ == "__main__":
    sys.exit(main())
