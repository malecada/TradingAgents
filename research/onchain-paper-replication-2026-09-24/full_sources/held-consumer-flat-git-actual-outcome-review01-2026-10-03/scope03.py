"""Retain exact out-of-scope tree refusal; final object bytes unchanged."""
import hashlib,json,os,stat,sys
from pathlib import Path
from unittest.mock import patch
O=Path(__file__).resolve().parent;F=O.parent;P=F/'held-consumer-flat-git-root-specification01-2026-10-03';H=F/'held-consumer-flat-git-recovery-preparation01-2026-10-03';sys.path.insert(0,str(H));import archive03 as a;import bounded_git_fd01 as g
spec=json.loads((P/'SPEC01.json').read_bytes());e=json.loads(Path(spec['expected_file']).read_bytes());root=Path(spec['output_root']);fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW);realpop=g.subprocess.Popen;realread=g.os.read;children=[];stderr=bytearray();error=None
try:
 def pop(*args,**kw):p=realpop(*args,**kw);children.append(p);return p
 def read(f,n):
  b=realread(f,n)
  if children and f==children[-1].stderr.fileno():stderr.extend(b);assert len(stderr)<=65536
  return b
 with patch.object(g.subprocess,'Popen',pop),patch.object(g.os,'read',read):
  try:g.git(fd,['--no-replace-objects','--literal-pathspecs','--git-dir=.','ls-tree','-r','-z',e['selected_c6']['commit']])
  except ValueError as x:error=str(x)
  else:raise AssertionError('previous out-of-scope full tree unexpectedly succeeded')
 assert error and children and all(p.poll() is not None and all(s.closed for s in (p.stdin,p.stdout,p.stderr)) for p in children)
finally:os.close(fd)
inventory=json.loads((O/'OBJECT_INVENTORY02.json').read_bytes())
for r in inventory:
 raw=a.read(root,r['path']);s=(root/r['path']).lstat();assert len(raw)==r['bytes'] and hashlib.sha256(raw).hexdigest()==r['sha256'] and stat.S_IMODE(s.st_mode)==r['actual_mode']
assert hashlib.sha256(a.read(root,'proof.json')).hexdigest()=='b4544ebb75a5411b99d07fccd5c34ed72e5c40f9f53a6e6558dfaf9bb3523c5c'
result={'status':'OUTSIDE_SELECTED_SCOPE_FULL_C6_TREE_REFUSAL_RETAINED','commit':e['selected_c6']['commit'],'command':['ls-tree','-r','-z',e['selected_c6']['commit']],'refusal':error,'stderr_utf8':stderr.decode(),'children_reaped_pipes_closed':True,'all354_objects_final_bytes_unchanged':True,'actual_proof_unchanged':True,'qualification':'full recursive C6 tree is not the accepted selected26-path contract; no objects fetched/generated or store modified'};(O/'SCOPE_REFUSAL03.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps(result,indent=2))
