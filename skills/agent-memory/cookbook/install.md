# Install Agent Memory

## Context
First-time setup of agent-memory on a machine where it has never been installed. After this, all agents on the machine share one database.

## Prerequisites
- Python 3.9+ (ships with macOS and most Linux)
- SQLite (ships with Python)
- `git` installed
- `~/.local/bin` in PATH

## Steps

### 1. Check if Already Installed
```bash
command -v mem && mem status
```
If this prints database stats, agent-memory is already installed. Skip to **Verify**.

### 2. Clone the Repo
```bash
git clone https://github.com/OctavianTocan/agent-memory.git ~/.agent-memory-repo
```

### 3. Run the Installer
```bash
cd ~/.agent-memory-repo
./install.sh
```

This will:
1. Create `~/.agent-memory/` with a `.env` template
2. Symlink `mem` and all scripts to `~/.local/bin/`
3. Initialize `~/.agent-memory/memory.db`

### 4. Ensure PATH
If `mem` is not found after install, add to shell profile (`~/.zshrc` or `~/.bashrc`):
```bash
export PATH="$HOME/.local/bin:$PATH"
```
Then reload: `source ~/.zshrc`

### 5. Set Up Semantic Search (Optional)
Get a free [Gemini API key](https://aistudio.google.com/apikey) and add it:
```bash
echo 'GEMINI_API_KEY=your_key_here' > ~/.agent-memory/.env
```
Without this, everything works but `mem search` falls back to keyword matching.

### 6. Set Up Context Hook

**Claude Code** — add to `~/.claude/settings.json`:
```json
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
```

**Gemini CLI** — add to `~/.gemini/settings.json`:
```json
{
  "hooks": {
    "user_prompt_submit": [
      {
        "command": "mem-context-hook"
      }
    ]
  }
}
```

**Other agents** (Cline, Cursor, Windsurf, Aider, Codex): see https://github.com/OctavianTocan/agent-memory#agent-setup

### 7. Verify
```bash
mem status
```
Should print database stats. Try saving a test fact:
```bash
mem fact notes test "install verified"
mem query "DELETE FROM facts WHERE subject='test'"
```

### 8. Done
Tell the user:
- `mem` is now available globally
- The `=== MEMORY CONTEXT ===` block will inject before every message
- Use `mem fact`, `mem soul`, `mem log` to save memories
- Use `mem search` to query them
