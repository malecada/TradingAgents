import hashlib,json,os,subprocess,tarfile
from pathlib import Path
H=Path(__file__).resolve().parent;R=Path.cwd();D=H.parent.parent/'real-data-pilot-twentyfirst-failed-increment01-2026-10-08';f=D/'FRESH_GIT_RECOVERY01.json';r=json.loads(f.read_text());checks=[]
def ck(n,v):
 assert v,n
 checks.append(n)
def sha(b):return hashlib.sha256(b).hexdigest()
env=dict(os.environ,GIT_NO_LAZY_FETCH='1',GIT_TERMINAL_PROMPT='0');env.pop('GIT_ALTERNATE_OBJECT_DIRECTORIES',None)
def git(repo,*args):return subprocess.run(['git','-C',str(repo),*args],env=env,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE).stdout
bare=Path(r['fresh_bare']);source=r['source'];ck('exact_source',source=='a5134544c3c1259fed2cc62e34694da8f443060c'==r['actual_remote_head']==r['actual_fetch_head']);ck('no_alternates',not (bare/'objects/info/alternates').exists())
ops=json.loads((D/'GIT_OPERATIONS01.json').read_text());ck('all13actualexits',len(ops)==13 and ops==r['operations'] and all(x['exit_code']==0 for x in ops))
for o in ops:
 for kind in ('stdout','stderr'):
  raw=(D/(o['operation']+'.'+kind)).read_bytes();ck(o['operation']+'_'+kind,len(raw)==o[kind+'_bytes'] and sha(raw)==o[kind+'_sha256'])
ck('recorded_remote_head',(D/'remote_actual_branch_readback.stdout').read_text().split()[0]==source)
ck('external_remote_config',git(bare,'remote','get-url','origin').decode().strip()==r['actual_external_source'])
ck('fetch_head',git(bare,'rev-parse','FETCH_HEAD').decode().strip()==source)
commit=git(bare,'cat-file','commit',source);ck('commit_body',sha(commit)==r['commit_body_sha256'] and commit==(D/'actual_external_commit_body.stdout').read_bytes() and commit==git(R,'cat-file','commit',source))
blob=r['archive_git_blob_oid'];returned=R/r['returned_archive']['path'];body=returned.read_bytes();ck('returned_archive',len(body)==1280000==r['returned_archive']['bytes'] and sha(body)==r['returned_archive']['sha256']=='23973fce1e7ea541c7678aba018ad537e757c10fdad7a013bc0f375534870ec2')
ck('actual_fetched_blob',git(bare,'cat-file','blob',blob)==body);ck('blob_oid',hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()==blob)
capraw=(R/r['capture']['path']).read_bytes();ck('capture_pin',sha(capraw)==r['capture']['sha256']);cap=json.loads(capraw)
ck('local_committed_tree_binding',git(R,'ls-tree',source,'--',cap['archive']['path']).decode().strip()==r['local_commit_tree_join'])
sraw=(R/cap['selection']['path']).read_bytes();ck('original_selection_pin',sha(sraw)==cap['selection']['sha256']);s=json.loads(sraw);rows={x['path']:x for x in s['rows']+s['directories']}
with tarfile.open(returned,'r:') as tar:
 members=tar.getmembers();ck('exact118members',len(members)==118 and len({x.name for x in members})==118 and {x.name for x in members}==set(rows))
 for m in members:
  x=rows[m.name];assert m.mode==int(x['mode'],8)
  if x['type']=='directory':assert m.isdir()
  else:
   assert m.isfile();raw=tar.extractfile(m).read();assert len(raw)==m.size==x['bytes'] and sha(raw)==x['sha256']
checks.append('all87opaque_regular_bodies31directory_types_modes')
for fname,script in [('RECOVERY_SOURCE_JOIN01.json','recover01.py'),('CAPTURE_SOURCE_JOIN01.json','capture01.py')]:
 j=json.loads((D/fname).read_text());a=(D/script).read_bytes();b=(R/j['baseline_path']).read_bytes();ck(script+'_pins',sha(a)==j['candidate_sha256'] and sha(b)==j['baseline_sha256']);text=a.decode()
 edits=j.get('literal_edits')
 if edits is None:edits={x['old']:x['new'] for x in j['edits']}
 for old,new in edits.items():text=text.replace(new,old)
 ck(script+'_inverse',text==b.decode())
x={'decision':'accepted-returned-public-increment','identity':s['identity'],'source':source,'fresh_bare':str(bare),'receipt_sha256':sha(f.read_bytes()),'archive':r['returned_archive'],'files':87,'directories':31,'regular_bytes':1090330,'checks':checks,'offline_environment':{'GIT_NO_LAZY_FETCH':'1'},'qualification':'Recorded actual remote readback/13successful operations, fresh bare fetched commit and selected blob, returned original member hashes verified. Local complete committed tree binds archive path/blob to exact fetched commit body. Commit-only/direct blob recovery does not establish whole tree availability. No scientific binary semantics/private/runtime/POSIX reconstruction/deletion authority. Original FAILED/spent92 remains unchanged.'}
(H/'RECOVERY_REVIEW01.json').write_text(json.dumps(x,indent=2)+'\n');print(json.dumps({'decision':x['decision'],'checks':len(checks),'sha256':sha((H/'RECOVERY_REVIEW01.json').read_bytes())}))
