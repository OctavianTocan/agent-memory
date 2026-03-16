# Install Agent Memory

## Context
First-time setup of agent-memory on a machine where it has never been installed. One command does everything.

## Prerequisites
- Python 3.9+ (ships with macOS and most Linux)
- SQLite (ships with Python)
- `git` installed

## Steps

### 1. Check if Already Installed
```bash
command -v mem && mem status
```
If this prints database stats, agent-memory is already installed. Skip to **Verify**.

### 2. Clone and Install
```bash
git clone https://github.com/OctavianTocan/agent-memory.git
cd agent-memory
./install.sh
```

This single command will:
1. Create `~/.agent-memory/` with a `.env` template
2. Symlink `mem` and all scripts to `~/.local/bin/`
3. Initialize `~/.agent-memory/memory.db`
4. Install the agent-memory skill to `~/.claude/skills/`
5. Configure the `UserPromptSubmit` hook for Claude Code (if installed)
6. Configure the `user_prompt_submit` hook for Gemini CLI (if installed)

### 3. Ensure PATH
If `mem` is not found after install, add to shell profile (`~/.zshrc` or `~/.bashrc`):
```bash
export PATH="$HOME/.local/bin:$PATH"
```
Then reload: `source ~/.zshrc`

### 4. Set Up Semantic Search (Optional)
Get a free [Gemini API key](https://aistudio.google.com/apikey) and add it:
```bash
echo 'GEMINI_API_KEY=your_key_here' > ~/.agent-memory/.env
```
Without this, everything works but `mem search` falls back to keyword matching.

### 5. Verify
```bash
mem status
```
Should print database stats.

### 6. Done
Tell the user:
- `mem` is now available globally
- The `=== MEMORY CONTEXT ===` block will inject before every message
- Use `mem fact`, `mem soul`, `mem log` to save memories
- Use `mem search` to query them
- For other agents (Cline, Cursor, Windsurf, Aider, Codex): see https://github.com/OctavianTocan/agent-memory#agent-setup
