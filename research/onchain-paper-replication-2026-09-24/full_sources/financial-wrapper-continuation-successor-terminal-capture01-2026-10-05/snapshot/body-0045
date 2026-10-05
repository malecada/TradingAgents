"""Capture actual new terminal bytes once, reusing accepted unchanged bodies."""
from pathlib import Path
import hashlib, json, os, resource, shutil, stat, sys, time

root = Path.cwd()
f = root / 'research/onchain-paper-replication-2026-09-24/full_sources'
c = f / 'heartbeat-root-checkpoint10-2026-10-04'
parent = Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-continue100-resource-successor-root-launch-20261005-01')
cap = Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source')
identity = 'financial-wrapper-classification-eager-continue100-resource-successor-20261005-01'
review = f / 'financial-wrapper-continuation-successor-review01-2026-10-05'
outcome = f / 'financial-wrapper-continuation-successor-outcome-review01-2026-10-05'
out = f / 'financial-wrapper-continuation-successor-terminal-capture01-2026-10-05'
assert hashlib.sha256((parent / 'recovery04.py').read_bytes()).hexdigest() == 'b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a'
sys.path.insert(0, str(parent))
import recovery04 as R
from bounded_git01 import git

resource.setrlimit(resource.RLIMIT_FSIZE, (R.FILE, R.FILE))
assert not out.exists() and shutil.disk_usage(cap).free >= 10 * 1024**3
assert git(cap, ['rev-parse', 'HEAD'], cap=128).decode().strip() == 'a5bcc943167ad035b45e12ddf9864d46e685b124'
assert not os.path.lexists(cap / 'research_runs' / identity)
assert R.digest(R.read(outcome, 'RAW_EVIDENCE01.json')) == '5b13b8d4528e1dd05e9468a1ace6bb07ca2ee2cd144a846aa46a7e93cdbf2985'
assert R.digest(R.read(outcome, 'OUTCOME_CHECK01.json')) == 'b6dd3386136c761ada0baf6e8ad0ec2722ad9e7b2a92d862291419a235ede1c8'
basis = review / 'FULL_CURRENT_RECOVERY_PROOF01.json'
assert R.digest(R.read(basis.parent, basis.name)) == 'bdf0f39710054d34f2274eec35a192dc13200ff146b4a79d3f4822235efba7df'
old_raw = R.read(f / 'financial-wrapper-continuation-successor-current-capture01-2026-10-05/snapshot', 'COMPOSITION01.json')
assert R.digest(old_raw) == '7cfa0ac13cb3c4e76f087b155ae4ce0d5f58097091f1165fac9011003e66e779'
old = json.loads(old_raw)
assert old['source'] == 'a5bcc943167ad035b45e12ddf9864d46e685b124'

def metadata(base, omit_git=False):
    rows = []
    deadline = time.monotonic() + 10
    for current, dirs, files in os.walk(base):
        assert time.monotonic() < deadline and len(rows) < 4096
        if Path(current) == base and omit_git:
            dirs[:] = [n for n in dirs if n != '.git']
        for name in sorted(dirs + files):
            p = Path(current) / name
            s = p.lstat()
            assert p.resolve() == p and s.st_nlink >= 1
            assert stat.S_ISDIR(s.st_mode) or stat.S_ISREG(s.st_mode)
            row = {'path': p.relative_to(base).as_posix(), 'kind': 'directory' if stat.S_ISDIR(s.st_mode) else 'file', 'mode': stat.S_IMODE(s.st_mode)}
            if row['kind'] == 'file':
                assert s.st_nlink == 1 and s.st_size <= R.FILE
                row['bytes'] = s.st_size
            rows.append(row)
    return sorted(rows, key=lambda x: x['path'])

known = {x['path']: x for x in old['capsule']['members']}
before = metadata(cap, True)
actual = {x['path']: x for x in before}
assert stat.S_IMODE(cap.lstat().st_mode) == old['capsule']['root_mode']
assert set(known) <= set(actual)
for name, row in known.items():
    assert actual[name] == {k: v for k, v in row.items() if k != 'sha256'}
new = set(actual) - set(known)
prefix = 'research_artifacts/onchain-paper-replication-2026-09-24/runs/' + identity
assert new and all(n == prefix or n.startswith(prefix + '/') for n in new)
git_before = metadata(cap / '.git')
assert git_before == [{k: v for k, v in row.items() if k != 'sha256'} for row in old['scopes']['Git']['manifest']['members']]
saved = {}
current = []
for row in before:
    name = row['path']
    if row['kind'] == 'file' and name in new:
        raw = R.read(cap, name)
        assert len(raw) == row['bytes']
        saved['CAP/' + name] = raw
        current.append(dict(row, sha256=R.digest(raw)))
    else:
        current.append(known.get(name, row))

