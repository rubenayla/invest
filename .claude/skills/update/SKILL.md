---
name: update
description: Fetch fresh stock data, run valuations, generate dashboard, and start the live server. Use when the user wants to update data and view the dashboard.
disable-model-invocation: true
argument-hint: "[--universe sp500] [--skip-fetch] [--skip-gbm] [--skip-nn] [--skip-classic] [--skip-scanner]"
allowed-tools: Bash
---

# Update Data & Launch Dashboard

Run the full investment analysis pipeline and serve the dashboard.

## Steps

1. **Start the dashboard server** in the background so the user can see progress immediately:
   ```bash
   uv run python neural_network/invest_training_package/scripts/dashboard_server.py &
   ```
   Tell the user: **Dashboard is live at http://localhost:8080**

2. **Run the full update pipeline**. Pass through any arguments the user provided (universe, skip flags):
   ```bash
   uv run python scripts/update_all.py $ARGUMENTS
   ```
   This runs (in order, unless skipped):
   - Data fetching from yfinance
   - GBM predictions (6 variants)
   - Neural network multi-horizon predictions
   - Classic valuations (DCF, RIM, ratios, etc.)
   - Dashboard HTML regeneration
   - Opportunity scanner

   The default universe is `sp500`. Common alternatives: `international`, `japan`, `tech`, `growth`, `europe`, `spain`, `all`, `cached`.

3. **Report completion** — summarize what ran, how long it took, and remind the user the dashboard is at http://localhost:8080

## Important

- Always use `uv run python` for all commands
- Run the dashboard server FIRST so the user gets the link immediately
- The update pipeline can take 10-20 minutes for a full run; keep the user informed of progress
- If the dashboard server is already running on port 8080, skip starting it again and just run the update pipeline
- If the user only says `/update` with no arguments, default to `--universe sp500`
