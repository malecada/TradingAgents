"""Recover the actual complete failed comparison collection from real remote Git.
No numerical decoding, admission, source changes or identity replay.
"""
import hashlib, json, os, stat, subprocess, sys, tarfile
from pathlib import Path, PurePosixPath

ROOT = Path.cwd()
HERE = Path(__file__).resolve().parent
MAX = 4194304
COMMIT = sys.argv[1]
assert len(COMMIT) == 40 and all(c in '0123456789abcdef' for c in COMMIT)


def call(args, cwd=ROOT):
    r = subprocess.run(['git', *args], cwd=cwd, capture_output=True, timeout=60)
    assert r.returncode == 0 and max(len(r.stdout), len(r.stderr)) <= MAX
    return r.stdout


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
out = HERE / 'outcome-recovery02'
out.mkdir(mode=0o700, exist_ok=False)
repo = out / 'repository.git'
call(['init', '--bare', str(repo)])
call(['remote', 'add', 'origin', call(['remote', 'get-url', 'origin']).decode().strip()], repo)
call(['config', 'remote.origin.promisor', 'true'], repo)
call(['config', 'remote.origin.partialclonefilter', 'blob:none'], repo)
call(['fetch', '--depth=1', '--filter=blob:none', 'origin', COMMIT], repo)
assert call(['rev-parse', 'FETCH_HEAD'], repo).decode().strip() == COMMIT
names = [HERE / n for n in ('OUTCOME_RETENTION01.json', 'comparison-outcome01.tar.gz',
         'COLLECTION_REQUEST01.json', 'COLLECTION_CHILD01.json', 'COLLECTION_WAIT01.json',
         'collector.stdout', 'collector.stderr', 'ARCHIVE_IMPORT_FAILURE01.json',
         'recover_comparison_outcome04.py', 'recover_comparison_outcome03.py', 'recover_comparison_outcome02.py', 'recover_comparison_outcome01.py',
         'RECOVERY_SOURCE_ADAPTATION04.json', 'RECOVERY_SOURCE_ADAPTATION03.json', 'RECOVERY_FAILURE01.json', 'RECOVERY_TOOL_FAILURE01.txt',
         'RECOVERY_SOURCE_ADAPTATION01.json', 'COLLECTION_ROOT_MODE_BINDING01.json')]
fs = HERE.parent
for dirname, manifest_name in (
    ('neural-cold-feature-handoff-comparison-closure-review01-2026-10-03', 'MANIFEST01.json'),
    ('neural-cold-feature-handoff-outcome-retention-preparation02-2026-10-03', 'MANIFEST02.json'),
    ('neural-cold-feature-handoff-outcome-retention-review02-2026-10-03', 'MANIFEST02.json'),
    ('neural-cold-feature-handoff-comparison-outcome-local-review01-2026-10-03', 'MANIFEST01.json'),
    ('neural-cold-feature-handoff-comparison-outcome-recovery-source-review02-2026-10-03', 'MANIFEST02.json'),
    ('neural-cold-feature-handoff-comparison-outcome-recovery-source-review03-2026-10-03', 'MANIFEST01.json')):
    directory = fs / dirname
    manifest = directory / manifest_name
    names.append(manifest)
    for row in json.loads(manifest.read_bytes())['files']:
        path = PurePosixPath(row['path'])
        assert str(path) == row['path'] and not path.is_absolute() and '..' not in path.parts
        original = directory / row['path']
        assert original.resolve() == original and len(original.read_bytes()) == row['bytes']
        assert digest(original.read_bytes()) == row['sha256']
        names.append(original)
assert len(names) == len(set(names))
selected = []
for original in names:
    name = str(original.relative_to(ROOT))
    body = call(['show', COMMIT + ':' + name], repo)
    assert body == original.read_bytes() and len(body) <= MAX
    put(out / 'selected' / name, body)
    selected.append({'path': name, 'sha256': digest(body), 'bytes': len(body)})
retained = json.loads((out / 'selected' / str((HERE / 'OUTCOME_RETENTION01.json').relative_to(ROOT))).read_bytes())
archive = out / 'selected' / str((HERE / 'comparison-outcome01.tar.gz').relative_to(ROOT))
assert archive.stat().st_size == retained['archive_bytes'] and digest(archive.read_bytes()) == retained['archive_sha256']
# The actual directory census has no byte/hash fields. Preserve its typed schema.
for row in retained['members']:
    assert type(row) is dict and row.get('kind') in ('directory', 'file')
    fields = {'kind', 'mode', 'path'}
    if row['kind'] == 'file':
        fields |= {'bytes', 'sha256'}
        assert type(row['bytes']) is int and 0 <= row['bytes'] <= MAX
        assert type(row['sha256']) is str and len(row['sha256']) == 64
        assert all(c in '0123456789abcdef' for c in row['sha256'])
    assert set(row) == fields and type(row['mode']) is int and 0 <= row['mode'] <= 0o7777
    assert type(row['path']) is str
    relative = PurePosixPath(row['path'])
    assert str(relative) == row['path'] and row['path'] != '.' and not relative.is_absolute()
    assert '..' not in relative.parts and '\\' not in row['path'] and '\x00' not in row['path']
