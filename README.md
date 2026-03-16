# agent-memory

Persistent, structured memory for AI coding agents. A local SQLite database with semantic search that gives your agent long-term recall across sessions: facts about you, learned interaction preferences, daily logs, and vector search over everything.

Works with **Claude Code**, **Cline**, **Gemini CLI**, **Codex CLI**, **Aider**, **Cursor**, **Windsurf**, and anything else that can run shell commands.

Zero dependencies beyond Python 3.9+ and SQLite (both ship with macOS and most Linux distros).

```
You: "I work at Acme Corp as a backend engineer"
  --> auto-extracted to: work / employer: Acme Corp
  --> auto-extracted to: work / role: backend engineer

You: "remember that the deploy freeze starts March 20"
  --> agent calls: mem fact decisions deploy-freeze "starts March 20"

Next session:
=== MEMORY CONTEXT [Tue 18 Mar 2026, 09:15] ===
FACTS:
decisions / deploy-freeze: starts March 20
work / employer: Acme Corp
work / role: backend engineer
=== END MEMORY CONTEXT ===
```

## How it works

All agents on your machine share one database at `~/.agent-memory/memory.db`. Whatever Claude Code learns about you, Cline and Gemini CLI also know. Whatever Cursor saves, Aider can search.

Three layers:

1. **Hook/context injection** -- a script that fires before every message, queries `memory.db`, and injects a context block your agent sees automatically
2. **One CLI** (`mem`) with subcommands that agents call to read/write memory, and you can use directly from your terminal
3. **SQLite database** (`~/.agent-memory/memory.db`) with four tables: facts, soul, daily_logs, embeddings

```
~/.agent-memory/              # Shared data (not in the repo)
├── memory.db                 # The single shared database
└── .env                      # Your GEMINI_API_KEY for semantic search

agent-memory/                 # The repo (code only)
├── bin/
│   ├── mem                   # Unified CLI (mem fact, mem search, mem status, etc.)
│   ├── mem-context-hook      # Hook script for context injection
│   ├── mem-extract           # Auto-extract facts from user messages
│   └── mem-*                 # Individual commands (also work standalone)
├── memlib.py                 # Shared library (DB path resolution, embedding API)
├── install.sh                # One-command setup
└── .env.example              # Template for your Gemini API key
```

## Quick start

```bash
git clone https://github.com/OctavianTocan/agent-memory.git
cd agent-memory
./install.sh
```

That's it. `install.sh` will:
1. Create `~/.agent-memory/` with a `.env` template
2. Symlink `mem` and all scripts to `~/.local/bin/`
3. Initialize the database at `~/.agent-memory/memory.db`

