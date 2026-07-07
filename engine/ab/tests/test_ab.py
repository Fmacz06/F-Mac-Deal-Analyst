"""A/B harness tests — blind shuffle determinism, key separation, unblind math,
and the Phase 5 GO/DIAGNOSE/ESCALATE verdict logic.
Run: python3 -m unittest discover -s engine/ab/tests -v
"""
import json
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import importlib
ab = importlib.import_module("ab.ab_test")


def write_run(outdir: Path, task_id: str):
    (outdir / f"{task_id}.json").write_text(json.dumps({
        "id": task_id, "type": "code-review", "prompt": f"prompt {task_id}",
        "A_local": {"text": f"first-system-{task_id}", "latency_ms": 100, "tok_s": 25,
                    "route": "coding"},
        "B_claude": {"text": f"second-system-{task_id}", "latency_ms": 900},
    }), encoding="utf-8")


def scores_for(key, local_scores, claude_scores):
    """Build a scores.json dict that assigns fixed scores per underlying system."""
    out = {}
    for task_id, mapping in key.items():
        out[task_id] = {}
        for label in ("X", "Y"):
            src = local_scores if mapping[label] == "local" else claude_scores
            out[task_id][label] = dict(src)
    return out


class TestBlind(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.outdir = Path(self.tmp.name)
        for i in range(10):
            write_run(self.outdir, f"t{i:02d}")

    def test_blind_produces_doc_and_key_with_all_tasks(self):
        ab.cmd_blind(Namespace(outdir=self.outdir, seed=7))
        key = json.loads((self.outdir / "blind_key.json").read_text())
        self.assertEqual(len(key), 10)
        doc = (self.outdir / "scoring-doc.md").read_text()
        for i in range(10):
            self.assertIn(f"t{i:02d}", doc)
        # doc must not reveal which side is which
        self.assertNotIn("local", doc.lower().replace("scores.json", ""))

    def test_blind_is_seeded_and_actually_shuffles(self):
        ab.cmd_blind(Namespace(outdir=self.outdir, seed=7))
        key1 = json.loads((self.outdir / "blind_key.json").read_text())
        ab.cmd_blind(Namespace(outdir=self.outdir, seed=7))
        key2 = json.loads((self.outdir / "blind_key.json").read_text())
        self.assertEqual(key1, key2)
        assignments = {key1[t]["X"] for t in key1}
        self.assertEqual(assignments, {"local", "claude"},
                         "with 10 tasks both orderings should occur")

    def test_unblind_go_verdict(self):
        ab.cmd_blind(Namespace(outdir=self.outdir, seed=7))
        key = json.loads((self.outdir / "blind_key.json").read_text())
        scores = scores_for(key,
                            {"fidelity": 4, "correctness": 4, "usefulness": 4},
                            {"fidelity": 3, "correctness": 5, "usefulness": 5})
        scores_path = self.outdir / "scores.json"
        scores_path.write_text(json.dumps(scores))
        rc = ab.cmd_unblind(Namespace(outdir=self.outdir, scores=scores_path))
        self.assertEqual(rc, 0)
        results = (self.outdir / "results.md").read_text()
        self.assertIn("**GO**", results)
        self.assertIn("fidelity 4.0", results)

    def test_unblind_diagnose_verdict_when_fidelity_thin(self):
        ab.cmd_blind(Namespace(outdir=self.outdir, seed=7))
        key = json.loads((self.outdir / "blind_key.json").read_text())
        scores = scores_for(key,
                            {"fidelity": 2, "correctness": 4, "usefulness": 3},
                            {"fidelity": 3, "correctness": 5, "usefulness": 5})
        scores_path = self.outdir / "scores.json"
        scores_path.write_text(json.dumps(scores))
        rc = ab.cmd_unblind(Namespace(outdir=self.outdir, scores=scores_path))
        self.assertEqual(rc, 1)
        self.assertIn("**DIAGNOSE**", (self.outdir / "results.md").read_text())

    def test_unblind_escalate_verdict_when_correctness_thin(self):
        ab.cmd_blind(Namespace(outdir=self.outdir, seed=7))
        key = json.loads((self.outdir / "blind_key.json").read_text())
        scores = scores_for(key,
                            {"fidelity": 4, "correctness": 2, "usefulness": 3},
                            {"fidelity": 3, "correctness": 5, "usefulness": 5})
        scores_path = self.outdir / "scores.json"
        scores_path.write_text(json.dumps(scores))
        rc = ab.cmd_unblind(Namespace(outdir=self.outdir, scores=scores_path))
        self.assertEqual(rc, 1)
        self.assertIn("**ESCALATE**", (self.outdir / "results.md").read_text())


class StubSpecialist:
    def complete(self, route, prompt, **kw):
        return {"text": "local answer", "latency_ms": 10.0, "tok_s": 20.0}


class StubClaude:
    model = "claude-opus-4-8"

    def complete(self, system, user, **kw):
        return "claude answer"


class TestCollect(unittest.TestCase):
    def test_collect_writes_one_file_per_task(self):
        with tempfile.TemporaryDirectory() as tmp:
            tasks = Path(tmp, "tasks.json")
            tasks.write_text(json.dumps([
                {"id": "t01", "type": "code-review", "prompt": "review ```py\nx=1\n```"},
                {"id": "t02", "type": "architecture", "prompt": "plan the refactor"},
            ]))
            outdir = Path(tmp, "runs")
            from router.router import Router
            ab.cmd_collect(
                Namespace(tasks=tasks, outdir=outdir, route="coding"),
                specialist=StubSpecialist(), claude=StubClaude(),
                router=Router(llm_classify=lambda t: "coding"))
            files = sorted(p.name for p in outdir.glob("*.json"))
            self.assertEqual(files, ["t01.json", "t02.json"])
            data = json.loads((outdir / "t01.json").read_text())
            self.assertEqual(data["A_local"]["text"], "local answer")
            self.assertEqual(data["B_claude"]["text"], "claude answer")


if __name__ == "__main__":
    unittest.main()
