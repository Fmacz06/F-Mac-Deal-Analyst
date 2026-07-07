#!/usr/bin/env python3
"""Blind A/B harness — MASTER-BLUEPRINT §6 Phase 4 (reused for Phase 6).

Three subcommands:

  collect  — run every task in tasks.json against (A) the local specialist and
             (B) Claude; write raw outputs + per-task tok/s and latency.
  blind    — seeded label-shuffle the raw outputs into scoring-doc.md
             (labels X/Y per task; the key is kept in a separate file F Mac
             does not open until scoring is done).
  unblind  — merge F Mac's scores.json with the key; emit the per-task,
             per-dimension results table for PROGRESS.md and apply the
             Phase 5 thresholds (A3: fidelity >= 3.5 AND correctness >= 3.0).

tasks.json format (10 real tasks from F Mac's backlog — 4 review /
3 architecture / 3 implementation, §11 A6):
  [{"id": "t01", "type": "code-review", "prompt": "..."}, ...]

scores.json format (filled in by F Mac after blind scoring, 1-5 per dimension):
  {"t01": {"X": {"fidelity": 4, "correctness": 5, "usefulness": 4},
           "Y": {...}}, ...}
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from orchestrator.pipeline import LocalSpecialist, ClaudeClient  # noqa: E402
from router.router import Router  # noqa: E402

DIMENSIONS = ("fidelity", "correctness", "usefulness")
GO_THRESHOLDS = {"fidelity": 3.5, "correctness": 3.0}  # §11 A3


def cmd_collect(args, specialist=None, claude=None, router=None):
    tasks = json.loads(args.tasks.read_text(encoding="utf-8"))
    specialist = specialist or LocalSpecialist()
    claude = claude or ClaudeClient()
    router = router or Router(llm_classify=lambda t: args.route)
    args.outdir.mkdir(parents=True, exist_ok=True)
    for task in tasks:
        out_path = args.outdir / f"{task['id']}.json"
        if out_path.exists():
            print(f"{task['id']}: exists, skipping")
            continue
        route = router.route(task["prompt"]).route
        if route == "claude":
            route = args.route  # force the specialist under test for A/B
        local = specialist.complete(route, task["prompt"])
        t0 = time.perf_counter()
        claude_text = claude.complete(
            system="You are assisting F Mac (AP Capital) with an engineering task.",
            user=task["prompt"])
        claude_ms = round((time.perf_counter() - t0) * 1000, 1)
        out_path.write_text(json.dumps({
            "id": task["id"], "type": task.get("type", ""), "prompt": task["prompt"],
            "A_local": {"text": local["text"], "latency_ms": local["latency_ms"],
                        "tok_s": local["tok_s"], "route": route},
            "B_claude": {"text": claude_text, "latency_ms": claude_ms},
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{task['id']}: collected (local {local['latency_ms']}ms, "
              f"claude {claude_ms}ms)")
    return 0


def cmd_blind(args):
    rng = random.Random(args.seed)
    key = {}
    doc = ["# Blind A/B scoring — F Mac",
           "",
           "Score each output 1–5 on: **methodology fidelity** "
           "('sounds like my protocol'), **technical correctness**, "
           "**usefulness as first draft**. Record scores in scores.json "
           "(template below the tasks). Do NOT open blind_key.json until done.",
           ""]
    template = {}
    for path in sorted(args.outdir.glob("*.json")):
        if path.name in ("blind_key.json", "scores.json"):
            continue
        raw = json.loads(path.read_text(encoding="utf-8"))
        flip = rng.random() < 0.5
        key[raw["id"]] = {"X": "local" if not flip else "claude",
                          "Y": "claude" if not flip else "local"}
        x_text = raw["A_local"]["text"] if not flip else raw["B_claude"]["text"]
        y_text = raw["B_claude"]["text"] if not flip else raw["A_local"]["text"]
        doc += [f"---\n\n## Task {raw['id']} ({raw['type']})",
                f"\n**PROMPT:**\n\n{raw['prompt']}",
                f"\n### Output X\n\n{x_text}",
                f"\n### Output Y\n\n{y_text}", ""]
        template[raw["id"]] = {label: {d: 0 for d in DIMENSIONS} for label in ("X", "Y")}
    doc += ["---\n\n## scores.json template\n",
            "```json", json.dumps(template, indent=2), "```"]
    (args.outdir / "scoring-doc.md").write_text("\n".join(doc), encoding="utf-8")
    (args.outdir / "blind_key.json").write_text(json.dumps(key, indent=2),
                                                encoding="utf-8")
    print(f"wrote scoring-doc.md + blind_key.json ({len(key)} tasks, seed {args.seed})")
    return 0


def cmd_unblind(args):
    key = json.loads((args.outdir / "blind_key.json").read_text(encoding="utf-8"))
    scores = json.loads(args.scores.read_text(encoding="utf-8"))
    rows, sums = [], {"local": {d: 0.0 for d in DIMENSIONS},
                      "claude": {d: 0.0 for d in DIMENSIONS}}
    for task_id, labels in sorted(scores.items()):
        row = {"task": task_id}
        for label in ("X", "Y"):
            system = key[task_id][label]
            for d in DIMENSIONS:
                row[f"{system}_{d}"] = labels[label][d]
                sums[system][d] += labels[label][d]
        rows.append(row)
    n = len(rows)
    avg = {s: {d: round(v / n, 2) for d, v in dims.items()} for s, dims in sums.items()}

    lines = ["## Phase 4 A/B results (unblinded)", "",
             "| Task | Local fid | Local corr | Local use | Claude fid | Claude corr | Claude use |",
             "|---|---:|---:|---:|---:|---:|---:|"]
    for r in rows:
        lines.append(f"| {r['task']} | {r['local_fidelity']} | {r['local_correctness']} | "
                     f"{r['local_usefulness']} | {r['claude_fidelity']} | "
                     f"{r['claude_correctness']} | {r['claude_usefulness']} |")
    lines += ["", f"**Local averages:** fidelity {avg['local']['fidelity']} · "
                  f"correctness {avg['local']['correctness']} · "
                  f"usefulness {avg['local']['usefulness']}",
              f"**Claude averages:** fidelity {avg['claude']['fidelity']} · "
              f"correctness {avg['claude']['correctness']} · "
              f"usefulness {avg['claude']['usefulness']}", ""]

    go = (avg["local"]["fidelity"] >= GO_THRESHOLDS["fidelity"]
          and avg["local"]["correctness"] >= GO_THRESHOLDS["correctness"])
    if go:
        verdict = "**GO** — thresholds met (§11 A3). Phase 6 unlocks."
    elif avg["local"]["fidelity"] < GO_THRESHOLDS["fidelity"]:
        verdict = ("**DIAGNOSE** — fidelity thin: dataset problem. Map failed task "
                   "types to corpus gaps; loop Phases 2–4. Do NOT change the base model.")
    else:
        verdict = ("**ESCALATE** — fidelity fine, code quality thin: re-run the same "
                   "dataset on Qwen2.5-Coder-14B-Instruct-4bit and re-A/B (§2 C2).")
    lines.append(f"**Phase 5 verdict:** {verdict}")
    report = "\n".join(lines) + "\n"
    (args.outdir / "results.md").write_text(report, encoding="utf-8")
    print(report)
    return 0 if go else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("collect")
    c.add_argument("--tasks", type=Path, required=True)
    c.add_argument("--outdir", type=Path, default=Path(__file__).parent / "runs")
    c.add_argument("--route", default="coding",
                   help="specialist under test (coding for Phase 4, reasoning for 6)")
    b = sub.add_parser("blind")
    b.add_argument("--outdir", type=Path, default=Path(__file__).parent / "runs")
    b.add_argument("--seed", type=int, default=42)
    u = sub.add_parser("unblind")
    u.add_argument("--outdir", type=Path, default=Path(__file__).parent / "runs")
    u.add_argument("--scores", type=Path, required=True)
    args = ap.parse_args(argv)
    return {"collect": cmd_collect, "blind": cmd_blind, "unblind": cmd_unblind}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
