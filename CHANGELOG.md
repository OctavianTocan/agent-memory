# Changelog

All notable changes to agent-memory are documented here.

## [0.5.0] - 2026-03-18

### Added
- **npm package**: install via `npm install -g @octavian-tocan/agent-memory`
  - Node.js bin shim delegates to Python scripts -- zero Node dependencies
  - `postinstall` script automatically initializes database, installs Claude Code skill, and configures hooks
  - Registers both `agent-memory` and `mem` as CLI commands
- Integration test suite for dump/import (21 tests, real SQLite, zero mocking)

### Changed
- Removed standalone `mem-fact`, `mem-soul`, `mem-log`, `mem-embed`, `mem-search`, `mem-query` scripts -- use `mem <subcommand>` instead (the unified CLI has had these since v0.2.0)
- `install.sh` now only symlinks `mem` and `mem-context-hook` (no more standalone script symlinks)

## [0.4.0] - 2026-03-18

### Added
- **`mem dump [file]`** -- full database export to a JSON file, including all four tables (facts, soul, daily_logs, embeddings) with complete row data (IDs, timestamps, embedding vectors)
- **`mem import [file] [--force]`** -- import data from a dump file into any database
  - `INSERT OR REPLACE` merge by default (idempotent, safe to re-run)
  - `--force` flag wipes all tables before importing for a clean slate
  - Auto-initializes the database if it doesn't exist
  - Validates dump file structure before importing
- Dump format includes `version` and `exported_at` metadata for forward compatibility
- Integration test suite (`tests/test_dump_import.py`) with 21 tests covering dump, import, round-trip, merge vs force modes, error handling, and cross-directory portability -- all using real SQLite databases with zero mocking

### Changed
- `mem export` kept as a lightweight stdout-only export (facts/soul/logs, no IDs or embeddings); `mem dump` is now the recommended way to back up or migrate

## [0.3.0] - 2026-03-16

### Added
- **Agent-memory skill** with cookbook pattern for Claude Code (`skills/agent-memory/`)
  - `SKILL.md` with CLI reference, decision tree, and cookbook routing
  - `cookbook/install.md` -- step-by-step first-time setup guide
  - `cookbook/saving.md` -- when and how to save facts, soul, and logs
  - `cookbook/searching.md` -- semantic search and raw SQL queries
  - `cookbook/rules.md` -- non-negotiable best practices
- **One-command install** now sets up everything: CLI, database, skill, and hooks
  - Automatically installs the skill to `~/.claude/skills/agent-memory/`
  - Automatically configures `UserPromptSubmit` hook for Claude Code (if `~/.claude/` exists)
  - Automatically configures `user_prompt_submit` hook for Gemini CLI (if `~/.gemini/` exists)
  - Safe: won't overwrite existing settings files, prints manual instructions instead
- Installable via `npx skills add OctavianTocan/agent-memory` (vercel-labs/skills compatible)

### Changed
- `install.sh` expanded from 4 steps to 7 (added skill install, Claude Code hook, Gemini CLI hook)
- README quick start simplified: `git clone && ./install.sh` now does everything
- README reorganized: added Skill section, marked Claude Code/Gemini CLI setup as automatic

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
