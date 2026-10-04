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
PINS = {'recovery_pax01.py': 'a054d5922899b53579f4220ff3b427dc050dff075cb5470b43ff55e621b97eb2', 'owned_io.py': '09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb', 'bounded_git01.py': 'db4a65a450bf9930abac04ab794539ebd952b07826d7314b4aea4e989dd9240f'}
for name, pin in PINS.items():
    path = HERE / 'utilities' / name
    if path.resolve() != path or path.stat().st_size > 4194304 or hashlib.sha256(path.read_bytes()).hexdigest() != pin:
        raise ValueError('exact unchanged bounded primitive required')
sys.path.insert(0, str(HERE / 'utilities'))
import recovery_pax01 as R

REL = 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture02-2026-10-04'
OLD_REL = 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture01-2026-10-04'
CAPTURE = 'e9e78f1cc4f33d51ddca968bc80170e83e1a12b6ff2bff9cf301ab25e280fce8'
CAPTURE_STATUS = 'FAILED_COMPLETE100_OUTCOME_FROZEN'
REQUIRED = {'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture01-2026-10-04/CAPSULE_MASTER_MANIFEST01.json': {'bytes': 63, 'sha256': '87ef8249ef9652f98d57b4d5e885dbf3b5e5e0773987b8cab08eb23bc2176904'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture01-2026-10-04/CAPSULE_SHARD_INDEX01.json': {'bytes': 465, 'sha256': 'a9039426a5e30c4a7e7339fcff426d32669f507f4963175a8239bec57d954bfb'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture01-2026-10-04/CAPTURE01.json': {'bytes': 6615, 'sha256': '8b991df1466cf12f7812396b5b6afde3776edf684f1af12f9fa6e4454bf5dce1'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture01-2026-10-04/PARENT_MANIFEST01.json': {'bytes': 5112, 'sha256': '0e37c659c36f9918f6fcf643a51b2784c44b4891d3afacc5314ade0dc9401916'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture01-2026-10-04/ROOT_EVIDENCE_PATHS01.json': {'bytes': 3707, 'sha256': '3f4988561721c2bf208ebd1050dfb6eced16d1dec0ab9812da52d1ed40ad29b2'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture01-2026-10-04/SUPPORT_MANIFEST01.json': {'bytes': 5965, 'sha256': '37a0ff3e70003d50bf0128eb40dc53718e75833ff86cc32b5096de2455dba896'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture01-2026-10-04/SUPPORT_ROOTS01.json': {'bytes': 410, 'sha256': 'c7a7ff931db5efd369aec97919e015c7ff69d9357707ffad9fd523f5bb428425'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture01-2026-10-04/complete-parent01.tar.gz': {'bytes': 53889, 'sha256': '62272f91bd416dc094063902f972a2c3965db0b2e2a44f332f2f3c7dfc7b62aa'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture01-2026-10-04/complete-support01.tar.gz': {'bytes': 124284, 'sha256': '5d04fc75c2c82a9bc6959b0d534367be4885685d67fb2292a4c0c754b0b0acbc'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture02-2026-10-04/CAPSULE01_MANIFEST01.json': {'bytes': 53083, 'sha256': '96d00adfa68490694e69c521396ae601ca80ea28f282934e112df302e5afe8aa'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture02-2026-10-04/CAPSULE02_MANIFEST01.json': {'bytes': 41376, 'sha256': '14f80e2c44f29c9eb93abc1cc2f9086a9a977c0f9a59fabfd938843ee4d1824d'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture02-2026-10-04/CAPSULE03_MANIFEST01.json': {'bytes': 8751, 'sha256': '5b0c807f62ae5376709f7b8b5c637fdaf0b66a5b39f0729b9752ba2d542073c9'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture02-2026-10-04/CAPSULE04_MANIFEST01.json': {'bytes': 8319, 'sha256': '6b2e0757b177b3f710196355884aa1fe3505d8ebcc8969b837420a675f37080e'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture02-2026-10-04/CAPSULE05_MANIFEST01.json': {'bytes': 8319, 'sha256': '64c44e349b2cf8e16224a216b1b897389e45ce7fe8c554b5d18db0afa7e28710'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture02-2026-10-04/CAPSULE06_MANIFEST01.json': {'bytes': 8319, 'sha256': '56f7edc355855cb0a1b2a3229b0a7f39fd78205b924fba1fb4971cdae22bba48'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture02-2026-10-04/CAPSULE07_MANIFEST01.json': {'bytes': 50772, 'sha256': '23e5fcc4a0103932264ab6e2469e3e26d7b32bef8e1663436317b2aed41d5cff'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture02-2026-10-04/CAPSULE08_MANIFEST01.json': {'bytes': 2872, 'sha256': '7efc7bb9c9e4226586fe4e375c8499a77bee5499b1c3994750e9486c56da4d24'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture02-2026-10-04/CAPSULE_MASTER_MANIFEST01.json': {'bytes': 156650, 'sha256': '537a6553912d10ce59a411e01438499a7a04e07c7929b7c68e8e0cbb033dfec1'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture02-2026-10-04/CAPSULE_SHARD_INDEX01.json': {'bytes': 128243, 'sha256': '3a157938a90bb8f985f6623a6126ade33b2ffc74e1211fded8e9fc0d24b3043b'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture02-2026-10-04/CAPTURE01.json': {'bytes': 69134, 'sha256': 'e9e78f1cc4f33d51ddca968bc80170e83e1a12b6ff2bff9cf301ab25e280fce8'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture02-2026-10-04/PARENT_MANIFEST01.json': {'bytes': 5112, 'sha256': '0e37c659c36f9918f6fcf643a51b2784c44b4891d3afacc5314ade0dc9401916'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture02-2026-10-04/PRIOR_FAILED_CAPTURE_ERRATA01.json': {'bytes': 813, 'sha256': 'ce15a2a946af54290aee4040b70d9e18738637d822b8c9551edd9d287cc77e65'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture02-2026-10-04/ROOT_EVIDENCE_PATHS01.json': {'bytes': 3707, 'sha256': '3f4988561721c2bf208ebd1050dfb6eced16d1dec0ab9812da52d1ed40ad29b2'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture02-2026-10-04/SUPPORT_MANIFEST01.json': {'bytes': 5965, 'sha256': '37a0ff3e70003d50bf0128eb40dc53718e75833ff86cc32b5096de2455dba896'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture02-2026-10-04/SUPPORT_ROOTS01.json': {'bytes': 410, 'sha256': 'c7a7ff931db5efd369aec97919e015c7ff69d9357707ffad9fd523f5bb428425'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture02-2026-10-04/complete-capsule0101.tar.gz': {'bytes': 663185, 'sha256': '2288fd7d16883c4fda74c7dd84728fe724a49546c50ae7ab07f8bc9ee37d643e'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture02-2026-10-04/complete-capsule0201.tar.gz': {'bytes': 1724365, 'sha256': 'eb7d3d55fb1d62ee37beb3d3ce0c7dfcfa0661421152c9b1b4c4e6e8ab59973b'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture02-2026-10-04/complete-capsule0301.tar.gz': {'bytes': 2747900, 'sha256': '63ffffadc257f0bbea32738d48ad92a00c3efbe94d2456c24ad465393028f548'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture02-2026-10-04/complete-capsule0401.tar.gz': {'bytes': 2737208, 'sha256': '8e6d2c208e566ef39921548105b4d0e8a035f102e71fa69a0fd9a1367ab8fda4'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture02-2026-10-04/complete-capsule0501.tar.gz': {'bytes': 2738391, 'sha256': '7b9ba899fc9c9cde51be4f4de6bdb786737ed0f818feec32030865ea586c04dc'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture02-2026-10-04/complete-capsule0601.tar.gz': {'bytes': 2734920, 'sha256': 'de51e82005665950cf2c0945ddb46260ceb9922b2ee059548e0e9a74a9aacf25'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture02-2026-10-04/complete-capsule0701.tar.gz': {'bytes': 1780860, 'sha256': '30fc8b2e4e1e75188d8ceb3b593243a4f0f72808477c7f5cc7ed779e7095f4dd'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture02-2026-10-04/complete-capsule0801.tar.gz': {'bytes': 423945, 'sha256': '1f28552b811e5a7f362045e4575ed25007abeced2c8a316532756d1bde7b4b57'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture02-2026-10-04/complete-parent01.tar.gz': {'bytes': 53889, 'sha256': '62272f91bd416dc094063902f972a2c3965db0b2e2a44f332f2f3c7dfc7b62aa'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-complete100-failed-outcome-capture02-2026-10-04/complete-support01.tar.gz': {'bytes': 124284, 'sha256': '5d04fc75c2c82a9bc6959b0d534367be4885685d67fb2292a4c0c754b0b0acbc'}}
SOURCE = '9dc5c79f738920b52947b4e63fed0397f1b5b207'
IDENTITY = 'financial-wrapper-classification-eager-complete100-20261003-01'
LABELS = ('capsule01', 'capsule02', 'capsule03', 'capsule04', 'capsule05', 'capsule06', 'capsule07', 'capsule08', 'parent', 'support')
REMOTE_STATUS = 'fresh-actual-remote-complete100-failed-outcome02-recovered'
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
        R.require(type(name) is str and name in REQUIRED and name not in rows and any(name.startswith(prefix + '/') for prefix in (REL, OLD_REL)) and row['git_mode'] in ('100644', '100755'), 'exact unique selected body and Git mode')
        body = R.read(directory / 'selected', name)
        R.require(len(body) == row['bytes'] == REQUIRED[name]['bytes'] and R.digest(body) == row['sha256'] == REQUIRED[name]['sha256'], 'actual selected body hash/size')
        R.require(hashlib.sha1(b'blob ' + str(len(body)).encode() + b'\0' + body).hexdigest() == row['git_object'], 'actual remote Git blob OID')
        rows[name] = row
    R.require(set(rows) == set(REQUIRED) and list(rows) == sorted(rows), 'complete sorted fixed selected scope')
    R.require(remote['selected_count'] == len(rows) and remote['selected_logical_bytes'] == sum(row['bytes'] for row in rows.values()) and len(remote['operations']) == 11 + 2 * len(rows), 'actual remote receipt denominators')
    R.require(all(row['exit'] == 0 and row['cleanup_failures'] == [] for row in remote['operations']), 'actual successful remote cleanup')
    return rows


def load_scopes(bundle, capture):
    R.require(capture['source'] == SOURCE and capture['identity'] == IDENTITY and capture['status'] == CAPTURE_STATUS and capture['historical_native_started'] is True and capture['new_native_or_claim_started_by_capture'] is False and capture['permanent_disposition'] == 'FAILED_SPENT' and capture['prior_failed_capture_permanently_withheld'] is True and set(capture['scopes']) == set(LABELS), 'exact final two-scope context')
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
    validate_union(bundle, capture, scopes)
    return scopes


def validate_union(bundle, capture, scopes):
    """Fixed corrected Master and shard coverage; old zero is forensic only."""
    raw = R.read(bundle, 'CAPSULE_MASTER_MANIFEST01.json')
    R.require(R.digest(raw) == capture['capsule_master_sha256'] == '537a6553912d10ce59a411e01438499a7a04e07c7929b7c68e8e0cbb033dfec1', 'corrected nonempty Master pin')
    master = json.loads(raw)
    R.validate(master)
    members = {r['path']: r for r in master['members']}
    files = {k: r for k, r in members.items() if r['kind'] == 'file'}
    R.require(len(members) == 588 and len(files) == 475 and sum(r['bytes'] for r in files.values()) == 23015911, 'full actual corrected Master denominator')
    index_raw = R.read(bundle, 'CAPSULE_SHARD_INDEX01.json')
    R.require(R.digest(index_raw) == capture['shard_index_sha256'], 'actual fixed shard index')
    index = json.loads(index_raw)
    R.require(index['master_manifest_sha256'] == R.digest(raw) and index['shards'] == 8 and index['original_typed_members'] == 588 and index['regular_bodies'] == 475 and index['original_logical_bytes'] == 23015911 and index['files_exactly_once'] is True and index['directory_metadata_duplicate_across_shards'] is True, 'index full scope')
    observed = []
    cover = {}
    seen_members = set()
    for label in LABELS:
        m = scopes[label]['manifest']
        row = capture['scopes'][label]
        R.require(len(m['members']) == row['typed_members'] and sum(r['kind'] == 'file' for r in m['members']) == row['regular_bodies'] and sum(r.get('bytes', 0) for r in m['members']) == row['logical_bytes'], 'each exact complete scope')
        if label.startswith('capsule'):
            R.require(m['root_mode'] == master['root_mode'] and row['logical_bytes'] <= 3*1024**2, 'shard original root/3MiB logical')
            for r in m['members']:
                R.require(members.get(r['path']) == r, 'shard exact original name/type/mode/body')
                seen_members.add(r['path'])
                if r['kind'] == 'file':
                    R.require(r['path'] not in cover, 'no duplicated capsule file')
                    cover[r['path']] = label
                    observed.append({'path':r['path'],'scope':label,'bytes':r['bytes'],'sha256':r['sha256']})
    R.require(seen_members == set(members) and set(cover) == set(files) and sorted(observed, key=lambda r:r['path']) == index['file_mapping'], 'complete disjoint ordered Master shard cover')
    errata = json.loads(R.read(bundle, 'PRIOR_FAILED_CAPTURE_ERRATA01.json'))
    R.require(errata['permanent_disposition'] == 'WITHHELD_ROOT_CAPTURE_MISSING_VISIT' and errata['capture_sha256'] == capture['prior_failed_capture_sha256'], 'permanent original failure disposition')
    selected_root = bundle
    for unused in Path(REL).parts:
        selected_root = selected_root.parent
    old = selected_root / OLD_REL
    oldraw = R.read(old, 'CAPTURE01.json')
    R.require(R.digest(oldraw) == capture['prior_failed_capture_sha256'] == '8b991df1466cf12f7812396b5b6afde3776edf684f1af12f9fa6e4454bf5dce1', 'literal withheld capture retained')
    prior = json.loads(oldraw)
    R.require(json.loads(R.read(old, 'CAPSULE_MASTER_MANIFEST01.json'))['members'] == [], 'historical omitted visit preserved not repaired')
    for label in ('parent','support'):
        R.require(capture['scopes'][label]['archive'] == prior['scopes'][label]['archive'], 'literal reused original scope archive')
        for name in (label.upper()+'_MANIFEST01.json','complete-'+label+'01.tar.gz'):
            R.require(R.read(bundle,name) == R.read(old,name), 'literal old/new reused scope bytes')
    for name,key in [('ROOT_EVIDENCE_PATHS01.json','root_evidence_mapping_sha256'),('SUPPORT_ROOTS01.json','support_roots_sha256')]:
        R.require(R.digest(R.read(bundle,name)) == capture[key], 'actual explicit source mapping')
    return {'capsule_members':588,'capsule_bodies':475,'logical_bytes':23015911,'historical_capture_withheld':True}


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
        R.require(free >= R.FLOOR and elapsed < 180 and len(floors) < 64, 'bounded final supplement and10GiB floor')
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
    result = {'schema_version': 1, 'status': 'COMPLETE_FAILED_OUTCOME02_BYTES_RECOVERED', 'source': SOURCE, 'identity': IDENTITY, 'capture_sha256': CAPTURE, 'remote_commit': remote['remote_commit'], 'remote_receipt_sha256': args.remote_receipt_sha256, 'scopes': restored, 'floor_observations': floors, 'native_or_claim_started': False, 'original_git_reconstruction_performed_here': False, 'baseline_original385_git_recovery_separate': True, 'posix_tree_restored': False, 'installed_runtime_bodies': False, 'numerical_release': None, 'whole_fit_capacity': None, 'qualification': 'Actual corrected failed CAP588/475 and Parent/support bytes recovered; historical capture01 remains withheld forensic evidence and failed native identity remains spent. No checkpoint decode, scientific completion, new claim or restart; baseline385 Git recovery separate.'}
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
