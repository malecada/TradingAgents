"""One actual-receipt-bound operational delta flat recovery; byte preservation only."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import stat
import sys
import time

HERE = Path(__file__).absolute().parent
PINS = {'utilities/recovery_pax01.py': 'a054d5922899b53579f4220ff3b427dc050dff075cb5470b43ff55e621b97eb2', 'utilities/owned_io.py': '09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb', 'utilities/bounded_git01.py': 'db4a65a450bf9930abac04ab794539ebd952b07826d7314b4aea4e989dd9240f', 'watch01.py': 'cd2200b071cf14c8191c7b7e95ee660b6bc9a10c49a6de252e77f9832ede8673'}
for name, pin in PINS.items():
    p = HERE / name
    s = p.lstat()
    if HERE.resolve() != HERE or p.resolve() != p or not stat.S_ISREG(s.st_mode) or s.st_nlink != 1 or s.st_size > 4194304 or hashlib.sha256(p.read_bytes()).hexdigest() != pin or p.lstat() != s:
        raise ValueError('exact unchanged local primitive required')
sys.path.insert(0, str(HERE / 'utilities'))
import recovery_pax01 as R
import watch01 as W

REL = 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-operational-delta-capture02-2026-10-04'
CAPTURE = '61f3560c6fc64b7122f12a690ab728407803c7bb3c3406fd1a754456e207f939'
SOURCE = '7b056a574e3e7b3c7ba209a39ee6a615e649d60c'
POLICY = 'ae8fbdc9d13e75fc453b70b5ee633c89fb4577e9b68a35b4147cf1bbd58c6887'
REMOTE_STATUS = 'fresh-actual-remote-operational-source-policy01-supervised-recovered'
BRANCH = 'refs/heads/research/onchain-paper-replication-2026-09-24'
ORIGIN = 'git@github.com:malecada/TradingAgents.git'
REQUIRED = __REQUIRED_LITERAL__
LOGICAL = 64 * 1024**2
ALLOCATION = 96 * 1024**2
OUTPUT = 'flat-operational-delta01'


def hexpin(value, length=64):
    R.require(type(value) is str and len(value) == length and all(c in '0123456789abcdef' for c in value), 'exact non-null lowercase hash pin')
    return value


def number(value, lower, upper):
    return type(value) in (int, float) and math.isfinite(value) and lower <= value <= upper


def selection_rows(selection):
    R.require(type(selection) is dict and set(selection) == {'remote_commit', 'rows'}, 'exact selection schema')
    hexpin(selection['remote_commit'], 40)
    rows = selection['rows']
    R.require(type(rows) is list and len(rows) == len(REQUIRED) == 10, 'exact ten selected rows')
    expected = [dict(path=name, **pin) for name, pin in sorted(REQUIRED.items())]
    R.require(rows == expected, 'complete sorted fixed selection; no extras, duplicates or changed pins')
    R.require(sum(row['bytes'] for row in rows) == 451691 and all(0 <= row['bytes'] <= R.FILE for row in rows), 'exact finite selected extents')
    for row in rows:
        R.path_name(row['path'])
    return rows


def validate_remote(remote, selection, selection_sha256):
    """Validate recorded actual evidence. This function does not manufacture origin proof."""
    rows = selection_rows(selection)
    R.require(remote['schema_version'] == 1 and remote['status'] == REMOTE_STATUS and remote['genuine_run_or_native_started'] is False, 'actual operational delta remote status required')
    R.require(remote['selection_sha256'] == hexpin(selection_sha256) and remote['remote_commit'] == selection['remote_commit'] and remote['origin'] == ORIGIN and remote['branch'] == BRANCH, 'actual selected remote context')
    records = remote['selected_blobs']
    R.require(type(records) is list and len(records) == 10, 'actual selected denominator')
    for record, selected in zip(records, rows):
        R.require(type(record) is dict and set(record) == {'path','bytes','sha256','git_mode','git_object'}, 'actual selected record fields')
        R.require({key: record[key] for key in selected} == selected and record['git_mode'] in ('100644','100755'), 'exact selected row and regular Git mode')
        hexpin(record['git_object'], 40)
    unique = len({row['git_object'] for row in records})
    expected = 10 + unique + 2 * len(rows)
    R.require(remote['selected_count'] == 10 and remote['selected_logical_bytes'] == 451691 and remote['unique_selected_objects'] == unique and remote['expected_operations'] == expected, 'exact actual operation and object denominators')
    operations = remote['operations']
    names = ['remote','ls-remote','init','remote','config','config','fetch','rev-parse','ls-tree'] + ['fetch'] * unique + ['cat-file','cat-file'] * 10 + ['ls-remote']
    R.require(type(operations) is list and len(operations) == expected and [row['operation'] for row in operations] == names, 'complete ordered actual operation sequence')
    for row in operations:
        R.require(type(row['pid']) is int and row['pid'] > 0 and type(row['exit']) is int and row['exit'] == 0 and type(row['actual_reaped_exit']) is int and row['actual_reaped_exit'] == 0 and row['cleanup_failures'] == [], 'actual successful main/reaped exits and cleanup')
        R.require(row['actual_child_limits'] == {'pid':row['pid'], 'fsize':[R.FILE,R.FILE]} and number(row['seconds'],0,75), 'actual child4MiB readback and bounded operation')
        R.require(type(row['stdout_bytes']) is int and 0 <= row['stdout_bytes'] <= R.FILE and type(row['stderr_bytes']) is int and 0 <= row['stderr_bytes'] <= 65536, 'bounded actual pipe extents')
        hexpin(row['stdout_sha256']); hexpin(row['stderr_sha256'])
    R.require(remote['whole_tree_policy'] == W.POLICY and number(remote['elapsed_seconds'],0,600) and type(remote['free_bytes']) is int and remote['free_bytes'] >= R.FLOOR, 'original whole-tree policy/deadline/floor')
    observations = remote['whole_tree_observations']
    R.require(type(observations) is list and 1 <= len(observations) <= W.POLICY['samples'] and remote['initial_owned_allocation'] == observations[0], 'actual initial baseline and complete observation list')
    for row in observations:
        R.require(type(row['logical_bytes']) is int and 0 <= row['logical_bytes'] <= LOGICAL and type(row['allocated_bytes']) is int and 0 <= row['allocated_bytes'] <= ALLOCATION and type(row['members']) is int and 1 <= row['members'] <= 32768 and number(row['seconds'],0,5) and row['seconds'] < 5 and type(row['complete_attempts']) is int and 1 <= row['complete_attempts'] <= 3 and type(row['regular_extent_changes']) is int and 0 <= row['regular_extent_changes'] <= row['members'] and row['measurement'] == 'complete sampled namespace; maximum of two regular extent observations', 'actual finite whole-tree sample')
    return records


def authenticate_selected(root, remote, selection, selection_sha256):
    records = validate_remote(remote, selection, selection_sha256)
    R.require(remote['fresh_git_root'] == str(root / 'fresh-operational-source-policy01.git'), 'actual same-root remote receiver namespace')
    for row in records:
        body = R.read(root / 'selected', row['path'])
        R.require(len(body) == row['bytes'] and R.digest(body) == row['sha256'] and hashlib.sha1(b'blob ' + str(len(body)).encode() + b'\0' + body).hexdigest() == row['git_object'], 'actual selected body SHA/extent/Git OID')
        R.require(stat.S_IMODE((root / 'selected' / row['path']).lstat().st_mode) == 0o600, 'actual private selected body mode; Git mode retained separately')
    return records


def load_capture(bundle):
    raw = R.read(bundle, 'CAPTURE01.json')
    R.require(R.digest(raw) == CAPTURE, 'exact actual capture pin')
    capture = json.loads(raw)
    R.require(capture['source_design'] == SOURCE and capture['policy_sha256'] == POLICY and capture['status'] == 'FROZEN_OPERATIONAL_SOURCE_POLICY_DELTA_NOT_EXTERNAL_RECOVERY' and capture['native_or_Run_started'] is False and capture['actual_external_or_flat_receipt'] is None, 'original capture context/nulls unchanged')
    R.require((capture['typed'],capture['files'],capture['raw_bytes'],capture['new_target_bodies'],capture['new_git_objects'],capture['original_git_basis_objects'],capture['total_reachable_git_objects'],capture['current_complete_nongit_members'],capture['preserved_unchanged_nongit_members']) == (41,33,943578,4,9,385,394,589,585), 'complete actual finite delta denominators')
    manifest_raw = R.read(bundle, 'PAYLOAD_MANIFEST01.json')
    manifest = json.loads(manifest_raw); R.validate(manifest)
    R.require(R.digest(manifest_raw) == capture['manifest_sha256'] == capture['archive']['manifest_sha256'] and R.encode(manifest) == manifest_raw, 'exact canonical full manifest')
    R.require(len(manifest['members']) == 41 and sum(row['kind'] == 'file' for row in manifest['members']) == 33 and sum(row.get('bytes',0) for row in manifest['members']) == 943578, 'full41/33/943578 delta')
    origin_raw = R.read(bundle, 'ORIGIN_MAP01.json')
    R.require(R.digest(origin_raw) == capture['origin_map_sha256'], 'exact complete original mode/path mapping')
    origins = json.loads(origin_raw)
    members = {row['path']:row for row in manifest['members'] if row['kind'] == 'file'}
    seen = set()
    for row in origins['origins']:
        name = R.path_name(row['path'])
        R.require(name not in seen and name in members and row['bytes'] == members[name]['bytes'] and row['sha256'] == members[name]['sha256'] and type(row['original_mode']) is int and 0 <= row['original_mode'] <= 0o7777, 'literal original file/mode mapping')
        seen.add(name)
    R.require(len(seen) == 22 and len([n for n in members if n.startswith('git-new/')]) == 9, 'all original mapping and new Git bodies')
    archive = R.read(bundle, 'operational-delta01.tar.gz')
    R.require(len(archive) == capture['archive']['bytes'] <= R.FILE and R.digest(archive) == capture['archive']['sha256'], 'actual frozen archive')
    R.require(943578 + len(manifest_raw) + len(origin_raw) < LOGICAL, 'flat body/metadata logical budget')
    return capture, manifest


def verify_flat(destination, result, capture, manifest, boundary):
    boundary()
    R.require(destination.resolve() == destination and stat.S_IMODE(destination.lstat().st_mode) == 0o700, 'retained canonical private flat directory')
    raw = R.read(destination, result['metadata_file'])
    R.require(R.digest(raw) == result['metadata_sha256'], 'flat metadata readback')
    metadata = json.loads(raw)
    R.require(metadata == {'schema_version':1,'manifest':manifest,'flat_members':metadata['flat_members'],'archive':capture['archive']}, 'complete original modes and archive retained')
    files = {r['path']:r for r in manifest['members'] if r['kind'] == 'file'}
    mapping = metadata['flat_members']
    R.require(set(mapping) == set(files) and len(set(mapping.values())) == len(files), 'complete one-to-one flat mapping')
    R.require(set(p.name for p in destination.iterdir()) == set(mapping.values()) | {result['metadata_file']}, 'exact full flat namespace')
    for name,row in files.items():
        leaf = mapping[name]
        R.require(type(leaf) is str and '/' not in leaf and leaf not in ('.','..') and leaf.startswith('body-'), 'safe flat leaf')
        body = R.read(destination,leaf)
        R.require(len(body) == row['bytes'] and R.digest(body) == row['sha256'] and stat.S_IMODE((destination/leaf).lstat().st_mode) == 0o600, 'all original bytes and private storage modes')
    boundary()
    return metadata


def restore_delta(bundle, capture, manifest, root, boundary):
    destination = root / OUTPUT
    R.require(root.is_absolute() and root.resolve() == root and not os.path.lexists(destination), 'fresh canonical flat namespace')
    boundary()
    destination.mkdir(mode=0o700)
    R.require(destination.resolve() == destination and stat.S_IMODE(destination.lstat().st_mode) == 0o700, 'existing private0700 destination before original restore')
    result = R.restore(bundle/'operational-delta01.tar.gz',capture['archive'],manifest,destination)
    verify_flat(destination,result,capture,manifest,boundary)
    return result


def run(remote_sha256, selection_sha256):
    hexpin(remote_sha256); hexpin(selection_sha256)
    R.require(all(not os.path.lexists(HERE/name) for name in (OUTPUT,'FLAT_INTENT01.json','FLAT_RECOVERY01.json','FLAT_FAILED01.json')), 'fresh one-use flat identity')
    begun = time.monotonic(); observations = []
    def boundary():
        R.require(time.monotonic()-begun < 180 and len(observations) < 64, '180-second/64-sample flat bound')
        row = W.census(HERE)
        row = dict(row,elapsed_seconds=time.monotonic()-begun,free_bytes=shutil.disk_usage(HERE).free)
        R.require(row['free_bytes'] >= R.FLOOR and row['elapsed_seconds'] < 180, 'final observed floor/deadline')
        observations.append(row)
    boundary()
    raw = R.read(HERE,'REMOTE_RECOVERY01.json'); selected_raw = R.read(HERE,'SELECTED_BODIES01.json')
    R.require(R.digest(raw) == remote_sha256 and R.digest(selected_raw) == selection_sha256, 'actual explicit remote and selection pins')
    remote = json.loads(raw); selection = json.loads(selected_raw)
    R.require(R.encode(selection) == selected_raw, 'canonical actual selection')
    authenticate_selected(HERE,remote,selection,selection_sha256)
    bundle = HERE/'selected'/REL
    capture,manifest = load_capture(bundle)
    boundary()
    R.put(HERE/'FLAT_INTENT01.json',{'schema_version':1,'source':SOURCE,'policy_sha256':POLICY,'capture_sha256':CAPTURE,'remote_receipt_sha256':remote_sha256,'selection_sha256':selection_sha256,'one_use':True,'native_or_claim_started':False})
    boundary()
    restored = restore_delta(bundle,capture,manifest,HERE,boundary)
    authenticate_selected(HERE,remote,selection,selection_sha256)
    capture2,manifest2 = load_capture(bundle)
    R.require(capture2 == capture and manifest2 == manifest and R.read(HERE,'REMOTE_RECOVERY01.json') == raw and R.read(HERE,'SELECTED_BODIES01.json') == selected_raw, 'all immutable receipts/payload retained')
    verify_flat(HERE/OUTPUT,restored,capture,manifest,boundary)
    result = {'schema_version':1,'status':'COMPLETE_OPERATIONAL_SOURCE_POLICY_DELTA_FLAT_BYTES','source':SOURCE,'policy_sha256':POLICY,'capture_sha256':CAPTURE,'remote_receipt_sha256':remote_sha256,'selection_sha256':selection_sha256,'remote_commit':remote['remote_commit'],'restored':restored,'original_mapping_sha256':capture['origin_map_sha256'],'whole_tree_policy':dict(W.POLICY),'initial_owned_allocation':observations[0],'whole_tree_observations':list(observations),'native_or_claim_started':False,'actual_root_exit':None,'posix_tree_restored':False,'whole_fit_capacity':None,'numerical_release':None,'qualification':'Exact41 typed/33 body operational source-policy delta only. Old385 Git recovery is separate; nine additional objects are opaque retained bytes, not reconstructed or fsck here. Whole owned-tree limits observed at finite before/after boundaries, not continuous quota or atomic coverage. Root tool exit is a separate later observation; original capture nulls and failed/spent identities remain unchanged.'}
    R.put(HERE/'FLAT_RECOVERY01.json',result)
    boundary()
    R.require(R.read(HERE,'FLAT_RECOVERY01.json') == R.encode(result), 'durable final receipt readback')
    R.put(HERE/'FLAT_POSTWRITE_OBSERVATION01.json',{'schema_version':1,'recovery_sha256':R.digest(R.encode(result)),'observation':observations[-1],'qualification':'post recovery-receipt write; this sidecar itself is outside that observation'})
    boundary()
    print(json.dumps({'status':result['status'],'regular_bodies':restored['regular_bodies'],'postwrite_observation':observations[-1]}))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--remote-receipt-sha256',required=True)
    parser.add_argument('--selection-sha256',required=True)
    args = parser.parse_args()
    run(args.remote_receipt_sha256,args.selection_sha256)


def entry():
    try:
        main()
    except BaseException as primary:
        failures = []
        try:
            # No str/repr/add_note hook can replace the original exception.
            R.put(HERE/'FLAT_FAILED01.json',{'schema_version':1,'status':'FAILED_ORIGINAL_FLAT_ATTEMPT_RETAINED','native_or_claim_started':False,'original_error_text_uninspected':True,'partial_bytes_retained':True})
        except BaseException as secondary:
            failures.append(secondary)
        R._cleanup(tuple((lambda e=e: (_ for _ in ()).throw(e)) for e in failures),primary=primary)
        raise


if __name__ == '__main__':
    entry()
