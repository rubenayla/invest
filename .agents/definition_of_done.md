# Definition of Done (DoD) - Invest System

Before considering a task complete, verify the following:

- [ ] **Data Integrity:** Database schema matches script queries (Database is Truth).
- [ ] **Tested:** `uv run pytest` passes for affected modules.
- [ ] **Documented:** New scripts or major changes are reflected in `docs/` or `README.md`.
- [ ] **Clean:** No `debug_*.py` or temporary files left in the root.
- [ ] **Logged:** If a new failure mode was discovered, it is added to `.agents/error_log.md`.
- [ ] **Trend Checked:** (For analysis) Trends verified via `yfinance` income statement before claiming "decline".
- [ ] **Shipped:** Changes are committed and pushed (or explicitly deferred) and `git status` is clean.

Workflow tip: use `scripts/setup-githooks.sh` once, then `scripts/finish.sh -m "Message"` to run tests (when relevant), commit, and push.
