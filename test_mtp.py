"""Tests for mtp - Markdown Print."""

import re

import pytest

from mtp import (
    BOLD, DIM, FG_CYAN, FG_MAGENTA, FG_YELLOW,
    ITALIC, RESET, REVERSE, UNDERLINE,
    format_header,
    format_inline,
    format_table,
    is_separator_row,
    is_table_row,
    parse_table_row,
    render_markdown,
)


# ---------------------------------------------------------------------------
# format_inline
# ---------------------------------------------------------------------------

class TestFormatInline:
    def test_no_formatting(self):
        assert format_inline('plain text') == 'plain text'

    def test_bold_asterisk(self):
        result = format_inline('**bold**')
        assert BOLD in result
        assert 'bold' in result
        assert RESET in result

    def test_bold_underscore(self):
        result = format_inline('__bold__')
        assert BOLD in result
        assert 'bold' in result

    def test_italic_asterisk(self):
        result = format_inline('*italic*')
        assert ITALIC in result
        assert 'italic' in result

    def test_italic_underscore(self):
        result = format_inline('_italic_')
        assert ITALIC in result
        assert 'italic' in result

    def test_bold_italic_asterisk(self):
        result = format_inline('***both***')
        assert BOLD in result
        assert ITALIC in result
        assert 'both' in result

    def test_bold_italic_underscore(self):
        result = format_inline('___both___')
        assert BOLD in result
        assert ITALIC in result

    def test_inline_code(self):
        result = format_inline('`code`')
        assert REVERSE in result
        assert 'code' in result

    def test_link(self):
        result = format_inline('[example](http://example.com)')
        assert 'example' in result
        assert 'http://example.com' in result
        assert UNDERLINE in result

    def test_image(self):
        result = format_inline('![alt text](image.png)')
        assert 'Image:' in result
        assert 'alt text' in result
        assert FG_MAGENTA in result

    def test_mixed_inline(self):
        result = format_inline('Hello **world** and _italic_')
        assert 'Hello' in result
        assert 'world' in result
        assert 'italic' in result
        assert BOLD in result
        assert ITALIC in result

    def test_inline_code_takes_priority_over_bold(self):
        # The ** inside backticks must not trigger bold
        result = format_inline('`**not bold**`')
        # The literal ** characters should appear inside the reversed region
        assert '**not bold**' in result


# ---------------------------------------------------------------------------
# format_header
# ---------------------------------------------------------------------------

class TestFormatHeader:
    def test_h1_contains_bold_underline_and_text(self):
        result = format_header(1, 'Title')
        assert BOLD in result
        assert UNDERLINE in result
        assert 'Title' in result

    def test_h1_is_centred(self):
        result = format_header(1, 'Title')
        # Centred H1 has leading spaces
        assert result.lstrip() != result

    def test_h2_has_underline_rule(self):
        result = format_header(2, 'Section')
        assert BOLD in result
        assert 'Section' in result
        # H2 adds a rule on the next line
        assert '\n' in result

    def test_h3_is_bold(self):
        result = format_header(3, 'Sub')
        assert BOLD in result
        assert 'Sub' in result

    def test_h4_is_bold_dim(self):
        result = format_header(4, 'Minor')
        assert BOLD in result
        assert DIM in result
        assert 'Minor' in result

    def test_h5_is_italic(self):
        result = format_header(5, 'Tiny')
        assert ITALIC in result
        assert 'Tiny' in result

    def test_h6_is_dim(self):
        result = format_header(6, 'Smallest')
        assert DIM in result
        assert 'Smallest' in result


# ---------------------------------------------------------------------------
# parse_table_row
# ---------------------------------------------------------------------------

class TestParseTableRow:
    def test_standard_row(self):
        result = parse_table_row('| a | b | c |')
        assert [c.strip() for c in result] == ['a', 'b', 'c']

    def test_single_cell(self):
        result = parse_table_row('| single |')
        assert len(result) == 1
        assert result[0].strip() == 'single'

    def test_row_without_leading_pipe(self):
        result = parse_table_row('a | b | c')
        assert len(result) == 3


# ---------------------------------------------------------------------------
# is_table_row / is_separator_row
# ---------------------------------------------------------------------------

