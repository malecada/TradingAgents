import hashlib,json,os,stat
from pathlib import Path
H=Path(__file__).resolve().parent;sha=lambda b:hashlib.sha256(b).hexdigest()
first=json.loads((H/'MANIFEST01.json').read_text())
for r in first['members']:
 p=H/r['path'];s=p.lstat();assert stat.S_IMODE(s.st_mode)==r['mode']
 if r['kind']=='file':assert s.st_size==r['bytes'] and sha(p.read_bytes())==r['sha256'] and s.st_nlink==r['nlink']
 if r['kind']=='symlink':assert os.readlink(p)==r['target']
(H/'COMPLETION02.json').write_text(json.dumps({'status':'FIRST_SEAL_VERIFIED_ADDITIVE_COMPLETION','first_manifest_sha256':sha((H/'MANIFEST01.json').read_bytes()),'first_members':len(first['members']),'failure':'FREEZE01_FAILURE.json','source_changed':False,'controls_rerun':False,'report':'REPORT01.md','ordinary_graph_available':False},indent=2,sort_keys=True)+'\n')
entries=[]
for p in sorted(H.rglob('*'),key=lambda p:p.relative_to(H).as_posix()):
 if p==H/'MANIFEST02.json':continue
 s=p.lstat();r={'path':p.relative_to(H).as_posix(),'mode':stat.S_IMODE(s.st_mode)}
 if stat.S_ISDIR(s.st_mode):r.update(kind='directory')
 elif stat.S_ISREG(s.st_mode):r.update(kind='file',bytes=s.st_size,sha256=sha(p.read_bytes()),nlink=s.st_nlink)
 elif stat.S_ISLNK(s.st_mode):r.update(kind='symlink',target=os.readlink(p))
 else:raise AssertionError('unknown type')
 entries.append(r)
(H/'MANIFEST02.json').write_text(json.dumps({'schema_version':1,'members':entries,'self_excluded':True,'status':'SOURCE_ONLY_ORDINARY_GRAPH_UNAVAILABLE','supersession':'complete additive membership; MANIFEST01 and final-summary failure preserved'},indent=2,sort_keys=True)+'\n')
assert {p.relative_to(H).as_posix() for p in H.rglob('*') if p!=H/'MANIFEST02.json'}=={r['path'] for r in entries}
for r in entries:
 p=H/r['path'];s=p.lstat();assert stat.S_IMODE(s.st_mode)==r['mode']
 if r['kind']=='file':assert s.st_size==r['bytes'] and sha(p.read_bytes())==r['sha256'] and s.st_nlink==r['nlink']
a=json.loads((H/'AUTHENTICATION01.json').read_text());runs=[json.loads((H/n).read_text())['checks'] for n in ('CHECKS02.json','CHECKS04.json','CHECKS05.json')]
print(json.dumps({'source':sha((H/'npy_bytes03.py').read_bytes()),'manifest02':sha((H/'MANIFEST02.json').read_bytes()),'manifest01':sha((H/'MANIFEST01.json').read_bytes()),'machine':sha((H/'MACHINE01.json').read_bytes()),'report':sha((H/'REPORT01.md').read_bytes()),'members':len(entries),'files':sum(r['kind']=='file' for r in entries),'bytes':sum(r.get('bytes',0) for r in entries),'control_runs':runs,'authentication':a['checks']}))