expected = {row['path']: row for row in retained['members']}
assert len(expected) == len(retained['members']) == retained['member_count'] == 2313
root_binding = json.loads((out / 'selected' / str((HERE / 'COLLECTION_ROOT_MODE_BINDING01.json').relative_to(ROOT))).read_bytes())
assert root_binding['source'] == retained['source'] and root_binding['collection_sha256'] == retained['collection_sha256']
assert root_binding['archive_sha256'] == retained['archive_sha256'] and root_binding['archive_member_count_excludes_root'] == 2313
assert root_binding['whole_tree_members_including_root'] == 2314 and '.' not in expected
original_root_info = (HERE / 'collection01').lstat()
assert (original_root_info.st_dev, original_root_info.st_ino) == (root_binding['device'], root_binding['inode'])
assert stat.S_IMODE(original_root_info.st_mode) == root_binding['mode'] and type(root_binding['mode']) is int
owned = out / 'collection'
owned.mkdir(mode=0o700)
os.chmod(owned, root_binding['mode'])
assert stat.S_IMODE(owned.lstat().st_mode) == root_binding['mode']
seen = set()
files = directories = logical = 0
with tarfile.open(archive, 'r:gz') as tar:
    for member in tar:
        path = PurePosixPath(member.name)
        assert member.name == str(path) and not path.is_absolute() and '..' not in path.parts
        assert '\\' not in member.name and '\x00' not in member.name and path.parts[0] == 'collection'
        name = '.' if len(path.parts) == 1 else str(PurePosixPath(*path.parts[1:]))
        assert name in expected and name not in seen
        row = expected[name]
        assert member.mode == row['mode']
        dest = owned if name == '.' else owned / name
        assert dest.resolve() == dest and (dest == owned or dest.parent.is_dir())
        if row['kind'] == 'directory':
            assert member.isdir() and member.size == 0
            if dest != owned:
                dest.mkdir(mode=member.mode)
            os.chmod(dest, member.mode)
            directories += 1
        else:
            assert row['kind'] == 'file' and member.isfile() and member.size == row['bytes'] <= MAX
            stream = tar.extractfile(member)
            assert stream is not None
            with stream:
                body = stream.read(MAX + 1)
            assert len(body) == row['bytes'] and digest(body) == row['sha256']
            put(dest, body)
            os.chmod(dest, member.mode)
            files += 1
            logical += len(body)
        seen.add(name)
assert seen == set(expected) and files == retained['files'] == 1764
assert directories == retained['directories'] == 549 and logical == retained['logical_bytes'] == 9963221
actual = set()
for path in owned.rglob('*'):
    name = '.' if path == owned else str(path.relative_to(owned))
    actual.add(name)
    row = expected[name]
    info = path.lstat()
    assert stat.S_IMODE(info.st_mode) == row['mode']
    if row['kind'] == 'directory':
        assert stat.S_ISDIR(info.st_mode)
    else:
        assert stat.S_ISREG(info.st_mode) and info.st_nlink == 1
        assert info.st_size == row['bytes'] and digest(path.read_bytes()) == row['sha256']
assert actual == seen
capsule = owned / 'data/capsule'
assert call(['rev-parse', 'HEAD'], capsule).decode().strip() == retained['source'] == '361339125a3f1cd57e7ba8611f5a994ae649fa0b'
assert not (capsule / '.git/objects/info/alternates').exists()
source = fs / 'neural-cold-feature-handoff-outcome-retention-preparation02-2026-10-03/collector01.py'
assert digest(source.read_bytes()) == 'd3ab84766f8a0e42d1247f5620b9a331fc1975d38e6447ee192bb2b1324d0b69'
result = subprocess.run([sys.executable, '-B', str(source), 'verify-recovery', '--original', str(HERE / 'collection01'),
                        '--recovered', str(owned), '--collection-sha256', retained['collection_sha256']],
                       cwd=ROOT, capture_output=True, timeout=180)
put(out / 'verify-recovery.stdout', result.stdout)
put(out / 'verify-recovery.stderr', result.stderr)
assert result.returncode == 0 and len(result.stdout) <= MAX and len(result.stderr) <= MAX
verified = json.loads(result.stdout)
assert verified['status'] == 'complete-actual-recovered-byte-equality'
assert verified['scientific_dispositions'] == retained['dispositions']
receipt = {'schema_version': 1, 'status': 'fresh-actual-remote-complete-failed-comparison-outcome-recovered',
           'remote_commit': COMMIT, 'selected_blobs': selected, 'members': 2313, 'files': files,
           'directories': directories, 'logical_bytes': logical, 'archive_sha256': retained['archive_sha256'],
           'whole_tree_members_including_root': 2314, 'root_mode_binding': root_binding,
           'collection_sha256': retained['collection_sha256'], 'verification': verified,
           'actual_numerical_jobs_replayed': 0,
           'qualification': 'Actual selected remote Git bodies and the complete original closed outcome collection were freshly recovered. All member names/modes/hashes/lengths, full collection metadata and restored genuine B2 Git/source/input/43-emitted-and44-registered-input/native/ResearchRun/outer/supervisor/both-wrapper/both-parent/partial-and-failure records matched. Restoration is byte provenance only and does not rebase original authority or authorize identity replay. Installed runtime and financial empirical stores are excluded; original completed materialization SCIENCE_PENDING and failed comparison dispositions remain unchanged.'}
put(HERE / 'REMOTE_OUTCOME_RECOVERY02.json', (json.dumps(receipt, sort_keys=True, indent=2) + '\n').encode())
print(json.dumps({k: receipt[k] for k in ('status', 'remote_commit', 'members', 'files', 'directories', 'logical_bytes', 'actual_numerical_jobs_replayed')}))
