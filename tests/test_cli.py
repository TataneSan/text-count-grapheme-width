import io
import json
import sys
import unittest
from contextlib import redirect_stdout, redirect_stderr

from text_count_grapheme_width.cli import graphemes, main, text_width


class WidthTests(unittest.TestCase):
    def test_ascii(self):
        self.assertEqual(text_width("hello"), 5)

    def test_wide_cjk(self):
        self.assertEqual(text_width("日本語"), 6)

    def test_combining_mark(self):
        # e + combining acute = 1 column
        self.assertEqual(text_width("é"), 1)
        self.assertEqual(len(graphemes("é")), 1)

    def test_emoji_vs16(self):
        self.assertEqual(text_width("☀️"), 2)

    def test_emoji_text_presentation(self):
        self.assertEqual(text_width("☀"), 1)

    def test_zwj_sequence(self):
        self.assertEqual(text_width("👨‍👩‍👧"), 2)

    def test_flag_pair(self):
        self.assertEqual(text_width("🇫🇷"), 2)
        self.assertEqual(len(graphemes("🇫🇷")), 1)

    def test_mixed_line(self):
        self.assertEqual(text_width("hi 🎉 ok"), 8)


class CliTests(unittest.TestCase):
    def _run(self, argv, stdin_text=""):
        old = sys.stdin
        sys.stdin = io.StringIO(stdin_text)
        out, err = io.StringIO(), io.StringIO()
        try:
            with redirect_stdout(out), redirect_stderr(err):
                code = main(argv)
        finally:
            sys.stdin = old
        return code, out.getvalue(), err.getvalue()

    def test_stdin(self):
        code, out, _ = self._run(["-"], "abc\n")
        self.assertEqual(code, 0)
        self.assertIn("3 cols", out)

    def test_require_max_ok(self):
        code, _, _ = self._run(["--require-max-width", "5", "-"], "abc\n")
        self.assertEqual(code, 0)

    def test_require_max_fail(self):
        code, _, err = self._run(["--require-max-width", "2", "-"], "abcde\n")
        self.assertEqual(code, 2)
        self.assertIn("FAIL", err)

    def test_json(self):
        code, out, _ = self._run(["--json", "-"], "abc\n")
        data = json.loads(out)
        self.assertEqual(code, 0)
        self.assertTrue(data["ok"])
        self.assertEqual(data["max_width"], 3)

    def test_missing_file(self):
        code, _, err = self._run(["/nonexistent/file.txt"])
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
