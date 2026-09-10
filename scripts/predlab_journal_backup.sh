#!/usr/bin/env bash
# Append-only journal snapshots in the dedicated predlab-journal-backup branch.
# Run manually only when deployment is authorized; the existing cron is 00:45 UTC.
# Defaults match the documented VPS layout. S1_BACKUP_REPO, S1_BACKUP_WORKTREE,
# S1_BACKUP_DATA and S1_BACKUP_BRANCH allow isolated local-repository rehearsals.
# Only the four named journals are copied: operational logs are never added.
set -euo pipefail
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
exec python3 "$SCRIPT_DIR/predlab_journal_backup.py"