For semantic search, edit `~/.agent-memory/.env` with a free [Gemini API key](https://aistudio.google.com/apikey). Without it, everything works -- `mem search` just falls back to keyword matching.

Then set up whichever agents you use below. They all share the same database.

## Updating

```bash
mem update
```

Or manually: `cd agent-memory && git pull && ./install.sh`

Scripts are symlinked, so pulling updates them in place. Your data in `~/.agent-memory/` is never touched.

---

## CLI

Everything goes through one command: `mem`

```
mem fact <category> <subject> <content>    Save a structured fact + auto-embed
mem soul <aspect> <content>                Save an interaction preference
mem log <note>                             Append to today's session log
mem search <query>                         Semantic search (keyword fallback)
mem query <sql>                            Raw SQLite query
mem embed <text>                           Generate an embedding vector
mem init                                   Initialize the database schema
mem status                                 Show database stats
mem export                                 Export all data as JSON
mem reset                                  Wipe the database (with confirmation)
mem update                                 Pull latest code + re-install
```

Examples:

```bash
mem fact people alice "frontend lead, loves Rust"
mem soul tone "prefers direct answers without preamble"
mem log "shipped v2.1"
mem search "who works on frontend"
mem status
mem export > backup.json
```

---

## Agent setup

### Claude Code

Register `mem-context-hook` as a `UserPromptSubmit` hook.

**`~/.claude/settings.json`:**
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

For the best experience, create an output style that tells Claude how to use memory proactively. Add to `~/.claude/output-styles/assistant.md`:

```markdown
# Assistant Mode

You have a persistent memory system. Use it actively.

## Memory Context Block

Every message you receive is prefixed with an === MEMORY CONTEXT === block.
This contains FACTS, SOUL preferences, and TODAY'S LOG. Treat it as authoritative.

## Memory Commands

| Command | Usage |
|---------|-------|
| `mem fact category subject "content"` | Save a structured fact |
| `mem soul aspect "content"` | Save an interaction preference |
| `mem log "note"` | Log a notable event |
| `mem query "SELECT ..."` | Query memory.db directly |
| `mem search "natural language"` | Semantic search across facts |
```

Activate with `/output-style assistant`.

---

### Cline (VS Code)

Cline v3.36+ supports hooks. Hook scripts are executable files named after the hook type (no extension on macOS/Linux), placed in a hooks directory.

**1. Create the hook script:**

Global hooks go in `~/Documents/Cline/Hooks/`. Project hooks go in `.clinerules/hooks/`.

```bash
# Global (applies to all projects)
mkdir -p ~/Documents/Cline/Hooks

# Or project-level (committable)
mkdir -p .clinerules/hooks
```

Create the hook file named exactly `UserPromptSubmit` (no extension):

```bash
cat > ~/Documents/Cline/Hooks/UserPromptSubmit << 'HOOK'
#!/usr/bin/env bash
# Cline hook: inject agent-memory context into every prompt
INPUT=$(cat)
CONTEXT=$(mem-context-hook < /dev/null 2>/dev/null)
if [[ -n "$CONTEXT" ]]; then
    ESCAPED=$(echo "$CONTEXT" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read()))')
    echo "{\"cancel\":false,\"contextModification\":$ESCAPED}"
else
    echo '{"cancel":false}'
fi
HOOK
chmod +x ~/Documents/Cline/Hooks/UserPromptSubmit
```

The `contextModification` field injects text into the conversation that Cline sees before responding.

**2. Add to your Cline custom instructions** (Settings > Custom Instructions):

```
You have access to a persistent memory system via the `mem` command:
- mem fact category subject "content" -- save a structured fact
- mem soul aspect "content" -- save an interaction preference
- mem log "note" -- log a notable event
- mem search "query" -- semantic search across all facts
- mem query "SQL" -- raw SQLite query

Use these proactively when learning about the user, their project, or their preferences.
The === MEMORY CONTEXT === block injected via hooks contains previously saved knowledge.
```

**3. Enable hooks** in Cline settings (Features > Hooks). macOS and Linux only.

---

### Gemini CLI

Gemini CLI v0.26+ supports hooks similar to Claude Code.

**1. Register the hook in `~/.gemini/settings.json`:**

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

**2. Add memory instructions to your `GEMINI.md`** (in your home directory or project root):

```markdown
## Memory System

You have a persistent memory system. A === MEMORY CONTEXT === block is injected
before every message with previously saved facts, preferences, and session logs.

Available commands (run via shell):
- `mem fact category subject "content"` -- save a fact
- `mem soul aspect "content"` -- save an interaction preference
- `mem log "note"` -- log something notable
- `mem search "query"` -- semantic search across facts
- `mem query "SQL"` -- raw SQLite query

Save facts proactively when you learn about the user or project.
```

---

### Codex CLI (OpenAI)

Codex CLI reads `AGENTS.md` files for custom instructions and can run shell commands.

**1. Add to your `AGENTS.md`** (project root or `~/.codex/AGENTS.md`):

```markdown
## Memory System

You have a persistent memory system backed by SQLite. Before answering, check
for relevant context by running: `mem search "relevant query"`

To save information for future sessions:
- `mem fact category subject "content"` -- structured facts (people, projects, decisions)
- `mem soul aspect "content"` -- interaction preferences
- `mem log "note"` -- session log entries

To inject full context, run: `mem-context-hook < /dev/null`

Save facts proactively when you learn about the user or their project.
```

Codex doesn't have hooks, so context injection is manual (the agent runs `mem-context-hook` or `mem search` when it needs context). You can also prepend it to your prompt:

```bash
# Wrapper that injects memory before each Codex prompt
CONTEXT=$(mem-context-hook < /dev/null 2>/dev/null)
codex --system-prompt "$CONTEXT

You have a persistent memory system. Use mem fact/soul/log to save, mem search to query."
```

---

### Aider

Aider supports `--read` for injecting files and `--system-prompt-extras` for custom system context.

**Option A: Read a live context file (recommended)**

Create a wrapper script `aider-mem`:
```bash
#!/usr/bin/env bash
# Generate fresh memory context into a temp file, pass it to aider
CONTEXT_FILE=$(mktemp /tmp/memory-context.XXXXXX.md)
mem-context-hook < /dev/null > "$CONTEXT_FILE" 2>/dev/null
aider --read "$CONTEXT_FILE" "$@"
rm -f "$CONTEXT_FILE"
```

**Option B: Add to `.aider.conf.yml`**

```yaml
system-prompt-extras: |
  You have a persistent memory system. Run shell commands to use it:
  - mem fact category subject "content" -- save a fact
  - mem soul aspect "content" -- save a preference
  - mem search "query" -- search existing memories
  - mem-context-hook < /dev/null -- get full memory context
  Use these proactively when learning about the user or project.
```

---

### Cursor / Windsurf

These IDE-based agents can't run hooks natively, but you can inject memory through rules files.

**1. Generate a context file on session start:**

Add to your shell profile (`~/.zshrc` or `~/.bashrc`):
```bash
# Auto-refresh memory context for IDE agents
alias refresh-memory='mem-context-hook < /dev/null > .agent-memory-context.md 2>/dev/null'
```

Add `.agent-memory-context.md` to your `.gitignore`.

**2. Reference it in your rules:**

**Cursor** (`.cursor/rules/memory.mdc`):
```
---
description: Persistent memory system
globs: *
alwaysApply: true
---
Read `.agent-memory-context.md` at the start of every conversation for persistent
context about the user and project.

You can save new memories by running these terminal commands:
- mem fact category subject "content"
- mem soul aspect "content"
- mem log "note"
- mem search "query"

After saving new facts, run: refresh-memory
```

**Windsurf** (`.windsurfrules`):
```
Read `.agent-memory-context.md` at the start of every conversation for persistent
context about the user and project.

You can save new memories by running terminal commands:
- mem fact category subject "content"
- mem soul aspect "content"
- mem search "query"

After saving, regenerate context: mem-context-hook < /dev/null > .agent-memory-context.md
```

---

### Any other agent

If your agent can run shell commands, it can use memory:

```
mem fact category subject "content"    Save a fact
mem soul aspect "content"              Save a preference
mem log "note"                         Log something
mem search "query"                     Search memories
mem query "SELECT * FROM facts"        Raw SQL
mem-context-hook < /dev/null           Get full context block
```

Add the above to whatever instructions/rules file your agent reads.

---

## Database schema

```sql
CREATE TABLE facts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    subject TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(category, subject)
);

CREATE TABLE soul (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    aspect TEXT NOT NULL UNIQUE,
    content TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE daily_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fact_id INTEGER NOT NULL UNIQUE,
    vector TEXT NOT NULL,
    model TEXT DEFAULT 'gemini-embedding-2-preview',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (fact_id) REFERENCES facts(id) ON DELETE CASCADE
);
```

## Fact categories

Use whatever makes sense, but these work well as defaults:

| Category | For |
|----------|-----|
| `user_info` | Name, location, personal details |
| `people` | Colleagues, contacts, anyone by name |
| `projects` | Status, constraints, dependencies, decisions |
| `preferences` | Tools, workflows, habits |
| `decisions` | Architectural or workflow decisions |
| `work` | Employer, role, team context |
| `notes` | Everything else |

## Configuration

### Custom data directory

By default, all data lives in `~/.agent-memory/`. Override with:

```bash
export AGENT_MEMORY_DIR=/path/to/your/data
```

All scripts respect this variable. The directory will contain `memory.db` and `.env`.

## Credits

Inspired by [pocket-agent](https://github.com/KenKaiii/pocket-agent).

## License

MIT
