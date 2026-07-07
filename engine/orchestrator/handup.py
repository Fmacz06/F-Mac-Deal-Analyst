#!/usr/bin/env python3
"""Structured hand-up format — MASTER-BLUEPRINT §6 Phase 9.

The contract between the local specialist layer and the Claude polish layer.
Every specialist response is wrapped in a HandUp before anything is shown to
F Mac or sent to Claude.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict, field


@dataclass
class HandUp:
    task_type: str                 # coding | reasoning | video | design | claude
    prompt: str                    # the original user prompt
    specialist_output: str         # raw local-model output ("" when routed to Claude)
    confidence: float              # router confidence for the route
    needs_polish: bool             # escalation flag (§3.3)
    polish_instructions: str = ""  # domain-specific polish prompt (loaded per route)
    model_info: dict = field(default_factory=dict)   # base model, adapter path
    timing: dict = field(default_factory=dict)       # latency_ms, tok_s

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, raw: str) -> "HandUp":
        return cls(**json.loads(raw))

    def validate(self) -> None:
        if self.task_type not in ("coding", "reasoning", "video", "design", "claude"):
            raise ValueError(f"bad task_type: {self.task_type}")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence out of range: {self.confidence}")
        if self.needs_polish and not self.polish_instructions:
            raise ValueError("needs_polish set but no polish_instructions")
