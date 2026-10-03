"""Fresh actual remote recovery of selected final request/source/review bodies.

Complete capsule recovery is separate and immutable. Nothing is executed from
this restored byte copy and no scientific authority is inferred from a receipt.
"""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys

ROOT = Path.cwd()
HERE = Path(__file__).resolve().parent
MAX = 4194304
COMMIT = sys.argv[1]
assert len(COMMIT) == 40 and all(c in '0123456789abcdef' for c in COMMIT)


def call(args, cwd=ROOT):
    result = subprocess.run(['git', *args], cwd=cwd, capture_output=True, timeout=60)
    assert result.returncode == 0 and max(len(result.stdout), len(result.stderr)) <= MAX
    return result.stdout


def digest(body):
    return hashlib.sha256(body).hexdigest()


def put(path, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(body)
        stream.flush()
        os.fsync(stream.fileno())


branch = 'research/onchain-paper-replication-2026-09-24'
assert call(['ls-remote', 'origin', 'refs/heads/' + branch]).decode().split()[0] == COMMIT
out = HERE / 'final-release-recovery02'
out.mkdir(mode=0o700, exist_ok=False)
repo = out / 'repository.git'
call(['init', '--bare', str(repo)])
call(['remote', 'add', 'origin', call(['remote', 'get-url', 'origin']).decode().strip()], repo)
call(['config', 'remote.origin.promisor', 'true'], repo)
call(['config', 'remote.origin.partialclonefilter', 'blob:none'], repo)
call(['fetch', '--depth=1', '--filter=blob:none', 'origin', COMMIT], repo)
assert call(['rev-parse', 'FETCH_HEAD'], repo).decode().strip() == COMMIT
manifest_path = HERE / 'SELECTED_RELEASE_BODIES02.json'
manifest_name = str(manifest_path.relative_to(ROOT))
manifest_body = call(['show', COMMIT + ':' + manifest_name], repo)
assert manifest_body == manifest_path.read_bytes()
put(out / 'selected' / manifest_name, manifest_body)
manifest = json.loads(manifest_body)
assert set(manifest) == {'schema_version', 'status', 'rows', 'qualification'}
assert manifest['schema_version'] == 1 and manifest['status'] == 'selected-final-release-bodies'
rows = manifest['rows']
assert 1 <= len(rows) <= 512
names = [row['path'] for row in rows]
assert names == sorted(set(names))
logical = 0
for row in rows:
    assert set(row) == {'path', 'sha256', 'bytes'}
    name = row['path']
    path = PurePosixPath(name)
    assert str(path) == name and not path.is_absolute() and '..' not in path.parts
    assert '\\' not in name and '\x00' not in name and path.parts[0] == 'research'
    assert type(row['bytes']) is int and 0 <= row['bytes'] <= MAX
    original = ROOT / name
    assert original.resolve() == original and original.is_file() and not original.is_symlink()
    body = call(['show', COMMIT + ':' + name], repo)
    assert len(body) == row['bytes'] and digest(body) == row['sha256'] and body == original.read_bytes()
    put(out / 'selected' / name, body)
    logical += len(body)
    assert logical <= 64 * 1024**2
receipt = {
    'schema_version': 1,
    'status': 'fresh-actual-remote-final-release-bodies-recovered',
    'remote_commit': COMMIT,
    'manifest': {'path': manifest_name, 'sha256': digest(manifest_body), 'bytes': len(manifest_body)},
    'selected_blobs': rows,
    'blobs_including_manifest': len(rows) + 1,
    'logical_bytes_without_manifest': logical,
    'actual_numerical_jobs': 0,
    'qualification': 'Actual selected remote Git objects were freshly fetched into a distinct owned bare repository and every saved body was compared to its original and exact selected hash/length. These are final request, launcher, parent, frozen review and supporting metadata file bodies, not complete directory mode recovery, installed runtime, empirical stores or outcome recovery. Complete current974-member B2 capsule recovery remains independently accepted and immutable; original materialization recovery is separately retained. No request/claim/Owner/native proof or execution is created by recovery; final independent request/parent acceptance and fresh eligibility are separately required.'
}
put(HERE / 'REMOTE_FINAL_RELEASE_RECOVERY02.json', (json.dumps(receipt, sort_keys=True, indent=2) + '\n').encode())
print(json.dumps({k: receipt[k] for k in ('status', 'remote_commit', 'blobs_including_manifest', 'logical_bytes_without_manifest', 'actual_numerical_jobs')}))