scopes = {}
for label, base in [('Parent', parent), ('closed-preparation-review', review), ('outcome-phase', outcome)]:
    manifest = R.scan(base)
    scopes[label] = {'root': str(base), 'manifest': manifest}
    for row in manifest['members']:
        if row['kind'] == 'file':
            saved[label + '/' + row['path']] = R.read(base, row['path'])
for name in ('SUCCESSOR_NUMERICAL_ROOT01.stdout', 'SUCCESSOR_NUMERICAL_ROOT01.stderr', 'SUCCESSOR_NUMERICAL_ROOT_EXIT01.json', 'SUCCESSOR_LAUNCH_ELIGIBILITY01.json', 'SUCCESSOR_FULL_PREFLIGHT01.json', 'SUCCESSOR_FULL_PREFLIGHT01.stdout', 'SUCCESSOR_FULL_PREFLIGHT01.stderr', 'SUCCESSOR_TERMINAL_CAPTURE01.py'):
    saved['Root/' + name] = R.read(c, name)
assert sum(map(len, saved.values())) < 8 * 1024**2
out.mkdir(mode=0o700)
snapshot = out / 'snapshot'
snapshot.mkdir(mode=0o700)
mapped = {}
for index, (name, raw) in enumerate(sorted(saved.items())):
    leaf = 'body-%04d' % index
    with R.new_file(snapshot / leaf) as fd:
        with os.fdopen(os.dup(fd), 'wb') as w:
            w.write(raw)
    mapped[name] = {'flat': leaf, 'bytes': len(raw), 'sha256': R.digest(raw)}
composition = {'schema_version': 1, 'kind': 'actual-terminal-successor-byte-increment', 'identity': identity, 'source': old['source'], 'basis': {'path': str(basis), 'sha256': R.digest(R.read(basis.parent, basis.name))}, 'capsule': {'schema_version': old['capsule']['schema_version'], 'root_mode': old['capsule']['root_mode'], 'members': current}, 'Git': old['scopes']['Git'], 'Git_logical_objects': old['Git_logical_objects'], 'scopes': scopes, 'materialized': mapped, 'accepted_unchanged_CAP_and_Git_bodies_reused': True, 'immutable_current_writer_exclusion': False, 'runtime_package_bodies_recovered': False, 'POSIX_reconstruction': False, 'namespace_reuse_authority': False, 'numerical_updates': 0, 'lifecycle_claim': False, 'external_recovery': None, 'qualification': 'Actual new failed-startup bytes and full current Parent, closed preparation review and outcome phase; accepted unchanged CAP/Git byte basis reused after complete metadata/source joins. Unknown original Parent/guard exits remain null; this is not immutable writer exclusion, POSIX/runtime-body recovery, numerical completion or namespace reuse.'}
R.put(snapshot / 'COMPOSITION01.json', composition)
manifest = R.scan(snapshot)
R.put(out / 'archive-manifest.json', manifest)
archive = R.pack(snapshot, manifest, out / 'increment.tar.gz')
for scope in scopes.values():
    R.same(Path(scope['root']), scope['manifest'])
assert before == metadata(cap, True) and git_before == metadata(cap / '.git')
assert not os.path.lexists(cap / 'research_runs' / identity)
R.same(snapshot, manifest)
R.put(out / 'CAPTURE01.json', {'schema_version': 1, 'identity': identity, 'source': old['source'], 'archive': archive, 'new_original_bodies': len(mapped), 'new_original_bytes': sum(x['bytes'] for x in mapped.values()), 'new_CAP_regular': sum(actual[n]['kind'] == 'file' for n in new), 'CAP_regular': sum(x['kind'] == 'file' for x in current), 'CAP_typed': len(current), 'Git_logical_objects': old['Git_logical_objects'], 'Parent_regular': sum(x['kind'] == 'file' for x in scopes['Parent']['manifest']['members']), 'basis': composition['basis'], 'external_recovery': False, 'scope': composition['qualification']})
print(json.dumps({'status': 'actual-terminal-byte-increment-captured-once', 'archive': archive, 'new_original_bodies': len(mapped), 'new_original_bytes': sum(x['bytes'] for x in mapped.values()), 'CAP_regular': sum(x['kind'] == 'file' for x in current), 'CAP_typed': len(current)}))
