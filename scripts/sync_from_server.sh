#!/bin/bash
# Pull the latest DB from partle (server is source of truth for data)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Pulling stock_data.db from partle..."
rsync -avz --progress hetzner:~/invest/data/stock_data.db "$REPO_ROOT/data/stock_data.db"

echo "Pulling SEC data from partle..."
rsync -avz --progress hetzner:~/invest/data/sec_edgar/ "$REPO_ROOT/data/sec_edgar/"

echo "Done. DB synced from server."
