#!/usr/bin/env python3
"""md2p - Markdown to Print: formats Markdown files for terminal output using VT220 escape sequences."""

__version__ = "1.0.1"

MAX_INPUT_BYTES = 50 * 1024 * 1024  # 50 MB – reject inputs larger than this

import os
import re
import shutil
import sys

# ---------------------------------------------------------------------------
# VT220 / ANSI SGR escape sequences
# ---------------------------------------------------------------------------
RESET     = '\033[0m'
BOLD      = '\033[1m'
DIM       = '\033[2m'
ITALIC    = '\033[3m'
UNDERLINE = '\033[4m'
REVERSE   = '\033[7m'

FG_RED     = '\033[31m'
FG_GREEN   = '\033[32m'
FG_YELLOW  = '\033[33m'
FG_BLUE    = '\033[34m'
FG_MAGENTA = '\033[35m'
FG_CYAN    = '\033[36m'

BG_RED     = '\033[41m'


def get_terminal_width():
    """Return the current terminal column width, defaulting to 80."""
    try:
        return shutil.get_terminal_size().columns
    except Exception:
        return 80


# ---------------------------------------------------------------------------
# Input sanitisation
# ---------------------------------------------------------------------------

_ANSI_ESCAPE_RE = re.compile(r'\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')


def _strip_ansi_escapes(text: str) -> str:
    """Remove raw ANSI/VT terminal escape sequences from untrusted input."""
    return _ANSI_ESCAPE_RE.sub('', text)


_ALLOWED_NONPRINTABLE = frozenset('\n\r\t ')

# Variation selectors (VS1-16, VS17-256). Unicode category Mn, so Python's
# str.isprintable() reports them as printable even though they render with
# zero visible width. This is the block most commonly abused today to
# smuggle hidden bytes (watermarks, payloads) invisibly onto a base
# character, so it needs an explicit check rather than relying on
# isprintable() alone.
_VARIATION_SELECTOR_RANGES = (
    (0xFE00, 0xFE0F),
    (0xE0100, 0xE01EF),
)


def _is_variation_selector(ch: str) -> bool:
    """Return True if *ch* is a Unicode variation selector."""
    cp = ord(ch)
    return any(lo <= cp <= hi for lo, hi in _VARIATION_SELECTOR_RANGES)


def _replace_nonprintable(text: str) -> str:
    """Replace non-printable characters (except LF, CR, TAB, space) with
    a red-background hex representation: <HH> for single-byte codepoints,
    <H0,H1,...> for multi-byte UTF-8 encodings. Also flags variation
    selectors, which are zero-width but pass isprintable()."""
    parts: list[str] = []
    for ch in text:
        if ch in _ALLOWED_NONPRINTABLE:
            parts.append(ch)
        elif ch.isprintable() and not _is_variation_selector(ch):
            parts.append(ch)
        else:
            encoded = ch.encode('utf-8')
            hex_str = ','.join(f'{b:02X}' for b in encoded)
            parts.append(f'{BG_RED}<{hex_str}>{RESET}')
    return ''.join(parts)


# ---------------------------------------------------------------------------
# Inline formatting
# ---------------------------------------------------------------------------

