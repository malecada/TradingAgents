"""Fresh actual remote scientific sourceA2 recovery; no research or numerical execution."""
import hashlib,json,os,stat,subprocess,sys,tarfile
from pathlib import Path,PurePosixPath

ROOT=Path.cwd();HERE=Path(__file__).resolve().parent;MAX=4194304
COMMIT=sys.argv[1]
assert len(COMMIT)==40 and all(c in '0123456789abcdef' for c in COMMIT)
def digest(b):return hashlib.sha256(b).hexdigest()
def call(args,cwd=ROOT):
 result=subprocess.run(['git',*args],cwd=cwd,capture_output=True,timeout=60)
 assert result.returncode==0 and max(len(result.stdout),len(result.stderr))<=MAX
 return result.stdout
def put(p,b):
 with p.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
branch='research/onchain-paper-replication-2026-09-24'
assert call(['ls-remote','origin','refs/heads/'+branch]).decode().split()[0]==COMMIT
out=HERE/'sourceA2-recovery02';out.mkdir(mode=0o700)
repo=out/'repository.git';call(['init','--bare',str(repo)])
call(['remote','add','origin',call(['remote','get-url','origin']).decode().strip()],repo)
call(['config','remote.origin.promisor','true'],repo)
call(['config','remote.origin.partialclonefilter','blob:none'],repo)
call(['fetch','--depth=1','--filter=blob:none','origin',COMMIT],repo)
assert call(['rev-parse','FETCH_HEAD'],repo).decode().strip()==COMMIT
rows=[]
for name in ('SOURCE_A_RETENTION02.json','sourceA2-capsule02.tar.gz','REGISTRATION_SOURCE_A02.json','INPUT_PREPARATION02.json','SOURCE_GIT_SNAPSHOT02.json','numerical-anchor02.json','PROPOSED_MATERIALIZATION_RELEASE02.json','request-inputs02.json','request-materialize-draft02.json','proposed-resources02.json','software-environment02.json','installed-runtime-records02.json','recover_sourceA02.py'):
 path=HERE/name;raw=call(['show',COMMIT+':'+str(path.relative_to(ROOT))],repo)
 assert raw==path.read_bytes();put(out/name,raw)
 rows.append({'path':str(path.relative_to(ROOT)),'sha256':digest(raw),'bytes':len(raw)})
retained=json.loads((out/'SOURCE_A_RETENTION02.json').read_bytes())
archive=out/'sourceA2-capsule02.tar.gz'
assert archive.stat().st_size==retained['archive_bytes'] and digest(archive.read_bytes())==retained['archive_sha256']
expected={r['path']:r for r in retained['members']}
assert len(expected)==len(retained['members'])==733
owned=out/'source';owned.mkdir(mode=0o700);seen=set();logical=files=directories=0
with tarfile.open(archive,'r:gz') as tf:
 for member in tf:
  archived=member.name;p=PurePosixPath(archived)
  assert archived==str(p) and not p.is_absolute() and '..' not in p.parts and '\\' not in archived and '\x00' not in archived and p.parts[0]=='source'
  name='.' if len(p.parts)==1 else str(PurePosixPath(*p.parts[1:]))
  assert name in expected and name not in seen and member.mode==expected[name]['mode']
  row=expected[name];dest=owned if name=='.' else owned/name
  assert dest.resolve()==dest and (dest==owned or dest.parent.is_dir())
  if row['kind']=='directory':
   assert member.isdir() and member.size==0 and row['bytes']==0
   if dest!=owned:dest.mkdir(mode=member.mode)
   os.chmod(dest,member.mode);directories+=1
  else:
   assert row['kind']=='file' and member.isfile() and name!='.' and member.size==row['bytes']<=MAX
   stream=tf.extractfile(member);assert stream is not None
   with stream:raw=stream.read(MAX+1)
   assert len(raw)==row['bytes'] and digest(raw)==row['sha256']
   put(dest,raw);os.chmod(dest,member.mode);files+=1;logical+=len(raw)
  seen.add(name)
