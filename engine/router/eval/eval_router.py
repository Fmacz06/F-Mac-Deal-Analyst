#!/usr/bin/env python3
"""Router eval harness — Phase 8 gate: >=90% correct on a 50-prompt set.

Two modes:
  offline (default): rules layer + a simulated "general" LLM fallback — i.e.
    ambiguous prompts fall to Claude. Runs anywhere, used in CI.
  --live: uses the real local mlx_lm.server endpoint for the LLM fallback.
    Run on the Mac Studio with the server up.

The seed eval set ships with the repo; per §3.3 the routing log from real
usage (Phase 4/6 task logs) should progressively REPLACE these seeds.

Usage: python3 eval_router.py [--live] [--eval-set eval_set.jsonl]
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import router as R  # noqa: E402

GATE = 0.90


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--eval-set", type=Path,
                    default=Path(__file__).parent / "eval_set.jsonl")
    ap.add_argument("--live", action="store_true",
                    help="use the real local LLM fallback (server must be up)")
    args = ap.parse_args(argv)

    cases = [json.loads(l) for l in args.eval_set.read_text(encoding="utf-8").splitlines()
             if l.strip()]
    rt = (R.Router() if args.live
          else R.Router(llm_classify=lambda text: "general"))

    correct, misses, per_route = 0, [], {}
    for case in cases:
        d = rt.route(case["prompt"])
        exp = case["expected"]
        per_route.setdefault(exp, [0, 0])[1] += 1
        if d.route == exp:
            correct += 1
            per_route[exp][0] += 1
        else:
            misses.append((exp, d.route, d.method, case["prompt"][:70]))

    acc = correct / len(cases)
    print(f"accuracy: {correct}/{len(cases)} = {acc:.1%}  (gate: >={GATE:.0%})")
    for route, (ok, total) in sorted(per_route.items()):
        print(f"  {route:10s} {ok}/{total}")
    if misses:
        print("\nmisses (expected -> got [method]):")
        for exp, got, method, preview in misses:
            print(f"  {exp:10s} -> {got:10s} [{method:5s}]  {preview}")
    print("\nGATE:", "PASS" if acc >= GATE else "FAIL")
    return 0 if acc >= GATE else 1


if __name__ == "__main__":
    sys.exit(main())
