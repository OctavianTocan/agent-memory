# Saving Memories

## Context
Guidelines for when and how to save facts, soul preferences, and log entries. The key distinction: facts are structured knowledge, soul is behavioral guidance, logs are session events.

## Facts (`mem fact`)

### When to Save
- People: colleagues, contacts, anyone mentioned by name
- Personal info: location, role, employer, relationships
- Project context: status, constraints, dependencies, decisions
- Preferences: tools, workflows, habits
- Commitments or deadlines
- Decisions made

### When NOT to Save
- Casual remarks or thinking out loud
- Temporary context only relevant to this conversation
- Hypotheticals or brainstorming that hasn't been decided
- Information already in the codebase or git history

### How It Works
Facts are keyed by `(category, subject)`. Saving to the same key overwrites the previous value (upsert). Each save auto-generates a Gemini embedding for semantic search.

### Categories

| Category | For |
|----------|-----|
| `user_info` | Name, location, personal details |
| `people` | Colleagues, contacts, anyone by name |
| `projects` | Status, constraints, dependencies, decisions |
| `preferences` | Tools, workflows, habits |
| `decisions` | Architectural or workflow decisions |
| `work` | Employer, role, team context |
| `notes` | Everything else |

Use whatever category makes sense. These are defaults, not a strict list.

### Descriptions

Use `--desc` to provide a short one-liner (under 80 chars) for the memory context index. The description is what agents see at a glance; the full content is fetched on demand via `mem query`.

Good descriptions are scannable and capture the essential "what is this about":
- `--desc "Frontend colleague, GitHub alice-dev, ping for reviews"`
- `--desc "Deploy freeze starts 2026-03-20 for mobile release"`
- `--desc "Migrating to OAuth2, deadline 2026-04-01"`

Without `--desc`, the hook falls back to truncating content to 80 chars.

### Examples
```bash
mem fact people alice "frontend lead, loves Rust, GitHub: alice-dev" --desc "Frontend colleague, GitHub alice-dev"
mem fact work employer "Acme Corp"
mem fact decisions deploy-freeze "starts 2026-03-20, no non-critical merges until mobile release cut" --desc "Deploy freeze starts 2026-03-20 for mobile release"
mem fact projects web-app "migrating auth to OAuth2, deadline 2026-04-01" --desc "Migrating to OAuth2, deadline 2026-04-01"
mem fact preferences package-manager "always use pnpm, never hardcode npm"
```

### Debugging Context
When saving debugging context, write **detailed** entries:
- What was tried
- Why each approach failed
- What's still unexplored

Bad: `mem fact notes bug "tried multiple approaches, none working"`
Good: `mem fact notes chat-jump "Tried: (1) scroll-to-bottom on mount - fails because container height not settled, (2) useLayoutEffect - same timing issue, (3) ResizeObserver - fires too late. Unexplored: intersection observer, virtual scroll"`

## Soul (`mem soul`)

### When to Save
- User corrects your tone, style, or approach
- User expresses frustration or appreciation about how you responded
- A clear working preference emerges from repeated behavior
- You notice a pattern in what the user likes/dislikes

### How It Works
Soul entries are keyed by `aspect` (unique). Saving the same aspect overwrites.

### Keep Entries Actionable
Each entry should clearly describe what to do differently.

Bad: `mem soul code "user likes clean code"`
Good: `mem soul code_patterns "always add TSDoc to functions, inline comments explaining WHY not WHAT, View/Container pattern in React"`

### Examples
```bash
mem soul communication_style "prefers direct answers without preamble, confirm before acting"
mem soul commit_format "always use conventional commits: type(scope): description"
mem soul writing_style "never use em dashes in messages or text"
mem soul intent_parsing "when user says 'I need to X', treat as something to remember, not a command. Ask first."
```

## Log (`mem log`)

### When to Save
- A significant task completes
- An important decision is made mid-session
- Something worth remembering about this session happens

### How It Works
Log entries are **append-only** (never upserted). Each gets a timestamp and is grouped by date. They appear in the `TODAY'S LOG` section of the memory context block.

### Examples
```bash
mem log "shipped v2.1 to production"
mem log "decided to use Zustand over Redux for state management"
mem log "merged PR #697 after fixing mobile chat jump"
mem log "user approved the new API design, moving to implementation"
```
