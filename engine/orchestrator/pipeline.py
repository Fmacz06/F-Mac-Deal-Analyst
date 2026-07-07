#!/usr/bin/env python3
"""End-to-end pipeline — MASTER-BLUEPRINT §6 Phase 9.

prompt -> router -> local specialist (mlx_lm.server) -> HandUp
       -> Claude polish when flagged, or Claude directly for "claude" routes.

Mirrors the Threatic/Fable pattern: local ideation/domain reasoning ->
structured output -> Claude polish/expansion.

Claude calls use the official `anthropic` SDK (pip install anthropic) and
resolve credentials from the environment (ANTHROPIC_API_KEY or an
`ant auth login` profile). The SDK import is lazy so the rest of the
pipeline — and the tests — run without it installed.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from router.router import Router, DISPATCH, LOCAL_ENDPOINT  # noqa: E402
from orchestrator.handup import HandUp  # noqa: E402

POLISH_DIR = Path(__file__).parent / "polish_prompts"
CLAUDE_MODEL = "claude-opus-4-8"

# Same system prompts used at training time — the adapter's activation key (§4.1).
SPECIALIST_SYSTEM_PROMPTS = {
    "coding": ("You are F Mac's senior engineering specialist. You follow the "
               "Software Development Protocol v3.0: test-first, Clear/Fuzzy/Missing "
               "triage, Checkpoints."),
    "reasoning": ("You are F Mac's reasoning specialist. You think in his frameworks: "
                  "money-as-composite-time, faith-rooted security, and his argument "
                  "structure. You reason like him, not like a generic assistant."),
    "video": ("You are F Mac's video and graphics specialist. You understand his "
              "video briefs, design intent, output specs, and style."),
    "design": ("You are F Mac's design and CAD specialist. You reason about design "
               "constraints, manufacturing tolerances, and 3D-printing decisions "
               "the way he does."),
}


class LocalSpecialist:
    """Client for mlx_lm.server's OpenAI-compatible endpoint."""

    def __init__(self, endpoint: str = LOCAL_ENDPOINT):
        self.endpoint = endpoint

    def complete(self, route: str, prompt: str, max_tokens: int = 2048,
                 timeout: float = 300.0) -> dict:
        body = json.dumps({
            "messages": [
                {"role": "system", "content": SPECIALIST_SYSTEM_PROMPTS[route]},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": max_tokens,
        }).encode()
        req = urllib.request.Request(self.endpoint, data=body,
                                     headers={"Content-Type": "application/json"})
        t0 = time.perf_counter()
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
        latency = time.perf_counter() - t0
        text = data["choices"][0]["message"]["content"]
        completion_tokens = data.get("usage", {}).get("completion_tokens", 0)
        return {
            "text": text,
            "latency_ms": round(latency * 1000, 1),
            "tok_s": round(completion_tokens / latency, 1) if latency else None,
        }


class ClaudeClient:
    """Polish/expansion layer via the official Anthropic SDK."""

    def __init__(self, model: str = CLAUDE_MODEL):
        self.model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import anthropic
            except ImportError as e:
                raise RuntimeError(
                    "Claude layer needs the anthropic SDK: pip install anthropic"
                ) from e
            self._client = anthropic.Anthropic()
        return self._client

    def complete(self, system: str, user: str, max_tokens: int = 16000) -> str:
        client = self._get_client()
        response = client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            thinking={"type": "adaptive"},
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(b.text for b in response.content if b.type == "text")


def load_polish_prompt(route: str) -> str:
    return (POLISH_DIR / f"{route}.txt").read_text(encoding="utf-8").strip()


class Pipeline:
    def __init__(self, router: Router | None = None,
                 specialist: LocalSpecialist | None = None,
                 claude: ClaudeClient | None = None,
                 log_path: Path | str | None = None):
        self.router = router or Router(
            log_path=log_path or Path(__file__).parent / "pipeline-log.jsonl")
        self.specialist = specialist or LocalSpecialist()
        self.claude = claude or ClaudeClient()

    def run(self, prompt: str, polish: bool | None = None) -> dict:
        """Returns {"handup": HandUp-dict, "final": str, "polished": bool}."""
        decision = self.router.route(prompt)

        if decision.route == "claude":
            # Confidence floor (§3.3): weak local answers never masquerade
            # as specialist answers — go straight to Claude.
            final = self.claude.complete(
                system="You are assisting F Mac (AP Capital).", user=prompt)
            handup = HandUp(task_type="claude", prompt=prompt, specialist_output="",
                            confidence=decision.confidence, needs_polish=False,
                            model_info={"model": self.claude.model})
            handup.validate()
            return {"handup": asdict(handup), "final": final, "polished": False}

        result = self.specialist.complete(decision.route, prompt)
        needs_polish = decision.needs_polish if polish is None else polish
        handup = HandUp(
            task_type=decision.route,
            prompt=prompt,
            specialist_output=result["text"],
            confidence=decision.confidence,
            needs_polish=needs_polish,
            polish_instructions=load_polish_prompt(decision.route) if needs_polish else "",
            model_info={"base": "mlx-community/Qwen2.5-14B-Instruct-4bit",
                        "adapter": DISPATCH[decision.route]["adapter"]},
            timing={"latency_ms": result["latency_ms"], "tok_s": result["tok_s"]},
        )
        handup.validate()

        final = result["text"]
        polished = False
        if needs_polish:
            final = self.claude.complete(
                system=handup.polish_instructions,
                user=f"ORIGINAL TASK:\n{prompt}\n\nSPECIALIST DRAFT:\n{result['text']}")
            polished = True
        return {"handup": asdict(handup), "final": final, "polished": polished}


def main(argv=None):
    ap = argparse.ArgumentParser(description="prompt -> route -> specialist -> polish")
    ap.add_argument("prompt", nargs="?", help="task prompt (or pipe via stdin)")
    ap.add_argument("--no-polish", action="store_true", help="skip the Claude polish step")
    ap.add_argument("--json", action="store_true", help="emit the full result as JSON")
    args = ap.parse_args(argv)
    prompt = args.prompt or sys.stdin.read()
    result = Pipeline().run(prompt, polish=False if args.no_polish else None)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        h = result["handup"]
        print(f"[route={h['task_type']} conf={h['confidence']} "
              f"polished={result['polished']}]\n")
        print(result["final"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
