# text-count-grapheme-width

Measure the terminal display width of each line of text: ASCII and other
narrow characters count as 1 column, East Asian Wide/Fullwidth characters
(CJK, many emoji) count as 2 columns, combining marks as 0.

Useful before sending text to fixed-width terminals, progress bars,
ASCII tables, or output formats that must not exceed a column budget.

## Install

```bash
pip install .
# or run without installing
python3 -m text_count_grapheme_width --help
```

Requires Python 3.9+. No dependencies.

## Usage

```bash
text-count-grapheme-width [FILES...] [--require-max-width N] [--top N] [--json]
```

- `FILES` — text files; omit or `-` to read stdin.
- `--require-max-width N` — exit 2 when any line exceeds N columns. CI gate.
- `--top N` — also print the N longest lines per file.
- `--json` — machine-readable JSON report.

## Examples

```bash
$ printf 'hello world\nこんにちは\n' | text-count-grapheme-width
<stdin>: max_width=11

$ printf 'hello world\nこんにちは\n' | text-count-grapheme-width --require-max-width 10
<stdin>: max_width=11
  -> exceeds require-max-width 10
$ echo $?
2
```

JSON output:

```bash
$ printf 'abc\n' | text-count-grapheme-width --json
{
  "files": [{
    "file": "<stdin>",
    "max_width": 3,
    "lines": [{"line": 1, "width": 3, "text": "abc"}]
  }],
  "overall_max_width": 3
}
```

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | success |
| 1 | I/O or CLI error |
| 2 | `--require-max-width` exceeded |

## License

MIT
