import ast,hashlib,json,os,stat,subprocess,shutil,sys,importlib.metadata
from pathlib import Path
D=Path(__file__).resolve().parent;F=D.parent;ROOT=F.parents[2];T=F/'financial-wrapper-complete100-final-supplement-tooling01-2026-10-04';B=F/'financial-wrapper-complete100-final-supplement-capture01-2026-10-04';sha=lambda b:hashlib.sha256(b).hexdigest();checks=[];calls=[]
def ok(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
def pinned(p,h):
 b=p.read_bytes();ok(sha(b)==h,'pin '+str(p));return b
commit='3a17d3630d5c06380c5d4ede5f9f72c1b9b429b2';sel=pinned(T/'SELECTED_BODIES01.json','ef3aa53b788576c233d0bf712c04daf1ebaf4bb6cb2947352f3bea58b55f1c4d');selection=json.loads(sel);required=json.loads((B/'REQUIRED_BODIES01.json').read_bytes());ok(selection=={'remote_commit':commit,'rows':[dict(path=k,**v) for k,v in sorted(required.items())]},'exact seven current selected');ok(len(required)==7 and sum(r['bytes'] for r in required.values())==1063336,'seven finite bytes')
confraw=pinned(F/'heartbeat-root-checkpoint10-2026-10-04/REMOTE_CONFIRMATION40.json','3f19ff95ebe41db9dfa588a550fc71977765ee2fe2e769a2ad0f2b7eb7f0f632');conf=json.loads(confraw);ok(conf['actual_head']==conf['actual_remote_head']==commit and conf['push_exit']==conf['actual_ls_remote_exit']==0 and conf['push_chunk']=='10e0c4' and conf['actual_ls_remote_chunk']=='c9c823','actual Root push/readback')
env=dict(os.environ,GIT_NO_LAZY_FETCH='1',GIT_ALLOW_PROTOCOL='',GIT_NO_REPLACE_OBJECTS='1')
def git(root,args):
 p=subprocess.run(['git','--no-replace-objects','-C',str(root),*args],env=env,stdin=subprocess.DEVNULL,capture_output=True,timeout=10);ok(p.returncode==0 and not p.stderr and len(p.stdout)<=4*1024**2,'bounded offline Git '+args[0]);calls.append({'args':args,'bytes':len(p.stdout),'sha256':sha(p.stdout)});return p.stdout
ok(git(ROOT,['rev-parse','HEAD']).decode().strip()==commit,'actual current MainHEAD')
sourceproof=json.loads((D/'SOURCE02.json').read_bytes());paths=sorted(set(required)|{str(Path(r['path']).relative_to(ROOT)) for r in sourceproof['authenticated_files']});tree=git(ROOT,['ls-tree','-r','-z',commit,'--',*paths]);objects={}
for row in tree.rstrip(b'\0').split(b'\0'):
 a,b=row.split(b'\t');objects[b.decode()]=a.decode().split()
ok(set(objects)==set(paths),'all closed source/review bodies committed');joins=[]
for name in paths:
 b=(ROOT/name).read_bytes();mode,kind,oid=objects[name];ok(kind=='blob' and mode in ('100644','100755') and hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==oid,'current committed source/review bytejoin')
 if name in required:ok(git(ROOT,['cat-file','blob',oid])==b and sha(b)==required[name]['sha256'] and len(b)==required[name]['bytes'],'selected exact Gitbody');joins.append(dict(path=name,git_mode=mode,git_object=oid,**required[name]))
# Root's sole appended selection is integration metadata outside immutable author seal.
author=json.loads((T/'MANIFEST01.json').read_bytes());ok({p.relative_to(T).as_posix() for p in T.rglob('*')}==({r['path'] for r in author['members']}-{'.'})|{'MANIFEST01.json','SELECTED_BODIES01.json'},'one declared additive selection only')
Q=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-complete100-final-contract-20261004-01/REQUEST_RELEASED01.json');q=json.loads(pinned(Q,'34d1a85660af70706bd52fd8187c9a48edec39841246f03b12e88051f92e56f9'));C=Path(q['capsule_root']);P=Path(q['parent_root']);ok(git(C,['rev-parse','HEAD']).decode().strip()==q['source']==q['design_source']=='9dc5c79f738920b52947b4e63fed0397f1b5b207','current source/design')
for path,h in q['source_files'].items():pinned(C/path,h)
reg=json.loads(pinned(C/q['registration'],q['registration_sha256']));exp=reg['experiments'][q['identity']];ok(exp['source_files']==q['source_files'] and len(q['source_files'])==338 and len(exp['inputs'])==8,'complete source/input counts')
for role,ref in exp['inputs'].items():pinned(C/ref['path'],q['input_hashes'][role]);ok(ref['sha256']==q['input_hashes'][role],'registered role pin')
for ref in q['proofs'].values():pinned(Path(ref['path']),ref['sha256'])
pinned(Path(q['final_review']['path']),'f7e5b3d304090df7aaf3d6e107a2b401d752747160b9e4514708a7da6a45ef1b')
base=F/'financial-wrapper-complete100-baseline-remote01-2026-10-04';pm=json.loads((base/'flat-parent01/body-metadata.json').read_bytes());ok(set(x.name for x in P.iterdir())==set(pm['flat_members']) and len(pm['flat_members'])==9,'complete Parent9/noattempt')
for name,flat in pm['flat_members'].items():ok((P/name).read_bytes()==(base/'flat-parent01'/flat).read_bytes(),'unchanged Parentbody')
r=q['runtime_mapping'];ok(r['executable']==sys.executable and r['prefix']==sys.prefix and len(r['distribution_records'])==251,'locked runtime metadata cardinality');pinned(Path(sys.executable).resolve(),r['executable_sha256']);pinned(C/'uv.lock',r['lock_sha256'])
for item in r['distribution_records']:
 p=Path(item['record']);ok(p.is_relative_to(Path(sys.prefix)/'lib/python3.13/site-packages') and p.name=='RECORD' and p.stat().st_size<=4*1024**2,'bounded public RECORD');pinned(p,item['record_sha256']);ok(importlib.metadata.version(item['name'])==item['version'],'metadata packageversion')
jobpath=next(k for k in q['source_files'] if k.endswith('/job.py'));ja=ast.parse((C/jobpath).read_bytes());prefix=ast.literal_eval(next(x.value for x in ja.body if isinstance(x,ast.Assign) and any(isinstance(y,ast.Name) and y.id=='PREFIX' for y in x.targets)))
absent=[P/'attempt',C/'research_runs'/q['identity'],C/prefix/'runs'/q['identity'],T/'fresh-complete100-final-supplement01.git',T/'selected',T/'REMOTE_RECOVERY01.json',T/'FAILED01.json']
for p in absent:ok(not os.path.lexists(p),'fresh namespace '+str(p))
active=[]
for p in Path('/proc').iterdir():
 if p.name.isdecimal():
  try:args=(p/'cmdline').read_bytes().split(b'\0')
  except (FileNotFoundError,PermissionError,ProcessLookupError):continue
  if any(a in args for a in [str(T/'recover01.py').encode(),str(P/'parent01.py').encode(),q['identity'].encode()]):active.append(int(p.name))
ok(not active,'no exact remote/native process');free=shutil.disk_usage(T).free;ok(free>=10*1024**3,'10GiB diskfloor');memory={l.split(':')[0]:l.split(':')[1].strip() for l in Path('/proc/meminfo').read_text().splitlines() if l.startswith(('MemTotal:','MemAvailable:'))}
(D/'FINAL03.json').write_text(json.dumps({'checks':len(checks),'names':checks,'commit':commit,'selection_sha256':sha(sel),'selected_joins':joins,'committed_support_files':len(paths),'offline_git_calls':calls,'absent_namespaces':[str(p) for p in absent],'active_processes':active,'disk_free_bytes':free,'memory_observation_only':memory,'runtime_RECORD_metadata':251,'actual_remote_recovery':None,'native_release':None},indent=2)+'\n');(D/'SELECTED_BODIES01.json').write_bytes(sel);(D/'REMOTE_CONFIRMATION40.json').write_bytes(confraw);print(json.dumps({'checks':len(checks),'support':len(paths)}))
