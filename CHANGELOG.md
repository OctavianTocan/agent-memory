# Changelog

All notable changes to agent-memory are documented here.

## [0.2.0] - 2026-03-16

### Added
- **Unified `mem` CLI** with subcommands: `mem fact`, `mem soul`, `mem log`, `mem search`, `mem query`, `mem embed`, `mem init`, `mem status`, `mem export`, `mem reset`, `mem update`
- `mem status` -- show database stats (fact count, soul aspects, logs, DB size)
- `mem export` -- dump all data as JSON to stdout
- `mem reset` -- wipe the database with confirmation prompt
- `mem update` -- pull latest code and re-install in one command
- `mem-init` script for initializing the database schema
- Shared `~/.agent-memory/` data directory so all agents on the machine share one database
- `AGENT_MEMORY_DIR` env var to customize data location
- Setup instructions for **Cline**, **Gemini CLI**, **Codex CLI**, **Aider**, **Cursor**, **Windsurf**
- `.env.example` template
- MIT license

### Changed
- Upgraded embedding model from `gemini-embedding-001` to `gemini-embedding-2-preview` (Google's multimodal embedding model, March 2026)
- Bumped embedding dimensions from 768 to 3072 for better semantic resolution
- All scripts now resolve paths via `realpath` (works through symlinks)
- `install.sh` now creates `~/.agent-memory/`, symlinks scripts, copies `.env` template, and runs `mem init` automatically
- `.env` and `memory.db` now live in `~/.agent-memory/` instead of the repo directory
- Shell scripts (`mem-query`, `mem-context-hook`) use `AGENT_MEMORY_DIR` instead of hardcoded paths

### Fixed
- Cline hooks documentation corrected: proper file naming (`UserPromptSubmit`, no extension), correct directory (`~/Documents/Cline/Hooks/`), correct output format (`contextModification`, not `message`)
- Symlink resolution in all scripts (was using `abspath`, now uses `realpath`)

## [0.1.0] - 2026-03-15

### Added
- Initial release
- SQLite database with facts, soul, daily_logs, and embeddings tables
- `mem-fact` -- upsert structured facts with auto-embedding
- `mem-soul` -- upsert interaction preferences
- `mem-log` -- append to daily session log
- `mem-search` -- semantic search with Gemini embeddings, keyword fallback
- `mem-query` -- raw SQLite queries
- `mem-embed` -- generate embedding vectors
- `mem-extract` -- auto-extract facts from user messages via regex
- `mem-context-hook` -- UserPromptSubmit hook for context injection
- `memlib.py` shared library with DB path resolution and embedding API
- `install.sh` for symlinking scripts to `~/.local/bin`
- Claude Code hook setup
