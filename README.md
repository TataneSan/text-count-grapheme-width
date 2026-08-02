# text-count-grapheme-width

Compute the terminal display width of text lines, grapheme by grapheme.
ASCII and narrow characters count as 1 column, wide CJK and emoji as 2,
combining marks, variation selectors and ZWJ as 0.

Useful for checking that generated terminal output, tables, banners or
Unicode-art fits a fixed column budget — including emoji-heavy content
where a naive character count is misleading.

## Features

- Grapheme-like cluster segmentation (pure stdlib): combining marks,
  variation selectors, keycap modifiers, ZWJ sequences and regional
  indicator flag pairs are handled as single glyphs.
- East Asian wide/fullwidth (W/F) characters count as 2 columns;
  emoji-presentation clusters count as 2; combining/VS/ZWJ count as 0.
- Per-line report: number of graphemes and display columns.
- `--require-max-width N` CI gate: exit code 2 when any line exceeds N.
- `--json` machine-readable report.
- Multiple files or stdin.

## Install

```sh
pip install .
# or
pip install git+https://github.com/TataneSan/text-count-grapheme-width.git
```

## Usage

```sh
# from stdin
printf 'hello 世界\n' | text-count-grapheme-width -

# from files
text-count-grapheme-width banner.txt art/*.txt

# machine-readable report
text-count-grapheme-width --json banner.txt

# CI gate: fail if any line is wider than 40 columns
text-count-grapheme-width --require-max-width 40 menu.txt

# show the widest line
text-count-grapheme-width --show-widest *.txt
```

## Examples

```console
$ printf 'café\n' | text-count-grapheme-width -
1: 4 cols, 4 graphemes
max width: 4 cols across 1 file(s)

$ printf 'hi 🎉 ok\n' | text-count-grapheme-width -
1: 8 cols, 7 graphemes
max width: 8 cols across 1 file(s)

$ printf 'this line is way too long\n' | text-count-grapheme-width --require-max-width 10 -
1: 25 cols, 25 graphemes
max width: 25 cols across 1 file(s)
FAIL: max width 25 exceeds required 10
$ echo $?
2
```

## Exit codes

- `0` — success (width requirement satisfied, if given)
- `1` — I/O or CLI error (unreadable file, bad arguments)
- `2` — `--require-max-width` violated

## License

MIT — see [LICENSE](LICENSE).