assert seen==set(expected) and files==retained['files']==507 and directories==retained['directories']==226 and logical==retained['logical_bytes']==5106027
actual=set()
for p in [owned,*owned.rglob('*')]:
 name='.' if p==owned else str(p.relative_to(owned));actual.add(name);row=expected[name];s=p.lstat()
 assert stat.S_IMODE(s.st_mode)==row['mode']
 if row['kind']=='directory':assert stat.S_ISDIR(s.st_mode)
 else:assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size==row['bytes'] and digest(p.read_bytes())==row['sha256']
assert actual==seen
assert call(['rev-parse','HEAD'],owned).decode().strip()==retained['source_A2']=='9742c6ec817dd0917f9f35a52e4b83965ca1cd29'
assert not (owned/'.git/objects/info/alternates').exists()
assert call(['rev-list','--parents','-n','1',retained['source_A2']],owned).decode().split()==[retained['source_A2'],retained['source_T2']]
assert call(['rev-list','--parents','-n','1',retained['source_T2']],owned).decode().split()==[retained['source_T2'],retained['anchor_S2']]
assert call(['rev-list','--parents','-n','1',retained['anchor_S2']],owned).decode().split()==[retained['anchor_S2']]
anchor=json.loads((out/'numerical-anchor02.json').read_bytes());assert anchor['commit']==retained['anchor_S2'] and len(anchor['files'])==147
for name,pin in anchor['files'].items():assert digest(call(['show',anchor['commit']+':'+name],owned))==pin==digest((owned/name).read_bytes())
registration=json.loads((owned/'cold-registration.json').read_bytes());identity='compact-cold-inputs-20261003-01';experiment=registration['experiments'][identity]
assert set(registration['experiments'])=={identity} and registration['program_id']=='compact-cold-engineering-20261003'
assert registration['families'][experiment['family']]['attempt_budget']==2 and registration['families'][experiment['family']]['prior_attempts']==0
assert len(experiment['source_files'])==195 and len(experiment['inputs'])==9
for name,pin in experiment['source_files'].items():assert digest(call(['show',retained['source_A2']+':'+name],owned))==pin==digest((owned/name).read_bytes())
assert call(['show',retained['source_A2']+':cold-registration.json'],owned)==(owned/'cold-registration.json').read_bytes()
for ref in experiment['inputs'].values():assert digest((owned/ref['path']).read_bytes())==ref['sha256'] and call(['show',retained['source_A2']+':'+ref['path']],owned)==(owned/ref['path']).read_bytes()
assert not (owned/'research_runs'/identity).exists()
receipt={'schema_version':1,'status':'fresh-actual-remote-sourceA2-preparation-recovered','remote_commit':COMMIT,'selected_blobs':rows,'archive_sha256':retained['archive_sha256'],'members':733,'files':files,'directories':directories,'logical_bytes':logical,'source_count':retained['source_count'],'package_count':retained['package_count'],'actual_numerical_jobs':0,'qualification':'Actual selected remote Git bodies and complete new sourceA2 preparation freshly recovered into a separate owned tree. All733 original member names/modes/lengths/hashes, genuine sourceA2-T2-S2 Git ancestry, exact147 numerical-anchor/current hashes,195 sourceA2 bodies, committed finite2/prior0 registration and9 original inputs verified. This is a prepared source/registration/draft capsule only; no actual claims or numerical outcomes exist. Shared installedruntime and empiricalstores are excluded, though251 runtime RECORD pins are retained. Independent exact release/native/baseline review and final immutable released envelope remain before execution; no Owner/Binding, scientific capacity or model fit is inferred. Original capsule, archive and all earlier export/recovery evidence remain unchanged.'}
put(HERE/'REMOTE_SOURCE_A_RECOVERY02.json',(json.dumps(receipt,indent=2,sort_keys=True)+'\n').encode())
print(json.dumps({k:receipt[k] for k in ('status','remote_commit','members','files','directories','logical_bytes','actual_numerical_jobs')}))
