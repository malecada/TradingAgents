from pathlib import Path
import ast,hashlib,json,difflib
D=Path(__file__).resolve().parent;old=(D/'ORIGINAL_restore01.py').read_text();new=old;edits=[]
def replace(a,b):
 global new
 assert new.count(a)==1,a;new=new.replace(a,b);edits.append({'old':a,'new':b})
pins=next(x for x in ast.parse(old).body if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PINS' for t in x.targets));oldline=old.splitlines()[pins.lineno-1];p=ast.literal_eval(pins.value)
for n in ['COMPLETED_REMOTE03_READ_ONLY_SELECTED_MODE_PROFILE01.json','COMPLETED_REMOTE_REVIEW_MACHINE01.json','COMPLETED_REMOTE_REVIEW_MANIFEST01.json']:p[n]=hashlib.sha256((D/n).read_bytes()).hexdigest()
replace(oldline,'PINS = '+repr(p))
replace('        self.anchors = {}\n','        self.anchors = {}\n        self.selected_profile = None\n')
replace('        s = path.lstat()\n        R.require(stat.S_ISDIR(s.st_mode)', '''        s = path.lstat()
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
        R.require(stat.S_ISDIR(s.st_mode)''')
replace('    def anchor(self, root):\n', '''    def input_directory_mode(self, path, private_mode=0o700):
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
''')
replace("stat.S_IMODE(s.st_mode)==0o700 and s.st_uid==os.geteuid(), 'cohort root private owner/mode'", "stat.S_IMODE(s.st_mode)==self.input_directory_mode(root) and s.st_uid==os.geteuid(), 'cohort exact input or private output owner/mode'")
replace("stat.S_IMODE(before[2]) == directory_mode, 'cohort private directory mode'", "stat.S_IMODE(before[2]) == self.input_directory_mode(path,directory_mode), 'cohort exact input or private directory mode'")
replace("    cohort.tree(root/'selected', set(REQUIRED))\n", "    profile = cohort.bind_completed_selected_profile(root,remote,selection,selection_sha256)\n    cohort.tree(root/'selected', set(REQUIRED))\n")
replace("    R.require(set(selected_files) == set(REQUIRED) and all(row['mode'] == 0o700 for row in selected_manifest['members'] if row['kind'] == 'directory'), 'complete private selected namespace with no extra bodies')", "    R.require(set(selected_files) == set(REQUIRED) and selected_manifest == profile['full_manifest'], 'complete original selected namespace and literal observed modes')")
replace("'cohort_currentness':'sampled complete private membership/signature population tied to exact byte reads after IO cleanup; no writer exclusion or same-signature ABA assurance'", "'read_only_selected_mode_profile_sha256':PINS['COMPLETED_REMOTE03_READ_ONLY_SELECTED_MODE_PROFILE01.json'],'cohort_currentness':'sampled exact original input-mode population and private output population tied to exact byte reads after IO cleanup; no writer exclusion or same-signature ABA assurance'")
(D/'restore01.py').write_text(new)
rebuilt=new
for e in reversed(edits):assert rebuilt.count(e['new'])==1;rebuilt=rebuilt.replace(e['new'],e['old'])
assert rebuilt==old
oldtree=ast.parse(old);newtree=ast.parse(new)
f=lambda tree:{x.name:ast.dump(x) for x in tree.body if isinstance(x,(ast.ClassDef,ast.FunctionDef))}
a,b=f(oldtree),f(newtree);changed=sorted(n for n in a if a[n]!=b[n]);assert changed==['VerifiedCohort','authenticate_selected','run']
(D/'SOURCE_INVERSE01.json').write_text(json.dumps({'old_sha256':hashlib.sha256(old.encode()).hexdigest(),'new_sha256':hashlib.sha256(new.encode()).hexdigest(),'exact_literal_inverse':True,'exact_ast_inverse':ast.dump(ast.parse(rebuilt))==ast.dump(oldtree),'changed_top_level_definitions':changed,'edits':edits},indent=2)+'\n')
(D/'SOURCE_DIFF01.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='original-flat03',tofile='candidate-mode04')))
print(hashlib.sha256(new.encode()).hexdigest())
