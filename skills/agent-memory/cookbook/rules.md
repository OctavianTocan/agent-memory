# Rules

## Context
Non-negotiable rules for working with agent-memory. Follow these always.

## 1. Always Use `mem` Commands to Write
Never use `sqlite3` directly for writes. The `mem` commands handle:
- Embedding generation (auto-embeds facts for semantic search)
- Proper timestamps (`created_at`, `updated_at`)
- Correct upsert semantics (ON CONFLICT)
- Schema validation

`mem query` is fine for reads and deletes. Just don't INSERT/UPDATE with raw SQL.

## 2. Be Proactive
Don't wait for the user to say "remember this." Extract and save relevant facts as they come up naturally in conversation. If the user mentions a colleague's name and role, save it. If they state a preference, save it as soul.

## 3. Convert Relative Dates to Absolute
When saving facts with dates, always convert to absolute dates.

Bad: `mem fact decisions freeze "starts next Thursday"`
Good: `mem fact decisions freeze "starts 2026-03-19"`

The memory will be read in future sessions where "next Thursday" is meaningless.

## 4. Check Before Duplicating
Before saving a new fact, check if one already exists for that category+subject:
```bash
mem search "relevant query"
# or
mem query "SELECT * FROM facts WHERE category='x' AND subject='y'"
```

If it exists, saving to the same (category, subject) will overwrite it, which is usually fine. But check first to avoid accidentally overwriting something with less information.

## 5. Detail Matters for Debugging
When saving debugging context, write detailed entries that include:
- What was tried
- Why each approach failed
- What's still unexplored

Future sessions depend on this detail to avoid re-suggesting failed approaches.

## 6. Keep Soul Entries Actionable
Each soul entry should clearly describe what to do differently. Include enough context that a future agent session can follow the guidance without additional explanation.

## 7. Don't Save Ephemeral Context
Don't save:
- Information that's in the codebase (derivable from code)
- Git history (use `git log` / `git blame`)
- Fix recipes (the fix is in the code, the commit message has context)
- Temporary debugging state that won't matter tomorrow
