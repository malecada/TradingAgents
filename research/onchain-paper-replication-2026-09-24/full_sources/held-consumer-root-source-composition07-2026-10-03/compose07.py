"""Root-only local source composition; no registration or numerical execution."""
from pathlib import Path
import argparse, hashlib, json, os, subprocess
from datetime import datetime, timezone

REPO = Path('/home/malecada/master_thesis/TradingAgents-audit-fixes')
BASE = REPO / 'research/onchain-paper-replication-2026-09-24/full_sources'
OLD = Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-native-20261003-05/source')
NEW = Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-native-20261003-07/source')
PARENT = '6c36d073598c9949c463cf56619bb9d3b7b59329'
ANCHOR = '0cfc2c03200880534b7c91c2f16ac659a265a35b'
PREP = BASE / 'held-consumer-runtime-interpreter-reader-preparation01-2026-10-03'
OUT = Path(__file__).resolve().parent
TARGET = 'fixture_tools/capsule_builder01.py'
EXPECTED = 'b877557d1b11d1d1dbc596c703e21fc6f60a96c635a9645c87df08bc87920666'

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def read(path):
    path = Path(path)
    assert path.resolve() == path and path.is_file() and path.stat().st_nlink == 1
    assert path.stat().st_size <= 4 * 1024**2
    return path.read_bytes()

