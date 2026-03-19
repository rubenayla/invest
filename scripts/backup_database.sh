#!/bin/bash

# PostgreSQL Backup Script for Invest
# Runs daily backups with rotation (keeps last 7 days)
# Transfers to debian laptop via Cloudflare Tunnel

set -e

# Configuration
BACKUP_DIR="/srv/invest/backups"
LOG_FILE="$BACKUP_DIR/backup.log"
KEEP_DAYS=7

DB_USER="invest"
DB_PASSWORD="invest_2026"
DB_HOST="127.0.0.1"
DB_NAME="invest"

mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.sql"

log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# ── Local backup ─────────────────────────────────────────────────────────

log_message "Starting PostgreSQL backup for invest..."

export PGPASSWORD="$DB_PASSWORD"

if pg_dump -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" > "$BACKUP_FILE"; then
    gzip "$BACKUP_FILE"
    BACKUP_FILE="$BACKUP_FILE.gz"
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    log_message "Backup completed: $(basename "$BACKUP_FILE") ($BACKUP_SIZE)"

    log_message "Cleaning up backups older than $KEEP_DAYS days..."
    find "$BACKUP_DIR" -name "backup_*.sql.gz" -type f -mtime +$KEEP_DAYS -delete
    BACKUP_COUNT=$(find "$BACKUP_DIR" -name "backup_*.sql.gz" -type f | wc -l)
    log_message "Cleanup done. $BACKUP_COUNT backup files remaining."
else
    log_message "ERROR: Backup failed!"
    exit 1
fi

unset PGPASSWORD

# ── Transfer to debian laptop ────────────────────────────────────────────

log_message "Starting backup transfer to debian laptop..."

MAX_RETRIES=8
RETRY_DELAY=30
TRANSFER_SUCCESS=false

try_ssh_command() {
    timeout 120 bash -c "$1"
    return $?
}

for attempt in $(seq 1 $MAX_RETRIES); do
    log_message "Attempt $attempt/$MAX_RETRIES: Creating remote directory..."
    if try_ssh_command "ssh debian 'mkdir -p ~/backups/invest'"; then
        break
    else
        if [ $attempt -lt $MAX_RETRIES ]; then
            log_message "Failed to connect, retrying in ${RETRY_DELAY}s..."
            sleep $RETRY_DELAY
            RETRY_DELAY=$((RETRY_DELAY * 2))
        else
            log_message "ERROR: Failed to connect after $MAX_RETRIES attempts"
            log_message "Local backup OK, remote backup failed."
            exit 0
        fi
    fi
done

RETRY_DELAY=10

for attempt in $(seq 1 $MAX_RETRIES); do
    log_message "Attempt $attempt/$MAX_RETRIES: Transferring backup..."
    if try_ssh_command "scp '$BACKUP_FILE' debian:~/backups/invest/"; then
        log_message "Backup transferred to debian: $(basename "$BACKUP_FILE")"
        TRANSFER_SUCCESS=true
        break
    else
        if [ $attempt -lt $MAX_RETRIES ]; then
            log_message "Transfer failed, retrying in ${RETRY_DELAY}s..."
            sleep $RETRY_DELAY
            RETRY_DELAY=$((RETRY_DELAY * 2))
        else
            log_message "ERROR: Failed to transfer after $MAX_RETRIES attempts"
            log_message "Local backup OK, remote backup failed."
            exit 0
        fi
    fi
done

if [ "$TRANSFER_SUCCESS" = true ]; then
    log_message "Cleaning up old backups on debian..."
    if try_ssh_command "ssh debian 'find ~/backups/invest -name \"backup_*.sql.gz\" -type f -mtime +$KEEP_DAYS -delete'"; then
        REMOTE_COUNT=$(try_ssh_command "ssh debian 'find ~/backups/invest -name \"backup_*.sql.gz\" -type f | wc -l'")
        log_message "Remote cleanup done. $REMOTE_COUNT files on debian."
    else
        log_message "WARNING: Remote cleanup failed"
    fi
fi

log_message "Backup process completed."
