# Claude Memory Index

Memory system is active. See [README.md](README.md) for full docs.

## Quick Commands
- `mem-fact category subject "content"` — save a fact
- `mem-soul aspect "content"` — save interaction preference
- `mem-log "note"` — log something notable
- `mem-query "SELECT ..."` — query memory.db directly

**IMPORTANT:** Always use these scripts to write/read memory. NEVER use `sqlite3` directly.

## Current Soul
- `communication_style`: prefers direct, concise responses. confirm before acting

## Check Memory
```
mem-query "SELECT * FROM facts ORDER BY category"
mem-query "SELECT * FROM soul"
mem-query "SELECT * FROM daily_logs WHERE date=date('now')"
```
