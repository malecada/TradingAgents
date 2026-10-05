"""Fixed canonical increment byte restoration; accepted R4 mechanics unchanged."""
from pathlib import Path
import hashlib
import json
import resource
import shutil
import sys
import types

ROOT = Path.cwd()
F = ROOT / 'research/onchain-paper-replication-2026-09-24/full_sources'
REMOTE = F / 'held-consumer-canonical-current-remote01-2026-10-05'
PREFIX = 'research/onchain-paper-replication-2026-09-24/full_sources/held-consumer-canonical-current-capture01-2026-10-05'
OUT = F / 'held-consumer-canonical-current-flat01-2026-10-05'
HELPERS = F / 'held-consumer-final-recovery-preparation04-2026-10-03'


def main():
    for name, pin in [('owned_io.py', '09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb'),
                      ('bounded_git01.py', 'db4a65a450bf9930abac04ab794539ebd952b07826d7314b4aea4e989dd9240f'),
                      ('recovery04.py', 'b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a')]:
        assert name[:-3] not in sys.modules
        raw = (HELPERS / name).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == pin
        module = types.ModuleType(name[:-3]); module.__file__ = str(HELPERS / name)
        sys.modules[name[:-3]] = module
        exec(compile(raw, module.__file__, 'exec'), module.__dict__)
    R = sys.modules['recovery04']
    assert R.git is sys.modules['bounded_git01'].git and R._cleanup is sys.modules['owned_io']._cleanup
    resource.setrlimit(resource.RLIMIT_FSIZE, (R.FILE, R.FILE))
    assert not OUT.exists() and shutil.disk_usage(F).free >= 10 * 1024**3
    receipt = json.loads(R.read(REMOTE, 'REMOTE_RECOVERY01.json'))
    assert receipt['remote_commit'] == 'f89c6516b03d205a682a5faac54fcc093f5a8fc6'
    assert receipt['selection_sha256'] == '292462a40c1d482b37dc0114cf60302b2608bb01980cdd909ee0b185737ac652'
    assert receipt['selected_count'] == 8 and receipt['selected_logical_bytes'] == 807426
    assert len(receipt['operations']) == receipt['expected_operations'] == 34
    assert all(r['exit'] == r['actual_reaped_exit'] == 0 and r['cleanup_failures'] == [] and r['actual_child_limits'] == {'pid': r['pid'], 'fsize': [R.FILE, R.FILE]} for r in receipt['operations'])
    actual_root = json.loads(R.read(REMOTE, 'ACTUAL_ROOT_EXIT01.json'))
    assert actual_root['actual_root_exit_code'] == 0
    refs = {r['path']: r for r in receipt['selected_blobs']}
    recovered = REMOTE / 'selected' / PREFIX
    for n in ('increment.tar.gz', 'snapshot-manifest.json', 'CAPTURE01.json'):
        raw = R.read(recovered, n); ref = refs[PREFIX + '/' + n]
        assert len(raw) == ref['bytes'] and R.digest(raw) == ref['sha256']
    record = json.loads(R.read(recovered, 'CAPTURE01.json'))
    manifest = json.loads(R.read(recovered, 'snapshot-manifest.json'))
    assert record['archive']['sha256'] == '5655787612895dd1fbdf6fec7f52eca2df88adb5da6ab8af1123e36b2dfcaf71'
    assert R.digest(R.read(recovered, 'snapshot-manifest.json')) == '1bf39e5fa3b15a3b77017023b0ccbd21d89d5610f10e9b9a6aa9f4b5c7da620a'
    assert record['new_unique_bodies'] == 134 and record['new_unique_bytes'] == 1432931 and len(manifest['members']) == 135
    assert record['scope'] == ['Capsule', 'Parent', 'Root', 'gate-review', 'parent-review']
    assert record['external_recovery'] is False and record['execution_admitted'] is False
    OUT.mkdir(mode=0o700); (OUT / 'flat').mkdir(mode=0o700)
    primitive = R.restore(recovered / 'increment.tar.gz', record['archive'], manifest, OUT / 'flat')
    assert primitive['regular_bodies'] == 135
    R.put(OUT / 'RECOVERY01.json', {'schema_version': 1, 'status': 'ACTUAL_CANONICAL_INCREMENT_FLAT_BYTE_RECOVERY', 'receiver_receipt_sha256': R.digest(R.read(REMOTE, 'REMOTE_RECOVERY01.json')), 'actual_receiver_root_exit_sha256': R.digest(R.read(REMOTE, 'ACTUAL_ROOT_EXIT01.json')), 'capture_sha256': R.digest(R.read(recovered, 'CAPTURE01.json')), 'archive_sha256': record['archive']['sha256'], 'manifest_sha256': R.digest(R.read(recovered, 'snapshot-manifest.json')), 'primitive': primitive, 'new_unique_bodies': 134, 'new_unique_bytes': 1432931, 'paper_financial_fits': 0, 'numerical_authority': False, 'runtime_body_recovery': False, 'POSIX_reconstruction': False, 'immutable_writer_exclusion': False, 'qualification': 'Actual fresh remote-selected increment restored by unchanged R4. Complete declared current CAP/Git/Parent/Root/review byte scope must be independently composed through accepted original716 body inheritance and recovered134 new bodies. Original nulls/failures/spent identities unchanged.'})
    assert shutil.disk_usage(OUT).free >= 10 * 1024**3
    print(json.dumps({'status': 'ACTUAL_CANONICAL_INCREMENT_BYTE_RECOVERED', 'regular_bodies': 135, 'recovery_sha256': R.digest(R.read(OUT, 'RECOVERY01.json'))}))


if __name__ == '__main__':
    main()
