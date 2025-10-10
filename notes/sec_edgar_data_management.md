# SEC EDGAR Data Management Strategy

## Directory Structure

```
/Users/rubenayla/repos/invest/
├── data/
│   ├── stock_data.db                    # Main database (production)
│   ├── sec_edgar/                        # SEC EDGAR data
│   │   ├── raw/                          # RAW downloads (backup copy - never modified)
│   │   │   ├── companyfacts.zip          # Original bulk download (~5-10 GB)
│   │   │   ├── companyfacts/             # Extracted JSON files (read-only)
│   │   │   │   ├── CIK0000320193.json    # Apple
│   │   │   │   ├── CIK0000789019.json    # Microsoft
│   │   │   │   └── ...                   # ~10,000+ company files
│   │   │   └── download_date.txt         # When downloaded (for reference)
│   │   │
│   │   ├── processed/                    # Working copy for migration
│   │   │   ├── parsed_fundamentals/      # Processed JSON (calculated ratios)
│   │   │   │   ├── AAPL_fundamentals.json
│   │   │   │   ├── MSFT_fundamentals.json
│   │   │   │   └── ...
│   │   │   ├── quarterly_data.csv        # Intermediate CSV (optional)
│   │   │   └── migration_log.txt         # What was imported, when
│   │   │
│   │   └── scripts/                      # Processing scripts
│   │       ├── 1_download_edgar.py       # Download companyfacts.zip
│   │       ├── 2_extract_fundamentals.py # Parse JSON, calculate ratios
│   │       ├── 3_populate_snapshots.py   # Insert into database
│   │       └── verify_data_quality.py    # Sanity checks
│   │
│   ├── backups/                          # Database backups
│   │   ├── stock_data_YYYY-MM-DD.db      # Periodic database snapshots
│   │   └── pre_edgar_migration.db        # Backup before migration
│   │
│   └── stock_cache_backup/               # Existing JSON cache (legacy)
│       └── ... (435 files)
```

## Two-Copy Strategy

### Copy 1: BACKUP (READ-ONLY) - `data/sec_edgar/raw/`
**Purpose**: Permanent archive, never modified
**Location**: `data/sec_edgar/raw/`
**Contents**:
- Original `companyfacts.zip` as downloaded
- Extracted JSON files (10,000+ company files)
- `download_date.txt` with timestamp

**Permissions**:
```bash
# After downloading, make read-only
chmod -R 444 data/sec_edgar/raw/companyfacts/
chmod 444 data/sec_edgar/raw/companyfacts.zip
```

**Size**: ~10-15 GB (compressed + extracted)

**Why keep both ZIP and extracted?**
- ZIP: Quick restore if extracted files get corrupted
- Extracted: Can re-run processing without re-extracting

### Copy 2: WORKING COPY - `data/sec_edgar/processed/`
**Purpose**: Migration and processing workspace
**Location**: `data/sec_edgar/processed/`
**Contents**:
- Parsed fundamental data (calculated ratios, not raw JSON)
- Intermediate CSV files (optional)
- Migration logs

**Permissions**: Read-write (normal)

**Size**: ~1-2 GB (much smaller - only what we need)

**Can be deleted**: After successful migration to database, can be safely deleted

## Backup Strategy

### Before Migration
1. **Backup current database**:
   ```bash
   cp data/stock_data.db data/backups/pre_edgar_migration_$(date +%Y%m%d).db
   ```

2. **Download SEC EDGAR data to raw/**:
   ```bash
   # Download
   wget https://www.sec.gov/Archives/edgar/daily-index/xbrl/companyfacts.zip \
     -O data/sec_edgar/raw/companyfacts.zip

   # Extract
   unzip data/sec_edgar/raw/companyfacts.zip \
     -d data/sec_edgar/raw/companyfacts/

   # Record download date
   date > data/sec_edgar/raw/download_date.txt

   # Make read-only
   chmod -R 444 data/sec_edgar/raw/
   ```

3. **Process to working copy**:
   ```bash
   # Run extraction script
   python data/sec_edgar/scripts/2_extract_fundamentals.py
   # This reads from raw/, writes to processed/
   ```

### After Migration
4. **Verify database**:
   ```bash
   python data/sec_edgar/scripts/verify_data_quality.py
   # Check:
   # - How many snapshots now have fundamental data?
   # - Any NULL values where we expected data?
   # - Outliers or obviously wrong values?
   ```

5. **Create post-migration backup**:
   ```bash
   cp data/stock_data.db data/backups/post_edgar_migration_$(date +%Y%m%d).db
   ```

6. **Optional: Clean working copy**:
   ```bash
   # After successful verification, can delete processed/ to save space
   rm -rf data/sec_edgar/processed/
   ```

## Additional Backup: External Storage

For extra safety, also backup to external location:

### Option 1: Cloud Storage
```bash
# Example: Backup to iCloud, Dropbox, etc.
cp -r data/sec_edgar/raw/ ~/Library/Mobile\ Documents/com~apple~CloudDocs/invest_backups/sec_edgar_raw/
```

### Option 2: External Drive
```bash
# Mount external drive, then:
cp -r data/sec_edgar/raw/ /Volumes/BackupDrive/invest_backups/sec_edgar_raw/
```

### Option 3: Git LFS (NOT RECOMMENDED for large data)
- companyfacts.zip is too large for regular git (~10GB)
- Could use Git LFS, but cloud storage is simpler

## .gitignore Updates

Add to `.gitignore`:
```
# SEC EDGAR data (too large for git)
data/sec_edgar/raw/
data/sec_edgar/processed/

# Database backups
data/backups/

# Keep scripts and documentation
!data/sec_edgar/scripts/
!data/sec_edgar/README.md
```

## Data Refresh Strategy

SEC EDGAR data is updated nightly. Plan for periodic updates:

### Quarterly Refresh (Recommended)
Every 3 months, download fresh data:
```bash
# 1. Download new companyfacts.zip to a dated folder
wget https://www.sec.gov/Archives/edgar/daily-index/xbrl/companyfacts.zip \
  -O data/sec_edgar/raw/companyfacts_$(date +%Y%m%d).zip

# 2. Extract to dated folder
mkdir data/sec_edgar/raw/companyfacts_$(date +%Y%m%d)/
unzip data/sec_edgar/raw/companyfacts_$(date +%Y%m%d).zip \
  -d data/sec_edgar/raw/companyfacts_$(date +%Y%m%d)/

# 3. Process and update database
# 4. Keep old version as historical backup
```

This gives you:
- Historical snapshots of the data
- Ability to compare data quality over time
- Rollback if new data has issues

## Estimated Storage Requirements

| Item | Size | Location |
|------|------|----------|
| companyfacts.zip | ~5-7 GB | `raw/` |
| Extracted JSON files | ~8-10 GB | `raw/companyfacts/` |
| Parsed fundamentals | ~1-2 GB | `processed/` |
| Database (updated) | ~1.5 GB | `stock_data.db` |
| Database backups | ~3 GB | `backups/` (2 copies) |
| **Total** | **~20-25 GB** | |

After migration and cleanup (delete processed/):
- **Permanent storage**: ~18-20 GB
- **Active database**: ~1.5 GB

## Summary

**Safe storage (never touched)**:
- `data/sec_edgar/raw/` - Original SEC EDGAR data (read-only)
- `data/backups/pre_edgar_migration.db` - Database before changes

**Working copy**:
- `data/sec_edgar/processed/` - For migration (can delete after)

**External backup**:
- Copy `raw/` to cloud storage or external drive

This gives you triple redundancy:
1. Local raw copy (read-only)
2. External backup
3. Database backups (before and after migration)
