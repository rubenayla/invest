#!/bin/bash
# Daily opportunity scanner + price alerts with Telegram notification
cd ~/repos/invest

BOT_TOKEN="8124443148:AAFbXAY6hZVFLJu2LtDtYMEYDV2PKAzReWA"
CHAT_ID="82808594"

send_telegram() {
    local MSG="${1:0:4000}"
    curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
        -d chat_id="$CHAT_ID" \
        -d parse_mode="Markdown" \
        --data-urlencode text="$MSG" > /dev/null
}

# Run full opportunity scan (records to DB), capture notification output
OUTPUT=$(.venv/bin/python scripts/run_opportunity_scan.py --quiet 2>/dev/null)
if [ -n "$OUTPUT" ]; then
    send_telegram "$OUTPUT"
fi

# Run price target alerts
ALERTS=$(.venv/bin/python scripts/price_alerts.py --quiet 2>/dev/null)
if [ -n "$ALERTS" ]; then
    send_telegram "$ALERTS"
fi
