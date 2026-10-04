import ast,hashlib,json,os,stat,subprocess
from pathlib import Path
D=Path(__file__).resolve().parent;F=D.parent;ROOT=F.parents[2];T=F/'financial-wrapper-claimedrun-failed-remote01-2026-10-04';S=F/'financial-wrapper-claimedrun-failed-preservation-source-review01-2026-10-04';H=F/'heartbeat-root-checkpoint10-2026-10-04';sha=lambda b:hashlib.sha256(b).hexdigest();encode=lambda x:(json.dumps(x,sort_keys=True,indent=2)+'\n').encode();checks=[]
def ok(v,msg):assert v,msg;checks.append(msg)
raw=(T/'SELECTED_BODIES01.json').read_bytes();q=json.loads(raw);commit='fab9462e111fcf12a0be0e37e50b72a80cabe4bf';ok(sha(raw)=='716a22930e6671dea25e16224c98ec352dcbd5674c961d75b5f612e54f10a928'and encode(q)==raw and q['remote_commit']==commit and set(q)=={'remote_commit','rows'},'canonical actual selection')
source=(T/'recover01.py').read_bytes();flat=(T/'restore01.py').read_bytes();ok(sha(source)=='b1b6618949cacbe5db7230ca27b7b9cb06c356f95d4fbecc3df6d013b3acd9a9'and sha(flat)=='1cdfe7bfaf9001ec7a0ea27925f48a3d8e371d290d2da807de6e782aab244440','accepted current source pins')
tree=ast.parse(source);required=ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='REQUIRED'for t in n.targets)))
ok(q['rows']==[dict(path=n,**r)for n,r in sorted(required.items())]and len(q['rows'])==8,'exact required8 no supplemental rows')
ok(sum(r['bytes']for r in q['rows'])==2594804 and max(r['bytes']for r in q['rows'])<=4*1024**2 and 11+2*len(q['rows'])==27,'whole bounds and exact27calls')
manifest=(S/'MANIFEST01.json').read_bytes();ok(sha(manifest)=='0c858a94f5415976122dea23a4d0cb177b9972c1ca6eb33f4e7f12be15aeaa36','source acceptance seal')
paths=[]
for r in json.loads(manifest)['members']:
 p=S if r['path']=='.'else S/r['path'];st=p.lstat();ok(stat.S_IMODE(st.st_mode)==r['mode'],'prior review literal mode '+r['path'])
 if r['kind']=='file':ok(len(p.read_bytes())==r['bytes']and sha(p.read_bytes())==r['sha256'],'prior review complete body '+r['path']);paths.append(p.relative_to(ROOT).as_posix())
 elif r['kind']=='directory':ok(stat.S_ISDIR(st.st_mode),'prior review directory '+r['path'])
 else:raise AssertionError('unexpected scope kind')
actual={p.relative_to(S).as_posix()for p in S.rglob('*')if p.name!='MANIFEST01.json'};ok(actual=={r['path']for r in json.loads(manifest)['members']if r['path']!='.'},'prior source review complete membership')
paths+= [r['path']for r in q['rows']]+[(T/n).relative_to(ROOT).as_posix()for n in ('recover01.py','restore01.py','SOURCE_INVERSE01.json')]+[(S/'MANIFEST01.json').relative_to(ROOT).as_posix()]
env=dict(os.environ);env['GIT_NO_REPLACE_OBJECTS']='1';calls=[]
def git(args,cap=4*1024**2):
 p=subprocess.run(['git','--no-replace-objects','-C',str(ROOT),*args],env=env,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10)
 ok(p.returncode==0 and not p.stderr and len(p.stdout)<=cap,'bounded local immutable Git '+args[0]);calls.append({'args':args,'exit':p.returncode,'stdout_bytes':len(p.stdout),'stdout_sha256':sha(p.stdout)});return p.stdout
records=git(['ls-tree','-r','-z',commit,'--',*sorted(set(paths))]);objects={}
for item in records.rstrip(b'\0').split(b'\0'):
 a,b=item.split(b'\t');mode,kind,oid=a.decode().split();objects[b.decode()]=(mode,kind,oid)
ok(set(objects)==set(paths),'complete committed requested-body set')
joined=[]
for name in sorted(set(paths)):
 p=ROOT/name;b=p.read_bytes();mode,kind,oid=objects[name];s=p.lstat();ok(kind=='blob'and mode in ('100644','100755')and stat.S_ISREG(s.st_mode),'Git regular '+name);ok(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==oid,'actual committed OID/body '+name);ok(bool(s.st_mode&0o111)==(mode=='100755'),'Git executable mode '+name)
 if name in required:
  remote_object=git(['cat-file','blob',oid]);ok(remote_object==b and len(b)==required[name]['bytes']and sha(b)==required[name]['sha256'],'actual8 committed-object readback '+name);joined.append(dict(path=name,git_mode=mode,git_object=oid,bytes=len(b),sha256=sha(b),literal_mode=stat.S_IMODE(s.st_mode)))
confirmation=H/'REMOTE_CONFIRMATION37_ADDENDUM01.json';conf=json.loads(confirmation.read_bytes());old=H/'REMOTE_CONFIRMATION37.json';ok(sha(confirmation.read_bytes())=='101afe295168a83ec38d3d51f73d09ed698615919d7d131a58178291ff67dfce'and conf['actual_observed_head']==commit and conf['actual_exit_code']==0 and conf['actual_completion_tool']=='c8b62b','actual Root readback completion join');ok(conf['original_post_push_record_sha256']==sha(old.read_bytes())and conf['original_placeholder_is_not_actual_completion_evidence']is True,'placeholder preserved excluded')
for name in ('fresh-claimedrun-failed-source339-01.git','selected','REMOTE_RECOVERY01.json','FAILED01.json','flat-capsule01','flat-parent01','flat-root01','FLAT_INTENT01.json','FLAT_RECOVERY01.json'):ok(not os.path.lexists(T/name),'fresh original namespace absent '+name)
# Subsequent source-body readback: no current body changed during joins.
for r in q['rows']:ok(sha((ROOT/r['path']).read_bytes())==r['sha256'],'final current selected body '+r['path'])
(D/'READBACK01.json').write_bytes(encode({'checks':len(checks),'checks_detail':checks,'selection_sha256':sha(raw),'commit':commit,'selected_actual_git_joins':joined,'immutable_support_count':len(paths),'local_git_calls':calls,'actual_network_calls':0,'root_operational_confirmation_sha256':sha(confirmation.read_bytes()),'confirmation_scope':'Root-retained actual tool completion, not independent network request','unresolved_placeholder_used':False,'actual_future_remote_receipt':None,'source_review_manifest_sha256':sha(manifest)}))
print(json.dumps({'checks':len(checks),'local_git_calls':len(calls),'body_joins':len(set(paths))}))