def format_inline(text):
    """Apply inline Markdown formatting and return VT220-escaped text."""
    # Step 1: Extract spans whose rendered form must not be re-processed by
    # later patterns into placeholders. This covers inline code (its content
    # is literal) as well as links/images: their replacement text contains
    # escape sequences (e.g. "\033[4m") whose literal '[' would otherwise be
    # matched by the link regex, and their URLs may contain '*' or '_' that
    # the emphasis patterns would mangle.
    spans: list[str] = []

    def _stash(rendered):
        placeholder = f'\x02SPAN_{len(spans)}_\x03'
        spans.append(rendered)
        return placeholder

    # Inline code  `code`
    text = re.sub(r'`([^`]+)`',
                  lambda m: _stash(f'{REVERSE}{m.group(1)}{RESET}'),
                  text)

    # Image  ![alt](url)  – before link so the ! is not swallowed
    text = re.sub(r'!\[([^\]]*)\]\([^)]+\)',
                  lambda m: _stash(f'{FG_MAGENTA}[Image: {m.group(1)}]{RESET}'),
                  text)

    # Link  [text](url)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)',
                  lambda m: _stash(f'{UNDERLINE}{m.group(1)}{RESET}'
                                   f' ({FG_CYAN}{m.group(2)}{RESET})'),
                  text)

    # Bold + italic  (*** or ___)
    text = re.sub(r'\*\*\*(.+?)\*\*\*',
                  lambda m: f'{BOLD}{ITALIC}{m.group(1)}{RESET}',
                  text)
    text = re.sub(r'(?<!\w)___(.+?)___(?!\w)',
                  lambda m: f'{BOLD}{ITALIC}{m.group(1)}{RESET}',
                  text)

    # Bold  (** or __)
    text = re.sub(r'\*\*(.+?)\*\*',
                  lambda m: f'{BOLD}{m.group(1)}{RESET}',
                  text)
    text = re.sub(r'(?<!\w)__(.+?)__(?!\w)',
                  lambda m: f'{BOLD}{m.group(1)}{RESET}',
                  text)

    # Italic  (* or _)
    text = re.sub(r'\*(.+?)\*',
                  lambda m: f'{ITALIC}{m.group(1)}{RESET}',
                  text)
    text = re.sub(r'(?<!\w)_(.+?)_(?!\w)',
                  lambda m: f'{ITALIC}{m.group(1)}{RESET}',
                  text)

    # Step 3: Restore protected spans
    for idx, span in enumerate(spans):
        text = text.replace(f'\x02SPAN_{idx}_\x03', span)

    return text


# ---------------------------------------------------------------------------
# Header formatting
# ---------------------------------------------------------------------------

