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
PINS = {'utilities/recovery_pax01.py': 'a054d5922899b53579f4220ff3b427dc050dff075cb5470b43ff55e621b97eb2', 'utilities/owned_io.py': '09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb', 'utilities/bounded_git01.py': 'db4a65a450bf9930abac04ab794539ebd952b07826d7314b4aea4e989dd9240f', 'watch01.py': 'bdeacaadc053e615245b3e2175089842708719448ec7da970d981e5dc077ca18', 'COMPLETED_REMOTE03_READ_ONLY_SELECTED_MODE_PROFILE01.json': 'd238a23846a5bfc4b61fcc8b94092532d0ebfe1f0878833f22a6e100e1c27e29', 'COMPLETED_REMOTE_REVIEW_MACHINE01.json': '26216031a9182ca3b5a5987e3274c2263845eac974f1eb4065525f5d428bb53b', 'COMPLETED_REMOTE_REVIEW_MANIFEST01.json': '231ae543b65e63854e12a9433cbb9085b151539d0c03c90f0983f42adf75eb86'}
for name, pin in PINS.items():
    p = HERE / name
    s = p.lstat()
    if HERE.resolve() != HERE or p.resolve() != p or not stat.S_ISREG(s.st_mode) or s.st_nlink != 1 or s.st_size > 4194304 or hashlib.sha256(p.read_bytes()).hexdigest() != pin or tuple(getattr(p.lstat(), k) for k in ('st_dev','st_ino','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns')) != tuple(getattr(s, k) for k in ('st_dev','st_ino','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns')):
        raise ValueError('exact unchanged local primitive required')
