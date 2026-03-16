# Searching Memory

## Context
How to find previously saved information. Two approaches: semantic search for natural language queries, and raw SQL for precise lookups.

## Before Asking the User, Check Memory First
If the user asks about something that might already be stored (people, projects, decisions, preferences), search memory before asking them to repeat themselves.

## Semantic Search (`mem search`)

Natural language search across all facts. Uses Gemini embeddings with cosine similarity (threshold >= 0.3). Falls back to keyword matching if no API key is configured.

```bash
mem search "who works on frontend"
mem search "what's the deploy process"
mem search "project deadlines"
mem search "how does the user like commit messages"
```

Returns top 5 results ranked by similarity score.

## Raw SQL (`mem query`)

For precise lookups, filtering, and data management. Runs against SQLite directly.

### Common Queries

**Browse all facts in a category:**
```bash
mem query "SELECT * FROM facts WHERE category='people'"
mem query "SELECT * FROM facts WHERE category='projects'"
```

**Search by keyword in content:**
```bash
mem query "SELECT category, subject, content FROM facts WHERE content LIKE '%deploy%'"
```

**Check soul preferences:**
```bash
mem query "SELECT aspect, content FROM soul ORDER BY aspect"
```

**View today's log:**
```bash
mem query "SELECT content, created_at FROM daily_logs WHERE date='2026-03-16' ORDER BY created_at"
```

**View recent logs:**
```bash
mem query "SELECT date, content FROM daily_logs ORDER BY created_at DESC LIMIT 10"
```

**Delete an outdated fact:**
```bash
mem query "DELETE FROM facts WHERE category='notes' AND subject='old-thing'"
```

**Count everything:**
```bash
mem status
```

## Database Schema

Four tables:

- **facts** (`id`, `category`, `subject`, `content`, `created_at`, `updated_at`) — UNIQUE on (category, subject)
- **soul** (`id`, `aspect`, `content`, `created_at`, `updated_at`) — UNIQUE on aspect
- **daily_logs** (`id`, `date`, `content`, `created_at`) — append-only
- **embeddings** (`id`, `fact_id`, `vector`, `model`, `created_at`) — auto-generated, linked to facts

## Other Commands

```bash
mem status     # Database stats (counts, size)
mem export     # Export all data as JSON (for backup)
```
