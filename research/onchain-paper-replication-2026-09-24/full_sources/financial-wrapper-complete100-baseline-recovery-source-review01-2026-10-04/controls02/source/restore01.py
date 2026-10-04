"""One-use byte restoration and offline Git reconstruction; no run authority."""
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
PARENT = Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-complete100-root-launch-20261004-01')
PINS = {'recovery04.py': 'b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a', 'owned_io.py': '09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb', 'bounded_git01.py': 'db4a65a450bf9930abac04ab794539ebd952b07826d7314b4aea4e989dd9240f'}
for name, pin in PINS.items():
    if hashlib.sha256((PARENT / name).read_bytes()).hexdigest() != pin:
        raise ValueError('unchanged bounded primitive required')
sys.path.insert(0, str(PARENT))
import recovery04 as R

REL = 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-baseline-capture01-2026-10-04'
CAPTURE = '7d65c2bac832832df5d62d49a41b31b7d54b33b52a448d048cd94b9541f8a176'
SOURCE = '9dc5c79f738920b52947b4e63fed0397f1b5b207'
IDENTITY = 'financial-wrapper-classification-eager-complete100-20261003-01'
LABELS = ('capsule', 'parent', 'support', 'git1', 'git2', 'git3')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--remote-receipt-sha256', required=True)
    args = parser.parse_args()
    absent = [f'flat-{label}01' for label in LABELS] + ['fresh-original-source339-01.git', 'FLAT_INTENT01.json', 'FLAT_RECOVERY01.json', 'FLAT_FAILED01.json']
    R.require(all(not os.path.lexists(HERE / name) for name in absent), 'fresh one-use restoration namespace')
    begun = time.monotonic()
    floors = []
    operations = []

    def floor():
        free = shutil.disk_usage(HERE).free
        R.require(free >= R.FLOOR and time.monotonic() - begun < 180, 'finite restoration and10GiB floor')
        floors.append({'seconds': time.monotonic() - begun, 'free_bytes': free})

    def git(repo, arguments, cap=R.FILE):
        floor()
        R.require(len(operations) < 400, 'finite offline Git operations')
        body = R.git(repo, arguments, cap=cap)
        operations.append({'operation': arguments[0], 'stdout_bytes': len(body), 'stdout_sha256': R.digest(body), 'exit': 0})
        return body

    floor()
    remote_raw = R.read(HERE, 'REMOTE_RECOVERY01.json')
    R.require(R.digest(remote_raw) == args.remote_receipt_sha256, 'explicit actual remote receipt')
    remote = json.loads(remote_raw)
    R.require(remote['status'] == 'fresh-actual-remote-complete100-baseline-source339-recovered' and remote['genuine_run_or_native_started'] is False, 'actual baseline byte recovery only')
    required = json.loads(R.read(ROOT, REL + '/REQUIRED_BODIES02.json'))
    rows = {row['path']: row for row in remote['selected_blobs']}
    R.require(len(rows) == len(remote['selected_blobs']) == len(required) == 17 and set(rows) == set(required), 'exact seventeen original baseline bodies')
    for name, row in rows.items():
        R.require(name.startswith(REL + '/') and row['git_mode'] in ('100644', '100755'), 'exact selected scope and mode')
        body = R.read(HERE / 'selected', name)
        R.require(len(body) == row['bytes'] == required[name]['bytes'] and R.digest(body) == row['sha256'] == required[name]['sha256'], 'actual selected body extent and hash')
        R.require(hashlib.sha1(b'blob ' + str(len(body)).encode() + b'\0' + body).hexdigest() == row['git_object'], 'actual external Git blob object')
    bundle = HERE / 'selected' / REL
    capture_raw = R.read(bundle, 'CAPTURE01.json')
    R.require(R.digest(capture_raw) == CAPTURE, 'literal current baseline capture')
    capture = json.loads(capture_raw)
    R.require(capture['source'] == SOURCE and capture['identity'] == IDENTITY and capture['status'] == 'PRELAUNCH_SOURCE_DRAFT_NO_CLAIM' and capture['native_or_claim_started'] is False and capture['final_request_or_release_captured'] is False and set(capture['scopes']) == set(LABELS), 'genuine prelaunch scope; final supplement separate')
    R.put(HERE / 'FLAT_INTENT01.json', {'schema_version': 1, 'source': SOURCE, 'identity': IDENTITY, 'remote_receipt_sha256': args.remote_receipt_sha256, 'capture_sha256': CAPTURE, 'native_or_claim_started': False, 'one_use': True})
    restored = {}
    for label in LABELS:
        floor()
        manifest_raw = R.read(bundle, label.upper() + '_MANIFEST01.json')
        R.require(R.digest(manifest_raw) == capture['scopes'][label]['manifest_sha256'], 'exact captured scope manifest')
        manifest = json.loads(manifest_raw)
        archive = R.read(bundle, 'complete-' + label + '01.tar.gz')
        result = R.restore(bundle / ('complete-' + label + '01.tar.gz'), capture['scopes'][label]['archive'], manifest, HERE / ('flat-' + label + '01'))
        restored[label] = result

    index_raw = R.read(bundle, 'GIT_OBJECTS01.json')
    R.require(R.digest(index_raw) == capture['git_object_index_sha256'], 'literal original Git object index')
    index = json.loads(index_raw)
    objects = index['reachable_objects']
    R.require(index['source'] == SOURCE and index['object_count'] == len(objects) == 385 and index['object_body_bytes'] == sum(row['bytes'] for row in objects) == 7807097, 'complete exact original source object census')
    R.require(len({row['git_object'] for row in objects}) == len(objects), 'unique original Git objects')
    actual_paths = {}
    for label in ('git1', 'git2', 'git3'):
        metadata = json.loads(R.read(HERE / ('flat-' + label + '01'), restored[label]['metadata_file']))
        actual_paths[label] = metadata['flat_members']
    repo = HERE / 'fresh-original-source339-01.git'
    git(HERE, ['init', '--bare', str(repo)])
    for row in objects:
        floor()
        R.require(row['scope'] in actual_paths and row['path'] == row['git_object'] and row['kind'] in ('blob', 'tree', 'commit', 'tag'), 'original object role and type')
        name = actual_paths[row['scope']][row['path']]
        base = HERE / ('flat-' + row['scope'] + '01')
        raw = R.read(base, name)
        R.require(len(raw) == row['bytes'] and R.digest(raw) == row['sha256'], 'restored object extent and bytes')
        R.require(hashlib.sha1(row['kind'].encode() + b' ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() == row['git_object'], 'original immutable Git object identity')
        pin = R.sig((base / name).lstat())
        oid = git(repo, ['hash-object', '-w', '-t', row['kind'], str(base / name)], cap=128).decode().strip()
        R.require(oid == row['git_object'] and R.sig((base / name).lstat()) == pin and R.read(base, name) == raw, 'actual offline Git write and unchanged restored original')
    git(repo, ['update-ref', 'refs/heads/replication-capture', SOURCE], cap=128)
    git(repo, ['symbolic-ref', 'HEAD', 'refs/heads/replication-capture'], cap=128)
    R.require(git(repo, ['rev-parse', 'HEAD'], cap=128).decode().strip() == SOURCE, 'fresh actual current Git commit')
    git(repo, ['fsck', '--full', '--strict', '--no-reflogs', SOURCE])
    names = git(repo, ['ls-tree', '-r', '--name-only', SOURCE]).decode().splitlines()
    R.require(len(names) == len(set(names)) == 339, 'fresh original339 current tree')
    expected = sorted(row['git_object'] for row in objects)
    actual = sorted(git(repo, ['rev-list', '--objects', '--no-object-names', SOURCE]).decode().splitlines())
    R.require(actual == expected, 'complete actual reachable original Git population')
    floor()
    result = {'schema_version': 1, 'status': 'COMPLETE_CURRENT_BASELINE_BYTES_AND_ORIGINAL_GIT_RECOVERED', 'source': SOURCE, 'identity': IDENTITY, 'capture_sha256': CAPTURE, 'remote_receipt_sha256': args.remote_receipt_sha256, 'scopes': restored, 'fresh_original_git': str(repo), 'original_reachable_objects': len(objects), 'original_current_tree_files': len(names), 'offline_git_operations': operations, 'offline_git_PID_history_recorded': False, 'floor_observations': floors, 'native_or_claim_started': False, 'final_request_or_release_recovered': False, 'installed_runtime_bodies': False, 'posix_tree_restored': False, 'whole_fit_capacity': None, 'qualification': 'Complete current byte baseline and genuine original Git objects reconstructed from actual external recovery. Final request/release supplement and independent actual recovery verification remain separate.'}
    R.put(HERE / 'FLAT_RECOVERY01.json', result)
    print(json.dumps({'status': result['status'], 'scopes': len(restored), 'original_objects': len(objects), 'offline_operations': len(operations)}))


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
