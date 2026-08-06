#!/usr/bin/env bash
# Daily forward-journal backup: commits the paper-trader journals to the
# dedicated `predlab-journal-backup` branch and pushes to origin.
#
# The push cadence doubles as a heartbeat: if the GitHub branch goes stale,
# the journal (or this cron) is broken. A commit is flagged STALE when the
# journals are missing yesterday's UTC row.
#
# Operates in its own git worktree (predlab-backup-wt) so the main predlab
# checkout — which the hourly paper-trader cron executes from — is never
# switched off its branch. Runs on the VPS from tabot's crontab at
# 00:45 UTC, after the 00:15 journal write.
set -euo pipefail

REPO=/opt/tradingagents/predlab
WT=/opt/tradingagents/predlab-backup-wt
DATA=/opt/tradingagents/predlab-data/predlab/s1_paper
BRANCH=predlab-journal-backup

if [ ! -d "$WT" ]; then
    git -C "$REPO" fetch origin "$BRANCH" 2>/dev/null || true
    git -C "$REPO" worktree add "$WT" -B "$BRANCH" \
        $(git -C "$REPO" rev-parse -q --verify "origin/$BRANCH" >/dev/null \
          && echo "origin/$BRANCH" || echo "HEAD")
fi

cd "$WT"
git pull -q --ff-only origin "$BRANCH" 2>/dev/null || true
mkdir -p data/predlab/s1_paper
cp "$DATA"/journal.jsonl "$DATA"/journal_champion.jsonl data/predlab/s1_paper/
[ -f "$DATA"/cron.log ] && cp "$DATA"/cron.log data/predlab/s1_paper/ || true

YESTERDAY=$(date -u -d "yesterday" +%F)
FLAG=""
grep -q "\"asof\": \"$YESTERDAY\"" data/predlab/s1_paper/journal_champion.jsonl \
    || FLAG="STALE: missing $YESTERDAY — "
LAST=$(tail -1 data/predlab/s1_paper/journal_champion.jsonl \
    | grep -o '"asof": "[0-9-]*"' | cut -d'"' -f4)

git add -f data/predlab/s1_paper/
if ! git diff --cached --quiet; then
    git commit -q -m "${FLAG}journal backup through asof=$LAST"
    git push -q origin "$BRANCH"
    echo "$(date -u +%FT%TZ) pushed backup through $LAST ${FLAG:+(STALE)}"
else
    echo "$(date -u +%FT%TZ) no journal changes"
fi