def format_header(level, text):
    """Return a VT220-formatted header string for the given ATX level (1–6)."""
    formatted = format_inline(text)
    width = get_terminal_width()

    if level == 1:
        padding = max(0, (width - len(text)) // 2)
        return ' ' * padding + f'{BOLD}{UNDERLINE}{FG_YELLOW}{formatted}{RESET}'

    if level == 2:
        visible_len = len(re.sub(r'\*+|_+|`', '', text))
        rule = FG_CYAN + '─' * min(visible_len, width) + RESET
        return f'{BOLD}{FG_CYAN}{formatted}{RESET}\n{rule}'

    if level == 3:
        return f'{BOLD}{formatted}{RESET}'

    if level == 4:
        return f'{BOLD}{DIM}{formatted}{RESET}'

    if level == 5:
        return f'{ITALIC}{formatted}{RESET}'

    # level == 6
    return f'{DIM}{formatted}{RESET}'


# ---------------------------------------------------------------------------
# Table helpers
# ---------------------------------------------------------------------------

def parse_table_row(line):
    """Split a Markdown table row into a list of raw cell strings."""
    line = line.strip()
    if line.startswith('|'):
        line = line[1:]
    if line.endswith('|'):
        line = line[:-1]
    return line.split('|')


def is_table_row(line):
    """Return True if *line* looks like a Markdown table row."""
    stripped = line.strip()
    return stripped.startswith('|') and stripped.endswith('|')


def is_separator_row(line):
    """Return True if *line* is a table alignment-separator row (|---|---|)."""
    stripped = line.strip()
    if not (stripped.startswith('|') and stripped.endswith('|')):
        return False
    inner = stripped[1:-1]
    return all(re.match(r'^\s*:?-+:?\s*$', cell) for cell in inner.split('|'))


def format_table(rows):
    """
    Render *rows* (list-of-lists of raw cell strings) as a bordered ASCII table.

    The first row is treated as the header; any separator row (---) is removed
    from display but used to identify the header/body split.
    """
    if not rows:
        return ''

    header = rows[0]
    data_rows = [
        row for row in rows[1:]
        if not all(re.match(r'^:?-+:?$', cell.strip()) for cell in row)
    ]

    display_rows = [header] + data_rows
    num_cols = max(len(row) for row in display_rows)

    # Pre-format every cell so that visible widths (after ANSI stripping) drive
    # column sizing and padding — raw Markdown length is not a reliable measure
    # because inline formatting (e.g. `code`) removes markup characters.
    formatted_rows = []
    for row in display_rows:
        fmt_row = [format_inline(row[i].strip()) if i < len(row) else ''
                   for i in range(num_cols)]
        formatted_rows.append(fmt_row)

    def _visible_len(s):
        return len(_strip_ansi_escapes(s))

    col_widths = [0] * num_cols
    for fmt_row in formatted_rows:
        for i, cell in enumerate(fmt_row):
            col_widths[i] = max(col_widths[i], _visible_len(cell))
    col_widths = [max(w, 1) for w in col_widths]

    def sep_top():
        return '┌' + '┬'.join('─' * (w + 2) for w in col_widths) + '┐'

    def sep_mid():
        return '├' + '┼'.join('─' * (w + 2) for w in col_widths) + '┤'

    def sep_bot():
        return '└' + '┴'.join('─' * (w + 2) for w in col_widths) + '┘'

    def table_row(fmt_cells):
        parts = []
        for i, w in enumerate(col_widths):
            fmt = fmt_cells[i] if i < len(fmt_cells) else ''
            pad = w - _visible_len(fmt)
            parts.append(f' {fmt}{" " * pad} ')
        return '│' + '│'.join(parts) + '│'

    lines = [sep_top(), table_row(formatted_rows[0]), sep_mid()]
    for fmt_row in formatted_rows[1:]:
        lines.append(table_row(fmt_row))
    lines.append(sep_bot())

    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# Full Markdown renderer
# ---------------------------------------------------------------------------

def render_markdown(content):
    """Parse *content* as Markdown and return a VT220-formatted string."""
    lines   = content.split('\n')
    output  = []
    i       = 0

    while i < len(lines):
        line = lines[i]

        # ── Fenced code block (``` or ~~~) ──────────────────────────────────
        if re.match(r'^```|^~~~', line):
            i += 1
            code_lines = []
            while i < len(lines) and not re.match(r'^```|^~~~', lines[i]):
                code_lines.append(lines[i])
                i += 1
            output.append(f'{DIM}{FG_GREEN}' + '\n'.join(code_lines) + RESET)
            i += 1        # skip closing fence
            continue

        # ── ATX headers  (#, ##, …) ─────────────────────────────────────────
        m = re.match(r'^(#{1,6})\s+(.*)', line)
        if m:
            output.append(format_header(len(m.group(1)), m.group(2)))
            i += 1
            continue

        # ── Setext headers (text followed by === or ---) ────────────────────
        if i + 1 < len(lines):
            next_line = lines[i + 1]
            if re.match(r'^=+\s*$', next_line) and line.strip():
                output.append(format_header(1, line.strip()))
                i += 2
                continue
            if (re.match(r'^-+\s*$', next_line) and line.strip()
                    and not re.match(r'^(\*{3,}|-{3,}|_{3,})\s*$', line)):
                output.append(format_header(2, line.strip()))
                i += 2
                continue

        # ── Horizontal rule ─────────────────────────────────────────────────
        if re.match(r'^(\*{3,}|-{3,}|_{3,})\s*$', line):
            output.append(FG_CYAN + '─' * get_terminal_width() + RESET)
            i += 1
            continue

        # ── Table ───────────────────────────────────────────────────────────
        if is_table_row(line):
            table_rows = []
            while i < len(lines) and is_table_row(lines[i]):
                table_rows.append(parse_table_row(lines[i]))
                i += 1
            output.append(format_table(table_rows))
            continue

        # ── Blockquote ──────────────────────────────────────────────────────
        if line.startswith('>'):
            text = line[1:].strip()
            output.append(f'{FG_CYAN}│{RESET} {ITALIC}{format_inline(text)}{RESET}')
            i += 1
            continue

        # ── Unordered list ──────────────────────────────────────────────────
        m = re.match(r'^(\s*)([-*+])\s+(.*)', line)
        if m:
            indent = len(m.group(1))
            bullet = '•' if indent == 0 else '◦'
            prefix = '  ' * (indent // 2)
            output.append(f'{prefix}{FG_YELLOW}{bullet}{RESET} {format_inline(m.group(3))}')
            i += 1
            continue

        # ── Ordered list ────────────────────────────────────────────────────
        m = re.match(r'^(\s*)(\d+)[.)]\s+(.*)', line)
        if m:
            indent = len(m.group(1))
            prefix = '  ' * (indent // 2)
            output.append(f'{prefix}{FG_YELLOW}{m.group(2)}.{RESET} {format_inline(m.group(3))}')
            i += 1
            continue

        # ── Blank line ──────────────────────────────────────────────────────
        if not line.strip():
            output.append('')
            i += 1
            continue

        # ── Regular paragraph ────────────────────────────────────────────────
        output.append(format_inline(line))
        i += 1

    return '\n'.join(output)


# ---------------------------------------------------------------------------
# nroff overstrike conversion (for Midnight Commander's internal viewer)
# ---------------------------------------------------------------------------

_SGR_RE = re.compile(r'\033\[([0-9;]*)m')


def ansi_to_nroff(text: str) -> str:
    """Convert ANSI/VT220-formatted output into nroff overstrike sequences.

    Midnight Commander's internal viewer (in `nroff` mode) does not understand
    ANSI SGR colour escapes; it only renders the classic nroff overstrike
    conventions, colouring them with its own viewer theme:

        bold      ->  ``X\\bX``   (character, backspace, same character)
        underline ->  ``_\\bX``   (underscore, backspace, character)

    There is no colour or italic primitive, so attributes are mapped to the
    nearest of the two available styles:

        bold (1), reverse (7)      -> overstrike bold
        italic (3), underline (4)  -> overstrike underline
        dim (2), colours, reset    -> plain text

    When a span is both bold and underline (e.g. the H1 header style) bold
    wins, since it is the more legible of the two in MC's viewer.
    """
    out: list[str] = []
    bold = under = False
    i, n = 0, len(text)
    while i < n:
        m = _SGR_RE.match(text, i)
        if m:
            params = m.group(1)
            for code in (params.split(';') if params else ['0']):
                code = code or '0'
                if code == '0':
                    bold = under = False
                elif code in ('1', '7'):       # bold, reverse
                    bold = True
                elif code in ('3', '4'):       # italic, underline
                    under = True
                # dim (2) and colour codes carry no nroff equivalent -> ignore
            i = m.end()
            continue

        ch = text[i]
        i += 1
        if ch == '\033':
            # Drop any stray non-SGR escape sequence defensively.
            esc = _ANSI_ESCAPE_RE.match(text, i - 1)
            if esc:
                i = esc.end()
            continue
        if ch.isspace() or not ch.isprintable():
            out.append(ch)
        elif bold:
            out.append(f'{ch}\b{ch}')
        elif under:
            out.append(f'_\b{ch}')
        else:
            out.append(ch)
    return ''.join(out)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    # Parse flags, leaving positional arguments (the filename) in *rest*.
    nroff = False
    rest: list[str] = []
    for arg in sys.argv[1:]:
        if arg in ("-v", "--version"):
            print(__version__)
            sys.exit(0)
        elif arg in ("-n", "--nroff"):
            nroff = True
        else:
            rest.append(arg)

    if rest:
        # Mode 2: md2p example.md
        filename = rest[0]
        if not os.path.exists(filename):
            print(f'{FG_RED}Error:{RESET} File not found: {filename}', file=sys.stderr)
            sys.exit(1)
        try:
            with open(filename, encoding='utf-8') as fh:
                content = fh.read(MAX_INPUT_BYTES + 1)
            if len(content) > MAX_INPUT_BYTES:
                print(
                    f'{FG_RED}Error:{RESET} File too large'
                    f' (max {MAX_INPUT_BYTES // (1024 * 1024)} MB)',
                    file=sys.stderr,
                )
                sys.exit(1)
            content = _strip_ansi_escapes(content)
        except (IOError, UnicodeDecodeError) as exc:
            print(f'{FG_RED}Error:{RESET} Cannot read file: {exc}', file=sys.stderr)
            sys.exit(1)
    else:
        # Mode 1: cat example.md | md2p
        if sys.stdin.isatty():
            print(
                f'{BOLD}Usage:{RESET} md2p <file.md>  '
                f'or  cat <file.md> | md2p',
                file=sys.stderr,
            )
            sys.exit(1)
        try:
            content = sys.stdin.read(MAX_INPUT_BYTES + 1)
            if len(content) > MAX_INPUT_BYTES:
                print(
                    f'{FG_RED}Error:{RESET} Input too large'
                    f' (max {MAX_INPUT_BYTES // (1024 * 1024)} MB)',
                    file=sys.stderr,
                )
                sys.exit(1)
            content = _strip_ansi_escapes(content)
        except (IOError, UnicodeDecodeError) as exc:
            print(f'{FG_RED}Error:{RESET} Cannot read stdin: {exc}', file=sys.stderr)
            sys.exit(1)

    content = _replace_nonprintable(content)
    rendered = render_markdown(content)
    if nroff:
        rendered = ansi_to_nroff(rendered)
    print(rendered)


if __name__ == '__main__':
    main()
