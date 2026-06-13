# mtp

MarkDown Print (mtp)

`mtp` is a small command-line utility for printing or rendering Markdown files to standard output. It is intended as a lightweight helper to preview Markdown content or convert it to plain text from the terminal.

## Version

Current version: 0.1

## Features

- Print rendered or plain Markdown to stdout
- Simple CLI usage with a Markdown file path

## Installation

1. Ensure you have Python 3.8+ installed.
2. (Optional) Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

There are no external dependencies required by default. 

Linux (user install)

To install `mtp` for your user on Linux, use the included `install.sh` to copy the script to `~/.local/bin` (or your `XDG_BIN_HOME`):

```bash
chmod +x install.sh
./install.sh
# or specify destination explicitly
./install.sh --dest "$HOME/.local/bin"
```

Uninstall with:

```bash
./install.sh --uninstall
```

Ensure your user bin directory is in `PATH`, for example add to your shell profile:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

## Usage

Run the script with a Markdown file path:

```bash
python3 mtp.py path/to/file.md
```

This prints the processed Markdown to stdout. Redirect output to a file if desired:

```bash
python3 mtp.py README.md > out.txt
```

You can also pipe Markdown in on stdin:

```bash
cat README.md | mtp
```

### Options

- `-v`, `--version` — print the version and exit.
- `-n`, `--nroff` — emit nroff overstrike sequences (`X⌫X` for bold, `_⌫X` for
  underline) instead of ANSI colour escapes. This is for viewers that interpret
  the classic nroff bold/underline convention but not ANSI SGR colours — most
  notably Midnight Commander's internal file viewer in `nroff` mode. Colours,
  dim and italic are mapped onto the two available styles (bold / underline).

### Midnight Commander integration

To preview Markdown with formatting inside `mc`'s internal viewer (F3), add the
following to `~/.config/mc/mc.ext.ini`:

```ini
[markdown]
Regex=\.(md|mkd|mdown|markdown)$
RegexIgnoreCase=true
View=%view{nroff} mtp --nroff %f
```

`%view{nroff}` tells the internal viewer to interpret the overstrike sequences
produced by `mtp --nroff`. For full ANSI colour instead, drop `%view` and pipe
through a colour-capable pager: `View=mtp %f | less -R`.

### Example: Markdown Table

Tables are rendered as bordered ASCII grids with aligned columns.

**Source Markdown:**

```markdown
| Name  | Age | City   |
|-------|-----|--------|
| Alice | 30  | London |
| Bob   | 25  | Paris  |
```

**Terminal output:**

```
┌───────┬─────┬────────┐
│ Name  │ Age │ City   │
├───────┼─────┼────────┤
│ Alice │ 30  │ London │
│ Bob   │ 25  │ Paris  │
└───────┴─────┴────────┘
```

### Example: Non-printable Characters

Non-printable characters (anything that is not a printable Unicode character, newline, carriage return, tab, or space) are never passed through silently. Each such character is replaced inline with a red-background hex marker so it is immediately visible.

Single-byte characters are shown as `<HH>`, and multi-byte UTF-8 sequences as `<H0,H1,...>`.

**Source Markdown** (paragraph contains a raw `BEL` U+0007 and a `NULL` U+0000):

```
This line has a bell \x07 and a null \x00 byte inside.
```

**Terminal output** (markers rendered on a red background):

```
This line has a bell <07> and a null <00> byte inside.
```

The surrounding text is printed normally; only the offending bytes are highlighted, making it easy to spot encoding errors or accidental binary content in Markdown source files.

## Development & Tests

Run the existing tests with `pytest`:

```bash
pytest -q
```

## Contributing

Contributions and bug reports are welcome. Open an issue or submit a pull request.

## License

This project is licensed under the MIT License — see the `LICENSE` file for details.

