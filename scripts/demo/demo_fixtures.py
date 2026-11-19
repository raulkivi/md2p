"""Files the demo scenes run against, written into a throwaway HOME."""
from __future__ import annotations

import re
from pathlib import Path
from typing import AbstractSet, Dict, Mapping

SHOWCASE = """\
# md2p showcase

Render **Markdown** in the terminal: *italic*, ***both***, `inline code`
and [links](https://github.com/raulkivi/md2p).

## Lists, quotes and tables

- Headers, lists and tables
  - nested items keep their indent
1. Pipe a file in
2. Read it in place

> Page long files with `md2p FILE | less -R`.

| Option    | Effect                  |
|-----------|-------------------------|
| `--nroff` | overstrike for viewers  |
| `--help`  | usage and options       |
"""

MC_EXT_INI = """\
[mc.ext.ini]
Version=4.0

[markdown]
Regex=\\\\.(md|mkd|mdown|markdown)$
RegexIgnoreCase=true
View=%view{nroff} md2p --nroff %f
"""

_SAFE_PATH = re.compile(r'^[A-Za-z0-9_./-]+$')


def hidden_note() -> str:
    # Generated, not committed: CI's hidden-Unicode scan rejects files that carry these characters.
    # Two bytes, one variation selector per nibble: the usual way to smuggle data onto visible text.
    payload = ''.join(chr(0xFE00 + nibble)
                      for byte in b'ID' for nibble in (byte >> 4, byte & 0x0F))
    # The CR returns the cursor to column 0, so a terminal shows only the second total.
    total = 'Total: 9950 EUR\rTotal: 95 EUR  '
    return (
        '# Payment note\n'
        '\n'
        f'Approved by Alice. Pay by Friday.{payload}\n'
        '\n'
        f'{total}\n'
    )


def demo_files(readme: str) -> Dict[str, str]:
    return {
        'notes/showcase.md': SHOWCASE,
        'notes/note.md': hidden_note(),
        'notes/README.md': readme,
        '.config/mc/mc.ext.ini': MC_EXT_INI,
    }


def md2p_shim(md2p_path: str) -> str:
    if not _SAFE_PATH.match(md2p_path):
        raise ValueError(f'md2p path needs shell quoting: {md2p_path!r}')
    return f'#!/bin/sh\nexec python3 {md2p_path} "$@"\n'


def write_tree(root: Path, files: Mapping[str, str],
               executable: AbstractSet[str] = frozenset()) -> None:
    for rel, content in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        # Bytes, so a lone CR survives newline translation.
        path.write_bytes(content.encode('utf-8'))
        if rel in executable:
            path.chmod(0o755)
