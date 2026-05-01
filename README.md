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

