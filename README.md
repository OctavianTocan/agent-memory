# Claude Memory System

Persistent memory for Claude Code, inspired by [pocket-agent](https://github.com/KenKaiii/pocket-agent).

## How It Works

Three layers work together:

### 1. Output Style — static behavioral rules
**File:** `~/.claude/output-styles/assistant.md`
**Activate with:** `/output-style assistant`

Tells Claude when and how to use memory. Keeps the default coding instructions and adds:
- When to call each mem-* command (proactively, not just when asked)
- Behavior rules: confirm before acting, concise, no preamble
- How to interpret the injected memory context block

### 2. UserPromptSubmit Hook — dynamic per-turn injection
**Script:** `~/.local/bin/mem-context-hook`
**Registered in:** `~/.claude/settings.json` (global — all projects)

Fires before every message. Queries `memory.db` and prepends a context block:
```
=== MEMORY CONTEXT [Mon 09 Mar 2026, 18:45] ===

FACTS:
people / harsh: is an asshole
decisions / pr-696: merge first on web-app per Mahi

SOUL:
communication_style: prefers direct, concise responses

TODAY'S LOG:
- [18:30] initialized memory system

=== END MEMORY CONTEXT ===
```
Outputs nothing if the DB is empty — no noise.

### 3. SQLite Database — structured storage
**File:** `~/.claude/projects/-Volumes-Crucial-X10-assistant/memory/memory.db`

| Table | Purpose |
|-------|---------|
| `facts` | Structured knowledge: people, projects, decisions, preferences |
| `soul` | Learned interaction preferences |
| `daily_logs` | Append-only session notes |

## Commands

All scripts live in `~/.local/bin/` and are on PATH.

| Command | Example | Action |
|---------|---------|--------|
| `mem-fact category subject "content"` | `mem-fact people harsh "is an asshole"` | Upsert a fact + generate embedding |
| `mem-soul aspect "content"` | `mem-soul tone "prefers direct answers"` | Upsert soul aspect |
| `mem-log "note"` | `mem-log "merged PR 696"` | Append to today's log |
| `mem-query "SQL"` | `mem-query "SELECT * FROM facts"` | Raw DB query |
| `mem-search "query"` | `mem-search "web app decisions"` | Semantic search (falls back to keyword) |
| `mem-embed "text"` | `mem-embed "some text"` | Generate a Gemini embedding |

## Semantic Search Setup

Requires `GEMINI_API_KEY` in your environment. Add to `~/.zshrc`:
```
export GEMINI_API_KEY=your_key_here
```
Or create `~/.claude/projects/-Volumes-Crucial-X10-assistant/memory/.env`:
```
GEMINI_API_KEY=your_key_here
```

Once set, `mem-fact` automatically generates and stores embeddings. `mem-search` then uses cosine similarity (threshold: 0.3, top 5 results) with keyword fallback.

## Fact Categories

- `user_info` — name, location, personal details
- `people` — colleagues, contacts, anyone by name
- `projects` — project status, constraints, dependencies
- `preferences` — tools, workflows, habits
- `decisions` — architectural or workflow decisions
- `work` — employer, role, team
- `notes` — misc

## Usage

1. Start a session: `/output-style assistant`
2. Memory context is injected automatically before every message
3. Claude saves facts/soul/logs proactively as you talk — you don't need to say "remember"
4. Explicit: "remember that X" or "note that Y" also works
5. Query anytime: `mem-query "SELECT * FROM facts WHERE category='people'"`

## Files

```
~/.claude/
├── output-styles/
│   └── assistant.md              # Output style definition
├── settings.json                 # Hook registered here (global)
└── projects/-Volumes-Crucial-X10-assistant/memory/
    ├── README.md                 # This file
    ├── MEMORY.md                 # Auto-loaded index
    ├── memory.db                 # SQLite database
    ├── memlib.py                 # Shared Python library (embed, DB path)
    └── .env                      # Optional: GEMINI_API_KEY (gitignored)

~/.local/bin/
├── mem-context-hook              # UserPromptSubmit hook (reads stdin, extracts facts, injects context)
├── mem-extract                   # Python: regex fact extraction from message JSON
├── mem-fact                      # Upsert a fact + generate embedding
├── mem-soul                      # Upsert a soul aspect
├── mem-log                       # Append to daily log
├── mem-query                     # Raw SQLite query
├── mem-search                    # Semantic search with Gemini embeddings
└── mem-embed                     # Generate a Gemini embedding for any text
```
