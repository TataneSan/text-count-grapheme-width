"""text-count-grapheme-width - compute the terminal display width of each line.

Width rules (per Unicode codepoint, East Asian Width based):

* narrow/neutral characters (ASCII, Latin, ...) count as 1 column
* wide/full-width characters (CJK ideographs, most emoji) count as 2 columns
* zero-width characters (combining marks, format chars, ZWJ, variation
  selectors, control characters) count as 0 columns
* tab counts as ``--tab-width`` columns (default: 1)

Width is computed codepoint by codepoint, not per grapheme cluster; emoji
sequences joined with ZWJ therefore sum to the width of their components
(ZWJ itself counting 0).

Exit codes:
    0   success
    1   CLI or I/O error
    2   --require-max-width constraint not satisfied
"""

import argparse
import json
import sys
import unicodedata


def codepoint_width(ch, tab_width):
    """Display column width of a single character."""
    if ch == "\t":
        return tab_width
    category = unicodedata.category(ch)
    if category in ("Mn", "Me", "Cf", "Cc", "Cs"):
        return 0
    if unicodedata.east_asian_width(ch) in ("W", "F"):
        return 2
    return 1


def line_width(line, tab_width):
    """Display column width of a whole line."""
    return sum(codepoint_width(ch, tab_width) for ch in line)


def analyze_text(text, tab_width):
    """Return per-line widths and summary statistics for a text."""
    lines = text.splitlines()
    widths = [line_width(line, tab_width) for line in lines]
    count = len(widths)
    result = {
        "count": count,
        "lines": [{"line": i + 1, "width": w} for i, w in enumerate(widths)],
        "max": max(widths) if widths else 0,
        "min": min(widths) if widths else 0,
        "avg": (sum(widths) / count) if count else 0.0,
    }
    return result


def read_input(path):
    if path == "-":
        return sys.stdin.read()
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


def build_parser():
    parser = argparse.ArgumentParser(
        prog="text-count-grapheme-width",
        description=(
            "Compute the terminal display width of each line of a text file. "
            "ASCII and narrow characters count as 1 column, wide/full-width "
            "characters (CJK, emoji) count as 2, zero-width characters count "
            "as 0. Reads stdin when no file (or '-') is given."
        ),
    )
    parser.add_argument(
        "files",
        nargs="*",
        metavar="FILE",
        help="input files (default: stdin; use '-' for explicit stdin)",
    )
    parser.add_argument(
        "--tab-width",
        type=int,
        default=1,
        metavar="N",
        help="columns counted for a tab character (default: 1)",
    )
    parser.add_argument(
        "--require-max-width",
        type=int,
        metavar="N",
        help="exit 2 if any line is wider than N columns (CI gate)",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="print only the per-file summary, not the per-line widths",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit a machine-readable JSON report",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="suppress human output (exit code still applies)",
    )
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.tab_width < 0:
        print("error: --tab-width must be >= 0", file=sys.stderr)
        return 1

    files = args.files or ["-"]
    reports = []
    try:
        for path in files:
            text = read_input(path)
            report = analyze_text(text, args.tab_width)
            report["path"] = path
            reports.append(report)
    except OSError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 1

    over_limit = []
    if args.require_max_width is not None:
        for report in reports:
            for entry in report["lines"]:
                if entry["width"] > args.require_max_width:
                    over_limit.append(
                        {
                            "path": report["path"],
                            "line": entry["line"],
                            "width": entry["width"],
                        }
                    )

    exit_code = 2 if over_limit else 0

    if args.json:
        doc = {
            "files": reports,
            "require_max_width": args.require_max_width,
            "over_max_width": over_limit,
            "ok": exit_code == 0,
        }
        json.dump(doc, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    elif not args.quiet:
        multiple = len(files) > 1
        for report in reports:
            if multiple:
                print("==> %s <==" % report["path"])
            if not args.summary:
                for entry in report["lines"]:
                    print("%d" % entry["width"])
            print(
                "summary: %d lines, max=%d min=%d avg=%.2f"
                % (report["count"], report["max"], report["min"], report["avg"])
            )
        for violation in over_limit:
            print(
                "error: %s line %d is %d columns wide (max %d)"
                % (
                    violation["path"],
                    violation["line"],
                    violation["width"],
                    args.require_max_width,
                ),
                file=sys.stderr,
            )

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
