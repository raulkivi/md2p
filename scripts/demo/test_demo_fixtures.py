import os
import sys
from pathlib import Path

import pytest

from demo_fixtures import MC_EXT_INI, SHOWCASE, demo_files, hidden_note, md2p_shim, write_tree

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from md2p import _replace_nonprintable, render_markdown  # noqa: E402


def _cat_view(line):
    """What a terminal shows for *line*: a CR returns to column 0 and later text overwrites."""
    screen = []
    col = 0
    for ch in line:
        if ch == '\r':
            col = 0
            continue
        if 0xFE00 <= ord(ch) <= 0xFE0F:
            continue  # zero width
        if col < len(screen):
            screen[col] = ch
        else:
            screen.append(ch)
        col += 1
    return ''.join(screen).rstrip()


def test_showcase_fits_one_80x24_screen(monkeypatch):
    monkeypatch.setenv('COLUMNS', '80')

    lines = render_markdown(_replace_nonprintable(SHOWCASE)).split('\n')

    # Two prompt lines (command and the next prompt) share the 24 rows.
    assert len(lines) <= 22


def test_hidden_note_looks_innocent_under_cat():
    shown = [_cat_view(line) for line in hidden_note().split('\n')]

    assert 'Total: 95 EUR' in shown
    assert not any('9950' in line for line in shown)


def test_hidden_note_carries_a_carriage_return_and_variation_selectors():
    note = hidden_note()

    assert '\r' in note
    assert sum(1 for ch in note if 0xFE00 <= ord(ch) <= 0xFE0F) >= 3


def test_md2p_reveals_what_cat_hides():
    out = _replace_nonprintable(hidden_note())

    assert '<0D>' in out
    assert '9950' in out
    assert '<EF,B8,' in out


def test_mc_ext_ini_views_markdown_through_md2p_nroff():
    assert MC_EXT_INI.startswith('[mc.ext.ini]\nVersion=4.0\n')
    assert 'View=%view{nroff} md2p --nroff %f' in MC_EXT_INI
    # mc's ini parser unescapes values: a single backslash before "." is dropped as invalid.
    assert 'Regex=\\\\.(md|mkd|mdown|markdown)$' in MC_EXT_INI


def test_demo_files_layout():
    files = demo_files(readme='# R\n')

    assert files == {
        'notes/showcase.md': SHOWCASE,
        'notes/note.md': hidden_note(),
        'notes/README.md': '# R\n',
        '.config/mc/mc.ext.ini': MC_EXT_INI,
    }


def test_md2p_shim_runs_the_given_script():
    shim = md2p_shim('/src/md2p.py')

    assert shim.startswith('#!/bin/sh\n')
    assert 'exec python3 /src/md2p.py "$@"' in shim


def test_md2p_shim_rejects_paths_that_need_quoting():
    with pytest.raises(ValueError):
        md2p_shim("/src/it's here/md2p.py")


def test_write_tree_creates_parents_and_keeps_bytes(tmp_path):
    write_tree(tmp_path, {'a/b/c.md': 'x\ry\n', 'bin/md2p': '#!/bin/sh\n'}, executable={'bin/md2p'})

    assert (tmp_path / 'a/b/c.md').read_bytes() == b'x\ry\n'
    assert os.access(tmp_path / 'bin/md2p', os.X_OK)
    assert not os.access(tmp_path / 'a/b/c.md', os.X_OK)
