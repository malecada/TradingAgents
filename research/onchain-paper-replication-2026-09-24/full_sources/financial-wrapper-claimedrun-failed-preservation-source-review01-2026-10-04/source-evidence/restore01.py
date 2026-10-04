"""One-use flat restore of freshly fetched FAILED engineering outcome bytes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import time

ROOT = Path.cwd().resolve()
HERE = Path(__file__).resolve().parent
PARENT = Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-root-launch-20261004-01')
PINS = {'recovery04.py': 'b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a', 'owned_io.py': '09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb', 'bounded_git01.py': 'db4a65a450bf9930abac04ab794539ebd952b07826d7314b4aea4e989dd9240f'}
# The bounded helper bodies are authenticated before import.
for name, pin in PINS.items():
    if hashlib.sha256((PARENT / name).read_bytes()).hexdigest() != pin:
        raise ValueError('unchanged flat primitive required')
sys.path.insert(0, str(PARENT))
import recovery04 as R

REL = 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-claimedrun-failed-capture01-2026-10-04'
CAPTURE = '08f69b601770c81572e5223f1f5cdec21e2c48072ba86394255b0c5bcddc9ae1'
IDENTITY = 'financial-wrapper-classification-eager-interrupt1-claimedrun-20261004-01'

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--remote-receipt-sha256', required=True)
    a = p.parse_args()
    R.require(all(not os.path.lexists(HERE / n) for n in ('flat-capsule01', 'flat-parent01', 'flat-root01', 'FLAT_INTENT01.json', 'FLAT_RECOVERY01.json')), 'one-use restore namespace')
    floors = []
    begun = time.monotonic()
    def floor():
        free = shutil.disk_usage(HERE).free
        R.require(free >= R.FLOOR and time.monotonic() - begun < 120, 'finite restore and10GiB floor')
        floors.append({'seconds': time.monotonic() - begun, 'free_bytes': free})
    floor()
    raw = R.read(HERE, 'REMOTE_RECOVERY01.json')
    R.require(R.digest(raw) == a.remote_receipt_sha256, 'explicit actual remote receipt')
    remote = json.loads(raw)
    R.require(remote['status'] == 'fresh-actual-remote-claimedrun-failed-source339-recovered' and remote['genuine_run_or_native_started'] is False, 'actual byte-only recovery')
    rows = {r['path']: r for r in remote['selected_blobs']}
    R.require(len(rows) == len(remote['selected_blobs']) == 8, 'exact eight remote bodies')
    bundle = HERE / 'selected' / REL
    for name, row in rows.items():
        R.require(name.startswith(REL + '/') and row['git_mode'] in ('100644', '100755'), 'actual selected scope/mode')
        body = R.read(HERE / 'selected', name)
        R.require(len(body) == row['bytes'] and R.digest(body) == row['sha256'], 'actual selected body')
        R.require(hashlib.sha1(b'blob ' + str(len(body)).encode() + b'\0' + body).hexdigest() == row['git_object'], 'actual external Git object')
    capture_raw = R.read(bundle, 'CAPTURE01.json')
    R.require(R.digest(capture_raw) == CAPTURE, 'complete exact capture')
    capture = json.loads(capture_raw)
    R.require(capture['identity'] == IDENTITY and capture['source'] == '0a2e7639b42b9423b90743feadcda4078aa21816' and capture['actual_root_exit'] == capture['actual_child_exit'] == 1 and capture['original_parent_exit'] is None and capture['permanently_reserved'] is True, 'original FAILED/null/spent disposition')
    R.put(HERE / 'FLAT_INTENT01.json', {'identity': IDENTITY, 'remote_receipt_sha256': a.remote_receipt_sha256, 'capture_sha256': CAPTURE, 'native_or_claim_started': False, 'one_use': True})
    actual = {}
    for label in ('capsule', 'parent', 'root'):
        floor()
        manifest_raw = R.read(bundle, label.upper() + '_MANIFEST01.json')
        R.require(R.digest(manifest_raw) == capture['scopes'][label]['manifest_sha256'], 'exact scope manifest')
        manifest = json.loads(manifest_raw)
        R.validate(manifest)
        R.require(len(manifest['members']) == capture['scopes'][label]['members'], 'complete scope denominator')
        dest = HERE / ('flat-' + label + '01')
        dest.mkdir(mode=0o700)
        actual[label] = R.restore(bundle / ('complete-' + label + '01.tar.gz'), capture['scopes'][label]['archive'], manifest, dest)
        floor()
    result = {'schema_version': 1, 'identity': IDENTITY, 'status': 'actual-fresh-flat-FAILED-claimedrun-outcome-recovered', 'remote_receipt_sha256': a.remote_receipt_sha256, 'capture_sha256': CAPTURE, 'actual': actual, 'floor_observations': floors, 'actual_root_exit': 1, 'original_parent_exit': None, 'permanently_reserved': True, 'installed_runtime_bodies': False, 'posix_instantiation': False, 'native_capacity': False, 'numerical_import_or_repeat': False, 'independent_acceptance': False}
    R.put(HERE / 'FLAT_RECOVERY01.json', result)
    print(json.dumps({'status': result['status'], 'regular_bodies': sum(r['regular_bodies'] for r in actual.values())}, sort_keys=True))

if __name__ == '__main__':
    main()
