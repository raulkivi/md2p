#!/usr/bin/env bash
set -euo pipefail

# Simple installer for mtp into ~/.local/bin (or $XDG_BIN_HOME)

DEST_DIR="${XDG_BIN_HOME:-$HOME/.local/bin}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_FILE="$SCRIPT_DIR/mtp.py"

usage() {
  cat <<EOF
Usage: $0 [--dest DIR]

Installs mtp to the local user binary directory (default: ~/.local/bin).
Options:
  --dest DIR   Install destination directory (overrides XDG_BIN_HOME)
  --uninstall  Remove the installed mtp binary from the destination
  -h, --help   Show this help
EOF
}

if [[ ${1:-} == "--help" || ${1:-} == "-h" ]]; then
  usage
  exit 0
fi

if [[ ${1:-} == "--uninstall" ]]; then
  rm -f "$DEST_DIR/mtp"
  echo "mtp removed from $DEST_DIR"
  exit 0
fi

if [[ ${1:-} == "--dest" ]]; then
  if [[ -z ${2:-} ]]; then
    echo "--dest requires an argument" >&2
    exit 2
  fi
  DEST_DIR="$2"
fi

if [[ ! -f "$SRC_FILE" ]]; then
  echo "Could not find mtp.py in $SCRIPT_DIR" >&2
  exit 1
fi

mkdir -p "$DEST_DIR"
install_path="$DEST_DIR/mtp"
cp "$SRC_FILE" "$install_path"
chmod +x "$install_path"

cat <<EOF
Installed mtp to: $install_path

Make sure '$DEST_DIR' is in your PATH, for example add this to your shell profile:

  export PATH="$DEST_DIR:\$PATH"

You can uninstall with:

  $0 --uninstall

EOF

exit 0
