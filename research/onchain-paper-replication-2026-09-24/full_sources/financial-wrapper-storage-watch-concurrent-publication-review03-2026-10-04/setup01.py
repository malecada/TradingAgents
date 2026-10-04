from pathlib import Path
import json,hashlib,stat,ast,subprocess
R=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=R/'research/onchain-paper-replication-2026-09-24/full_sources'
A=F/'financial-wrapper-storage-watch-concurrent-publication-correction03-2026-10-04';O=F/'financial-wrapper-storage-watch-concurrent-publication-review03-2026-10-04';O.mkdir(mode=0o700)
h=lambda b:hashlib.sha256(b).hexdigest()
m=A/'MANIFEST01.json';assert h(m.read_bytes())=='81fb7274cd2db72faaa0ec35fb969b4bf838e4c6d676dffd3078da5ea115561b'
rows=json.loads(m.read_bytes())['members']; seen=[]
for x in rows:
 p=A/x['path'];s=p.lstat();assert stat.S_IMODE(s.st_mode)==x['mode'];assert s.st_nlink==x.get('links',s.st_nlink)
 if x['kind']=='file':assert stat.S_ISREG(s.st_mode) and s.st_size==x['bytes'] and h(p.read_bytes())==x['sha256']
 elif x['kind'] in ('directory','dir'):assert stat.S_ISDIR(s.st_mode)
 elif x['kind']=='symlink':assert stat.S_ISLNK(s.st_mode) and p.readlink().as_posix()==x.get('target',x.get('link_target'))
 else:raise AssertionError(x)
 seen.append(x['path'])
actual=sorted(str(p.relative_to(A)) for p in A.rglob('*') if p!=m);assert sorted(seen)==actual
new=(A/'workflow_storage.py').read_text();old=(A/'original02_workflow_storage.py').read_text();assert h(new.encode())=='91e21c525a156cc8c25877ac35f0308896a1a0d1e6279d5aecf91d7e02567780'
inv=json.loads((A/'FINAL_INVERSE02.json').read_bytes());back=new
for op in reversed(inv['operations']):assert back[op['new_start']:op['new_end']]==op['new_literal'];back=back[:op['new_start']]+op['old_literal']+back[op['new_end']:]
assert back==old
oldast=ast.parse(old);newast=ast.parse(new)
def strip(t):
 for n in t.body:
  if isinstance(n,ast.ClassDef) and n.name=='StorageWatch':n.body=[x for x in n.body if not isinstance(x,ast.FunctionDef) or x.name not in ('check','_check')]
 return ast.dump(t,include_attributes=False)
assert strip(oldast)==strip(newast)
for name in ['workflow_storage.py','original_workflow_storage.py','predecessor_workflow_storage.py','original02_workflow_storage.py','DRAFT02_interleaved_rejoin.py','FINAL_INVERSE02.json','REPORT01.md']:(O/name).write_bytes((A/name).read_bytes())
(O/'AUTHENTICATION01.json').write_text(json.dumps({'author_manifest_sha256':h(m.read_bytes()),'members':len(rows),'complete_membership':True,'literal_inverse':True,'all_other_ast_equal':True,'source_sha256':h(new.encode()),'original_anchor_sha256':h((A/'original_workflow_storage.py').read_bytes())},indent=2)+'\n')
for name in ['test15.py','test16.py','test17.py','nested_controls11.py','no_primary_controls12.py','diagnostic_controls13.py','history_controls14.py']:
 d=O/('replay-'+name.removesuffix('.py'));d.mkdir();(d/name).write_bytes((A/name).read_bytes())
 for p in O.glob('*.py'):(d/p.name).write_bytes(p.read_bytes())
 with (d/'stdout.json').open('xb') as out,(d/'stderr.txt').open('xb') as err:
  result=subprocess.run([str(R/'.venv/bin/python'),'-B',str(d/name)],stdout=out,stderr=err,timeout=30)
 (d/'exit.json').write_text(json.dumps({'returncode':result.returncode})+'\n')
 print(name,result.returncode)
