#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
text-count-grapheme-width - measure the terminal display width of each line.

East Asian Wide/Fullwidth characters count as 2 columns, printable ASCII
as 1, combining marks (variation selectors, ZWJ, .) as 0.

Exit codes:
    0 - success
    1 - I/O or CLI error
    2 - CI check failure (--require-max-width exceeded)
"""
import argparse
import json
import sys
import unicodedata


def char_width(ch: str) -> int:
    """Return display width of a single character."""
    cp = ord(ch)
    if ch == "\u200d":  # zero width joiner
        return 0
    if unicodedata.combining(ch):
        return 0
    if unicodedata.east_asian_width(ch) in ("W", "F"):
        return 2
    if cp < 32 or 0x7F <= cp < 0xA0:
        return 0
    return 1


def line_width(line: str) -> int:
    return sum(char_width(ch) for ch in line)


def iter_lines(path: str):
    if path == "-":
        for line in sys.stdin:
            yield "<stdin>", line.rstrip("\n\r")
    else:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                yield path, line.rstrip("\n\r")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        prog="text-count-grapheme-width",
        description="Count the display width of each line (ASCII=1, CJK/emoji wide=2).")
    p.add_argument("files", nargs="*", default=["-"],
                   help="Text files; omit or '-' to read stdin")
    p.add_argument("--require-max-width", type=int, metavar="N",
                   help="Exit 2 if any line exceeds N columns (CI gate)")
    p.add_argument("--top", type=int, metavar="N", default=0,
                   help="Show only the N longest lines per file")
    p.add_argument("--json", action="store_true",
                   help="Machine-readable JSON report")
    args = p.parse_args(argv)

    all_reports = []
    overall_max = 0
    exit_code = 0

    for path in args.files:
        try:
            rows = []
            max_w = 0
            for lineno, (src, line) in enumerate(iter_lines(path), 1):
                w = line_width(line)
                rows.append({"line": lineno, "width": w, "text": line})
                max_w = max(max_w, w)
            if args.top:
                rows = sorted(rows, key=lambda r: r["width"], reverse=True)[:args.top]
            report = {
                "file": path,
                "max_width": max_w,
                "lines": rows,
            }
            if args.require_max_width is not None:
                report["require_max_width"] = args.require_max_width
                report["check_ok"] = max_w <= args.require_max_width
                if not report["check_ok"]:
                    exit_code = 2
            all_reports.append(report)
            overall_max = max(overall_max, max_w)
        except OSError as e:
            print(f"text-count-grapheme-width: {path}: {e}", file=sys.stderr)
            return 1

    if args.json:
        print(json.dumps({"files": all_reports, "overall_max_width": overall_max},
                         indent=2, ensure_ascii=False))
    else:
        for report in all_reports:
            print(f"{report['file']}: max_width={report['max_width']}")
            if args.top:
                for r in report["lines"]:
                    print(f"  line {r['line']}: {r['width']} cols  {r['text']}")
            if args.require_max_width is not None and not report["check_ok"]:
                print(f"  -> exceeds require-max-width {args.require_max_width}",
                      file=sys.stderr)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
