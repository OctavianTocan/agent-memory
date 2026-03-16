#!/usr/bin/env bash
# Install agent-memory: symlink scripts, init DB, install skill, set up hooks
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BIN_DIR="$HOME/.local/bin"
DATA_DIR="${AGENT_MEMORY_DIR:-$HOME/.agent-memory}"
SKILL_SOURCE="$SCRIPT_DIR/skills/agent-memory"

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

# 5. Install skill for Claude Code
if [[ -d "$SKILL_SOURCE" ]]; then
    SKILL_TARGET="$HOME/.claude/skills/agent-memory"
    mkdir -p "$HOME/.claude/skills"

    if [[ -L "$SKILL_TARGET" ]]; then
        rm "$SKILL_TARGET"
    elif [[ -d "$SKILL_TARGET" ]]; then
        rm -rf "$SKILL_TARGET"
    fi

    ln -s "$SKILL_SOURCE" "$SKILL_TARGET"
    echo "  skill: linked to $SKILL_TARGET"
fi

# 6. Set up Claude Code hook (if Claude Code is installed)
CLAUDE_SETTINGS="$HOME/.claude/settings.json"
if [[ -d "$HOME/.claude" ]]; then
    if [[ ! -f "$CLAUDE_SETTINGS" ]]; then
        # No settings file yet, create one with the hook
        cat > "$CLAUDE_SETTINGS" << 'JSON'
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "type": "command",
        "command": "mem-context-hook"
      }
    ]
  }
}
JSON
        echo "  hook: created $CLAUDE_SETTINGS with UserPromptSubmit hook"
    elif ! grep -q "mem-context-hook" "$CLAUDE_SETTINGS" 2>/dev/null; then
        echo "  hook: mem-context-hook not found in $CLAUDE_SETTINGS"
        echo "        Add this to your hooks.UserPromptSubmit array:"
        echo '        { "type": "command", "command": "mem-context-hook" }'
    else
        echo "  hook: mem-context-hook already configured"
    fi
fi

# 7. Set up Gemini CLI hook (if Gemini CLI is installed)
GEMINI_SETTINGS="$HOME/.gemini/settings.json"
if [[ -d "$HOME/.gemini" ]]; then
    if [[ ! -f "$GEMINI_SETTINGS" ]]; then
        cat > "$GEMINI_SETTINGS" << 'JSON'
{
  "hooks": {
    "user_prompt_submit": [
      {
        "command": "mem-context-hook"
      }
    ]
  }
}
JSON
        echo "  hook: created $GEMINI_SETTINGS with user_prompt_submit hook"
    elif ! grep -q "mem-context-hook" "$GEMINI_SETTINGS" 2>/dev/null; then
        echo "  hook: mem-context-hook not found in $GEMINI_SETTINGS"
        echo "        Add this to your hooks.user_prompt_submit array:"
        echo '        { "command": "mem-context-hook" }'
    else
        echo "  hook: mem-context-hook already configured"
    fi
fi

echo ""
echo "==> Done. All agents on this machine now share $DATA_DIR/memory.db"
echo "    Make sure $BIN_DIR is in your PATH."
echo "    Edit $DATA_DIR/.env to add your GEMINI_API_KEY for semantic search."
