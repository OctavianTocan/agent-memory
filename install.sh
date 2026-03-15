#!/usr/bin/env bash
# Install claude-memory: symlink bin scripts to ~/.local/bin
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BIN_DIR="$HOME/.local/bin"

mkdir -p "$BIN_DIR"

for script in "$SCRIPT_DIR"/bin/mem-*; do
    name="$(basename "$script")"
    target="$BIN_DIR/$name"

    if [[ -L "$target" ]]; then
        rm "$target"
    elif [[ -e "$target" ]]; then
        echo "warning: $target exists and is not a symlink, skipping (back it up first)"
        continue
    fi

    ln -s "$script" "$target"
    echo "linked: $target -> $script"
done

echo "done. make sure $BIN_DIR is in your PATH."