class TestIsTableRow:
    def test_valid_row(self):
        assert is_table_row('| a | b | c |')

    def test_separator_row(self):
        assert is_table_row('|---|---|---|')

    def test_plain_text(self):
        assert not is_table_row('not a table row')

    def test_missing_closing_pipe(self):
        assert not is_table_row('| a | b')


class TestIsSeparatorRow:
    def test_basic_separator(self):
        assert is_separator_row('|---|---|---|')

    def test_separator_with_spaces(self):
        assert is_separator_row('| --- | --- | --- |')

    def test_left_aligned(self):
        assert is_separator_row('| :--- | :--- |')

    def test_right_aligned(self):
        assert is_separator_row('| ---: | ---: |')

    def test_centre_aligned(self):
        assert is_separator_row('| :---: | :---: |')

    def test_mixed_alignment(self):
        assert is_separator_row('| :--- | ---: | :---: |')

    def test_data_row_is_not_separator(self):
        assert not is_separator_row('| a | b | c |')


# ---------------------------------------------------------------------------
# format_table
# ---------------------------------------------------------------------------

class TestFormatTable:
    def test_empty_returns_empty_string(self):
        assert format_table([]) == ''

    def test_basic_table_contains_borders(self):
        rows = [
            [' Header 1 ', ' Header 2 '],
            [' ---', '--- '],
            [' Cell 1 ', ' Cell 2 '],
        ]
        result = format_table(rows)
        assert '+' in result
        assert '|' in result
        assert 'Header 1' in result
        assert 'Cell 1' in result

    def test_separator_row_not_in_output(self):
        rows = [
            [' A ', ' B '],
            [' ---', '---'],
            [' 1 ', ' 2 '],
        ]
        result = format_table(rows)
        # The raw dashes from the separator row must not appear as a data row
        for line in result.split('\n'):
            if '|' in line:
                assert not all(
                    re.match(r'^:?-+:?$', c.strip()) for c in line.strip('|').split('|')
                )

    def test_first_and_last_lines_are_border(self):
        rows = [
            [' Col1 ', ' Col2 '],
            [' ---- ', ' ---- '],
            [' val1 ', ' val2 '],
        ]
        result = format_table(rows)
        table_lines = result.split('\n')
        assert table_lines[0].startswith('+')
        assert table_lines[-1].startswith('+')

    def test_column_widths_align(self):
        rows = [
            [' Short ', ' A very long header '],
            [' --- ', ' --- '],
            [' X ', ' Y '],
        ]
        result = format_table(rows)
        # Every row in the rendered table should have the same length
        table_lines = result.split('\n')
        lengths = [len(line) for line in table_lines]
        assert len(set(lengths)) == 1


# ---------------------------------------------------------------------------
# render_markdown  (integration)
# ---------------------------------------------------------------------------

class TestRenderMarkdown:
    def test_empty_content(self):
        assert render_markdown('') == ''

    def test_h1(self):
        result = render_markdown('# Hello World')
        assert 'Hello World' in result
        assert BOLD in result
        assert UNDERLINE in result

    def test_h2(self):
        result = render_markdown('## Section')
        assert 'Section' in result
        assert BOLD in result
        assert '\n' in result   # underline rule

    def test_h3(self):
        result = render_markdown('### Sub')
        assert BOLD in result
        assert 'Sub' in result

    def test_setext_h1(self):
        result = render_markdown('Title\n=====')
        assert 'Title' in result
        assert BOLD in result

    def test_setext_h2(self):
        result = render_markdown('Section\n-------')
        assert 'Section' in result
        assert BOLD in result

    def test_horizontal_rule_asterisk(self):
        result = render_markdown('***')
        assert '─' in result

    def test_horizontal_rule_dash(self):
        result = render_markdown('---')
        assert '─' in result

    def test_horizontal_rule_underscore(self):
        result = render_markdown('___')
        assert '─' in result

    def test_bold(self):
        result = render_markdown('Hello **world**')
        assert BOLD in result
        assert 'world' in result

    def test_italic(self):
        result = render_markdown('Hello *world*')
        assert ITALIC in result
        assert 'world' in result

    def test_inline_code(self):
        result = render_markdown('Use `cmd` here')
        assert REVERSE in result
        assert 'cmd' in result

    def test_fenced_code_block(self):
        result = render_markdown('```\nprint("hi")\n```')
        assert 'print("hi")' in result
        assert DIM in result

    def test_fenced_code_block_with_language(self):
        result = render_markdown('```python\nx = 1\n```')
        assert 'x = 1' in result

    def test_blockquote(self):
        result = render_markdown('> A quote')
        assert 'A quote' in result
        assert '│' in result

    def test_unordered_list(self):
        result = render_markdown('- Item 1\n- Item 2')
        assert '•' in result
        assert 'Item 1' in result
        assert 'Item 2' in result

    def test_ordered_list(self):
        result = render_markdown('1. First\n2. Second')
        assert 'First' in result
        assert 'Second' in result
        assert FG_YELLOW in result

    def test_link(self):
        result = render_markdown('[example](http://example.com)')
        assert 'example' in result
        assert 'http://example.com' in result
        assert UNDERLINE in result

    def test_image(self):
        result = render_markdown('![logo](logo.png)')
        assert 'Image:' in result
        assert 'logo' in result

    def test_table(self):
        md = '| H1 | H2 |\n|---|---|\n| A | B |'
        result = render_markdown(md)
        assert 'H1' in result
        assert 'H2' in result
        assert 'A' in result
        assert 'B' in result
        assert '+' in result

    def test_blank_lines_preserved(self):
        result = render_markdown('para1\n\npara2')
        lines = result.split('\n')
        # There should be an empty line between the two paragraphs
        assert '' in lines

    def test_paragraph_plain_text(self):
        result = render_markdown('Just plain text.')
        assert 'Just plain text.' in result


