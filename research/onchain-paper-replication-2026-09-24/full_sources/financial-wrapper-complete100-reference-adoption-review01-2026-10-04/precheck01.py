import ast,hashlib,json,os,stat,subprocess,sys
from pathlib import Path
D=Path(__file__).resolve().parent;F=D.parent;S=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');H=F/'heartbeat-root-checkpoint10-2026-10-04';C=F/'financial-wrapper-claimedrun-failed-capture01-2026-10-04';P=F/'financial-batch-output-genuine-byte-bridge-preparation03-2026-10-04';sys.path.insert(0,str(P));import recovery04 as R
sha=lambda b:hashlib.sha256(b).hexdigest();checks=[];OLD='0a2e7639b42b9423b90743feadcda4078aa21816';NEW='9dc5c79f738920b52947b4e63fed0397f1b5b207';GATE='fixture_inputs/financial_wrapper_claimedrun01/gates.json';ID='financial-wrapper-classification-eager-complete100-20261003-01'
def ok(v,n):assert v,n;checks.append(n)
for name,pin in [('REFERENCE_GATE_ADOPTION01.json','9a6824f1a8e3e533930b68fa63a6e7ae19c15e3b329cdbfe079df1e64f6883cf'),('REFERENCE_GATE_ADOPTION01_INTENT.json','a7ef584b55169b9720c99efcaa69c3a3a7e9cb5dacffd9e33bc76a0cd1f13a45')]:ok(sha((H/name).read_bytes())==pin,'actual Root adoption pin '+name)
for name,pin in [('financial-wrapper-claimedrun-failed-actual-flat-review01-2026-10-04','3990bed86ee8aa873c7ed28c6170a9e67c478cc64f338eef61f3f8af3a6a51b9'),('financial-wrapper-claimedrun-next-reference-handoff-review01-2026-10-04','a8cedd365c750f58ec8e3e2afa492abf2ac2e5a072b9f8f72509c0a39accfc1d')]:
 root=F/name;mraw=(root/'MANIFEST01.json').read_bytes();ok(sha(mraw)==pin,'actual prerequisite seal '+name);m=json.loads(mraw)
 for row in m['members']:
  p=root if row['path']=='.'else root/row['path'];s=p.lstat();mode=int(row['mode'],8)if isinstance(row['mode'],str)else row['mode'];ok(stat.S_IMODE(s.st_mode)==mode,'prerequisite mode '+str(p))
  if row['kind']=='file':ok(sha(p.read_bytes())==row['sha256']and s.st_size==row['bytes'],'prerequisite body '+str(p))
 ok({p.relative_to(root).as_posix()for p in root.rglob('*')if p.name!='MANIFEST01.json'}=={r['path']for r in m['members']if r['path']!='.'},'whole prerequisite membership')
env=dict(os.environ);env['GIT_NO_REPLACE_OBJECTS']='1';calls=[]
def git(args):
 p=subprocess.run(['git','--no-replace-objects','-C',str(S),*args],env=env,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10);ok(p.returncode==0 and not p.stderr,'bounded local git '+args[0]);calls.append({'args':args,'stdout_sha256':sha(p.stdout),'exit':p.returncode});return p.stdout
ok(git(['rev-parse','HEAD']).decode().strip()==NEW,'current actual Source9dc');ok(git(['rev-parse',NEW+'^']).decode().strip()==OLD,'direct unchanged original parent');ok(git(['diff','--name-only',OLD,NEW]).decode().splitlines()==[GATE],'only one committed gate changed');ok(git(['diff','--name-only','HEAD']).strip()==b'','no tracked working changes')
trees=[]
for commit in (OLD,NEW):
 objects={}
 for item in git(['ls-tree','-r','-z',commit]).rstrip(b'\0').split(b'\0'):
  a,b=item.split(b'\t');objects[b.decode()]=tuple(a.decode().split())
 trees.append(objects)
ok(len(trees[0])==len(trees[1])==339 and set(trees[0])==set(trees[1]),'complete339 tracked set')
for n,t in trees[1].items():
 mode,kind,oid=t;b=R.read(S,n);ok(kind=='blob'and hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==oid,'actual current committed source '+n)
 if n!=GATE:ok(t==trees[0][n],'original unchanged source body/mode '+n)
oldmanifest=json.loads((C/'CAPSULE_MANIFEST01.json').read_bytes());actual=[]
for p in S.rglob('*'):
 rel=p.relative_to(S).as_posix()
 if rel.split('/')[0]=='.git':continue
 s=p.lstat();r={'path':rel,'mode':stat.S_IMODE(s.st_mode)}
 if stat.S_ISDIR(s.st_mode):r['kind']='directory'
 else:
  ok(stat.S_ISREG(s.st_mode)and s.st_nlink==1 and s.st_size<=R.FILE,'actual current regular file '+rel);b=R.read(S,rel);r.update(kind='file',bytes=len(b),sha256=sha(b))
 actual.append(r)
actual.sort(key=lambda r:r['path']);ok([r['path']for r in actual]==[r['path']for r in oldmanifest['members']],'all original failed files retained no new namespaces')
for a,b in zip(actual,oldmanifest['members']):
 if a['path']!=GATE:ok(a==b,'exact original literal mode/rawbody '+a['path'])
graw=R.read(S,GATE);ok(sha(graw)=='752c34dfad4df2ca36b5dc4dcb999846f8de01bd1a61c5356092c4e55fbd678c','accepted adopted gate exact')
gate=json.loads(graw);(D/'GATE_SCHEMA01.json').write_bytes(R.encode({'keys':list(gate),'experiment_container_type':type(gate['experiments']).__name__}))
experiments=gate['experiments'];exp=next(e for e in experiments if e['id']==ID)if isinstance(experiments,list)else experiments[ID]
ok(len(exp['source_files'])==338 and set(exp['source_files'])==set(trees[1])-{GATE},'exact338 source pins excluding gate')
for n,pin in exp['source_files'].items():ok(sha(R.read(S,n))==pin,'actual target source pin '+n)
ok(len(exp['inputs'])==8,'target eight roles')
inputs={}
for role,row in exp['inputs'].items():b=R.read(S,row['path']);ok(sha(b)==row['sha256'],'target input body '+role);inputs[role]=json.loads(b)
runtime=inputs['runtime_mapping'];exe=Path(sys.executable).resolve();ok(exe.stat().st_size<=64*1024**2 and sha(exe.read_bytes())==runtime['executable_sha256'],'actual interpreter <=64MiB body hash');ok(len(runtime['distribution_records'])==251,'runtime251 record declarations')
for row in runtime['distribution_records']:
 p=Path(row['record']);ok(p.stat().st_size<=R.FILE and sha(p.read_bytes())==row['record_sha256'],'actual opaque runtime RECORD '+row['name'])
for path in [S/'research_runs'/ID,S/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/ID]:ok(not os.path.lexists(path),'original unused namespace '+str(path))
(D/'SOURCE_BEFORE01.json').write_bytes(R.encode({'schema_version':1,'root_mode':stat.S_IMODE(S.stat().st_mode),'members':actual}));(D/'PRECHECK01.json').write_bytes(R.encode({'checks':len(checks),'checks_detail':checks,'source':NEW,'old_source':OLD,'identity':ID,'registration':GATE,'git_calls':calls,'inputs':exp['inputs'],'source_files':exp['source_files'],'runtime_RECORD_count':251,'actual_admission_not_yet_called':True,'no_new_claim':True}));print(json.dumps({'checks':len(checks),'prerequisites':'PASS','source':NEW}))
