"""Snapshot reviewed closed evidence without changing the active pilot checkout."""
from pathlib import Path
import hashlib
import io
import json
import os
import subprocess
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
STUDY = HERE.parent
BASE = 'f45ffecafec136db14c8214208690110b82dc216'


def save(path, record):
    with path.open('x') as output:
        json.dump(record, output, indent=2, sort_keys=True)


def main():
    local_env = dict(os.environ, GIT_NO_LAZY_FETCH='1')
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, env=local_env, text=True).strip()
    if head != 'c6b568d4b1c177ab94ac37fbad462c2decc721c0':
        raise ValueError('active pilot HEAD differs')
    for asset in ('btc', 'eth'):
        run = ROOT/'research_runs'/('paper-prices-coinmetrics-'+asset+'-20260924')
        if not (run/'complete.json').is_file() or (run/'failed.json').exists():
            raise ValueError('only closed successful source claims enter this checkpoint')
    guard = json.loads((HERE/'fresh-expanded-02-guard/final.json').read_bytes())
    if guard['phase'] != 'complete' or guard['child_exit_code'] != 0 or not guard['cleanup_verified']:
        raise ValueError('offline verification is not cleanly closed')
    fd, index = tempfile.mkstemp(prefix='onchain-checkpoint-04-', suffix='.index')
    os.close(fd); os.unlink(index)
    env = dict(local_env, GIT_INDEX_FILE=index)
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=ROOT, env=env, text=True).strip()
    git('read-tree', BASE)
    git('add', '--', str(STUDY.relative_to(ROOT)), 'tradingagents/research/onchain_replication',
        'tests/research/onchain_replication')
    extras = []
    for asset in ('btc', 'eth'):
        identity = 'paper-prices-coinmetrics-'+asset+'-20260924'
        extras.extend(['research_runs/'+identity,
            'research_artifacts/onchain-paper-replication-2026-09-24/sources/'+identity,
            'research_artifacts/onchain-paper-replication-2026-09-24/runs/'+identity])
    git('add', '-f', '--', *extras)
    commit = git('commit-tree', git('write-tree'), '-p', BASE, '-m',
        'research: preserve verified price coverage and incomplete replication checkpoint')
    branch = 'refs/heads/research/onchain-paper-preparation-20260924-04'
    git('update-ref', branch, commit, '0'*40)
    names = git('diff', '--name-only', BASE, commit).splitlines()
    allowed = ('research/onchain-paper-replication-2026-09-24/',
        'tradingagents/research/onchain_replication/', 'tests/research/onchain_replication/',
        'research_runs/paper-prices-coinmetrics-',
        'research_artifacts/onchain-paper-replication-2026-09-24/sources/paper-prices-coinmetrics-',
        'research_artifacts/onchain-paper-replication-2026-09-24/runs/paper-prices-coinmetrics-')
    if any(not n.startswith(allowed) or '..' in Path(n).parts for n in names):
        raise ValueError('unexpected checkpoint member')
    proc = subprocess.Popen(['git', 'cat-file', '--batch'], cwd=ROOT, env=env,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    archive = HERE/'preparation-snapshot-04-delta.tar.gz'
    members = {}; total = 0
    with archive.open('xb') as output, tarfile.open(fileobj=output, mode='w:gz') as tar:
        for name in names:
            proc.stdin.write((commit+':'+name+'\n').encode()); proc.stdin.flush()
            header = proc.stdout.readline().decode().split()
            if header[1] != 'blob': raise ValueError('checkpoint member is not a blob')
            size = int(header[2])
            if not 0 <= size <= 128*1024**2-total:
                proc.kill(); proc.wait()
                raise ValueError('compact checkpoint byte bound before allocation')
            body = proc.stdout.read(size)
            if proc.stdout.read(1) != b'\n' or len(body) != size:
                raise ValueError('short local Git member')
            total += size
            if total > 128*1024**2: raise ValueError('compact checkpoint byte bound')
            info = tarfile.TarInfo(name); info.size = size; info.mode = 0o644
            tar.addfile(info, io.BytesIO(body))
            members[name] = {'bytes': size, 'sha256': hashlib.sha256(body).hexdigest()}
    proc.stdin.close()
    if proc.wait() != 0: raise ValueError('Git member read failed')
    manifest = HERE/'preparation-snapshot-04-delta.json'
    save(manifest, {'schema_version': 1, 'source_commit': commit, 'base_commit': BASE,
        'members': members, 'member_count': len(members), 'total_bytes': total,
        'archive': str(archive.relative_to(ROOT)), 'archive_bytes': archive.stat().st_size,
        'archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
        'scope': 'exact closed-evidence delta; prior externally recovered base chain required; active pilot and full raw transaction stores excluded'})
    git('read-tree', commit)
    git('add', '--', str(archive.relative_to(ROOT)), str(manifest.relative_to(ROOT)))
    publication = git('commit-tree', git('write-tree'), '-p', commit, '-m',
        'research: package verified source outcomes and checkpoint for external recovery')
    public_branch = 'refs/heads/research/onchain-paper-recovery-bundle-20260924-04'
    git('update-ref', public_branch, publication, '0'*40)
    if git('rev-parse', 'HEAD') != head: raise ValueError('active HEAD changed')
    record = {'commit': commit, 'branch': branch, 'parent': BASE,
        'publication_commit': publication, 'publication_branch': public_branch,
        'member_count': len(members), 'total_bytes': total,
        'archive_bytes': archive.stat().st_size, 'active_HEAD_preserved': head,
        'temporary_index': index, 'external_recovery': 'pending'}
    save(HERE/'preparation-snapshot-04.json', record)
    print(json.dumps(record))


if __name__ == '__main__': main()
