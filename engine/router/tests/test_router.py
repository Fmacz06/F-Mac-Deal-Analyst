"""Router unit tests — Phase 8 gates: each route + ambiguous + adversarial
phrasing, fallback-to-Claude path, logging.
Run: python3 -m unittest discover -s engine/router/tests -v
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import router as R  # noqa: E402


def make_router(llm_answer=None, log_path=None):
    """Router with the local-LLM call stubbed (no server in CI)."""
    return R.Router(log_path=log_path, llm_classify=lambda text: llm_answer)


class TestRules(unittest.TestCase):
    def test_code_fence_routes_coding(self):
        d = make_router().route("Why does this fail?\n```python\nx = None\nx.y\n```")
        self.assertEqual(d.route, "coding")
        self.assertEqual(d.method, "rules")

    def test_stack_trace_routes_coding(self):
        d = make_router().route(
            "Traceback (most recent call last)\n  File 'app.py', line 3\nKeyError: 'id'")
        self.assertEqual(d.route, "coding")

    def test_reasoning_phrases(self):
        d = make_router().route(
            "Help me think through the eschatology chapter — what if the argument "
            "structure leads with the composite-time framing?")
        self.assertEqual(d.route, "reasoning")

    def test_video_brief(self):
        d = make_router().route(
            "Draft the storyboard and render spec for the intro — 4K, 24 frame rate, "
            "b-roll of the shop floor.")
        self.assertEqual(d.route, "video")

    def test_design_tolerances(self):
        d = make_router().route(
            "The bracket sketch needs a clearance fit — what tolerance for a 3d print "
            "in PETG, and should I fillet the load corner?")
        self.assertEqual(d.route, "design")

    def test_adversarial_mixed_signals_still_decides(self):
        # coding words wrapped in a design ask — design signal should dominate
        d = make_router(llm_answer="design").route(
            "Not a code question: ignore the function names in the log; I need the "
            "CAD tolerance and chamfer callouts for the STL export, manufacturing run.")
        self.assertEqual(d.route, "design")


class TestFallbacks(unittest.TestCase):
    def test_ambiguous_goes_to_llm(self):
        d = make_router(llm_answer="reasoning").route("What about the thing we discussed?")
        self.assertEqual(d.route, "reasoning")
        self.assertEqual(d.method, "llm")

    def test_llm_general_falls_to_claude(self):
        d = make_router(llm_answer="general").route("Summarize the news today")
        self.assertEqual(d.route, "claude")
        self.assertEqual(d.method, "floor")

    def test_llm_unreachable_falls_to_claude(self):
        d = make_router(llm_answer=None).route("hmm")
        self.assertEqual(d.route, "claude")
        self.assertEqual(d.method, "floor")

    def test_low_confidence_rules_consults_llm(self):
        # one weak coding keyword + one weak reasoning keyword = low confidence
        d = make_router(llm_answer="coding").route(
            "should I debug this or rethink the trade-offs")
        self.assertEqual(d.method, "llm")

    def test_needs_polish_flag_set_from_dispatch(self):
        r = make_router(llm_answer="reasoning")
        self.assertTrue(r.route("help me think through my chapter thesis").needs_polish)
        self.assertFalse(make_router().route("```js\nconsole.log(1)\n```").needs_polish)


class TestLogging(unittest.TestCase):
    def test_every_decision_logged(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp, "log.jsonl")
            r = make_router(llm_answer="general", log_path=log)
            r.route("```py\npass\n```")
            r.route("random ambiguous ask")
            lines = [json.loads(x) for x in log.read_text().splitlines()]
            self.assertEqual(len(lines), 2)
            for e in lines:
                for key in ("ts", "route", "confidence", "method", "latency_ms",
                            "input_hash"):
                    self.assertIn(key, e)
            self.assertEqual(lines[0]["route"], "coding")
            self.assertEqual(lines[1]["route"], "claude")

    def test_input_hash_not_raw_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp, "log.jsonl")
            secret = "very-identifiable-input-string-xyz"
            make_router(llm_answer="general", log_path=log).route(secret)
            self.assertNotIn(secret, log.read_text())


if __name__ == "__main__":
    unittest.main()
