import hashlib,json,os,subprocess,tarfile,resource,signal,stat
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,256*1024**2))
resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,4*1024**2))
os.sched_setaffinity(0,{3,4});os.nice(10);signal.alarm(60)
from pathlib import Path
H=Path(__file__).resolve().parent;R=Path.cwd();D=H.parent.parent/'real-data-pilot-twentythird-failed-increment01-2026-10-09';f=D/'FRESH_GIT_RECOVERY01.json';r=json.loads(f.read_text());checks=[]
def ck(n,v):
 assert v,n
 checks.append(n)
def sha(b):return hashlib.sha256(b).hexdigest()
env=dict(os.environ,GIT_NO_LAZY_FETCH='1',GIT_TERMINAL_PROMPT='0');env.pop('GIT_ALTERNATE_OBJECT_DIRECTORIES',None)
def git(repo,*args):return subprocess.run(['git','-c','core.packedGitWindowSize=1m','-c','core.packedGitLimit=16m','-C',str(repo),*args],env=env,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE).stdout
bare=Path(r['fresh_bare']);source=r['source'];ck('exact_source',source=='c379ac9e7abb4af6aa9dab55729f9d3280e9e2ee'==r['actual_remote_head']==r['actual_fetch_head']);ck('no_alternates',not (bare/'objects/info/alternates').exists())
ops=json.loads((D/'GIT_OPERATIONS01.json').read_text());ck('all13actualexits',len(ops)==13 and ops==r['operations'] and all(x['exit_code']==0 for x in ops))
for o in ops:
 for kind in ('stdout','stderr'):
  raw=(D/(o['operation']+'.'+kind)).read_bytes();ck(o['operation']+'_'+kind,len(raw)==o[kind+'_bytes'] and sha(raw)==o[kind+'_sha256'])
ck('recorded_remote_head',(D/'remote_actual_branch_readback.stdout').read_text().split()[0]==source)
ck('external_remote_config',git(bare,'remote','get-url','origin').decode().strip()==r['actual_external_source'])
ck('fetch_head',git(bare,'rev-parse','FETCH_HEAD').decode().strip()==source)
commit=git(bare,'cat-file','commit',source);ck('commit_body',sha(commit)==r['commit_body_sha256'] and commit==(D/'actual_external_commit_body.stdout').read_bytes() and commit==git(R,'cat-file','commit',source))
blob=r['archive_git_blob_oid'];returned=R/r['returned_archive']['path'];body=returned.read_bytes();ck('returned_archive',len(body)==4331520==r['returned_archive']['bytes'] and sha(body)==r['returned_archive']['sha256']=='3c5439cb702f169d31d2d113004e0f1c132d2f8d6a5585fb4d66aaea78db611c')
ck('actual_fetched_blob',git(bare,'cat-file','blob',blob)==body);ck('blob_oid',hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()==blob)
capraw=(R/r['capture']['path']).read_bytes();ck('capture_pin',sha(capraw)==r['capture']['sha256']);cap=json.loads(capraw)
ck('local_committed_tree_binding',git(R,'ls-tree',source,'--',cap['archive']['path']).decode().strip()==r['local_commit_tree_join'])
sraw=(R/cap['selection']['path']).read_bytes();ck('original_selection_pin',sha(sraw)==cap['selection']['sha256']);s=json.loads(sraw);rows={x['path']:x for x in s['rows']+s['directories']}
with tarfile.open(returned,'r:') as tar:
 members=tar.getmembers();ck('exact175members',len(members)==175 and len({x.name for x in members})==175 and {x.name for x in members}==set(rows))
 for m in members:
  x=rows[m.name];assert m.mode==int(x['mode'],8)
  if x['type']=='directory':assert m.isdir()
  else:
   assert m.isfile();raw=tar.extractfile(m).read();assert len(raw)==m.size==x['bytes'] and sha(raw)==x['sha256']
checks.append('all140opaque_regular_bodies35directory_types_modes')
scope=H.parent/'SELECTION_REVIEW01.json';scraw=scope.read_bytes();ck('accepted_selection_scope_pin',sha(scraw)=='f1b2b8bbf090928906ec34ce5bca629a49ba7c493962ce7ba11940bafc14ceda')
for fn,review in json.loads(scraw)['helper_inverse'].items():ck('reused_helper_pin_'+fn,sha((D/fn).read_bytes())==review['candidate_sha256'] and review['literal_inverse'] is True)
ck('capture_original_archive_equal',body==(R/cap['archive']['path']).read_bytes() and cap['archive']['sha256']==sha(body) and cap['archive']['bytes']==len(body))
ck('original_selection_exact',sha(sraw)=='b9627d59d83f18d6fd2e1b7ef01db9620248f0d573444af575368f7740f8b90f' and len(s['rows'])==140 and len(s['directories'])==35 and sum(x['bytes'] for x in s['rows'])==4043990 and len(rows)==175)
for x in s['rows']+s['directories']:
 p=R/x['path'];before=p.lstat();assert stat.S_IMODE(before.st_mode)==int(x['mode'],8)
 if x['type']=='directory':assert stat.S_ISDIR(before.st_mode)
 else:
  assert stat.S_ISREG(before.st_mode) and before.st_nlink==1
  raw=p.read_bytes();after=p.lstat();assert before==after and len(raw)==x['bytes'] and sha(raw)==x['sha256']
checks.append('all_original_selected_types_modes_body_hashes_current')
x={'decision':'accepted-returned-public-increment','identity':s['identity'],'source':source,'fresh_bare':str(bare),'receipt_sha256':sha(f.read_bytes()),'archive':r['returned_archive'],'files':140,'directories':35,'regular_bytes':4043990,'checks':checks,'source_scope_review_sha256':sha(scraw),'selection_sha256':sha(sraw),'offline_environment':{'GIT_NO_LAZY_FETCH':'1','affinity':sorted(os.sched_getaffinity(0)),'nice':os.getpriority(os.PRIO_PROCESS,0),'AS_bytes':256*1024**2,'FSIZE_bytes':4*1024**2,'wall_seconds':60},'qualification':'Recorded actual remote readback/13successful operations, fresh bare fetched commit and selected blob, returned original member hashes verified. Local complete committed tree binds archive path/blob to exact fetched commit body. Commit-only/direct blob recovery does not establish whole tree availability. No scientific binary semantics/private/runtime/POSIX reconstruction/deletion authority. Original FAILED/spent94 remains unchanged.'}
(H/'RECOVERY_REVIEW01.json').write_text(json.dumps(x,indent=2)+'\n');print(json.dumps({'decision':x['decision'],'checks':len(checks),'sha256':sha((H/'RECOVERY_REVIEW01.json').read_bytes())}))
