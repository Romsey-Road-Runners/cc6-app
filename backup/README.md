# CC6 Database Backup & Restore

This directory contains scripts to backup and restore the CC6 Firestore database.

## Prerequisites

- Python 3.7+
- Google Cloud SDK configured with appropriate credentials
- `google-cloud-firestore` package installed

```bash
pip install google-cloud-firestore
```

## Backup

Create a backup of the entire CC6 database:

```bash
python backup.py
```

Or specify a custom filename:

```bash
python backup.py my_backup.json
```

The backup includes:
- All participants
- All clubs
- All admin emails
- All seasons with their races and results

## Restore

Restore from a backup file:

```bash
python restore.py backup_file.json
```

**⚠️ Warning**: This will overwrite existing data in Firestore. You'll be prompted to confirm.

## Backup File Format

The backup is stored as JSON with this structure:

```json
{
  "backup_timestamp": "2024-01-01T12:00:00",
  "participants": {
    "A123456": {
      "first_name": "John",
      "last_name": "Doe",
      ...
    }
  },
  "clubs": {
    "Club Name": {
      "short_names": ["Short"]
    }
  },
  "admin_emails": {
    "admin@example.com": {}
  },
  "season": {
    "2024": {
      "age_category_size": 5,
      "is_default": true,
      "races": {
        "Race 1": {
          "date": "2024-01-15",
          "organising_clubs": ["Club A"],
          "results": {
            "1": {
              "participant": {
                "first_name": "Jane",
                ...
              }
            }
          }
        }
      }
    }
  }
}
```

## Usage Examples

### Regular Backup
```bash
# Create timestamped backup
python backup.py

# Output: cc6_backup_20240101_120000.json
```

### Restore from Backup
```bash
python restore.py cc6_backup_20240101_120000.json
```

### Automated Backup (Cron)
```bash
# Add to crontab for daily backups at 2 AM
0 2 * * * cd /path/to/cc6-app/backup && python backup.py
```

## Notes

- Backups preserve the complete nested structure of seasons → races → results
- Large databases may take several minutes to backup/restore
- The restore process uses Firestore batch operations for efficiency
- Timestamps are converted to strings in the backup file
- The restore process will recreate the exact document structure