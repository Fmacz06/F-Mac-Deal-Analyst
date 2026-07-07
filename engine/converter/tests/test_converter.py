"""Unit tests for the Phase 2 converter — gates per MASTER-BLUEPRINT §6 Phase 2:
malformed md, empty file, giant file, unicode, plus schema/split/dedup/PII checks.
Run: python3 -m unittest discover -s engine/converter/tests -v
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import convert  # noqa: E402


def conv(user, assistant):
    return f"**User:** {user}\n\n**Assistant:** {assistant}\n"


LONG_ANSWER = ("First, write the failing test. Then implement the smallest change "
               "that passes it. Triage the requirement as Clear, Fuzzy, or Missing "
               "before touching code, and checkpoint after each green run.")


class TestParsing(unittest.TestCase):
    def test_bold_and_heading_markers(self):
        md = "## User\nHow do I start?\n## Assistant\n" + LONG_ANSWER
        turns = convert.parse_turns(md)
        self.assertEqual([t.role for t in turns], ["user", "assistant"])
        self.assertIn("failing test", turns[1].text)

    def test_bold_marker_with_colon_inside_bold(self):
        # "**User:**" — colon inside the bold — must strip cleanly, no stray "**"
        turns = convert.parse_turns("**User:** How do I start?\n**Assistant:** " + LONG_ANSWER)
        self.assertEqual(turns[0].text, "How do I start?")
        self.assertFalse(turns[1].text.startswith("*"))

    def test_plain_colon_markers(self):
        turns = convert.parse_turns("User: hi there\nAssistant: hello response text")
        self.assertEqual([t.role for t in turns], ["user", "assistant"])

    def test_no_markers_returns_empty(self):
        self.assertEqual(convert.parse_turns("# Just a doc\n\nplain prose, no chat"), [])

    def test_marker_inside_code_fence_ignored(self):
        md = ("**User:** here is code\n```\nUser: not a real turn\n```\nmore context\n"
              "**Assistant:** " + LONG_ANSWER)
        turns = convert.parse_turns(md)
        self.assertEqual(len(turns), 2)
        self.assertIn("not a real turn", turns[0].text)

    def test_consecutive_same_role_merged(self):
        md = "**User:** part one\n**User:** part two\n**Assistant:** " + LONG_ANSWER
        turns = convert.parse_turns(md)
        self.assertEqual(len(turns), 2)
        self.assertIn("part one", turns[0].text)
        self.assertIn("part two", turns[0].text)

    def test_unicode_content_preserved(self):
        md = "**User:** émoji test 🚀 中文 works?\n**Assistant:** " + LONG_ANSWER + " ✅ 中文 é"
        turns = convert.parse_turns(md)
        self.assertIn("🚀", turns[0].text)
        self.assertIn("中文", turns[1].text)


class TestFilters(unittest.TestCase):
    def test_strip_pleasantries(self):
        self.assertEqual(convert.strip_pleasantries("Great question! Thanks! Use TDD."),
                         "Use TDD.")

    def test_glue_only_user_dropped(self):
        self.assertTrue(convert._GLUE_ONLY.match("thanks!!"))
        self.assertFalse(convert._GLUE_ONLY.match("thanks — but why does the test fail?"))

    def test_pii_detection(self):
        self.assertIn("email", convert.pii_hits("mail me at a@b.com"))
        self.assertIn("api_key", convert.pii_hits("key sk-abcdefghijklmnop1234"))
        self.assertIn("private_key", convert.pii_hits("-----BEGIN RSA PRIVATE KEY-----"))
        self.assertEqual(convert.pii_hits("nothing sensitive here"), [])

    def test_near_dup_index(self):
        idx = convert.NearDupIndex()
        a = "how should I structure the retry logic for the fetcher module? " * 3
        self.assertFalse(idx.is_dup(a))
        self.assertTrue(idx.is_dup(a + " thanks"))
        self.assertFalse(idx.is_dup("completely different topic about CAD tolerances"))


class TestSchema(unittest.TestCase):
    def test_valid_line_passes(self):
        line = json.dumps({"messages": [
            {"role": "system", "content": "s"},
            {"role": "user", "content": "u"},
            {"role": "assistant", "content": "a"}]})
        convert.validate_chat_line(line)  # no raise

    def test_final_message_must_be_assistant(self):
        line = json.dumps({"messages": [
            {"role": "user", "content": "u"}, {"role": "system", "content": "s"}]})
        with self.assertRaises(ValueError):
            convert.validate_chat_line(line)

    def test_bad_role_rejected(self):
        line = json.dumps({"messages": [
            {"role": "narrator", "content": "x"}, {"role": "assistant", "content": "a"}]})
        with self.assertRaises(ValueError):
            convert.validate_chat_line(line)


class TestEndToEnd(unittest.TestCase):
    def _run(self, files: dict, **kwargs):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        src, out = Path(tmp.name, "src"), Path(tmp.name, "out")
        src.mkdir()
        for name, content in files.items():
            (src / name).write_text(content, encoding="utf-8")
        stats = convert.run(src, out, "You are the test specialist.", **kwargs)
        return stats, out

    def test_empty_file_and_malformed_file_handled(self):
        stats, _ = self._run({
            "empty.md": "",
            "malformed.md": "\x00\x01 not really markdown {{{ ###",
            "good.md": conv("How do I add retries?", LONG_ANSWER),
        })
        self.assertEqual(stats["pairs_kept"], 1)
        self.assertIn("empty.md", stats["files_unparsed"])
        self.assertIn("malformed.md", stats["files_unparsed"])

    def test_giant_file(self):
        def distinct(i):
            # genuinely distinct body per pair so the near-dup filter keeps them
            rng = __import__("random").Random(i)
            return " ".join("".join(rng.choice("abcdefghijklmnopqrstuvwxyz")
                                    for _ in range(8)) for _ in range(40))
        body = "\n".join(conv(f"question number {i} about module structure?",
                              f"Answer {i}. {distinct(i)}")
                         for i in range(500))
        stats, out = self._run({"giant.md": body})
        self.assertGreater(stats["pairs_kept"], 300)
        self.assertEqual(convert.validate_jsonl_file(out / "train.jsonl"), stats["train"])

    def test_split_is_seeded_and_90_10(self):
        files = {"a.md": "\n".join(conv(f"distinct question {i} on topic {i*7}?",
                                        LONG_ANSWER + f" case {i} " + "y" * (i % 11))
                                   for i in range(100))}
        s1, _ = self._run(files, seed=7)
        s2, _ = self._run(files, seed=7)
        self.assertEqual(s1["train"], s2["train"])
        self.assertAlmostEqual(s1["valid"] / s1["pairs_kept"], 0.1, delta=0.03)

    def test_outputs_exist_and_validate(self):
        stats, out = self._run({"c.md": "\n".join(
            conv(f"unique architecture question {i}?", LONG_ANSWER + f" detail {i}")
            for i in range(30))})
        for f in ("train.jsonl", "valid.jsonl", "sample-20.md", "stats.md",
                  "stats.json", "provenance.json"):
            self.assertTrue((out / f).exists(), f)
        prov = json.loads((out / "provenance.json").read_text())
        self.assertEqual(len(prov), stats["pairs_kept"])
        # provenance stays OUTSIDE the training data
        train_text = (out / "train.jsonl").read_text()
        self.assertNotIn("provenance", train_text)
        self.assertNotIn(prov[0]["id"], train_text)

    def test_pii_pair_dropped(self):
        stats, _ = self._run({
            "pii.md": conv("Email me at real.person@example.com with the fix?",
                           LONG_ANSWER),
            "ok.md": conv("How should the router classify code fences?", LONG_ANSWER),
        })
        self.assertEqual(stats["pairs_kept"], 1)
        self.assertTrue(any(k.startswith("pii:") for k in stats["drops"]))

    def test_unicode_end_to_end(self):
        stats, out = self._run({"u.md": conv("Explain the café naming — 中文 ok? 🚀",
                                             LONG_ANSWER + " Résumé: 完成 ✅")})
        self.assertEqual(stats["pairs_kept"], 1)
        line = (out / "train.jsonl").read_text(encoding="utf-8") + \
               (out / "valid.jsonl").read_text(encoding="utf-8")
        self.assertIn("中文", line)


if __name__ == "__main__":
    unittest.main()
