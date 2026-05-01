#!/usr/bin/env python3
"""mtp - Markdown Print: formats Markdown files for terminal output using VT220 escape sequences."""

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


def get_terminal_width():
    """Return the current terminal column width, defaulting to 80."""
    try:
        return shutil.get_terminal_size().columns
    except Exception:
        return 80


# ---------------------------------------------------------------------------
# Inline formatting
# ---------------------------------------------------------------------------

def format_inline(text):
    """Apply inline Markdown formatting and return VT220-escaped text."""
    # Step 1: Extract inline code spans into placeholders so that their
    # content is not re-processed by subsequent patterns.
    code_spans: list[str] = []

    def _save_code(m):
        placeholder = f'\x00CODE{len(code_spans)}\x00'
        code_spans.append(f'{REVERSE}{m.group(1)}{RESET}')
        return placeholder

    text = re.sub(r'`([^`]+)`', _save_code, text)

    # Bold + italic  (*** or ___)
    text = re.sub(r'\*\*\*(.+?)\*\*\*',
                  lambda m: f'{BOLD}{ITALIC}{m.group(1)}{RESET}',
                  text)
    text = re.sub(r'___(.+?)___',
                  lambda m: f'{BOLD}{ITALIC}{m.group(1)}{RESET}',
                  text)

    # Bold  (** or __)
    text = re.sub(r'\*\*(.+?)\*\*',
                  lambda m: f'{BOLD}{m.group(1)}{RESET}',
                  text)
    text = re.sub(r'__(.+?)__',
                  lambda m: f'{BOLD}{m.group(1)}{RESET}',
                  text)

    # Italic  (* or _)
    text = re.sub(r'\*(.+?)\*',
                  lambda m: f'{ITALIC}{m.group(1)}{RESET}',
                  text)
    text = re.sub(r'_(.+?)_',
                  lambda m: f'{ITALIC}{m.group(1)}{RESET}',
                  text)

    # Image  ![alt](url)  – before link so the ! is not swallowed
    text = re.sub(r'!\[([^\]]*)\]\([^)]+\)',
                  lambda m: f'{FG_MAGENTA}[Image: {m.group(1)}]{RESET}',
                  text)

    # Link  [text](url)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)',
                  lambda m: (f'{UNDERLINE}{m.group(1)}{RESET}'
                             f' ({FG_CYAN}{m.group(2)}{RESET})'),
                  text)

    # Step 3: Restore saved inline code spans
    for idx, span in enumerate(code_spans):
        text = text.replace(f'\x00CODE{idx}\x00', span)

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
        rule = FG_CYAN + '─' * min(len(text), width) + RESET
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

    # Column widths are computed from raw (unformatted) cell content
    col_widths = [0] * num_cols
    for row in display_rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(cell.strip()))
    col_widths = [max(w, 1) for w in col_widths]

    def separator():
        return '+' + '+'.join('-' * (w + 2) for w in col_widths) + '+'

    def table_row(cells):
        parts = []
        for i, w in enumerate(col_widths):
            raw  = cells[i].strip() if i < len(cells) else ''
            fmt  = format_inline(raw)
            pad  = w - len(raw)
            parts.append(f' {fmt}{" " * pad} ')
        return '|' + '|'.join(parts) + '|'

    lines = [separator(), table_row(header), separator()]
    for row in data_rows:
        lines.append(table_row(row))
    lines.append(separator())

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
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) >= 2:
        # Mode 2: mtp example.md
        filename = sys.argv[1]
        if not os.path.exists(filename):
            print(f'{FG_RED}Error:{RESET} File not found: {filename}', file=sys.stderr)
            sys.exit(1)
        try:
            with open(filename, encoding='utf-8') as fh:
                content = fh.read()
        except IOError as exc:
            print(f'{FG_RED}Error:{RESET} Cannot read file: {exc}', file=sys.stderr)
            sys.exit(1)
    else:
        # Mode 1: cat example.md | mtp
        if sys.stdin.isatty():
            print(
                f'{BOLD}Usage:{RESET} mtp <file.md>  '
                f'or  cat <file.md> | mtp',
                file=sys.stderr,
            )
            sys.exit(1)
        try:
            content = sys.stdin.read()
        except IOError as exc:
            print(f'{FG_RED}Error:{RESET} Cannot read stdin: {exc}', file=sys.stderr)
            sys.exit(1)

    print(render_markdown(content))


if __name__ == '__main__':
    main()
