"""Fresh two-blob remote recovery of the exact retained source preparation."""
import hashlib
import json
import os
import stat
import subprocess
import sys
import tarfile
from pathlib import Path, PurePosixPath

ROOT = Path.cwd()
HERE = Path(__file__).resolve().parent
MAX = 4194304
COMMIT = sys.argv[1]
assert len(COMMIT) == 40 and all(c in '0123456789abcdef' for c in COMMIT)

def sha(body):
    return hashlib.sha256(body).hexdigest()

def git(args, root=ROOT):
    p = subprocess.run(['git', *args], cwd=root, capture_output=True, timeout=60)
    assert p.returncode == 0 and max(len(p.stdout), len(p.stderr)) <= MAX
    return p.stdout

def put(path, body):
    with path.open('xb') as f:
        f.write(body)
        f.flush()
        os.fsync(f.fileno())

branch = 'research/onchain-paper-replication-2026-09-24'
assert git(['ls-remote', 'origin', 'refs/heads/' + branch]).decode().split()[0] == COMMIT
out = HERE / 'source-preparation-recovery01'
out.mkdir(mode=0o700)
repo = out / 'repository.git'
git(['init', '--bare', str(repo)])
git(['remote', 'add', 'origin', git(['remote', 'get-url', 'origin']).decode().strip()], repo)
git(['config', 'remote.origin.promisor', 'true'], repo)
git(['config', 'remote.origin.partialclonefilter', 'blob:none'], repo)
git(['fetch', '--depth=1', '--filter=blob:none', 'origin', COMMIT], repo)
assert git(['rev-parse', 'FETCH_HEAD'], repo).decode().strip() == COMMIT
blobs = []
for name in ('SOURCE_PREPARATION_RETENTION01.json', 'source-preparation-bundle01.tar.gz', 'recover_preparation01.py'):
    local = HERE / name
    path = str(local.relative_to(ROOT))
    body = git(['show', COMMIT + ':' + path], repo)
    assert body == local.read_bytes()
    put(out / name, body)
    blobs.append({'path': path, 'sha256': sha(body), 'bytes': len(body)})
retained = json.loads((out / 'SOURCE_PREPARATION_RETENTION01.json').read_bytes())
archive = out / 'source-preparation-bundle01.tar.gz'
assert archive.stat().st_size == retained['archive_bytes'] and sha(archive.read_bytes()) == retained['archive_sha256']
expected = {r['path']: r for r in retained['members']}
assert len(expected) == len(retained['members']) == retained['files'] == 299
owned = out / 'selected'
owned.mkdir(mode=0o700)
seen = set()
with tarfile.open(archive, 'r:gz') as tf:
    for member in tf:
        path = PurePosixPath(member.name)
        assert member.name == str(path) and not path.is_absolute() and '..' not in path.parts
        assert len(path.parts) >= 2 and path.parts[0] == 'selected' and '\\' not in member.name and '\x00' not in member.name
        name = str(PurePosixPath(*path.parts[1:]))
        assert name in expected and name not in seen and member.isfile()
        row = expected[name]
        assert row['kind'] == 'file' and member.size == row['bytes'] <= MAX and member.mode == row['mode']
        destination = owned / name
        assert destination.resolve() == destination
        destination.parent.mkdir(parents=True, exist_ok=True)
        stream = tf.extractfile(member)
        assert stream is not None
        with stream:
            body = stream.read(MAX + 1)
        assert len(body) == row['bytes'] and sha(body) == row['sha256']
        put(destination, body)
        os.chmod(destination, row['mode'])
        seen.add(name)
assert seen == set(expected)
for name, row in expected.items():
    p = owned / name
    s = p.lstat()
    assert stat.S_ISREG(s.st_mode) and s.st_nlink == 1 and s.st_size == row['bytes'] and stat.S_IMODE(s.st_mode) == row['mode']
    assert sha(p.read_bytes()) == row['sha256']
receipt = {'schema_version': 1, 'status': 'fresh-actual-remote-source-preparation-recovered',
    'remote_commit': COMMIT, 'selected_blobs': blobs, 'source_snapshot': retained['source_commit'],
    'files': 299, 'logical_bytes': retained['logical_bytes'], 'archive_sha256': retained['archive_sha256'],
    'actual_numerical_jobs': 0,
    'qualification': 'Actual three remote Git blobs and all299 retained source/preparation/review/checkpoint file bodies, names, modes, lengths and hashes freshly recovered. The original299-main-Git objects, original directory modes, source capsule, installed runtime and empirical stores are excluded. New directory modes only establish an owned extraction container. Independent acceptance and final successor bindings/recovery/release remain required; no speed, scientific or capacity result is inferred.'}
put(HERE / 'REMOTE_PREPARATION_RECOVERY01.json', (json.dumps(receipt, indent=2, sort_keys=True) + '\n').encode())
print(json.dumps({k: receipt[k] for k in ('status', 'remote_commit', 'files', 'logical_bytes', 'actual_numerical_jobs')}, sort_keys=True))
