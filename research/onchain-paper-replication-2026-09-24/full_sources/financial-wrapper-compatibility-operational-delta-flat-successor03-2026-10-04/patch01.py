from pathlib import Path
import ast,hashlib
O=Path(__file__).resolve().parent;s=(O/'ORIGINAL_restore01.py').read_text();assert hashlib.sha256(s.encode()).hexdigest()=='4832c8f2664f1e97c339a5b6c80fdde6f73a6ca808856deb6324608e8f2e290e'
cohort='''
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
    def tick(self):
        R.require(time.monotonic() < self.deadline and len(self.pins) <= 32768, 'finite verified cohort')
    def signature(self, path):
        self.tick(); path = Path(path)
        R.require(path.is_absolute() and path.resolve(strict=True) == path, 'cohort canonical current path')
        s = path.lstat()
        R.require(stat.S_ISDIR(s.st_mode) or (stat.S_ISREG(s.st_mode) and s.st_nlink == 1 and s.st_size <= R.FILE), 'cohort regular/directory identity')
        return (s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_blocks)
    def pin(self, path):
        path = Path(path); sig = self.signature(path)
        R.require(path not in self.pins or self.pins[path] == sig, 'verified cohort member changed')
        self.pins[path] = sig
        return sig
    def read(self, root, name, limit=R.FILE):
        path = Path(root)/R.path_name(name)
        before = self.pin(path)
        raw = R.read(root,name,limit)
        R.require(self.signature(path) == before, 'verified read changed during descriptor cleanup')
        proof = (len(raw),R.digest(raw))
        R.require(path not in self.byte_proofs or self.byte_proofs[path] == proof, 'cohort byte proof differs')
        self.byte_proofs[path] = proof
        return raw
    def tree(self, root, files, directory_mode=0o700, file_mode=0o600):
        root = Path(root); expected = frozenset(files)
        R.require(len(expected) <= 32768 and all(type(n) is str and R.path_name(n) == n for n in expected), 'bounded exact cohort file names')
        seen = set()
        def visit(path, depth):
            self.tick(); R.require(depth <= 32, 'cohort path depth')
            before = self.pin(path)
            if stat.S_ISREG(before[2]):
                name = path.relative_to(root).as_posix()
                R.require(name in expected and stat.S_IMODE(before[2]) == file_mode, 'cohort private complete file membership')
                seen.add(name); return
            R.require(stat.S_IMODE(before[2]) == directory_mode, 'cohort private directory mode')
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
        for path,pin in tuple(self.pins.items()):
            R.require(self.signature(path) == pin, 'terminal verified cohort signature differs')
            if stat.S_ISREG(pin[2]):
                R.require(path in self.byte_proofs, 'terminal member lacks actual byte proof')
        self.tick()

'''
s=s.replace('\ndef hexpin(',cohort+'\ndef hexpin(')
s=s.replace('def authenticate_selected(root, remote, selection, selection_sha256):','def authenticate_selected(root, remote, selection, selection_sha256, cohort=None):\n    cohort = VerifiedCohort() if cohort is None else cohort\n    cohort.tree(root/\'selected\', set(REQUIRED))')
s=s.replace("body = R.read(root / 'selected', row['path'])","body = cohort.read(root / 'selected', row['path'])")
s=s.replace('    return records\n\n\ndef load_capture','    cohort.check()\n    return records\n\n\ndef load_capture')
s=s.replace('def load_capture(bundle):','def load_capture(bundle, cohort=None):\n    read = R.read if cohort is None else cohort.read')
s=s.replace('def load_failed_capture(bundle):','def load_failed_capture(bundle, cohort=None):\n    read = R.read if cohort is None else cohort.read')
# Replace reads only inside these two loader functions.
for name in ['load_capture','load_failed_capture']:
 t=ast.parse(s);n=next(x for x in t.body if isinstance(x,ast.FunctionDef) and x.name==name);lines=s.splitlines(True);section=''.join(lines[n.lineno-1:n.end_lineno]).replace('= R.read(bundle,','= read(bundle,');lines[n.lineno-1:n.end_lineno]=[section];s=''.join(lines)
s=s.replace('def verify_flat(destination, result, capture, manifest, boundary):','def verify_flat(destination, result, capture, manifest, boundary, cohort=None):\n    cohort = VerifiedCohort() if cohort is None else cohort')
s=s.replace("raw = R.read(destination, result['metadata_file'])","raw = cohort.read(destination, result['metadata_file'])")
s=s.replace("    for name,row in files.items():","    cohort.tree(destination, set(mapping.values()) | {result['metadata_file']})\n    for name,row in files.items():")
s=s.replace('body = R.read(destination,leaf)','body = cohort.read(destination,leaf)')
s=s.replace('    boundary()\n    return metadata','    boundary()\n    cohort.check()\n    return metadata')
s=s.replace('    begun = time.monotonic(); observations = []','    begun = time.monotonic(); observations = []; cohort = VerifiedCohort()')
s=s.replace("raw = R.read(HERE,'REMOTE_RECOVERY01.json'); selected_raw = R.read(HERE,'SELECTED_BODIES01.json')","raw = cohort.read(HERE,'REMOTE_RECOVERY01.json'); selected_raw = cohort.read(HERE,'SELECTED_BODIES01.json')")
s=s.replace('authenticate_selected(HERE,remote,selection,selection_sha256)','authenticate_selected(HERE,remote,selection,selection_sha256,cohort)')
s=s.replace('load_capture(bundle)','load_capture(bundle,cohort)').replace('load_failed_capture(failed_bundle)','load_failed_capture(failed_bundle,cohort)')
s=s.replace("R.read(HERE,'REMOTE_RECOVERY01.json')", "cohort.read(HERE,'REMOTE_RECOVERY01.json')").replace("R.read(HERE,'SELECTED_BODIES01.json')", "cohort.read(HERE,'SELECTED_BODIES01.json')")
s=s.replace('verify_flat(HERE/OUTPUT,restored,capture,manifest,boundary)','verify_flat(HERE/OUTPUT,restored,capture,manifest,boundary,cohort)').replace('verify_flat(HERE/FAILED_OUTPUT,failed_restored,failed_capture,failed_manifest,boundary)','verify_flat(HERE/FAILED_OUTPUT,failed_restored,failed_capture,failed_manifest,boundary,cohort)')
s=s.replace("    R.put(HERE/'FLAT_RECOVERY01.json',result)","    cohort.check()\n    R.put(HERE/'FLAT_RECOVERY01.json',result)")
s=s.replace("R.read(HERE,'FLAT_RECOVERY01.json')","cohort.read(HERE,'FLAT_RECOVERY01.json')")
s=s.replace("    print(json.dumps({'status':result['status']", "    cohort.check()\n    print(json.dumps({'status':result['status']")
s=s.replace("'qualification':'Exact41", "'cohort_currentness':'sampled complete private membership/signature population tied to exact byte reads after IO cleanup; no writer exclusion or same-signature ABA assurance','qualification':'Exact41")
ast.parse(s);(O/'restore01.py').write_text(s);print(hashlib.sha256(s.encode()).hexdigest())
