"""Finite two-scope final byte supplement; missing real pins refuse before IO."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import time

HERE = Path(__file__).resolve().parent
PINS = {'recovery04.py': 'b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a', 'owned_io.py': '09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb', 'bounded_git01.py': 'db4a65a450bf9930abac04ab794539ebd952b07826d7314b4aea4e989dd9240f'}
for name, pin in PINS.items():
    path = HERE / 'utilities' / name
    if path.resolve() != path or path.stat().st_size > 4194304 or hashlib.sha256(path.read_bytes()).hexdigest() != pin:
        raise ValueError('exact unchanged bounded primitive required')
sys.path.insert(0, str(HERE / 'utilities'))
import recovery04 as R

REL = None
CAPTURE = None
CAPTURE_STATUS = None
REQUIRED = None
SOURCE = '9dc5c79f738920b52947b4e63fed0397f1b5b207'
IDENTITY = 'financial-wrapper-classification-eager-complete100-20261003-01'
LABELS = ('contract', 'support')
REMOTE_STATUS = 'fresh-actual-remote-complete100-final-supplement-recovered'
LOGICAL = 64 * 1024**2


def pins_ready():
    R.require(type(REL) is str and type(CAPTURE) is str and len(CAPTURE) == 64 and type(CAPTURE_STATUS) is str and type(REQUIRED) is dict and 1 <= len(REQUIRED) <= 506, 'actual final capture pins unavailable')
    R.require(all(c in '0123456789abcdef' for c in CAPTURE), 'actual capture digest')
    R.require(sum(row['bytes'] for row in REQUIRED.values()) <= LOGICAL, 'fixed selected logical bound')


def authenticate_selected(directory, remote):
    """Actual receipt/body checks only; does not mint remote provenance."""
    R.require(remote['status'] == REMOTE_STATUS and remote['genuine_run_or_native_started'] is False, 'actual final supplement remote receipt required')
    commit = remote['remote_commit']
    R.require(type(commit) is str and len(commit) == 40 and all(c in '0123456789abcdef' for c in commit), 'actual remote commit')
    records = remote['selected_blobs']
    R.require(type(records) is list and len(records) == len(REQUIRED), 'exact selected denominator')
    rows = {}
    for row in records:
        name = row['path']
        R.require(type(name) is str and name in REQUIRED and name not in rows and name.startswith(REL + '/') and row['git_mode'] in ('100644', '100755'), 'exact unique selected body and Git mode')
        body = R.read(directory / 'selected', name)
        R.require(len(body) == row['bytes'] == REQUIRED[name]['bytes'] and R.digest(body) == row['sha256'] == REQUIRED[name]['sha256'], 'actual selected body hash/size')
        R.require(hashlib.sha1(b'blob ' + str(len(body)).encode() + b'\0' + body).hexdigest() == row['git_object'], 'actual remote Git blob OID')
        rows[name] = row
    R.require(set(rows) == set(REQUIRED) and list(rows) == sorted(rows), 'complete sorted fixed selected scope')
    R.require(remote['selected_count'] == len(rows) and remote['selected_logical_bytes'] == sum(row['bytes'] for row in rows.values()) and len(remote['operations']) == 11 + 2 * len(rows), 'actual remote receipt denominators')
    R.require(all(row['exit'] == 0 and row['cleanup_failures'] == [] for row in remote['operations']), 'actual successful remote cleanup')
    return rows


def load_scopes(bundle, capture):
    R.require(capture['source'] == SOURCE and capture['identity'] == IDENTITY and capture['status'] == CAPTURE_STATUS and capture['native_or_claim_started'] is False and set(capture['scopes']) == set(LABELS), 'exact final two-scope context')
    scopes = {}
    total = 0
    for label in LABELS:
        row = capture['scopes'][label]
        raw = R.read(bundle, label.upper() + '_MANIFEST01.json')
        R.require(R.digest(raw) == row['manifest_sha256'] == row['archive']['manifest_sha256'], 'exact captured manifest bytes')
        manifest = json.loads(raw)
        R.validate(manifest)
        total += sum(member.get('bytes', 0) for member in manifest['members']) + len(raw)
        R.require(total <= LOGICAL and row['archive']['bytes'] <= R.FILE, 'complete flat plus mode metadata logical bound')
        archive = R.read(bundle, 'complete-' + label + '01.tar.gz')
        R.require(len(archive) == row['archive']['bytes'] and R.digest(archive) == row['archive']['sha256'], 'actual captured archive bytes')
        scopes[label] = {'manifest': manifest, 'archive': row['archive']}
    return scopes


def restore_scopes(bundle, scopes, output, boundary):
    """Owned byte utility; caller supplies authenticated exact scope metadata."""
    R.require(set(scopes) == set(LABELS), 'exact two flat scopes')
    R.require(all(not os.path.lexists(output / ('flat-' + label + '01')) for label in LABELS), 'fresh two-scope destinations')
    restored = {}
    for label in LABELS:
        boundary()
        destination = output / ('flat-' + label + '01')
        destination.mkdir(mode=0o700)
        R.require(destination.resolve() == destination and stat.S_IMODE(destination.lstat().st_mode) == 0o700, 'fresh canonical private destination')
        restored[label] = R.restore(bundle / ('complete-' + label + '01.tar.gz'), scopes[label]['archive'], scopes[label]['manifest'], destination)
        boundary()
    # Rejoin every retained first-scope body after the second scope and its cleanup.
    for label in LABELS:
        boundary()
        destination = output / ('flat-' + label + '01')
        result = restored[label]
        raw = R.read(destination, result['metadata_file'])
        R.require(R.digest(raw) == result['metadata_sha256'], 'retained mode metadata unchanged')
        metadata = json.loads(raw)
        R.require(metadata['manifest'] == scopes[label]['manifest'] and metadata['archive'] == scopes[label]['archive'], 'retained complete mode/archive metadata')
        mapping = metadata['flat_members']
        files = {member['path']: member for member in metadata['manifest']['members'] if member['kind'] == 'file'}
        R.require(set(mapping) == set(files) and set(p.name for p in destination.iterdir()) == set(mapping.values()) | {result['metadata_file']}, 'complete private flat body namespace')
        for name, member in files.items():
            body = R.read(destination, mapping[name])
            R.require(len(body) == member['bytes'] and R.digest(body) == member['sha256'], 'retained flat body exact')
        boundary()
    return restored


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--remote-receipt-sha256', required=True)
    args = parser.parse_args()
    pins_ready()
    absent = [f'flat-{label}01' for label in LABELS] + ['FLAT_INTENT01.json', 'FLAT_RECOVERY01.json', 'FLAT_FAILED01.json']
    R.require(all(not os.path.lexists(HERE / name) for name in absent), 'fresh one-use final supplement namespace')
    begun = time.monotonic()
    floors = []

    def boundary():
        free = shutil.disk_usage(HERE).free
        elapsed = time.monotonic() - begun
        R.require(free >= R.FLOOR and elapsed < 180 and len(floors) < 32, 'bounded final supplement and10GiB floor')
        floors.append({'seconds': elapsed, 'free_bytes': free})

    boundary()
    remote_raw = R.read(HERE, 'REMOTE_RECOVERY01.json')
    R.require(R.digest(remote_raw) == args.remote_receipt_sha256, 'explicit actual remote receipt pin')
    remote = json.loads(remote_raw)
    authenticate_selected(HERE, remote)
    bundle = HERE / 'selected' / REL
    capture_raw = R.read(bundle, 'CAPTURE01.json')
    R.require(R.digest(capture_raw) == CAPTURE, 'exact actual final capture')
    capture = json.loads(capture_raw)
    scopes = load_scopes(bundle, capture)
    boundary()
    R.put(HERE / 'FLAT_INTENT01.json', {'schema_version': 1, 'source': SOURCE, 'identity': IDENTITY, 'capture_sha256': CAPTURE, 'remote_receipt_sha256': args.remote_receipt_sha256, 'one_use': True, 'native_or_claim_started': False})
    restored = restore_scopes(bundle, scopes, HERE, boundary)
    boundary()
    authenticate_selected(HERE, remote)
    R.require(R.read(HERE, 'REMOTE_RECOVERY01.json') == remote_raw and R.read(bundle, 'CAPTURE01.json') == capture_raw, 'original receipt/capture retained unchanged')
    boundary()
    result = {'schema_version': 1, 'status': 'COMPLETE_FINAL_SUPPLEMENT_CONTRACT_SUPPORT_BYTES_RECOVERED', 'source': SOURCE, 'identity': IDENTITY, 'capture_sha256': CAPTURE, 'remote_commit': remote['remote_commit'], 'remote_receipt_sha256': args.remote_receipt_sha256, 'scopes': restored, 'floor_observations': floors, 'native_or_claim_started': False, 'original_git_reconstruction_performed_here': False, 'baseline_original385_git_recovery_separate': True, 'posix_tree_restored': False, 'installed_runtime_bodies': False, 'numerical_release': None, 'whole_fit_capacity': None, 'qualification': 'Actual final contract/support bytes and mode metadata only; genuine baseline Source339/all385 Git recovery stays separate. Independent exact recovery/release review remains required; no native or scientific authority is minted.'}
    R.put(HERE / 'FLAT_RECOVERY01.json', result)
    print(json.dumps({'status': result['status'], 'scopes': len(restored)}))


def entry():
    try:
        main()
    except BaseException as primary:
        secondary = []
        try:
            R.put(HERE / 'FLAT_FAILED01.json', {'schema_version': 1, 'status': 'FAILED_ORIGINAL_RESTORATION_ATTEMPT', 'error_type': type(primary).__name__, 'error': str(primary), 'native_or_claim_started': False})
        except BaseException as error:
            secondary.append(error)
        R._cleanup(tuple((lambda error=error: (_ for _ in ()).throw(error)) for error in secondary), primary=primary)
        raise


if __name__ == '__main__':
    entry()
