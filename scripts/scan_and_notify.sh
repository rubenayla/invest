#!/bin/bash
# Daily opportunity scanner with Telegram notification
cd ~/repos/invest

BOT_TOKEN="8124443148:AAFbXAY6hZVFLJu2LtDtYMEYDV2PKAzReWA"
CHAT_ID="82808594"

# Run full scan (records to DB), capture notification output
OUTPUT=$(.venv/bin/python scripts/run_opportunity_scan.py --quiet 2>/dev/null)

if [ -n "$OUTPUT" ]; then
    # Telegram has 4096 char limit - truncate if needed
    MSG="${OUTPUT:0:4000}"
    
    curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
        -d chat_id="$CHAT_ID" \
        -d parse_mode="Markdown" \
        --data-urlencode text="$MSG" > /dev/null
fi