def put(name, value):
    raw = (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()
    with (OUT / name).open('xb') as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--review-manifest', required=True)
    parser.add_argument('--review-manifest-sha256', required=True)
    args = parser.parse_args()
    review = Path(args.review_manifest)
    assert sha(read(review)) == args.review_manifest_sha256
    observations = []

    def git(root, *argv):
        result = subprocess.run(['git', '-c', 'protocol.allow=never', *(['-c', 'protocol.file.allow=always'] if argv[0] == 'clone' else []), *argv], cwd=root,
            env={**os.environ, 'GIT_NO_LAZY_FETCH': '1', 'GIT_NO_REPLACE_OBJECTS': '1'},
            capture_output=True, timeout=30)
        observations.append({'cwd': str(root), 'args': list(argv), 'exit_code': result.returncode,
            'stdout': None if argv[0] == 'cat-file' else result.stdout.decode(),
            'stdout_bytes': len(result.stdout), 'stdout_sha256': sha(result.stdout),
            'stderr': result.stderr.decode()})
        assert result.returncode == 0, observations[-1]
        return result.stdout

    assert git(OLD, 'rev-parse', 'HEAD').decode().strip() == PARENT
    old = json.loads(read(BASE / 'held-consumer-root-source-composition05-2026-10-03/SOURCE_COMPOSITION05.json'))
    assert len(old['source_entries']) == 199 and old['package_count'] == 148
    candidate = read(PREP / 'capsule_builder01.py')
    assert sha(candidate) == EXPECTED
    assert not NEW.exists()
    NEW.parent.mkdir(exist_ok=False)
    git(REPO, 'clone', '--no-checkout', '--no-hardlinks', str(OLD), str(NEW))
    git(NEW, 'checkout', '--detach', PARENT)
    git(NEW, 'config', 'user.name', 'Research source preparation')
    git(NEW, 'config', 'user.email', 'research-source@localhost')
    before = {x['target']: read(OLD / x['target']) for x in old['source_entries']}
    tracked = git(NEW, 'ls-files').decode().splitlines()
    assert len(tracked) == 204
    copied = []
    for row in old['copied_opaque_and_closed_history_files']:
        raw = read(OLD / row['path'])
        assert len(raw) == row['bytes'] and sha(raw) == row['sha256']
        path = NEW / row['path']
        assert not path.exists() and '..' not in Path(row['path']).parts
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as handle:
            handle.write(raw)
        os.chmod(path, row['mode'])
        copied.append(dict(row, original_path=str(OLD / row['path'])))
    assert len(copied) == 42
    (NEW / TARGET).write_bytes(candidate)
    git(NEW, 'add', '--', TARGET)
    git(NEW, 'commit', '--quiet', '-m', 'Verify interpreter with bounded runtime-only streaming reader')
    commit = git(NEW, 'rev-parse', 'HEAD').decode().strip()
    assert git(NEW, 'show', '-s', '--format=%P', commit).decode().strip() == PARENT
    assert git(NEW, 'diff-tree', '--no-commit-id', '--name-only', '-r', commit).decode().splitlines() == [TARGET]
    entries = []
    for row in old['source_entries']:
        name = row['target']
        raw = read(NEW / name)
        assert raw == (candidate if name == TARGET else before[name])
        assert git(NEW, 'cat-file', 'blob', commit + ':' + name) == raw
        if row['package_source']:
            assert git(NEW, 'cat-file', 'blob', ANCHOR + ':' + name) == raw
        entries.append(dict(row, sha256=sha(raw), bytes=len(raw), actual_git_commit=commit,
            origin=str(PREP / 'capsule_builder01.py') if name == TARGET else row['origin'],
            change='reviewed-runtime-only-stream-reader' if name == TARGET else row['change']))
    for name in tracked:
        if name != TARGET:
            assert read(NEW / name) == read(OLD / name)
    for row in copied:
        assert sha(read(NEW / row['path'])) == row['sha256']
        assert (NEW / row['path']).stat().st_mode & 0o777 == row['mode']
    history = json.loads(read(BASE / 'held-consumer-historical-admission-closure-investigation01-2026-10-03/COPY_PLAN01.json'))
    original = json.loads(read(BASE / 'held-consumer-original-git-runtime-role-investigation01-2026-10-03/ORIGINAL_GIT_COPY_PLAN01.json'))
    assert len(history['objects']) == 222 and len(history['logical_committed_lookups']) == 638
    assert len(original['objects']) == 34 and len(original['source_paths']) == 26
    for row in history['objects'] + original['objects']:
        raw = git(NEW, 'cat-file', row['type'], row['object'])
        assert len(raw) == row['bytes'] and sha(raw) == row['sha256']
    for row in history['logical_committed_lookups']:
        raw = git(NEW, 'cat-file', 'blob', row['commit'] + ':' + row['path'])
        assert len(raw) == row['bytes'] and sha(raw) == row['sha256']
    for row in original['source_paths']:
        raw = git(NEW, 'cat-file', 'blob', original['source'] + ':' + row['path'])
        assert len(raw) == row['bytes'] and sha(raw) == row['sha256']
    result = dict(old, observed_utc=datetime.now(timezone.utc).isoformat(), source_root=str(NEW),
        actual_source_commit=commit, authentic_parent_source=PARENT, source_entries=entries,
        logical_source_bytes=sum(x['bytes'] for x in entries),
        copied_opaque_and_closed_history_files=copied, actual_git_command_observations=observations,
        accepted_runtime_reader_review_manifest_sha256=args.review_manifest_sha256,
        qualification='Actual single external runtime-reader helper change; source199/package148/tracked204 and 42 opaque/runtime/closed-history files preserved. Registration, allowance adoption, current native proof and complete external writable recovery remain absent.')
    put('SOURCE_COMPOSITION07.json', result)
    members = []
    for path in (OUT / 'compose07.py', OUT / 'SOURCE_COMPOSITION07.json'):
        raw = read(path)
        members.append({'path': path.name, 'bytes': len(raw), 'sha256': sha(raw)})
    put('MANIFEST07.json', {'schema_version': 1, 'files': members})
    print(json.dumps({'source': commit, 'parent': PARENT, 'package_anchor': ANCHOR,
        'source_count': 199, 'package_count': 148, 'tracked_count': 204,
        'copied_preserved_files': 42, 'claim_created': False, 'execution_admitted': False}))

if __name__ == '__main__':
    main()
