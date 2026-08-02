"""text-count-grapheme-width - compute the terminal display width of text lines.

Reads text from files or stdin, segments it into grapheme-like clusters
(base character plus combining marks, variation selectors, ZWJ sequences and
keycap modifiers) and computes the terminal display width of each line:

  - ASCII and narrow/natural-width characters count as 1 column.
  - East Asian wide/fullwidth characters count as 2 columns.
  - Emoji (standalone or in ZWJ/VS16/keycap sequences) count as 2 columns.
  - Combining marks, variation selectors, ZWJ and control characters count
    as 0 columns.

Exit codes:
  0 - success (and --require-max-width satisfied, when given)
  1 - I/O or CLI error
  2 - a width requirement (--require-max-width) was violated
"""

from __future__ import annotations

import argparse
import json
import sys
import unicodedata

__version__ = "1.0.0"

ZWJ = "‍"
VS16 = "️"  # variation selector-16 (emoji presentation)
KEYCAP = "⃣"

# Blocks considered to carry emoji-style glyphs.
_EMOJI_RANGES = (
    (0x1F000, 0x1FAFF),  # symbols & pictographs, emoticons, transport, supplemental
)


def _is_emoji(ch: str) -> bool:
    cp = ord(ch)
    for lo, hi in _EMOJI_RANGES:
        if lo <= cp <= hi:
            return True
    return False


def _char_cols(ch: str) -> int:
    """Display columns of a single base character (no modifiers)."""
    if not ch:
        return 0
    cat = unicodedata.category(ch)
    if cat in ("Mn", "Me", "Cf"):
        return 0
    if ch in "\n\r\t":
        return 0 if ch != "\t" else 4
    o = ord(ch)
    if o < 32 or o == 0x7F:
        return 0
    if _is_emoji(ch):
        return 2
    if unicodedata.east_asian_width(ch) in ("W", "F"):
        return 2
    return 1


def _is_ri(ch: str) -> bool:
    cp = ord(ch)
    return 0x1F1E6 <= cp <= 0x1F1FF


def graphemes(text: str):
    """Segment text into grapheme-like clusters.

    A cluster is a base character followed by any combining marks,
    variation selectors, keycap modifier, and ZWJ-joined continuations.
    Pairs of regional indicators (flags) are also joined.
    This is an approximation of UAX #29 using only the standard library.
    """
    clusters = []
    current = []
    in_zwj = False
    ri_run = 0  # regional indicators in current cluster
    for ch in text:
        cat = unicodedata.category(ch)
        if not current:
            current.append(ch)
            in_zwj = ch == ZWJ
            ri_run = 1 if _is_ri(ch) else 0
            continue
        if in_zwj:
            current.append(ch)
            in_zwj = False
            ri_run = 1 if _is_ri(ch) else 0
            continue
        if ch == ZWJ:
            current.append(ch)
            in_zwj = True
            continue
        if cat in ("Mn", "Me") or ch == VS16 or ch == KEYCAP:
            current.append(ch)
            continue
        if _is_ri(ch) and ri_run % 2 == 1:
            # complete a flag pair
            current.append(ch)
            ri_run += 1
            continue
        clusters.append("".join(current))
        current = [ch]
        ri_run = 1 if _is_ri(ch) else 0
    if current:
        clusters.append("".join(current))
    return clusters


def grapheme_width(cluster: str) -> int:
    """Display columns of one grapheme cluster."""
    base = cluster[0]
    # Emoji-style base, or made emoji via VS16 / keycap / ZWJ join: width 2.
    if _is_emoji(base) or VS16 in cluster or KEYCAP in cluster or ZWJ in cluster:
        return 2
    # Flags (pairs of regional indicators) render as one glyph of width 2.
    cp = ord(base)
    if 0x1F1E6 <= cp <= 0x1F1FF:
        return 2
    return _char_cols(base)


def text_width(text: str) -> int:
    return sum(grapheme_width(g) for g in graphemes(text))


def _read_input(path: str | None) -> str:
    if path in (None, "-"):
        return sys.stdin.read()
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="text-count-grapheme-width",
        description="Compute terminal display width of text lines "
                    "(ASCII=1, wide CJK/emoji=2, combining=0).",
    )
    parser.add_argument("files", nargs="*",
                        help="input files (default: stdin, '-' for stdin)")
    parser.add_argument("--json", action="store_true",
                        help="emit a machine-readable JSON report")
    parser.add_argument("--require-max-width", type=int, metavar="N",
                        help="exit 2 if any line exceeds N columns (CI gate)")
    parser.add_argument("--show-widest", action="store_true",
                        help="print the widest line and its width")
    parser.add_argument("-q", "--quiet", action="store_true",
                        help="suppress per-line output; print only summary")
    args = parser.parse_args(argv)

    paths = args.files or ["-"]
    results = []
    worst = 0
    worst_ref = None
    had_error = False

    for path in paths:
        try:
            content = _read_input(path)
        except OSError as exc:
            print(f"error: {path}: {exc}", file=sys.stderr)
            had_error = True
            continue
        lines = content.splitlines()
        entries = []
        for lineno, line in enumerate(lines, start=1):
            w = text_width(line)
            entries.append({"line": lineno, "width": w, "graphemes": len(graphemes(line))})
            if w > worst:
                worst = w
                worst_ref = (path, lineno, line)
        results.append({
            "file": path if path != "-" else "<stdin>",
            "lines": len(entries),
            "max_width": max((e["width"] for e in entries), default=0),
            "total_width": sum(e["width"] for e in entries),
            "entries": entries,
        })

    if had_error:
        return 1

    violation = None
    if args.require_max_width is not None and worst > args.require_max_width:
        violation = f"max width {worst} exceeds required {args.require_max_width}"

    if args.json:
        report = {
            "files": results,
            "max_width": worst,
            "require_max_width": args.require_max_width,
            "ok": violation is None,
        }
        if violation:
            report["violation"] = violation
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        if not args.quiet:
            for f in results:
                prefix = "" if len(results) == 1 else f"{f['file']}:"
                for e in f["entries"]:
                    print(f"{prefix}{e['line']}: {e['width']} cols, {e['graphemes']} graphemes")
        fcount = len(results)
        print(f"max width: {worst} cols across {fcount} file(s)")
        if args.show_widest and worst_ref:
            path, lineno, line = worst_ref
            print(f"widest: {path}:{lineno}: {line!r} ({worst} cols)")
        if violation:
            print(f"FAIL: {violation}", file=sys.stderr)

    if violation:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
