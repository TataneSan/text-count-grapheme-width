# text-count-grapheme-width

Compute the **terminal display width** of each line of a text file.

Width rules (East Asian Width based, per codepoint):

- ASCII and narrow characters count as **1** column
- wide / full-width characters (CJK ideographs, most emoji) count as **2** columns
- zero-width characters (combining marks, format characters, ZWJ, variation selectors, control characters) count as **0**
- tab counts as `--tab-width` columns (default: 1)

Useful to verify that ASCII-art, banners, tables or wrapped text fit a fixed
terminal width, and to gate that constraint in CI.

Zero dependencies — Python standard library only (Python >= 3.9).

## Installation

```sh
pip install .
# or directly from GitHub
pip install git+https://github.com/TataneSan/text-count-grapheme-width.git
```

You can also run it without installing:

```sh
python3 -m text_count_grapheme_width
```

## Usage

```
text-count-grapheme-width [FILE ...] [--tab-width N] [--require-max-width N]
                          [--summary] [--json] [-q]
```

Reads stdin when no file (or `-`) is given.

### Examples

Width of each line (one number per line), plus a summary:

```sh
$ printf 'hello\n您好\n' | text-count-grapheme-width -
5
4
summary: 2 lines, max=5 min=4 avg=4.50
```

CI gate — fail if any line exceeds 80 columns:

```sh
$ text-count-grapheme-width --require-max-width 80 banner.txt
error: banner.txt line 12 is 83 columns wide (max 80)
$ echo $?
2
```

Machine-readable report:

```sh
$ printf 'a🙂b\n' | text-count-grapheme-width --json -
{
  "files": [
    {
      "count": 1,
      "lines": [
        { "line": 1, "width": 4 }
      ],
      "max": 4,
      "min": 4,
      "avg": 4.0,
      "path": "-"
    }
  ],
  "require_max_width": null,
  "over_max_width": [],
  "ok": true
}
```

Multiple files (summary only):

```sh
text-count-grapheme-width --summary docs/*.txt
```

## Options

| Option | Description |
| --- | --- |
| `--tab-width N` | columns counted for a tab character (default: 1) |
| `--require-max-width N` | exit 2 if any line is wider than N columns |
| `--summary` | print only the per-file summary |
| `--json` | machine-readable JSON report |
| `-q`, `--quiet` | suppress human output |

## Exit codes

| Code | Meaning |
| --- | --- |
| 0 | success |
| 1 | CLI or I/O error |
| 2 | `--require-max-width` constraint not satisfied |

## License

MIT
