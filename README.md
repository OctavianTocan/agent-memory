# claude-memory

Persistent, structured memory for [Claude Code](https://docs.anthropic.com/en/docs/claude-code). A local SQLite database that gives Claude long-term recall across sessions: facts about you, learned interaction preferences, daily logs, and semantic search over everything.

Zero dependencies beyond Python 3.9+ and SQLite (both ship with macOS and most Linux distros).

```
You: "I work at Acme Corp as a backend engineer"
  --> auto-extracted to: work / employer: Acme Corp
  --> auto-extracted to: work / role: backend engineer

You: "remember that the deploy freeze starts March 20"
  --> Claude calls: mem-fact decisions deploy-freeze "starts March 20"

Next session:
=== MEMORY CONTEXT [Tue 18 Mar 2026, 09:15] ===
FACTS:
decisions / deploy-freeze: starts March 20
work / employer: Acme Corp
work / role: backend engineer
=== END MEMORY CONTEXT ===
```

## How it works

Three layers:

1. **UserPromptSubmit hook** (`mem-context-hook`) fires before every message, queries `memory.db`, and injects a context block that Claude sees automatically
2. **CLI scripts** (`mem-fact`, `mem-soul`, `mem-log`, etc.) that Claude calls to write memory, and you can use directly from your terminal
3. **SQLite database** (`memory.db`) with four tables: facts, soul, daily_logs, embeddings

```
claude-memory/
├── bin/
│   ├── mem-init            # Initialize the database schema
│   ├── mem-fact            # Upsert a structured fact + auto-embed
│   ├── mem-soul            # Upsert an interaction preference
│   ├── mem-log             # Append to today's session log
│   ├── mem-search          # Semantic search (Gemini embeddings, keyword fallback)
│   ├── mem-query           # Raw SQLite query
│   ├── mem-embed           # Generate an embedding for any text
│   ├── mem-extract         # Auto-extract facts from user messages (regex)
│   └── mem-context-hook    # The UserPromptSubmit hook script
├── memlib.py               # Shared library (DB path resolution, embedding API)
├── install.sh              # Symlink bin/ scripts to ~/.local/bin
├── .env.example            # Template for your Gemini API key
├── .gitignore              # Excludes memory.db, .env, __pycache__
├── MEMORY.md               # Quick reference (loaded by Claude)
├── facts.md                # Category template
└── soul.md                 # Soul template
```

## Setup

### 1. Clone and install

```bash
# Clone wherever you want
git clone https://github.com/OctavianTocan/claude-memory.git
cd claude-memory

# Initialize the database
./bin/mem-init

# Symlink scripts to your PATH
./install.sh
```

### 2. Register the hook

Add to your Claude Code settings (`~/.claude/settings.json`):

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

### 3. (Optional) Enable semantic search

Get a [Gemini API key](https://aistudio.google.com/apikey) (free tier works fine) and either:

```bash
# Option A: environment variable
export GEMINI_API_KEY=your_key_here  # add to ~/.zshrc or ~/.bashrc

# Option B: .env file in the repo
cp .env.example .env
# edit .env with your key
```

With a key, `mem-fact` auto-generates embeddings and `mem-search` does cosine similarity ranking. Without it, everything still works -- `mem-search` falls back to keyword matching.

### 4. (Optional) Output style

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
| `mem-fact category subject "content"` | Save a structured fact |
| `mem-soul aspect "content"` | Save an interaction preference |
| `mem-log "note"` | Log a notable event |
| `mem-query "SELECT ..."` | Query memory.db directly |
| `mem-search "natural language"` | Semantic search across facts |
```

Activate with: `/output-style assistant`

## Commands

| Command | What it does | Example |
|---------|-------------|---------|
| `mem-init` | Create/reset DB schema | `mem-init` |
| `mem-fact` | Upsert a fact + embed | `mem-fact people alice "frontend lead"` |
| `mem-soul` | Upsert a preference | `mem-soul tone "prefers direct answers"` |
| `mem-log` | Append to today's log | `mem-log "shipped v2.1"` |
| `mem-search` | Semantic search | `mem-search "who works on frontend"` |
| `mem-query` | Raw SQL | `mem-query "SELECT * FROM facts"` |
| `mem-embed` | Get embedding vector | `mem-embed "some text"` |

## Database schema

```sql
-- Structured knowledge, keyed by (category, subject) for natural upserts
CREATE TABLE facts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    subject TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(category, subject)
);

-- Learned interaction preferences (how Claude should behave with you)
CREATE TABLE soul (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    aspect TEXT NOT NULL UNIQUE,
    content TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Append-only session notes
CREATE TABLE daily_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Gemini vector embeddings for semantic search
CREATE TABLE embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fact_id INTEGER NOT NULL UNIQUE,
    vector TEXT NOT NULL,
    model TEXT DEFAULT 'gemini-embedding-001',
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

## How context injection works

The `mem-context-hook` script runs on every `UserPromptSubmit` event:

1. Reads the user's message JSON from stdin
2. Runs regex extraction (`mem-extract`) to auto-capture facts like "I work at X" or "my name is Y"
3. Queries all facts, soul aspects, and today's logs from the DB
4. Outputs a formatted context block that Claude sees before your message

If the database is empty or doesn't exist, it outputs nothing.

## Configuration

### Custom database location

By default, `memory.db` lives next to `memlib.py`. Override with:

```bash
export CLAUDE_MEMORY_DB=/path/to/your/memory.db
```

All scripts respect this variable.

## Credits

Inspired by [pocket-agent](https://github.com/KenKaiii/pocket-agent). Built for use with [Claude Code](https://docs.anthropic.com/en/docs/claude-code).

## License

MIT
