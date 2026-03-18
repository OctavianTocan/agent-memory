#!/usr/bin/env bash
# npm postinstall -- initialize database, install skill, set up hooks.
# Runs automatically after `npm install -g @octavian-tocan/agent-memory`.
# Non-fatal: postinstall failures should not block npm install (package.json uses || true).
set -euo pipefail

# Resolve the package root (parent of scripts/)
PKG_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DATA_DIR="${AGENT_MEMORY_DIR:-$HOME/.agent-memory}"
SKILL_SOURCE="$PKG_ROOT/skills/agent-memory"

echo "==> Setting up agent-memory"

# 1. Create data directory
mkdir -p "$DATA_DIR"
echo "  data dir: $DATA_DIR"

# 2. Copy .env.example if no .env exists yet
if [[ ! -f "$DATA_DIR/.env" ]]; then
    if [[ -f "$PKG_ROOT/.env.example" ]]; then
        cp "$PKG_ROOT/.env.example" "$DATA_DIR/.env"
        echo "  created: $DATA_DIR/.env (edit with your GEMINI_API_KEY)"
    fi
fi

# 3. Check Python is available
if ! command -v python3 &>/dev/null; then
    echo "  warning: python3 not found -- install Python 3.9+ and run 'mem init' manually"
    exit 0
fi

# 4. Initialize the database
python3 "$PKG_ROOT/bin/mem" init

# 5. Install skill for Claude Code
if [[ -d "$SKILL_SOURCE" ]]; then
    SKILL_TARGET="$HOME/.claude/skills/agent-memory"
    mkdir -p "$HOME/.claude/skills" 2>/dev/null || true

    if [[ -d "$HOME/.claude/skills" ]]; then
        if [[ -L "$SKILL_TARGET" ]]; then
            rm "$SKILL_TARGET"
        elif [[ -d "$SKILL_TARGET" ]]; then
            rm -rf "$SKILL_TARGET"
        fi

        ln -s "$SKILL_SOURCE" "$SKILL_TARGET"
        echo "  skill: linked to $SKILL_TARGET"
    fi
fi

# 6. Set up Claude Code hook (if Claude Code is installed)
CLAUDE_SETTINGS="$HOME/.claude/settings.json"
if [[ -d "$HOME/.claude" ]]; then
    if [[ ! -f "$CLAUDE_SETTINGS" ]]; then
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
echo "    Edit $DATA_DIR/.env to add your GEMINI_API_KEY for semantic search."
