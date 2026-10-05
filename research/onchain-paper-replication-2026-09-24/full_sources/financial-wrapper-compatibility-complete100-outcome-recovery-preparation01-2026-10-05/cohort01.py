import os,stat,time,json
from pathlib import Path
import recovery_pax01 as R
HERE=Path(__file__).resolve().parent
PINS={}
REQUIRED={}
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
