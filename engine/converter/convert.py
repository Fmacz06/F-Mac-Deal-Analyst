#!/usr/bin/env python3
"""JSONL conversion pipeline — MASTER-BLUEPRINT §6 Phase 2.

Turns a folder of markdown conversation exports into an mlx-lm chat-format
dataset. Reusable across adapters (coding / reasoning / design): nothing in
here is corpus-specific — the system prompt and source folder are parameters.

Outputs (into --out):
  train.jsonl / valid.jsonl   90/10 seeded-random split, chat schema
  sample-20.md                human-readable random sample for the spot-check
  stats.md / stats.json       pair counts, per-source yield, length dist, drops
  provenance.json             pair id -> source file (kept OUTSIDE training data)

Stdlib only. Python 3.9+.
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import random
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------- parsing

# Speaker-header patterns seen in common chat .md exports. Order matters:
# first match on a line wins. Each maps to canonical role "user"/"assistant".
_USER_NAMES = r"(?:User|Human|Me|F ?Mac|Prompt|You)"
_ASSISTANT_NAMES = r"(?:Assistant|Claude|AI|Model|Response|ChatGPT|GPT)"

TURN_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(rf"^#{{1,6}}\s*{_USER_NAMES}\s*:?\s*$", re.I), "user"),
    (re.compile(rf"^#{{1,6}}\s*{_ASSISTANT_NAMES}\s*:?\s*$", re.I), "assistant"),
    (re.compile(rf"^\*\*{_USER_NAMES}\*?\*?\s*[:：]", re.I), "user"),
    (re.compile(rf"^\*\*{_ASSISTANT_NAMES}\*?\*?\s*[:：]", re.I), "assistant"),
    (re.compile(rf"^{_USER_NAMES}\s*[:：]", re.I), "user"),
    (re.compile(rf"^{_ASSISTANT_NAMES}\s*[:：]", re.I), "assistant"),
]

_HEADER_STRIP = re.compile(
    rf"^(?:#{{1,6}}\s*|\*\*)?(?:{_USER_NAMES}|{_ASSISTANT_NAMES})"
    rf"(?:\*\*)?\s*[:：]?\s*(?:\*\*)?\s*",
    re.I,
)


@dataclass
class Turn:
    role: str
    text: str
    line: int  # 1-based line where the turn starts (for provenance)


def parse_turns(markdown: str) -> list[Turn]:
    """Split a markdown export into ordered user/assistant turns.

    Returns [] when no speaker markers are found (non-conversation doc —
    reported upstream, never guessed at). Consecutive same-role turns merge.
    """
    turns: list[Turn] = []
    current: Turn | None = None
    inside_fence = False
    for i, line in enumerate(markdown.splitlines(), start=1):
        if line.lstrip().startswith("```"):
            inside_fence = not inside_fence
        role = None
        if not inside_fence:
            for pat, r in TURN_PATTERNS:
                if pat.match(line.strip()):
                    role = r
                    break
        if role:
            if current is not None:
                turns.append(current)
            remainder = _HEADER_STRIP.sub("", line.strip(), count=1)
            current = Turn(role=role, text=remainder, line=i)
        elif current is not None:
            current.text += ("\n" if current.text else "") + line
    if current is not None:
        turns.append(current)
    # merge consecutive same-role turns, trim whitespace
    merged: list[Turn] = []
    for t in turns:
        t.text = t.text.strip()
        if merged and merged[-1].role == t.role:
            merged[-1].text += "\n\n" + t.text
        else:
            merged.append(t)
    return [t for t in merged if t.text]


# ---------------------------------------------------------------- filters

# Openers that are pure social glue — stripped from the front of a turn.
_PLEASANTRY_OPENERS = re.compile(
    r"^(?:(?:great|excellent|good|awesome|perfect)\s+(?:question|point|idea|catch)[!,. ]*"
    r"|thanks?(?:\s+you)?[!,. ]*|you'?re welcome[!,. ]*|sure(?: thing)?[!,. ]+"
    r"|of course[!,. ]+|absolutely[!,. ]+|certainly[!,. ]+"
    r"|i'?d be (?:happy|glad) to(?: help)?[!,. ]*)\s*",
    re.I,
)

# A user turn that is ONLY glue (no content) kills the pair.
_GLUE_ONLY = re.compile(
    r"^(?:ok(?:ay)?|k|thanks?(?: you)?|thx|ty|got it|sounds good|nice|cool|"
    r"perfect|great|awesome|yes|yep|yeah|no|nope|sure|lol|haha|hm+|continue|"
    r"go on|next)[!,.\s]*$",
    re.I,
)

# PII / secrets — any hit drops the pair and is counted by reason.
_PII_PATTERNS = {
    "email": re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]{2,}\b"),
    "api_key": re.compile(
        r"\b(?:sk-[A-Za-z0-9_-]{16,}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{20,}|"
        r"xox[bpars]-[A-Za-z0-9-]{10,}|AIza[0-9A-Za-z_-]{30,})\b"
    ),
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "phone": re.compile(r"\b(?:\+?1[ .-]?)?\(?\d{3}\)?[ .-]\d{3}[ .-]\d{4}\b"),
    "private_key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
}


def strip_pleasantries(text: str) -> str:
    prev = None
    while prev != text:
        prev = text
        text = _PLEASANTRY_OPENERS.sub("", text.lstrip())
    return text.strip()


def pii_hits(text: str) -> list[str]:
    return [name for name, pat in _PII_PATTERNS.items() if pat.search(text)]


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).lower()
    return re.sub(r"\s+", " ", text).strip()


class NearDupIndex:
    """O(n^2) near-duplicate check — fine at the 300–1,000-pair scale (§4.3)."""

    def __init__(self, threshold: float = 0.92, window: int = 2000):
        self.threshold = threshold
        self.window = window
        self._kept: list[str] = []

    def is_dup(self, text: str) -> bool:
        norm = _normalize(text)[: self.window]
        for existing in self._kept:
            if abs(len(existing) - len(norm)) / max(len(existing), len(norm), 1) > 0.3:
                continue
            if difflib.SequenceMatcher(None, existing, norm).ratio() >= self.threshold:
                return True
        self._kept.append(norm)
        return False


# ---------------------------------------------------------------- pipeline

@dataclass
class Pair:
    pair_id: str
    source: str
    line: int
    user: str
    assistant: str

    def to_chat(self, system_prompt: str) -> dict:
        return {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": self.user},
                {"role": "assistant", "content": self.assistant},
            ]
        }


@dataclass
class Stats:
    files_seen: int = 0
    files_unparsed: list[str] = field(default_factory=list)
    pairs_kept: int = 0
    drops: dict = field(default_factory=dict)
    per_source: dict = field(default_factory=dict)
    length_dist: dict = field(default_factory=dict)

    def drop(self, reason: str) -> None:
        self.drops[reason] = self.drops.get(reason, 0) + 1


LENGTH_BUCKETS = [(0, 200), (200, 500), (500, 1500), (1500, 4000), (4000, 10**9)]


def _bucket_label(n: int) -> str:
    for lo, hi in LENGTH_BUCKETS:
        if lo <= n < hi:
            return f"{lo}-{hi if hi < 10**9 else '+'}"
    return "?"


def extract_pairs(
    md_files: list[Path],
    root: Path,
    stats: Stats,
    min_assistant_chars: int = 80,
    max_pair_chars: int = 24000,
) -> list[Pair]:
    """Every user->assistant exchange becomes one candidate pair (§4.3:
    long threads become multiple single-lesson pairs)."""
    dup_index = NearDupIndex()
    pairs: list[Pair] = []
    for path in sorted(md_files):
        rel = str(path.relative_to(root))
        stats.files_seen += 1
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            stats.files_unparsed.append(rel)
            continue
        turns = parse_turns(text)
        if not turns:
            stats.files_unparsed.append(rel)
            continue
        source_kept = 0
        for i in range(len(turns) - 1):
            if turns[i].role != "user" or turns[i + 1].role != "assistant":
                continue
            user = strip_pleasantries(turns[i].text)
            assistant = strip_pleasantries(turns[i + 1].text)
            if not user or _GLUE_ONLY.match(user):
                stats.drop("glue_only_user")
                continue
            if len(assistant) < min_assistant_chars:
                stats.drop("assistant_too_short")
                continue
            if len(user) + len(assistant) > max_pair_chars:
                stats.drop("pair_too_long")
                continue
            hits = pii_hits(user) + pii_hits(assistant)
            if hits:
                stats.drop(f"pii:{','.join(sorted(set(hits)))}")
                continue
            if dup_index.is_dup(user + "\n" + assistant):
                stats.drop("near_duplicate")
                continue
            pid = hashlib.sha256(f"{rel}:{turns[i].line}:{user[:80]}".encode()).hexdigest()[:12]
            pairs.append(Pair(pid, rel, turns[i].line, user, assistant))
            source_kept += 1
            stats.length_dist[_bucket_label(len(user) + len(assistant))] = (
                stats.length_dist.get(_bucket_label(len(user) + len(assistant)), 0) + 1
            )
        stats.per_source[rel] = source_kept
    stats.pairs_kept = len(pairs)
    return pairs


def split_pairs(pairs: list[Pair], seed: int, val_frac: float = 0.1):
    rng = random.Random(seed)
    shuffled = pairs[:]
    rng.shuffle(shuffled)
    n_val = max(1, round(len(shuffled) * val_frac)) if len(shuffled) > 1 else 0
    return shuffled[n_val:], shuffled[:n_val]


# ---------------------------------------------------------------- schema

def validate_chat_line(line: str) -> None:
    """Raise ValueError unless the line matches the mlx-lm chat schema (§4.1)."""
    obj = json.loads(line)
    msgs = obj.get("messages")
    if not isinstance(msgs, list) or len(msgs) < 2:
        raise ValueError("messages must be a list of >=2 entries")
    for m in msgs:
        if not isinstance(m, dict) or set(m) != {"role", "content"}:
            raise ValueError(f"bad message keys: {m}")
        if m["role"] not in ("system", "user", "assistant"):
            raise ValueError(f"bad role: {m['role']}")
        if not isinstance(m["content"], str) or not m["content"]:
            raise ValueError("content must be a non-empty string")
    if msgs[-1]["role"] != "assistant":
        raise ValueError("final message must be assistant (it is the completion)")


def validate_jsonl_file(path: Path) -> int:
    n = 0
    with path.open(encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                validate_chat_line(line)
            except ValueError as e:
                raise ValueError(f"{path.name}:{i}: {e}") from e
            n += 1
    return n


# ---------------------------------------------------------------- outputs

def write_outputs(out: Path, train, valid, pairs, stats: Stats, system_prompt: str, seed: int):
    out.mkdir(parents=True, exist_ok=True)
    for name, subset in (("train.jsonl", train), ("valid.jsonl", valid)):
        with (out / name).open("w", encoding="utf-8") as f:
            for p in subset:
                f.write(json.dumps(p.to_chat(system_prompt), ensure_ascii=False) + "\n")

    rng = random.Random(seed)
    sample = rng.sample(pairs, min(20, len(pairs)))
    with (out / "sample-20.md").open("w", encoding="utf-8") as f:
        f.write("# Spot-check sample — 20 random pairs\n\n"
                "F Mac: review for accuracy of voice. GO or FIX. (~10 min)\n\n")
        for i, p in enumerate(sample, 1):
            f.write(f"---\n\n## Pair {i}  ·  `{p.source}` (line {p.line}, id {p.pair_id})\n\n"
                    f"**USER:**\n\n{p.user}\n\n**ASSISTANT:**\n\n{p.assistant}\n\n")

    provenance = [{"id": p.pair_id, "source": p.source, "line": p.line} for p in pairs]
    (out / "provenance.json").write_text(json.dumps(provenance, indent=2), encoding="utf-8")

    est_tokens = sum(len(p.user) + len(p.assistant) for p in pairs) // 4
    stats_obj = {
        "files_seen": stats.files_seen,
        "files_unparsed": stats.files_unparsed,
        "pairs_kept": stats.pairs_kept,
        "train": len(train),
        "valid": len(valid),
        "estimated_tokens": est_tokens,
        "drops": stats.drops,
        "per_source_yield": stats.per_source,
        "length_distribution_chars": stats.length_dist,
        "seed": seed,
    }
    (out / "stats.json").write_text(json.dumps(stats_obj, indent=2), encoding="utf-8")

    lines = ["# Conversion stats\n",
             f"- Files seen: **{stats.files_seen}** (unparsed: {len(stats.files_unparsed)})",
             f"- Pairs kept: **{stats.pairs_kept}** → train {len(train)} / valid {len(valid)}",
             f"- Estimated tokens: ~{est_tokens:,}", "", "## Drops by reason"]
    lines += [f"- {k}: {v}" for k, v in sorted(stats.drops.items())] or ["- none"]
    lines += ["", "## Per-source yield"]
    lines += [f"- `{k}`: {v}" for k, v in sorted(stats.per_source.items(), key=lambda kv: -kv[1])]
    lines += ["", "## Pair length distribution (chars)"]
    lines += [f"- {k}: {v}" for k, v in sorted(stats.length_dist.items())]
    if stats.files_unparsed:
        lines += ["", "## Unparsed files (no conversation turns found — need manual review)"]
        lines += [f"- `{f}`" for f in stats.files_unparsed]
    (out / "stats.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return stats_obj


# ---------------------------------------------------------------- main

def run(source: Path, out: Path, system_prompt: str, seed: int = 42,
        val_frac: float = 0.1, min_assistant_chars: int = 80) -> dict:
    md_files = sorted(p for p in source.rglob("*.md") if p.is_file())
    stats = Stats()
    pairs = extract_pairs(md_files, source, stats, min_assistant_chars=min_assistant_chars)
    train, valid = split_pairs(pairs, seed=seed, val_frac=val_frac)
    stats_obj = write_outputs(out, train, valid, pairs, stats, system_prompt, seed)
    for name in ("train.jsonl", "valid.jsonl"):
        validate_jsonl_file(out / name)
    return stats_obj


def main(argv=None):
    ap = argparse.ArgumentParser(description="md conversation exports -> mlx-lm chat JSONL")
    ap.add_argument("--source", type=Path, required=True, help="folder of .md exports")
    ap.add_argument("--out", type=Path, required=True, help="output dataset dir")
    sp = ap.add_mutually_exclusive_group(required=True)
    sp.add_argument("--system-prompt", help="adapter system prompt (inline)")
    sp.add_argument("--system-prompt-file", type=Path, help="file containing the system prompt")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--val-frac", type=float, default=0.1)
    ap.add_argument("--min-assistant-chars", type=int, default=80)
    args = ap.parse_args(argv)
    prompt = args.system_prompt or args.system_prompt_file.read_text(encoding="utf-8").strip()
    stats_obj = run(args.source, args.out, prompt, args.seed, args.val_frac,
                    args.min_assistant_chars)
    kept = stats_obj["pairs_kept"]
    print(f"kept {kept} pairs -> {args.out} (train {stats_obj['train']} / valid {stats_obj['valid']})")
    if kept < 150:
        print("WARNING: below the 150-pair hard floor (§4.3) — STOP and report to F Mac.",
              file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
