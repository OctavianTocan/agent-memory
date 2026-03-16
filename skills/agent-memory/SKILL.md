---
name: agent-memory
description: Persistent memory system for AI coding agents. Use when you need to save facts about the user, store interaction preferences, log session events, or search previously saved memories. Triggers on remembering, saving context, recalling past decisions, or when the user says "remember this". Also use proactively when the user shares personal info, project context, or preferences worth persisting across sessions.
---

# Agent Memory

Persistent, structured memory for AI coding agents. A local SQLite database with semantic search that gives your agent long-term recall across sessions: facts about people and projects, learned interaction preferences, and daily session logs.

All agents on the machine share one database at `~/.agent-memory/memory.db`. Whatever one agent learns, every other agent knows.

## How It Works

Three layers:

1. **Hook** — `mem-context-hook` fires before every message, queries the database, and injects a `=== MEMORY CONTEXT ===` block the agent sees automatically
2. **CLI** — `mem` with subcommands that agents call to read and write memory
3. **Database** — `~/.agent-memory/memory.db` with four tables: facts, soul, daily_logs, embeddings

## CLI Quick Reference

```
mem fact <category> <subject> "<content>"   Save/update a structured fact (auto-embeds)
mem soul <aspect> "<content>"               Save/update an interaction preference
mem log "<note>"                            Append to today's session log
mem search "<query>"                        Semantic search (keyword fallback)
mem query "<sql>"                           Raw SQLite query
mem status                                  Show database stats
mem export                                  Export all data as JSON
```

## Cookbook

Each operation has a detailed guide. **Read the relevant cookbook file before executing.**

| Task | Cookbook | Use When |
|------|---------|----------|
| Install | [cookbook/install.md](cookbook/install.md) | First-time setup, `mem` not found, new machine |
| Save | [cookbook/saving.md](cookbook/saving.md) | Deciding what/when/how to save facts, soul, or logs |
| Search | [cookbook/searching.md](cookbook/searching.md) | Finding previously saved information |
| Rules | [cookbook/rules.md](cookbook/rules.md) | Understanding constraints and best practices |

**When saving or searching memory, read the matching cookbook file first, then act.**

## Quick Decision Tree

```
User shares personal info, people, project context, or preferences?
  → Read cookbook/saving.md, save as fact or soul

User corrects your behavior or expresses a working preference?
  → Read cookbook/saving.md, save as soul

Significant event happens (task complete, decision made)?
  → mem log "<what happened>"

Need to recall something from a past session?
  → Read cookbook/searching.md, search first before asking the user

mem command not found?
  → Read cookbook/install.md, install from scratch
```
