# Error Log - Invest System

This file tracks mistakes and failures in the investment analysis system and the mechanisms added to prevent recurrence.

## Format
```markdown
## YYYY-MM-DD - Brief title
**What happened:** Description of the error
**Prevention added:**
- List of changes made
- Link to postmortem if applicable
```

---

## 2026-02-08 - Initial Workflow Setup
**What happened:** System lacked a structured way to track recurring errors and ensure quality before completion.
**Prevention added:**
- Created `error_log.md` (this file).
- Created `definition_of_done.md`.
- Updated `AGENTS.md` to enforce usage of these files.
