"""Finite remote evidence recovery; never extracts or executes retained content."""
from pathlib import Path
import hashlib
import json
import resource
import shutil
import subprocess
import tarfile
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
OUT = HERE / 'red-remote-recovery01'
BRANCH = 'research/onchain-paper-replication-2026-09-24'
NAMES = ('red-retained-tree01.tar.gz', 'red-retained-tree01.json',
         'red-execution-result01.json', 'REVIEW_RED_EXECUTION01.md')

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def invoke(args, cwd):
    result = subprocess.run(args, cwd=cwd, capture_output=True, timeout=60)
    if result.returncode:
        raise RuntimeError('bounded Git recovery command failed')
    if len(result.stdout) > 4 * 1024**2 or len(result.stderr) > 4 * 1024**2:
        raise RuntimeError('Git recovery output bound exceeded')
    return result.stdout

def main():
    resource.setrlimit(resource.RLIMIT_FSIZE, (4 * 1024**2, 4 * 1024**2))
    assert shutil.disk_usage(ROOT).free >= 10 * 1024**3
    source = invoke(['git', 'rev-parse', 'HEAD'], ROOT).decode().strip()
    remote = invoke(['git', 'ls-remote', 'origin', 'refs/heads/' + BRANCH], ROOT)
    assert remote.decode().split()[0] == source
    url = invoke(['git', 'remote', 'get-url', 'origin'], ROOT).decode().strip()
    OUT.mkdir(mode=0o700)
    repo = OUT / 'repository.git'
    invoke(['git', 'init', '--bare', str(repo)], ROOT)
    invoke(['git', 'remote', 'add', 'origin', url], repo)
    invoke(['git', 'config', 'remote.origin.promisor', 'true'], repo)
    invoke(['git', 'config', 'remote.origin.partialclonefilter', 'blob:none'], repo)
    invoke(['git', 'fetch', '--depth=1', '--filter=blob:none', 'origin', source], repo)
    assert invoke(['git', 'rev-parse', 'FETCH_HEAD'], repo).decode().strip() == source
    refs = {}
    for name in NAMES:
        path = str((HERE / name).relative_to(ROOT))
        raw = invoke(['git', 'show', source + ':' + path], repo)
        assert len(raw) <= 1024**2
        assert digest(raw) == digest((HERE / name).read_bytes())
        with (OUT / name).open('xb') as stream:
            stream.write(raw)
        refs[name] = {'bytes': len(raw), 'sha256': digest(raw)}
    manifest = json.loads((OUT / 'red-retained-tree01.json').read_bytes())
    rows = {}
    for row in manifest['members']:
        suffix = '' if row['path'] == '.' else '/' + row['path']
        name = 'retained/' + row['role'] + suffix
        assert name not in rows
        rows[name] = row
    seen = set()
    files = directories = total = 0
    with tarfile.open(OUT / 'red-retained-tree01.tar.gz', 'r:gz') as archive:
        for member in archive:
            assert member.name in rows and member.name not in seen
            seen.add(member.name)
            row = rows[member.name]
            assert member.mode == row['mode']
            if row['type'] == 'directory':
                assert member.isdir()
                directories += 1
            else:
                assert member.isfile() and member.size == row['bytes']
                stream = archive.extractfile(member)
                assert stream is not None
                with stream:
                    raw = stream.read(member.size + 1)
                assert len(raw) == row['bytes'] and digest(raw) == row['sha256']
                files += 1
                total += len(raw)
    assert seen == set(rows) and files == manifest['files'] == 10
    assert directories == manifest['directories_including_each_root'] == 5
    assert len(seen) == manifest['entries_including_each_root'] == 15
    assert total == manifest['logical_bytes'] == 58094
    assert manifest['allocated_bytes_including_directories'] == 81920
    result = {
        'schema_version': 1, 'status': 'fresh_remote_recovery_verified',
        'commit': source, 'verified_utc': datetime.now(timezone.utc).isoformat(),
        'retrieved_refs': refs, 'files': files,
        'directories_including_each_root': directories,
        'archive_members': len(seen), 'logical_body_bytes_verified': total,
        'qualification': 'Four actual remote blobs retrieved into a fresh bare partial Git repository. All10 file bodies/modes and5 directory modes verified by streaming15 archive members without extraction or execution. The accepted RED review is separately recovered among four selected blobs. Other outer evidence/source pins are hashreferenced, not separately retrieved here. Allocation describes original host, not recovery media.'}
    with (HERE / 'RED_REMOTE_RECOVERY01.json').open('x') as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
        stream.write('\n')
    print(json.dumps({'commit': source, 'members': len(seen), 'files': files,
                      'directories': directories, 'status': result['status']}))

if __name__ == '__main__':
    main()