sys.path.insert(0, str(HERE))
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
REQUIRED = {'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-concrete-policy-review01-2026-10-04/MACHINE01.json': {'bytes': 2676, 'sha256': '27367565dc31fdbe190a80cfecca7f609ca9e2391c8335a3a85321669e794a6a'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-concrete-policy-review01-2026-10-04/MANIFEST01.json': {'bytes': 127520, 'sha256': '82b1066539316421d5d58ab43583ba2a5ac1fad065f5360cb12e1441b0832361'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-concrete-policy-review01-2026-10-04/READBACK01.json': {'bytes': 64208, 'sha256': '54f08e320c6671e6179b4a515d0e048672032a25711b286153e005af3889f4e6'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-concrete-policy-review01-2026-10-04/REPORT01.md': {'bytes': 5361, 'sha256': '03330ea8378429a7846a5826af75646aaac3b3daa581ea552bf404a651fa9835'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-concrete-policy-review01-2026-10-04/REVIEW_PROOF01.json': {'bytes': 466, 'sha256': '0a0db0cb8fafce00024aa25c048cb9efa27d1411e57586f7217b0bc209a41cd5'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-operational-delta-capture02-2026-10-04/CAPTURE01.json': {'bytes': 1249, 'sha256': '61f3560c6fc64b7122f12a690ab728407803c7bb3c3406fd1a754456e207f939'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-operational-delta-capture02-2026-10-04/ORIGIN_MAP01.json': {'bytes': 9451, 'sha256': '0f096484bb25ce6faf59edbc4a4af388ecb91d1a2687608cf8e1f252465c4bd1'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-operational-delta-capture02-2026-10-04/PAYLOAD_MANIFEST01.json': {'bytes': 8265, 'sha256': 'a04069280b7bf7b49fc075e640109f935f65b292fe69e1f4e96342bc08ad246e'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-operational-delta-capture02-2026-10-04/operational-delta01.tar.gz': {'bytes': 225862, 'sha256': 'a60e19140e04a6ec1877bf17134ee7b16d560068e1296b13c05535ea6212357e'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-operational-delta-capture02-2026-10-04/root_delta_capture05.py': {'bytes': 6633, 'sha256': '9e7ac229e24453ae1fc89b84c575cdfd8fc557ad2d8bd9576d7bac4f04770ad4'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-operational-delta-failed-remote-capture02-2026-10-04/CAPTURE01.json': {'bytes': 1875, 'sha256': '58d76ef3d7da87994ec7052e1d16c6facadcfd53535c15fe7532956515eab740'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-operational-delta-failed-remote-capture02-2026-10-04/FAILED_PAYLOAD_MANIFEST01.json': {'bytes': 8102, 'sha256': '9843ad4d50df192912c19920198da454a5e5f0f7515b407206a56ca5c4fc7e37'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-operational-delta-failed-remote-capture02-2026-10-04/ORIGINAL_FAILED_ROOT_SCOPE43.json': {'bytes': 9840, 'sha256': '7995f07ef7660d77a40fed81f9a7fc14054a5d1b609b6e81002332c8033b6a4b'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-operational-delta-failed-remote-capture02-2026-10-04/failed-remote02.tar.gz': {'bytes': 33372, 'sha256': '06c8a9cd583bebb3f03fe4800a6f17972b490cff552509097a1e1ed09695b1da'}, 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-operational-delta-failed-remote-capture02-2026-10-04/root_remote_failure_capture02.py': {'bytes': 3066, 'sha256': '6f06bef1476024d01b730fb9f37add1ebe05b7913a549d80d8daed81415b1614'}}
LOGICAL = 64 * 1024**2
ALLOCATION = 96 * 1024**2
OUTPUT = 'flat-operational-delta01'
FAILED_OUTPUT = 'flat-failed-remote02-01'
FAILED_REL = 'research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-operational-delta-failed-remote-capture02-2026-10-04'
FAILED_CAPTURE = '58d76ef3d7da87994ec7052e1d16c6facadcfd53535c15fe7532956515eab740'
FAILURE_OBJECTS = []


class VerifiedCohort:
    """Finite sampled names/signatures tied to actual verified byte reads.

    No held writer exclusion, no atomicity or same-signature ABA guarantee.
    Every iterator is closed before the final descriptor-free signature pass.
    """
    def __init__(self):
        self.deadline = time.monotonic() + 180
        self.pins = {}
        self.byte_proofs = {}
        self.trees = {}
        self.anchors = {}
        self.selected_profile = None
    def tick(self):
        R.require(time.monotonic() < self.deadline and len(self.pins) <= 32768, 'finite verified cohort')
    def signature(self, path):
        self.tick(); path = Path(path)
        R.require(path.is_absolute() and path.resolve(strict=True) == path, 'cohort canonical current path')
        s = path.lstat()
        if self.selected_profile is not None:
            selected = Path(self.selected_profile['actual_selected_root'])
            if path == selected or path.is_relative_to(selected):
                name = path.relative_to(selected).as_posix()
                directories = self.selected_profile['directory_modes']
                files = self.selected_profile['files']
                R.require(s.st_uid == self.selected_profile['expected_owner_uid'] == os.geteuid(), 'exact completed selected owner')
                if name in directories:
                    R.require(stat.S_ISDIR(s.st_mode) and stat.S_IMODE(s.st_mode) == directories[name], 'exact completed selected directory type/mode')
                else:
                    R.require(name in files and stat.S_ISREG(s.st_mode) and stat.S_IMODE(s.st_mode) == files[name]['mode'], 'exact completed selected file population/type/mode')
        R.require(stat.S_ISDIR(s.st_mode) or (stat.S_ISREG(s.st_mode) and s.st_nlink == 1 and s.st_size <= R.FILE), 'cohort regular/directory identity')
        return (s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_blocks)
    def pin(self, path):
        path = Path(path); sig = self.signature(path)
        R.require(path not in self.pins or self.pins[path] == sig, 'verified cohort member changed')
        self.pins[path] = sig
        return sig
    def input_directory_mode(self, path, private_mode=0o700):
        # This is a single authenticated completed input tree, never a generic
        # allowance for public roots or for new flat output storage.
        if self.selected_profile is not None:
            selected = Path(self.selected_profile['actual_selected_root'])
            path = Path(path)
            if path == selected or path.is_relative_to(selected):
                name = path.relative_to(selected).as_posix()
                R.require(name in self.selected_profile['directory_modes'], 'unselected input directory')
                return self.selected_profile['directory_modes'][name]
        return private_mode
    def bind_completed_selected_profile(self, root, remote, selection, selection_sha256):
        profile_name = 'COMPLETED_REMOTE03_READ_ONLY_SELECTED_MODE_PROFILE01.json'
        raw = self.read(HERE, profile_name)
        R.require(R.digest(raw) == PINS[profile_name], 'exact completed input-mode profile bytes')
        profile = json.loads(raw)
        root = Path(root)
        R.require(str(root) == profile['actual_receiver_root'] and str(root/'selected') == profile['actual_selected_root'], 'one fixed completed receiver input profile')
        R.require(profile['schema_version'] == 1 and profile['status'] == 'OBSERVED_COMPLETED_FORENSIC_SOURCE_MODES_NO_RESTORATION_OR_MODE_MUTATION' and profile['raw_directory_mode_history_preserved'] is True, 'original input-mode observation retained')
        R.require(type(profile['expected_owner_uid']) is int and profile['expected_owner_uid'] == os.geteuid() and profile['new_owned_flat_storage_modes_required'] == {'directory':0o700,'file':0o600}, 'original owner and private new outputs')
        R.require(profile['files'] == {n:dict(pin,mode=0o600) for n,pin in REQUIRED.items()} and len(profile['directory_modes']) == 7 and set(profile['directory_modes'].values()) == {0o700,0o775}, 'exact completed selected file and directory profile')
        R.validate(profile['full_manifest'])
        expected_directories = {'.':profile['full_manifest']['root_mode']}
        expected_directories.update({r['path']:r['mode'] for r in profile['full_manifest']['members'] if r['kind']=='directory'})
        expected_files = {r['path']:{k:r[k] for k in ('bytes','mode','sha256')} for r in profile['full_manifest']['members'] if r['kind']=='file'}
        R.require(expected_directories == profile['directory_modes'] and expected_files == profile['files'], 'exact complete profile manifest projection')
        remote_raw = self.read(root,'REMOTE_RECOVERY01.json')
        selection_raw = self.read(root,'SELECTED_BODIES01.json')
        exit_raw = self.read(root,'ROOT_REMOTE03_EXIT01.json')
        R.require(R.digest(remote_raw) == profile['actual_remote_receipt_sha256'] and R.encode(remote) == remote_raw, 'actual completed remote body bound to mode profile')
        R.require(R.digest(selection_raw) == selection_sha256 == profile['selection_sha256'] and R.encode(selection) == selection_raw, 'actual completed selection body bound to mode profile')
        R.require(R.digest(exit_raw) == profile['actual_Root_exit_sha256'] and type(json.loads(exit_raw)['actual_outer_exit']) is int and json.loads(exit_raw)['actual_outer_exit'] == 0, 'actual completed Root exit bound to mode profile')
        review_raw = self.read(HERE,'COMPLETED_REMOTE_REVIEW_MACHINE01.json')
        manifest_raw = self.read(HERE,'COMPLETED_REMOTE_REVIEW_MANIFEST01.json')
        R.require(R.digest(review_raw) == PINS['COMPLETED_REMOTE_REVIEW_MACHINE01.json'] == profile['actual_remote_outcome_review_sha256'] and R.digest(manifest_raw) == PINS['COMPLETED_REMOTE_REVIEW_MANIFEST01.json'] == profile['actual_remote_outcome_review_manifest_sha256'], 'genuine original remote review and manifest pins')
        review = json.loads(review_raw); review_manifest = json.loads(manifest_raw)
        R.require(review['decision'] == 'ACCEPTED_ACTUAL_REMOTE_BYTES_WITHHELD_FLAT_ENTRY_RM1' and review['remote_receipt_sha256'] == profile['actual_remote_receipt_sha256'] and review['root_exit_sha256'] == profile['actual_Root_exit_sha256'] and review['selection_sha256'] == selection_sha256 and review['flat_entry_released'] is False and review['numerical_authority'] is False, 'original accepted bytes and withheld flat entry remain distinct')
        R.require(any(r['path']=='MACHINE01.json' and r['kind']=='file' and r['sha256']==R.digest(review_raw) and r['bytes']==len(review_raw) for r in review_manifest['members']), 'original review machine sealed by original manifest')
        R.require(self.selected_profile is None or self.selected_profile == profile, 'completed input mode profile cannot change')
        self.selected_profile = profile
        return profile
    def anchor(self, root):
        # The receiver root gains deliberate intent/output/receipt names. Pin
        # its canonical private identity, not a pre-publication directory mtime.
        root = Path(root); self.tick()
        R.require(root.is_absolute() and root.resolve(strict=True)==root, 'cohort root canonical identity')
        s = root.lstat()
        R.require(stat.S_ISDIR(s.st_mode) and stat.S_IMODE(s.st_mode)==self.input_directory_mode(root) and s.st_uid==os.geteuid(), 'cohort exact input or private output owner/mode')
        pin = (s.st_dev,s.st_ino,s.st_mode,s.st_uid)
        R.require(root not in self.anchors or self.anchors[root]==pin, 'cohort root identity changed')
        self.anchors[root] = pin
    def read(self, root, name, limit=R.FILE):
        self.anchor(root)
        path = Path(root)/R.path_name(name)
        before = self.pin(path)
        raw = R.read(root,name,limit)
        R.require(self.signature(path) == before, 'verified read changed during descriptor cleanup')
        proof = (len(raw),R.digest(raw))
        R.require(path not in self.byte_proofs or self.byte_proofs[path] == proof, 'cohort byte proof differs')
        self.byte_proofs[path] = proof
        return raw
    def tree(self, root, files, directory_mode=0o700, file_mode=0o600):
        root = Path(root); self.anchor(root); expected = frozenset(files)
        R.require(len(expected) <= 32768 and all(type(n) is str and R.path_name(n) == n for n in expected), 'bounded exact cohort file names')
        seen = set()
        def visit(path, depth):
            self.tick(); R.require(depth <= 32, 'cohort path depth')
            before = self.pin(path)
            if stat.S_ISREG(before[2]):
                name = path.relative_to(root).as_posix()
                R.require(name in expected and stat.S_IMODE(before[2]) == file_mode, 'cohort private complete file membership')
                seen.add(name); return
            R.require(stat.S_IMODE(before[2]) == self.input_directory_mode(path,directory_mode), 'cohort exact input or private directory mode')
            iterator = None; primary = None; names = []
            try:
                iterator = os.scandir(path)
                for entry in iterator:
                    self.tick(); R.require(len(names) + len(self.pins) < 32768, 'cohort finite directory members')
                    names.append(entry.name)
            except BaseException as error:
                primary = error
            R._cleanup(() if iterator is None else (iterator.close,),primary=primary)
            if primary is not None: raise primary
            R.require(self.signature(path) == before, 'cohort directory changed during iterator cleanup')
            for name in sorted(names): visit(path/name, depth+1)
        visit(root,0)
        R.require(seen == expected, 'cohort missing current body')
        previous = self.trees.get(root)
        R.require(previous is None or previous == (expected,directory_mode,file_mode), 'cohort expected population changed')
        self.trees[root] = (expected,directory_mode,file_mode)
    def check(self):
        # Finish all enumeration/iterator cleanup before the final whole-cohort
        # descriptor-free pass, which also covers earlier scopes and prerequisites.
        for root,(files,dm,fm) in tuple(self.trees.items()): self.tree(root,files,dm,fm)
        for root in tuple(self.anchors): self.anchor(root)
        for path,pin in tuple(self.pins.items()):
            R.require(self.signature(path) == pin, 'terminal verified cohort signature differs')
            if stat.S_ISREG(pin[2]):
                R.require(path in self.byte_proofs, 'terminal member lacks actual byte proof')
        self.tick()


def hexpin(value, length=64):
    R.require(type(value) is str and len(value) == length and all(c in '0123456789abcdef' for c in value), 'exact non-null lowercase hash pin')
    return value


def number(value, lower, upper):
    return type(value) in (int, float) and math.isfinite(value) and lower <= value <= upper


def selection_rows(selection):
    R.require(type(selection) is dict and set(selection) == {'remote_commit', 'rows'}, 'exact selection schema')
    hexpin(selection['remote_commit'], 40)
    rows = selection['rows']
    R.require(type(rows) is list and len(rows) == len(REQUIRED) == 15, 'exact fifteen selected rows')
    expected = [dict(path=name, **pin) for name, pin in sorted(REQUIRED.items())]
    R.require(all(type(row) is dict and set(row)=={'path','bytes','sha256'} and type(row['path']) is str and type(row['bytes']) is int and type(row['sha256']) is str for row in rows), 'strict selected field types')
    R.require(rows == expected, 'complete sorted fixed selection; no extras, duplicates or changed pins')
    R.require(sum(row['bytes'] for row in rows) == 507946 and all(0 <= row['bytes'] <= R.FILE for row in rows), 'exact finite selected extents')
    for row in rows:
        R.path_name(row['path'])
    return rows


def validate_remote(remote, selection, selection_sha256):
    """Validate recorded actual evidence. This function does not manufacture origin proof."""
    rows = selection_rows(selection)
    R.require(remote['schema_version'] == 1 and remote['status'] == REMOTE_STATUS and remote['genuine_run_or_native_started'] is False, 'actual operational delta remote status required')
    R.require(remote['selection_sha256'] == hexpin(selection_sha256) and remote['remote_commit'] == selection['remote_commit'] and remote['origin'] == ORIGIN and remote['branch'] == BRANCH, 'actual selected remote context')
    records = remote['selected_blobs']
    R.require(type(records) is list and len(records) == 15, 'actual selected denominator')
    for record, selected in zip(records, rows):
        R.require(type(record) is dict and set(record) == {'path','bytes','sha256','git_mode','git_object'}, 'actual selected record fields')
        R.require({key: record[key] for key in selected} == selected and record['git_mode'] in ('100644','100755'), 'exact selected row and regular Git mode')
        hexpin(record['git_object'], 40)
    unique = len({row['git_object'] for row in records})
    expected = 10 + unique + 2 * len(rows)
    R.require(remote['selected_count'] == 15 and remote['selected_logical_bytes'] == 507946 and remote['unique_selected_objects'] == unique and remote['expected_operations'] == expected, 'exact actual operation and object denominators')
    operations = remote['operations']
    names = ['remote','ls-remote','init','remote','config','config','fetch','rev-parse','ls-tree'] + ['fetch'] * unique + ['cat-file','cat-file'] * 15 + ['ls-remote']
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


def authenticate_selected(root, remote, selection, selection_sha256, cohort=None):
    cohort = VerifiedCohort() if cohort is None else cohort
    profile = cohort.bind_completed_selected_profile(root,remote,selection,selection_sha256)
    cohort.tree(root/'selected', set(REQUIRED))
    records = validate_remote(remote, selection, selection_sha256)
    R.require(remote['fresh_git_root'] == str(root / 'fresh-operational-source-policy02.git'), 'actual same-root remote receiver namespace')
    for row in records:
        body = cohort.read(root / 'selected', row['path'])
        R.require(len(body) == row['bytes'] and R.digest(body) == row['sha256'] and hashlib.sha1(b'blob ' + str(len(body)).encode() + b'\0' + body).hexdigest() == row['git_object'], 'actual selected body SHA/extent/Git OID')
        R.require(stat.S_IMODE((root / 'selected' / row['path']).lstat().st_mode) == 0o600, 'actual private selected body mode; Git mode retained separately')
    selected_manifest = R.scan(root / 'selected')
    selected_files = {row['path']:row for row in selected_manifest['members'] if row['kind'] == 'file'}
    R.require(set(selected_files) == set(REQUIRED) and selected_manifest == profile['full_manifest'], 'complete original selected namespace and literal observed modes')
    cohort.check()
    return records


def load_capture(bundle, cohort=None):
    read = R.read if cohort is None else cohort.read
    raw = read(bundle, 'CAPTURE01.json')
    R.require(R.digest(raw) == CAPTURE, 'exact actual capture pin')
    capture = json.loads(raw)
    R.require(capture['source_design'] == SOURCE and capture['policy_sha256'] == POLICY and capture['status'] == 'FROZEN_OPERATIONAL_SOURCE_POLICY_DELTA_NOT_EXTERNAL_RECOVERY' and capture['native_or_Run_started'] is False and capture['actual_external_or_flat_receipt'] is None, 'original capture context/nulls unchanged')
    R.require((capture['typed'],capture['files'],capture['raw_bytes'],capture['new_target_bodies'],capture['new_git_objects'],capture['original_git_basis_objects'],capture['total_reachable_git_objects'],capture['current_complete_nongit_members'],capture['preserved_unchanged_nongit_members']) == (41,33,943578,4,9,385,394,589,585), 'complete actual finite delta denominators')
    manifest_raw = read(bundle, 'PAYLOAD_MANIFEST01.json')
    manifest = json.loads(manifest_raw); R.validate(manifest)
    R.require(R.digest(manifest_raw) == capture['manifest_sha256'] == capture['archive']['manifest_sha256'] and R.encode(manifest) == manifest_raw, 'exact canonical full manifest')
    R.require(len(manifest['members']) == 41 and sum(row['kind'] == 'file' for row in manifest['members']) == 33 and sum(row.get('bytes',0) for row in manifest['members']) == 943578, 'full41/33/943578 delta')
    origin_raw = read(bundle, 'ORIGIN_MAP01.json')
    R.require(R.digest(origin_raw) == capture['origin_map_sha256'], 'exact complete original mode/path mapping')
    origins = json.loads(origin_raw)
    members = {row['path']:row for row in manifest['members'] if row['kind'] == 'file'}
    seen = set()
    for row in origins['origins']:
        name = R.path_name(row['path'])
        R.require(name not in seen and name in members and row['bytes'] == members[name]['bytes'] and row['sha256'] == members[name]['sha256'] and type(row['original_mode']) is int and 0 <= row['original_mode'] <= 0o7777, 'literal original file/mode mapping')
        seen.add(name)
    R.require(len(seen) == 22 and len([n for n in members if n.startswith('new-git-objects/')]) == 9, 'all original mapping and new Git bodies')
    archive = read(bundle, 'operational-delta01.tar.gz')
    R.require(len(archive) == capture['archive']['bytes'] <= R.FILE and R.digest(archive) == capture['archive']['sha256'], 'actual frozen archive')
    R.require(943578 + len(manifest_raw) + len(origin_raw) < LOGICAL, 'flat body/metadata logical budget')
    return capture, manifest


def verify_flat(destination, result, capture, manifest, boundary, cohort=None):
    cohort = VerifiedCohort() if cohort is None else cohort
    boundary()
    R.require(destination.resolve() == destination and stat.S_IMODE(destination.lstat().st_mode) == 0o700, 'retained canonical private flat directory')
    raw = cohort.read(destination, result['metadata_file'])
    R.require(R.digest(raw) == result['metadata_sha256'], 'flat metadata readback')
    metadata = json.loads(raw)
    R.require(metadata == {'schema_version':1,'manifest':manifest,'flat_members':metadata['flat_members'],'archive':capture['archive']}, 'complete original modes and archive retained')
    files = {r['path']:r for r in manifest['members'] if r['kind'] == 'file'}
    mapping = metadata['flat_members']
    R.require(set(mapping) == set(files) and len(set(mapping.values())) == len(files), 'complete one-to-one flat mapping')
    R.require(set(p.name for p in destination.iterdir()) == set(mapping.values()) | {result['metadata_file']}, 'exact full flat namespace')
    cohort.tree(destination, set(mapping.values()) | {result['metadata_file']})
    for name,row in files.items():
        leaf = mapping[name]
        R.require(type(leaf) is str and '/' not in leaf and leaf not in ('.','..') and leaf.startswith('body-'), 'safe flat leaf')
        body = cohort.read(destination,leaf)
        R.require(len(body) == row['bytes'] and R.digest(body) == row['sha256'] and stat.S_IMODE((destination/leaf).lstat().st_mode) == 0o600, 'all original bytes and private storage modes')
    boundary()
    cohort.check()
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


def load_failed_capture(bundle, cohort=None):
    read = R.read if cohort is None else cohort.read
    raw = read(bundle, 'CAPTURE01.json')
    R.require(R.digest(raw) == FAILED_CAPTURE, 'exact failed capture pin')
    capture = json.loads(raw)
    R.require(capture['status'] == 'COMPLETE_ORIGINAL_FAILED_FORENSIC_ROOT02_LOCAL_CAPTURE_NO_EXTERNAL_RECOVERY' and capture['actual_external_or_flat_receipt'] is None and capture['native_or_ResearchRun_claim_started'] is False, 'failed capture status and nulls')
    R.require((capture['original_typed_including_root'],capture['payload_descendants'],capture['regular_bodies'],capture['logical_original_body_bytes']) == (43,42,31,114237), 'failed complete original and descendant denominators')
    R.require(capture['Root_outer_exit'] == 1 and capture['original_init_observed_exit'] is None and capture['separate_init_actual_reaped_exit'] == 0 and capture['historical_changed_directory_path_or_field'] is None and capture['permanent_disposition'] == 'FAILED_SPENT_FORENSIC_NAMESPACE_NO_NUMERICAL_CLAIM', 'original failure observations unchanged')
    manifest_raw = read(bundle,'FAILED_PAYLOAD_MANIFEST01.json')
    manifest = json.loads(manifest_raw); R.validate(manifest)
    R.require(R.digest(manifest_raw) == capture['manifest_sha256'] == capture['archive']['manifest_sha256'] and R.encode(manifest) == manifest_raw, 'failed canonical manifest pin')
    R.require(len(manifest['members']) == 42 and sum(x['kind']=='file' for x in manifest['members']) == 31 and sum(x.get('bytes',0) for x in manifest['members']) == 114237, 'failed complete body population')
    original_raw = read(bundle,'ORIGINAL_FAILED_ROOT_SCOPE43.json')
    R.require(R.digest(original_raw) == capture['original_scope_sha256'], 'original failed full scope pin')
    original = json.loads(original_raw)
    roots = [x for x in original['members'] if x['path']=='.']
    R.require(len(roots)==1 and roots[0]['kind']=='directory' and roots[0]['mode']==manifest['root_mode'], 'original root mode retained separately')
    projected = [{k:v for k,v in x.items() if k!='allocated_bytes'} for x in original['members'] if x['path']!='.']
    R.require(projected == manifest['members'] and len(original['members'])==43, 'every original descendant kind/path/mode/body retained')
    archive = read(bundle,'failed-remote02.tar.gz')
    R.require(len(archive)==capture['archive']['bytes'] <= R.FILE and R.digest(archive)==capture['archive']['sha256'], 'failed archive full byte pin')
    return capture, manifest


def restore_failed_delta(bundle, capture, manifest, root, boundary):
    destination = root / FAILED_OUTPUT
    R.require(root.is_absolute() and root.resolve()==root and not os.path.lexists(destination), 'fresh canonical failed flat namespace')
    boundary()
    destination.mkdir(mode=0o700)
    R.require(destination.resolve()==destination and stat.S_IMODE(destination.lstat().st_mode)==0o700, 'existing private failed destination')
    result = R.restore(bundle/'failed-remote02.tar.gz',capture['archive'],manifest,destination)
    verify_flat(destination,result,capture,manifest,boundary)
    return result


def run(remote_sha256, selection_sha256):
    hexpin(remote_sha256); hexpin(selection_sha256)
    R.require(all(not os.path.lexists(HERE/name) for name in (OUTPUT,FAILED_OUTPUT,'FLAT_INTENT01.json','FLAT_RECOVERY01.json','FLAT_FAILED01.json','FLAT_POSTWRITE_OBSERVATION01.json')), 'fresh one-use flat identity')
    begun = time.monotonic(); observations = []; cohort = VerifiedCohort()
    def boundary():
        R.require(time.monotonic()-begun < 180 and len(observations) < 64, '180-second/64-sample flat bound')
        row = W.census(HERE)
        row = dict(row,elapsed_seconds=time.monotonic()-begun,free_bytes=shutil.disk_usage(HERE).free)
        R.require(row['free_bytes'] >= R.FLOOR and row['elapsed_seconds'] < 180, 'final observed floor/deadline')
        observations.append(row)
    boundary()
    raw = cohort.read(HERE,'REMOTE_RECOVERY01.json'); selected_raw = cohort.read(HERE,'SELECTED_BODIES01.json')
    R.require(R.digest(raw) == remote_sha256 and R.digest(selected_raw) == selection_sha256, 'actual explicit remote and selection pins')
    remote = json.loads(raw); selection = json.loads(selected_raw)
    R.require(R.encode(selection) == selected_raw, 'canonical actual selection')
    authenticate_selected(HERE,remote,selection,selection_sha256,cohort)
    bundle = HERE/'selected'/REL
    capture,manifest = load_capture(bundle,cohort)
    failed_bundle = HERE/'selected'/FAILED_REL
    failed_capture,failed_manifest = load_failed_capture(failed_bundle,cohort)
    boundary()
    R.put(HERE/'FLAT_INTENT01.json',{'schema_version':1,'source':SOURCE,'policy_sha256':POLICY,'capture_sha256':CAPTURE,'failed_capture_sha256':FAILED_CAPTURE,'remote_receipt_sha256':remote_sha256,'selection_sha256':selection_sha256,'one_use':True,'native_or_claim_started':False})
    boundary()
    restored = restore_delta(bundle,capture,manifest,HERE,boundary)
    failed_restored = restore_failed_delta(failed_bundle,failed_capture,failed_manifest,HERE,boundary)
    authenticate_selected(HERE,remote,selection,selection_sha256,cohort)
    capture2,manifest2 = load_capture(bundle,cohort)
    failed_capture2,failed_manifest2 = load_failed_capture(failed_bundle,cohort)
    R.require(failed_capture2 == failed_capture and failed_manifest2 == failed_manifest, 'original failed capture retained')
    R.require(capture2 == capture and manifest2 == manifest and cohort.read(HERE,'REMOTE_RECOVERY01.json') == raw and cohort.read(HERE,'SELECTED_BODIES01.json') == selected_raw, 'all immutable receipts/payload retained')
    verify_flat(HERE/OUTPUT,restored,capture,manifest,boundary,cohort)
    verify_flat(HERE/FAILED_OUTPUT,failed_restored,failed_capture,failed_manifest,boundary,cohort)
    result = {'schema_version':1,'status':'COMPLETE_OPERATIONAL_DELTA_AND_FAILED_ROOT_FLAT_BYTES','source':SOURCE,'policy_sha256':POLICY,'capture_sha256':CAPTURE,'failed_capture_sha256':FAILED_CAPTURE,'remote_receipt_sha256':remote_sha256,'selection_sha256':selection_sha256,'remote_commit':remote['remote_commit'],'restored':restored,'failed_restored':failed_restored,'original_mapping_sha256':capture['origin_map_sha256'],'whole_tree_policy':dict(W.POLICY),'initial_owned_allocation':observations[0],'whole_tree_observations':list(observations),'native_or_claim_started':False,'actual_root_exit':None,'posix_tree_restored':False,'whole_fit_capacity':None,'numerical_release':None,'read_only_selected_mode_profile_sha256':PINS['COMPLETED_REMOTE03_READ_ONLY_SELECTED_MODE_PROFILE01.json'],'cohort_currentness':'sampled exact original input-mode population and private output population tied to exact byte reads after IO cleanup; no writer exclusion or same-signature ABA assurance','qualification':'Exact41 typed/33 body operational delta plus failedRoot42 descendants/31 bodies (43 including original root) preserved. Original failed init observed exit null, separately reaped0, Root exit1 and unknown directory component remain unchanged. No failed namespace replay. Old385 Git recovery is separate; nine additional objects are opaque retained bytes, not reconstructed or fsck here. Whole owned-tree limits observed at finite before/after boundaries, not continuous quota or atomic coverage. Root tool exit is a separate later observation; original capture nulls and failed/spent identities remain unchanged.'}
    cohort.check()
    R.put(HERE/'FLAT_RECOVERY01.json',result)
    boundary()
    R.require(cohort.read(HERE,'FLAT_RECOVERY01.json') == R.encode(result), 'durable final receipt readback')
    R.put(HERE/'FLAT_POSTWRITE_OBSERVATION01.json',{'schema_version':1,'recovery_sha256':R.digest(R.encode(result)),'observation':observations[-1],'qualification':'post recovery-receipt write; this sidecar itself is outside that observation'})
    boundary()
    cohort.check()
    print(json.dumps({'status':result['status'],'regular_bodies':restored['regular_bodies']+failed_restored['regular_bodies'],'postwrite_observation':observations[-1]}))


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
        FAILURE_OBJECTS.append(primary)
        failures = []
        try:
            # No str/repr/add_note hook can replace the original exception.
            R.put(HERE/'FLAT_FAILED01.json',{'schema_version':1,'status':'FAILED_ORIGINAL_FLAT_ATTEMPT_RETAINED','native_or_claim_started':False,'original_error_text_uninspected':True,'partial_bytes_retained':True})
        except BaseException as secondary:
            failures.append(secondary)
            FAILURE_OBJECTS.append(secondary)
        R._cleanup(tuple((lambda e=e: (_ for _ in ()).throw(e)) for e in failures),primary=primary)
        raise


if __name__ == '__main__':
    entry()
