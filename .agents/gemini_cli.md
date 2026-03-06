# Gemini CLI Context

**Resume Capability**
The CLI supports resuming previous sessions. This restores conversation history but check `AGENTS.md` or status files for project context.
- `gemini --resume` (or `-r`) resumes the latest session.
- `gemini --resume <index>` resumes a specific session.
- `gemini --list-sessions` lists available sessions.

**Other Useful Flags**
- `--yolo`: Automatically accepts all tool calls (use with caution).
- `--sandbox`: Runs in a sandbox environment.
- `--prompt-interactive` (`-i`): Execute a prompt and continue interactively.
