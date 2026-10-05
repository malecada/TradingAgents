"""One fresh outcome-increment byte restoration; accepted R4 unchanged."""
from pathlib import Path
import hashlib
import json
import resource
import shutil
import sys

ROOT = Path.cwd()
F = ROOT / 'research/onchain-paper-replication-2026-09-24/full_sources'
P = Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-predict-serialized-storage-root-launch-20261005-01')
REMOTE = F / 'financial-wrapper-serialized-prediction-outcome-remote01-2026-10-05'
PREFIX = 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-prediction-outcome-capture01-2026-10-05'
OUT = F / 'financial-wrapper-serialized-prediction-outcome-flat01-2026-10-05'


def main():
    assert hashlib.sha256((P / 'recovery04.py').read_bytes()).hexdigest() == 'b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a'
    sys.path.insert(0, str(P))
    import recovery04 as R
    resource.setrlimit(resource.RLIMIT_FSIZE, (R.FILE, R.FILE))
    assert not OUT.exists() and shutil.disk_usage(F).free >= 10 * 1024**3
    receipt = json.loads(R.read(REMOTE, 'REMOTE_RECOVERY01.json'))
    assert receipt['remote_commit'] == 'e260b040baba493449e89d3e91cab3d89ae4a55e'
    assert receipt['selection_sha256'] == 'feb5ef6a2d6973ad7cfd7065e713b4569d92103b9b8c2bd68a1b0d7d6a31d20d'
    assert receipt['selected_count'] == 8 and receipt['selected_logical_bytes'] == 1252014
    assert len(receipt['operations']) == receipt['expected_operations'] == 34
    assert all(r['exit'] == r['actual_reaped_exit'] == 0 and r['cleanup_failures'] == [] and r['actual_child_limits'] == {'pid': r['pid'], 'fsize': [R.FILE, R.FILE]} for r in receipt['operations'])
    actual_root = json.loads(R.read(REMOTE, 'ACTUAL_ROOT_EXIT01.json'))
    assert actual_root['actual_root_exit_code'] == 0
    refs = {r['path']: r for r in receipt['selected_blobs']}
    recovered = REMOTE / 'selected' / PREFIX
    for n in ('increment.tar.gz', 'archive-manifest.json', 'CAPTURE01.json'):
        raw = R.read(recovered, n); ref = refs[PREFIX + '/' + n]
        assert len(raw) == ref['bytes'] and R.digest(raw) == ref['sha256']
    record = json.loads(R.read(recovered, 'CAPTURE01.json'))
    manifest = json.loads(R.read(recovered, 'archive-manifest.json'))
    assert record['archive']['sha256'] == 'b37afd04fa53bb7d1b5d53adbe653ff1a34019e0b4e4af1706964da455c3354f'
    assert R.digest(R.read(recovered, 'archive-manifest.json')) == 'b6c5811de6ed0429a405c09e9c353863f8f52c60d000368996310bb4b9ae92fd'
    assert record['new_original_bodies'] == 85 and record['new_original_bytes'] == 2837266 and len(manifest['members']) == 86
    assert record['CAP_regular'] == 1213 and record['CAP_typed'] == 1563 and record['Parent_regular'] == 28 and record['Git_logical_objects'] == 473
    OUT.mkdir(mode=0o700); (OUT / 'flat').mkdir(mode=0o700)
    primitive = R.restore(recovered / 'increment.tar.gz', record['archive'], manifest, OUT / 'flat')
    assert primitive['regular_bodies'] == 86
    R.put(OUT / 'RECOVERY01.json', {'schema_version': 1, 'status': 'ACTUAL_CLOSED_PREDICTION_INCREMENT_FLAT_BYTE_RECOVERY', 'receiver_receipt_sha256': R.digest(R.read(REMOTE, 'REMOTE_RECOVERY01.json')), 'actual_receiver_root_exit_sha256': R.digest(R.read(REMOTE, 'ACTUAL_ROOT_EXIT01.json')), 'capture_sha256': R.digest(R.read(recovered, 'CAPTURE01.json')), 'archive_sha256': record['archive']['sha256'], 'manifest_sha256': R.digest(R.read(recovered, 'archive-manifest.json')), 'primitive': primitive, 'new_original_bodies': 85, 'new_original_bytes': 2837266, 'CAP_regular': 1213, 'CAP_typed': 1563, 'Parent_regular': 28, 'Git_logical_objects': 473, 'accepted_unchanged_basis': record['basis'], 'final_envelope_basis': record['final_envelope_basis'], 'paper_financial_fits': 0, 'numerical_authority': False, 'runtime_body_recovery': False, 'POSIX_reconstruction': False, 'immutable_writer_exclusion': False, 'qualification': 'Actual fresh remote-selected increment restored by unchanged R4; complete declared current CAP/Git/Parent scope composes through pinned accepted prior current and final-envelope byte bases. Independent full composition verification remains required. Original nulls/failures/spent identity unchanged.'})
    assert shutil.disk_usage(OUT).free >= 10 * 1024**3
    print(json.dumps({'status': 'ACTUAL_PREDICTION_INCREMENT_BYTE_RECOVERED', 'regular_bodies': 86, 'recovery_sha256': R.digest(R.read(OUT, 'RECOVERY01.json'))}))


if __name__ == '__main__':
    main()
