import ast,hashlib,json,os,stat,subprocess
from pathlib import Path
D=Path(__file__).resolve().parent;F=D.parent;ROOT=F.parents[2];T=F/'financial-wrapper-complete100-baseline-remote01-2026-10-04';B=F/'financial-wrapper-complete100-baseline-capture01-2026-10-04';H=F/'heartbeat-root-checkpoint10-2026-10-04';sha=lambda b:hashlib.sha256(b).hexdigest();checks=[];support=[]
def ok(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
def pin(p,h):
 raw=p.read_bytes();ok(sha(raw)==h,'exact '+str(p));support.append(p);return raw
selection=pin(T/'SELECTED_BODIES01.json','e5195d5eed8ff7a981199e34f9aeb4ce1f7c210dd9ba5441ec63114840125574');q=json.loads(selection);commit='189855726b372bf4bbfdf63eab0687add74886eb';ok(q['remote_commit']==commit and set(q)=={'remote_commit','rows'},'exact selection schema commit')
source=pin(T/'recover01.py','b03a2c296d122f95f395c02fa1821df25d246d3d21ce93a28560a953f2335879');pin(T/'restore02.py','8b010b28e37978c6ea24eb0e4aaad68d715f4031a102d7396f4627fd501d06e1')
required=ast.literal_eval(next(n.value for n in ast.parse(source).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='REQUIRED' for t in n.targets)));req=json.loads(pin(B/'REQUIRED_BODIES02.json','fe907bbba1d738f29876ae57a1ed52fd2a1610ba7bec8ac8ac9e52b35c662640'));ok(required==req and q['rows']==[dict(path=k,**v) for k,v in sorted(req.items())],'fixed17 exact no extras');ok(len(req)==17 and sum(x['bytes'] for x in q['rows'])==5320678 and max(x['bytes'] for x in q['rows'])<=4*1024**2 and 11+2*len(req)==45,'finite45ops/body/total')
pin(B/'CAPTURE01.json','7d65c2bac832832df5d62d49a41b31b7d54b33b52a448d048cd94b9541f8a176');pin(B/'ORIGINAL_ROOT_RECEIPT_MODES01.json','17b9baf9e9a37c3b98943e7c9d46ffa85d2771eb8d7bd7cc76530017372450da')
for name,seal in [('financial-wrapper-complete100-baseline-preservation-review01-2026-10-04','fa176fbe63a8f6d0628875998f82a8d5b0eb27fd65e7f0f4c83b53f226bba317'),('financial-wrapper-complete100-baseline-recovery-source-review01-2026-10-04','b84dc23af15e6a6fac0a3a4b73c70b1dd098ff9e18a962641ce6a0590ddc7c37')]:
 R=F/name;m=pin(R/'MANIFEST01.json',seal);rows=json.loads(m)['members'];ok({p.relative_to(R).as_posix() for p in R.rglob('*') if p!=R/'MANIFEST01.json'}=={x['path'] for x in rows}-{'.'},'full accepted review scope')
 for x in rows:
  p=R/x['path'];s=p.lstat();mode=int(x['mode'],8) if isinstance(x['mode'],str) else x['mode'];ok(stat.S_IMODE(s.st_mode)==mode,'review literal mode')
  if x['kind']=='file':ok(stat.S_ISREG(s.st_mode) and s.st_size==x['bytes'] and sha(p.read_bytes())==x['sha256'],'review body');support.append(p)
  elif x['kind']=='directory':ok(stat.S_ISDIR(s.st_mode),'review directory')
  elif x['kind']=='symlink':ok(os.readlink(p)==x['target'],'review literal link')
  else:raise AssertionError(x)
paths=sorted(set([x['path'] for x in q['rows']]+[p.relative_to(ROOT).as_posix() for p in support if p.is_file()]));env=dict(os.environ,GIT_NO_LAZY_FETCH='1',GIT_ALLOW_PROTOCOL='',GIT_NO_REPLACE_OBJECTS='1');calls=[]
def git(args):
 p=subprocess.run(['git','--no-replace-objects','-C',str(ROOT),*args],env=env,stdin=subprocess.DEVNULL,capture_output=True,timeout=10);ok(p.returncode==0 and not p.stderr and len(p.stdout)<=4*1024**2,'offline committed '+args[0]);calls.append({'args':args,'bytes':len(p.stdout),'sha256':sha(p.stdout)});return p.stdout
# Selection itself is postcommit metadata and is not falsely required in its own selected commit.
paths=[p for p in paths if p!=(T/'SELECTED_BODIES01.json').relative_to(ROOT).as_posix()]
tree=git(['ls-tree','-r','-z',commit,'--',*paths]);objects={}
for row in tree.rstrip(b'\0').split(b'\0'):
 a,b=row.split(b'\t');objects[b.decode()]=a.decode().split()
ok(set(paths)==set(objects),'all committed support/selection membership');joined=[]
for p in paths:
 raw=(ROOT/p).read_bytes();mode,kind,oid=objects[p];ok(kind=='blob' and mode in ('100644','100755') and hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==oid,'current-to-committed OID '+p)
 if p in req:ok(raw==git(['cat-file','blob',oid]) and sha(raw)==req[p]['sha256'] and len(raw)==req[p]['bytes'],'exact selected object body');joined.append(dict(path=p,git_mode=mode,git_object=oid,**req[p]))
confraw=pin(H/'REMOTE_CONFIRMATION39.json','c8979aedea1565b6d6a39d7bfe86a73d01f46d45d6352a92e26f8109b6aab557');conf=json.loads(confraw);ok(conf['actual_remote_head']==conf['local_head']==commit and conf['push_exit']==conf['readback_exit']==0 and conf['push_chunk']=='ee38d6','genuine Root HEAD receipt')
for n in ('fresh-complete100-baseline-source339-01.git','selected','REMOTE_RECOVERY01.json','FAILED01.json'):ok(not os.path.lexists(T/n),'fresh namespace '+n)
active=[]
for p in Path('/proc').iterdir():
 if p.name.isdecimal():
  try:args=(p/'cmdline').read_bytes().split(b'\0')
  except (FileNotFoundError,PermissionError,ProcessLookupError):continue
  if str(T/'recover01.py').encode() in args:active.append(int(p.name))
ok(not active,'no exact remote helper process')
for p in q['rows']:ok(sha((ROOT/p['path']).read_bytes())==p['sha256'],'final selected body unchanged')
(D/'SELECTED_BODIES01.json').write_bytes(selection);(D/'REMOTE_CONFIRMATION39.json').write_bytes(confraw)
(D/'READBACK01.json').write_text(json.dumps({'checks':len(checks),'names':checks,'actual_current_committed_joins':joined,'offline_git_calls':calls,'committed_support_bodies':len(paths),'remote_processes':active,'actual_remote_receipt':None,'actual_flat_receipt':None,'network_calls':0},indent=2)+'\n');print(json.dumps({'checks':len(checks),'selected':len(joined),'support':len(paths)}))
