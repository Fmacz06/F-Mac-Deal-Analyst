"""Phase 9 pipeline tests — local specialist and Claude layers are stubbed
so these run anywhere (no server, no API key).
Run: python3 -m unittest discover -s engine/orchestrator/tests -v
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from router.router import Router  # noqa: E402
from orchestrator.handup import HandUp  # noqa: E402
from orchestrator import pipeline as P  # noqa: E402


class StubSpecialist:
    endpoint = "stub://local"

    def __init__(self):
        self.calls = []

    def complete(self, route, prompt, **kw):
        self.calls.append((route, prompt))
        return {"text": f"[{route} draft] answer", "latency_ms": 12.0, "tok_s": 30.0}


class StubClaude:
    model = "claude-opus-4-8"

    def __init__(self):
        self.calls = []

    def complete(self, system, user, **kw):
        self.calls.append((system, user))
        return "[claude output]"


def make_pipeline(llm_answer="general"):
    router = Router(llm_classify=lambda text: llm_answer)
    return P.Pipeline(router=router, specialist=StubSpecialist(),
                      claude=StubClaude()), router


class TestHandUp(unittest.TestCase):
    def test_roundtrip(self):
        h = HandUp(task_type="coding", prompt="p", specialist_output="o",
                   confidence=0.8, needs_polish=False)
        self.assertEqual(HandUp.from_json(h.to_json()), h)

    def test_validate_rejects_bad_route(self):
        h = HandUp(task_type="poetry", prompt="p", specialist_output="o",
                   confidence=0.5, needs_polish=False)
        with self.assertRaises(ValueError):
            h.validate()

    def test_polish_requires_instructions(self):
        h = HandUp(task_type="coding", prompt="p", specialist_output="o",
                   confidence=0.5, needs_polish=True, polish_instructions="")
        with self.assertRaises(ValueError):
            h.validate()


class TestPipeline(unittest.TestCase):
    def test_coding_route_no_polish_by_default(self):
        pipe, _ = make_pipeline()
        result = pipe.run("Fix this bug:\n```python\nx = None\nx.y\n```")
        self.assertEqual(result["handup"]["task_type"], "coding")
        self.assertFalse(result["polished"])
        self.assertIn("[coding draft]", result["final"])
        self.assertEqual(pipe.claude.calls, [])

    def test_reasoning_route_gets_polished(self):
        pipe, _ = make_pipeline()
        result = pipe.run("Help me think through the eschatology chapter thesis")
        self.assertEqual(result["handup"]["task_type"], "reasoning")
        self.assertTrue(result["polished"])
        self.assertEqual(result["final"], "[claude output]")
        # polish call carries the specialist draft
        system, user = pipe.claude.calls[0]
        self.assertIn("reasoning specialist", system)
        self.assertIn("[reasoning draft]", user)

    def test_claude_floor_route_skips_specialist(self):
        pipe, _ = make_pipeline(llm_answer="general")
        result = pipe.run("What's a good gift for my brother?")
        self.assertEqual(result["handup"]["task_type"], "claude")
        self.assertEqual(result["final"], "[claude output]")
        self.assertEqual(pipe.specialist.calls, [])

    def test_polish_override(self):
        pipe, _ = make_pipeline()
        result = pipe.run("Review:\n```js\nlet a=1\n```", polish=True)
        self.assertTrue(result["polished"])
        self.assertIn("polish layer", pipe.claude.calls[0][0])

    def test_handup_carries_model_and_timing(self):
        pipe, _ = make_pipeline()
        result = pipe.run("```py\nprint(1)\n```")
        h = result["handup"]
        self.assertEqual(h["model_info"]["model"], "fmac-coding")
        self.assertEqual(h["timing"]["latency_ms"], 12.0)

    def test_all_polish_prompts_exist_and_nonempty(self):
        for route in ("coding", "reasoning", "video", "design"):
            self.assertGreater(len(P.load_polish_prompt(route)), 100, route)


if __name__ == "__main__":
    unittest.main()
