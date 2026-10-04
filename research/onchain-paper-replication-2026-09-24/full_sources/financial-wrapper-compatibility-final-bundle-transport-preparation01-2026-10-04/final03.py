from pathlib import Path
import ast,hashlib,json,sys,stat
D=Path(__file__).resolve().parent;F=D.parent;ROOT=F.parents[2];sys.path.insert(0,str(D));import binding01 as B
from receipt01 import selection_rows
R=B.R;h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();n=0
old=R.read(D,'KNOWN_REQUIRED01.json');(D/'KNOWN_REQUIRED_DRAFT01.json').write_bytes(old);known=json.loads(old)
paths=[F/'heartbeat-root-checkpoint10-2026-10-04'/x for x in ('root_source_parent_capture03.py','root_source_parent_capture04.py')]
review=F/'financial-wrapper-compatibility-source-parent-capture-review04-2026-10-04';paths.extend(p for p in review.rglob('*') if p.is_file())
for p in paths:
 s=p.lstat();assert stat.S_ISREG(s.st_mode) and p.resolve()==p and s.st_size<=R.FILE;known[str(p.relative_to(ROOT))]={'bytes':s.st_size,'sha256':h(p)};n+=1
failed=json.loads((F/'financial-wrapper-compatibility-current-source-parent-capture03-2026-10-04/FAILED_LOCAL_CAPTURE01.json').read_bytes());assert h(paths[0])==failed['source_sha256'];n+=1
(D/'KNOWN_REQUIRED01.json').write_text(json.dumps(known,indent=2,sort_keys=True)+'\n')
selection={'remote_commit':'32d57eac5ea14435cd9d4aeb3e3b04d98bf16c41','rows':[dict(path=k,**v) for k,v in sorted(known.items())]};assert selection_rows(selection,known)==selection['rows'];n+=1
for change in ('missing','extra','bool'):
 q=json.loads(json.dumps(selection))
 if change=='missing':q['rows'].pop()
 elif change=='extra':q['rows'].append(q['rows'][0])
 else:q['rows'][0]['bytes']=True
 try:selection_rows(q,known)
 except ValueError:n+=1
 else:raise AssertionError('mutated population accepted')
A=F/'financial-wrapper-compatibility-current-source-parent-capture04-2026-10-04';cap=json.loads(R.read(A,'CAPTURE01.json'));raw=R.read(A,'source-parent-delta04.tar.gz');m=json.loads(R.read(A,'MANIFEST01.json'));frames=list(R.framed_members(raw));assert len(frames)==len(m['members'])==55;assert sum(r['kind']=='file' for r in m['members'])==47;n+=2
for (name,t,body),r in zip(frames,m['members'],strict=True):
 assert name==r['path'] and t.mode==r['mode'];n+=1
 if r['kind']=='file':assert len(body)==r['bytes'] and R.digest(body)==r['sha256'];n+=1
for p in D.glob('*.py'):ast.parse(p.read_bytes());n+=1
(D/'FINAL03.json').write_text(json.dumps({'checks':n,'known_required':len(known),'actual_capture04_frames':55,'actual_body_count':47,'known_parent_envelope_still_incomplete':True,'final_commit_selection_proofs':None,'actual_network':False,'actual_Root_restore':False},indent=2)+'\n');print(n)
