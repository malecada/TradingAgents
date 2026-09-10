"""Scoped append-only journal backup; stdlib only, no trading/account access.

BACKUP_SYNCED reports Git delivery. V2_FRESH reports source-journal dates and
versions only, not complete measurement, execution reconciliation or validation.
"""
from datetime import date, datetime, timedelta, timezone
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys

NAMES = ('journal.jsonl', 'journal_champion.jsonl',
         'journal_v2.jsonl', 'journal_champion_v2.jsonl')
V2 = NAMES[2:]
PREFIX = Path('data/predlab/s1_paper')


def git(repo, *args, check=True):
    result = subprocess.run(['git', '-C', str(repo), *args],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and result.returncode:
        # Avoid dumping remote URLs, credentials or unrelated Git output to cron.
        raise RuntimeError(f'git {args[0]} failed (exit {result.returncode})')
    return result


def freshness(raw, expected, versioned):
    result = {'present': raw is not None, 'fresh': False, 'last_asof': None}
    if raw is None:
        return result
    try:
        rows = [json.loads(line) for line in raw.decode().splitlines() if line.strip()]
        days = [row['asof'] for row in rows]
        if not rows or any(not isinstance(d, str) for d in days):
            return result
        dates = [date.fromisoformat(d) for d in days]
        result['last_asof'] = days[-1]
        result['measurement_status'] = rows[-1].get('measurement_status')
        result['fresh'] = (days[-1] == expected and dates == sorted(set(dates)) and
                           (not versioned or all(row.get('journal_version') == 2 for row in rows)))
    except (UnicodeError, ValueError, KeyError, TypeError, AttributeError):
        result['unreadable'] = True
    return result


def backup():
    repo = Path(os.environ.get('S1_BACKUP_REPO', '/opt/tradingagents/predlab')).resolve()
    wt = Path(os.environ.get('S1_BACKUP_WORKTREE', '/opt/tradingagents/predlab-backup-wt')).resolve()
    data = Path(os.environ.get('S1_BACKUP_DATA', '/opt/tradingagents/predlab-data/predlab/s1_paper')).resolve()
    branch = os.environ.get('S1_BACKUP_BRANCH', 'predlab-journal-backup')
    git(repo, 'check-ref-format', '--branch', branch)
    common = Path(git(repo, 'rev-parse', '--path-format=absolute', '--git-common-dir').stdout.decode().strip())
    with (common/'s1-journal-backup.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RuntimeError('another journal backup holds the lock') from error
        if not data.is_dir():
            raise RuntimeError('source journal directory is missing')
        snapshots = {name: (data/name).read_bytes() for name in NAMES if (data/name).is_file()}
        if not snapshots:
            raise RuntimeError('no source journals available')
        expected = str(datetime.now(timezone.utc).date() - timedelta(days=1))
        health = {name: freshness(snapshots.get(name), expected, name in V2) for name in NAMES}
        flag = 'V2_FRESH' if all(health[name]['fresh'] for name in V2) else 'V2_INCOMPLETE'

        # A missing remote branch is normal on first run; remote failure is not.
        remote = git(repo, 'ls-remote', '--heads', 'origin', f'refs/heads/{branch}').stdout
        remote_ref = f'refs/remotes/origin/{branch}'
        if remote:
            git(repo, 'fetch', '--no-tags', 'origin', f'refs/heads/{branch}:{remote_ref}')
        if not wt.exists():
            wt.parent.mkdir(parents=True, exist_ok=True)
            exists = git(repo, 'show-ref', '--verify', '--quiet', f'refs/heads/{branch}', check=False).returncode == 0
            if exists:
                git(repo, 'worktree', 'add', str(wt), branch)
            else:
                git(repo, 'worktree', 'add', '-b', branch, str(wt), remote_ref if remote else 'HEAD')
        actual_common = git(wt, 'rev-parse', '--path-format=absolute', '--git-common-dir').stdout.decode().strip()
        actual_branch = git(wt, 'branch', '--show-current').stdout.decode().strip()
        if Path(actual_common).resolve() != common.resolve() or actual_branch != branch:
            raise RuntimeError('backup worktree belongs to a different repository or branch')
        allowed = {str(PREFIX/name) for name in NAMES}
        dirty = set()
        for args in [('diff', '--name-only', '-z'), ('diff', '--cached', '--name-only', '-z'),
                     ('ls-files', '--others', '--exclude-standard', '-z')]:
            dirty.update(p for p in git(wt, *args).stdout.decode().split('\0') if p)
        if dirty - allowed or any(Path(p).name not in snapshots for p in dirty):
            raise RuntimeError('unrelated or unavailable-source changes in backup worktree')
        if remote and git(wt, 'merge-base', '--is-ancestor', remote_ref, 'HEAD', check=False).returncode:
            # Preserve local pending commits after a failed push; never reset them.
            # Divergence or an obstructed fast-forward must fail before copying.
            git(wt, 'merge', '--ff-only', remote_ref)

        # Validate every candidate before any copy. Missing sources leave old
        # files intact; source rewrites/truncations cannot replace either a
        # committed snapshot or a pending snapshot from an interrupted attempt.
        for name, raw in snapshots.items():
            rel = str(PREFIX/name)
            old = git(wt, 'show', f'HEAD:{rel}', check=False)
            dest = wt/rel
            previous = ([old.stdout] if old.returncode == 0 else [])
            if dest.is_file():
                previous.append(dest.read_bytes())
            if any(not raw.startswith(prior) for prior in previous):
                raise RuntimeError(f'non-append journal change refused: {name}')
        for name, raw in snapshots.items():
            dest = wt/PREFIX/name
            dest.parent.mkdir(parents=True, exist_ok=True)
            if not dest.exists() or dest.read_bytes() != raw:
                dest.write_bytes(raw)
            git(wt, 'add', '-f', '--', str(PREFIX/name))
        changed = git(wt, 'diff', '--cached', '--quiet', check=False).returncode
        if changed not in (0, 1):
            raise RuntimeError('cannot inspect staged journal changes')
        if changed:
            git(wt, 'commit', '-m', f'{flag}: journal backup expected asof={expected}')
        # Always push: a previous rejected push may have left an unpushed commit
        # even though this wake finds no additional journal bytes.
        git(wt, 'push', 'origin', f'HEAD:refs/heads/{branch}')
        print(f'BACKUP_SYNCED {flag} ' + json.dumps(dict(expected_asof=expected,
            journals=health, commit_created=bool(changed),
            commit=git(wt, 'rev-parse', 'HEAD').stdout.decode().strip()), sort_keys=True))


if __name__ == '__main__':
    try:
        backup()
    except (OSError, ValueError, RuntimeError) as error:
        print(f'backup failed: {error}', file=sys.stderr)
        sys.exit(1)
