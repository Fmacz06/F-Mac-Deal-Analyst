#!/usr/bin/env python3
"""Router — MASTER-BLUEPRINT §3.3 / §6 Phase 8.

Layer 1: rules (keyword/pattern table) handles the obvious ~80%.
Layer 2: one cheap classification call to the LOCAL base model (mlx_lm.server,
         OpenAI-compatible) for ambiguous input.
Floor:   below confidence threshold, or classified "general" -> route to Claude.
         A weak local answer never masquerades as a specialist answer.
Flag:    every specialist response carries needs_polish for the Claude layer.
Log:     every decision -> JSONL (input hash, route, confidence, method,
         latency). The log IS the future eval set.

Stdlib only. Adapter swap = restart mlx_lm.server with a different
--adapter-path (v1 per §11 A5); the dispatch table records which adapter
each route needs so the orchestrator can manage the restart.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, asdict
from pathlib import Path

ROUTES = ("coding", "reasoning", "video", "design", "claude")
CONFIDENCE_FLOOR = 0.55
LOCAL_ENDPOINT = "http://127.0.0.1:8080/v1/chat/completions"

# Dispatch table: route -> adapter the server must be running (§3.3).
DISPATCH = {
    "coding":    {"adapter": "adapters/coding",    "needs_polish_default": False},
    "reasoning": {"adapter": "adapters/reasoning", "needs_polish_default": True},
    "video":     {"adapter": "adapters/video",     "needs_polish_default": True},
    "design":    {"adapter": "adapters/design",    "needs_polish_default": True},
    "claude":    {"adapter": None,                 "needs_polish_default": False},
}

# ---- Layer 1: rules ------------------------------------------------------
# (pattern, route, weight). Weights accumulate per route; strongest wins.
_RULES: list[tuple[re.Pattern, str, float]] = [
    # coding — code fences, stack traces, file extensions, dev vocabulary
    (re.compile(r"```"), "coding", 3.0),
    (re.compile(r"Traceback \(most recent call last\)|^\s+at \w[\w.$]*\(", re.M), "coding", 3.0),
    (re.compile(r"\b\w+\.(?:py|js|ts|tsx|jsx|go|rs|java|rb|c|cpp|h|swift|sql|sh|yml|yaml|json|html|css)\b"), "coding", 2.0),
    (re.compile(r"\b(?:refactor|unit test|test-first|TDD|stack trace|null pointer|"
                r"exception|regression|pull request|merge conflict|code review|"
                r"debug(?:ging)?|compil(?:e|er|ation)|API endpoint|function|class method|"
                r"bug|linter|type error|architectur\w+|test plan)\b", re.I), "coding", 1.5),
    # reasoning — think-it-through, theology, book/argument work
    (re.compile(r"\b(?:help me think through|what if|think through|walk me through the logic|"
                r"theolog\w+|eschatolog\w+|scripture|doctrine|chapter|thesis|argument|"
                r"first principles|worldview|conviction|framework for)\b", re.I), "reasoning", 2.0),
    (re.compile(r"\b(?:should I|is it wise|trade-?offs?|pros and cons|implications)\b", re.I), "reasoning", 1.0),
    # video/graphics — briefs, storyboards, render specs
    (re.compile(r"\b(?:storyboard|video brief|render spec|b-?roll|color grade|"
                r"motion graphics|frame rate|aspect ratio|edit(?:ing)? timeline|"
                r"thumbnail|footage|scene list)\b", re.I), "video", 2.5),
    # design/CAD — tolerances, sketches, printing
    (re.compile(r"\bsketch\w*\b", re.I), "design", 1.0),
    (re.compile(r"\b(?:toleranc\w+|CAD|3[dD][- ]print\w*|extrude|fillet|"
                r"chamfer|dimension(?:ing)?|manufactur\w+|injection mold\w*|"
                r"assembly fit|clearance fit|STL|STEP file)\b", re.I), "design", 2.5),
]


@dataclass
class RouteDecision:
    route: str
    confidence: float
    method: str          # "rules" | "llm" | "floor"
    needs_polish: bool
    latency_ms: float
    input_hash: str
    scores: dict


def _rule_scores(text: str) -> dict:
    scores: dict[str, float] = {}
    for pat, route, weight in _RULES:
        n = len(pat.findall(text))
        if n:
            scores[route] = scores.get(route, 0.0) + weight * min(n, 3)
    return scores


def _rules_decision(text: str) -> tuple[str | None, float, dict]:
    scores = _rule_scores(text)
    if not scores:
        return None, 0.0, scores
    ranked = sorted(scores.items(), key=lambda kv: -kv[1])
    top_route, top = ranked[0]
    second = ranked[1][1] if len(ranked) > 1 else 0.0
    # confidence: dominance of the winner, scaled by absolute score mass
    dominance = (top - second) / top if top else 0.0
    confidence = min(0.95, dominance * min(1.0, top / 2.0))
    return top_route, confidence, scores


# ---- Layer 2: local-LLM fallback ----------------------------------------

_CLASSIFY_PROMPT = (
    "Classify this task into exactly one word from: coding, reasoning, video, "
    "design, general. Reply with the single word only.\n\nTask:\n{task}"
)


def _llm_classify(text: str, endpoint: str, timeout: float = 20.0) -> str | None:
    """One cheap classification call to the local base model. Returns a route
    name, 'general', or None on any failure (caller falls to Claude)."""
    body = json.dumps({
        "messages": [{"role": "user",
                      "content": _CLASSIFY_PROMPT.format(task=text[:2000])}],
        "max_tokens": 8,
        "temperature": 0.0,
    }).encode()
    req = urllib.request.Request(endpoint, data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
        word = data["choices"][0]["message"]["content"].strip().lower()
        word = re.sub(r"[^a-z]", "", word)
        return word if word in (*ROUTES, "general") else None
    except (urllib.error.URLError, KeyError, IndexError, json.JSONDecodeError,
            TimeoutError, OSError):
        return None


# ---- public API ----------------------------------------------------------

class Router:
    def __init__(self, endpoint: str = LOCAL_ENDPOINT,
                 floor: float = CONFIDENCE_FLOOR,
                 log_path: Path | str | None = None,
                 llm_classify=None):
        self.endpoint = endpoint
        self.floor = floor
        self.log_path = Path(log_path) if log_path else None
        # injectable for tests; defaults to the real local call
        self._llm_classify = llm_classify or (
            lambda text: _llm_classify(text, self.endpoint))

    def route(self, text: str) -> RouteDecision:
        t0 = time.perf_counter()
        route, confidence, scores = _rules_decision(text)
        method = "rules"
        if route is None or confidence < self.floor:
            word = self._llm_classify(text)
            if word in ROUTES and word != "claude":
                route, confidence, method = word, max(confidence, 0.6), "llm"
            else:
                # unclassifiable or "general" -> Claude floor (§3.3)
                route, confidence, method = "claude", confidence, "floor"
        needs_polish = DISPATCH[route]["needs_polish_default"]
        decision = RouteDecision(
            route=route, confidence=round(confidence, 3), method=method,
            needs_polish=needs_polish,
            latency_ms=round((time.perf_counter() - t0) * 1000, 2),
            input_hash=hashlib.sha256(text.encode()).hexdigest()[:16],
            scores=scores,
        )
        self._log(decision)
        return decision

    def _log(self, decision: RouteDecision) -> None:
        if not self.log_path:
            return
        entry = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), **asdict(decision)}
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")


if __name__ == "__main__":
    import sys
    text = sys.stdin.read() if not sys.stdin.isatty() else " ".join(sys.argv[1:])
    d = Router(log_path=Path(__file__).parent / "routing-log.jsonl").route(text)
    print(json.dumps(asdict(d), indent=2))
