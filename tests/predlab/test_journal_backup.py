"""Real local Git remotes and synthetic journals; no network, VPS or market data."""
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import subprocess

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / 'scripts/predlab_journal_backup.sh'
BRANCH = 'predlab-journal-backup'
LEGACY = ('journal.jsonl', 'journal_champion.jsonl')
V2 = ('journal_v2.jsonl', 'journal_champion_v2.jsonl')
PREFIX = 'data/predlab/s1_paper/'
TODAY = datetime.now(timezone.utc).date()
YESTERDAY = str(TODAY - timedelta(days=1))
OLD = str(TODAY - timedelta(days=2))


class LocalBackup:
    def __init__(self, root):
        self.repo, self.remote = root/'source repo', root/'remote.git'
        self.wt, self.data = root/'backup worktree', root/'journals'
        self.data.mkdir()
        self.env = dict(os.environ, GIT_CONFIG_GLOBAL='/dev/null', GIT_CONFIG_NOSYSTEM='1',
                        GIT_TERMINAL_PROMPT='0', GIT_ALLOW_PROTOCOL='file',
                        S1_BACKUP_REPO=str(self.repo), S1_BACKUP_WORKTREE=str(self.wt),
                        S1_BACKUP_DATA=str(self.data), S1_BACKUP_BRANCH=BRANCH)
        self.git(None, 'init', '--bare', str(self.remote))
        self.git(None, 'init', '-b', 'main', str(self.repo))
        self.configure(self.repo)
        (self.repo/'README').write_text('Synthetic fixture only\n')
        (self.repo/'.gitignore').write_text('data/\n')
        self.git(self.repo, 'add', '.')
        self.git(self.repo, 'commit', '-m', 'fixture')
        self.git(self.repo, 'remote', 'add', 'origin', str(self.remote))
        self.git(self.repo, 'push', 'origin', 'main')
        self.source_head = self.git(self.repo, 'rev-parse', 'HEAD').strip()

    def git(self, cwd, *args, check=True):
        r = subprocess.run(['git', *args], cwd=cwd, env=self.env, text=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if check:
            assert r.returncode == 0, r.stderr
        return r.stdout

    def configure(self, repo):
        self.git(repo, 'config', 'user.name', 'Synthetic fixture')
        self.git(repo, 'config', 'user.email', 'fixture@example.invalid')

    def write(self, names, day=YESTERDAY, *, append=False):
        for name in names:
            row = {'asof': day}
            if name in V2:
                row.update(journal_version=2, measurement_status='incomplete')
            with (self.data/name).open('a' if append else 'w') as f:
                f.write(json.dumps(row)+'\n')

    def run(self):
        return subprocess.run(['bash', str(SCRIPT)], env=self.env, text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)

    def remote_head(self):
        return self.git(self.remote, 'rev-parse', BRANCH).strip()

    def saved(self, name):
        return self.git(self.remote, 'show', f'{BRANCH}:{PREFIX}{name}')

    def other_clone(self):
        other = self.data.parent/'other clone'
        self.git(None, 'clone', '--branch', BRANCH, str(self.remote), str(other))
        self.configure(other)
        return other


@pytest.fixture
def backup(tmp_path):
    return LocalBackup(tmp_path)


def test_path_overrides_backup_legacy_without_touching_source_checkout(backup):
    backup.write(LEGACY)
    result = backup.run()
    assert result.returncode == 0, result.stderr
    assert backup.saved(LEGACY[0]) == (backup.data/LEGACY[0]).read_text()
    assert backup.git(backup.repo, 'rev-parse', 'HEAD').strip() == backup.source_head
    assert backup.git(backup.repo, 'branch', '--show-current').strip() == 'main'


@pytest.mark.parametrize('names', [V2, LEGACY + V2, (V2[1],)])
def test_partial_rollout_preserves_every_present_journal_without_requiring_legacy(backup, names):
    backup.write(names)
    result = backup.run()
    assert result.returncode == 0, result.stderr
    for name in names:
        assert backup.saved(name) == (backup.data/name).read_text()
    if set(V2) <= set(names):
        assert 'V2_FRESH' in result.stdout
    else:
        assert 'V2_INCOMPLETE' in result.stdout


def test_fresh_legacy_cannot_hide_missing_or_stale_v2(backup):
    backup.write(LEGACY)
    result = backup.run()
    assert result.returncode == 0, result.stderr
    assert 'V2_INCOMPLETE' in result.stdout
    backup.write(V2, OLD)
    result = backup.run()
    assert result.returncode == 0, result.stderr
    assert 'V2_INCOMPLETE' in result.stdout
    assert 'V2_FRESH' not in result.stdout


def test_backup_excludes_operational_logs_and_unrelated_files(backup):
    backup.write(LEGACY + V2)
    (backup.data/'cron.log').write_text('synthetic-sensitive-operation\n')
    (backup.data/'unrelated.txt').write_text('not a journal\n')
    result = backup.run()
    assert result.returncode == 0, result.stderr
    files = backup.git(backup.remote, 'ls-tree', '-r', '--name-only', BRANCH).splitlines()
    assert PREFIX+'cron.log' not in files
    assert PREFIX+'unrelated.txt' not in files


def test_append_and_repeat_preserve_history_without_extra_commits(backup):
    backup.write(LEGACY + V2, OLD)
    assert backup.run().returncode == 0
    first = backup.remote_head()
    backup.write(LEGACY + V2, append=True)
    assert backup.run().returncode == 0
    second = backup.remote_head()
    assert first != second
    assert backup.run().returncode == 0
    assert backup.remote_head() == second
    for name in LEGACY + V2:
        assert backup.saved(name) == (backup.data/name).read_text()


def test_disappearing_source_journal_does_not_delete_archived_evidence(backup):
    backup.write(LEGACY + V2)
    assert backup.run().returncode == 0
    original = backup.saved(V2[0])
    (backup.data/V2[0]).unlink()
    result = backup.run()
    assert result.returncode == 0, result.stderr
    assert backup.saved(V2[0]) == original
    assert 'V2_INCOMPLETE' in result.stdout


@pytest.mark.parametrize('replacement', ['truncated', 'rewritten'])
def test_source_truncation_or_rewrite_cannot_replace_archived_bytes(backup, replacement):
    backup.write(LEGACY + V2, OLD)
    backup.write(LEGACY + V2, append=True)
    assert backup.run().returncode == 0
    before = backup.remote_head()
    saved = backup.saved(LEGACY[0])
    (backup.data/LEGACY[0]).write_text('' if replacement == 'truncated' else '{"asof":"2000-01-01"}\n')
    result = backup.run()
    assert result.returncode != 0
    assert backup.remote_head() == before
    assert backup.saved(LEGACY[0]) == saved
    assert (backup.wt/PREFIX/LEGACY[0]).read_text() == saved


def test_failed_push_is_retried_even_when_no_new_journal_bytes_arrive(backup):
    backup.write(LEGACY + V2)
    hook = backup.remote/'hooks/pre-receive'
    hook.write_text('#!/bin/sh\nexit 1\n')
    hook.chmod(0o755)
    failed = backup.run()
    assert failed.returncode != 0
    pending = backup.git(backup.wt, 'rev-parse', 'HEAD').strip()
    hook.unlink()
    retry = backup.run()
    assert retry.returncode == 0, retry.stderr
    assert backup.remote_head() == pending
    assert backup.git(backup.wt, 'rev-parse', 'HEAD').strip() == pending


def test_remote_failure_stops_before_local_snapshot_mutation(backup):
    backup.write(LEGACY + V2, OLD)
    assert backup.run().returncode == 0
    before = backup.git(backup.wt, 'rev-parse', 'HEAD').strip()
    archived = (backup.wt/PREFIX/LEGACY[0]).read_bytes()
    backup.write(LEGACY + V2, append=True)
    hidden = backup.remote.with_name('remote-offline.git')
    backup.remote.rename(hidden)
    try:
        failed = backup.run()
        assert failed.returncode != 0
        assert backup.git(backup.wt, 'rev-parse', 'HEAD').strip() == before
        assert (backup.wt/PREFIX/LEGACY[0]).read_bytes() == archived
    finally:
        hidden.rename(backup.remote)
    assert backup.run().returncode == 0


def test_divergent_pull_fails_before_copying_or_committing_source_updates(backup):
    backup.write(LEGACY + V2, OLD)
    assert backup.run().returncode == 0
    other = backup.other_clone()
    (other/'remote-note').write_text('remote history\n')
    backup.git(other, 'add', 'remote-note')
    backup.git(other, 'commit', '-m', 'remote advance')
    backup.git(other, 'push', 'origin', BRANCH)
    (backup.wt/'local-note').write_text('local history\n')
    backup.git(backup.wt, 'add', 'local-note')
    backup.git(backup.wt, 'commit', '-m', 'local advance')
    before = backup.git(backup.wt, 'rev-parse', 'HEAD').strip()
    archived = (backup.wt/PREFIX/LEGACY[0]).read_bytes()
    backup.write(LEGACY + V2, append=True)
    result = backup.run()
    assert result.returncode != 0
    assert backup.git(backup.wt, 'rev-parse', 'HEAD').strip() == before
    assert (backup.wt/PREFIX/LEGACY[0]).read_bytes() == archived


def test_malformed_v2_history_is_preserved_but_never_reported_fresh(backup):
    backup.write(V2, '0000-invalid')
    backup.write(V2, append=True)
    result = backup.run()
    assert result.returncode == 0, result.stderr
    assert backup.saved(V2[0]) == (backup.data/V2[0]).read_text()
    assert 'V2_INCOMPLETE' in result.stdout
    assert 'V2_FRESH' not in result.stdout
