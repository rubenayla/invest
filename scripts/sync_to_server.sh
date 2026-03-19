#!/bin/bash
# Push ML predictions back to partle (Mac runs models, server serves dashboard)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Pushing stock_data.db to partle..."
rsync -avz --progress "$REPO_ROOT/data/stock_data.db" partle:~/invest/data/stock_data.db

echo "Done. DB synced to server."
