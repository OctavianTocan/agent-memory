#!/usr/bin/env bash
# Install agent-memory: symlink scripts, init DB, set up data dir
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BIN_DIR="$HOME/.local/bin"
DATA_DIR="${AGENT_MEMORY_DIR:-$HOME/.agent-memory}"

echo "==> Setting up agent-memory"

# 1. Create data directory
mkdir -p "$DATA_DIR"
echo "  data dir: $DATA_DIR"

# 2. Copy .env.example if no .env exists yet
if [[ ! -f "$DATA_DIR/.env" ]]; then
    cp "$SCRIPT_DIR/.env.example" "$DATA_DIR/.env"
    echo "  created: $DATA_DIR/.env (edit with your GEMINI_API_KEY)"
fi

# 3. Symlink bin scripts to PATH
mkdir -p "$BIN_DIR"

for script in "$SCRIPT_DIR"/bin/mem "$SCRIPT_DIR"/bin/mem-*; do
    [[ ! -f "$script" ]] && continue
    name="$(basename "$script")"
    target="$BIN_DIR/$name"

    if [[ -L "$target" ]]; then
        rm "$target"
    elif [[ -e "$target" ]]; then
        echo "  warning: $target exists and is not a symlink, skipping (back it up first)"
        continue
    fi

    ln -s "$script" "$target"
    echo "  linked: $name"
done

# 4. Initialize the database
"$BIN_DIR/mem" init

echo ""
echo "==> Done. All agents on this machine now share $DATA_DIR/memory.db"
echo "    Make sure $BIN_DIR is in your PATH."
echo "    Edit $DATA_DIR/.env to add your GEMINI_API_KEY for semantic search."
