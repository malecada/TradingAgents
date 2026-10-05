"""Fixed canonical source increment using unchanged reviewed byte primitives.

No launch, research admission, historical outcome copying or network operation.
The recovered original716 bodies supply authenticated byte inheritance only.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import shutil
import sys

HERE = Path(__file__).resolve().parent
FS = HERE.parent
CAP = Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-canonical-native-20261005-01/source')
PARENT = CAP.parent.parent / 'held-score-consumer-canonical-root-launch-20261005-01'
OUT = FS / 'held-consumer-canonical-current-capture01-2026-10-05'
SOURCE = '468d756c16b3825e83a931c082ab4072764a873d'
IDENTITY = 'original-import-canonical-held-success-20261005-01'
HELPERS = FS / 'held-consumer-final-recovery-preparation04-2026-10-03'

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def main():
    assert not OUT.exists() and not (PARENT / 'attempt').exists()
    assert not any((CAP / name / IDENTITY).exists() for name in
                   ('research_runs', 'fixture_outer', 'research_artifacts/onchain-paper-replication-2026-09-24/runs'))
    assert shutil.disk_usage(CAP).free >= 10 * 1024**3
    assert sha((HELPERS / 'recovery04.py').read_bytes()) == 'b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a'
    sys.path.insert(0, str(HELPERS))
    import recovery04 as R
    from bounded_git01 import git
    resource.setrlimit(resource.RLIMIT_FSIZE, (R.FILE, R.FILE))
    assert git(CAP, ['rev-parse', 'HEAD'], cap=128).decode().strip() == SOURCE
    assert git(CAP, ['status', '--short', '--untracked-files=no']) == b''
    base_path = FS / 'held-consumer-post-outcome-root-flat-recovery01-2026-10-03/flat01/capsule-metadata.json'
    base_raw = R.read(base_path.parent, base_path.name)
    assert sha(base_raw) == 'd8b81554205b9eeb5523fbed41ba616ffc79a0b7fb78c6779b2bcee7f4844fdb'
    base = json.loads(base_raw)
    R.validate(base['manifest'])
    assert sha(R.encode(base['manifest'])) == '52d650e256c6e11d9362a215d8af50197cac6be27c951175a5837508570f20d3'
    assert len(base['manifest']['members']) == 1012
    prior = {row['sha256']: row['path'] for row in base['manifest']['members'] if row['kind'] == 'file'}
    assert sum(row['kind'] == 'file' for row in base['manifest']['members']) == 716
    accepted = FS / 'held-consumer-post-outcome-actual-preservation-review01-2026-10-03'
    basis = {}
    for name, pin in [('ACTUAL_RECOVERY_REVIEW03.json', '31640c18b341c4fd7bed39178863e578296b6b241b634f0fe929c9fb658e08b3'),
                      ('ACTUAL_FLAT_RECEIPT03.json', '4018c09c3fc4a27d9cdd88e7cd1d7e38df0b0f0a97f542deecb6433e77d655f4')]:
        raw = R.read(accepted, name)
        assert sha(raw) == pin
        basis[name] = {'path': str(accepted / name), 'sha256': pin}
    scopes = [('Capsule', CAP), ('Parent', PARENT), ('Root', HERE),
              ('gate-review', FS / 'held-consumer-canonical-gate-draft-review01-2026-10-05'),
              ('parent-review', FS / 'held-consumer-canonical-parent-review01-2026-10-05')]
    manifests = {}; joins = {}; bodies = {}
    for label, root in scopes:
        manifest = R.scan(root)
        manifests[label] = manifest
        for row in manifest['members']:
            if row['kind'] != 'file':
                continue
            raw = R.read(root, row['path'])
            assert sha(raw) == row['sha256'] and len(raw) == row['bytes']
            key = label + '/' + row['path']
            if row['sha256'] in prior:
                joins[key] = {'kind': 'inherited-original-body', 'original_path': prior[row['sha256']], 'sha256': row['sha256'], 'bytes': row['bytes']}
            else:
                bodies[row['sha256']] = raw
                joins[key] = {'kind': 'new-body', 'sha256': row['sha256'], 'bytes': row['bytes']}
    assert sum(map(len, bodies.values())) <= 16 * 1024**2
    for label, root in scopes:
        R.same(root, manifests[label])
    assert git(CAP, ['rev-parse', 'HEAD'], cap=128).decode().strip() == SOURCE
    assert shutil.disk_usage(CAP).free >= 10 * 1024**3
    OUT.mkdir(mode=0o700)
    snapshot = OUT / 'snapshot'
    snapshot.mkdir(mode=0o700)
    names = {}
    for index, (pin, raw) in enumerate(sorted(bodies.items())):
        name = 'body-%04d' % index
        with R.new_file(snapshot / name) as fd:
            offset = 0
            while offset < len(raw):
                count = os.write(fd, raw[offset:])
                assert count > 0
                offset += count
            os.fsync(fd)
        names[pin] = name
    for join in joins.values():
        if join['kind'] == 'new-body':
            join['snapshot_name'] = names[join['sha256']]
    composition = {'schema_version': 1, 'kind': 'fixed-canonical-import-byte-increment-v1',
                   'source': SOURCE, 'identity': IDENTITY, 'manifests': manifests, 'body_joins': joins,
                   'original_capsule_metadata': {'path': str(base_path), 'sha256': sha(base_raw)},
                   'inherited_recovery': basis, 'new_unique_bodies': len(bodies),
                   'new_unique_bytes': sum(map(len, bodies.values())),
                   'qualification': 'Complete declared current byte bodies and typed names/modes through accepted original body inheritance plus this increment. No POSIX reconstruction, installed runtime body recovery, whole scientific capacity, continuous writer exclusion or execution authority.'}
    R.put(snapshot / 'COMPOSITION01.json', composition)
    manifest = R.scan(snapshot)
    R.put(OUT / 'snapshot-manifest.json', manifest)
    archive = R.pack(snapshot, manifest, OUT / 'increment.tar.gz')
    for label, root in scopes:
        R.same(root, manifests[label])
    assert shutil.disk_usage(CAP).free >= 10 * 1024**3
    R.put(OUT / 'CAPTURE01.json', {'status': 'COMPLETE_LOCAL_INCREMENT_BYTES_ONLY', 'archive': archive,
          'new_unique_bodies': len(bodies), 'new_unique_bytes': sum(map(len, bodies.values())),
          'scope': [label for label, _ in scopes], 'external_recovery': False, 'execution_admitted': False})
    print(json.dumps({'archive': archive, 'bodies': len(bodies), 'execution_admitted': False}, sort_keys=True))

if __name__ == '__main__':
    main()
