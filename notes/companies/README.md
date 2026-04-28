# Company notes

One file or folder per ticker. Pick by how much material you actually have.

## Flat layout — default

```
notes/companies/TICKER.md
```

Use this for the long tail: a single thesis, no transcripts, no per-quarter
log. Most names live here.

## Folder layout — opt-in promotion

```
notes/companies/TICKER/
├── thesis.md          ← the main analysis (same content as TICKER.md was)
├── history.md         ← dated log: catalysts hit, surprises, thesis revisions
├── earnings/          ← per-quarter notes (e.g. 2026Q1.md)
└── transcripts/       ← raw call transcripts, releases (optional)
```

Promote a ticker to a folder when one of these is true:
- It's a position you hold or actively watch
- You're tracking quarterly evolution of a key metric (e.g. MCR for MOH)
- You've started accumulating earnings releases / transcripts / scheduled
  catalyst notes

To promote: `git mv TICKER.md TICKER/thesis.md`, then add `history.md` with
the first dated entry.

## Conventions

- `thesis.md` is always the entry point. Dashboard "Analysis notes" link
  resolves `TICKER/thesis.md` first, then falls back to `TICKER.md`.
- `history.md` is append-only, newest first, dated entries:
  `## 2026-04-23 — Q1 print: MCR 91.1%, beat, +11%`.
- Earnings files: `earnings/YYYYQN.md` (e.g. `earnings/2026Q1.md`).
- Don't mirror the thesis in history.md. History is the diary; thesis is
  the current view.