# ---------------------------------------------------------------------------
# main() – CLI entry point (both usage modes)
# ---------------------------------------------------------------------------

class TestMain:
    """Integration tests for the two supported invocation modes."""

    def test_mode_file_argument(self, tmp_path):
        """mtp example.md  reads the file and prints rendered output."""
        import io
        import sys
        from mtp import main

        md_file = tmp_path / 'sample.md'
        md_file.write_text('# Hello\n\nWorld', encoding='utf-8')

        captured = io.StringIO()
        old_argv, old_stdout = sys.argv, sys.stdout
        try:
            sys.argv = ['mtp', str(md_file)]
            sys.stdout = captured
            main()
        finally:
            sys.argv = old_argv
            sys.stdout = old_stdout

        out = captured.getvalue()
        assert 'Hello' in out
        assert 'World' in out

    def test_mode_stdin_pipe(self, tmp_path):
        """cat example.md | mtp  reads from stdin and prints rendered output."""
        import io
        import sys
        from mtp import main

        captured = io.StringIO()
        fake_stdin = io.StringIO('# Piped\n\nContent')
        fake_stdin.isatty = lambda: False   # simulate a pipe, not a terminal

        old_argv, old_stdout, old_stdin = sys.argv, sys.stdout, sys.stdin
        try:
            sys.argv = ['mtp']
            sys.stdout = captured
            sys.stdin = fake_stdin
            main()
        finally:
            sys.argv = old_argv
            sys.stdout = old_stdout
            sys.stdin = old_stdin

        out = captured.getvalue()
        assert 'Piped' in out
        assert 'Content' in out

    def test_mode_no_args_tty_prints_usage(self, capsys):
        """Running mtp with no args and no pipe prints a usage message."""
        import io
        import sys
        from mtp import main

        fake_stdin = io.StringIO('')
        fake_stdin.isatty = lambda: True    # simulate interactive terminal

        old_argv, old_stdin = sys.argv, sys.stdin
        try:
            sys.argv = ['mtp']
            sys.stdin = fake_stdin
            with pytest.raises(SystemExit) as exc_info:
                main()
        finally:
            sys.argv = old_argv
            sys.stdin = old_stdin

        assert exc_info.value.code == 1
        err = capsys.readouterr().err
        assert 'Usage' in err

    def test_mode_file_not_found(self, capsys):
        """mtp missing.md prints an error and exits with code 1."""
        import sys
        from mtp import main

        old_argv = sys.argv
        try:
            sys.argv = ['mtp', '/nonexistent/path/missing.md']
            with pytest.raises(SystemExit) as exc_info:
                main()
        finally:
            sys.argv = old_argv

        assert exc_info.value.code == 1
        err = capsys.readouterr().err
        assert 'Error' in err
