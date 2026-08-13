# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

## [1.0] - 2026-08-13

### Added
- First stable release. Documented every supported Markdown construct
  with illustrative terminal-mockup screenshots in the README (headers,
  inline formatting, lists/blockquotes/code blocks, tables, and the
  non-printable/hidden-watermark highlighting), generated directly from
  `render_markdown()`'s actual output.

## [0.2] - 2026-08-13

### Changed
- Renamed the project from `mtp` to `md2p` (`mtp.py` → `md2p.py`,
  `test_mtp.py` → `test_md2p.py`, installed binary name, CLI usage text).
  `mtp` collided with the well-known Media Transfer Protocol tooling
  (`mtp-tools`, `libmtp-runtime`) already packaged on most Linux
  distributions; `md2p` is unambiguous and free of naming collisions.

### Fixed
- `_replace_nonprintable` now also flags Unicode variation selectors
  (`U+FE00`–`FE0F`, `U+E0100`–`E01EF`) with the same red-background hex
  marker used for other non-printable characters. Python's
  `str.isprintable()` reports these as printable even though they render
  with zero visible width, so they previously passed through silently —
  this is the block most commonly used to smuggle hidden watermarks or
  payloads onto an otherwise ordinary-looking character.

## [0.1] - 2025

### Added
- Initial release: Markdown-to-terminal renderer (`mtp.py`) supporting
  ATX/setext headers, horizontal rules, blockquotes, fenced code blocks,
  ordered/unordered lists, tables, and inline formatting (bold, italic,
  bold+italic, inline code, links, images).
- `--nroff` output mode emitting nroff overstrike sequences for Midnight
  Commander's internal viewer, alongside the default ANSI/VT220 mode.
- `-v`/`--version` flag.
- stdin pipe support (`cat file.md | mtp`) in addition to a file-path
  argument.
- Non-printable byte handling: any non-printable character in the input
  is replaced with a visible red-background hex marker instead of being
  passed through to the terminal.
- Raw ANSI escape stripping and a 50 MB input size cap, so a malicious
  Markdown file can't inject terminal escape sequences or exhaust memory.
- `install.sh` user-local installer (`~/.local/bin` or `$XDG_BIN_HOME`),
  with `--dest` and `--uninstall` options.
- MIT license.
